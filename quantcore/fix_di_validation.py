"""
修复依赖注入函数的异常类型验证

修复内容：
1. 为所有依赖注入函数添加服务实例 None 检查
2. 添加更详细的错误日志
"""

from pathlib import Path

BASE_DIR = Path(r"D:\PROJ\Quant")


def fix_dependency_injection_validation():
    """修复依赖注入函数缺少异常类型验证的问题"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查是否已经修复
    if "if smart_polling_service is None:" in content:
        print(f"✅ {file_path} 已经修复（异常类型验证已存在）")
        return True
    
    # 修复 get_smart_polling_service
    old_func1 = '''def get_smart_polling_service():
    """获取智能轮询服务实例（依赖注入）"""
    try:
        from app.services.smart_polling import smart_polling_service
        return smart_polling_service
    except ImportError as e:
        logger.error(f"智能轮询服务导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")'''
    
    new_func1 = '''def get_smart_polling_service():
    """获取智能轮询服务实例（依赖注入）"""
    try:
        from app.services.smart_polling import smart_polling_service
        if smart_polling_service is None:
            logger.error("智能轮询服务实例为 None")
            raise HTTPException(status_code=503, detail="服务未初始化")
        return smart_polling_service
    except ImportError as e:
        logger.error(f"智能轮询服务导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")'''
    
    content = content.replace(old_func1, new_func1)
    
    # 修复 get_incremental_updater
    old_func2 = '''def get_incremental_updater():
    """获取增量更新器实例（依赖注入）"""
    try:
        from app.services.incremental_update import incremental_updater
        return incremental_updater
    except ImportError as e:
        logger.error(f"增量更新器导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")'''
    
    new_func2 = '''def get_incremental_updater():
    """获取增量更新器实例（依赖注入）"""
    try:
        from app.services.incremental_update import incremental_updater
        if incremental_updater is None:
            logger.error("增量更新器实例为 None")
            raise HTTPException(status_code=503, detail="服务未初始化")
        return incremental_updater
    except ImportError as e:
        logger.error(f"增量更新器导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")'''
    
    content = content.replace(old_func2, new_func2)
    
    # 修复 get_anti_scraping_rules
    old_func3 = '''def get_anti_scraping_rules():
    """获取反爬规则实例（依赖注入）"""
    try:
        from app.utils.anti_scraping_rules import anti_scraping_rules
        return anti_scraping_rules
    except ImportError as e:
        logger.error(f"反爬规则导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")'''
    
    new_func3 = '''def get_anti_scraping_rules():
    """获取反爬规则实例（依赖注入）"""
    try:
        from app.utils.anti_scraping_rules import anti_scraping_rules
        if anti_scraping_rules is None:
            logger.error("反爬规则实例为 None")
            raise HTTPException(status_code=503, detail="服务未初始化")
        return anti_scraping_rules
    except ImportError as e:
        logger.error(f"反爬规则导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")'''
    
    content = content.replace(old_func3, new_func3)
    
    # 保存
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ {file_path} 修复完成（异常类型验证）")
    return True


def verify_fix():
    """验证修复效果"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查三个函数的验证逻辑
    checks = [
        ("get_smart_polling_service", "if smart_polling_service is None:"),
        ("get_incremental_updater", "if incremental_updater is None:"),
        ("get_anti_scraping_rules", "if anti_scraping_rules is None:"),
    ]
    
    print()
    print("🔍 验证修复效果...")
    print()
    
    all_fixed = True
    
    for func_name, check_pattern in checks:
        # 查找函数定义
        func_start = content.find(f"def {func_name}")
        if func_start == -1:
            print(f"❌ 未找到函数 {func_name}")
            all_fixed = False
            continue
        
        # 查找下一个函数定义
        next_func = content.find("def ", func_start + 1)
        if next_func == -1:
            next_func = len(content)
        
        # 提取函数体
        func_body = content[func_start:next_func]
        
        # 检查是否有 None 检查
        if check_pattern in func_body:
            print(f"✅ {func_name} - 已添加 None 检查")
        else:
            print(f"❌ {func_name} - 缺少 None 检查")
            all_fixed = False
    
    return all_fixed


def main():
    """主函数"""
    
    print("=" * 60)
    print("🔧 修复依赖注入函数异常类型验证")
    print("=" * 60)
    print()
    
    # 应用修复
    print("正在修复...")
    print("-" * 60)
    success = fix_dependency_injection_validation()
    print()
    
    if not success:
        print("⚠️ 修复失败")
        return
    
    # 验证修复效果
    print("验证修复效果...")
    print("-" * 60)
    all_fixed = verify_fix()
    print()
    
    # 总结
    print("=" * 60)
    print("总结")
    print("=" * 60)
    print()
    
    if all_fixed:
        print("🎉 所有依赖注入函数已添加异常类型验证！")
        print()
        print("📝 下一步:")
        print("   1. 重启 Backend 服务")
        print("   2. 测试 API 端点功能")
        print("   3. 查看日志确认服务初始化正常")
    else:
        print("⚠️ 部分修复未完成，请检查上方详情")
    
    print()


if __name__ == "__main__":
    main()
