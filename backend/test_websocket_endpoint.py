"""
测试 WebSocket 端点是否正确
"""
import asyncio
import websockets
import json

async def test_websocket():
    print("=" * 70)
    print("测试 WebSocket 连接")
    print("=" * 70)
    
    # 测试不同的 URL
    urls = [
        "ws://localhost:8000/api/v1/ws",
        "ws://localhost:8000/api/v1/ws/ws",
    ]
    
    for url in urls:
        print(f"\n测试: {url}")
        try:
            async with websockets.connect(url, close_timeout=1) as ws:
                print(f"  ✅ 连接成功！")
                
                # 发送心跳测试
                await ws.send(json.dumps({
                    "type": "system",
                    "event": "ping",
                    "data": {"timestamp": "test"}
                }))
                
                # 接收响应
                response = await asyncio.wait_for(ws.recv(), timeout=2)
                print(f"  收到响应: {response[:100]}...")
                
        except Exception as e:
            print(f"  ❌ 连接失败: {type(e).__name__}: {e}")
    
    print("\n" + "=" * 70)

if __name__ == '__main__':
    asyncio.run(test_websocket())
