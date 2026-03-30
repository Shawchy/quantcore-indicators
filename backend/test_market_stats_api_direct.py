"""
测试市场统计 API 端点
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from app.api.v1.endpoints.screener import get_market_statistics

async def test_api():
    print("=" * 70)
    print("测试市场统计 API")
    print("=" * 70)
    
    result = await get_market_statistics(trade_date=None, current_user=None)
    
    print(f"\nAPI 返回数据:")
    print(f"  total_stocks: {result.data.get('total_stocks')}")
    print(f"  turnover: {result.data.get('turnover', 0) / 100000000:.2f}亿")
    print(f"  trade_date: {result.data.get('trade_date')}")
    print(f"  top_industries: {len(result.data.get('top_industries', []))} 个")
    
    if result.data.get('total_stocks') == 5830:
        print("\n✅ 市场股票数正确！")
    else:
        print(f"\n❌ 市场股票数错误！期望 5830，实际 {result.data.get('total_stocks')}")

if __name__ == '__main__':
    asyncio.run(test_api())
