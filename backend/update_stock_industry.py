"""
更新股票的 industry 字段
从数据源获取完整的股票信息（包含行业信息）
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.storage.sqlite import get_session, StockInfo
from app.adapters import data_source_manager
from loguru import logger

async def update_stock_industry():
    """更新股票的 industry 字段"""
    print("=" * 80, flush=True)
    print("更新股票行业信息")
    print("=" * 80, flush=True)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("-" * 80, flush=True)
    
    # 初始化数据源管理器
    await data_source_manager.initialize()
    print(f"✅ 数据源管理器初始化完成，当前使用：{data_source_manager._default_source}\n", flush=True)
    
    async with get_session() as session:
        # 获取所有股票
        result = await session.execute(select(StockInfo))
        stocks = result.scalars().all()
        
        print(f"📊 数据库共有 {len(stocks)} 只股票\n", flush=True)
        
        # 从数据源获取完整的股票列表
        print("📈 正在从数据源获取完整股票信息（含行业）...", flush=True)
        all_stocks = await data_source_manager.get_stock_list()
        
        if not all_stocks:
            print("❌ 获取股票列表失败", flush=True)
            return False
        
        print(f"✅ 获取到 {len(all_stocks)} 只股票\n", flush=True)
        
        # 创建代码到股票的映射
        stock_map = {s.code: s for s in all_stocks}
        
        # 更新数据库中的股票
        print("💾 正在更新行业信息...", flush=True)
        updated_count = 0
        
        for stock in stocks:
            if stock.code in stock_map:
                source_stock = stock_map[stock.code]
                # 更新 industry 字段
                if hasattr(source_stock, 'industry') and source_stock.industry:
                    stock.industry = source_stock.industry
                    updated_count += 1
        
        # 提交事务
        await session.commit()
        
        print(f"\n✅ 更新完成", flush=True)
        print(f"   更新股票数：{updated_count} 只", flush=True)
    
    # 验证结果
    print("\n📊 验证更新结果...", flush=True)
    async with get_session() as session:
        result = await session.execute(select(StockInfo))
        stocks = result.scalars().all()
        
        with_industry = [s for s in stocks if s.industry]
        
        print(f"\n✅ 数据库共有 {len(stocks)} 只股票", flush=True)
        print(f"   有 industry 字段：{len(with_industry)} 只", flush=True)
        
        # 统计 industry 分布
        if with_industry:
            industry_stats = {}
            for s in with_industry:
                ind = s.industry
                if ind not in industry_stats:
                    industry_stats[ind] = 0
                industry_stats[ind] += 1
            
            print(f"\n   Industry 分布 (前 10):", flush=True)
            for ind, count in sorted(industry_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"     {ind:15} {count:5} 只", flush=True)
    
    print("\n" + "=" * 80, flush=True)
    print("完成", flush=True)
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 80, flush=True)
    
    return updated_count > 0

async def main():
    """主函数"""
    try:
        success = await update_stock_industry()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 脚本执行失败：{e}\n", flush=True)
        logger.exception(e)
        sys.exit(1)

if __name__ == '__main__':
    asyncio.run(main())
