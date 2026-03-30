"""
数据归档自动化脚本
定期将 SQLite 中 90 天前的数据归档到 Parquet
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select, distinct
from app.storage.sqlite import get_session, KLine
from app.storage.lifecycle_manager import DataLifecycleManager
from loguru import logger

async def archive_old_data(days_threshold: int = 90):
    """
    归档旧数据
    
    Args:
        days_threshold: 归档天数阈值，默认 90 天
    """
    print("=" * 80, flush=True)
    print("数据归档自动化脚本")
    print("=" * 80, flush=True)
    print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print(f"归档阈值：{days_threshold} 天前的数据", flush=True)
    print("-" * 80, flush=True)
    
    lifecycle = DataLifecycleManager()
    
    async with get_session() as session:
        # 获取所有股票代码
        result = await session.execute(select(distinct(KLine.code)))
        codes = [row[0] for row in result.fetchall()]
        
        print(f"\n共有 {len(codes)} 只股票需要检查归档\n", flush=True)
        
        threshold_date = (datetime.now() - timedelta(days=days_threshold)).strftime("%Y-%m-%d")
        total_archived = 0
        processed = 0
        
        for i, code in enumerate(codes, 1):
            try:
                # 检查该股票是否有需要归档的数据
                result = await session.execute(
                    select(KLine.date)
                    .where(KLine.code == code)
                    .where(KLine.date < threshold_date)
                    .limit(1)
                )
                has_old_data = result.scalar()
                
                if has_old_data:
                    print(f"[{i}/{len(codes)}] {code}: 发现旧数据，开始归档...", flush=True)
                    await lifecycle.auto_archive(code)
                    total_archived += 1
                    print(f"  ✅ {code} 归档完成\n", flush=True)
                else:
                    print(f"[{i}/{len(codes)}] {code}: 无需归档", flush=True)
                
                processed += 1
                
                # 每处理 10 只股票显示进度
                if i % 10 == 0:
                    print(f"\n进度：{i}/{len(codes)} 已处理 {processed} 只股票，归档 {total_archived} 只\n", flush=True)
                
            except Exception as e:
                print(f"❌ {code} 归档失败：{e}\n", flush=True)
                logger.exception(e)
    
    print("\n" + "=" * 80, flush=True)
    print("归档完成", flush=True)
    print(f"处理股票数：{processed}", flush=True)
    print(f"归档股票数：{total_archived}", flush=True)
    print(f"结束时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", flush=True)
    print("=" * 80, flush=True)
    
    return total_archived

async def main():
    """主函数"""
    # 默认归档 90 天前的数据
    days_threshold = 90
    
    # 可以从命令行参数读取
    if len(sys.argv) > 1:
        try:
            days_threshold = int(sys.argv[1])
            print(f"使用命令行参数：归档 {days_threshold} 天前的数据\n", flush=True)
        except ValueError:
            print(f"无效的参数，使用默认值：归档 {days_threshold} 天前的数据\n", flush=True)
    
    await archive_old_data(days_threshold)

if __name__ == '__main__':
    asyncio.run(main())
