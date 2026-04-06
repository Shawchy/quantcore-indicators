"""检查数据库股票数据"""
from app.storage.sqlite import get_session, StockInfo
from sqlalchemy import select, func
import asyncio

async def check():
    async with get_session() as session:
        # 查询总数
        result = await session.execute(select(func.count()).select_from(StockInfo))
        total_count = result.scalar()
        print(f'股票总数：{total_count}')
        
        # 查询行业分布
        result = await session.execute(
            select(StockInfo.industry, func.count()).group_by(StockInfo.industry)
        )
        industries = {ind: cnt for ind, cnt in result.all() if ind}
        print(f'行业数：{len(industries)}')
        print(f'前 10 大行业:')
        for ind, cnt in sorted(industries.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f'  {ind}: {cnt}')

asyncio.run(check())
