"""
获取完整 A 股股票列表脚本
从数据源获取所有 A 股股票信息并保存到数据库
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.storage.sqlite import get_session, StockInfo as StockInfoDB
from app.adapters import data_source_manager
from loguru import logger

async def get_all_stocks():
    """获取所有 A 股股票"""
    print("=" * 80, flush=True)
    print("获取完整 A 股股票列表")
    print("=" * 80, flush=True)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("-" * 80, flush=True)
    
    # 初始化数据源管理器
    await data_source_manager.initialize()
    print(f"✅ 数据源管理器初始化完成，当前使用：{data_source_manager._default_source}\n", flush=True)
    
    async with get_session() as session:
        # 检查当前数据库中的股票数
        result = await session.execute(select(StockInfoDB.code).distinct())
        existing_codes = set(row[0] for row in result.fetchall())
        print(f"📊 当前数据库股票数：{len(existing_codes)}\n", flush=True)
        
        # 从数据源获取股票列表
        print("📈 正在从数据源获取 A 股股票列表...", flush=True)
        stocks = await data_source_manager.get_stock_list()
        
        if not stocks:
            print("❌ 获取股票列表失败", flush=True)
            return False
        
        print(f"✅ 获取到 {len(stocks)} 只股票\n", flush=True)
        
        # 显示前 10 只股票
        print("前 10 只股票示例:", flush=True)
        for i, stock in enumerate(stocks[:10], 1):
            print(f"  {i:2}. {stock.code} | {stock.name:15} | {stock.market}", flush=True)
        print(flush=True)
        
        # 保存到数据库
        print("💾 正在保存到数据库...", flush=True)
        saved_count = 0
        updated_count = 0
        
        for stock in stocks:
            # 检查是否已存在
            existing = await session.execute(
                select(StockInfoDB).where(StockInfoDB.code == stock.code)
            )
            existing_stock = existing.scalar_one_or_none()
            
            if existing_stock:
                # 更新现有记录
                existing_stock.name = stock.name
                existing_stock.market = stock.market
                existing_stock.industry = getattr(stock, 'industry', None)
                existing_stock.sector = getattr(stock, 'sector', None)
                existing_stock.area = getattr(stock, 'area', None)
                existing_stock.list_date = getattr(stock, 'list_date', None)
                existing_stock.total_shares = getattr(stock, 'total_shares', None)
                existing_stock.float_shares = getattr(stock, 'float_shares', None)
                existing_stock.updated_at = datetime.now()
                updated_count += 1
            else:
                # 创建新记录
                new_stock = StockInfoDB(
                    code=stock.code,
                    name=stock.name,
                    market=stock.market,
                    industry=getattr(stock, 'industry', None),
                    sector=getattr(stock, 'sector', None),
                    area=getattr(stock, 'area', None),
                    list_date=getattr(stock, 'list_date', None),
                    total_shares=getattr(stock, 'total_shares', None),
                    float_shares=getattr(stock, 'float_shares', None)
                )
                session.add(new_stock)
                saved_count += 1
        
        # 提交事务
        await session.commit()
        
        print(f"\n✅ 数据库更新完成", flush=True)
        print(f"   新增股票：{saved_count} 只", flush=True)
        print(f"   更新股票：{updated_count} 只", flush=True)
        print(f"   总计股票：{len(stocks)} 只", flush=True)
    
    # 验证结果
    print("\n📊 验证数据库中的股票数据...", flush=True)
    async with get_session() as session:
        result = await session.execute(select(StockInfoDB))
        all_stocks = result.scalars().all()
        
        # 按市场统计
        market_stats = {}
        for stock in all_stocks:
            market = stock.market
            if market not in market_stats:
                market_stats[market] = 0
            market_stats[market] += 1
        
        print(f"\n✅ 数据库共有 {len(all_stocks)} 只股票", flush=True)
        print("\n按市场分布:", flush=True)
        for market, count in sorted(market_stats.items()):
            print(f"  {market:10} {count:5} 只", flush=True)
        
        # 显示前 20 只股票
        print(f"\n前 20 只股票:", flush=True)
        for i, stock in enumerate(all_stocks[:20], 1):
            print(f"  {i:2}. {stock.code} | {stock.name:15} | {stock.market}", flush=True)
    
    print("\n" + "=" * 80, flush=True)
    print("完成", flush=True)
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 80, flush=True)
    
    return True

async def main():
    """主函数"""
    try:
        success = await get_all_stocks()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 脚本执行失败：{e}\n", flush=True)
        logger.exception(e)
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
