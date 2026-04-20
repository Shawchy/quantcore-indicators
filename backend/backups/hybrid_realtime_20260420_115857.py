"""
混合实时性策略 - TickFlow WS + Smart Polling

将TickFlow WebSocket作为优先数据源，
当WebSocket不可用时自动降级为智能轮询。

架构：
┌──────────────┐     ┌─────────────────┐
│   前端       │ ←→ │  FastAPI Server   │
└──────────────┘     │                   │
                      ├─ TickFlow WS ──→ 实时推送（优先）
                      │    ↓ 失败        │
                      ├─ Smart Polling → 智能轮询（降级）
                      │                  │
                      └─ Cache Layer ──→ 分层缓存
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from loguru import logger


class DataSourcePriority(str, Enum):
    """数据源优先级"""
    TICKFLOW_WS = "tickflow_ws"      # WebSocket实时（最高）
    SMART_POLLING = "smart_polling"   # 智能轮询（降级）
    CACHE_ONLY = "cache_only"         # 仅缓存（最低）


@dataclass
class HybridConfig:
    """混合模式配置"""
    prefer_websocket: bool = True           # 优先使用WebSocket
    ws_fallback_to_polling: bool = True     # WS失败时降级为轮询
    polling_interval_ms: int = 30000        # 轮询间隔
    cache_ttl_seconds: int = 30             # 缓存TTL
    max_ws_reconnect_attempts: int = 5      # 最大重连次数
    auto_switch_back: bool = True           # WS恢复后切回


class HybridRealtimeService:
    """
    混合实时行情服务
    
    自动选择最优数据源：
    1. TickFlow WebSocket（毫秒级延迟，低带宽）
    2. Smart Polling（秒级延迟，兼容性好）
    3. Cache Only（离线/降级模式）
    
    使用示例：
        >>> service = HybridRealtimeService()
        >>> await service.initialize()
        >>> 
        >>> # 获取行情（自动选择最佳数据源）
        >>> quotes = await service.get_quotes(["000001", "600000"])
        
        >>> # 监听数据源切换事件
        >>> @service.on_source_changed
        ... def on_change(old, new):
        ...     print(f"数据源: {old} → {new}")
    """
    
    def __init__(self, config: Optional[HybridConfig] = None):
        self.config = config or HybridConfig()
        
        self._current_source: DataSourcePriority = DataSourcePriority.CACHE_ONLY
        self._ws_available: bool = False
        self._last_source_change: Optional[datetime] = None
        
        self._tickflow_service = None
        self._polling_service = None
        
        self._callbacks: Dict[str, List] = {
            "source_changed": [],
            "quotes_received": [],
            "error": []
        }
        
        logger.info("HybridRealtimeService 初始化完成")
    
    async def initialize(self):
        """初始化所有服务"""
        try:
            from app.services.tickflow_websocket import get_tickflow_ws_service
            
            self._tickflow_service = get_tickflow_ws_service()
            
            if self._tickflow_service and self._tickflow_service.api_key:
                try:
                    await self._tickflow_service.connect()
                    self._ws_available = True
                    
                    @self._tickflow_service.on_quotes
                    async def on_ws_quotes(quotes):
                        await self._handle_quotes_from_ws(quotes)
                    
                    @self._tickflow_service.on_error
                    def on_ws_error(msg):
                        logger.warning(f"TickFlow错误: {msg}")
                        
                except Exception as e:
                    logger.warning(f"TickFlow连接失败，使用降级方案: {e}")
                    self._ws_available = False
            else:
                logger.info("未配置TICKFLOW_API_KEY，跳过WebSocket")
                
        except ImportError as e:
            logger.debug(f"TickFlow模块不可用: {e}")
            
        from app.services.smart_polling import smart_polling_service
        self._polling_service = smart_polling_service
        
        if self._ws_available and self.config.prefer_websocket:
            self._switch_source(DataSourcePriority.TICKFLOW_WS)
        elif self._polling_service:
            self._switch_source(DataSourcePriority.SMART_POLLING)
        else:
            self._switch_source(DataSourcePriority.CACHE_ONLY)
    
    async def get_quotes(
        self, 
        symbols: List[str],
        force_source: Optional[DataSourcePriority] = None,
        use_cache: bool = True
    ) -> Tuple[Dict[str, Any], str]:
        """
        获取实时行情（核心方法）
        
        根据当前状态自动选择最优数据源。
        
        Args:
            symbols: 股票代码列表
            force_source: 强制指定数据源（可选）
            use_cache: 是否使用缓存
            
        Returns:
            Tuple[data, source]: 行情数据和实际使用的来源
        """
        source = force_source or self._current_source
        
        if source == DataSourcePriority.TICKFLOW_WS and self._ws_available:
            return await self._get_from_ws(symbols)
            
        elif source == DataSourcePriority.SMART_POLLING and self._polling_service:
            return await self._get_from_polling(symbols)
            
        else:
            return await self._get_from_cache(symbols)
    
    async def _get_from_ws(self, symbols: List[str]) -> Tuple[Dict[str, Any], str]:
        """从WebSocket获取（读取缓存）"""
        # 使用健康检查代替简单的属性检查
        if not self._tickflow_service or not self._tickflow_service.is_connection_healthy():
            logger.warning("WebSocket 连接不健康，降级到轮询")
            return await self._fallback_to_polling(symbols)
        
        # 添加额外的检查
            return await self._fallback_to_polling(symbols)
        
        quotes = {}
        for symbol in symbols:
            cached = self._tickflow_service.get_cached_quote(symbol)
            if cached:
                quotes[symbol] = cached
        
        if quotes:
            return (quotes, "tickflow_ws")
        else:
            return await self._fallback_to_polling(symbols)
    
    async def _get_from_polling(self, symbols: List[str]) -> Tuple[Dict[str, Any], str]:
        """从智能轮询获取"""
        if not self._polling_service:
            return ({}, "error")
        
        result = await self._polling_service.get_realtime_batch(
            codes=symbols,
            user_tier="premium"
        )
        
        if result["success"] and result["data"]:
            return (result["data"], "smart_polling")
        else:
            return ({}, "error")
    
    async def _get_from_cache(self, symbols: List[str]) -> Tuple[Dict[str, Any], str]:
        """仅从缓存获取"""
        from app.services.hierarchical_cache import hierarchical_cache
        
        quotes = {}
        for symbol in symbols:
            key = f"realtime_{symbol}"
            data = await hierarchical_cache.get(key)
            if data:
                quotes[symbol] = data
        
        return (quotes, "cache")
    
    async def _fallback_to_polling(self, symbols: List[str]) -> Tuple[Dict[str, Any], str]:
        """降级到轮询"""
        old_source = self._current_source
        
        if self.config.ws_fallback_to_polling:
            self._switch_source(DataSourcePriority.SMART_POLLING)
            logger.warning("⚠️ 数据源降级: WebSocket → Smart Polling")
        
        return await self._get_from_polling(symbols)
    
    async def _handle_quotes_from_ws(self, quotes: List[Dict]):
        """处理WebSocket收到的行情"""
        for cb in self._callbacks["quotes_received"]:
            try:
                cb(quotes)
            except Exception as e:
                logger.error(f"行情回调执行失败: {e}")
    
    def _switch_source(self, new_source: DataSourcePriority):
        """切换数据源"""
        old_source = self._current_source
        
        if old_source != new_source:
            self._current_source = new_source
            self._last_source_change = datetime.now()
            
            logger.info(
                f"🔄 数据源切换: {old_source.value} → {new_source.value}"
            )
            
            for cb in self._callbacks["source_changed"]:
                try:
                    cb(old_source.value, new_source.value)
                except Exception as e:
                    logger.error(f"数据源切换回调失败: {e}")
    
    def on(self, event: str, callback):
        """注册事件回调"""
        if event in self._callbacks:
            self._callbacks[event].append(callback)
    
    def off(self, event: str, callback):
        """移除事件回调"""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        ws_status = {}
        if self._tickflow_service:
            ws_status = {
                "available": self._ws_available,
                **self._tickflow_service.get_status()
            }
        
        polling_stats = {}
        if self._polling_service:
            polling_stats = self._polling_service.get_statistics()
        
        return {
            "current_source": self._current_source.value,
            "ws_status": ws_status,
            "polling_stats": polling_stats,
            "last_source_change": (
                self._last_source_change.isoformat() 
                if self._last_source_change else None
            ),
            "config": {
                "prefer_websocket": self.config.prefer_websocket,
                "auto_switch_back": self.config.auto_switch_back,
            }
        }


# 全局单例
hybrid_realtime_service: Optional[HybridRealtimeService] = None


def get_hybrid_realtime_service() -> HybridRealtimeService:
    """获取全局混合实时服务实例"""
    global hybrid_realtime_service
    
    if hybrid_realtime_service is None:
        hybrid_realtime_service = HybridRealtimeService()
    
    return hybrid_realtime_service


async def initialize_hybrid_service():
    """初始化混合服务（应用启动时调用）"""
    service = get_hybrid_realtime_service()
    await service.initialize()
    logger.info("✅ 混合实时服务初始化完成")


if __name__ == "__main__":
    import asyncio
    
    async def demo():
        print("=" * 60)
        print("🔄 Hybrid Realtime Service Demo")
        print("=" * 60)
        
        service = HybridRealtimeService()
        
        @service.on_source_changed
        def on_source_change(old, new):
            print(f"\n📡 数据源切换: {old} → {new}")
        
        @service.on_quotes_received
        def on_quotes(quotes):
            print(f"\n📊 收到 {len(quotes)} 条行情")
        
        print("\n1️⃣ 初始化服务...")
        await service.initialize()
        
        print("\n2️⃣ 获取行情...")
        test_symbols = ["000001", "600000"]
        data, source = await service.get_quotes(test_symbols)
        
        print(f"\n3️⃣ 结果:")
        print(f"   数据源: {source}")
        print(f"   获取数量: {len(data)}")
        
        status = service.get_status()
        print(f"\n4️⃣ 状态:")
        print(f"   当前数据源: {status['current_source']}")
        print(f"   WebSocket可用: {status['ws_status'].get('available', False)}")
    
    asyncio.run(demo())
