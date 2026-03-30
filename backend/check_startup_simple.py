"""
启动异常检查工具 - 简化版
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

async def main():
    print("\n" + "="*70)
    print("后端启动异常检查工具")
    print("="*70 + "\n")
    
    issues = []
    
    # 1. 环境检查
    print("[1] 环境配置检查")
    try:
        from app.config import settings
        print(f"✅ 配置文件加载成功")
        print(f"   APP_NAME: {settings.APP_NAME}")
        print(f"   DATABASE_URL: {'已设置' if settings.DATABASE_URL else '未设置'}")
    except Exception as e:
        issues.append(f"❌ 配置加载失败：{e}")
        print(f"❌ 配置加载失败：{e}")
    
    # 2. 数据库检查
    print("\n[2] 数据库初始化检查")
    try:
        from app.storage.sqlite import init_database
        await init_database()
        print("✅ 数据库初始化成功")
    except Exception as e:
        issues.append(f"❌ 数据库初始化失败：{e}")
        print(f"❌ 数据库初始化失败：{e}")
    
    # 3. 数据源检查
    print("\n[3] 数据源初始化检查")
    try:
        from app.adapters.factory import DataSourceManager
        manager = DataSourceManager()
        await manager.initialize()
        print(f"✅ 数据源初始化成功")
        print(f"   默认数据源：{manager._default_source}")
    except Exception as e:
        issues.append(f"❌ 数据源初始化失败：{e}")
        print(f"❌ 数据源初始化失败：{e}")
    
    # 4. 本地数据库服务检查
    print("\n[4] 本地数据库服务检查")
    try:
        from app.services.local_database import local_db_service
        await local_db_service.initialize()
        print("✅ 本地数据库服务初始化成功")
    except Exception as e:
        issues.append(f"❌ 本地数据库服务初始化失败：{e}")
        print(f"❌ 本地数据库服务初始化失败：{e}")
    
    # 5. 缓存管理器检查
    print("\n[5] 缓存管理器检查")
    try:
        from app.storage.cache import cache_manager
        print("✅ 缓存管理器已初始化")
    except Exception as e:
        issues.append(f"❌ 缓存管理器初始化失败：{e}")
        print(f"❌ 缓存管理器初始化失败：{e}")
    
    # 6. 智能加载器检查
    print("\n[6] 智能加载器检查")
    try:
        from app.services.smart_loader import smart_loader
        print("✅ 智能加载器已初始化")
    except Exception as e:
        issues.append(f"❌ 智能加载器初始化失败：{e}")
        print(f"❌ 智能加载器初始化失败：{e}")
    
    # 总结
    print("\n" + "="*70)
    print("检查总结")
    print("="*70)
    
    if not issues:
        print("✅ 所有检查通过！系统可以正常启动。")
        return True
    else:
        print(f"⚠️  发现 {len(issues)} 个问题：")
        for i, issue in enumerate(issues, 1):
            print(f"  {i}. {issue}")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n❌ 检查过程出现异常：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
