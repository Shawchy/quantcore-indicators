"""
清除板块缓存
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.storage import cache_manager

async def clear_cache():
    print("=" * 80, flush=True)
    print("清除板块缓存")
    print("=" * 80, flush=True)
    
    # 清除 sector 相关的所有缓存
    cache_keys = [
        "sector_list_sw",
        "sector_list_industry",
        "sector_list_concept",
        "sector_ranking_sw_change_pct_20",
        "sector_ranking_industry_change_pct_20",
        "sector_ranking_concept_change_pct_20",
    ]
    
    for key in cache_keys:
        try:
            await cache_manager.delete("sector", key)
            print(f"✅ 已删除缓存：{key}")
        except Exception as e:
            print(f"❌ 删除缓存失败 {key}: {e}")
    
    print("\n" + "=" * 80, flush=True)
    print("缓存清除完成", flush=True)
    print("=" * 80, flush=True)

if __name__ == '__main__':
    asyncio.run(clear_cache())
