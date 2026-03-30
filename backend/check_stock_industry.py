"""
检查 StockInfo 表的 industry 字段
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.storage.sqlite import get_session, StockInfo

async def check():
    async with get_session() as session:
        # 检查总数
        result = await session.execute(select(StockInfo))
        stocks = result.scalars().all()
        
        print(f'📊 股票总数：{len(stocks)}')
        
        # 检查 industry 字段
        with_industry = [s for s in stocks if s.industry]
        without_industry = [s for s in stocks if not s.industry]
        
        print(f'\n有 industry 字段的：{len(with_industry)} 只')
        print(f'无 industry 字段的：{len(without_industry)} 只')
        
        if with_industry:
            print(f'\n有 industry 的前 10 只股票:')
            for i, s in enumerate(with_industry[:10]):
                print(f"  {i+1}. {s.code} | {s.name:15} | industry={s.industry}")
        
        # 统计 industry 分布
        if with_industry:
            industry_stats = {}
            for s in with_industry:
                ind = s.industry
                if ind not in industry_stats:
                    industry_stats[ind] = 0
                industry_stats[ind] += 1
            
            print(f'\nIndustry 分布 (前 10):')
            for ind, count in sorted(industry_stats.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {ind:15} {count:5} 只")

if __name__ == '__main__':
    asyncio.run(check())
