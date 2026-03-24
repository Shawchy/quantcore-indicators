"""
WebSocket 数据推送服务
负责从数据源获取实时数据并推送给订阅的客户端
"""
import asyncio
from typing import List, Dict, Any, Optional, Set
from datetime import datetime, timedelta
from loguru import logger

from app.websocket.manager import connection_manager
from app.adapters.factory import data_source_manager


class RealtimeDataPusher:
    """
    实时数据推送服务
    
    功能:
    1. 定期获取实时行情数据
    2. 推送给订阅的客户端
    3. 支持多种数据类型（个股、板块、资金流等）
    4. 智能推送频率控制
    """
    
    def __init__(self):
        # 推送任务 {task_name: task}
        self.tasks: Dict[str, asyncio.Task] = {}
        # 推送间隔配置（秒）
        self.intervals = {
            "quote": 3,          # 个股实时行情
            "tick": 5,           # 成交明细
            "market": 5,         # 市场板块行情
            "moneyflow": 10,     # 资金流向
            "board": 10,         # 龙虎榜
        }
        # 订阅的股票代码集合
        self.subscribed_stocks: Set[str] = set()
        # 是否正在运行
        self._running = False
    
    async def start(self):
        """启动推送服务"""
        if self._running:
            logger.warning("推送服务已在运行中")
            return
        
        self._running = True
        logger.info("实时数据推送服务已启动")
        
        # 启动各类数据推送任务
        self.tasks["market_pusher"] = asyncio.create_task(
            self._push_market_quotes()
        )
        
        # 监控订阅变化并启动个股推送
        self.tasks["stock_monitor"] = asyncio.create_task(
            self._monitor_stock_subscriptions()
        )
    
    async def stop(self):
        """停止推送服务"""
        if not self._running:
            return
        
        self._running = False
        
        # 取消所有任务
        for task_name, task in self.tasks.items():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self.tasks.clear()
        logger.info("实时数据推送服务已停止")
    
    async def _monitor_stock_subscriptions(self):
        """监控股票订阅变化并启动/停止个股推送任务"""
        last_subscribed = set()
        
        while self._running:
            try:
                # 获取当前订阅的股票代码
                current_subscribed = set()
                if "stock" in connection_manager.subscriptions:
                    current_subscribed = set(
                        topic.split(":")[1] 
                        for topic in connection_manager.subscriptions.keys()
                        if topic.startswith("stock:")
                    )
                
                # 检测变化
                added = current_subscribed - last_subscribed
                removed = last_subscribed - current_subscribed
                
                # 启动新增股票的推送
                for code in added:
                    task_name = f"stock_{code}"
                    if task_name not in self.tasks:
                        self.tasks[task_name] = asyncio.create_task(
                            self._push_single_stock(code)
                        )
                        logger.info(f"启动股票推送 - {code}")
                
                # 停止移除的股票推送
                for code in removed:
                    task_name = f"stock_{code}"
                    if task_name in self.tasks:
                        self.tasks[task_name].cancel()
                        del self.tasks[task_name]
                        logger.info(f"停止股票推送 - {code}")
                
                self.subscribed_stocks = current_subscribed
                last_subscribed = current_subscribed
                
                # 每秒检查一次
                await asyncio.sleep(1)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"监控股票订阅异常：{e}")
                await asyncio.sleep(5)
    
    async def _push_single_stock(self, code: str):
        """
        推送单只股票的实时行情
        
        Args:
            code: 股票代码
        """
        topic = f"stock:{code}"
        
        while self._running and topic in connection_manager.subscriptions:
            try:
                # 检查是否有订阅者
                if connection_manager.get_subscriber_count(topic) == 0:
                    await asyncio.sleep(1)
                    continue
                
                # 获取实时行情
                quote_data = await self._fetch_stock_quote(code)
                
                if quote_data:
                    # 推送数据
                    message = {
                        "type": "data",
                        "event": "quote_update",
                        "topic": topic,
                        "data": {
                            "ts_code": code,
                            "timestamp": datetime.now().isoformat(),
                            "quote": quote_data
                        }
                    }
                    
                    await connection_manager.broadcast_to_topic(topic, message)
                
                # 等待下次推送
                await asyncio.sleep(self.intervals["quote"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"推送股票 {code} 行情异常：{e}")
                await asyncio.sleep(5)
    
    async def _fetch_stock_quote(self, code: str) -> Optional[Dict[str, Any]]:
        """
        获取股票实时行情
        
        Args:
            code: 股票代码
            
        Returns:
            行情数据字典
        """
        try:
            # 使用数据源管理器获取实时行情
            quote = await data_source_manager.get_realtime_quote(code)
            
            if quote:
                return {
                    "price": quote.get("price", 0),
                    "change": quote.get("change", 0),
                    "change_pct": quote.get("change_pct", 0),
                    "open": quote.get("open", 0),
                    "high": quote.get("high", 0),
                    "low": quote.get("low", 0),
                    "close": quote.get("close", 0),
                    "volume": quote.get("volume", 0),
                    "amount": quote.get("amount", 0),
                    "bid": quote.get("bid", []),
                    "ask": quote.get("ask", []),
                }
            return None
            
        except Exception as e:
            logger.error(f"获取股票 {code} 行情失败：{e}")
            return None
    
    async def _push_market_quotes(self):
        """推送市场板块行情数据"""
        topic = "market:quotes"
        
        while self._running:
            try:
                # 检查是否有订阅者
                if connection_manager.get_subscriber_count(topic) > 0:
                    # 获取市场实时行情
                    market_data = await self._fetch_market_quotes()
                    
                    if market_data:
                        message = {
                            "type": "data",
                            "event": "market_update",
                            "topic": topic,
                            "data": {
                                "timestamp": datetime.now().isoformat(),
                                "quotes": market_data
                            }
                        }
                        
                        await connection_manager.broadcast_to_topic(topic, message)
                
                # 等待下次推送
                await asyncio.sleep(self.intervals["market"])
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"推送市场行情异常：{e}")
                await asyncio.sleep(5)
    
    async def _fetch_market_quotes(self) -> Optional[List[Dict[str, Any]]]:
        """
        获取市场实时行情
        
        Returns:
            行情数据列表
        """
        try:
            # 获取沪深 A 股行情
            data = await data_source_manager.get_market_realtime_quotes(
                market_types=["沪深 A 股"],
                source_type="efinance"
            )
            
            if data:
                # 简化数据，只保留关键字段
                simplified = []
                for quote in data[:100]:  # 限制前 100 只
                    simplified.append({
                        "ts_code": quote.get("ts_code", ""),
                        "name": quote.get("name", ""),
                        "price": quote.get("price", 0),
                        "change_pct": quote.get("change_pct", 0),
                        "volume": quote.get("volume", 0),
                        "amount": quote.get("amount", 0),
                    })
                return simplified
            
            return None
            
        except Exception as e:
            logger.error(f"获取市场行情失败：{e}")
            return None


# 全局推送服务实例
data_pusher = RealtimeDataPusher()


async def start_pusher_service():
    """启动推送服务（应用启动时调用）"""
    await data_pusher.start()
    logger.info("WebSocket 数据推送服务已启动")


async def stop_pusher_service():
    """停止推送服务（应用关闭时调用）"""
    await data_pusher.stop()
    logger.info("WebSocket 数据推送服务已停止")
