"""
检查板块数据和 API
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.storage.sqlite import get_session, SectorInfo

async def check():
    async with get_session() as session:
        # 检查总数
        result = await session.execute(select(SectorInfo))
        sectors = result.scalars().all()
        
        print(f'📊 板块总数：{len(sectors)}')
        
        # 按类型统计
        sector_types = {}
        for s in sectors:
            st = s.sector_type
            if st not in sector_types:
                sector_types[st] = 0
            sector_types[st] += 1
        
        print(f'\n按类型分布:')
        for st, count in sorted(sector_types.items()):
            print(f"  {st:15} {count:5} 个")
        
        # 检查 industry 类型
        industry_sectors = [s for s in sectors if s.sector_type == "industry"]
        sw_sectors = [s for s in sectors if s.sector_type == "sw"]
        
        print(f'\n📋 详细检查:')
        print(f"  industry 类型：{len(industry_sectors)} 个")
        print(f"  sw 类型：{len(sw_sectors)} 个")
        
        if industry_sectors:
            print(f"\n  industry 类型前 10 个:")
            for i, s in enumerate(industry_sectors[:10]):
                print(f"    {i+1}. {s.code} | {s.name:15} | {s.sector_type}")
        
        if sw_sectors:
            print(f"\n  sw 类型前 10 个:")
            for i, s in enumerate(sw_sectors[:10]):
                print(f"    {i+1}. {s.code} | {s.name:15} | {s.sector_type}")

if __name__ == '__main__':
    asyncio.run(check())
