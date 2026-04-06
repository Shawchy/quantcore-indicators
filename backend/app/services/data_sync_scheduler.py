"""
数据同步定时任务

定期从 API 同步数据到本地数据库，减少实时请求
"""
import asyncio
from datetime import datetime, timedelta, time
from typing import List, Optional
from loguru import logger

from app.adapters.factory import data_source_manager
from app.services.local_database import local_db_service
from app.services.stock_list_sync import stock_list_sync
from app.storage.unified_storage import storage_manager, DataCategory


class DataSyncScheduler:
    """数据同步调度器"""
    
    def __init__(self):
        self._running = False
        self._tasks: List[asyncio.Task] = []
    
    async def start(self):
        """启动定时同步任务"""
        if self._running:
            logger.warning("数据同步任务已在运行")
            return
        
        self._running = True
        logger.info("数据同步定时任务已启动")
        
        # 启动各类数据的定时同步任务
        self._tasks.append(asyncio.create_task(
            self._sync_stock_list_daily(),
            name="sync_stock_list"
        ))
        
        self._tasks.append(asyncio.create_task(
            self._sync_kline_data_hourly(),
            name="sync_kline_hourly"
        ))
        
        self._tasks.append(asyncio.create_task(
            self._sync_realtime_quotes_frequently(),
            name="sync_quotes_frequent"
        ))
    
    async def stop(self):
        """停止所有同步任务"""
        self._running = False
        
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._tasks.clear()
        logger.info("数据同步定时任务已停止")
    
    async def _sync_stock_list_daily(self):
        """每日同步股票列表（每天收盘后执行）"""
        while self._running:
            try:
                # 在每天 15:30 执行（收盘后）
                now = datetime.now()
                target_time = now.replace(
                    hour=15, minute=30, second=0, microsecond=0
                )
                
                if now >= target_time:
                    # 已经过了今天的目标时间，等待到明天
                    await asyncio.sleep(24 * 3600)
                    continue
                
                # 计算距离目标时间的秒数
                delay = (target_time - now).total_seconds()
                logger.info(f"股票列表同步任务：等待 {delay/3600:.1f}小时后执行")
                await asyncio.sleep(delay)
                
                # 执行同步
                if self._running:
                    # 使用新的同步工具（不依赖数据源适配器）
                    success = await stock_list_sync.auto_sync()
                    if success:
                        logger.info("定时任务：股票列表同步成功")
                    else:
                        logger.error("定时任务：股票列表同步失败")
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"股票列表同步任务异常：{e}")
                await asyncio.sleep(3600)  # 异常后等待 1 小时
    
    async def _sync_kline_data_hourly(self):
        """每小时同步 K 线数据"""
        while self._running:
            try:
                # 每小时执行一次
                await asyncio.sleep(3600)
                
                if self._running:
                    await self._do_sync_kline_data()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"K 线数据同步任务异常：{e}")
                await asyncio.sleep(3600)
    
    async def _sync_realtime_quotes_frequently(self):
        """高频同步实时行情（每 5 分钟）"""
        while self._running:
            try:
                # 每 5 分钟执行一次
                await asyncio.sleep(300)
                
                if self._running:
                    await self._do_sync_quotes()
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"实时行情同步任务异常：{e}")
                await asyncio.sleep(300)
    

    
    async def _do_sync_kline_data(self, limit_stocks: int = 100):
        """执行 K 线数据同步
        
        Args:
            limit_stocks: 每次同步的股票数量限制（避免请求过多）
        """
        logger.info("开始同步 K 线数据...")
        
        try:
            # 获取热门股票列表
            stock_list = await local_db_service.get_stock_list_from_db()
            
            if not stock_list:
                logger.warning("本地数据库无股票列表，先同步股票列表")
                await self._do_sync_stock_list()
                stock_list = await local_db_service.get_stock_list_from_db()
            
            # 只同步前 N 只股票
            stocks_to_sync = stock_list[:limit_stocks]
            
            # 使用统一存储层
            kline_storage = storage_manager.get_kline_storage("daily")
            
            for stock in stocks_to_sync:
                try:
                    # 从数据源获取 K 线数据
                    kline_data = await data_source_manager.get_kline(
                        code=stock.code,
                        start_date=(datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
                        end_date=datetime.now().strftime("%Y-%m-%d")
                    )
                    
                    if kline_data:
                        # 使用统一存储层（自动同步到数据库）
                        await kline_storage.set(stock.code, kline_data)
                    
                    # 避免请求过快
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    logger.error(f"同步 K 线数据失败 {stock.code}: {e}")
                    continue
            
            logger.info(f"K 线数据同步完成：{len(stocks_to_sync)}只股票")
            
        except Exception as e:
            logger.error(f"K 线数据同步失败：{e}")
    
    async def _do_sync_quotes(self, limit_stocks: int = 50):
        """执行实时行情同步
        
        Args:
            limit_stocks: 每次同步的股票数量限制
        """
        logger.debug("开始同步实时行情...")
        
        try:
            # 获取股票列表
            stock_list = await local_db_service.get_stock_list_from_db()
            
            if not stock_list:
                return
            
            # 只同步前 N 只热门股票
            stocks_to_sync = stock_list[:limit_stocks]
            
            # 使用统一存储层
            quote_storage = storage_manager.get_quote_storage()
            
            for stock in stocks_to_sync:
                try:
                    # 从数据源获取实时行情
                    quote_data = await data_source_manager.get_realtime_quote(
                        code=stock.code
                    )
                    
                    if quote_data:
                        # 使用统一存储层（自动同步到数据库，缓存 30 秒）
                        await quote_storage.set(stock.code, [quote_data])
                    
                    # 避免请求过快
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.debug(f"获取行情失败 {stock.code}: {e}")
                    continue
            
            logger.debug(f"实时行情同步完成")
            
        except Exception as e:
            logger.error(f"实时行情同步失败：{e}")


# 全局实例
data_sync_scheduler = DataSyncScheduler()
