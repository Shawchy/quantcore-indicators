"""
检查板块数据
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.storage.sqlite import get_session, SectorInfo

async def check():
    async with get_session() as session:
        result = await session.execute(select(SectorInfo))
        sectors = result.scalars().all()
        
        print(f'板块总数：{len(sectors)}')
        
        industry_count = len([s for s in sectors if s.sector_type == "industry"])
        concept_count = len([s for s in sectors if s.sector_type == "concept"])
        
        print(f'行业板块：{industry_count}')
        print(f'概念板块：{concept_count}')
        
        print(f'\n前 10 个板块:')
        for i, s in enumerate(sectors[:10]):
            print(f"  {i+1}. {s.code} | {s.name:15} | {s.sector_type}")
        
        print(f'\n所有板块类型统计:')
        sector_types = {}
        for s in sectors:
            st = s.sector_type
            if st not in sector_types:
                sector_types[st] = 0
            sector_types[st] += 1
        
        for st, count in sector_types.items():
            print(f"  {st}: {count}")

if __name__ == '__main__':
    asyncio.run(check())
