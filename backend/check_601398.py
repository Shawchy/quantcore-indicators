"""
检查数据库保存和查询的日期格式
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.storage.sqlite import get_session, KLine
from sqlalchemy import select


async def check_all_klines():
    """检查所有 K 线数据"""
    
    print("=" * 80)
    print("检查数据库中的 K 线记录")
    print("=" * 80)
    
    async with get_session() as session:
        # 查询所有股票的数据
        result = await session.execute(
            select(KLine.code, KLine.adjust_type, KLine.date).limit(20)
        )
        klines = result.all()
        
        if klines:
            print(f"\n找到 {len(klines)} 条记录")
            print("\n前 20 条记录:")
            for i, (code, adjust_type, date) in enumerate(klines, 1):
                print(f"{i}. 代码：{code}, 日期：{date} (长度：{len(date)}), 复权：{adjust_type}")
            
            # 统计不同股票的数量
            result = await session.execute(
                select(KLine.code, KLine.adjust_type)
            )
            rows = result.all()
            
            print(f"\n股票统计:")
            stock_counts = {}
            for code, adjust_type in rows:
                key = f"{code}_{adjust_type}"
                stock_counts[key] = stock_counts.get(key, 0) + 1
            
            for key, count in sorted(stock_counts.items())[:10]:
                print(f"  - {key}: {count} 条")
            
            print(f"  ... 共 {len(stock_counts)} 只股票/复权组合")
        else:
            print("\n⚠️  数据库中没有任何 K 线记录!")
        
        print("\n" + "=" * 80)


if __name__ == "__main__":
    asyncio.run(check_all_klines())
