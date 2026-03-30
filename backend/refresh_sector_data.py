"""
重新获取并正确分类板块数据
包括：申万一级行业、申万二级行业、概念板块等
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, delete
from app.storage.sqlite import get_session, SectorInfo, SectorInfo as SectorInfoDB
from app.adapters import data_source_manager
from loguru import logger

async def refresh_sector_data():
    """刷新板块数据"""
    print("=" * 80, flush=True)
    print("刷新板块数据")
    print("=" * 80, flush=True)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("-" * 80, flush=True)
    
    # 初始化数据源管理器
    await data_source_manager.initialize()
    print(f"✅ 数据源管理器初始化完成，当前使用：{data_source_manager._default_source}\n", flush=True)
    
    async with get_session() as session:
        # 清空现有板块数据
        print("🗑️  清空现有板块数据...", flush=True)
        await session.execute(delete(SectorInfoDB))
        await session.commit()
        print("✅ 清空完成\n", flush=True)
        
        total_saved = 0
        
        # 1. 获取申万一级行业
        print("📊 获取申万一级行业...", flush=True)
        try:
            sectors = await data_source_manager.get_sector_list(sector_type="sw")
            
            if sectors:
                print(f"✅ 获取到 {len(sectors)} 个申万一级行业", flush=True)
                
                saved_count = 0
                seen_codes = set()
                for sector in sectors:
                    # 避免重复代码导致唯一约束冲突
                    if sector.code in seen_codes:
                        continue
                    seen_codes.add(sector.code)
                    
                    sector_db = SectorInfoDB(
                        code=sector.code,
                        name=sector.name,
                        sector_type="sw",  # 申万行业
                        change_pct=sector.change_pct or 0,
                        volume=sector.volume or 0,
                        amount=sector.amount or 0
                    )
                    session.add(sector_db)
                    saved_count += 1
                
                await session.commit()
                print(f"✅ 保存 {saved_count} 个申万一级行业到数据库\n", flush=True)
                total_saved += saved_count
            else:
                print("❌ 获取申万一级行业失败\n", flush=True)
        except Exception as e:
            print(f"❌ 获取申万一级行业失败：{e}\n", flush=True)
            logger.exception(e)
        
        # 2. 获取行业板块
        print("📊 获取行业板块...", flush=True)
        try:
            sectors = await data_source_manager.get_sector_list(sector_type="industry")
            
            if sectors:
                print(f"✅ 获取到 {len(sectors)} 个行业板块", flush=True)
                
                saved_count = 0
                seen_codes = set()
                for sector in sectors:
                    # 避免重复代码导致唯一约束冲突
                    if sector.code in seen_codes:
                        continue
                    seen_codes.add(sector.code)
                    
                    sector_db = SectorInfoDB(
                        code=sector.code,
                        name=sector.name,
                        sector_type="industry",  # 行业板块
                        change_pct=sector.change_pct or 0,
                        volume=sector.volume or 0,
                        amount=sector.amount or 0
                    )
                    session.add(sector_db)
                    saved_count += 1
                
                await session.commit()
                print(f"✅ 保存 {saved_count} 个行业板块到数据库\n", flush=True)
                total_saved += saved_count
            else:
                print("❌ 获取行业板块失败\n", flush=True)
        except Exception as e:
            print(f"❌ 获取行业板块失败：{e}\n", flush=True)
            logger.exception(e)
        
        # 3. 获取概念板块
        print("📊 获取概念板块...", flush=True)
        try:
            sectors = await data_source_manager.get_sector_list(sector_type="concept")
            
            if sectors:
                print(f"✅ 获取到 {len(sectors)} 个概念板块", flush=True)
                
                saved_count = 0
                seen_codes = set()
                for sector in sectors:
                    # 避免重复代码导致唯一约束冲突
                    if sector.code in seen_codes:
                        continue
                    seen_codes.add(sector.code)
                    
                    sector_db = SectorInfoDB(
                        code=sector.code,
                        name=sector.name,
                        sector_type="concept",  # 概念板块
                        change_pct=sector.change_pct or 0,
                        volume=sector.volume or 0,
                        amount=sector.amount or 0
                    )
                    session.add(sector_db)
                    saved_count += 1
                
                await session.commit()
                print(f"✅ 保存 {saved_count} 个概念板块到数据库\n", flush=True)
                total_saved += saved_count
            else:
                print("❌ 获取概念板块失败\n", flush=True)
        except Exception as e:
            print(f"❌ 获取概念板块失败：{e}\n", flush=True)
            logger.exception(e)
        
        # 验证结果
        print("\n📊 验证数据库中的板块数据...", flush=True)
        result = await session.execute(select(SectorInfoDB))
        all_sectors = result.scalars().all()
        
        # 按类型统计
        sector_type_stats = {}
        for sector in all_sectors:
            st = sector.sector_type
            if st not in sector_type_stats:
                sector_type_stats[st] = 0
            sector_type_stats[st] += 1
        
        print(f"\n✅ 数据库共有 {len(all_sectors)} 个板块", flush=True)
        print("\n按类型分布:", flush=True)
        for st, count in sorted(sector_type_stats.items()):
            print(f"  {st:15} {count:5} 个", flush=True)
        
        # 显示前 20 个板块
        print(f"\n前 20 个板块:", flush=True)
        for i, sector in enumerate(all_sectors[:20], 1):
            print(f"  {i:2}. {sector.code} | {sector.name:15} | {sector.sector_type}", flush=True)
    
    print("\n" + "=" * 80, flush=True)
    print("完成", flush=True)
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"总共保存：{total_saved} 个板块", flush=True)
    print("=" * 80, flush=True)
    
    return total_saved > 0

async def main():
    """主函数"""
    try:
        success = await refresh_sector_data()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 脚本执行失败：{e}\n", flush=True)
        logger.exception(e)
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
