"""
检查市场股票数的数据来源和持久化状态
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from sqlalchemy import select, func
from app.storage.sqlite import get_session, StockInfo

async def check_stock_data():
    print("=" * 70)
    print("检查股票数据持久化状态")
    print("=" * 70)
    
    async with get_session() as session:
        # 1. 检查股票总数
        result = await session.execute(select(func.count()).select_from(StockInfo))
        total_count = result.scalar()
        print(f"\n1. 数据库股票总数：{total_count}")
        
        # 2. 检查股票数据分布
        result = await session.execute(
            select(StockInfo.market, func.count()).group_by(StockInfo.market)
        )
        print(f"\n2. 按市场分布：")
        for market, count in result.all():
            print(f"   {market or '未知'}: {count} 只")
        
        # 3. 检查行业分布
        result = await session.execute(
            select(StockInfo.industry, func.count()).group_by(StockInfo.industry)
        )
        industries = result.all()
        print(f"\n3. 行业分布：共 {len(industries)} 个行业")
        
        # 4. 检查数据完整性
        result = await session.execute(
            select(func.count()).where(StockInfo.industry.isnot(None))
        )
        with_industry = result.scalar()
        
        result = await session.execute(
            select(func.count()).where(StockInfo.market.isnot(None))
        )
        with_market = result.scalar()
        
        print(f"\n4. 数据完整性：")
        print(f"   有行业数据：{with_industry}/{total_count} ({with_industry/total_count*100:.1f}%)")
        print(f"   有市场数据：{with_market}/{total_count} ({with_market/total_count*100:.1f}%)")
        
        # 5. 检查最新更新时间
        result = await session.execute(
            select(StockInfo.code, StockInfo.name, StockInfo.updated_at)
            .order_by(StockInfo.updated_at.desc())
            .limit(5)
        )
        print(f"\n5. 最新更新的股票（前 5 只）：")
        for code, name, updated_at in result.all():
            print(f"   {code} {name}: {updated_at}")
        
        # 6. 检查是否有重复数据
        result = await session.execute(
            select(StockInfo.code, func.count()).group_by(StockInfo.code).having(func.count() > 1)
        )
        duplicates = result.all()
        if duplicates:
            print(f"\n⚠️  发现重复数据：{len(duplicates)} 只股票有重复")
        else:
            print(f"\n✅ 无重复数据")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    asyncio.run(check_stock_data())
