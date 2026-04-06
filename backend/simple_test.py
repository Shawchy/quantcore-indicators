"""
简单测试 stock_individual_info_em API
"""

import akshare as ak
import pandas as pd

print("="*60)
print("测试 stock_individual_info_em API")
print("="*60)

# 测试股票：贵州茅台
code = "600519"
print(f"\n📊 测试股票：{code}（贵州茅台）")

try:
    print(f"\n⏳ 调用 ak.stock_individual_info_em('{code}')...")
    df = ak.stock_individual_info_em(symbol=code)
    
    if df is not None and not df.empty:
        print(f"✅ 获取成功！")
        print(f"\n数据预览:")
        print(df)
        
        # 转换为字典
        info_dict = dict(zip(df["item"], df["value"]))
        print(f"\n📋 详细信息:")
        for key, value in info_dict.items():
            print(f"  {key}: {value}")
    else:
        print(f"❌ 返回空数据")
        
except Exception as e:
    print(f"❌ 测试失败：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*60)
