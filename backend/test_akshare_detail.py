"""
测试 akshare 股票详细信息接口
"""
import akshare as ak

# 测试获取单只股票的详细信息
code = "000001"
print(f"测试获取 {code} 的详细信息...")

try:
    df = ak.stock_individual_info_em(symbol=code)
    print(f"\n✅ 获取成功！共 {len(df)} 条信息")
    print(f"\n数据内容:")
    print(df)
    
    # 转换为字典
    info = {}
    for _, row in df.iterrows():
        item = row.get('item', '')
        value = row.get('value', '')
        info[item] = value
    
    print(f"\n提取的关键信息:")
    print(f"  行业：{info.get('行业', 'N/A')}")
    print(f"  地区：{info.get('地区', 'N/A')}")
    print(f"  上市日期：{info.get('上市日期', 'N/A')}")
    print(f"  总股本：{info.get('总股本', 'N/A')}")
    print(f"  流通股：{info.get('流通股', 'N/A')}")
    
except Exception as e:
    print(f"\n❌ 获取失败：{e}")
    import traceback
    traceback.print_exc()
