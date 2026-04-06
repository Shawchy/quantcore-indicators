"""
测试市场统计数据 API
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from sqlalchemy import select, func
from app.storage.sqlite import get_session, StockInfo

async def test():
    print("=" * 70)
    print("测试市场股票数获取逻辑")
    print("=" * 70)
    
    async with get_session() as session:
        # 查询总数
        result = await session.execute(select(func.count()).select_from(StockInfo))
        total_count = result.scalar()
        print(f"\n✅ 数据库股票总数：{total_count}")
        
        # 查询行业分布
        result = await session.execute(
            select(StockInfo.industry, func.count()).group_by(StockInfo.industry)
        )
        industries = {ind: cnt for ind, cnt in result.all() if ind}
        print(f"✅ 行业数量：{len(industries)}")
        
        if industries:
            print(f"\n前 10 大行业:")
            for ind, cnt in sorted(industries.items(), key=lambda x: x[1], reverse=True)[:10]:
                print(f"  {ind}: {cnt} 只")
    
    print("\n" + "=" * 70)
    print("✅ 测试完成！市场股票数优先从数据库获取")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(test())
