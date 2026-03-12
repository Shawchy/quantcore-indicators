"""
测试 Tushare 交易日历接口
接口：trade_cal
描述：获取各大交易所交易日历数据
积分：需要 2000 积分
"""
import tushare as ts
from pathlib import Path
from dotenv import load_dotenv
import os
from datetime import datetime

print("=" * 70)
print("测试 Tushare 交易日历接口 (trade_cal)")
print("=" * 70)

# 加载 Token
env_file = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_file)
token = os.getenv('TUSHARE_TOKEN')

print(f"\nToken: {token[:10]}...{token[-5:]}")

# 初始化 pro 接口
ts.set_token(token)
pro = ts.pro_api()

# 测试 1: 获取 2024 年上交所交易日历
print("\n" + "=" * 70)
print("测试 1: 获取 2024 年上交所交易日历")
print("=" * 70)

try:
    df = pro.trade_cal(
        exchange='SSE',
        start_date='20240101',
        end_date='20241231'
    )
    
    print(f"\n✅ 成功获取数据!")
    print(f"   记录数：{len(df)} 条")
    print(f"   交易所：{df['exchange'].iloc[0] if len(df) > 0 else 'N/A'}")
    
    # 显示前 20 条
    print(f"\n📊 前 20 条记录:")
    print(df.head(20).to_string())
    
    # 统计
    total_days = len(df)
    open_days = len(df[df['is_open'] == '1'])
    closed_days = len(df[df['is_open'] == '0'])
    
    print(f"\n📈 统计信息:")
    print(f"   总天数：{total_days} 天")
    print(f"   交易日：{open_days} 天")
    print(f"   休市日：{closed_days} 天")
    print(f"   交易日占比：{open_days/total_days*100:.1f}%")
    
    # 保存数据
    output_file = Path(__file__).parent / "trade_cal_2024.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 数据已保存到：{output_file}")
    
except Exception as e:
    print(f"\n❌ 获取数据失败：{e}")
    print(f"\n可能原因:")
    print(f"   1. Token 积分不足（需要 2000 积分）")
    print(f"   2. Token 无效")
    print(f"   3. 网络问题")
    print(f"\n💡 建议:")
    print(f"   - 当前 Token 积分为 120 分")
    print(f"   - 交易日历接口需要 2000 积分")
    print(f"   - 可以使用本地计算方式估算交易日历")

# 测试 2: 获取最近 30 天数据（减少数据量）
print("\n" + "=" * 70)
print("测试 2: 获取 2024 年 3 月交易日历")
print("=" * 70)

try:
    df = pro.trade_cal(
        exchange='SSE',
        start_date='20240301',
        end_date='20240331'
    )
    
    print(f"\n✅ 成功获取数据!")
    print(f"   记录数：{len(df)} 条")
    
    if len(df) > 0:
        print(f"\n📊 数据样例:")
        print(df.head(10).to_string())
        
        # 筛选交易日
        trading_days = df[df['is_open'] == '1']
        print(f"\n📅 3 月份交易日：{len(trading_days)} 天")
        print(f"   日期列表：{', '.join(trading_days['cal_date'].tolist())}")
    
except Exception as e:
    print(f"\n❌ 获取数据失败：{e}")

# 测试 3: 使用 query 方法
print("\n" + "=" * 70)
print("测试 3: 使用 query 方法获取")
print("=" * 70)

try:
    df = pro.query('trade_cal', 
                   exchange='SSE',
                   start_date='20240101', 
                   end_date='20240131')
    
    print(f"\n✅ query 方法成功!")
    print(f"   记录数：{len(df)} 条")
    
except Exception as e:
    print(f"\n❌ query 方法失败：{e}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)

print("\n💡 说明:")
print("   - trade_cal 接口需要 2000 积分")
print("   - 当前 Token 积分为 120 分，可能无法访问")
print("   - 如果无法访问，可以使用以下方式:")
print("     1. 升级 Tushare 积分到 2000 分")
print("     2. 使用本地计算方式估算交易日历（排除周末和节假日）")
print("     3. 使用 AkShare 的交易日历接口（免费）")
