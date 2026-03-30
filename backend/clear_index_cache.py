"""
清除指数数据的旧缓存，确保使用新的涨跌计算逻辑
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from app.storage.cache import cache_manager

async def clear_index_cache():
    """清除所有指数相关的缓存"""
    index_codes = ['000001', '399001', '399006', '000016', '000300']
    
    print("开始清除指数数据缓存...")
    for code in index_codes:
        cache_key = f"quote:{code}"
        await cache_manager.delete('api_stats', cache_key)
        print(f"  ✅ 已清除 {code} 的缓存：{cache_key}")
    
    print("\n所有指数缓存已清除，下次请求将使用新的计算逻辑")

if __name__ == '__main__':
    asyncio.run(clear_index_cache())
