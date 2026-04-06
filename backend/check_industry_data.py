"""
检查 industry 数据
"""
import asyncio
from sqlalchemy import select
from app.storage.sqlite import get_session, StockInfo

async def test():
    async with get_session() as session:
        # 查询前 10 只股票的 industry
        result = await session.execute(
            select(StockInfo.code, StockInfo.name, StockInfo.industry).limit(20)
        )
        
        print("前 20 只股票的 industry 字段:")
        for row in result.all():
            code, name, industry = row
            print(f"  {code} - {name}: industry={repr(industry)}")
        
        # 统计 industry 分布
        print("\n\nIndustry 字段统计:")
        result = await session.execute(
            select(StockInfo.industry, func.count()).group_by(StockInfo.industry)
        )
        
        from sqlalchemy import func
        result = await session.execute(
            select(StockInfo.industry, func.count()).group_by(StockInfo.industry)
        )
        
        for row in result.all():
            ind, cnt = row
            print(f"  {repr(ind)}: {cnt} 只")

if __name__ == '__main__':
    asyncio.run(test())
