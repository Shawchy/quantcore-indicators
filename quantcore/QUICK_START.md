# QuantCore 快速开始指南

## 前置条件

在开始之前，请确保已安装以下工具：

### 1. Python 3.8+

```bash
# 检查 Python 版本
python --version
# 或
python3 --version
```

如果未安装，请从 [python.org](https://www.python.org/downloads/) 下载安装。

### 2. Rust 1.70+

**Windows:**
```bash
# 下载并运行 rustup-init.exe
# 从 https://rustup.rs/ 下载
```

**Linux/macOS:**
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

**验证安装:**
```bash
rustc --version
cargo --version
```

### 3. 开发工具

```bash
# 安装 Python 开发工具
pip install maturin pytest black ruff
```

---

## 安装 QuantCore

### 方法 1：从源码安装（推荐）

```bash
# 1. 进入项目目录
cd quantcore

# 2. 创建虚拟环境（推荐）
python -m venv venv

# Windows
.\venv\Scripts\activate

# Linux/macOS
source venv/bin/activate

# 3. 安装 maturin
pip install maturin

# 4. 开发模式安装
maturin develop

# 或生产模式安装
maturin build --release
pip install target/wheels/*.whl
```

### 方法 2：使用 pip（未来支持）

```bash
pip install quantcore
```

---

## 验证安装

### 1. 测试 Python 导入

```python
# test_import.py
import quantcore

print(f"QuantCore 版本：{quantcore.version()}")
print(f"可用模块：{quantcore.__all__}")
```

运行：
```bash
python test_import.py
```

### 2. 测试 Rust 引擎

```python
# test_rust.py
from quantcore import Bar
from datetime import datetime, timezone

# 创建 Bar 对象
bar = Bar(
    timestamp=datetime.now(timezone.utc),
    open=10.0,
    high=10.5,
    low=9.8,
    close=10.2,
    volume=1000000
)

print(bar)
print(f"平均价格：{bar.average_price}")
print(f"涨跌幅：{bar.price_change_percent:.2%}")
```

---

## 第一个回测策略

### 示例 1：简单移动平均策略

```python
# examples/ma_strategy.py
from quantcore import Strategy, Bar, BacktestEngine, BacktestConfig

class MAStrategy(Strategy):
    """单均线策略"""
    
    def __init__(self, period=20):
        super().__init__()
        self.period = period
        self.prices = []
        self.position = 0
    
    def on_bar(self, bar: Bar, engine):
        # 记录价格
        self.prices.append(bar.close)
        
        # 等待足够的数据
        if len(self.prices) < self.period:
            return
        
        # 计算移动平均
        ma = sum(self.prices[-self.period:]) / self.period
        
        # 交易逻辑
        if bar.close > ma and self.position == 0:
            # 价格上穿均线，买入
            engine.buy(bar.symbol, bar.close, 1000)
            self.position = 1
        elif bar.close < ma and self.position == 1:
            # 价格下穿均线，卖出
            engine.sell(bar.symbol, bar.close, 1000)
            self.position = 0

# 运行回测
if __name__ == "__main__":
    # 配置回测
    config = BacktestConfig(
        initial_capital=1000000,
        commission_rate=0.0003,
        slippage=0.001
    )
    
    engine = BacktestEngine(config)
    
    # TODO: 加载数据
    # bars = load_data('SH.600000', '2020-01-01', '2024-12-31')
    
    # 运行回测
    # result = engine.run(MAStrategy(period=20), bars)
    
    # 输出结果
    # print(f"总收益：{result.total_return:.2%}")
    # print(f"夏普比率：{result.sharpe_ratio:.2f}")
    # print(f"最大回撤：{result.max_drawdown:.2%}")
```

### 示例 2：双均线策略

```python
# examples/dual_ma_strategy.py
from quantcore import Strategy, Bar, BacktestEngine, BacktestConfig

class DualMAStrategy(Strategy):
    """双均线交叉策略"""
    
    def __init__(self, fast_period=5, slow_period=20):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.prices = []
        self.position = 0
    
    def on_bar(self, bar: Bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.slow_period:
            return
        
        # 计算均线
        fast_ma = sum(self.prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(self.prices[-self.slow_period:]) / self.slow_period
        
        # 金叉：快线上穿慢线
        if fast_ma > slow_ma and self.position == 0:
            engine.buy(bar.symbol, bar.close, 1000)
            self.position = 1
        
        # 死叉：快线下穿慢线
        elif fast_ma < slow_ma and self.position == 1:
            engine.sell(bar.symbol, bar.close, 1000)
            self.position = 0

# 运行回测
if __name__ == "__main__":
    config = BacktestConfig(initial_capital=1000000)
    engine = BacktestEngine(config)
    
    # TODO: 加载数据并运行回测
    # result = engine.run(DualMAStrategy(), bars)
```

---

## 使用数据加载器

### 示例：从 Baostock 加载数据

```python
# examples/load_data.py
from quantcore import DataLoader

# 创建数据加载器
loader = DataLoader()

# 加载历史数据
bars = loader.load_history(
    symbol='SH.600000',
    start_date='2020-01-01',
    end_date='2024-12-31'
)

print(f"加载了 {len(bars)} 条 K 线数据")

# 查看第一条和最后一条
if bars:
    print(f"第一条：{bars[0]}")
    print(f"最后一条：{bars[-1]}")
```

### 示例：从 CSV 加载数据

```python
# examples/load_csv.py
import pandas as pd
from quantcore import Bar
from datetime import datetime, timezone

def load_csv(filepath: str) -> list:
    """从 CSV 文件加载数据"""
    df = pd.read_csv(filepath)
    
    bars = []
    for _, row in df.iterrows():
        bar = Bar(
            timestamp=datetime.strptime(row['date'], '%Y-%m-%d').replace(tzinfo=timezone.utc),
            open=row['open'],
            high=row['high'],
            low=row['low'],
            close=row['close'],
            volume=row['volume']
        )
        bars.append(bar)
    
    return bars

# 使用
bars = load_csv('data/600000.csv')
```

---

## 风险管理示例

```python
# examples/risk_management.py
from quantcore import RiskManager, PositionLimit

# 创建风险管理器
risk = RiskManager()

# 添加单只股票仓位限制
risk.add_limit(PositionLimit(
    symbol='SH.600000',
    max_percent=0.1,      # 不超过 10%
    max_volume=10000      # 不超过 10000 股
))

# 设置单日最大亏损
risk.set_daily_loss_limit(50000)  # 5 万元

# 设置最大回撤
risk.set_max_drawdown(0.15)  # 15%

# 检查订单
# if risk.check_order(order, portfolio):
#     engine.submit_order(order)
```

---

## 绩效分析示例

```python
# examples/performance_analysis.py
from quantcore import PerformanceAnalyzer, PerformanceMetrics

# 创建绩效分析器
analyzer = PerformanceAnalyzer(
    trades=engine.trades,
    portfolio_values=engine.daily_values
)

# 计算指标
metrics = analyzer.calculate_metrics()

print("=" * 50)
print("绩效分析报告")
print("=" * 50)
print(f"总收益：{metrics.total_return:.2%}")
print(f"年化收益：{metrics.annual_return:.2%}")
print(f"夏普比率：{metrics.sharpe_ratio:.2f}")
print(f"最大回撤：{metrics.max_drawdown:.2%}")
print(f"胜率：{metrics.win_rate:.2%}")
print(f"盈亏比：{metrics.profit_loss_ratio:.2f}")
print(f"交易次数：{metrics.total_trades}")
print("=" * 50)
```

---

## 运行测试

### Python 测试

```bash
# 运行所有测试
pytest python-api/tests

# 运行特定测试
pytest python-api/tests/test_core.py

# 带覆盖率报告
pytest --cov=quantcore python-api/tests
```

### Rust 测试

```bash
# 进入 Rust 目录
cd rust-engine

# 运行测试
cargo test

# 带输出
cargo test -- --nocapture
```

---

## 代码格式化

### Python 代码

```bash
# 格式化代码
black python-api/

# 检查代码质量
ruff check python-api/

# 自动修复
ruff check --fix python-api/
```

### Rust 代码

```bash
cd rust-engine

# 格式化代码
cargo fmt

# 代码检查
cargo clippy

# 自动修复
cargo clippy --fix
```

---

## 常见问题

### Q1: 安装时遇到 PyO3 错误

**解决方案:**
```bash
# 确保 Rust 已正确安装
rustc --version

# 重新安装 maturin
pip uninstall maturin
pip install maturin

# 重新安装
maturin develop
```

### Q2: Python 导入错误

**解决方案:**
```bash
# 检查是否在虚拟环境中
which python  # Linux/macOS
where python  # Windows

# 重新安装
pip install -e .
```

### Q3: Rust 编译错误

**解决方案:**
```bash
# 更新 Rust 工具链
rustup update

# 清理并重新编译
cd rust-engine
cargo clean
cargo build
```

---

## 下一步

### 学习路径

1. **阅读文档**
   - [README.md](README.md) - 项目概述
   - [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - 实施计划
   - [API 文档](docs/api-reference/) - 详细 API

2. **运行示例**
   ```bash
   cd examples
   python basic_strategy.py
   ```

3. **开发自己的策略**
   - 参考示例策略
   - 实现 Strategy 基类
   - 运行回测

4. **贡献代码**
   - Fork 仓库
   - 创建分支
   - 提交 PR

### 资源链接

- **GitHub**: https://github.com/quantcore/quantcore
- **文档**: https://quantcore.readthedocs.io
- **PyPI**: https://pypi.org/project/quantcore
- **Rust 文档**: https://doc.rust-lang.org/
- **PyO3 文档**: https://pyo3.rs/

---

## 获取帮助

### 遇到问题？

1. **查看文档**: [quantcore.readthedocs.io](https://quantcore.readthedocs.io)
2. **搜索 Issues**: [GitHub Issues](https://github.com/quantcore/quantcore/issues)
3. **提问**: 创建新的 Issue
4. **社区**: 加入 QuantCore 开发者微信群

### 联系方式

- **邮箱**: contact@quantcore.io
- **微信**: QuantCore 开发者社区
- **QQ 群**: 123456789

---

**祝你量化交易之旅愉快！** 🚀

> 从简单策略开始，逐步完善，你也能打造出专业的量化框架！
