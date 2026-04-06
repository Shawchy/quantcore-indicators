# QuantCore Indicators 快速开始

## 环境检查 ✅

已确认安装：
- ✅ maturin 1.12.6
- ✅ Python 3.12

## 第一步：检查 Rust 安装

```powershell
# 检查 Rust 是否安装
rustc --version
cargo --version
```

如果未安装 Rust，请访问：https://rustup.rs/

## 第二步：开发模式构建

```powershell
# 进入项目目录
cd m:\Project\Quant\quantcore-indicators

# 开发模式构建（自动安装到当前 Python 环境）
maturin develop
```

## 第三步：验证安装

```python
python -c "from quantcore_indicators import ma; import numpy as np; print('MA test:', ma(np.random.rand(10), 3))"
```

## 第四步：运行测试

```powershell
# 运行 Python 测试
pytest tests/ -v

# 运行 Rust 测试
cargo test
```

## 第五步：使用示例

```python
from quantcore_indicators import ma, rsi, macd
import numpy as np

# 生成数据
prices = np.random.rand(1000) * 100 + 50

# 计算指标
ma_values = ma(prices, 20)
rsi_values = rsi(prices, 14)
macd_result = macd(prices)

print(f"MA(20) 最新值：{ma_values[-1]:.2f}")
print(f"RSI(14) 最新值：{rsi_values[-1]:.2f}")
print(f"MACD 最新值：{macd_result['macd'][-1]:.2f}")
```

## 常见问题

### 问题 1: 找不到 Rust 编译器

```powershell
# 安装 Rust
# Windows: 下载 https://win.rustup.rs/x86_64
# 运行 rustup-init.exe
```

### 问题 2: maturin develop 失败

```powershell
# 清理缓存
cargo clean
maturin develop --force
```

### 问题 3: 导入错误

```python
# 确保在项目目录下运行
cd m:\Project\Quant\quantcore-indicators
python -c "import quantcore_indicators; print('OK')"
```

## 性能测试

```python
import numpy as np
import time
from quantcore_indicators import ma

# 大数据集
prices = np.random.rand(100000)

# 测试性能
start = time.time()
result = ma(prices, 20)
elapsed = time.time() - start

print(f"数据量：{len(prices):,}")
print(f"耗时：{elapsed*1000:.2f}ms")
print(f"速度：{len(prices)/elapsed/1000000:.1f}M 点/秒")
```

## 下一步

1. 运行性能基准测试
2. 查看使用示例
3. 集成到 QuantCore 项目

---

**项目位置**: `m:\Project\Quant\quantcore-indicators\`
**文档**: 查看 README.md 和 BUILD.md
