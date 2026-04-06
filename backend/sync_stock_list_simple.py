"""
同步股票列表到数据库（使用 efinance 数据源）
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.adapters.efinance_adapter import EFinanceAdapter
from app.services.local_database import LocalDatabaseService
from loguru import logger

async def sync_stock_list():
    """同步股票列表"""
    logger.info("=" * 60)
    logger.info("开始同步股票列表（使用 efinance）")
    logger.info("=" * 60)
    
    adapter = None
    try:
        # 创建 efinance 适配器
        adapter = EFinanceAdapter()
        success = await adapter.initialize()
        
        if not success:
            logger.error("efinance 适配器初始化失败")
            return
        
        logger.info("efinance 适配器初始化成功")
        
        # 创建本地数据库服务实例
        db_service = LocalDatabaseService()
        
        # 获取股票列表
        logger.info("获取股票列表...")
        stocks = await adapter.get_stock_list()
        logger.info(f"获取到 {len(stocks)} 只股票")
        
        if not stocks:
            logger.error("未获取到股票数据")
            return
        
        # 同步到数据库
        logger.info("同步到数据库...")
        count = await db_service.sync_stock_list(stocks)
        logger.info(f"同步成功：{count} 只股票")
        
        logger.info("=" * 60)
        logger.info("股票列表同步完成")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"同步失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        if adapter:
            await adapter.close()

if __name__ == "__main__":
    asyncio.run(sync_stock_list())
