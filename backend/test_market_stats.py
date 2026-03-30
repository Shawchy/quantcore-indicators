"""
测试市场统计数据 API
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from sqlalchemy import select, func
from app.storage.sqlite import get_session, StockInfo

async def test():
    async with get_session() as session:
        result = await session.execute(select(func.count()).select_from(StockInfo))
        count = result.scalar()
        print(f'股票总数: {count}')
        
        # 检查数据库中的股票
        result = await session.execute(select(StockInfo.code, StockInfo.name).limit(5))
        print(f'\n前 5 只股票:')
        for row in result.all():
            print(f'  {row[0]}: {row[1]}')

if __name__ == '__main__':
    asyncio.run(test())
