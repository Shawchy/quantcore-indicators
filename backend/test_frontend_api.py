"""
测试前端 API 调用
"""
import requests
import json

print("=" * 70)
print("测试前端 API 调用")
print("=" * 70)

# 模拟前端调用
url = 'http://localhost:8000/api/v1/screener/market-stats'
print(f"\n请求 URL: {url}")

try:
    response = requests.get(url, timeout=20)
    
    print(f"\n响应状态码：{response.status_code}")
    print(f"响应头 Content-Type: {response.headers.get('Content-Type')}")
    
    # 检查响应内容
    if response.status_code == 200:
        data = response.json()
        
        print(f"\n✅ JSON 解析成功")
        print(f"\n完整响应:")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # 检查数据结构
        print(f"\n数据结构分析:")
        print(f"  - 根对象 keys: {list(data.keys())}")
        
        if 'data' in data:
            print(f"  - data 字段类型：{type(data['data'])}")
            print(f"  - data 字段 keys: {list(data['data'].keys())}")
            print(f"  - total_stocks: {data['data'].get('total_stocks')}")
            print(f"  - industry_distribution: {data['data'].get('industry_distribution')}")
            print(f"  - turnover: {data['data'].get('turnover')}")
        else:
            print(f"  - ❌ 没有 data 字段")
            print(f"  - 实际返回：{data}")
    else:
        print(f"\n❌ 状态码异常：{response.status_code}")
        print(f"响应内容：{response.text[:500]}")
        
except requests.Timeout:
    print(f"\n❌ 请求超时（>20 秒）")
except Exception as e:
    print(f"\n❌ 请求失败：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
