"""
验证智能实时 API 端点修复效果

验证内容：
1. Issue 1: 服务模块存在性
2. Issue 2: 函数内硬编码导入已删除
3. Issue 3: 安全端点重复导入已删除
"""

from pathlib import Path

BASE_DIR = Path(r"D:\PROJ\Quant")


def verify_issue1_modules_exist():
    """验证 Issue 1: 服务模块存在性"""
    
    modules_to_check = [
        ("backend/app/services/smart_polling.py", "SmartPollingService"),
        ("backend/app/services/incremental_update.py", "IncrementalUpdateService"),
        ("backend/app/utils/anti_scraping_rules.py", "AntiScrapingRules"),
    ]
    
    results = []
    
    for module_path, class_name in modules_to_check:
        file_path = BASE_DIR / module_path
        
        if file_path.exists():
            content = file_path.read_text(encoding='utf-8')
            if class_name in content:
                results.append((f"{module_path}", True, "模块存在且包含正确的类"))
            else:
                results.append((f"{module_path}", False, f"模块不包含 {class_name}"))
        else:
            results.append((f"{module_path}", False, "模块不存在"))
    
    all_exist = all(success for _, success, _ in results)
    
    return all_exist, results


def verify_issue2_batch_imports_removed():
    """验证 Issue 2: get_batch_quotes 函数内导入已删除"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py"
    
    if not file_path.exists():
        return False, "文件不存在"
    
    content = file_path.read_text(encoding='utf-8')
    
    # 查找 get_batch_quotes 函数
    func_start = content.find("async def get_batch_quotes")
    if func_start == -1:
        return False, "未找到 get_batch_quotes 函数"
    
    # 查找下一个函数
    next_func = content.find("async def ", func_start + 1)
    if next_func == -1:
        next_func = len(content)
    
    # 提取函数体
    func_body = content[func_start:next_func]
    
    # 检查是否还有内部导入
    if "from app.services.smart_polling import smart_polling_service" in func_body:
        return False, "函数内仍有硬编码导入"
    
    # 检查是否使用了依赖注入参数
    if "smart_polling_service=Depends(get_smart_polling_service)" not in content:
        return False, "函数签名缺少依赖注入参数"
    
    if "incremental_updater=Depends(get_incremental_updater)" not in content:
        return False, "函数签名缺少 incremental_updater 参数"
    
    # 检查函数体是否使用了注入的参数
    if "smart_polling_service.get_realtime_batch" not in func_body:
        return False, "函数体未使用注入的 smart_polling_service 参数"
    
    return True, "函数内硬编码导入已删除，正确使用依赖注入"


def verify_issue3_safety_imports_removed():
    """验证 Issue 3: get_safety_status 函数内导入已删除"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py"
    
    if not file_path.exists():
        return False, "文件不存在"
    
    content = file_path.read_text(encoding='utf-8')
    
    # 查找 get_safety_status 函数
    func_start = content.find("async def get_safety_status")
    if func_start == -1:
        return False, "未找到 get_safety_status 函数"
    
    # 查找下一个函数
    next_func = content.find("async def ", func_start + 1)
    if next_func == -1:
        next_func = len(content)
    
    # 提取函数体
    func_body = content[func_start:next_func]
    
    # 检查是否还有内部导入
    if "from app.utils.anti_scraping_rules import anti_scraping_rules" in func_body:
        return False, "函数内仍有硬编码导入"
    
    # 检查是否使用了依赖注入参数
    if "anti_scraping_rules=Depends(get_anti_scraping_rules)" not in content:
        return False, "函数签名缺少依赖注入参数"
    
    # 检查函数体是否使用了注入的参数
    if "anti_scraping_rules.get_statistics()" not in func_body:
        return False, "函数体未使用注入的 anti_scraping_rules 参数"
    
    return True, "函数内硬编码导入已删除，正确使用依赖注入"


def main():
    """主验证函数"""
    
    print("=" * 60)
    print("🔍 验证智能实时 API 端点修复效果")
    print("=" * 60)
    print()
    
    issues = [
        ("Issue 1: 服务模块存在性", verify_issue1_modules_exist),
        ("Issue 2: get_batch_quotes 导入删除", verify_issue2_batch_imports_removed),
        ("Issue 3: get_safety_status 导入删除", verify_issue3_safety_imports_removed),
    ]
    
    all_success = True
    
    for issue_name, verify_func in issues:
        print(f"{issue_name}")
        print("-" * 60)
        
        result = verify_func()
        
        if isinstance(result, tuple):
            success, message = result
            
            if success:
                print(f"✅ 修复成功：{message}")
            else:
                print(f"❌ 修复失败：{message}")
                all_success = False
        else:
            # Issue 1 返回多个结果
            success, details = result
            
            for detail_path, detail_success, detail_msg in details:
                status = "✅" if detail_success else "❌"
                print(f"{status} {detail_path}: {detail_msg}")
            
            if success:
                print(f"✅ 所有服务模块都存在")
            else:
                print(f"❌ 部分服务模块不存在")
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
        print("   3. 查看日志确认无循环导入警告")
        print("   4. 监控依赖注入是否正常工作")
    else:
        print("\n⚠️ 部分修复未完成，请检查上方详情")
    
    print()


if __name__ == "__main__":
    main()
