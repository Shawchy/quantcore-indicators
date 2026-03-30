"""
检查板块数据并修复板块类型
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, update
from app.storage.sqlite import get_session, SectorInfo

async def check_and_fix():
    async with get_session() as session:
        # 检查所有板块
        result = await session.execute(select(SectorInfo))
        sectors = result.scalars().all()
        
        print(f'板块总数：{len(sectors)}')
        print(f'\n当前板块类型分布:')
        sector_types = {}
        for s in sectors:
            st = s.sector_type
            if st not in sector_types:
                sector_types[st] = 0
            sector_types[st] += 1
        
        for st, count in sector_types.items():
            print(f"  {st}: {count}")
        
        # 检查是否有 sw 开头的代码（申万板块）
        sw_sectors = [s for s in sectors if s.code.startswith('801') or s.code.startswith('BK')]
        print(f'\n申万板块 (801/BK 开头): {len(sw_sectors)}')
        
        if sw_sectors:
            print(f'\n前 10 个申万板块:')
            for i, s in enumerate(sw_sectors[:10]):
                print(f"  {i+1}. {s.code} | {s.name:15} | {s.sector_type}")
        
        # 检查是否需要更新板块类型
        print(f'\n检查板块类型字段...')
        for s in sectors[:5]:
            print(f"  {s.code} | {s.name:15} | sector_type={s.sector_type}")

if __name__ == '__main__':
    asyncio.run(check_and_fix())
