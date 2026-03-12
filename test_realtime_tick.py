"""
测试 Tushare 实时成交数据接口
接口：realtime_tick
描述：获取股票当日开盘以来的所有分笔成交数据（爬虫版）
权限：0 积分（需要 Tushare 账号）
数据源：sina（新浪）或 dc（东方财富）
"""
import tushare as ts
from pathlib import Path
from dotenv import load_dotenv
import os
import pandas as pd
from datetime import datetime
import time

print("=" * 70)
print("测试 Tushare 实时成交数据接口 (realtime_tick)")
print("=" * 70)

# 加载 Token
env_file = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_file)
token = os.getenv('TUSHARE_TOKEN')

print(f"\nToken: {token[:10]}...{token[-5:]}")

# 初始化 pro 接口
ts.set_token(token)

# 测试 1: 使用新浪数据源获取单只股票
# 注意：新浪数据源存在 Tushare 库解析 bug，已跳过
print("\n" + "=" * 70)
print("测试 1: 新浪数据源测试 - 已跳过")
print("=" * 70)
print("\n⚠️  跳过原因：Tushare 库在解析新浪数据时存在 bug")
print("   错误信息：ValueError: could not convert string to float: '该股票没有交易数据'")
print("\n💡 建议使用东方财富数据源 (src='dc')")

# 测试 2: 使用东方财富数据源
print("\n" + "=" * 70)
print("测试 2: 获取浦发银行 (600000.SH) 实时成交数据 - 东方财富数据源")
print("=" * 70)
print("\n⏳ 正在获取数据，请稍候...")

start_time = time.time()

# 添加重试机制
max_retries = 3
df_dc = None

for attempt in range(max_retries):
    try:
        df_dc = ts.realtime_tick(ts_code='600000.SH', src='dc')
        break  # 成功后退出循环
    except Exception as e:
        if attempt < max_retries - 1:
            print(f"\n⚠️  第 {attempt + 1} 次尝试失败：{e}")
            print(f"   等待 3 秒后重试...")
            time.sleep(3)
        else:
            print(f"\n❌ 获取数据失败（已重试{max_retries}次）：{e}")
            import traceback
            traceback.print_exc()
            break

if df_dc is not None:
    elapsed = time.time() - start_time
    print(f"\n✅ 成功获取数据！耗时：{elapsed:.1f}秒")
    print(f"   记录数：{len(df_dc)} 条")
    
    if len(df_dc) > 0:
        # 显示基本信息
        print(f"\n📊 数据概览:")
        print(f"   时间范围：{df_dc['TIME'].iloc[0]} 到 {df_dc['TIME'].iloc[-1]}")
        print(f"   总成交量：{df_dc['VOLUME'].sum():,} 手")
        
        # 东方财富数据源没有 AMOUNT 字段，需要计算
        if 'AMOUNT' in df_dc.columns:
            print(f"   总成交额：¥{df_dc['AMOUNT'].sum():,.0f} 元")
        else:
            # 估算成交额 = 成交量 * 均价
            avg_price = df_dc['PRICE'].mean()
            estimated_amount = df_dc['VOLUME'].sum() * avg_price * 100  # 1 手=100 股
            print(f"   估算成交额：¥{estimated_amount:,.0f} 元 (基于均价估算)")
        
        # 统计买卖盘
        buy_count = len(df_dc[df_dc['TYPE'] == '买盘'])
        sell_count = len(df_dc[df_dc['TYPE'] == '卖盘'])
        neutral_count = len(df_dc[df_dc['TYPE'] == '中性'])
        
        print(f"\n📈 成交类型统计:")
        print(f"   买盘：{buy_count} 笔 ({buy_count/len(df_dc)*100:.1f}%)")
        print(f"   卖盘：{sell_count} 笔 ({sell_count/len(df_dc)*100:.1f}%)")
        print(f"   中性：{neutral_count} 笔 ({neutral_count/len(df_dc)*100:.1f}%)")
        
        # 显示样例
        print(f"\n📋 数据样例 (前 10 条):")
        print(df_dc.head(10).to_string())
        
        # 价格统计
        print(f"\n📊 价格统计:")
        print(f"   最高价：¥{df_dc['PRICE'].max():.2f}")
        print(f"   最低价：¥{df_dc['PRICE'].min():.2f}")
        print(f"   最新价：¥{df_dc['PRICE'].iloc[-1]:.2f}")
        
        # 大单统计（不需要 AMOUNT 字段）
        large_orders = df_dc[df_dc['VOLUME'] >= 1000]
        print(f"\n📈 大单统计 (≥1000 手):")
        print(f"   大单数量：{len(large_orders)} 笔")
        if len(large_orders) > 0:
            print(f"   最大单笔：{large_orders['VOLUME'].max():,} 手")
            print(f"   大单总成交：{large_orders['VOLUME'].sum():,} 手")
            print(f"\n   最大 10 笔成交:")
            if 'AMOUNT' in large_orders.columns:
                print(large_orders.nlargest(10, 'VOLUME')[['TIME', 'PRICE', 'VOLUME', 'AMOUNT', 'TYPE']].to_string())
            else:
                print(large_orders.nlargest(10, 'VOLUME')[['TIME', 'PRICE', 'VOLUME', 'TYPE']].to_string())
    
    # 保存数据
    output_file_dc = Path(__file__).parent / "realtime_tick_dc.csv"
    df_dc.to_csv(output_file_dc, index=False, encoding='utf-8-sig')
    print(f"\n💾 数据已保存到：{output_file_dc}")

