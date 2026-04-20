"""
验证后续问题修复效果

检查所有三个 Issue 是否已正确修复。
"""

from pathlib import Path

BASE_DIR = Path(r"D:\PROJ\Quant")


def verify_issue1():
    """验证 Issue 1: 依赖注入异常处理"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py"
    
    if not file_path.exists():
        return False, "文件不存在"
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查异常处理是否存在
    checks = [
        ("try:", "try 块"),
        ("except ImportError as e:", "ImportError 捕获"),
        ("智能轮询服务导入失败", "智能轮询错误日志"),
        ("增量更新器导入失败", "增量更新器错误日志"),
        ("反爬规则导入失败", "反爬规则错误日志"),
        ("HTTPException(status_code=500", "HTTP 异常抛出"),
    ]
    
    results = []
    for pattern, description in checks:
        if pattern in content:
            results.append(f"✅ {description}")
        else:
            results.append(f"❌ {description} 缺失")
    
    all_present = all(pattern in content for pattern, _ in checks)
    
    if all_present:
        return True, "依赖注入异常处理已完善"
    else:
        return False, "\n".join(results)


def verify_issue2():
    """验证 Issue 2: 重复降级逻辑已删除"""
    
    file_path = BASE_DIR / "backend/app/services/hybrid_realtime.py"
    
    if not file_path.exists():
        return False, "文件不存在"
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查重复的降级逻辑是否已删除
    duplicate_pattern = '''        # 添加额外的检查
            return await self._fallback_to_polling(symbols)'''
    
    if duplicate_pattern in content:
        return False, "重复的降级逻辑仍然存在"
    else:
        return True, "重复降级逻辑已删除"


def verify_issue3():
    """验证 Issue 3: 方法存在性验证"""
    
    file_path = BASE_DIR / "backend/app/services/hybrid_realtime.py"
    
    if not file_path.exists():
        return False, "文件不存在"
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查方法存在性验证
    checks = [
        ("hasattr(self._tickflow_service, 'is_connection_healthy')", "hasattr 检查"),
        ("TickFlow 服务缺少健康检查方法", "警告日志"),
        ("getattr(self._tickflow_service, '_is_connected', False)", "getattr 默认值"),
    ]
    
    results = []
    for pattern, description in checks:
        if pattern in content:
            results.append(f"✅ {description}")
        else:
            results.append(f"❌ {description} 缺失")
    
    all_present = all(pattern in content for pattern, _ in checks)
    
    if all_present:
        return True, "方法存在性验证已添加"
    else:
        return False, "\n".join(results)


def main():
    """主验证函数"""
    
    print("=" * 60)
    print("🔍 验证后续问题修复效果")
    print("=" * 60)
    print()
    
    issues = [
        ("Issue 1: 依赖注入异常处理", verify_issue1),
        ("Issue 2: 重复降级逻辑", verify_issue2),
        ("Issue 3: 方法存在性验证", verify_issue3),
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
        print("   3. 测试 WebSocket 连接")
        print("   4. 监控日志确认无错误")
    else:
        print("\n⚠️ 部分修复未完成，请检查上方详情")
    
    print()


if __name__ == "__main__":
    main()
