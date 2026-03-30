"""
清除市场统计数据缓存
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from app.utils.api_cache_stats import api_cache

async def clear_cache():
    print("=" * 70)
    print("清除市场统计数据缓存")
    print("=" * 70)
    
    # 清除所有 api_stats 缓存
    await api_cache.clear('api_stats')
    print("✅ 已清除所有 api_stats 缓存")
    
    print("\n缓存已清除，下次请求将重新获取数据")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(clear_cache())