# 测试 3: 分析成交活跃度（使用东方财富数据源）
print("\n" + "=" * 70)
print("测试 3: 成交活跃度分析 - 东方财富数据源")
print("=" * 70)

try:
    # 使用东方财富数据源的数据
    if 'df_dc' in locals() and len(df_dc) > 0:
        analysis_df = df_dc.copy()
        
        # 按小时统计
        analysis_df['HOUR'] = analysis_df['TIME'].str[:2].astype(int)
        
        # 检查是否有 AMOUNT 字段
        has_amount = 'AMOUNT' in analysis_df.columns
        
        if has_amount:
            hourly_stats = analysis_df.groupby('HOUR').agg({
                'VOLUME': 'sum',
                'AMOUNT': 'sum',
                'PRICE': 'mean'
            }).reset_index()
        else:
            # 没有 AMOUNT 字段时，只统计成交量
            hourly_stats = analysis_df.groupby('HOUR').agg({
                'VOLUME': 'sum',
                'PRICE': 'mean'
            }).reset_index()
            hourly_stats['AMOUNT'] = hourly_stats['VOLUME'] * hourly_stats['PRICE'] * 100  # 估算
        
        print(f"\n📊 分时段成交统计:")
        print(f"{'时段':<10} {'成交量 (手)':<15} {'成交额 (万元)':<15} {'均价':<10}")
        print("-" * 50)
        for idx, row in hourly_stats.iterrows():
            hour = int(row['HOUR'])
            if 9 <= hour <= 15:  # 只显示交易时段
                print(f"{hour:02d}:00      {row['VOLUME']:>12,}    {row['AMOUNT']/10000:>12.0f}    {row['PRICE']:>8.2f}")
        
        # 找出最活跃的 5 分钟
        analysis_df['MINUTE'] = analysis_df['TIME'].str[:5]
        
        if has_amount:
            minute_stats = analysis_df.groupby('MINUTE').agg({
                'VOLUME': 'sum',
                'AMOUNT': 'sum'
            }).reset_index()
        else:
            minute_stats = analysis_df.groupby('MINUTE').agg({
                'VOLUME': 'sum'
            }).reset_index()
            minute_stats['AMOUNT'] = minute_stats['VOLUME'] * analysis_df.groupby('MINUTE')['PRICE'].mean().values * 100
        
        top5_minutes = minute_stats.nlargest(5, 'VOLUME')
        print(f"\n📈 最活跃的 5 个分钟:")
        for idx, row in top5_minutes.iterrows():
            print(f"   {row['MINUTE']} - 成交量：{row['VOLUME']:,} 手，成交额：¥{row['AMOUNT']/10000:.0f} 万")
    
except Exception as e:
    print(f"\n❌ 分析失败：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)

print("\n💡 说明:")
print("   - realtime_tick 接口 0 积分即可使用")
print("   - 需要 Tushare 账号")
print("   - 数据包括当日开盘以来的所有分笔成交")
print("   - 支持两个数据源：sina（新浪）和 dc（东方财富）")
print("   - 采集需要一定时间，请耐心等待")
print("   - 数据来自爬虫，实时更新")
print("   - 适用于研究和学习的非商业用途")
