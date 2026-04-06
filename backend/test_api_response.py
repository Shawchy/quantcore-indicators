"""
测试 API 返回数据格式
"""
import requests
import json

# 调用 API
response = requests.get('http://localhost:8000/api/v1/screener/market-stats')

print("=" * 70)
print("API 响应测试")
print("=" * 70)

print(f"\n状态码：{response.status_code}")
print(f"响应头：{dict(response.headers)}")

try:
    data = response.json()
    print(f"\n✅ JSON 解析成功")
    print(f"\n完整响应数据:")
    print(json.dumps(data, indent=2, ensure_ascii=False))
    
    # 检查数据结构
    if 'data' in data:
        print(f"\n✅ 包含 'data' 字段")
        data_content = data['data']
        
        print(f"\n'data' 字段内容:")
        print(json.dumps(data_content, indent=2, ensure_ascii=False))
        
        # 检查关键字段
        print(f"\n关键字段检查:")
        print(f"  - total_stocks: {data_content.get('total_stocks', '❌ 缺失')}")
        print(f"  - industry_distribution: {data_content.get('industry_distribution', '❌ 缺失')}")
        print(f"  - top_industries: {data_content.get('top_industries', '❌ 缺失')}")
        print(f"  - turnover: {data_content.get('turnover', '❌ 缺失')}")
        print(f"  - trade_date: {data_content.get('trade_date', '❌ 缺失')}")
        
        # 检查类型
        print(f"\n字段类型检查:")
        print(f"  - total_stocks 类型：{type(data_content.get('total_stocks')).__name__}")
        print(f"  - industry_distribution 类型：{type(data_content.get('industry_distribution')).__name__}")
        print(f"  - top_industries 类型：{type(data_content.get('top_industries')).__name__}")
        
    else:
        print(f"\n❌ 缺少 'data' 字段")
        print(f"实际返回：{data}")
        
except Exception as e:
    print(f"\n❌ JSON 解析失败：{e}")
    print(f"响应内容：{response.text}")

print("\n" + "=" * 70)
