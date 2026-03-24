"""
WebSocket 功能测试脚本
用于测试 WebSocket 连接、订阅和消息推送功能
"""
import asyncio
import websockets
import json
from datetime import datetime
from loguru import logger


async def test_websocket_connection():
    """测试 WebSocket 连接"""
    uri = "ws://localhost:8000/api/v1/ws"
    
    try:
        logger.info(f"正在连接：{uri}")
        async with websockets.connect(uri) as websocket:
            logger.info("✓ 连接成功")
            
            # 等待欢迎消息
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"收到欢迎消息：{data}")
            
            return True
            
    except Exception as e:
        logger.error(f"✗ 连接失败：{e}")
        return False


async def test_subscribe():
    """测试订阅功能"""
    uri = "ws://localhost:8000/api/v1/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✓ 连接成功")
            
            # 订阅股票行情
            subscribe_msg = {
                "type": "system",
                "event": "subscribe",
                "data": {
                    "topic": "stock:000001"
                }
            }
            
            logger.info("发送订阅消息")
            await websocket.send(json.dumps(subscribe_msg))
            
            # 等待确认
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"收到确认：{data}")
            
            if data.get("event") == "subscribed":
                logger.info("✓ 订阅成功")
                return True
            else:
                logger.error("✗ 订阅失败")
                return False
                
    except Exception as e:
        logger.error(f"✗ 测试失败：{e}")
        return False


async def test_heartbeat():
    """测试心跳功能"""
    uri = "ws://localhost:8000/api/v1/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✓ 连接成功")
            
            # 发送心跳
            heartbeat_msg = {
                "type": "system",
                "event": "heartbeat",
                "data": {
                    "timestamp": datetime.now().isoformat()
                }
            }
            
            logger.info("发送心跳")
            await websocket.send(json.dumps(heartbeat_msg))
            
            # 等待响应
            response = await websocket.recv()
            data = json.loads(response)
            logger.info(f"收到心跳响应：{data}")
            
            if data.get("event") == "heartbeat_ack":
                logger.info("✓ 心跳正常")
                return True
            else:
                logger.error("✗ 心跳异常")
                return False
                
    except Exception as e:
        logger.error(f"✗ 测试失败：{e}")
        return False


async def test_ping_latency():
    """测试延迟"""
    uri = "ws://localhost:8000/api/v1/ws"
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("✓ 连接成功")
            
            # 发送 Ping
            start_time = datetime.now()
            ping_msg = {
                "type": "system",
                "event": "ping",
                "data": {
                    "timestamp": str(start_time.timestamp())
                }
            }
            
            await websocket.send(json.dumps(ping_msg))
            
            # 等待 Pong
            response = await websocket.recv()
            end_time = datetime.now()
            
            latency = (end_time - start_time).total_seconds() * 1000
            logger.info(f"延迟：{latency:.2f}ms")
            
            if latency < 1000:
                logger.info("✓ 延迟正常")
                return True
            else:
                logger.warning("⚠ 延迟较高")
                return False
                
    except Exception as e:
        logger.error(f"✗ 测试失败：{e}")
        return False


async def run_all_tests():
    """运行所有测试"""
    logger.info("=" * 60)
    logger.info("WebSocket 功能测试")
    logger.info("=" * 60)
    
    tests = [
        ("连接测试", test_websocket_connection),
        ("订阅测试", test_subscribe),
        ("心跳测试", test_heartbeat),
        ("延迟测试", test_ping_latency),
    ]
    
    results = []
    for name, test_func in tests:
        logger.info(f"\n▶ 开始测试：{name}")
        result = await test_func()
        results.append((name, result))
        await asyncio.sleep(1)  # 避免连接过于频繁
    
    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        logger.info(f"{status} - {name}")
    
    logger.info(f"\n总计：{passed}/{total} 通过")
    logger.info("=" * 60)
    
    return passed == total


if __name__ == "__main__":
    # 设置日志
    logger.add("logs/websocket_test.log", rotation="10 MB")
    
    # 运行测试
    success = asyncio.run(run_all_tests())
    
    if success:
        logger.info("\n🎉 所有测试通过！")
        exit(0)
    else:
        logger.error("\n❌ 部分测试失败，请检查日志")
        exit(1)
