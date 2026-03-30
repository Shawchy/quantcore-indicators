"""
删除 000001 的错误实时行情数据
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import delete
from app.storage.sqlite import get_session, RealtimeQuote

async def delete_bad_data():
    async with get_session() as session:
        # 删除 000001 的记录
        await session.execute(
            delete(RealtimeQuote).where(RealtimeQuote.code == '000001')
        )
        await session.commit()
        print("✅ 已删除 000001 的错误数据")

if __name__ == '__main__':
    asyncio.run(delete_bad_data())
