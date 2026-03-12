"""
测试 Tushare 实时盘口 TICK 快照接口
接口：realtime_quote
描述：A 股实时行情数据（爬虫版）
权限：0 积分（需要 Tushare 账号）
数据源：sina（新浪）或 dc（东方财富）
"""
import tushare as ts
from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime

print("=" * 70)
print("测试 Tushare 实时盘口接口 (realtime_quote)")
print("=" * 70)

# 加载 Token
env_file = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_file)
token = os.getenv('TUSHARE_TOKEN')

print(f"\nToken: {token[:10]}...{token[-5:]}")

# 初始化 pro 接口
ts.set_token(token)

# 测试 1: 使用新浪数据源获取单只股票
print("\n" + "=" * 70)
print("测试 1: 获取平安银行 (000001.SZ) 实时行情 - 新浪数据源")
print("=" * 70)

try:
    df = ts.realtime_quote(ts_code='000001.SZ', src='sina')
    
    print(f"\n✅ 成功获取数据!")
    print(f"   记录数：{len(df)} 条")
    
    if len(df) > 0:
        # 显示主要字段
        print(f"\n📊 实时行情:")
        for idx, row in df.iterrows():
            print(f"   股票：{row['NAME']} ({row['TS_CODE']})")
            print(f"   现价：¥{row['PRICE']:.2f}")
            print(f"   涨跌：{row['PRICE'] - row['PRE_CLOSE']:.2f} ({(row['PRICE'] - row['PRE_CLOSE'])/row['PRE_CLOSE']*100:.2f}%)")
            print(f"   开盘：¥{row['OPEN']:.2f}")
            print(f"   最高：¥{row['HIGH']:.2f}")
            print(f"   最低：¥{row['LOW']:.2f}")
            print(f"   昨收：¥{row['PRE_CLOSE']:.2f}")
            print(f"   成交量：{row['VOLUME']:,} 股")
            print(f"   成交额：¥{row['AMOUNT']:,.2f} 元")
            print(f"   买一：¥{row['B1_P']:.2f} × {row['B1_V']:,} 手")
            print(f"   卖一：¥{row['A1_P']:.2f} × {row['A1_V']:,} 手")
            print(f"   时间：{row['DATE']} {row['TIME']}")
    
    # 保存数据
    output_file = Path(__file__).parent / "realtime_quote.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"\n💾 数据已保存到：{output_file}")
    
except Exception as e:
    print(f"\n❌ 获取数据失败：{e}")
    import traceback
    traceback.print_exc()

# 测试 2: 使用新浪数据源获取多只股票
print("\n" + "=" * 70)
print("测试 2: 获取多只股票实时行情 - 新浪数据源")
print("=" * 70)

try:
    # 多个股票代码（逗号分隔，最多 50 个）
    codes = '600000.SH,000001.SZ,000002.SZ,601318.SH,600519.SH'
    
    df = ts.realtime_quote(ts_code=codes, src='sina')
    
    print(f"\n✅ 成功获取数据!")
    print(f"   股票数量：{len(df)} 只")
    
    # 显示每只股票
    print(f"\n📊 实时行情概览:")
    for idx, row in df.iterrows():
        change = row['PRICE'] - row['PRE_CLOSE']
        change_pct = change / row['PRE_CLOSE'] * 100 if row['PRE_CLOSE'] > 0 else 0
        symbol = '📈' if change > 0 else '📉' if change < 0 else '➖'
        print(f"   {symbol} {row['NAME']} ({row['TS_CODE']}): ¥{row['PRICE']:.2f} "
              f"{'+' if change > 0 else ''}{change:.2f} ({change_pct:.2f}%)")
    
    # 显示详细数据
    print(f"\n📋 详细数据:")
    print(df[['NAME', 'TS_CODE', 'PRICE', 'B1_P', 'B1_V', 'A1_P', 'A1_V', 'VOLUME']].to_string())
    
except Exception as e:
    print(f"\n❌ 获取数据失败：{e}")
    import traceback
    traceback.print_exc()

