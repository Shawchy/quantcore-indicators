"""
FastAPI WebSocket 端点 - TickFlow 实时行情代理

提供WebSocket接口供前端连接，实现：
- 客户端连接管理
- 订阅/退订代理
- 行情数据转发
- 心跳检测
- 自动重连

API端点：
- WS /api/v1/ws/quotes - 实时行情WebSocket

前端使用示例：
```javascript
const ws = new WebSocket('ws://localhost:8000/api/v1/ws/quotes');

// 连接成功后订阅
ws.send(JSON.stringify({
  op: 'subscribe',
  symbols: ['000001', '600000']
}));

// 接收行情数据
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  if (data.op === 'quotes') {
    console.log('行情更新:', data.data);
  }
};
```
"""

import asyncio
import json
import uuid
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from loguru import logger

router = APIRouter()


class ConnectionManager:
    """
    WebSocket连接管理器
    
    管理所有客户端的WebSocket连接，
    处理订阅关系和数据分发。
    """
    
    def __init__(self):
        self._connections: Dict[str, Dict] = {}
        self._symbol_subscribers: Dict[str, Set[str]] = {}  # symbol -> {client_ids}
        
    async def connect(self, websocket: WebSocket) -> str:
        """接受新连接"""
        await websocket.accept()
        client_id = str(uuid.uuid4())[:8]
        
        self._connections[client_id] = {
            "websocket": websocket,
            "client_id": client_id,
            "subscribed_symbols": set(),
            "connected_at": datetime.now(),
            "last_activity": datetime.now(),
        }
        
        logger.info(f"✅ WebSocket客户端连接: {client_id} (总计: {len(self._connections)})")
        return client_id
    
    def disconnect(self, client_id: str):
        """断开连接"""
        if client_id in self._connections:
            conn = self._connections.pop(client_id)
            
            # 清理订阅关系
            for symbol in conn["subscribed_symbols"]:
                if symbol in self._symbol_subscribers:
                    self._symbol_subscribers[symbol].discard(client_id)
                    if not self._symbol_subscribers[symbol]:
                        del self._symbol_subscribers[symbol]
            
            logger.info(f"❌ WebSocket客户端断开: {client_id} (剩余: {len(self._connections)})")
    
    def subscribe(self, client_id: str, symbols: List[str]) -> bool:
        """客户端订阅标的"""
        if client_id not in self._connections:
            return False
        
        conn = self._connections[client_id]
        
        for symbol in symbols:
            conn["subscribed_symbols"].add(symbol)
            
            if symbol not in self._symbol_subscribers:
                self._symbol_subscribers[symbol] = set()
            self._symbol_subscribers[symbol].add(client_id)
        
        logger.debug(f"📌 客户端 {client_id} 订阅: {symbols}")
        return True
    
    def unsubscribe(self, client_id: str, symbols: List[str]) -> bool:
        """客户端退订标的"""
        if client_id not in self._connections:
            return False
        
        conn = self._connections[client_id]
        
        for symbol in symbols:
            conn["subscribed_symbols"].discard(symbol)
            
            if symbol in self._symbol_subscribers:
                self._symbol_subscribers[symbol].discard(client_id)
                if not self._symbol_subscribers[symbol]:
                    del self._symbol_subscribers[symbol]
        
        logger.debug(f"🔗 客户端 {client_id} 退订: {symbols}")
        return True
    
    async def send_to_client(
        self, 
        client_id: str, 
        message: Dict[str, Any],
        exclude_op: Optional[str] = None
    ):
        """发送消息给指定客户端"""
        if client_id not in self._connections:
            return False
        
        conn = self._connections[client_id]
        
        # 过滤消息类型（可选）
        if exclude_op and message.get("op") == exclude_op:
            return True
        
        try:
            json_msg = json.dumps(message, ensure_ascii=False)
            await conn["websocket"].send_text(json_msg)
            conn["last_activity"] = datetime.now()
            return True
            
        except Exception as e:
            logger.warning(f"发送给客户端 {client_id} 失败: {e}")
            return False
    
    async def broadcast_quotes(self, quotes_data: Dict[str, Any]):
        """广播行情数据给所有相关订阅者"""
        sent_count = 0
        
        for code, quote_data in quotes_data.items():
            subscribers = self._symbol_subscribers.get(code, set())
            
            message = {
                "op": "quotes",
                "data": {code: quote_data},
                "timestamp": datetime.now().isoformat()
            }
            
            json_msg = json.dumps(message, ensure_ascii=False)
            
            for client_id in subscribers:
                try:
                    conn = self._connections.get(client_id)
                    if conn:
                        await conn["websocket"].send_text(json_msg)
                        conn["last_activity"] = datetime.now()
                        sent_count += 1
                        
                except Exception as e:
                    logger.debug(f"广播失败 ({client_id}): {e}")
        
        return sent_count
    
    async def send_subscription_status(self, client_id: str):
        """发送当前订阅状态"""
        if client_id not in self._connections:
            return
        
        conn = self._connections[client_id]
        
        status_message = {
            "op": "subscribed",
            "symbols": list(conn["subscribed_symbols"]),
            "total": len(conn["subscribed_symbols"])
        }
        
        await self.send_to_client(client_id, status_message)
    
    def get_client_info(self, client_id: str) -> Optional[Dict]:
        """获取客户端信息"""
        return self._connections.get(client_id)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        total_subs = sum(
            len(c["subscribed_symbols"]) 
            for c in self._connections.values()
        )
        
        return {
            "connected_clients": len(self._connections),
            "total_subscriptions": total_subs,
            "unique_symbols": len(self._symbol_subscribers),
            "top_symbols": sorted(
                self._symbol_subscribers.keys(),
                key=lambda s: len(self._symbol_subscribers[s]),
                reverse=True
            )[:10]
        }


