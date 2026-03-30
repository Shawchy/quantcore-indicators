"""
检查数据库中 000001 的实时行情数据
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.storage.sqlite import get_session, RealtimeQuote

async def check():
    async with get_session() as session:
        result = await session.execute(
            select(RealtimeQuote).where(RealtimeQuote.code == '000001')
        )
        quote = result.scalar_one_or_none()
        
        if quote:
            print(f"找到 000001 的实时行情数据:")
            print(f"  代码：{quote.code}")
            print(f"  名称：{quote.name}")
            print(f"  价格：{quote.price}")
            print(f"  涨跌：{quote.change}")
            print(f"  涨跌幅：{quote.change_pct}%")
            print(f"  更新时间：{quote.updated_at}")
        else:
            print("未找到 000001 的实时行情数据")

if __name__ == '__main__':
    asyncio.run(check())
