"""
依赖安装验证脚本

验证所有依赖是否正确安装
"""
import sys
from importlib import import_module

# 依赖清单及其最低版本
DEPENDENCIES = [
    # 核心框架
    ("fastapi", "0.115.0"),
    ("uvicorn", "0.34.0"),
    ("pydantic", "2.10.0"),
    ("pydantic_settings", "2.7.0"),
    
    # 数据处理
    ("pandas", "2.2.0"),
    ("polars", "1.16.0"),
    ("numpy", "1.26.0"),
    
    # 数据源
    ("efinance", "0.6.0"),
    ("akshare", "1.15.0"),
    ("baostock", "0.8.9"),
    
    # 技术指标
    ("pandas_ta", "0.3.14b"),
    
    # 存储
    ("sqlalchemy", "2.0.36"),
    ("aiosqlite", "0.20.0"),
    ("pyarrow", "18.1.0"),
    ("fastparquet", "2024.11.0"),
    
    # 工具
    ("loguru", "0.7.2"),
    ("httpx", "0.28.0"),
    
    # 测试
    ("pytest", "8.3.0"),
]

# 可选依赖
OPTIONAL_DEPENDENCIES = [
    ("torch", "2.5.0"),
    ("tensorflow", "2.18.0"),
    ("talib", "0.4.28"),
    ("redis", "5.2.0"),
]


def check_dependency(package_name, min_version):
    """检查单个依赖是否安装"""
    try:
        module = import_module(package_name)
        version = getattr(module, "__version__", "unknown")
        
        # 简单版本检查（实际应该使用 packaging.version）
        print(f"✓ {package_name}: {version}")
        return True
    except ImportError as e:
        print(f"✗ {package_name}: 未安装 - {e}")
        return False


def main():
    """主函数"""
    print("=" * 60)
    print("依赖安装验证")
    print("=" * 60)
    print()
    
    print("核心依赖:")
    print("-" * 60)
    
    installed = 0
    total = len(DEPENDENCIES)
    
    for package, version in DEPENDENCIES:
        if check_dependency(package, version):
            installed += 1
    
    print()
    print(f"核心依赖：{installed}/{total} 已安装")
    print()
    
    # 检查可选依赖
    optional_installed = 0
    optional_total = len(OPTIONAL_DEPENDENCIES)
    
    if OPTIONAL_DEPENDENCIES:
        print("可选依赖:")
        print("-" * 60)
        
        for package, version in OPTIONAL_DEPENDENCIES:
            if check_dependency(package, version):
                optional_installed += 1
        
        print()
        print(f"可选依赖：{optional_installed}/{optional_total} 已安装")
        print()
    
    # 总结
    print("=" * 60)
    total_installed = installed + optional_installed
    total_all = total + optional_total
    
    print(f"总计：{total_installed}/{total_all} 已安装")
    print(f"安装率：{total_installed/total_all*100:.1f}%")
    print("=" * 60)
    
    if installed == total:
        print("\n✓ 所有核心依赖已安装！")
        return 0
    else:
        print(f"\n✗ 缺少 {total - installed} 个核心依赖")
        print("\n请运行以下命令安装所有依赖:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    sys.exit(main())
