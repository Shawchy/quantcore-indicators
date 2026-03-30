import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.adapters import data_source_manager

async def test():
    print("开始初始化数据源管理器...")
    await data_source_manager.initialize()
    print(f"初始化完成，当前使用：{data_source_manager._default_source}")
    
    print("\n获取行业板块列表...")
    sectors = await data_source_manager.get_sector_list(sector_type="industry")
    print(f"获取到 {len(sectors)} 个行业板块")
    
    if sectors:
        print(f"\n前 5 个板块:")
        for i, s in enumerate(sectors[:5], 1):
            print(f"  {i}. {s.code} - {s.name}")

if __name__ == '__main__':
    asyncio.run(test())
