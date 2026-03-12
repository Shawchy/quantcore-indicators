"""
批量导入股票 K 线数据到数据库
使用 Tushare daily 接口
"""
import tushare as ts
import pandas as pd
import sqlite3
from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta
import time

print("=" * 70)
print("批量导入股票 K 线数据")
print("=" * 70)

# 加载 Token
env_file = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_file)
token = os.getenv('TUSHARE_TOKEN')

# 初始化 pro 接口
ts.set_token(token)
pro = ts.pro_api()

# 数据库路径
db_file = Path(__file__).parent / "backend" / "data" / "sqlite" / "quant.db"
print(f"\n💾 数据库：{db_file}")

# 连接数据库
conn = sqlite3.connect(str(db_file))
cursor = conn.cursor()

# 获取股票列表
print("\n📋 获取股票列表...")
cursor.execute('SELECT code, name FROM stock_info WHERE market IN ("主板", "创业板", "科创板") LIMIT 50')
stocks = cursor.fetchall()
print(f"   准备导入 {len(stocks)} 只股票的 K 线数据")

# 计算日期范围（最近 3 个月）
end_date = datetime.now()
start_date = end_date - timedelta(days=90)

start_date_str = start_date.strftime('%Y%m%d')
end_date_str = end_date.strftime('%Y%m%d')

print(f"\n📅 日期范围：{start_date_str} 到 {end_date_str}")

# 导入数据
imported_count = 0
failed_stocks = []

for idx, (code, name) in enumerate(stocks, 1):
    try:
        # 添加后缀
        if code.startswith('6'):
            ts_code = f"{code}.SH"
        else:
            ts_code = f"{code}.SZ"
        
        print(f"[{idx}/{len(stocks)}] 导入 {ts_code} ({name})...", end=" ")
        
        # 获取 K 线数据
        df = pro.daily(
            ts_code=ts_code,
            start_date=start_date_str,
            end_date=end_date_str
        )
        
        if df.empty:
            print("⚠️  无数据")
            failed_stocks.append((ts_code, "无数据"))
            continue
        
        # 转换字段名
        df = df.rename(columns={
            'trade_date': 'date',
            'vol': 'volume',
            'pct_chg': 'change_pct'
        })
        
        # 保存到数据库
        saved = 0
        for _, row in df.iterrows():
            try:
                # 检查是否已存在
                cursor.execute('''
                    SELECT id FROM kline 
                    WHERE code=? AND date=? AND adjust_type='none'
                ''', (code, str(row['date'])))
                
                if cursor.fetchone():
                    # 更新
                    cursor.execute('''
                        UPDATE kline SET
                            open=?, high=?, low=?, close=?, 
                            volume=?, amount=?, change_pct=?
                        WHERE code=? AND date=? AND adjust_type='none'
                    ''', (
                        row['open'], row['high'], row['low'], row['close'],
                        row['volume'], row['amount'], row['change_pct'],
                        code, str(row['date'])
                    ))
                else:
                    # 插入
                    cursor.execute('''
                        INSERT INTO kline (
                            code, date, open, high, low, close,
                            volume, amount, change_pct, adjust_type
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        code, str(row['date']),
                        row['open'], row['high'], row['low'], row['close'],
                        row['volume'], row['amount'], row['change_pct'],
                        'none'
                    ))
                
                saved += 1
            except Exception as e:
                continue
        
        conn.commit()
        print(f"✅ {saved}条")
        imported_count += 1
        
        # 避免请求过快
        time.sleep(0.1)
        
    except Exception as e:
        print(f"❌ 失败：{e}")
        failed_stocks.append((code, str(e)))
        time.sleep(1)

# 统计
print("\n" + "=" * 70)
print("导入完成")
print("=" * 70)
print(f"   成功：{imported_count}/{len(stocks)} 只股票")
print(f"   失败：{len(failed_stocks)} 只股票")

if failed_stocks:
    print(f"\n失败的股票:")
    for code, reason in failed_stocks[:10]:
        print(f"   {code}: {reason}")
    if len(failed_stocks) > 10:
        print(f"   ... 还有 {len(failed_stocks) - 10} 只")

# 验证数据
print("\n📊 验证数据:")
cursor.execute('SELECT COUNT(*) FROM kline')
total = cursor.fetchone()[0]
print(f"   kline 表总记录数：{total:,} 条")

cursor.execute('SELECT COUNT(DISTINCT code) FROM kline')
stock_count = cursor.fetchone()[0]
print(f"   涉及股票数：{stock_count} 只")

cursor.execute('SELECT MIN(date), MAX(date) FROM kline')
date_range = cursor.fetchone()
print(f"   日期范围：{date_range[0]} 到 {date_range[1]}")

conn.close()

print("\n" + "=" * 70)
print("✅ 批量导入完成")
print("=" * 70)
