#!/bin/bash
# QuantCore Indicators 构建脚本

set -e

echo "========================================="
echo "QuantCore Indicators 构建脚本"
echo "========================================="

# 检查依赖
check_dependencies() {
    echo "检查依赖..."
    
    if ! command -v cargo &> /dev/null; then
        echo "错误：未找到 Rust/Cargo，请先安装 Rust"
        echo "访问：https://rustup.rs/"
        exit 1
    fi
    
    if ! command -v maturin &> /dev/null; then
        echo "安装 maturin..."
        pip install maturin
    fi
    
    echo "✓ 依赖检查完成"
}

# 开发模式构建
build_dev() {
    echo "========================================="
    echo "开发模式构建"
    echo "========================================="
    
    cd "$(dirname "$0")"
    
    echo "构建 Rust 扩展..."
    maturin develop
    
    echo "✓ 开发构建完成"
}

# 发布模式构建
build_release() {
    echo "========================================="
    echo "发布模式构建"
    echo "========================================="
    
    cd "$(dirname "$0")"
    
    echo "构建发布版本..."
    maturin build --release
    
    echo "构建产物在 target/wheels/ 目录"
    echo "✓ 发布构建完成"
}

# 运行测试
run_tests() {
    echo "========================================="
    echo "运行测试"
    echo "========================================="
    
    cd "$(dirname "$0")"
    
    echo "运行 Rust 测试..."
    cargo test
    
    echo "运行 Python 测试..."
    pytest tests/ -v
    
    echo "✓ 测试完成"
}

# 运行基准测试
run_benchmarks() {
    echo "========================================="
    echo "运行基准测试"
    echo "========================================="
    
    cd "$(dirname "$0")"
    
    echo "运行 Rust 基准测试..."
    cargo bench
    
    echo "✓ 基准测试完成"
}

# 清理
clean() {
    echo "========================================="
    echo "清理构建产物"
    echo "========================================="
    
    cd "$(dirname "$0")"
    
    echo "删除 target 目录..."
    rm -rf target/
    
    echo "删除 Python 构建产物..."
    rm -rf dist/ build/ *.egg-info
    
    echo "删除 Python 缓存..."
    find . -type d -name "__pycache__" -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    
    echo "✓ 清理完成"
}

# 显示帮助
show_help() {
    echo "用法：$0 [命令]"
    echo ""
    echo "命令:"
    echo "  dev       开发模式构建（默认）"
    echo "  release   发布模式构建"
    echo "  test      运行测试"
    echo "  bench     运行基准测试"
    echo "  clean     清理构建产物"
    echo "  help      显示帮助信息"
    echo ""
    echo "示例:"
    echo "  $0 dev      # 开发构建"
    echo "  $0 release  # 发布构建"
    echo "  $0 test     # 运行测试"
}

# 主函数
main() {
    case "${1:-dev}" in
        dev)
            check_dependencies
            build_dev
            ;;
        release)
            check_dependencies
            build_release
            ;;
        test)
            run_tests
            ;;
        bench)
            run_benchmarks
            ;;
        clean)
            clean
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            echo "未知命令：$1"
            show_help
            exit 1
            ;;
    esac
}

main "$@"
