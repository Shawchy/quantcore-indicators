"""
检查数据库中日期存储格式
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.storage.sqlite import get_session, KLine
from app.services.trading_calendar import TradingDay
from sqlalchemy import select


async def check_date_format():
    """检查数据库中的日期格式"""
    
    print("=" * 80)
    print("检查数据库日期存储格式")
    print("=" * 80)
    
    async with get_session() as session:
        # 检查 KLine 表
        print("\n1. 检查 KLine 表的日期格式...")
        result = await session.execute(
            select(KLine.date).limit(20)
        )
        kline_dates = result.scalars().all()
        
        if kline_dates:
            print(f"   找到 {len(kline_dates)} 条日期记录")
            
            # 统计格式
            iso_format_count = 0  # YYYY-MM-DD
            compact_format_count = 0  # YYYYMMDD
            other_format_count = 0
            
            for date in kline_dates:
                if len(date) == 10 and '-' in date:
                    iso_format_count += 1
                elif len(date) == 8 and date.isdigit():
                    compact_format_count += 1
                else:
                    other_format_count += 1
                    print(f"   ⚠️  发现其他格式：{date}")
            
            print(f"\n   日期格式统计:")
            print(f"   - ISO 格式 (YYYY-MM-DD): {iso_format_count} 条 ({iso_format_count/len(kline_dates)*100:.1f}%)")
            print(f"   - 紧凑格式 (YYYYMMDD): {compact_format_count} 条 ({compact_format_count/len(kline_dates)*100:.1f}%)")
            print(f"   - 其他格式：{other_format_count} 条")
            
            # 显示示例
            print(f"\n   日期示例:")
            for i, date in enumerate(kline_dates[:5]):
                print(f"   {i+1}. {date} (长度：{len(date)})")
        else:
            print("   ⚠️  KLine 表没有数据")
        
        # 检查 TradingDay 表
        print("\n2. 检查 TradingDay 表的日期格式...")
        result = await session.execute(
            select(TradingDay.date).limit(20)
        )
        trading_dates = result.scalars().all()
        
        if trading_dates:
            print(f"   找到 {len(trading_dates)} 条日期记录")
            
            # 统计格式
            iso_format_count = 0
            compact_format_count = 0
            other_format_count = 0
            
            for date in trading_dates:
                if len(date) == 10 and '-' in date:
                    iso_format_count += 1
                elif len(date) == 8 and date.isdigit():
                    compact_format_count += 1
                else:
                    other_format_count += 1
                    print(f"   ⚠️  发现其他格式：{date}")
            
            print(f"\n   日期格式统计:")
            print(f"   - ISO 格式 (YYYY-MM-DD): {iso_format_count} 条 ({iso_format_count/len(trading_dates)*100:.1f}%)")
            print(f"   - 紧凑格式 (YYYYMMDD): {compact_format_count} 条 ({compact_format_count/len(trading_dates)*100:.1f}%)")
            print(f"   - 其他格式：{other_format_count} 条")
            
            # 显示示例
            print(f"\n   日期示例:")
            for i, date in enumerate(trading_dates[:5]):
                print(f"   {i+1}. {date} (长度：{len(date)})")
        else:
            print("   ⚠️  TradingDay 表没有数据")
        
        # 检查是否有混合格式导致的问题
        print("\n3. 检查日期格式一致性...")
        result = await session.execute(
            select(KLine.date).distinct()
        )
        all_dates = result.scalars().all()
        
        formats_found = set()
        for date in all_dates[:100]:  # 只检查前 100 个不同的日期
            if len(date) == 10 and '-' in date:
                formats_found.add("ISO (YYYY-MM-DD)")
            elif len(date) == 8 and date.isdigit():
                formats_found.add("Compact (YYYYMMDD)")
            else:
                formats_found.add(f"Other ({date})")
        
        if len(formats_found) > 1:
            print(f"   ⚠️  警告：发现多种日期格式混用!")
            for fmt in formats_found:
                print(f"   - {fmt}")
        else:
            print(f"   ✓ 日期格式统一：{formats_found.pop() if formats_found else '未知'}")
        
        print("\n" + "=" * 80)
        print("检查完成")
        print("=" * 80)


if __name__ == "__main__":
    asyncio.run(check_date_format())
