"""
TickFlow WebSocket 实时行情服务

基于TickFlow官方API实现的WebSocket实时行情推送系统。

核心功能：
- WebSocket长连接管理（自动重连、心跳保活）
- 智能订阅管理（去重、批量、动态增减）
- 实时行情数据接收与分发
- 多客户端支持（广播/单播）
- 与智能轮询系统无缝集成

使用场景：
- 股票实时行情（毫秒级延迟）
- 指数实时数据
- 高频交易信号
- 盘口异动监控

架构设计：
┌──────────┐     ┌─────────────┐     ┌──────────────┐
│  前端    │ ←→ │ FastAPI WS   │ ←→ │ TickFlow WSS  │
│ (React)  │     │ (代理/转发)  │     │ (数据源)      │
└──────────┘     └──────┬──────┘     └──────────────┘
                        │
                   ┌────▼────┐
                   │ 缓存层   │
                   │ 分发器   │
                   └─────────┘
"""

import asyncio
import json
import time
from typing import Dict, List, Any, Optional, Callable, Set, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from loguru import logger

try:
    import websockets
    from websockets.client import connect as ws_connect
    from websockets.exceptions import ConnectionClosed, InvalidHandshake
    WEBSOCKETS_AVAILABLE = True
except ImportError:
    WEBSOCKETS_AVAILABLE = False
    logger.warning("websockets库未安装，TickFlow WebSocket功能不可用")


class OperationType(str, Enum):
    """操作类型"""
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SUBSCRIBED = "subscribed"
    QUOTES = "quotes"
    ERROR = "error"


@dataclass
class QuoteData:
    """行情数据模型"""
    symbol: str           # 标的代码 (如 "600000.SH")
    region: str           # 地区 (CN, US)
    last_price: float     # 最新价
    prev_close: float     # 昨收价
    open_price: float     # 开盘价
    high: float           # 最高价
    low: float            # 最低价
    volume: int           # 成交量(手)
    amount: float         # 成交额(元)
    timestamp: int        # 时间戳(毫秒)
    
    # 扩展字段
    change: float = 0.0          # 涨跌额
    change_pct: float = 0.0      # 涨跌幅%
    turnover_rate: float = 0.0   # 换手率%
    amplitude: float = 0.0       # 振幅%
    speed: float = 0.0           # 涨速
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "symbol": self.symbol,
            "region": self.region,
            "last_price": self.last_price,
            "prev_close": self.prev_close,
            "open": self.open_price,
            "high": self.high,
            "low": self.low,
            "volume": self.volume,
            "amount": self.amount,
            "timestamp": self.timestamp,
            "change": self.change,
            "change_pct": self.change_pct,
            "turnover_rate": self.turnover_rate,
            "amplitude": self.amplitude,
            "speed": self.speed,
        }
    
    @classmethod
    def from_tickflow(cls, data: Dict) -> 'QuoteData':
        """从TickFlow格式转换"""
        last_price = data.get('last_price', 0) or 0
        prev_close = data.get('prev_close', 0) or 0
        
        if prev_close != 0:
            change = round(last_price - prev_close, 2)
            change_pct = round(change / abs(prev_close) * 100, 2)
        else:
            change = 0
            change_pct = 0
        
        high = data.get('high', 0) or 0
        low = data.get('low', 0) or 0
        
        if low != 0:
            amplitude = round((high - low) / abs(low) * 100, 2)
        else:
            amplitude = 0
        
        return cls(
            symbol=data.get('symbol', ''),
            region=data.get('region', 'CN'),
            last_price=last_price,
            prev_close=prev_close,
            open_price=data.get('open', 0) or 0,
            high=high,
            low=low,
            volume=int(data.get('volume', 0) or 0),
            amount=float(data.get('amount', 0) or 0),
            timestamp=int(data.get('timestamp', 0) or 0),
            change=change,
            change_pct=change_pct,
            turnover_rate=float(data.get('turnover_rate', 0) or 0),
            amplitude=amplitude,
            speed=float(data.get('speed', 0) or 0),
        )


@dataclass 
class ClientConnection:
    """客户端连接信息"""
    client_id: str
    websocket: Any = None
    subscribed_symbols: Set[str] = field(default_factory=set)
    connected_at: datetime = field(default_factory=datetime.now)
    last_activity: datetime = field(default_factory=datetime.now)


