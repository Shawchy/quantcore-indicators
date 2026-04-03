"""
WebSocket 路由和端点
提供 WebSocket 连接、订阅、消息推送等功能
"""
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from typing import Optional
import asyncio
from datetime import datetime
import json

from app.websocket.manager import connection_manager, ConnectionManager
from app.api.deps import get_optional_current_user, get_current_admin_user
from app.core.security import User
from loguru import logger

router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None, description="认证 Token"),
):
    """
    WebSocket 主连接端点
    
    连接示例:
    ws://localhost:8000/api/v1/ws?token=your_jwt_token
    
    功能:
    1. 建立 WebSocket 连接
    2. 处理订阅/取消订阅请求
    3. 接收心跳
    4. 推送实时数据
    """
    # 生成连接 ID
    connection_id = f"conn_{datetime.now().timestamp()}_{id(websocket)}"
    
    # 尝试验证用户（如果提供了 token）
    user_id = None
    if token:
        try:
            from app.core.security import verify_access_token
            from jose import JWTError
            
            # 验证 JWT Token
            token_data = verify_access_token(token)
            if token_data:
                user_id = token_data.username
                logger.info(f"WebSocket 连接认证成功 - Connection: {connection_id}, User: {user_id}")
            else:
                logger.warning(f"WebSocket Token 无效 - Connection: {connection_id}")
                await websocket.close(code=4001, reason="Invalid token")
                return
        except JWTError as e:
            logger.warning(f"WebSocket Token 验证失败：{e} - Connection: {connection_id}")
            await websocket.close(code=4001, reason="Token verification failed")
            return
        except Exception as e:
            logger.warning(f"WebSocket 认证异常：{e} - Connection: {connection_id}")
            await websocket.close(code=4001, reason="Authentication error")
            return
    
    # 连接
    success = await connection_manager.connect(websocket, connection_id, user_id)
    if not success:
        return
    
    # 启动心跳检测（如果还未启动）
    await connection_manager.start_heartbeat_checker()
    
    try:
        while True:
            # 接收客户端消息
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # 处理不同类型的消息
                await handle_client_message(connection_id, message)
                
            except json.JSONDecodeError:
                # JSON 解析错误
                await connection_manager.send_message(
                    connection_id,
                    {
                        "type": "error",
                        "event": "invalid_json",
                        "data": {"message": "无效的 JSON 格式"}
                    }
                )
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开连接 - ID: {connection_id}")
    except Exception as e:
        logger.error(f"WebSocket 通信异常 - ID: {connection_id}, Error: {e}")
    finally:
        # 断开连接
        await connection_manager.disconnect(connection_id)


async def handle_client_message(connection_id: str, message: dict):
    """
    处理客户端发送的消息
    
    Args:
        connection_id: 连接 ID
        message: 消息内容
    """
    msg_type = message.get("type", "")
    event = message.get("event", "")
    data = message.get("data", {})
    
    logger.debug(f"收到客户端消息 - Connection: {connection_id}, Type: {msg_type}, Event: {event}")
    
    if msg_type == "system":
        # 系统消息
        if event == "heartbeat":
            # 心跳响应
            await connection_manager.update_heartbeat(connection_id)
            await connection_manager.send_message(
                connection_id,
                {
                    "type": "system",
                    "event": "heartbeat_ack",
                    "data": {
                        "timestamp": datetime.now().isoformat(),
                        "connection_id": connection_id
                    }
                }
            )
        
        elif event == "subscribe":
            # 订阅主题
            topic = data.get("topic")
            if topic:
                await connection_manager.subscribe(connection_id, topic)
            else:
                await connection_manager.send_message(
                    connection_id,
                    {
                        "type": "error",
                        "event": "missing_topic",
                        "data": {"message": "缺少 topic 参数"}
                    }
                )
        
        elif event == "unsubscribe":
            # 取消订阅
            topic = data.get("topic")
            if topic:
                await connection_manager.unsubscribe(connection_id, topic)
        
        elif event == "ping":
            # Ping 测试
            await connection_manager.send_message(
                connection_id,
                {
                    "type": "system",
                    "event": "pong",
                    "data": {
                        "timestamp": datetime.now().isoformat(),
                        "latency_ms": data.get("timestamp")
                    }
                }
            )
    
    elif msg_type == "auth":
        # 认证消息
        if event == "login":
            # 实现客户端认证逻辑
            logger.info(f"客户端认证请求 - Connection: {connection_id}")
            
            username = data.get("username")
            password = data.get("password")
            
            if not username or not password:
                await connection_manager.send_message(
                    connection_id,
                    {
                        "type": "system",
                        "event": "auth_error",
                        "data": {"message": "缺少用户名或密码"}
                    }
                )
                return
            
            # 验证用户凭证
            from app.core.security import authenticate_user
            user = await authenticate_user(username, password)
            
            if user:
                # 认证成功，更新连接的用户信息
                await connection_manager.update_user(connection_id, user.id)
                
                # 生成临时会话 Token
                from app.core.security import create_access_token
                from datetime import timedelta
                from app.config import settings
                
                access_token = create_access_token(
                    data={"sub": user.id},
                    expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
                )
                
                await connection_manager.send_message(
                    connection_id,
                    {
                        "type": "system",
                        "event": "auth_success",
                        "data": {
                            "message": "认证成功",
                            "user_id": user.id,
                            "username": user.username,
                            "token": access_token
                        }
                    }
                )
                logger.info(f"客户端认证成功 - Connection: {connection_id}, User: {user.username}")
            else:
                await connection_manager.send_message(
                    connection_id,
                    {
                        "type": "system",
                        "event": "auth_error",
                        "data": {"message": "用户名或密码错误"}
                    }
                )
                logger.warning(f"客户端认证失败 - Connection: {connection_id}, Username: {username}")
    
    else:
        # 未知消息类型
        await connection_manager.send_message(
            connection_id,
            {
                "type": "error",
                "event": "unknown_message",
                "data": {"message": f"未知的消息类型：{msg_type}"}
            }
        )


@router.get("/ws/stats")
async def get_websocket_stats():
    """
    获取 WebSocket 连接统计信息
    
    返回:
    - 总连接数
    - 各主题订阅数
    - 连接详情
    """
    stats = connection_manager.get_stats()
    return {
        "success": True,
        "data": stats,
        "timestamp": datetime.now().isoformat()
    }


@router.get("/ws/connections")
async def list_connections(current_user: User = Depends(get_current_admin_user)):
    """列出所有活跃连接（仅管理员可访问）"""
    connections = []
    for conn_id, conn in connection_manager.active_connections.items():
        connections.append({
            "connection_id": conn_id,
            "user_id": conn.user_id,
            "subscriptions": list(conn.subscriptions),
            "last_heartbeat": conn.last_heartbeat.isoformat(),
            "is_alive": conn.is_alive
        })
    
    return {
        "success": True,
        "data": {
            "total": len(connections),
            "connections": connections
        }
    }
