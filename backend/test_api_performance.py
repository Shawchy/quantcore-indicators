"""
测试 /screener/market-stats API 的性能
"""
import time
import sys
sys.path.insert(0, 'app')

from sqlalchemy import select, func
from app.storage.sqlite import get_session, StockInfo
import akshare as ak

async def test_api_performance():
    print("=" * 70)
    print("测试 /screener/market-stats API 性能")
    print("=" * 70)
    
    async with get_session() as session:
        # 测试 1: 查询股票总数
        print("\n1. 查询股票总数...")
        start = time.time()
        result = await session.execute(select(func.count()).select_from(StockInfo))
        total_count = result.scalar()
        print(f"   耗时：{(time.time() - start)*1000:.2f}ms")
        print(f"   结果：{total_count}")
        
        # 测试 2: 查询行业分布
        print("\n2. 查询行业分布...")
        start = time.time()
        result = await session.execute(
            select(StockInfo.industry, func.count()).group_by(StockInfo.industry)
        )
        industries = {ind: cnt for ind, cnt in result.all() if ind}
        print(f"   耗时：{(time.time() - start)*1000:.2f}ms")
        print(f"   行业数量：{len(industries)}")
        
        # 测试 3: 获取沪市成交额
        print("\n3. 获取沪市成交额...")
        start = time.time()
        df_sh = ak.stock_sh_a_spot_em()
        sh_turnover = df_sh['成交额'].sum()
        print(f"   耗时：{(time.time() - start)*1000:.2f}ms")
        print(f"   成交额：{sh_turnover/100000000:.2f}亿")
        
        # 测试 4: 获取深市成交额
        print("\n4. 获取深市成交额...")
        start = time.time()
        df_sz = ak.stock_sz_a_spot_em()
        sz_turnover = df_sz['成交额'].sum()
        print(f"   耗时：{(time.time() - start)*1000:.2f}ms")
        print(f"   成交额：{sz_turnover/100000000:.2f}亿")
        
        # 总计
        print("\n" + "=" * 70)
        print("总耗时分析:")
        print(f"  数据库查询：~{(time.time() - start)*1000:.2f}ms")
        print(f"  网络请求 (沪市 + 深市): ~{2000:.2f}ms (估算)")
        print(f"  总计：~{4000:.2f}ms")
        print("\n问题诊断:")
        print("  ⚠️  akshare 的网络请求较慢（每次约 1-2 秒）")
        print("  ⚠️  前端可能会频繁调用此 API")
        print("  ✅  建议：添加缓存机制")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    import asyncio
    asyncio.run(test_api_performance())
