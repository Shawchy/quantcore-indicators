"""
计算技术指标数据脚本
为所有股票计算 MA/RSI/MACD 等技术指标并保存到数据库
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.storage.sqlite import get_session, KLine, TechnicalIndicatorDB
from app.services.indicators import TechnicalIndicators
from loguru import logger

async def calculate_indicators_for_stock(code: str, session) -> int:
    """为单只股票计算技术指标"""
    import pandas as pd
    
    # 从数据库获取 K 线数据
    result = await session.execute(
        select(KLine)
        .where(KLine.code == code)
        .where(KLine.adjust_type == 'qfq')
        .order_by(KLine.date)
    )
    klines = result.scalars().all()
    
    if not klines:
        return 0
    
    # 转换为 DataFrame
    df = pd.DataFrame([{
        'date': k.date,
        'close': k.close,
        'open': k.open,
        'high': k.high,
        'low': k.low,
        'volume': k.volume
    } for k in klines])
    
    # 计算技术指标
    df = TechnicalIndicators.calculate_ma(df, periods=[5, 10, 20, 60])
    df = TechnicalIndicators.calculate_rsi(df, periods=[6, 12, 24])
    df = TechnicalIndicators.calculate_macd(df)
    
    # 保存到数据库
    saved_count = 0
    for _, row in df.iterrows():
        # 检查是否已存在
        existing = await session.execute(
            select(TechnicalIndicatorDB).where(
                TechnicalIndicatorDB.code == code,
                TechnicalIndicatorDB.date == row['date']
            )
        )
        if existing.scalar_one_or_none():
            continue
        
        # 创建新记录
        indicator = TechnicalIndicatorDB(
            code=code,
            date=row['date'],
            ma5=row.get('ma5'),
            ma10=row.get('ma10'),
            ma20=row.get('ma20'),
            ma60=row.get('ma60'),
            rsi6=row.get('rsi6'),
            rsi12=row.get('rsi12'),
            rsi24=row.get('rsi24'),
            macd=row.get('macd'),
            macd_signal=row.get('macd_signal'),
            macd_hist=row.get('macd_hist')
        )
        session.add(indicator)
        saved_count += 1
    
    return saved_count

async def main():
    """主函数"""
    print("=" * 80, flush=True)
    print("技术指标数据计算脚本")
    print("=" * 80, flush=True)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("-" * 80, flush=True)
    
    import pandas as pd
    
    async with get_session() as session:
        # 获取所有股票代码
        result = await session.execute(select(KLine.code).distinct())
        codes = [row[0] for row in result.fetchall()]
        
        print(f"\n共有 {len(codes)} 只股票需要计算技术指标\n", flush=True)
        
        import pandas as pd
        
        total_saved = 0
        processed = 0
        
        for i, code in enumerate(codes, 1):
            try:
                saved = await calculate_indicators_for_stock(code, session)
                total_saved += saved
                processed += 1
                
                if i % 10 == 0 or i == len(codes):
                    print(f"进度：{i}/{len(codes)} 已处理 {processed} 只股票，保存 {total_saved} 条指标数据", flush=True)
                
                # 每处理 10 只股票 commit 一次
                if i % 10 == 0:
                    await session.commit()
                    print(f"  ✅ 已 commit 前 {i} 只股票的数据", flush=True)
                    
            except Exception as e:
                print(f"❌ 处理 {code} 失败：{e}", flush=True)
                logger.exception(e)
        
        # 最后 commit 一次
        await session.commit()
        print(f"\n✅ 所有股票处理完成", flush=True)
        print(f"   处理股票数：{processed}", flush=True)
        print(f"   保存指标数：{total_saved}", flush=True)
    
    print("\n" + "=" * 80, flush=True)
    print("完成", flush=True)
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 80, flush=True)

if __name__ == '__main__':
    asyncio.run(main())
