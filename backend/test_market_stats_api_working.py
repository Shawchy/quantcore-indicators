"""
测试市场统计数据 API 是否正常工作
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from sqlalchemy import select
from app.storage.sqlite import get_session
from app.services.market_turnover_service import MarketTurnover, market_turnover_service

async def test_api():
    print("=" * 70)
    print("测试市场统计数据 API")
    print("=" * 70)
    
    async with get_session() as session:
        # 1. 检查数据库表是否存在
        print("\n1. 检查数据库表...")
        result = await session.execute(
            select(MarketTurnover).limit(1)
        )
        try:
            record = result.fetchone()
            if record:
                print(f"   ✅ 表存在且有数据")
                r = record[0]
                print(f"   最新数据：{r.trade_date} | 总额：{r.total_turnover/100000000:.2f}亿")
            else:
                print(f"   ⚠️  表存在但无数据")
        except Exception as e:
            print(f"   ❌ 表不存在或查询失败：{e}")
        
        # 2. 测试服务方法
        print("\n2. 测试持久化服务...")
        try:
            latest = await market_turnover_service.get_latest_turnover(session)
            if latest:
                print(f"   ✅ 服务正常")
                print(f"   最新日期：{latest['trade_date']}")
                print(f"   总成交额：{latest['total_turnover']/100000000:.2f}亿")
            else:
                print(f"   ⚠️  无数据")
        except Exception as e:
            print(f"   ❌ 服务异常：{e}")
        
        # 3. 测试 API 导入
        print("\n3. 测试 API 导入...")
        try:
            from app.api.v1.endpoints import screener
            print(f"   ✅ API 模块导入成功")
            print(f"   API 端点：/screener/market-stats")
        except Exception as e:
            print(f"   ❌ API 导入失败：{e}")
    
    print("\n" + "=" * 70)
    print("测试完成！")
    print("现在可以访问：http://localhost:8000/api/v1/screener/market-stats")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(test_api())
