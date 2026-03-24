"""
WebSocket 连接管理器
负责管理所有 WebSocket 连接、订阅关系和消息推送
"""
from typing import Dict, Set, Optional, List, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio
from loguru import logger
from fastapi import WebSocket
import json


@dataclass
class ClientConnection:
    """客户端连接信息"""
    websocket: WebSocket
    user_id: Optional[int] = None
    subscriptions: Set[str] = field(default_factory=set)  # 订阅的主题
    last_heartbeat: datetime = field(default_factory=datetime.now)
    is_alive: bool = True


class ConnectionManager:
    """
    WebSocket 连接管理器（单例模式）
    
    功能：
    1. 管理所有 WebSocket 连接
    2. 处理订阅/取消订阅
    3. 广播消息给特定订阅者
    4. 心跳检测
    5. 连接状态监控
    """
    
    def __init__(self):
        # 所有活跃连接 {connection_id: ClientConnection}
        self.active_connections: Dict[str, ClientConnection] = {}
        # 订阅关系 {topic: set[connection_id]}
        self.subscriptions: Dict[str, Set[str]] = {}
        # 用户到连接的映射 {user_id: set[connection_id]}
        self.user_connections: Dict[int, Set[str]] = {}
        # 心跳检测间隔（秒）
        self.heartbeat_interval = 30
        # 心跳超时时间（秒）
        self.heartbeat_timeout = 90
        # 是否正在运行心跳检测
        self._heartbeat_task: Optional[asyncio.Task] = None
        # 锁
        self._lock = asyncio.Lock()
    
    async def connect(
        self,
        websocket: WebSocket,
        connection_id: str,
        user_id: Optional[int] = None
    ) -> bool:
        """
        接受新的 WebSocket 连接
        
        Args:
            websocket: WebSocket 连接对象
            connection_id: 连接唯一标识
            user_id: 用户 ID（可选）
            
        Returns:
            是否连接成功
        """
        try:
            await websocket.accept()
            
            async with self._lock:
                connection = ClientConnection(
                    websocket=websocket,
                    user_id=user_id
                )
                self.active_connections[connection_id] = connection
                
                # 关联用户和连接
                if user_id is not None:
                    if user_id not in self.user_connections:
                        self.user_connections[user_id] = set()
                    self.user_connections[user_id].add(connection_id)
                
                logger.info(f"WebSocket 连接成功 - ID: {connection_id}, User: {user_id}")
                
                # 发送欢迎消息
                await self.send_message(
                    connection_id,
                    {
                        "type": "system",
                        "event": "connected",
                        "data": {
                            "connection_id": connection_id,
                            "timestamp": datetime.now().isoformat()
                        }
                    }
                )
                
                return True
                
        except Exception as e:
            logger.error(f"WebSocket 连接失败：{e}")
            return False
    
    async def disconnect(self, connection_id: str):
        """
        断开 WebSocket 连接
        
        Args:
            connection_id: 连接唯一标识
        """
        async with self._lock:
            if connection_id not in self.active_connections:
                return
            
            connection = self.active_connections[connection_id]
            
            # 关闭 WebSocket
            try:
                await connection.websocket.close()
            except Exception:
                pass
            
            # 从用户连接中移除
            if connection.user_id is not None:
                if connection.user_id in self.user_connections:
                    self.user_connections[connection.user_id].discard(connection_id)
                    if not self.user_connections[connection.user_id]:
                        del self.user_connections[connection.user_id]
            
            # 取消所有订阅
            for topic in connection.subscriptions:
                if topic in self.subscriptions:
                    self.subscriptions[topic].discard(connection_id)
                    if not self.subscriptions[topic]:
                        del self.subscriptions[topic]
            
            # 移除连接
            del self.active_connections[connection_id]
            
            logger.info(f"WebSocket 连接断开 - ID: {connection_id}")
    
    async def subscribe(self, connection_id: str, topic: str) -> bool:
        """
        订阅主题
        
        Args:
            connection_id: 连接 ID
            topic: 主题名称
            
        Returns:
            是否订阅成功
        """
        async with self._lock:
            if connection_id not in self.active_connections:
                logger.warning(f"订阅失败 - 连接不存在：{connection_id}")
                return False
            
            connection = self.active_connections[connection_id]
            connection.subscriptions.add(topic)
            
            if topic not in self.subscriptions:
                self.subscriptions[topic] = set()
            self.subscriptions[topic].add(connection_id)
            
            logger.info(f"订阅主题 - Connection: {connection_id}, Topic: {topic}")
            
            # 发送确认消息
            await self.send_message(
                connection_id,
                {
                    "type": "system",
                    "event": "subscribed",
                    "data": {
                        "topic": topic,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )
            
            return True
    
    async def unsubscribe(self, connection_id: str, topic: str) -> bool:
        """
        取消订阅主题
        
        Args:
            connection_id: 连接 ID
            topic: 主题名称
            
        Returns:
            是否取消成功
        """
        async with self._lock:
            if connection_id not in self.active_connections:
                return False
            
            connection = self.active_connections[connection_id]
            connection.subscriptions.discard(topic)
            
            if topic in self.subscriptions:
                self.subscriptions[topic].discard(connection_id)
                if not self.subscriptions[topic]:
                    del self.subscriptions[topic]
            
            logger.info(f"取消订阅 - Connection: {connection_id}, Topic: {topic}")
            
            # 发送确认消息
            await self.send_message(
                connection_id,
                {
                    "type": "system",
                    "event": "unsubscribed",
                    "data": {
                        "topic": topic,
                        "timestamp": datetime.now().isoformat()
                    }
                }
            )
            
            return True
    
    async def send_message(self, connection_id: str, message: dict) -> bool:
        """
        发送消息给特定连接
        
        Args:
            connection_id: 连接 ID
            message: 消息内容（字典）
            
        Returns:
            是否发送成功
        """
        if connection_id not in self.active_connections:
            return False
        
        connection = self.active_connections[connection_id]
        
        try:
            # 更新心跳时间
            connection.last_heartbeat = datetime.now()
            
            # 发送 JSON 消息
            await connection.websocket.send_json(message)
            return True
            
        except Exception as e:
            logger.error(f"发送消息失败 - Connection: {connection_id}, Error: {e}")
            # 发送失败，标记为不活跃
            connection.is_alive = False
            return False
    
    async def broadcast_to_topic(self, topic: str, message: dict, exclude_connections: Optional[Set[str]] = None):
        """
        广播消息给订阅特定主题的所有连接
        
        Args:
            topic: 主题名称
            message: 消息内容
            exclude_connections: 要排除的连接 ID 集合
        """
        if topic not in self.subscriptions:
            return
        
        subscribers = self.subscriptions[topic].copy()
        
        tasks = []
        for connection_id in subscribers:
            if exclude_connections and connection_id in exclude_connections:
                continue
            
            task = asyncio.create_task(self.send_message(connection_id, message))
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            failed = sum(1 for r in results if isinstance(r, Exception) or r is False)
            if failed > 0:
                logger.warning(f"广播消息失败 - Topic: {topic}, 失败数：{failed}/{len(tasks)}")
    
    async def broadcast_to_user(self, user_id: int, message: dict):
        """
        广播消息给特定用户的所有连接
        
        Args:
            user_id: 用户 ID
            message: 消息内容
        """
        if user_id not in self.user_connections:
            return
        
        connection_ids = self.user_connections[user_id].copy()
        
        tasks = []
        for connection_id in connection_ids:
            task = asyncio.create_task(self.send_message(connection_id, message))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def broadcast_to_all(self, message: dict):
        """
        广播消息给所有连接
        
        Args:
            message: 消息内容
        """
        connection_ids = list(self.active_connections.keys())
        
        tasks = []
        for connection_id in connection_ids:
            task = asyncio.create_task(self.send_message(connection_id, message))
            tasks.append(task)
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def update_heartbeat(self, connection_id: str):
        """
        更新连接的心跳时间
        
        Args:
            connection_id: 连接 ID
        """
        if connection_id in self.active_connections:
            self.active_connections[connection_id].last_heartbeat = datetime.now()
            self.active_connections[connection_id].is_alive = True
    
    async def start_heartbeat_checker(self):
        """启动心跳检测任务"""
        if self._heartbeat_task is not None:
            return
        
        async def check_heartbeats():
            """定期检测心跳"""
            while True:
                try:
                    await asyncio.sleep(self.heartbeat_interval)
                    
                    now = datetime.now()
                    disconnected = []
                    
                    async with self._lock:
                        for connection_id, connection in self.active_connections.items():
                            # 检查超时
                            elapsed = (now - connection.last_heartbeat).total_seconds()
                            if elapsed > self.heartbeat_timeout:
                                logger.warning(f"心跳超时 - Connection: {connection_id}, 超时：{elapsed}秒")
                                disconnected.append(connection_id)
                    
                    # 断开超时的连接
                    for connection_id in disconnected:
                        await self.disconnect(connection_id)
                        
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"心跳检测异常：{e}")
        
        self._heartbeat_task = asyncio.create_task(check_heartbeats())
        logger.info("心跳检测任务已启动")
    
    async def stop_heartbeat_checker(self):
        """停止心跳检测任务"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
            self._heartbeat_task = None
            logger.info("心跳检测任务已停止")
    
    def get_connection_count(self) -> int:
        """获取当前连接数"""
        return len(self.active_connections)
    
    def get_subscriber_count(self, topic: str) -> int:
        """获取主题的订阅者数量"""
        return len(self.subscriptions.get(topic, set()))
    
    def get_stats(self) -> dict:
        """获取连接统计信息"""
        return {
            "total_connections": len(self.active_connections),
            "total_subscriptions": len(self.subscriptions),
            "topics": {
                topic: len(subscribers)
                for topic, subscribers in self.subscriptions.items()
            }
        }


# 全局连接管理器实例
connection_manager = ConnectionManager()
