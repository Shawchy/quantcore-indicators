"""
测试 Tushare A 股日线行情接口
接口：daily
描述：获取股票日线行情数据（未复权）
积分：120 分（基础权限）
"""
import tushare as ts
from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime

print("=" * 70)
print("测试 Tushare A 股日线行情接口 (daily)")
print("=" * 70)

# 加载 Token
env_file = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_file)
token = os.getenv('TUSHARE_TOKEN')

print(f"\nToken: {token[:10]}...{token[-5:]}")

# 初始化 pro 接口
ts.set_token(token)
pro = ts.pro_api()

# 测试 1: 获取单只股票日线数据
print("\n" + "=" * 70)
print("测试 1: 获取平安银行 (000001.SZ) 最近 10 个交易日数据")
print("=" * 70)

try:
    # 计算日期范围（最近 10 个交易日）
    end_date = datetime.now().strftime('%Y%m%d')
    start_date = (datetime.now() - pd.Timedelta(days=30)).strftime('%Y%m%d')
    
    df = pro.daily(
        ts_code='000001.SZ',
        start_date=start_date,
        end_date=end_date
    )
    
    print(f"\n✅ 成功获取数据!")
    print(f"   记录数：{len(df)} 条")
    print(f"   股票代码：{df['ts_code'].iloc[0] if len(df) > 0 else 'N/A'}")
    
    # 显示前 10 条
    print(f"\n📊 前 10 条记录:")
    print(df.head(10).to_string())
    
    # 统计信息
    if len(df) > 0:
        print(f"\n📈 统计信息:")
        print(f"   最高价：{df['high'].max():.2f}")
        print(f"   最低价：{df['low'].min():.2f}")
        print(f"   平均成交量：{df['vol'].mean():.2f} 手")
        print(f"   平均成交额：{df['amount'].mean():.2f} 千元")
    
    # 保存数据
    output_file = Path(__file__).parent / "daily_000001.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 数据已保存到：{output_file}")
    
except Exception as e:
    print(f"\n❌ 获取数据失败：{e}")
    import traceback
    traceback.print_exc()

# 测试 2: 获取多只股票数据
print("\n" + "=" * 70)
print("测试 2: 获取多只股票数据")
print("=" * 70)

try:
    # 多个股票代码（逗号分隔）
    codes = '000001.SZ,600000.SH,000002.SZ'
    
    df = pro.daily(
        ts_code=codes,
        start_date='20240301',
        end_date='20240312'
    )
    
    print(f"\n✅ 成功获取数据!")
    print(f"   记录数：{len(df)} 条")
    print(f"   股票数量：{df['ts_code'].nunique()} 只")
    
    # 按股票分组显示
    print(f"\n📊 各股票数据量:")
    for code in df['ts_code'].unique():
        count = len(df[df['ts_code'] == code])
        print(f"   {code}: {count} 条")
    
    # 显示样例
    print(f"\n📋 数据样例:")
    print(df.head(6).to_string())
    
except Exception as e:
    print(f"\n❌ 获取数据失败：{e}")

# 测试 3: 使用 trade_date 获取某一天全部股票
print("\n" + "=" * 70)
print("测试 3: 获取 2024 年 3 月 11 日全部股票数据")
print("=" * 70)

try:
    df = pro.daily(trade_date='20240311')
    
    print(f"\n✅ 成功获取数据!")
    print(f"   股票数量：{len(df)} 只")
    
    # 显示前 10 只
    print(f"\n📊 前 10 只股票:")
    print(df[['ts_code', 'trade_date', 'open', 'high', 'low', 'close', 'vol']].head(10).to_string())
    
    # 统计涨跌
    up_count = len(df[df['pct_chg'] > 0])
    down_count = len(df[df['pct_chg'] < 0])
    flat_count = len(df[df['pct_chg'] == 0])
    
    print(f"\n📈 市场表现:")
    print(f"   上涨：{up_count} 只 ({up_count/len(df)*100:.1f}%)")
    print(f"   下跌：{down_count} 只 ({down_count/len(df)*100:.1f}%)")
    print(f"   平盘：{flat_count} 只 ({flat_count/len(df)*100:.1f}%)")
    
except Exception as e:
    print(f"\n❌ 获取数据失败：{e}")
    print(f"   可能原因：该日期不是交易日或数据未更新")

# 测试 4: 使用 query 方法
print("\n" + "=" * 70)
print("测试 4: 使用 query 方法获取数据")
print("=" * 70)

try:
    df = pro.query('daily', 
                   ts_code='000001.SZ',
                   start_date='20240301',
                   end_date='20240312')
    
    print(f"\n✅ query 方法成功!")
    print(f"   记录数：{len(df)} 条")
    print(f"\n📊 数据样例:")
    print(df.head(5).to_string())
    
except Exception as e:
    print(f"\n❌ query 方法失败：{e}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)

print("\n💡 说明:")
print("   - daily 接口只需要 120 积分（基础权限）")
print("   - 每分钟内可调取 500 次")
print("   - 每次最多 6000 条数据")
print("   - 数据在交易日 15-16 点更新")
print("   - 停牌期间不提供数据")
print("   - 此接口为未复权行情")
