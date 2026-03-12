"""
测试股票列表功能
使用新的 Tushare Token
"""
import tushare as ts
from pathlib import Path
from dotenv import load_dotenv
import os

print("=" * 70)
print("测试股票列表功能")
print("=" * 70)

# 加载 Token
env_file = Path(__file__).parent / "backend" / ".env"
load_dotenv(env_file)
token = os.getenv('TUSHARE_TOKEN')

print(f"\nToken: {token[:10]}...{token[-5:]}")
print(f"来源：{env_file}")

# 初始化 pro 接口
print("\n初始化 Tushare API...")
ts.set_token(token)
pro = ts.pro_api()

# 拉取股票列表数据
print("\n正在拉取股票列表...")
try:
    df = pro.stock_basic(**{
        "ts_code": "",
        "name": "",
        "exchange": "",
        "market": "",
        "is_hs": "",
        "list_status": "L",  # 只拉取上市状态的股票
        "limit": "",
        "offset": ""
    }, fields=[
        "ts_code",
        "symbol",
        "name",
        "area",
        "industry",
        "cnspell",
        "market",
        "list_date",
        "act_name",
        "act_ent_type"
    ])
    
    print(f"\n✅ 成功获取股票列表!")
    print(f"   总数：{len(df)} 只股票")
    
    # 显示前 10 条
    print(f"\n📊 前 10 只股票:")
    print(df.head(10).to_string())
    
    # 统计信息
    print(f"\n📈 市场分布:")
    print(df['market'].value_counts())
    
    print(f"\n📊 板块分布 (前 10):")
    print(df['industry'].value_counts().head(10))
    
    # 保存数据
    print(f"\n💾 保存数据到 CSV...")
    output_file = Path(__file__).parent / "stock_list.csv"
    df.to_csv(output_file, index=False, encoding='utf-8-sig')
    print(f"   ✅ 已保存到：{output_file}")
    
except Exception as e:
    print(f"\n❌ 获取数据失败：{e}")
    print(f"\n可能原因:")
    print(f"   1. Token 无效")
    print(f"   2. 积分不足")
    print(f"   3. 网络问题")

print("\n" + "=" * 70)
