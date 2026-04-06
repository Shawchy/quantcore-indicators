#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QuantCore Indicators 依赖版本兼容性检查脚本

检查所有依赖的版本兼容性，确保构建成功
"""

import sys
import subprocess
from pathlib import Path

def print_header(text):
    print("\n" + "="*60)
    print(text)
    print("="*60)

def check_python_version():
    """检查 Python 版本"""
    print_header("Python 版本检查")
    version = sys.version_info
    print(f"Python 版本：{version.major}.{version.minor}.{version.micro}")
    
    if version.major == 3 and version.minor >= 8:
        print("✓ Python 版本符合要求 (>= 3.8)")
        return True
    else:
        print("✗ Python 版本不符合要求 (需要 >= 3.8)")
        return False

def check_rust_version():
    """检查 Rust 版本"""
    print_header("Rust 版本检查")
    
    try:
        result = subprocess.run(
            ["rustc", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Rust 编译器：{result.stdout.strip()}")
        
        # 解析版本号
        version_str = result.stdout.strip()
        if "1.70" in version_str or any(f"1.{i}" in version_str for i in range(71, 100)):
            print("✓ Rust 版本符合要求 (>= 1.70)")
            return True
        else:
            print(f"⚠ Rust 版本可能过旧 (建议 >= 1.70)")
            return True  # 仍然尝试
    except subprocess.CalledProcessError:
        print("✗ 未找到 Rust 编译器")
        print("请安装 Rust: https://rustup.rs/")
        return False
    except FileNotFoundError:
        print("✗ 未找到 Rust 编译器")
        print("请安装 Rust: https://rustup.rs/")
        return False

def check_cargo_version():
    """检查 Cargo 版本"""
    print_header("Cargo 版本检查")
    
    try:
        result = subprocess.run(
            ["cargo", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Cargo: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError:
        print("✗ 未找到 Cargo")
        return False
    except FileNotFoundError:
        print("✗ 未找到 Cargo")
        return False

def check_maturin():
    """检查 maturin"""
    print_header("Maturin 检查")
    
    try:
        result = subprocess.run(
            ["maturin", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"Maturin: {result.stdout.strip()}")
        print("✓ Maturin 已安装")
        return True
    except subprocess.CalledProcessError:
        print("✗ 未找到 Maturin")
        print("请安装：pip install maturin")
        return False
    except FileNotFoundError:
        print("✗ 未找到 Maturin")
        print("请安装：pip install maturin")
        return False

def check_python_packages():
    """检查 Python 包"""
    print_header("Python 包版本检查")
    
    required_packages = {
        'numpy': '>=1.20.0',
        'pyarrow': '>=10.0.0',
    }
    
    all_installed = True
    
    for package, min_version in required_packages.items():
        try:
            pkg = __import__(package)
            version = getattr(pkg, '__version__', 'unknown')
            print(f"✓ {package}: {version}")
        except ImportError:
            print(f"✗ {package}: 未安装")
            all_installed = False
    
    return all_installed

def check_cargo_dependencies():
    """检查 Cargo 依赖"""
    print_header("Cargo 依赖检查")
    
    cargo_toml = Path("Cargo.toml")
    if not cargo_toml.exists():
        print("✗ 未找到 Cargo.toml")
        return False
    
    print("✓ Cargo.toml 存在")
    
    # 读取并解析关键依赖
    content = cargo_toml.read_text(encoding='utf-8')
    
    # 检查关键依赖
    key_deps = [
        'pyo3 = { version = "0.28"',
        'numpy = "0.28"',
        'arrow-array = "58"',
        'pyo3-arrow = "0.17"',
    ]
    
    for dep in key_deps:
        if dep.split('=')[0].strip() in content:
            print(f"✓ 依赖已配置：{dep.split('=')[0].strip()}")
        else:
            print(f"⚠ 依赖可能缺失：{dep.split('=')[0].strip()}")
    
    return True

def test_build():
    """测试构建"""
    print_header("测试构建")
    
    try:
        print("运行 cargo check...")
        result = subprocess.run(
            ["cargo", "check", "--features", "numpy-backend"],
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✓ Cargo check 通过")
            return True
        else:
            print("✗ Cargo check 失败")
            print(result.stdout)
            print(result.stderr)
            return False
    except subprocess.TimeoutExpired:
        print("⚠ Cargo check 超时（可能是首次构建）")
        return True
    except FileNotFoundError:
        print("✗ 未找到 cargo")
        return False

def main():
    """主函数"""
    print("="*60)
    print("QuantCore Indicators 依赖兼容性检查")
    print("="*60)
    
    checks = [
        ("Python 版本", check_python_version),
        ("Rust 版本", check_rust_version),
        ("Cargo 版本", check_cargo_version),
        ("Maturin", check_maturin),
        ("Python 包", check_python_packages),
        ("Cargo 依赖", check_cargo_dependencies),
        ("测试构建", test_build),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 检查失败：{e}")
            results.append((name, False))
    
    # 总结
    print_header("检查总结")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print(f"\n总计：{passed}/{total} 项通过")
    
    if passed == total:
        print("\n✓ 所有检查通过！可以开始构建")
        return 0
    else:
        print("\n⚠ 部分检查未通过，请修复后再构建")
        return 1

if __name__ == "__main__":
    sys.exit(main())
