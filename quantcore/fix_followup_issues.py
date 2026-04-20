"""
修复 WebSocket 和 API 端点的后续问题

修复内容：
1. Issue 1: 依赖注入函数缺少异常处理
2. Issue 2: 重复的降级检查逻辑
3. Issue 3: 缺少 is_connection_healthy 方法验证
"""

from pathlib import Path
import sys

# 使用绝对路径
BASE_DIR = Path(r"D:\PROJ\Quant")


def fix_issue1_exception_handling():
    """修复 Issue 1: 依赖注入函数缺少异常处理"""
    
    file_path = BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 检查是否已经修复
    if "try:" in content and "智能轮询服务导入失败" in content:
        print(f"✅ {file_path} 已经修复（异常处理已存在）")
        return True
    
    # 替换 get_smart_polling_service
    old_func1 = '''def get_smart_polling_service():
    """获取智能轮询服务实例（依赖注入）"""
    from app.services.smart_polling import smart_polling_service
    return smart_polling_service'''
    
    new_func1 = '''def get_smart_polling_service():
    """获取智能轮询服务实例（依赖注入）"""
    try:
        from app.services.smart_polling import smart_polling_service
        return smart_polling_service
    except ImportError as e:
        logger.error(f"智能轮询服务导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")'''
    
    content = content.replace(old_func1, new_func1)
    
    # 替换 get_incremental_updater
    old_func2 = '''def get_incremental_updater():
    """获取增量更新器实例（依赖注入）"""
    from app.services.incremental_update import incremental_updater
    return incremental_updater'''
    
    new_func2 = '''def get_incremental_updater():
    """获取增量更新器实例（依赖注入）"""
    try:
        from app.services.incremental_update import incremental_updater
        return incremental_updater
    except ImportError as e:
        logger.error(f"增量更新器导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")'''
    
    content = content.replace(old_func2, new_func2)
    
    # 替换 get_anti_scraping_rules
    old_func3 = '''def get_anti_scraping_rules():
    """获取反爬规则实例（依赖注入）"""
    from app.utils.anti_scraping_rules import anti_scraping_rules
    return anti_scraping_rules'''
    
    new_func3 = '''def get_anti_scraping_rules():
    """获取反爬规则实例（依赖注入）"""
    try:
        from app.utils.anti_scraping_rules import anti_scraping_rules
        return anti_scraping_rules
    except ImportError as e:
        logger.error(f"反爬规则导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")'''
    
    content = content.replace(old_func3, new_func3)
    
    # 保存
    file_path.write_text(content, encoding='utf-8')
    print(f"✅ {file_path} 修复完成（异常处理）")
    return True


def fix_issue2_duplicate_fallback():
    """修复 Issue 2: 重复的降级检查逻辑"""
    
    file_path = BASE_DIR / "backend/app/services/hybrid_realtime.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 查找重复的降级逻辑
    duplicate_pattern = '''        # 添加额外的检查
            return await self._fallback_to_polling(symbols)'''
    
    if duplicate_pattern in content:
        content = content.replace(duplicate_pattern, '')
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ {file_path} 修复完成（删除重复降级逻辑）")
        return True
    else:
        print(f"⚠️ {file_path} 未找到重复的降级逻辑")
        return False


def fix_issue3_method_check():
    """修复 Issue 3: 缺少 is_connection_healthy 方法验证"""
    
    file_path = BASE_DIR / "backend/app/services/hybrid_realtime.py"
    
    if not file_path.exists():
        print(f"❌ 文件不存在：{file_path}")
        return False
    
    content = file_path.read_text(encoding='utf-8')
    
    # 旧的检查方式
    old_check = '''        # 使用健康检查代替简单的属性检查
        if not self._tickflow_service or not self._tickflow_service.is_connection_healthy():
            logger.warning("WebSocket 连接不健康，降级到轮询")
            return await self._fallback_to_polling(symbols)'''
    
    # 新的检查方式（添加方法存在性验证）
    new_check = '''        # 使用健康检查代替简单的属性检查
        if not self._tickflow_service:
            return await self._fallback_to_polling(symbols)
        
        # 验证 is_connection_healthy 方法是否存在
        if not hasattr(self._tickflow_service, 'is_connection_healthy'):
            logger.warning("TickFlow 服务缺少健康检查方法，使用默认检查")
            if not getattr(self._tickflow_service, '_is_connected', False):
                return await self._fallback_to_polling(symbols)
        elif not self._tickflow_service.is_connection_healthy():
            logger.warning("WebSocket 连接不健康，降级到轮询")
            return await self._fallback_to_polling(symbols)'''
    
    if old_check in content:
        content = content.replace(old_check, new_check)
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ {file_path} 修复完成（方法存在性验证）")
        return True
    else:
        print(f"⚠️ {file_path} 未找到需要修改的健康检查逻辑")
        return False


def create_backup():
    """创建备份"""
    
    files_to_backup = [
        BASE_DIR / "backend/app/api/v1/endpoints/smart_realtime.py",
        BASE_DIR / "backend/app/services/hybrid_realtime.py",
    ]
    
    from datetime import datetime
    backup_dir = BASE_DIR / "backend/backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    for src in files_to_backup:
        if src.exists():
            dst = backup_dir / f"{src.stem}_{timestamp}{src.suffix}"
            dst.write_text(src.read_text(encoding='utf-8'), encoding='utf-8')
            print(f"💾 已备份：{src} → {dst}")


def main():
    """主函数"""
    
    print("=" * 60)
    print("🔧 修复 WebSocket 和 API 端点后续问题")
    print("=" * 60)
    print()
    
    # 创建备份
    print("1️⃣ 创建备份...")
    create_backup()
    print()
    
    # 应用修复
    print("2️⃣ 应用修复...")
    print()
    
    fixes = [
        ("Issue 1: 依赖注入异常处理", fix_issue1_exception_handling),
        ("Issue 2: 重复降级逻辑", fix_issue2_duplicate_fallback),
        ("Issue 3: 方法存在性验证", fix_issue3_method_check),
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
        print("   2. 测试 API 端点")
        print("   3. 查看日志确认无错误")
    else:
        print("\n⚠️ 部分修复失败，请手动处理")
    
    print()


if __name__ == "__main__":
    main()
