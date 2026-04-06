"""
检查股票行业信息数据库保存
"""
import asyncio
from sqlalchemy import select, func
from app.storage.sqlite import get_session, StockInfo

async def check():
    print("=" * 70)
    print("检查股票行业信息数据库保存")
    print("=" * 70)
    
    async with get_session() as session:
        # 1. 检查总数
        print("\n1. 股票总数...")
        result = await session.execute(select(func.count()).select_from(StockInfo))
        total = result.scalar()
        print(f"   总数：{total}")
        
        # 2. 检查 industry 字段
        print("\n2. industry 字段统计...")
        result = await session.execute(
            select(StockInfo.industry, func.count()).group_by(StockInfo.industry)
        )
        rows = result.all()
        
        industry_stats = {}
        for ind, cnt in rows:
            key = str(ind) if ind is not None else "NULL"
            industry_stats[key] = cnt
        
        print(f"   不同值的数量：{len(industry_stats)}")
        for key, cnt in sorted(industry_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {repr(key)}: {cnt} 只")
        
        # 3. 检查 sector 字段
        print("\n3. sector 字段统计...")
        result = await session.execute(
            select(StockInfo.sector, func.count()).group_by(StockInfo.sector)
        )
        rows = result.all()
        
        sector_stats = {}
        for sec, cnt in rows:
            key = str(sec) if sec is not None else "NULL"
            sector_stats[key] = cnt
        
        print(f"   不同值的数量：{len(sector_stats)}")
        for key, cnt in sorted(sector_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {repr(key)}: {cnt} 只")
        
        # 4. 检查 area 字段
        print("\n4. area 字段统计...")
        result = await session.execute(
            select(StockInfo.area, func.count()).group_by(StockInfo.area)
        )
        rows = result.all()
        
        area_stats = {}
        for area, cnt in rows:
            key = str(area) if area is not None else "NULL"
            area_stats[key] = cnt
        
        print(f"   不同值的数量：{len(area_stats)}")
        for key, cnt in sorted(area_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"   {repr(key)}: {cnt} 只")
        
        # 5. 查看前 10 只股票的详细信息
        print("\n5. 前 10 只股票的详细信息...")
        result = await session.execute(
            select(
                StockInfo.code,
                StockInfo.name,
                StockInfo.industry,
                StockInfo.sector,
                StockInfo.area,
                StockInfo.market
            ).limit(10)
        )
        
        print(f"   {'代码':<10} {'名称':<15} {'行业':<20} {'板块':<20} {'地区':<15} {'市场':<5}")
        print(f"   {'-'*10} {'-'*15} {'-'*20} {'-'*20} {'-'*15} {'-'*5}")
        
        for row in result.all():
            code, name, industry, sector, area, market = row
            print(f"   {code:<10} {name:<15} {str(industry):<20} {str(sector):<20} {str(area):<15} {market:<5}")
        
        # 6. 检查 list_date 字段
        print("\n6. list_date 字段统计...")
        result = await session.execute(
            select(StockInfo.list_date, func.count()).group_by(StockInfo.list_date)
        )
        rows = result.all()
        
        none_count = sum(1 for date, _ in rows if date is None)
        has_count = sum(1 for date, _ in rows if date is not None)
        
        print(f"   NULL: {none_count}")
        print(f"   有值：{has_count}")
        
        # 7. 检查股本字段
        print("\n7. 股本字段统计...")
        result = await session.execute(
            select(func.count()).where(StockInfo.total_shares.isnot(None))
        )
        total_shares_count = result.scalar()
        
        result = await session.execute(
            select(func.count()).where(StockInfo.float_shares.isnot(None))
        )
        float_shares_count = result.scalar()
        
        print(f"   total_shares 有值：{total_shares_count}")
        print(f"   float_shares 有值：{float_shares_count}")
    
    print("\n" + "=" * 70)
    print("✅ 检查完成")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(check())
