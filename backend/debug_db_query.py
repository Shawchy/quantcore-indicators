"""
调试数据库查询
"""
import asyncio
from sqlalchemy import select, func
from app.storage.sqlite import get_session, StockInfo

async def test():
    print("=" * 70)
    print("调试数据库查询")
    print("=" * 70)
    
    async with get_session() as session:
        # 查询总数
        print("\n1. 查询股票总数...")
        result = await session.execute(select(func.count()).select_from(StockInfo))
        total_count = result.scalar()
        print(f"   结果：{total_count}")
        
        # 查询行业分布
        print("\n2. 查询行业分布...")
        result = await session.execute(
            select(StockInfo.industry, func.count()).group_by(StockInfo.industry)
        )
        rows = result.all()
        print(f"   结果：{len(rows)} 个行业")
        
        industries = {ind: cnt for ind, cnt in rows if ind}
        print(f"   过滤后：{len(industries)} 个行业")
        
        if industries:
            print(f"\n   前 5 大行业:")
            for ind, cnt in sorted(industries.items(), key=lambda x: x[1], reverse=True)[:5]:
                print(f"     {ind}: {cnt} 只")
        
        # 模拟 API 返回
        print("\n3. 模拟 API 返回数据...")
        result_data = {
            "total_stocks": total_count or 0,
            "industry_distribution": industries,
            "turnover": 0.0,
        }
        
        print(f"   total_stocks: {result_data['total_stocks']}")
        print(f"   industry_distribution: {len(result_data['industry_distribution'])} 个行业")
        print(f"   turnover: {result_data['turnover']}")
        
        # 测试缓存
        print("\n4. 测试缓存 key...")
        from app.utils.api_cache_stats import api_cache
        cache_key = {'date': None}
        cached_data = await api_cache.get('api_stats', cache_key)
        if cached_data:
            print(f"   ✅ 缓存命中：{cached_data}")
        else:
            print(f"   ❌ 缓存未命中")
    
    print("\n" + "=" * 70)
    print("✅ 调试完成")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(test())
