"""
检查数据源返回的股票对象结构
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.adapters import data_source_manager

async def check():
    # 初始化数据源管理器
    await data_source_manager.initialize()
    print(f"✅ 数据源管理器初始化完成，当前使用：{data_source_manager._default_source}\n")
    
    # 获取股票列表
    stocks = await data_source_manager.get_stock_list()
    
    print(f"获取到 {len(stocks)} 只股票\n")
    
    if stocks:
        print("前 5 只股票的字段:")
        for i, stock in enumerate(stocks[:5]):
            print(f"\n{i+1}. {stock.code} - {stock.name}")
            print(f"   所有字段：{stock.__dict__.keys()}")
            print(f"   industry: {getattr(stock, 'industry', 'N/A')}")
            print(f"   sector: {getattr(stock, 'sector', 'N/A')}")
            print(f"   area: {getattr(stock, 'area', 'N/A')}")

if __name__ == '__main__':
    asyncio.run(check())
