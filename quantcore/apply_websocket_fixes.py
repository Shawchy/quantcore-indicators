"""
自动修复脚本 - WebSocket 和 API 端点问题

应用以下修复：
1. Issue 1: 循环导入依赖问题 → 使用 FastAPI 依赖注入
2. Issue 2: WebSocket 广播性能问题 → 批量处理和合并消息
3. Issue 3: WebSocket 连接状态检查不完整 → 添加心跳超时检测

使用方法:
    python apply_fixes.py
"""

import os
import re
from pathlib import Path
from datetime import datetime


def fix_smart_realtime():
    """修复 Issue 1: 循环导入依赖问题"""
    
    file_path = Path("backend/app/api/v1/endpoints/smart_realtime.py")
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查是否已经修复
    if "def get_smart_polling_service():" in content:
        print(f"✅ {file_path} 已经修复（依赖注入已存在）")
        return True
    
    # 添加依赖注入函数
    import_section_end = content.find('router = APIRouter')
    if import_section_end == -1:
        print(f"❌ 未找到 router 定义")
        return False
    
    # 查找插入位置
    insert_pos = content.find('\n\n', import_section_end) + 2
    
    dependency_injection_code = """

# ==================== 依赖注入 ====================

def get_smart_polling_service():
    \"\"\"获取智能轮询服务实例（依赖注入）\"\"\"
    from app.services.smart_polling import smart_polling_service
    return smart_polling_service


def get_incremental_updater():
    \"\"\"获取增量更新器实例（依赖注入）\"\"\"
    from app.services.incremental_update import incremental_updater
    return incremental_updater


def get_anti_scraping_rules():
    \"\"\"获取反爬规则实例（依赖注入）\"\"\"
    from app.utils.anti_scraping_rules import anti_scraping_rules
    return anti_scraping_rules

"""
    
    # 插入依赖注入代码
    new_content = content[:insert_pos] + dependency_injection_code + content[insert_pos:]
    
    # 修改端点函数签名，添加 Depends
    endpoint_patterns = [
        (r'async def get_batch_quotes\(\n    request: BatchQuoteRequest\n\):',
         'async def get_batch_quotes(\n    request: BatchQuoteRequest,\n    smart_polling_service=Depends(get_smart_polling_service),\n    incremental_updater=Depends(get_incremental_updater)\n):'),
        
        (r'async def get_polling_stats\(\):',
         'async def get_polling_stats(\n    smart_polling_service=Depends(get_smart_polling_service)\n):'),
        
        (r'async def get_polling_config\(\n    user_tier: str = Query\(default="normal", description="用户等级"\)\n\):',
         'async def get_polling_config(\n    user_tier: str = Query(default="normal", description="用户等级"),\n    smart_polling_service=Depends(get_smart_polling_service)\n):'),
        
        (r'async def get_incremental_update\(\n    current_data: Dict\[str, Dict\] = Body\(\.\.\.\)\n\):',
         'async def get_incremental_update(\n    current_data: Dict[str, Dict] = Body(...),\n    incremental_updater=Depends(get_incremental_updater)\n):'),
        
        (r'async def get_single_quote\(\n    code: str,\n    use_cache: bool = Query\(default=True, description="使用缓存"\)\n\):',
         'async def get_single_quote(\n    code: str,\n    use_cache: bool = Query(default=True, description="使用缓存"),\n    smart_polling_service=Depends(get_smart_polling_service)\n):'),
        
        (r'async def get_safety_status\(\):',
         'async def get_safety_status(\n    anti_scraping_rules=Depends(get_anti_scraping_rules)\n):'),
        
        (r'async def get_active_rules\(\):',
         'async def get_active_rules(\n    anti_scraping_rules=Depends(get_anti_scraping_rules)\n):'),
    ]
    
    for pattern, replacement in endpoint_patterns:
        new_content = re.sub(pattern, replacement, new_content)
    
    # 移除函数内部的导入语句
    internal_imports = [
        r'from app\.services\.smart_polling import smart_polling_service',
        r'from app\.services\.incremental_update import incremental_updater',
        r'from app\.utils\.anti_scraping_rules import anti_scraping_rules',
    ]
    
    for import_pattern in internal_imports:
        # 只移除函数内部的导入（在 def 之后）
        lines = new_content.split('\n')
        new_lines = []
        in_function = False
        
        for line in lines:
            if line.strip().startswith('async def ') or line.strip().startswith('def '):
                in_function = True
                new_lines.append(line)
            elif line.strip().startswith('@') or (line.strip() and not line.strip().startswith(' ') and in_function):
                in_function = False
                new_lines.append(line)
            elif in_function and re.match(import_pattern, line.strip()):
                # 跳过内部导入
                continue
            else:
                new_lines.append(line)
        
        new_content = '\n'.join(new_lines)
    
    # 保存修复后的文件
    file_path.write_text(new_content, encoding='utf-8')
    print(f"✅ {file_path} 修复完成（依赖注入）")
    return True


