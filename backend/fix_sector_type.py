"""
修复板块数据类型
将现有的 industry 类型板块重新分类为 sw (申万行业)
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, update
from app.storage.sqlite import get_session, SectorInfo

async def fix_sector_type():
    """修复板块类型"""
    print("=" * 80, flush=True)
    print("修复板块数据类型")
    print("=" * 80, flush=True)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("-" * 80, flush=True)
    
    async with get_session() as session:
        # 检查现有数据
        result = await session.execute(select(SectorInfo))
        sectors = result.scalars().all()
        
        print(f'\n当前板块总数：{len(sectors)}')
        
        # 统计现有类型
        sector_types = {}
        for s in sectors:
            st = s.sector_type
            if st not in sector_types:
                sector_types[st] = 0
            sector_types[st] += 1
        
        print(f'当前板块类型分布:')
        for st, count in sector_types.items():
            print(f"  {st}: {count}")
        
        # 将 industry 类型重命名为 sw (申万行业)
        print(f'\n🔧 将 industry 类型更新为 sw (申万行业)...', flush=True)
        await session.execute(
            update(SectorInfo)
            .where(SectorInfo.sector_type == "industry")
            .values(sector_type="sw")
        )
        await session.commit()
        print(f'✅ 更新完成', flush=True)
        
        # 验证结果
        result = await session.execute(select(SectorInfo))
        sectors = result.scalars().all()
        
        print(f'\n✅ 修复后板块总数：{len(sectors)}')
        
        # 重新统计
        sector_types = {}
        for s in sectors:
            st = s.sector_type
            if st not in sector_types:
                sector_types[st] = 0
            sector_types[st] += 1
        
        print(f'修复后板块类型分布:')
        for st, count in sorted(sector_types.items()):
            print(f"  {st:15} {count:5} 个")
        
        # 显示前 20 个板块
        print(f'\n前 20 个板块示例:')
        for i, sector in enumerate(sectors[:20], 1):
            print(f"  {i:2}. {sector.code} | {sector.name:15} | {sector.sector_type}")
    
    print("\n" + "=" * 80, flush=True)
    print("完成", flush=True)
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 80, flush=True)

if __name__ == '__main__':
    asyncio.run(fix_sector_type())
