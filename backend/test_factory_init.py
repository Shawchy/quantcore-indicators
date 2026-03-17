"""测试数据源工厂初始化"""
import asyncio
from app.adapters.factory import DataSourceFactory

async def test():
    print("开始测试数据源工厂初始化...")
    await DataSourceFactory.initialize()
    print("\n可用数据源:", [s.value for s in DataSourceFactory._adapters.keys()])

asyncio.run(test())
