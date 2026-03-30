"""
简单的板块数据初始化脚本 - 带错误处理
"""
import asyncio
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def main():
    try:
        print("=" * 80, flush=True)
        print("板块数据初始化脚本", flush=True)
        print("=" * 80, flush=True)
        
        from app.adapters import data_source_manager
        from app.storage.sqlite import get_session, SectorInfo as SectorInfoDB
        from sqlalchemy import select
        
        # 初始化数据源管理器
        print("\n初始化数据源管理器...", flush=True)
        await data_source_manager.initialize()
        print(f"✅ 当前使用数据源：{data_source_manager._default_source}\n", flush=True)
        
        # 获取行业板块
        print("获取行业板块列表...", flush=True)
        sectors = await data_source_manager.get_sector_list(sector_type="industry")
        print(f"✅ 获取到 {len(sectors)} 个行业板块\n", flush=True)
        
        if sectors:
            print(f"前 5 个板块:", flush=True)
            for i, s in enumerate(sectors[:5], 1):
                print(f"  {i}. {s.code} - {s.name}", flush=True)
            
            # 保存到数据库
            print("\n保存到数据库...", flush=True)
            async with get_session() as session:
                saved_count = 0
                for sector in sectors:
                    existing = await session.execute(
                        select(SectorInfoDB).where(SectorInfoDB.code == sector.code)
                    )
                    if existing.scalar_one_or_none():
                        continue
                    
                    sector_db = SectorInfoDB(
                        code=sector.code,
                        name=sector.name,
                        sector_type="industry",
                        change_pct=sector.change_pct or 0,
                        volume=sector.volume or 0,
                        amount=sector.amount or 0
                    )
                    session.add(sector_db)
                    saved_count += 1
                
                await session.commit()
                print(f"✅ 新增 {saved_count} 个板块到数据库\n", flush=True)
        
        print("=" * 80, flush=True)
        print("完成", flush=True)
        print("=" * 80, flush=True)
        return True
        
    except Exception as e:
        print(f"\n❌ 错误：{e}\n", flush=True)
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
