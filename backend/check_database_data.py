"""
数据库数据检查和问题诊断
"""
import sqlite3
import os
from datetime import datetime

# 数据库路径
db_path = os.path.join(os.path.dirname(__file__), 'data', 'sqlite', 'quant.db')

print("=" * 70)
print("数据库数据检查报告")
print("=" * 70)
print(f"\n数据库路径：{db_path}")
print(f"数据库文件存在：{os.path.exists(db_path)}")
print(f"数据库文件大小：{os.path.getsize(db_path) / 1024:.2f} KB")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 1. 检查所有表的记录数
print("\n" + "=" * 70)
print("1️⃣ 各表数据量统计")
print("=" * 70)

tables = ['stock_info', 'kline', 'technical_indicators', 'sector_info', 
          'watchlist', 'chip_data', 'strategy', 'backtest_record', 'trade_record']

for table in tables:
    try:
        cursor.execute(f'SELECT COUNT(*) FROM {table}')
        count = cursor.fetchone()[0]
        status = "✅" if count > 0 else "❌ 空表"
        print(f"{status} {table:25} : {count:>10,} 条记录")
    except Exception as e:
        print(f"❌ {table:25} : 检查失败 - {e}")

# 2. 检查 stock_info 表是否为空
print("\n" + "=" * 70)
print("2️⃣ stock_info 表检查")
print("=" * 70)

cursor.execute('SELECT COUNT(*) FROM stock_info')
stock_count = cursor.fetchone()[0]

if stock_count == 0:
    print("⚠️  stock_info 表为空！这是前端无股票数据展示的根本原因")
    print("\n可能的原因:")
    print("  1. 数据源未正常拉取股票列表")
    print("  2. 股票列表保存逻辑有问题")
    print("  3. 数据库初始化后未填充数据")
else:
    print(f"✅ stock_info 表有 {stock_count} 条记录")
    cursor.execute('SELECT code, name, market, industry FROM stock_info LIMIT 5')
    print("\n前 5 条记录:")
    for row in cursor.fetchall():
        print(f"  {row[0]} | {row[1]:10} | {row[2]} | {row[3]}")

# 3. 检查 kline 表数据
print("\n" + "=" * 70)
print("3️⃣ kline 表数据检查")
print("=" * 70)

cursor.execute('SELECT COUNT(*) FROM kline')
kline_count = cursor.fetchone()[0]
print(f"kline 表记录数：{kline_count:,}")

if kline_count > 0:
    cursor.execute('SELECT DISTINCT code FROM kline LIMIT 10')
    codes = [row[0] for row in cursor.fetchall()]
    print(f"涉及的股票代码：{', '.join(codes)}")
    
    cursor.execute('SELECT MIN(date), MAX(date) FROM kline')
    date_range = cursor.fetchone()
    print(f"日期范围：{date_range[0]} ~ {date_range[1]}")
    
    cursor.execute('SELECT DISTINCT adjust_type FROM kline')
    adjusts = [row[0] for row in cursor.fetchall()]
    print(f"复权类型：{', '.join(adjusts)}")

# 4. 检查 sector_info 表
print("\n" + "=" * 70)
print("4️⃣ sector_info 表检查")
print("=" * 70)

cursor.execute('SELECT COUNT(*) FROM sector_info')
sector_count = cursor.fetchone()[0]
if sector_count == 0:
    print("⚠️  sector_info 表为空！前端无法显示板块列表")
else:
    print(f"✅ sector_info 表有 {sector_count} 条记录")
    cursor.execute('SELECT code, name, sector_type FROM sector_info LIMIT 5')
    print("\n前 5 条记录:")
    for row in cursor.fetchall():
        print(f"  {row[0]} | {row[1]:15} | {row[2]}")

# 5. 数据问题分析
print("\n" + "=" * 70)
print("5️⃣ 问题诊断")
print("=" * 70)

issues = []

if stock_count == 0:
    issues.append({
        'level': '🔴 P0',
        'issue': 'stock_info 表为空',
        'impact': '前端无法显示股票列表、搜索结果',
        'solution': '调用数据源的 get_stock_list() 方法拉取股票列表并保存'
    })

if sector_count == 0:
    issues.append({
        'level': '🔴 P0',
        'issue': 'sector_info 表为空',
        'impact': '前端无法显示板块列表、板块分析',
        'solution': '调用数据源的 get_sector_list() 方法拉取板块列表并保存'
    })

if kline_count < 100:
    issues.append({
        'level': '🟡 P1',
        'issue': f'kline 表数据过少 ({kline_count}条)',
        'impact': '前端 K 线图显示数据不足',
        'solution': '调用数据源的 get_kline() 方法批量拉取历史 K 线数据'
    })

if issues:
    print("\n发现的问题:\n")
    for idx, issue in enumerate(issues, 1):
        print(f"{idx}. {issue['level']} {issue['issue']}")
        print(f"   影响：{issue['impact']}")
        print(f"   解决：{issue['solution']}\n")
else:
    print("✅ 未发现明显问题")

# 6. 建议操作
print("=" * 70)
print("6️⃣ 建议操作")
print("=" * 70)

print("\n立即执行:")
print("  1. 启动数据源拉取股票列表")
print("  2. 启动数据源拉取板块列表")
print("  3. 批量拉取历史 K 线数据")
print("\n验证步骤:")
print("  1. 重新运行此脚本检查数据量")
print("  2. 测试后端 API 返回数据")
print("  3. 检查前端数据展示")

conn.close()

print("\n" + "=" * 70)
print("检查完成")
print("=" * 70)
