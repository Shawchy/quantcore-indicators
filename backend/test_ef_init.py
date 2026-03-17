"""测试 efinance 初始化"""
import asyncio
from app.adapters.efinance_adapter import EFinanceAdapter

async def test():
    adapter = EFinanceAdapter()
    result = await adapter.initialize()
    print(f'初始化结果：{result}')

asyncio.run(test())