class TickFlowWebSocketService:
    """
    TickFlow WebSocket 服务
    
    管理：
    - 与TickFlow服务器的长连接
    - 客户端订阅关系
    - 行情数据的缓存与分发
    - 自动重连与错误恢复
    
    使用示例：
        >>> service = TickFlowWebSocketService(api_key="your-key")
        >>> await service.connect()
        >>> await service.subscribe(["000001.SZ", "600000.SH"])
        
        # 设置回调
        @service.on_quotes
        def handle_quotes(quotes):
            print(f"收到 {len(quotes)} 条行情")
    """
    
    TICKFLOW_WS_URL = "wss://api.tickflow.org/v1/ws/quotes"
    
    PING_INTERVAL = 30       # 心跳间隔（秒）
    RECONNECT_DELAY = 5      # 重连延迟（秒）
    MAX_RECONNECT_ATTEMPTS = 10  # 最大重连次数
    
    def __init__(self, api_key: str = "", max_subscriptions: int = 50):
        if not api_key:
            from app.config import settings
            api_key = getattr(settings, 'TICKFLOW_API_KEY', '')
        
        self.api_key = api_key
        self.max_subscriptions = max_subscriptions
        
        self._ws_connection: Optional[Any] = None
        self._is_connected: bool = False
        self._reconnect_attempts: int = 0
        
        self._subscribed_symbols: Set[str] = set()
        self._pending_subscriptions: Set[str] = set()
        
        self._quote_cache: Dict[str, QuoteData] = {}
        self._clients: Dict[str, ClientConnection] = {}
        
        self._callbacks: Dict[str, List[Callable]] = {
            "quotes": [],
            "error": [],
            "connected": [],
            "disconnected": [],
            "subscription_changed": []
        }
        
        self._background_task: Optional[asyncio.Task] = None
        self._ping_task: Optional[asyncio.Task] = None
        
        self._lock = asyncio.Lock()
        
        logger.info(f"TickFlowWebSocketService 初始化 (max={max_subscriptions})")
    
    async def connect(self) -> bool:
        """
        连接到TickFlow WebSocket服务器
        
        Returns:
            bool: 是否成功连接
        """
        if not WEBSOCKETS_AVAILABLE:
            raise RuntimeError("websockets库未安装，请运行: pip install websockets")
        
        if not self.api_key:
            raise ValueError("未配置TICKFLOW_API_KEY，请在.env文件中设置")
        
        try:
            url = f"{self.TICKFLOW_WS_URL}?api_key={self.api_key}"
            
            logger.info(f"正在连接TickFlow WebSocket...")
            
            self._ws_connection = await ws_connect(
                url,
                ping_interval=self.PING_INTERVAL,
                ping_timeout=10,
                close_timeout=5,
                compression=None  # 使用默认压缩
            )
            
            self._is_connected = True
            self._reconnect_attempts = 0
            
            logger.success("✅ TickFlow WebSocket 连接成功")
            
            for callback in self._callbacks["connected"]:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"连接回调执行失败: {e}")
            
            self._background_task = asyncio.create_task(self._message_loop())
            self._ping_task = asyncio.create_task(self._keep_alive())
            
            return True
            
        except InvalidHandshake as e:
            status_code = getattr(e, 'status_code', None)
            if status_code in [401, 403]:
                logger.error(f"❌ TickFlow认证失败 ({status_code}): 请检查API Key和套餐权限")
                raise PermissionError(f"认证失败: HTTP {status_code}")
            else:
                logger.error(f"❌ 握手失败: {e}")
                raise
                
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            self._is_connected = False
            raise
    
    async def disconnect(self):
        """断开连接"""
        logger.info("正在断开TickFlow WebSocket...")
        
        self._is_connected = False
        
        if self._background_task and not self._background_task.done():
            self._background_task.cancel()
            try:
                await self._background_task
            except asyncio.CancelledError:
                pass
        
        if self._ping_task and not self._ping_task.done():
            self._ping_task.cancel()
            try:
                await self._ping_task
            except asyncio.CancelledError:
                pass
        
        if self._ws_connection:
            try:
                await self._ws_connection.close()
            except:
                pass
            self._ws_connection = None
        
        for callback in self._callbacks["disconnected"]:
            try:
                callback()
            except Exception as e:
                logger.error(f"断开回调失败: {e}")
        
        logger.info("✅ TickFlow WebSocket 已断开")
    
    async def subscribe(self, symbols: List[str]) -> bool:
        """
        订阅标的行情
        
        Args:
            symbols: 标的代码列表 ["000001.SZ", "600000.SH"]
            
        Returns:
            bool: 是否成功
        """
        if not self._is_connected:
            logger.warning("未连接，无法订阅")
            return False
        
        async with self._lock:
            new_symbols = set(symbols) - self._subscribed_symbols
            total_after = len(self._subscribed_symbols) + len(new_symbols)
            
            if total_after > self.max_subscriptions:
                logger.error(
                    f"超出订阅上限 {total_after}/{self.max_subscriptions} "
                    f"(当前:{len(self._subscribed_symbols)}, 新增:{len(new_symbols)})"
                )
                
                error_msg = {
                    "op": OperationType.ERROR.value,
                    "message": (
                        f"exceeded max {self.max_subscriptions} symbols "
                        f"(current: {len(self._subscribed_symbols)}, requested: +{len(new_symbols)})"
                    )
                }
                
                for cb in self._callbacks["error"]:
                    try:
                        cb(error_msg["message"])
                    except:
                        pass
                    
                return False
            
            if not new_symbols:
                logger.debug(f"所有标的已订阅: {symbols}")
                return True
            
            message = {
                "op": OperationType.SUBSCRIBE.value,
                "symbols": list(new_symbols)
            }
            
            try:
                await self._send_message(message)
                logger.info(f"发送订阅请求: {new_symbols}")
                return True
                
            except Exception as e:
                logger.error(f"订阅失败: {e}")
                return False
    
    async def unsubscribe(self, symbols: List[str]) -> bool:
        """
        退订标的行情
        
        Args:
            symbols: 要退订的标的列表
            
        Returns:
            bool: 是否成功
        """
        if not self._is_connected:
            return False
        
        to_unsubscribe = set(symbols) & self._subscribed_symbols
        
        if not to_unsubscribe:
            return True
        
        message = {
            "op": OperationType.UNSUBSCRIBE.value,
            "symbols": list(to_unsubscribe)
        }
        
        try:
            await self._send_message(message)
            logger.info(f"发送退订请求: {to_unsubscribe}")
            return True
        except Exception as e:
            logger.error(f"退订失败: {e}")
            return False
    
    async def _send_message(self, message: Dict):
        """发送JSON消息"""
        if self._ws_connection:
            json_str = json.dumps(message, ensure_ascii=False)
            await self._ws_connection.send(json_str)
    
    async def _message_loop(self):
        """消息接收循环（后台任务）"""
        logger.info("📡 消息循环启动")
        
        while self._is_connected and self._ws_connection:
            try:
                raw_message = await asyncio.wait_for(
                    self._ws_connection.recv(),
                    timeout=self.PING_INTERVAL * 2
                )
                
                if isinstance(raw_message, bytes):
                    raw_message = raw_message.decode('utf-8')
                
                await self._handle_message(raw_message)
                
            except asyncio.TimeoutError:
                logger.warning("⏰ 接收超时，检查连接状态...")
                continue
                
            except ConnectionClosed as e:
                logger.warning(f"🔌 连接关闭: {e.code} - {e.reason}")
                break
                
            except Exception as e:
                logger.error(f"消息处理异常: {e}", exc_info=True)
                continue
        
        logger.info("📡 消息循环结束")
        
        if self._is_connected:
            await self._handle_reconnect()
    
    async def _handle_message(self, raw_message: str):
        """处理收到的消息"""
        try:
            message = json.loads(raw_message)
            op = message.get("op", "")
            
            if op == OperationType.SUBSCRIBED.value:
                await self._handle_subscription_response(message)
                
            elif op == OperationType.QUOTES.value:
                await self._handle_quotes_push(message)
                
            elif op == OperationType.ERROR.value:
                error_msg = message.get("message", "未知错误")
                logger.error(f"❌ TickFlow错误: {error_msg}")
                
                for cb in self._callbacks["error"]:
                    try:
                        cb(error_msg)
                    except Exception as e:
                        logger.error(f"错误回调执行失败: {e}")
                        
            else:
                logger.warning(f"未知操作类型: {op}, 消息: {raw_message[:200]}")
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}, 原始消息: {raw_message[:200]}")
        except Exception as e:
            logger.error(f"消息处理失败: {e}", exc_info=True)
    
    async def _handle_subscription_response(self, message: Dict):
        """处理订阅响应"""
        symbols = message.get("symbols", [])
        total = message.get("total", 0)
        
        async with self._lock:
            self._subscribed_symbols = set(symbols)
        
        logger.info(f"✅ 订阅状态更新: {total}个标的")
        
        for cb in self._callbacks["subscription_changed"]:
            try:
                cb(list(self._subscribed_symbols))
            except Exception as e:
                logger.error(f"订阅变更回调失败: {e}")
    
    async def _handle_quotes_push(self, message: Dict):
        """处理行情推送"""
        quotes_data = message.get("data", [])
        
        if not quotes_data:
            return
        
        quotes = []
        updated_codes = []
        
        for qd in quotes_data:
            quote = QuoteData.from_tickflow(qd)
            quotes.append(quote)
            
            code = self._normalize_symbol(quote.symbol)
            self._quote_cache[code] = quote
            updated_codes.append(code)
        
        logger.debug(f"📊 收到 {len(quotes)} 条行情更新: {updated_codes}")
        
        for cb in self._callbacks["quotes"]:
            try:
                cb([q.to_dict() for q in quotes])
            except Exception as e:
                logger.error(f"行情回调执行失败: {e}")
        
        await self._broadcast_to_clients(updated_codes)
    
    async def _broadcast_to_clients(self, codes: List[str]):
        """向已连接的客户端广播行情"""
        broadcast_data = {}
        
        for code in codes:
            if code in self._quote_cache:
                broadcast_data[code] = self._quote_cache[code].to_dict()
        
        if not broadcast_data:
            return
        
        message = {
            "op": "quotes",
            "data": broadcast_data,
            "timestamp": datetime.now().isoformat()
        }
        
        json_msg = json.dumps(message, ensure_ascii=False)
        
        disconnected_clients = []
        
        for client_id, client in self._clients.items():
            if client.websocket is None:
                continue
            
            client_symbols = {
                self._normalize_symbol(s) for s in client.subscribed_symbols
            }
            
            relevant_data = {
                k: v for k, v in broadcast_data.items() 
                if k in client_symbols
            }
            
            if relevant_data:
                try:
                    filtered_msg = json.dumps({
                        "op": "quotes",
                        "data": relevant_data,
                        "timestamp": datetime.now().isoformat()
                    }, ensure_ascii=False)
                    await client.websocket.send_text(filtered_msg)
                    client.last_activity = datetime.now()
                    
                except Exception as e:
                    logger.debug(f"客户端 {client_id} 发送失败: {e}")
                    disconnected_clients.append(client_id)
        
        for client_id in disconnected_clients:
            await self._remove_client(client_id)
    
    async def _keep_alive(self):
        """心跳保活"""
        while self._is_connected:
            await asyncio.sleep(self.PING_INTERVAL)
            
            if self._is_connected and self._ws_connection:
                try:
                    pong = await self._ws_connection.ping()
                    if pong:
                        logger.debug("💓 心跳正常")
                        
                except Exception as e:
                    logger.warning(f"💔 心跳失败: {e}")
                    break
    
    async def _handle_reconnect(self):
        """自动重连"""
        if self._reconnect_attempts >= self.MAX_RECONNECT_ATTEMPTS:
            logger.error(f"❌ 达到最大重连次数 {self.MAX_RECONNECT_ATTEMPTS}，停止重连")
            self._is_connected = False
            return
        
        self._reconnect_attempts += 1
        delay = min(self.RECONNECT_DELAY * self._reconnect_attempts, 60)
        
        logger.warning(
            f"🔄 准备重连 (第{self._reconnect_attempts}次), "
            f"{delay}秒后尝试..."
        )
        
        await asyncio.sleep(delay)
        
        try:
            old_subs = list(self._subscribed_symbols)
            
            await self.connect()
            
            if old_subs:
                logger.info(f"恢复订阅: {old_subs}")
                await self.subscribe(old_subs)
                
        except Exception as e:
            logger.error(f"重连失败: {e}")
    
    def on(self, event: str, callback: Callable):
        """
        注册事件回调
        
        Args:
            event: 事件类型 ("quotes", "error", "connected", etc.)
            callback: 回调函数
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)
            logger.debug(f"注册回调: {event}")
        else:
            logger.warning(f"未知事件类型: {event}")
    
    def off(self, event: str, callback: Callable):
        """移除事件回调"""
        if event in self._callbacks and callback in self._callbacks[event]:
            self._callbacks[event].remove(callback)
    
    async def register_client(self, client_id: str, websocket: Any) -> ClientConnection:
        """注册客户端连接"""
        client = ClientConnection(client_id=client_id, websocket=websocket)
        self._clients[client_id] = client
        logger.info(f"客户端注册: {client_id} (总计: {len(self._clients)})")
        return client
    
    async def remove_client(self, client_id: str):
        """移除客户端"""
        await self._remove_client(client_id)
    
    async def _remove_client(self, client_id: str):
        """内部：移除客户端"""
        if client_id in self._clients:
            del self._clients[client_id]
            logger.info(f"客户端移除: {client_id} (剩余: {len(self._clients)})")
    
    async def client_subscribe(self, client_id: str, symbols: List[str]) -> bool:
        """客户端订阅"""
        if client_id not in self._clients:
            return False
        
        client = self._clients[client_id]
        normalized = [self._normalize_symbol(s) for s in symbols]
        client.subscribed_symbols.update(normalized)
        
        success = await self.subscribe(normalized)
        
        if success:
            logger.info(f"客户端 {client_id} 订阅: {normalized}")
        
        return success
    
    async def client_unsubscribe(self, client_id: str, symbols: List[str]) -> bool:
        """客户端退订"""
        if client_id not in self._clients:
            return False
        
        client = self._clients[client_id]
        normalized = [self._normalize_symbol(s) for s in symbols]
        client.subscribed_symbols -= set(normalized)
        
        success = await self.unsubscribe(normalized)
        
        if success:
            logger.info(f"客户端 {client_id} 退订: {normalized}")
        
        return success
    
    def get_cached_quote(self, symbol: str) -> Optional[Dict]:
        """获取缓存的行情数据"""
        code = self._normalize_symbol(symbol)
        quote = self._quote_cache.get(code)
        return quote.to_dict() if quote else None
    
    def get_all_cached_quotes(self) -> Dict[str, Dict]:
        """获取所有缓存行情"""
        return {
            code: quote.to_dict() 
            for code, quote in self._quote_cache.items()
        }
    
    def get_status(self) -> Dict[str, Any]:
        """获取服务状态"""
        return {
            "connected": self._is_connected,
            "api_key_configured": bool(self.api_key),
            "subscribed_count": len(self._subscribed_symbols),
            "subscribed_symbols": list(self._subscribed_symbols),
            "cache_size": len(self._quote_cache),
            "connected_clients": len(self._clients),
            "reconnect_attempts": self._reconnect_attempts,
            "max_subscriptions": self.max_subscriptions,
            "available": WEBSOCKETS_AVAILABLE,
        }
    
    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        """
        标准化股票代码
        
        将TickFlow格式转换为内部格式：
        - "600000.SH" → "600000"
        - "000001.SZ" → "000001"
        - "300001.SZ" → "300001"
        """
        return symbol.split('.')[0]


# 全局单例
tickflow_ws_service: Optional[TickFlowWebSocketService] = None


def get_tickflow_ws_service() -> Optional[TickFlowWebSocketService]:
    """获取全局TickFlow WebSocket服务实例"""
    global tickflow_ws_service
    
    if tickflow_ws_service is None:
        try:
            tickflow_ws_service = TickFlowWebSocketService()
        except Exception as e:
            logger.warning(f"TickFlow WebSocket服务初始化失败: {e}")
            return None
    
    return tickflow_ws_service


async def demo_usage():
    """演示用法"""
    print("=" * 70)
    print("🔌 TickFlow WebSocket 实时行情演示")
    print("=" * 70)
    
    service = get_tickflow_ws_service()
    
    if not service:
        print("\n❌ 服务初始化失败（可能缺少API Key或依赖）")
        print("请确保:")
        print("  1. 已设置环境变量 TICKFLOW_API_KEY")
        print("  2. 已安装: pip install websockets")
        return
    
    @service.on_quotes
    def on_quotes_handler(quotes):
        print(f"\n📊 收到 {len(quotes)} 条行情:")
        for q in quotes[:3]:  # 只显示前3条
            print(f"   {q['symbol']}: ¥{q['last_price']} ({q['change_pct']}%)")
    
    @service.on_error
    def on_error_handler(msg):
        print(f"\n❌ 错误: {msg}")
    
    try:
        print("\n1️⃣ 正在连接...")
        await service.connect()
        
        print("\n2️⃣ 订阅测试标的...")
        test_symbols = ["000001.SZ", "600000.SH"]
        success = await service.subscribe(test_symbols)
        
        if success:
            print(f"   ✅ 成功订阅: {test_symbols}")
            
            print("\n3️⃣ 等待行情推送 (30秒)...")
            await asyncio.sleep(30)
            
            print("\n4️⃣ 当前缓存行情:")
            cached = service.get_all_cached_quotes()
            for code, data in cached.items():
                print(f"   {code}: ¥{data['last_price']} ({data['change_pct']}%)")
            
        else:
            print("   ❌ 订阅失败")
            
    except Exception as e:
        print(f"\n❌ 异常: {e}")
        
    finally:
        if service._is_connected:
            await service.disconnect()
            print("\n5️⃣ 已断开连接")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo_usage())
