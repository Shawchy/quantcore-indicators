# 构建指南

## 环境要求

### 必需
- **Rust** >= 1.70.0
- **Python** >= 3.8
- **maturin** >= 1.0

### 可选
- **pytest** (用于测试)
- **criterion** (用于基准测试)

## 安装依赖

### 1. 安装 Rust

```bash
# Linux/macOS
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Windows
# 访问 https://rustup.rs/ 下载并运行 rustup-init.exe
```

### 2. 安装 maturin

```bash
pip install maturin
```

### 3. 安装开发依赖

```bash
pip install pytest pytest-benchmark numpy pandas
```

## 快速开始

### 开发模式构建

```bash
# 克隆仓库
cd quantcore-indicators

# 开发模式构建（自动安装到当前 Python 环境）
maturin develop

# 或者使用构建脚本
./build.sh dev
```

### 验证安装

```python
>>> from quantcore_indicators import ma, rsi
>>> import numpy as np
>>> prices = np.random.rand(100)
>>> ma(prices, 20)
array([...])
```

## 构建命令

### 开发构建

```bash
# 构建并安装到当前 Python 环境
maturin develop

# 开启热重载
maturin develop --watch
```

### 发布构建

```bash
# 构建 wheel 文件
maturin build --release

# 构建产物在 target/wheels/ 目录
```

### 安装本地 wheel

```bash
pip install target/wheels/quantcore_indicators-*.whl
```

## 测试

### 运行 Rust 测试

```bash
cargo test
```

### 运行 Python 测试

```bash
pytest tests/ -v
```

### 运行所有测试

```bash
./build.sh test
```

## 基准测试

### 运行 Rust 基准测试

```bash
cargo bench
```

### 查看基准测试结果

基准测试结果会显示在终端，并生成 HTML 报告：

```bash
# 查看报告
open target/criterion/report/index.html  # macOS
xdg-open target/criterion/report/index.html  # Linux
```

## 打包发布

### 1. 更新版本号

编辑 `Cargo.toml` 和 `pyproject.toml` 中的版本号。

### 2. 构建所有平台

```bash
# Linux
maturin build --release --manylinux

# macOS
maturin build --release --target x86_64-apple-darwin
maturin build --release --target aarch64-apple-darwin

# Windows
maturin build --release --target x86_64-pc-windows-msvc
```

### 3. 发布到 PyPI

```bash
# 安装 twine
pip install twine

# 上传
twine upload target/wheels/*
```

## 故障排查

### 问题：找不到 Rust 编译器

```bash
# 检查 Rust 安装
rustc --version

# 重新安装 Rust
rustup update
```

### 问题：maturin 构建失败

```bash
# 清理构建缓存
maturin develop --clean

# 或者
cargo clean
maturin develop
```

### 问题：Python 版本不兼容

```bash
# 检查 Python 版本
python --version

# 确保使用 Python 3.8+
python3.9 -m pip install maturin
python3.9 -m maturin develop
```

### 问题：导入错误

```python
# 确保在正确的目录
cd quantcore-indicators

# 重新安装
maturin develop --force
```

## 性能优化

### 编译优化

```bash
# 在 Cargo.toml 中添加
[profile.release]
lto = true
codegen-units = 1
```

### 使用 Arrow 零拷贝

```python
import pyarrow as pa
from quantcore_indicators import ma_arrow

# 创建 Arrow 数组
array = pa.array([1.0, 2.0, 3.0, 4.0, 5.0])

# 零拷贝计算
result = ma_arrow(array)
```

## CI/CD

### GitHub Actions 示例

```yaml
name: Build and Test

on: [push, pull_request]

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Install Rust
      uses: dtolnay/rust-action@stable
    
    - name: Install Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: |
        pip install maturin pytest
    
    - name: Build
      run: maturin develop
    
    - name: Test
      run: pytest tests/ -v
```

## 更多信息

- [Rust 文档](https://doc.rust-lang.org/book/)
- [PyO3 文档](https://pyo3.rs/)
- [maturin 文档](https://www.maturin.rs/)
- [Apache Arrow](https://arrow.apache.org/)
