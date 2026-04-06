"""
简单测试 market-stats API
"""
import requests
import time

print("测试 market-stats API...")
start = time.time()

try:
    response = requests.get('http://localhost:8000/api/v1/screener/market-stats', timeout=20)
    elapsed = time.time() - start
    
    print(f"✅ 响应时间：{elapsed:.2f}秒")
    print(f"状态码：{response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ 数据获取成功！")
        print(f"total_stocks: {data.get('total_stocks')}")
        print(f"industry_distribution: {len(data.get('industry_distribution', {}))} 个行业")
        print(f"turnover: {data.get('turnover')}")
    else:
        print(f"❌ 状态码异常：{response.status_code}")
        
except requests.Timeout:
    elapsed = time.time() - start
    print(f"❌ 请求超时（{elapsed:.2f}秒）")
    print("\n可能的问题:")
    print("1. 后端正在获取 akshare 凭证（等待浏览器启动）")
    print("2. 数据库连接池耗尽")
    print("3. 网络问题")
except Exception as e:
    print(f"❌ 请求失败：{e}")
