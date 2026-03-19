from app.adapters.efinance_adapter import EFinanceAdapter
import asyncio

async def test():
    adapter = EFinanceAdapter()
    await adapter.initialize()
    klines = await adapter.get_kline('600000', '2026-02-17', '2026-03-19')
    print(f'获取{len(klines)}条')
    print(f'第一条类型：{type(klines[0])}')
    if hasattr(klines[0], 'model_dump'):
        print(f'数据示例：{klines[0].model_dump()}')
    else:
        print(f'数据示例：{klines[0]}')

asyncio.run(test())
