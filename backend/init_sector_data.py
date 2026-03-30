"""
初始化板块数据脚本
从数据源获取板块列表并保存到数据库
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.storage.sqlite import get_session, SectorInfo as SectorInfoDB
from app.adapters import data_source_manager
from loguru import logger

async def init_sector_data():
    """初始化板块数据"""
    # 先初始化数据源管理器
    await data_source_manager.initialize()
    print(f"✅ 数据源管理器初始化完成，当前使用：{data_source_manager._default_source}\n")
    
    print("=" * 80)
    print("初始化板块数据")
    print("=" * 80)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 80)
    
    total_saved = 0
    
    # 1. 初始化行业板块
    print("\n【1】初始化行业板块...")
    try:
        sectors = await data_source_manager.get_sector_list(sector_type="industry")
        
        if not sectors:
            print("  ❌ 获取行业板块列表失败")
        else:
            print(f"  ✅ 获取到 {len(sectors)} 个行业板块")
            
            # 保存到数据库
            async with get_session() as session:
                saved_count = 0
                for sector in sectors:
                    # 检查是否已存在
                    existing = await session.execute(
                        select(SectorInfoDB).where(SectorInfoDB.code == sector.code)
                    )
                    if existing.scalar_one_or_none():
                        continue
                    
                    # 创建新记录
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
                print(f"  ✅ 新增 {saved_count} 个行业板块到数据库")
                total_saved += saved_count
                
    except Exception as e:
        print(f"  ❌ 初始化行业板块失败：{e}")
        logger.exception(e)
    
    # 2. 初始化概念板块
    print("\n【2】初始化概念板块...")
    try:
        sectors = await data_source_manager.get_sector_list(sector_type="concept")
        
        if not sectors:
            print("  ❌ 获取概念板块列表失败")
        else:
            print(f"  ✅ 获取到 {len(sectors)} 个概念板块")
            
            # 保存到数据库
            async with get_session() as session:
                saved_count = 0
                for sector in sectors:
                    # 检查是否已存在
                    existing = await session.execute(
                        select(SectorInfoDB).where(SectorInfoDB.code == sector.code)
                    )
                    if existing.scalar_one_or_none():
                        continue
                    
                    # 创建新记录
                    sector_db = SectorInfoDB(
                        code=sector.code,
                        name=sector.name,
                        sector_type="concept",
                        change_pct=sector.change_pct or 0,
                        volume=sector.volume or 0,
                        amount=sector.amount or 0
                    )
                    session.add(sector_db)
                    saved_count += 1
                
                await session.commit()
                print(f"  ✅ 新增 {saved_count} 个概念板块到数据库")
                total_saved += saved_count
                
    except Exception as e:
        print(f"  ❌ 初始化概念板块失败：{e}")
        logger.exception(e)
    
    # 3. 统计结果
    print("\n" + "=" * 80)
    print("初始化完成")
    print("=" * 80)
    print(f"总共保存：{total_saved} 个板块")
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    # 4. 验证数据
    print("\n【验证】检查数据库中的板块数据...")
    async with get_session() as session:
        result = await session.execute(select(SectorInfoDB))
        all_sectors = result.scalars().all()
        
        industry_count = len([s for s in all_sectors if s.sector_type == "industry"])
        concept_count = len([s for s in all_sectors if s.sector_type == "concept"])
        
        print(f"  ✅ 数据库中共有 {len(all_sectors)} 个板块")
        print(f"     - 行业板块：{industry_count} 个")
        print(f"     - 概念板块：{concept_count} 个")
        
        if all_sectors:
            print("\n  前 10 个板块:")
            for i, sector in enumerate(all_sectors[:10], 1):
                print(f"    {i:2}. {sector.code} | {sector.name:15} | {sector.sector_type}")
    
    return total_saved > 0

if __name__ == '__main__':
    try:
        print("开始执行脚本...\n", flush=True)
        success = asyncio.run(init_sector_data())
        print(f"\n脚本执行完成，结果：{'成功' if success else '失败'}\n", flush=True)
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 脚本执行失败：{e}\n", flush=True)
        logger.exception(e)
        sys.exit(1)
