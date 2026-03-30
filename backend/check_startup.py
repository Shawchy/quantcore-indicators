"""
启动异常检查工具

检查后端启动过程中可能出现的异常和配置问题
"""
import asyncio
import sys
from pathlib import Path
from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))


async def check_environment():
    """检查环境配置"""
    print("=" * 70)
    print("环境配置检查")
    print("=" * 70)
    
    issues = []
    
    # 1. 检查 .env 文件
    env_file = Path(__file__).parent / ".env"
    if not env_file.exists():
        issues.append("⚠️  .env 文件不存在")
    else:
        print("✅ .env 文件存在")
    
    # 2. 检查必要的环境变量
    from app.config import settings
    
    required_vars = [
        "DATABASE_URL",
        "SECRET_KEY",
        "API_PREFIX"
    ]
    
    for var in required_vars:
        if not hasattr(settings, var) or not getattr(settings, var):
            issues.append(f"⚠️  环境变量 {var} 未设置")
        else:
            print(f"✅ {var} 已设置")
    
    # 3. 检查数据目录
    from app.config import settings
    data_dirs = [
        settings.SQLITE_DIR,
        settings.PARQUET_DIR,
    ]
    
    for dir_path in data_dirs:
        path = Path(dir_path)
        try:
            path.mkdir(parents=True, exist_ok=True)
            print(f"✅ 数据目录可创建：{dir_path}")
        except Exception as e:
            issues.append(f"❌ 数据目录创建失败：{dir_path} - {e}")
    
    print()
    return issues


async def check_database():
    """检查数据库初始化"""
    print("=" * 70)
    print("数据库初始化检查")
    print("=" * 70)
    
    issues = []
    
    try:
        from app.storage.sqlite import init_database
        await init_database()
        print("✅ 数据库初始化成功")
    except Exception as e:
        issues.append(f"❌ 数据库初始化失败：{e}")
        print(f"❌ 数据库初始化失败：{e}")
    
    print()
    return issues


async def check_data_sources():
    """检查数据源初始化"""
    print("=" * 70)
    print("数据源初始化检查")
    print("=" * 70)
    
    issues = []
    
    try:
        from app.adapters import data_source_manager
        await data_source_manager.initialize()
        print(f"✅ 数据源初始化成功")
        print(f"   默认数据源：{data_source_manager._default_source}")
        
        # 检查各数据源状态
        from app.adapters.factory import DataSourceFactory
        available_sources = list(DataSourceFactory._adapters.keys())
        print(f"   可用数据源：{[s.value for s in available_sources]}")
        
        if not available_sources:
            issues.append("⚠️  没有可用的数据源")
        
    except Exception as e:
        issues.append(f"❌ 数据源初始化失败：{e}")
        print(f"❌ 数据源初始化失败：{e}")
    
    print()
    return issues


async def check_trading_calendar():
    """检查交易日历服务"""
    print("=" * 70)
    print("交易日历服务检查")
    print("=" * 70)
    
    issues = []
    
    try:
        from app.services.trading_calendar import trading_calendar
        await trading_calendar.initialize()
        print("✅ 交易日历服务初始化成功")
    except Exception as e:
        issues.append(f"❌ 交易日历服务初始化失败：{e}")
        print(f"❌ 交易日历服务初始化失败：{e}")
    
    print()
    return issues


async def check_local_database():
    """检查本地数据库服务"""
    print("=" * 70)
    print("本地数据库服务检查")
    print("=" * 70)
    
    issues = []
    
    try:
        from app.services.local_database import local_db_service
        await local_db_service.initialize()
        print("✅ 本地数据库服务初始化成功")
    except Exception as e:
        issues.append(f"❌ 本地数据库服务初始化失败：{e}")
        print(f"❌ 本地数据库服务初始化失败：{e}")
    
    print()
    return issues


async def check_middleware():
    """检查中间件初始化"""
    print("=" * 70)
    print("中间件初始化检查")
    print("=" * 70)
    
    issues = []
    
    try:
        from app.middleware import init_middleware
        init_middleware()
        print("✅ 中间件初始化成功")
    except Exception as e:
        issues.append(f"❌ 中间件初始化失败：{e}")
        print(f"❌ 中间件初始化失败：{e}")
    
    print()
    return issues


async def check_websocket():
    """检查 WebSocket 服务"""
    print("=" * 70)
    print("WebSocket 服务检查")
    print("=" * 70)
    
    issues = []
    
    try:
        from app.websocket import start_pusher_service
        await start_pusher_service()
        print("✅ WebSocket 服务启动成功")
    except Exception as e:
        issues.append(f"❌ WebSocket 服务启动失败：{e}")
        print(f"❌ WebSocket 服务启动失败：{e}")
    
    print()
    return issues


async def main():
    """主检查函数"""
    print("\n")
    print("🔍 " + "=" * 68)
    print("🔍 后端启动异常检查工具")
    print("🔍 " + "=" * 68)
    print()
    
    all_issues = []
    
    # 执行所有检查
    all_issues.extend(await check_environment())
    all_issues.extend(await check_database())
    all_issues.extend(await check_data_sources())
    all_issues.extend(await check_trading_calendar())
    all_issues.extend(await check_local_database())
    all_issues.extend(await check_middleware())
    all_issues.extend(await check_websocket())
    
    # 输出总结
    print("=" * 70)
    print("检查总结")
    print("=" * 70)
    
    if not all_issues:
        print("✅ 所有检查通过！系统可以正常启动。")
    else:
        print(f"⚠️  发现 {len(all_issues)} 个问题：")
        for i, issue in enumerate(all_issues, 1):
            print(f"  {i}. {issue}")
        
        # 分类问题
        critical = [i for i in all_issues if i.startswith("❌")]
        warning = [i for i in all_issues if i.startswith("⚠️")]
        
        if critical:
            print()
            print("🚨 严重问题（必须解决）：")
            for issue in critical:
                print(f"   - {issue}")
        
        if warning:
            print()
            print("⚠️  警告问题（建议检查）：")
            for issue in warning:
                print(f"   - {issue}")
    
    print()
    print("=" * 70)
    
    return len(all_issues) == 0


if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n检查中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n检查过程出现异常：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
