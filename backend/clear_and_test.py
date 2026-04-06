"""
清除缓存并测试
"""
import asyncio
import requests

async def clear_cache():
    from app.utils.api_cache_stats import api_cache
    
    print("清除 api_stats 缓存...")
    await api_cache.clear('api_stats')
    print("✅ 缓存已清除")

if __name__ == '__main__':
    asyncio.run(clear_cache())
    
    print("\n等待 1 秒...")
    import time
    time.sleep(1)
    
    print("\n测试 API...")
    response = requests.get('http://localhost:8000/api/v1/screener/market-stats', timeout=20)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ API 响应成功！")
        print(f"total_stocks: {data['data']['total_stocks']}")
        print(f"industry_distribution: {len(data['data']['industry_distribution'])} 个行业")
        print(f"top_industries: {len(data['data']['top_industries'])} 个")
        print(f"turnover: {data['data']['turnover']}")
    else:
        print(f"❌ API 失败：{response.status_code}")
        print(f"响应：{response.text[:200]}")
