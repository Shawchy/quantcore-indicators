"""
初始化市场成交额历史数据

从 akshare 获取最近 30 个交易日的成交额数据并保存到数据库
"""
import asyncio
import sys
sys.path.insert(0, 'app')

from app.storage.sqlite import get_session
from app.services.market_turnover_service import market_turnover_service
from app.services.trading_calendar import trading_calendar
import akshare as ak
from loguru import logger

async def init_historical_data(days: int = 30):
    """初始化历史数据"""
    
    print("=" * 70)
    print(f"初始化最近 {days} 个交易日的成交额数据")
    print("=" * 70)
    
    # 获取最近 N 个交易日
    trading_days = await trading_calendar.get_recent_trading_days(days * 2)  # 获取多一些
    
    if not trading_days:
        print("❌ 无法获取交易日列表")
        return
    
    print(f"\n获取到 {len(trading_days)} 个交易日")
    
    async with get_session() as session:
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for i, trade_date in enumerate(trading_days):
            print(f"\n[{i+1}/{len(trading_days)}] 处理 {trade_date}...")
            
            # 检查是否已存在
            existing = await market_turnover_service.get_turnover_data(session, trade_date)
            if existing:
                print(f"  ⏭️  跳过（已存在）")
                skip_count += 1
                continue
            
            try:
                # 获取该日期的数据
                # 注意：akshare 的 stock_sh_a_spot_em() 只能获取最新交易日数据
                # 这里我们使用最新数据作为近似值
                # 实际应用中应该使用历史数据接口
                
                if i == 0:  # 只获取最新交易日
                    logger.info(f"从 akshare 获取 {trade_date} 数据...")
                    df_sh = ak.stock_sh_a_spot_em()
                    df_sz = ak.stock_sz_a_spot_em()
                    
                    sh_turnover = df_sh['成交额'].sum()
                    sz_turnover = df_sz['成交额'].sum()
                    total_turnover = sh_turnover + sz_turnover
                    stock_count = len(df_sh) + len(df_sz)
                    
                    # 保存
                    success = await market_turnover_service.save_turnover_data(
                        session, trade_date, sh_turnover, sz_turnover, total_turnover, stock_count
                    )
                    
                    if success:
                        print(f"  ✅ 保存成功：{total_turnover/100000000:.2f}亿")
                        success_count += 1
                    else:
                        print(f"  ❌ 保存失败")
                        error_count += 1
                else:
                    # 对于历史日期，使用最新数据作为占位符
                    # 实际应用中应该从历史数据接口获取
                    print(f"  ⏭️  跳过（需要历史数据接口）")
                    skip_count += 1
                    
            except Exception as e:
                print(f"  ❌ 错误：{e}")
                error_count += 1
    
    print("\n" + "=" * 70)
    print("初始化完成！")
    print(f"  ✅ 成功：{success_count} 天")
    print(f"  ⏭️  跳过：{skip_count} 天")
    print(f"  ❌ 错误：{error_count} 天")
    print("=" * 70)
    print("\n说明:")
    print("  - akshare 的实时接口只能获取最新交易日数据")
    print("  - 历史数据需要使用其他接口或数据源")
    print("  - 当前只保存最新交易日数据作为示例")
    print("=" * 70)

if __name__ == '__main__':
    asyncio.run(init_historical_data(30))
