"""
验证依赖注入函数异常类型验证修复效果
"""

from pathlib import Path

BASE_DIR = Path(r"D:\PROJ\Quant")


def verify_di_validation():
    """验证依赖注入函数的异常类型验证"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py"
    
    if not file_path.exists():
        return False, "文件不存在"
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查三个函数的验证逻辑
    functions_to_check = [
        {
            "name": "get_smart_polling_service",
            "service": "smart_polling_service",
            "error_msg": "智能轮询服务"
        },
        {
            "name": "get_incremental_updater",
            "service": "incremental_updater",
            "error_msg": "增量更新器"
        },
        {
            "name": "get_anti_scraping_rules",
            "service": "anti_scraping_rules",
            "error_msg": "反爬规则"
        }
    ]
    
    results = []
    all_passed = True
    
    for func_info in functions_to_check:
        func_name = func_info["name"]
        service_name = func_info["service"]
        error_msg = func_info["error_msg"]
        
        # 查找函数定义
        func_start = content.find(f"def {func_name}")
        if func_start == -1:
            results.append(f"❌ {func_name}: 未找到函数定义")
            all_passed = False
            continue
        
        # 查找下一个函数定义
        next_func = content.find("def ", func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        # 提取函数体
        func_body = content[func_start:next_func]
        
        # 检查各项验证
        checks = {
            "try-except 块": "try:" in func_body and "except ImportError" in func_body,
            "None 检查": f"if {service_name} is None:" in func_body,
            "503 错误": 'status_code=503' in func_body and "服务未初始化" in func_body,
            "500 错误": 'status_code=500' in func_body and "服务初始化失败" in func_body,
            "错误日志": f'logger.error(f"{error_msg}' in func_body or f'logger.error("{error_msg}' in func_body
        }
        
        func_passed = all(checks.values())
        all_passed = all_passed and func_passed
        
        status = "✅" if func_passed else "❌"
        results.append(f"{status} {func_name}:")
        
        for check_name, check_result in checks.items():
            check_status = "✅" if check_result else "❌"
            results.append(f"   {check_status} {check_name}")
    
    return all_passed, "\n".join(results)


def main():
    """主验证函数"""
    
    print("=" * 60)
    print("🔍 验证依赖注入函数异常类型修复效果")
    print("=" * 60)
    print()
    
    print("验证内容:")
    print("-" * 60)
    print("1. try-except ImportError 捕获")
    print("2. 服务实例 None 检查")
    print("3. HTTP 503 错误（服务未初始化）")
    print("4. HTTP 500 错误（服务初始化失败）")
    print("5. 详细错误日志记录")
    print()
    
    success, message = verify_di_validation()
    
    print("验证结果:")
    print("-" * 60)
    print(message)
    print()
    
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print()
    
    if success:
        print("🎉 所有依赖注入函数已完善异常类型验证！")
        print()
        print("📝 后续步骤:")
        print("   1. 重启 Backend 服务")
        print("   2. 测试 API 端点功能")
        print("   3. 验证服务未初始化时的错误处理")
        print("   4. 监控日志中的错误信息")
    else:
        print("⚠️ 部分验证未通过，请检查上方详情")
    
    print()


if __name__ == "__main__":
    main()
