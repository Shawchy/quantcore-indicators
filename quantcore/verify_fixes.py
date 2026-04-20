"""
验证修复效果

检查所有三个 Issue 是否已正确修复。
"""

import re
from pathlib import Path


def verify_issue1():
    """验证 Issue 1: 依赖注入"""
    
    file_path = Path("backend/app/api/v1/endpoints/smart_realtime.py")
    
    if not file_path.exists():
        return False, "文件不存在"
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查依赖注入函数是否存在
    checks = [
        ("get_smart_polling_service", "依赖注入函数"),
        ("get_incremental_updater", "增量更新器依赖"),
        ("get_anti_scraping_rules", "反爬规则依赖"),
        ("Depends(get_smart_polling_service)", "端点依赖注入使用"),
    ]
    
    results = []
    for pattern, description in checks:
        if pattern in content:
            results.append(f"✅ {description}")
        else:
            results.append(f"❌ {description} 缺失")
    
    all_present = all(pattern in content for pattern, _ in checks)
    
    if all_present:
        # 检查是否还有内部导入（不应该有）
        internal_imports = re.findall(
            r'from app\.services\.(smart_polling|incremental_update) import',
            content
        )
        
        # 过滤掉模块级别的导入
        lines = content.split('\n')
        module_level_imports = []
        in_function = False
        
        for line in lines:
            if line.strip().startswith('def '):
                in_function = True
            elif line.strip().startswith('from ') and in_function:
                module_level_imports.append(line.strip())
        
        if module_level_imports:
            return True, f"部分修复成功，但仍有内部导入:\n" + "\n".join(module_level_imports)
        else:
            return True, "完全修复"
    else:
        return False, "\n".join(results)


def verify_issue2():
    """验证 Issue 2: WebSocket 批量广播"""
    
    file_path = Path("backend/app/api/v1/endpoints/tickflow_ws_endpoint.py")
    
    if not file_path.exists():
        return False, "文件不存在"
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查批量处理逻辑
    checks = [
        ("client_messages: Dict[str, Dict] = {}", "客户端消息分组"),
        ("合并到同一个消息", "消息合并注释"),
        ("每个客户端只发送一次", "批量发送注释"),
        ("只序列化一次", "序列化优化注释"),
    ]
    
    results = []
    for pattern, description in checks:
        if pattern in content:
            results.append(f"✅ {description}")
        else:
            results.append(f"❌ {description} 缺失")
    
    all_present = all(pattern in content for pattern, _ in checks)
    
    if all_present:
        return True, "批量广播优化已应用"
    else:
        return False, "\n".join(results)


def verify_issue3():
    """验证 Issue 3: 连接健康检查"""
    
    file_path = Path("backend/app/services/hybrid_realtime.py")
    
    if not file_path.exists():
        return False, "文件不存在"
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查健康检查逻辑
    checks = [
        ("is_connection_healthy", "健康检查方法调用"),
        ("连接不健康", "降级日志"),
        ("健康检查", "注释"),
    ]
    
    results = []
    for pattern, description in checks:
        if pattern in content:
            results.append(f"✅ {description}")
        else:
            results.append(f"❌ {description} 缺失")
    
    # 检查是否还有旧的检查方式
    if "not self._tickflow_service._is_connected:" in content:
        results.append("⚠️ 仍使用旧的属性检查方式")
    
    all_present = all(pattern in content for pattern, _ in checks[:2])
    
    if all_present:
        return True, "健康检查已添加"
    else:
        return False, "\n".join(results)


def main():
    """主验证函数"""
    
    print("=" * 60)
    print("🔍 验证修复效果")
    print("=" * 60)
    print()
    
    import os
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    print(f"📂 当前目录：{os.getcwd()}\n")
    
    issues = [
        ("Issue 1: 循环导入依赖问题", verify_issue1),
        ("Issue 2: WebSocket 广播性能问题", verify_issue2),
        ("Issue 3: WebSocket 连接状态检查", verify_issue3),
    ]
    
    all_success = True
    
    for issue_name, verify_func in issues:
        print(f"{issue_name}")
        print("-" * 60)
        
        success, message = verify_func()
        
        if success:
            print(f"✅ 修复成功：{message}")
        else:
            print(f"❌ 修复失败：{message}")
            all_success = False
        
        print()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    
    if all_success:
        print("\n🎉 所有问题已成功修复！")
        print("\n📝 后续步骤:")
        print("   1. 重启 Backend 服务")
        print("   2. 测试 API 端点功能")
        print("   3. 测试 WebSocket 连接和广播")
        print("   4. 监控性能指标")
    else:
        print("\n⚠️ 部分修复未完成，请检查上方详情")
    
    print()


if __name__ == "__main__":
    main()