# 测试 3: 使用东方财富数据源
print("\n" + "=" * 70)
print("测试 3: 获取浦发银行 (600000.SH) 实时行情 - 东方财富数据源")
print("=" * 70)

try:
    # 东财数据源只支持单只股票
    df = ts.realtime_quote(ts_code='600000.SH', src='dc')
    
    print(f"\n✅ 成功获取数据!")
    print(f"   记录数：{len(df)} 条")
    
    if len(df) > 0:
        row = df.iloc[0]
        print(f"\n📊 {row['NAME']} ({row['TS_CODE']}) 实时行情:")
        print(f"   现价：¥{row['PRICE']:.2f}")
        print(f"   涨跌：{row['PRICE'] - row['PRE_CLOSE']:.2f} ({(row['PRICE'] - row['PRE_CLOSE'])/row['PRE_CLOSE']*100:.2f}%)")
        print(f"   成交量：{row['VOLUME']:,} 手")
        print(f"   成交额：¥{row['AMOUNT']:,.2f} 元")
        print(f"   时间：{row['DATE']} {row['TIME']}")
        
        # 显示买卖盘
        print(f"\n📋 五档盘口:")
        print(f"   卖五：¥{row['A5_P']:.2f} × {row['A5_V']:,} 手")
        print(f"   卖四：¥{row['A4_P']:.2f} × {row['A4_V']:,} 手")
        print(f"   卖三：¥{row['A3_P']:.2f} × {row['A3_V']:,} 手")
        print(f"   卖二：¥{row['A2_P']:.2f} × {row['A2_V']:,} 手")
        print(f"   卖一：¥{row['A1_P']:.2f} × {row['A1_V']:,} 手")
        print(f"   -----")
        print(f"   买一：¥{row['B1_P']:.2f} × {row['B1_V']:,} 手")
        print(f"   买二：¥{row['B2_P']:.2f} × {row['B2_V']:,} 手")
        print(f"   买三：¥{row['B3_P']:.2f} × {row['B3_V']:,} 手")
        print(f"   买四：¥{row['B4_P']:.2f} × {row['B4_V']:,} 手")
        print(f"   买五：¥{row['B5_P']:.2f} × {row['B5_V']:,} 手")
    
except Exception as e:
    print(f"\n❌ 获取数据失败：{e}")
    import traceback
    traceback.print_exc()

# 测试 4: 获取上证指数
print("\n" + "=" * 70)
print("测试 4: 获取上证指数 (000001.SH) 实时行情")
print("=" * 70)

try:
    df = ts.realtime_quote(ts_code='000001.SH', src='sina')
    
    print(f"\n✅ 成功获取数据!")
    
    if len(df) > 0:
        row = df.iloc[0]
        print(f"\n📊 上证指数实时行情:")
        print(f"   点位：{row['PRICE']:.2f}")
        print(f"   涨跌：{row['PRICE'] - row['PRE_CLOSE']:.2f} "
              f"({(row['PRICE'] - row['PRE_CLOSE'])/row['PRE_CLOSE']*100:.2f}%)")
        print(f"   今开：{row['OPEN']:.2f}")
        print(f"   最高：{row['HIGH']:.2f}")
        print(f"   最低：{row['LOW']:.2f}")
        print(f"   昨收：{row['PRE_CLOSE']:.2f}")
        print(f"   成交量：{row['VOLUME']:,} 股")
        print(f"   成交额：¥{row['AMOUNT']:,.2f} 元")
        print(f"   时间：{row['DATE']} {row['TIME']}")
    
except Exception as e:
    print(f"\n❌ 获取数据失败：{e}")

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)

print("\n💡 说明:")
print("   - realtime_quote 接口 0 积分即可使用")
print("   - 需要 Tushare 账号")
print("   - 支持两个数据源：sina（新浪）和 dc（东方财富）")
print("   - sina 支持批量获取（最多 50 只股票）")
print("   - dc 只支持单只股票")
print("   - 数据来自爬虫，实时更新")
print("   - 适用于研究和学习的非商业用途")
