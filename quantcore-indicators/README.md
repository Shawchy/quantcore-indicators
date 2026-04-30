# QuantCore Indicators

高性能金融指标库，使用 Rust 编写核心计算，通过 PyO3 提供 Python 绑定。

## 特性

- 🚀 **极致性能**: Rust 核心，比纯 Python 快 10-100 倍
- 📊 **零拷贝**: Apache Arrow 列式内存，高效数据交换
- 🐍 **Python 3.14 支持**: 完全兼容最新 Python 版本
- 📈 **丰富指标**: 21 种常用技术指标，持续扩展
- 🔒 **类型安全**: Rust 强类型系统保证
- 📦 **易于安装**: `pip install quantcore-indicators`
- 🔧 **PyO3 0.28**: 使用最新的 Python-Rust 绑定技术

## 安装

```bash
pip install quantcore-indicators
```

## 快速开始

```python
from quantcore_indicators import ma, ema, macd, rsi, bollinger_bands

# 移动平均
prices = [100.0, 101.0, 102.0, 103.0, 104.0, 105.0]
ma_values = ma(prices, period=3)
print(ma_values)  # [101.0, 102.0, 103.0, 104.0]

# RSI
rsi_values = rsi(prices, period=14)
print(rsi_values)

# MACD
macd_result = macd(prices, fast=12, slow=26, signal=9)
print(macd_result['macd'])
print(macd_result['signal'])
print(macd_result['histogram'])
```

## 性能对比

```python
import numpy as np
from quantcore_indicators import ma as ma_rust
from pure_python_indicators import ma as ma_python

prices = np.random.rand(10000).tolist()

# 纯 Python 实现
%timeit ma_python(prices, 20)  # ~50ms

# Rust 实现
%timeit ma_rust(prices, 20)    # ~0.5ms (快 100 倍!)
```

## 支持的指标

### 趋势指标
- **MA** - 移动平均 (Simple Moving Average)
- **EMA** - 指数移动平均 (Exponential Moving Average)
- **WMA** - 加权移动平均 (Weighted Moving Average)
- **DEMA** - 双指数移动平均 (Double EMA)
- **TEMA** - 三指数移动平均 (Triple EMA)
- **HMA** - Hull 移动平均 (Hull Moving Average)
- **MACD** - 异同移动平均 (Moving Average Convergence Divergence)
- **ADX** - 平均趋向指标 (Average Directional Index)
- **ROC** - 变动率 (Rate of Change)
- **PSAR** - 抛物线指标 (Parabolic SAR)

### 动量指标
- **RSI** - 相对强弱指标 (Relative Strength Index)
- **KDJ** - 随机指标 (KDJ Indicator)
- **CCI** - 商品通道指标 (Commodity Channel Index)
- **Williams %R** - 威廉指标 (Williams Percent Range)
- **Stochastic** - 随机指标 (Stochastic Oscillator)

### 成交量指标
- **OBV** - 能量潮 (On-Balance Volume)
- **VWAP** - 成交量加权平均价 (Volume Weighted Average Price)

### 波动率指标
- **ATR** - 平均真实波幅 (Average True Range)
- **NATR** - 归一化真实波幅 (Normalized ATR)
- **BOLL** - 布林带 (Bollinger Bands)

## 开发指南

### 环境要求

- **Python**: 3.14+
- **Rust**: 1.83+ (PyO3 0.28 要求)
- **maturin**: 1.0+

### 构建

```bash
# 安装 maturin
pip install maturin

# 设置 Python 路径 (Windows)
$env:PYO3_PYTHON = "path\to\python.exe"

# 开发模式构建
maturin develop

# 发布构建
maturin build --release
```

### 测试

```bash
# Rust 测试
cargo test

# 基准测试
cargo bench
```

## 许可证

MIT License

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)
