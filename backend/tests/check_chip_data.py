"""
检查数据库中是否有筹码数据
"""
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import asyncio
from app.storage.sqlite import get_session, ChipData as ChipDataDB
from sqlalchemy import select


async def check_chip_data():
    async with get_session() as session:
        result = await session.execute(select(ChipDataDB).limit(10))
        data = result.scalars().all()
        
        print(f"数据库中有 {len(data)} 条筹码数据")
        
        if data:
            print("\n前 10 条数据:")
            for d in data:
                print(f"  {d.code}: {d.date} - 股东户数={d.shareholder_count}, 户均持股={d.avg_shares_per_holder}")
        else:
            print("\n数据库为空，没有筹码数据")


if __name__ == "__main__":
    asyncio.run(check_chip_data())
