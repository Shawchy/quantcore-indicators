"""
手动修复 Issue 2: WebSocket 批量广播优化

由于自动脚本无法匹配到 broadcast_quotes 方法，使用此脚本手动修复。
"""

import re
from pathlib import Path


def fix_broadcast():
    """修复 WebSocket 广播性能问题"""
    
    file_path = Path("backend/app/api/v1/endpoints/tickflow_ws_endpoint.py")
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 查找旧的 broadcast_quotes 方法（更精确的匹配）
    old_method_start = content.find('    async def broadcast_quotes(self, quotes_data: Dict[str, Any]):')
    
    if old_method_start == -1:
        print(f"❌ 未找到 broadcast_quotes 方法")
        return False
    
    # 查找方法结束位置（下一个方法或类结束）
    next_method = content.find('    async def send_subscription_status', old_method_start)
    
    if next_method == -1:
        print(f"❌ 未找到方法边界")
        return False
    
    # 提取旧方法
    old_method = content[old_method_start:next_method]
    
    # 新的优化版本
    new_method = '''    async def broadcast_quotes(self, quotes_data: Dict[str, Any]):
        """广播行情数据给所有相关订阅者（批量优化）"""
        
        # 按客户端分组，合并多个标的数据
        client_messages: Dict[str, Dict] = {}
        
        for code, quote_data in quotes_data.items():
            subscribers = self._symbol_subscribers.get(code, set())
            
            for client_id in subscribers:
                if client_id not in client_messages:
                    client_messages[client_id] = {
                        "op": "quotes",
                        "data": {},
                        "timestamp": datetime.now().isoformat()
                    }
                # 合并到同一个消息的 data 中
                client_messages[client_id]["data"][code] = quote_data
        
        # 每个客户端只发送一次（批量）
        sent_count = 0
        for client_id, message in client_messages.items():
            try:
                conn = self._connections.get(client_id)
                if conn:
                    # 只序列化一次
                    json_msg = json.dumps(message, ensure_ascii=False)
                    await conn["websocket"].send_text(json_msg)
                    conn["last_activity"] = datetime.now()
                    sent_count += 1
            except Exception as e:
                logger.debug(f"广播失败 ({client_id}): {e}")
        
        return sent_count
    
'''
    
    # 替换
    new_content = content[:old_method_start] + new_method + content[next_method:]
    
    # 保存
    file_path.write_text(new_content, encoding='utf-8')
    print(f"✅ {file_path} 修复完成（批量广播优化）")
    return True


if __name__ == "__main__":
    fix_broadcast()
