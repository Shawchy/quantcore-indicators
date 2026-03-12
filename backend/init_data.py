"""
数据初始化脚本
拉取股票列表、板块列表、历史 K 线数据到数据库
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.adapters.factory import data_source_manager
from app.services.data_persistence import data_persistence
from app.storage.sqlite import get_session, StockInfo as StockInfoDB, SectorInfo as SectorInfoDB
from sqlalchemy import select


async def init_stock_list():
    """初始化股票列表"""
    print("\n" + "=" * 70)
    print("1️⃣ 初始化股票列表")
    print("=" * 70)
    
    try:
        # 从数据源获取股票列表
        stocks = await data_source_manager.get_stock_list()
        
        if not stocks:
            print("❌ 获取股票列表失败")
            return False
        
        print(f"✅ 获取到 {len(stocks)} 只股票")
        
        # 保存到数据库
        async with get_session() as session:
            saved_count = 0
            for stock in stocks:
                # 检查是否已存在
                existing = await session.execute(
                    select(StockInfoDB).where(StockInfoDB.code == stock.code)
                )
                if existing.scalar_one_or_none():
                    continue
                
                # 插入新记录
                stock_db = StockInfoDB(
                    code=stock.code,
                    name=stock.name,
                    market=stock.market,
                    industry=stock.industry,
                    sector=getattr(stock, 'sector', None),
                    area=getattr(stock, 'area', None),
                    list_date=getattr(stock, 'list_date', None),
                    total_shares=getattr(stock, 'total_shares', None),
                    float_shares=getattr(stock, 'float_shares', None)
                )
                session.add(stock_db)
                saved_count += 1
            
            await session.commit()
            print(f"✅ 新增 {saved_count} 只股票到数据库")
            return True
            
    except Exception as e:
        print(f"❌ 初始化股票列表失败：{e}")
        logger.exception(e)
        return False


async def init_sector_list():
    """初始化板块列表"""
    print("\n" + "=" * 70)
    print("2️⃣ 初始化板块列表")
    print("=" * 70)
    
    try:
        # 获取行业板块
        sectors = await data_source_manager.get_sector_list(sector_type="industry")
        
        if not sectors:
            print("❌ 获取板块列表失败")
            return False
        
        print(f"✅ 获取到 {len(sectors)} 个板块")
        
        # 保存到数据库
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
                    sector_type=sector.sector_type,
                    change_pct=0,
                    volume=0,
                    amount=0
                )
                session.add(sector_db)
                saved_count += 1
            
            await session.commit()
            print(f"✅ 新增 {saved_count} 个板块到数据库")
            return True
            
    except Exception as e:
        print(f"❌ 初始化板块列表失败：{e}")
        logger.exception(e)
        return False


async def init_kline_data(codes: list, days: int = 60):
    """
    初始化 K 线数据
    
    Args:
        codes: 股票代码列表
        days: 拉取天数
    """
    print("\n" + "=" * 70)
    print(f"3️⃣ 初始化 K 线数据（{len(codes)} 只股票，{days} 天）")
    print("=" * 70)
    
    end_date = datetime.now().strftime("%Y%m%d")
    start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    
    success_count = 0
    failed_codes = []
    
    for idx, code in enumerate(codes, 1):
        try:
            print(f"[{idx}/{len(codes)}] 拉取 {code} 的 K 线数据...", end=" ")
            
            klines = await data_source_manager.get_kline(
                code=code,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            if klines:
                # 保存到数据库
                saved = await data_persistence.save_klines(code, klines, "qfq")
                print(f"✅ 拉取 {len(klines)} 条，保存 {saved} 条")
                success_count += 1
            else:
                print("❌ 无数据")
                failed_codes.append(code)
                
        except Exception as e:
            print(f"❌ 失败：{e}")
            failed_codes.append(code)
        
        # 避免请求过快
        await asyncio.sleep(0.5)
    
    print(f"\n✅ 成功：{success_count}/{len(codes)} 只股票")
    if failed_codes:
        print(f"❌ 失败股票：{', '.join(failed_codes[:10])}{'...' if len(failed_codes) > 10 else ''}")
    
    return success_count


async def main():
    """主函数"""
    print("=" * 70)
    print("数据初始化脚本")
    print("=" * 70)
    print(f"\n开始时间：{datetime.now()}")
    
    # 初始化数据源管理器
    print("\n初始化数据源管理器...")
    await data_source_manager.initialize()
    print(f"✅ 数据源管理器初始化完成，当前使用：{data_source_manager._default_source}")
    
    # 1. 初始化股票列表
    stock_success = await init_stock_list()
    
    # 2. 初始化板块列表
    sector_success = await init_sector_list()
    
    # 3. 初始化 K 线数据（只拉取部分热门股票）
    if stock_success:
        # 获取已保存的股票代码
        async with get_session() as session:
            result = await session.execute(select(StockInfoDB.code).limit(20))
            codes = [row[0] for row in result.fetchall()]
        
        if codes:
            await init_kline_data(codes, days=60)
        else:
            print("\n⚠️  股票列表为空，跳过 K 线数据初始化")
    else:
        print("\n⚠️  股票列表初始化失败，跳过 K 线数据初始化")
    
    print("\n" + "=" * 70)
    print("初始化完成")
    print("=" * 70)
    print(f"完成时间：{datetime.now()}")
    print("\n请运行 check_database_data.py 检查数据量")


if __name__ == "__main__":
    asyncio.run(main())