# 全局连接管理器实例
connection_manager = ConnectionManager()


@router.websocket("/quotes")
async def websocket_quotes_endpoint(websocket: WebSocket):
    """
    实时行情WebSocket端点
    
    协议说明：
    1. 客户端连接后获得唯一client_id
    2. 发送 {"op": "subscribe", "symbols": [...]} 进行订阅
    3. 收到 {"op": "subscribed", "symbols": [...]} 确认
    4. 持续收到 {"op": "quotes", "data": {...}} 行情推送
    5. 可随时发送 subscribe/unsubscribe 动态调整
    
    消息格式：
    - 订阅:   {"op": "subscribe", "symbols": ["000001", "600000"]}
    - 退订:   {"op": "unsubscribe", "symbols": ["000001"]}
    - 响应:   {"op": "subscribed", "symbols": [...], "total": N}
    - 行情:   {"op": "quotes", "data": {"000001": {...}}, "timestamp": "..."}
    - 错误:   {"op": "error", "message": "..."}
    """
    client_id = await connection_manager.connect(websocket)
    
    # 尝试获取TickFlow服务
    from app.services.tickflow_websocket import get_tickflow_ws_service
    tickflow_service = get_tickflow_ws_service()
    
    # 注册到TickFlow服务
    if tickflow_service:
        await tickflow_service.register_client(client_id, websocket)
    
    # 设置行情回调（仅第一次连接时设置）
    is_callback_set = [False]  # 使用列表以便在闭包中修改
    
    def setup_tickflow_callback():
        if not tickflow_service or is_callback_set[0]:
            return
            
        @tickflow_service.on_quotes
        async def on_tickflow_quotes(quotes):
            """转发TickFlow行情给所有订阅该标的的客户端"""
            quotes_dict = {}
            for q in quotes:
                code = TickFlowWebSocketService._normalize_symbol(q.get("symbol", ""))
                quotes_dict[code] = q
            
            await connection_manager.broadcast_quotes(quotes_dict)
        
        is_callback_set[0] = True
    
    try:
        # 如果TickFlow已连接，立即设置回调并推送缓存数据
        if tickflow_service and tickflow_service._is_connected:
            setup_tickflow_callback()
            
            # 推送当前缓存
            cached_quotes = tickflow_service.get_all_cached_quotes()
            if cached_quotes:
                initial_message = {
                    "op": "quotes",
                    "data": cached_quotes,
                    "timestamp": datetime.now().isoformat(),
                    "_type": "initial_snapshot"
                }
                await connection_manager.send_to_client(client_id, initial_message)
        
        # 主消息循环
        while True:
            raw_data = await websocket.receive_text()
            
            try:
                message = json.loads(raw_data)
                op = message.get("op", "")
                
                if op == "subscribe":
                    symbols = message.get("symbols", [])
                    
                    if not symbols:
                        error_msg = {"op": "error", "message": "symbols不能为空"}
                        await connection_manager.send_to_client(client_id, error_msg)
                        continue
                    
                    # 本地订阅
                    connection_manager.subscribe(client_id, symbols)
                    
                    # 转发到TickFlow
                    if tickflow_service and tickflow_service._is_connected:
                        tickflow_symbols = [
                            f"{s}.SH" if s.startswith("6") else f"{s}.SZ"
                            for s in symbols
                        ]
                        success = await tickflow_service.client_subscribe(
                            client_id, 
                            tickflow_symbols
                        )
                        
                        if not success:
                            error_msg = {
                                "op": "error",
                                "message": "订阅失败（可能超出限制）"
                            }
                            await connection_manager.send_to_client(client_id, error_msg)
                            continue
                    
                    # 回复订阅状态
                    await connection_manager.send_subscription_status(client_id)
                    
                    logger.info(f"📌 客户端 {client_id} 订阅: {symbols}")
                
                elif op == "unsubscribe":
                    symbols = message.get("symbols", [])
                    
                    connection_manager.unsubscribe(client_id, symbols)
                    
                    if tickflow_service and tickflow_service._is_connected:
                        tickflow_symbols = [
                            f"{s}.SH" if s.startswith("6") else f"{s}.SZ"
                            for s in symbols
                        ]
                        await tickflow_service.client_unsubscribe(
                            client_id,
                            tickflow_symbols
                        )
                    
                    await connection_manager.send_subscription_status(client_id)
                    
                    logger.info(f"🔗 客户端 {client_id} 退订: {symbols}")
                
                elif op == "ping":
                    # 心跳响应
                    pong_msg = {"op": "pong", "timestamp": datetime.now().isoformat()}
                    await connection_manager.send_to_client(client_id, pong_msg)
                
                elif op == "status":
                    # 查询状态
                    status = {
                        "op": "status",
                        "client_id": client_id,
                        "tickflow_connected": (
                            tickflow_service._is_connected 
                            if tickflow_service else False
                        ),
                        "subscribed_symbols": list(
                            connection_manager.get_client_info(client_id)["subscribed_symbols"]
                        ) if connection_manager.get_client_id(client_id) else [],
                        "server_time": datetime.now().isoformat()
                    }
                    await connection_manager.send_to_client(client_id, status)
                
                else:
                    warning_msg = {
                        "op": "warning",
                        "message": f"未知操作: {op}"
                    }
                    await connection_manager.send_to_client(client_id, warning_msg)
                    
            except json.JSONDecodeError:
                error_msg = {
                    "op": "error",
                    "message": "JSON格式错误"
                }
                await connection_manager.send_to_client(client_id, error_msg)
                
    except WebSocketDisconnect:
        logger.info(f"⚠️  WebSocket断开: {client_id}")
        
    except Exception as e:
        logger.error(f"❌ WebSocket异常 ({client_id}): {e}", exc_info=True)
        
    finally:
        # 清理
        connection_manager.disconnect(client_id)
        
        if tickflow_service:
            await tickflow_service.remove_client(client_id)


@router.get("/ws/status")
async def get_websocket_status():
    """获取WebSocket服务状态"""
    from app.services.tickflow_websocket import get_tickflow_ws_service
    
    stats = connection_manager.get_statistics()
    
    tickflow_service = get_tickflow_ws_service()
    tickflow_status = tickflow_service.get_status() if tickflow_service else {
        "connected": False,
        "available": False,
        "message": "服务未初始化"
    }
    
    return {
        "success": True,
        "data": {
            **stats,
            "tickflow": tickflow_status,
            "endpoint": "/api/v1/ws/quotes"
        },
        "timestamp": datetime.now().isoformat()
    }


# 需要在文件末尾导入以避免循环引用
from app.services.tickflow_websocket import TickFlowWebSocketService


__all__ = ["router", "connection_manager"]
