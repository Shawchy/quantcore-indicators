"""
测试 Tushare 实时涨跌幅排名接口
接口：realtime_list
描述：获取全市场股票的实时涨跌幅排名（爬虫版）
权限：0 积分（需要 Tushare 账号）
数据源：sina（新浪）或 dc（东方财富）
"""
import tushare as ts
from pathlib import Path
from dotenv import load_dotenv
import os
import time
import pandas as pd

print("=" * 70)
print("测试 Tushare 实时涨跌幅排名接口 (realtime_list)")
print("=" * 70)

# 加载 Token
env_file = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_file)
token = os.getenv('TUSHARE_TOKEN')

print(f"\nToken: {token[:10]}...{token[-5:]}")

# 初始化 pro 接口
ts.set_token(token)

# 测试 1: 使用东方财富数据源
print("\n" + "=" * 70)
print("测试 1: 获取全市场实时涨跌幅排名 - 东方财富数据源")
print("=" * 70)
print("\n⏳ 正在获取数据，请稍候...（可能需要较长时间）")

start_time = time.time()

# 添加重试机制
max_retries = 3
df_dc = None

for attempt in range(max_retries):
    try:
        df_dc = ts.realtime_list(src='dc')
        break  # 成功后退出循环
    except Exception as e:
        if attempt < max_retries - 1:
            print(f"\n⚠️  第 {attempt + 1} 次尝试失败：{e}")
            print(f"   等待 5 秒后重试...")
            time.sleep(5)
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
        # 显示字段
        print(f"\n📊 数据字段:")
        print(f"   {', '.join(df_dc.columns.tolist())}")
        
        # 显示数据样例
        print(f"\n📋 数据样例 (前 10 条):")
        print(df_dc.head(10).to_string())
        
        # 基本统计
        print(f"\n📊 基本统计:")
        print(f"   股票数量：{len(df_dc)}")
        print(f"   平均涨跌幅：{df_dc['pct_change'].mean():.2f}%")
        print(f"   最高涨跌幅：{df_dc['pct_change'].max():.2f}%")
        print(f"   最低涨跌幅：{df_dc['pct_change'].min():.2f}%")
        
        # 涨跌幅分布
        print(f"\n📈 涨跌幅分布:")
        up_count = len(df_dc[df_dc['pct_change'] > 0])
        down_count = len(df_dc[df_dc['pct_change'] < 0])
        flat_count = len(df_dc[df_dc['pct_change'] == 0])
        limit_up = len(df_dc[df_dc['pct_change'] >= 9.9])
        limit_down = len(df_dc[df_dc['pct_change'] <= -9.9])
        
        print(f"   上涨：{up_count} 家 ({up_count/len(df_dc)*100:.1f}%)")
        print(f"   下跌：{down_count} 家 ({down_count/len(df_dc)*100:.1f}%)")
        print(f"   平盘：{flat_count} 家 ({flat_count/len(df_dc)*100:.1f}%)")
        print(f"   涨停：{limit_up} 家")
        print(f"   跌停：{limit_down} 家")
        
        # 涨幅榜前 10
        print(f"\n📊 涨幅榜前 10:")
        top10 = df_dc.nlargest(10, 'pct_change')[['ts_code', 'name', 'price', 'pct_change', 'volume', 'amount']]
        for idx, row in top10.iterrows():
            amount_str = f"{row['amount']/10000:.0f}万" if 'amount' in df_dc.columns and pd.notna(row['amount']) else "N/A"
            print(f"   {row['ts_code']} {row['name']}: {row['price']:.2f}元 "
                  f"{'+' if row['pct_change'] > 0 else ''}{row['pct_change']:.2f}% "
                  f"成交量:{row['volume']:,}手 成交额:{amount_str}")
        
        # 跌幅榜前 10
        print(f"\n📉 跌幅榜前 10:")
        bottom10 = df_dc.nsmallest(10, 'pct_change')[['ts_code', 'name', 'price', 'pct_change', 'volume', 'amount']]
        for idx, row in bottom10.iterrows():
            amount_str = f"{row['amount']/10000:.0f}万" if 'amount' in df_dc.columns and pd.notna(row['amount']) else "N/A"
            print(f"   {row['ts_code']} {row['name']}: {row['price']:.2f}元 "
                  f"{row['pct_change']:.2f}% "
                  f"成交量:{row['volume']:,}手 成交额:{amount_str}")
        
        # 成交额前 10
        if 'amount' in df_dc.columns:
            print(f"\n💰 成交额前 10:")
            top_amount = df_dc.nlargest(10, 'amount')[['ts_code', 'name', 'price', 'pct_change', 'amount']]
            for idx, row in top_amount.iterrows():
                print(f"   {row['ts_code']} {row['name']}: {row['amount']/100000000:.2f}亿元")
        
        # 换手率前 10
        if 'turnover_rate' in df_dc.columns:
            print(f"\n🔄 换手率前 10:")
            top_turnover = df_dc.nlargest(10, 'turnover_rate')[['ts_code', 'name', 'price', 'pct_change', 'turnover_rate']]
            for idx, row in top_turnover.iterrows():
                print(f"   {row['ts_code']} {row['name']}: {row['turnover_rate']:.2f}%")
        
        # 保存数据
        output_file = Path(__file__).parent / "realtime_list_dc.csv"
        df_dc.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 数据已保存到：{output_file}")

# 测试 2: 使用新浪数据源
print("\n" + "=" * 70)
print("测试 2: 获取全市场实时涨跌幅排名 - 新浪数据源")
print("=" * 70)
print("\n⏳ 正在获取数据，请稍候...")

start_time = time.time()

try:
    df_sina = ts.realtime_list(src='sina')
    
    elapsed = time.time() - start_time
    print(f"\n✅ 成功获取数据！耗时：{elapsed:.1f}秒")
    print(f"   记录数：{len(df_sina)} 条")
    
    if len(df_sina) > 0:
        # 显示字段
        print(f"\n📊 数据字段:")
        print(f"   {', '.join(df_sina.columns.tolist())}")
        
        # 显示数据样例
        print(f"\n📋 数据样例 (前 10 条):")
        print(df_sina.head(10).to_string())
        
        # 基本统计
        print(f"\n📊 基本统计:")
        print(f"   股票数量：{len(df_sina)}")
        if 'pct_change' in df_sina.columns:
            print(f"   平均涨跌幅：{df_sina['pct_change'].mean():.2f}%")
        
        # 保存数据
        output_file = Path(__file__).parent / "realtime_list_sina.csv"
        df_sina.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"\n💾 数据已保存到：{output_file}")
    
except Exception as e:
    print(f"\n❌ 获取数据失败：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("测试完成")
print("=" * 70)

print("\n💡 说明:")
print("   - realtime_list 接口 0 积分即可使用")
print("   - 需要 Tushare 账号")
print("   - 数据包括全市场所有股票的实时行情")
print("   - 支持两个数据源：sina（新浪）和 dc（东方财富）")
print("   - 采集需要一定时间，请耐心等待")
print("   - 数据来自爬虫，实时更新")
print("   - 适用于研究和学习的非商业用途")
