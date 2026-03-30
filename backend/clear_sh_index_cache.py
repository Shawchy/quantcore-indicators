"""
清除上证指数缓存
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.storage import cache_manager

async def clear_cache():
    print("=" * 80, flush=True)
    print("清除上证指数缓存")
    print("=" * 80, flush=True)
    
    # 清除 000001 的实时行情缓存
    cache_key = "quote_000001"
    try:
        await cache_manager.delete("realtime_quote", cache_key)
        print(f"✅ 已删除缓存：{cache_key}")
    except Exception as e:
        print(f"❌ 删除缓存失败 {cache_key}: {e}")
    
    print("\n" + "=" * 80, flush=True)
    print("缓存清除完成", flush=True)
    print("=" * 80, flush=True)

if __name__ == '__main__':
    asyncio.run(clear_cache())
