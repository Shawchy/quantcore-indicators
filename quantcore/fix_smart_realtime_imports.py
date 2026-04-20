"""
修复智能实时 API 端点的循环导入问题

修复内容：
1. Issue 1: 验证服务模块存在性
2. Issue 2: 删除 get_batch_quotes 函数内的硬编码导入
3. Issue 3: 删除 get_safety_status 函数内的重复导入
"""

from pathlib import Path

BASE_DIR = Path(r"D:\PROJ\Quant")


def verify_service_modules():
    """验证服务模块是否存在"""
    
    modules_to_check = [
        ("backend/app/services/smart_polling.py", "smart_polling_service"),
        ("backend/app/services/incremental_update.py", "incremental_updater"),
        ("backend/app/utils/anti_scraping_rules.py", "anti_scraping_rules"),
    ]
    
    print("📋 验证服务模块存在性...")
    print()
    
    all_exist = True
    
    for module_path, service_name in modules_to_check:
        file_path = BASE_DIR / module_path
        
        if file_path.exists():
            print(f"✅ {module_path} - 存在")
        else:
            print(f"❌ {module_path} - 不存在")
            all_exist = False
    
    print()
    
    if all_exist:
        print("✅ 所有服务模块都存在")
        return True
    else:
        print("❌ 部分服务模块不存在，需要创建或修改引用")
        return False


def fix_issue2_remove_internal_imports():
    """修复 Issue 2: 删除 get_batch_quotes 函数内的硬编码导入"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查是否已经修复
    if "from app.services.smart_polling import smart_polling_service" not in content:
        print(f"✅ {file_path} 已经修复（无内部导入）")
        return True
    
    # 查找 get_batch_quotes 函数内的导入
    old_import_block = '''    try:
        from app.services.smart_polling import smart_polling_service
        from app.services.incremental_update import incremental_updater
        
        logger.info('''
    
    new_import_block = '''    try:
        logger.info('''
    
    content = content.replace(old_import_block, new_import_block)
    
    # 查找 get_polling_stats 函数内的导入
    old_stats_import = '''    try:
        from app.services.smart_polling import smart_polling_service
        
        stats = smart_polling_service.get_statistics()'''
    
    new_stats_import = '''    try:
        stats = smart_polling_service.get_statistics()'''
    
    content = content.replace(old_stats_import, new_stats_import)
    
    # 保存
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ {file_path} 修复完成（删除 get_batch_quotes 和 get_polling_stats 内部导入）")
    return True


def fix_issue3_remove_safety_import():
    """修复 Issue 3: 删除 get_safety_status 函数内的重复导入"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 查找 get_safety_status 函数内的导入
    old_safety_import = '''@safety_router.get("/status")
async def get_safety_status(
    anti_scraping_rules=Depends(get_anti_scraping_rules)
):
    """获取反爬安全状态"""
    try:
        from app.utils.anti_scraping_rules import anti_scraping_rules
        
        stats = anti_scraping_rules.get_statistics()'''
    
    new_safety_import = '''@safety_router.get("/status")
async def get_safety_status(
    anti_scraping_rules=Depends(get_anti_scraping_rules)
):
    """获取反爬安全状态"""
    try:
        stats = anti_scraping_rules.get_statistics()'''
    
    if old_safety_import in content:
        content = content.replace(old_safety_import, new_safety_import)
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ {file_path} 修复完成（删除 get_safety_status 内部导入）")
        return True
    else:
        print(f"⚠️ {file_path} 未找到需要删除的导入")
        return False


def verify_fixes():
    """验证修复效果"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查函数内的导入是否已删除
    issues = [
        ("get_batch_quotes 函数内导入", "get_batch_quotes", "from app.services.smart_polling import smart_polling_service"),
        ("get_polling_stats 函数内导入", "get_polling_stats", "from app.services.smart_polling import smart_polling_service"),
        ("get_safety_status 函数内导入", "get_safety_status", "from app.utils.anti_scraping_rules import anti_scraping_rules"),
    ]
    
    print()
    print("🔍 验证修复效果...")
    print()
    
    all_fixed = True
    
    for issue_name, func_name, import_pattern in issues:
        # 查找函数定义
        func_start = content.find(f"async def {func_name}")
        if func_start == -1:
            print(f"❌ 未找到函数 {func_name}")
            all_fixed = False
            continue
        
        # 查找下一个函数定义
        next_func = content.find("async def ", func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        # 提取函数体
        func_body = content[func_start:next_func]
        
        # 检查是否还有内部导入
        if import_pattern in func_body:
            print(f"❌ {issue_name} - 仍然存在")
            all_fixed = False
        else:
            print(f"✅ {issue_name} - 已删除")
    
    return all_fixed


def main():
    """主函数"""
    
    print("=" * 60)
    print("🔧 修复智能实时 API 端点循环导入问题")
    print("=" * 60)
    print()
    
    # Step 1: 验证服务模块存在性
    print("Step 1: 验证服务模块存在性")
    print("-" * 60)
    modules_exist = verify_service_modules()
    print()
    
    if not modules_exist:
        print("⚠️ 部分服务模块不存在，无法继续修复")
        return
    
    # Step 2: 删除函数内的硬编码导入
    print("Step 2: 删除函数内的硬编码导入")
    print("-" * 60)
    fix_issue2_remove_internal_imports()
    print()
    
    # Step 3: 删除安全端点的重复导入
    print("Step 3: 删除安全端点的重复导入")
    print("-" * 60)
    fix_issue3_remove_safety_import()
    print()
    
    # Step 4: 验证修复效果
    print("Step 4: 验证修复效果")
    print("-" * 60)
    all_fixed = verify_fixes()
    print()
    
    # 总结
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print()
    
    if all_fixed:
        print("🎉 所有循环导入问题已修复！")
        print()
        print("📝 下一步:")
        print("   1. 重启 Backend 服务")
        print("   2. 测试 API 端点功能")
        print("   3. 查看日志确认无循环导入警告")
    else:
        print("⚠️ 部分问题未修复，请检查上方详情")
    
    print()


if __name__ == "__main__":
    main()
