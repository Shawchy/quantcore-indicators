"""
分层数据加载功能测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加后端路径
sys.path.insert(0, str(Path(__file__).parent / "backend"))

from app.services.data_loader import DataLoader, LoadPriority
from app.services import stock_service
from loguru import logger


async def test_data_loader():
    """测试数据加载器"""
    print("=" * 60)
    print("测试数据加载器")
    print("=" * 60)
    
    loader = DataLoader()
    await loader.start()
    
    try:
        # 测试本月数据加载
        print("\n1. 测试加载本月数据...")
        from app.adapters import data_source_manager
        from app.services.data_persistence import data_persistence
        
        await data_source_manager.initialize()
        
        progress = await loader.load_kline_priority(
            code="000001",
            data_source_manager=data_source_manager,
            data_persistence=data_persistence,
            priority=LoadPriority.CURRENT_MONTH
        )
        
        print(f"✓ 加载完成")
        print(f"  状态：{progress.status}")
        print(f"  已加载：{progress.loaded}")
        print(f"  预计总量：{progress.total_expected}")
        print(f"  后台加载中：{progress.background_loading}")
        
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        logger.exception(e)
    
    finally:
        await loader.stop()


async def test_stock_service():
    """测试 StockService 优先加载"""
    print("\n" + "=" * 60)
    print("测试 StockService 优先加载")
    print("=" * 60)
    
    try:
        # 初始化数据源
        from app.adapters import data_source_manager
        await data_source_manager.initialize()
        
        # 启动数据加载器
        from app.services.data_loader import data_loader
        await data_loader.start()
        
        print("\n1. 测试优先加载模式...")
        result = await stock_service.get_kline(
            code="000001",
            priority_load=True
        )
        
        print(f"✓ 优先加载完成")
        print(f"  状态：{result.get('status')}")
        print(f"  数据条数：{len(result.get('data', []))}")
        print(f"  后台加载中：{result.get('background_loading')}")
        if result.get('coverage'):
            print(f"  覆盖范围：{result['coverage']}")
        
        print("\n2. 测试传统加载模式...")
        result2 = await stock_service.get_kline(
            code="000001",
            priority_load=False
        )
        
        print(f"✓ 传统加载完成")
        print(f"  状态：{result2.get('status')}")
        print(f"  数据条数：{len(result2.get('data', []))}")
        
    except Exception as e:
        print(f"✗ 测试失败：{e}")
        logger.exception(e)
    
    finally:
        # 停止数据加载器
        from app.services.data_loader import data_loader
        await data_loader.stop()


async def main():
    """主测试函数"""
    print("\n" + "=" * 60)
    print("分层数据加载功能测试")
    print("=" * 60)
    
    # 测试 1: 数据加载器
    await test_data_loader()
    
    # 测试 2: StockService
    await test_stock_service()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