def fix_tickflow_broadcast():
    """修复 Issue 2: WebSocket 广播性能问题"""
    
    file_path = Path("backend/app/api/v1/endpoints/tickflow_ws_endpoint.py")
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查是否已经修复
    if "client_messages: Dict[str, Dict] = {}" in content:
        print(f"✅ {file_path} 已经修复（批量广播已实现）")
        return True
    
    # 查找旧的 broadcast_quotes 方法
    old_method_pattern = r'(    async def broadcast_quotes\(self, quotes_data: Dict\[str, Any\]:.*?)(    async def|\Z)'
    match = re.search(old_method_pattern, content, re.DOTALL)
    
    if not match:
        print(f"❌ 未找到 broadcast_quotes 方法")
        return False
    
    old_method = match.group(1)
    
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
    
    # 替换旧方法
    new_content = content.replace(old_method, new_method)
    
    # 保存修复后的文件
    file_path.write_text(new_content, encoding='utf-8')
    print(f"✅ {file_path} 修复完成（批量广播优化）")
    return True


def fix_hybrid_realtime():
    """修复 Issue 3: WebSocket 连接状态检查不完整"""
    
    file_path = Path("backend/app/services/hybrid_realtime.py")
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查是否已经修复
    if "is_connection_healthy" in content:
        print(f"✅ {file_path} 已经修复（健康检查已存在）")
        return True
    
    # 查找 _get_from_ws 方法并修改
    old_check = '''if not self._tickflow_service or not self._tickflow_service._is_connected:'''
    new_check = '''# 使用健康检查代替简单的属性检查
        if not self._tickflow_service or not self._tickflow_service.is_connection_healthy():
            logger.warning("WebSocket 连接不健康，降级到轮询")
            return await self._fallback_to_polling(symbols)
        
        # 添加额外的检查'''
    
    if old_check not in content:
        print(f"⚠️ 未找到需要修改的检查逻辑")
        return False
    
    new_content = content.replace(old_check, new_check)
    
    # 保存修复后的文件
    file_path.write_text(new_content, encoding='utf-8')
    print(f"✅ {file_path} 修复完成（健康检查）")
    
    # 提示需要添加 is_connection_healthy 方法到 TickFlowWebSocketService
    print(f"\n⚠️ 注意：需要在 TickFlowWebSocketService 中添加 is_connection_healthy() 方法")
    print(f"   参考实现见 WEBSOCKET_AND_API_FIXES.md 文档\n")
    
    return True


def create_backup():
    """创建备份"""
    
    files_to_backup = [
        "backend/app/api/v1/endpoints/smart_realtime.py",
        "backend/app/api/v1/endpoints/tickflow_ws_endpoint.py",
        "backend/app/services/hybrid_realtime.py",
    ]
    
    backup_dir = Path("backend/backups")
    backup_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for file_path in files_to_backup:
        src = Path(file_path)
        if src.exists():
            dst = backup_dir / f"{src.stem}_{timestamp}{src.suffix}"
            dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
            print(f"💾 已备份：{file_path} → {dst}")
    
    print(f"\n备份目录：{backup_dir.absolute()}\n")


def main():
    """主函数"""
    
    print("=" * 60)
    print("🔧 WebSocket 和 API 端点自动修复脚本")
    print("=" * 60)
    print()
    
    # 切换到项目根目录
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"📂 当前目录：{os.getcwd()}\n")
    
    # 创建备份
    print("1️⃣ 创建备份...")
    create_backup()
    
    # 应用修复
    print("\n2️⃣ 应用修复...")
    print()
    
    fixes = [
        ("Issue 1: 循环依赖注入", fix_smart_realtime),
        ("Issue 2: WebSocket 批量广播", fix_tickflow_broadcast),
        ("Issue 3: 连接健康检查", fix_hybrid_realtime),
    ]
    
    results = []
    for issue_name, fix_func in fixes:
        print(f"正在修复：{issue_name}")
        try:
            success = fix_func()
            results.append((issue_name, success))
            print()
        except Exception as e:
            print(f"❌ 修复失败：{e}\n")
            results.append((issue_name, False))
    
    # 输出总结
    print("=" * 60)
    print("修复总结")
    print("=" * 60)
    print()
    
    for issue_name, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {issue_name}")
    
    all_success = all(success for _, success in results)
    
    if all_success:
        print("\n🎉 所有修复成功应用！")
        print("\n📝 下一步:")
        print("   1. 重启 Backend 服务")
        print("   2. 测试 API 端点：http://localhost:8000/api/v1/realtime/stats")
        print("   3. 测试 WebSocket: ws://localhost:8000/api/v1/ws/quotes")
        print("   4. 查看日志确认无错误")
    else:
        print("\n⚠️ 部分修复失败，请手动处理")
        print("   详细步骤见：WEBSOCKET_AND_API_FIXES.md")
    
    print()


if __name__ == "__main__":
    main()
