"""
测试 /screener/market-stats API 返回的成交额数据
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from sqlalchemy import select, func
from app.storage.sqlite import get_session, StockInfo
import akshare as ak

async def test_market_turnover():
    print("=" * 70)
    print("测试市场总成交额计算（沪市 + 深市）")
    print("=" * 70)
    
    async with get_session() as session:
        # 查询总数
        result = await session.execute(select(func.count()).select_from(StockInfo))
        total_count = result.scalar()
        print(f"\n股票总数：{total_count}")
        
        # 获取沪市总成交额
        df_sh = ak.stock_sh_a_spot_em()
        sh_turnover = df_sh['成交额'].sum()
        print(f"沪市总成交额：{sh_turnover/100000000:.2f}亿元")
        
        # 获取深市总成交额
        df_sz = ak.stock_sz_a_spot_em()
        sz_turnover = df_sz['成交额'].sum()
        print(f"深市总成交额：{sz_turnover/100000000:.2f}亿元")
        
        # 总成交额
        total_turnover = sh_turnover + sz_turnover
        print(f"\n市场总成交额：{total_turnover/100000000:.2f}亿元")
        
        # 对比实际值
        print(f"\n对比实际值 (2026 年 3 月 27 日):")
        print(f"  实际沪市：7,996.96 亿 | 获取：{sh_turnover/100000000:.2f}亿 | 误差：{abs(sh_turnover/100000000 - 7996.96)/7996.96*100:.2f}%")
        print(f"  实际深市：10,535.77 亿 | 获取：{sz_turnover/100000000:.2f}亿 | 误差：{abs(sz_turnover/100000000 - 10535.77)/10535.77*100:.2f}%")
        print(f"  实际合计：18,500 亿 | 获取：{total_turnover/100000000:.2f}亿")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    asyncio.run(test_market_turnover())
