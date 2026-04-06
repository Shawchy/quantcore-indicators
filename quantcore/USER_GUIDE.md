# QuantCore 使用指南

## 目录

1. [快速开始](#快速开始)
2. [安装配置](#安装配置)
3. [核心概念](#核心概念)
4. [策略开发](#策略开发)
5. [数据加载](#数据加载)
6. [技术指标](#技术指标)
7. [风险管理](#风险管理)
8. [回测示例](#回测示例)
9. [绩效分析](#绩效分析)
10. [常见问题](#常见问题)

---

## 快速开始

### 1. 最简单的策略回测

```python
from quantcore import *

# 1. 准备数据
bars = generate_sample_data()  # 或使用 load_baostock_data()

# 2. 定义策略
class MyStrategy(Strategy):
    def on_bar(self, bar, engine):
        # 简单的买入持有策略
        if len(engine.trades) == 0:
            self.buy(bar.symbol, bar.close, 1000)

# 3. 配置回测
config = BacktestConfig(initial_capital=1000000.0)
engine = BacktestEngine(config)
strategy = MyStrategy()

# 4. 运行回测
runner = StrategyRunner(strategy)
result = runner.run(engine, bars)

# 5. 查看结果
print(f"总收益：{result.total_return*100:.2f}%")
print(f"交易次数：{result.total_trades}")
```

### 2. 使用技术指标

```python
from quantcore import *

class MAStrategy(Strategy):
    def on_init(self, engine):
        self.prices = []
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < 20:
            return
        
        # 计算均线
        ma5 = sum(self.prices[-5:]) / 5
        ma20 = sum(self.prices[-20:]) / 20
        
        # 金叉买入
        if ma5 > ma20 and len(engine.trades) == 0:
            self.buy(bar.symbol, bar.close, 1000)
```

### 3. 加载真实数据

```python
from quantcore import *

# 从 Baostock 加载
bars = load_baostock_data(
    symbol="SH.600000",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# 从 CSV 加载
loader = CSVLoader()
bars = loader.load(
    symbol="SH.600000",
    file_path="data/600000.csv"
)
```

---

## 安装配置

### 系统要求

- Python 3.10+
- Rust 1.70+ (用于编译 Rust 引擎)
- Windows / Linux / macOS

### 安装步骤

```bash
# 1. 克隆项目
cd m:\Project\Quant\quantcore

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac

# 3. 安装 Python 依赖
pip install -r requirements.txt

# 4. 编译 Rust 引擎
cd rust-engine
cargo build --release

# 5. 测试安装
cd ..
python example_quickstart.py
```

### 依赖项

**Python 依赖** (`requirements.txt`):
```
pandas>=2.0.0
numpy>=1.24.0
baostock>=0.8.8
```

**Rust 依赖** (`rust-engine/Cargo.toml`):
```toml
pyo3 = "0.23"
serde = "1.0"
```

---

## 核心概念

### 数据模型

#### Bar - K 线数据

```python
bar = Bar(
    timestamp=datetime(2024, 1, 1),
    symbol="SH.600000",
    open=10.0,
    high=10.5,
    low=9.8,
    close=10.3,
    volume=1000000,
    turnover=10300000.0
)
```

**属性**:
- `timestamp`: 时间戳
- `symbol`: 证券代码
- `open/high/low/close`: 开高低收
- `volume`: 成交量
- `turnover`: 成交额

**计算方法**:
```python
bar.average_price  # 平均价
bar.price_range    # 价格区间
bar.price_change_percent  # 涨跌幅
```

#### Order - 订单

```python
order = Order(
    order_id="ORD-001",
    strategy_id="strategy_1",
    symbol="SH.600000",
    side=OrderSide.BUY,
    order_type=OrderType.MARKET,
    price=10.0,
    quantity=1000
)
```

**订单方向** (`OrderSide`):
- `BUY`: 买入
- `SELL`: 卖出

**订单类型** (`OrderType`):
- `MARKET`: 市价单
- `LIMIT`: 限价单

#### Trade - 成交

```python
trade = Trade(
    trade_id="TRD-001",
    order_id="ORD-001",
    symbol="SH.600000",
    side=OrderSide.BUY,
    price=10.0,
    quantity=1000,
    commission=3.0,
    tax=0.0
)
```

#### Portfolio - 投资组合

```python
portfolio = Portfolio(
    cash=1000000.0,
    positions={"SH.600000": 1000}
)

# 计算总资产
total_asset = portfolio.total_asset

# 获取持仓
position = portfolio.get_position("SH.600000")
```

---

## 策略开发

### 策略基类

所有策略都必须继承 `Strategy` 类：

```python
class Strategy:
    # 策略参数
    parameters = {}
    
    def on_init(self, engine):
        """策略初始化（只调用一次）"""
        pass
    
    def on_bar(self, bar, engine):
        """每根 K 线触发（必须实现）"""
        raise NotImplementedError
    
    def on_finish(self, engine):
        """回测结束回调"""
        pass
    
    # 交易方法
    def buy(self, symbol, price, volume):
        """买入"""
        pass
    
    def sell(self, symbol, price, volume):
        """卖出"""
        pass
```

### 策略开发完整示例

```python
from quantcore import *

class DualMAStrategy(Strategy):
    """双均线策略"""
    
    # 策略参数
    parameters = {
        'fast_period': 5,   # 快速均线周期
        'slow_period': 20,  # 慢速均线周期
    }
    
    def on_init(self, engine):
        """初始化"""
        self.fast_period = self.parameters['fast_period']
        self.slow_period = self.parameters['slow_period']
        self.prices = []
        self.position = 0
    
    def on_bar(self, bar, engine):
        """K 线事件处理"""
        # 更新价格序列
        self.prices.append(bar.close)
        
        # 等待足够的数据
        if len(self.prices) < self.slow_period:
            return
        
        # 计算均线
        fast_ma = sum(self.prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(self.prices[-self.slow_period:]) / self.slow_period
        
        # 获取之前的均线值（用于判断交叉）
        prev_fast_ma = sum(self.prices[-self.fast_period-1:-1]) / self.fast_period
        prev_slow_ma = sum(self.prices[-self.slow_period-1:-1]) / self.slow_period
        
        # 交易逻辑
        if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma:
            # 金叉：买入
            if self.position == 0:
                self.buy(bar.symbol, bar.close, 1000)
                self.position = 1
                print(f"{bar.timestamp} 金叉买入：{bar.close:.2f}")
        
        elif prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma:
            # 死叉：卖出
            if self.position == 1:
                self.sell(bar.symbol, bar.close, 1000)
                self.position = 0
                print(f"{bar.timestamp} 死叉卖出：{bar.close:.2f}")
    
    def on_finish(self, engine):
        """回测结束"""
        print(f"策略结束，最终持仓：{self.position}")
```

### 使用策略运行器

```python
# 创建策略实例
strategy = DualMAStrategy()

# 配置回测
config = BacktestConfig(
    initial_capital=1000000.0,  # 初始资金
    commission_rate=0.0003,      # 手续费率
    slippage=0.001,              # 滑点
)

# 创建引擎
engine = BacktestEngine(config)

# 运行回测
runner = StrategyRunner(strategy)
result = runner.run(engine, bars)
```

---

## 数据加载

### Baostock 数据源

```python
from quantcore import load_baostock_data

# 加载日 K 线
bars = load_baostock_data(
    symbol="SH.600000",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# 使用数据加载器
loader = create_data_loader(use_cache=True)
bars = loader.load_history(
    symbol="SH.600000",
    start_date="2024-01-01",
    end_date="2024-12-31",
    source='baostock'
)
```

### CSV 文件加载

```python
from quantcore import CSVLoader

# 基本用法
loader = CSVLoader()
bars = loader.load(
    symbol="SH.600000",
    file_path="data/600000.csv"
)

# 带日期过滤
bars = loader.load(
    symbol="SH.600000",
    file_path="data/600000.csv",
    start_date="2024-01-01",
    end_date="2024-06-30"
)

# 批量加载多个文件
files = {
    "SH.600000": "data/600000.csv",
    "SH.600001": "data/600001.csv",
}
result = loader.load_multiple(files)
```

**CSV 文件格式要求**:

```csv
date,open,high,low,close,volume,turnover
2024-01-02,10.0,10.5,9.8,10.3,1000000,10300000.0
2024-01-03,10.3,10.8,10.2,10.6,1200000,12720000.0
```

支持的列名别名:
- `date/datetime/time` → `timestamp`
- `Open` → `open`
- `High` → `high`
- `Low` → `low`
- `Close` → `close`
- `Vol/Volume` → `volume`
- `Turnover/Amount/Money` → `turnover`

### 数据缓存

```python
from quantcore import CachedDataLoader

# 创建带缓存的加载器
loader = CachedDataLoader(cache_size=1000)

# 第一次加载（从数据源）
bars1 = loader.load_history("SH.600000", "2024-01-01", "2024-12-31")
# 输出：Cache miss, loaded 250 bars for SH.600000

# 第二次加载（从缓存）
bars2 = loader.load_history("SH.600000", "2024-01-01", "2024-12-31")
# 输出：Cache hit: SH.600000:2024-01-01:2024-12-31:baostock
```

---

## 技术指标

### 移动平均线

```python
from quantcore import ma, ema

# 简单移动平均
ma5 = ma(prices, period=5)
ma20 = ma(prices, period=20)

# 指数移动平均
ema12 = ema(prices, period=12)
ema26 = ema(prices, period=26)
```

### MACD

```python
from quantcore import macd

result = macd(prices, fast=12, slow=26, signal=9)

# 返回值
dif = result['macd']        # DIF 线
dea = result['signal']      # DEA 线
histogram = result['histogram']  # 柱状图
```

### RSI

```python
from quantcore import rsi

rsi_6 = rsi(prices, period=6)
rsi_12 = rsi(prices, period=12)
rsi_24 = rsi(prices, period=24)
```

**RSI 解读**:
- RSI > 80: 超买
- RSI < 20: 超卖

### 布林带

```python
from quantcore import bollinger_bands

result = bollinger_bands(prices, period=20, std_dev=2)

# 返回值
upper = result['upper']    # 上轨
middle = result['middle']  # 中轨（MA20）
lower = result['lower']    # 下轨
```

**布林带用法**:
- 价格突破上轨：可能超买
- 价格跌破下轨：可能超卖
- 带宽收窄：即将变盘

---

## 风险管理

### 仓位限制

```python
from quantcore import RiskManager, PositionLimit

# 创建风险管理器
risk = RiskManager(
    total_position_limit=0.9,  # 总仓位上限 90%
    single_position_limit=0.3   # 单只股票上限 30%
)

# 添加单个证券限制
risk.add_position_limit(
    PositionLimit(
        symbol="SH.600000",
        max_percent=0.1,    # 最多 10% 仓位
        max_volume=10000    # 最多 10000 股
    )
)

# 检查买入是否合规
can_buy = risk.check_buy(
    symbol="SH.600000",
    price=10.0,
    volume=1000,
    portfolio_value=1000000.0,
    current_position=0
)

if can_buy:
    # 执行买入
    pass
```

### 止损策略

```python
from quantcore import StopLoss

# 创建止损策略
stop_loss = StopLoss(
    stop_loss_percent=0.05,   # 5% 止损
    stop_profit_percent=0.20  # 20% 止盈
)

# 检查是否需要止损
should_stop = stop_loss.check_stop_loss(
    entry_price=10.0,
    current_price=9.5
)

if should_stop:
    # 执行卖出
    pass
```

---

## 回测示例

### 完整回测流程

```python
from quantcore import *

# 1. 准备数据
bars = load_baostock_data("SH.600000", "2024-01-01", "2024-12-31")

# 2. 定义策略
class MyStrategy(Strategy):
    parameters = {'period': 20}
    
    def on_init(self, engine):
        self.prices = []
        self.period = self.parameters['period']
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        if len(self.prices) < self.period:
            return
        
        ma = sum(self.prices[-self.period:]) / self.period
        if bar.close > ma and len(engine.trades) == 0:
            self.buy(bar.symbol, bar.close, 1000)
        elif bar.close < ma and len(engine.trades) > 0:
            self.sell(bar.symbol, bar.close, 1000)

# 3. 配置回测
config = BacktestConfig(
    initial_capital=1000000.0,
    commission_rate=0.0003,
    slippage=0.001,
    stamp_tax=0.001,
)

# 4. 运行回测
strategy = MyStrategy()
engine = BacktestEngine(config)
runner = StrategyRunner(strategy)
result = runner.run(engine, bars)

# 5. 查看结果
print("=" * 60)
print("回测结果")
print("=" * 60)
print(f"初始资金：{result.initial_capital:,.2f}")
print(f"最终资金：{result.final_capital:,.2f}")
print(f"总收益：{result.total_return*100:.2f}%")
print(f"交易次数：{result.total_trades}")
print(f"持仓：{result.positions}")
```

### 多策略对比

```python
strategies = {
    "MA5_20": DualMAStrategy(fast_period=5, slow_period=20),
    "MA10_60": DualMAStrategy(fast_period=10, slow_period=60),
    "MA20_120": DualMAStrategy(fast_period=20, slow_period=120),
}

results = {}
for name, strategy in strategies.items():
    engine = BacktestEngine(config)
    runner = StrategyRunner(strategy)
    result = runner.run(engine, bars)
    results[name] = result

# 对比结果
print("策略对比:")
for name, result in results.items():
    print(f"{name}: {result.total_return*100:.2f}%")
```

---

## 绩效分析

### 基础绩效指标

```python
from quantcore import PerformanceAnalyzer

# 创建分析器
analyzer = PerformanceAnalyzer(
    trades=result.trades,
    portfolio_values=result.daily_values,
    initial_capital=result.initial_capital
)

# 计算指标
total_return = analyzer.total_return()
annual_return = analyzer.annual_return(days=250)
volatility = analyzer.volatility()
sharpe = analyzer.sharpe_ratio(risk_free_rate=0.03)
max_dd = analyzer.max_drawdown()
win_rate = analyzer.win_rate()

print(f"总收益：{total_return*100:.2f}%")
print(f"年化收益：{annual_return*100:.2f}%")
print(f"波动率：{volatility*100:.2f}%")
print(f"夏普比率：{sharpe:.2f}")
print(f"最大回撤：{max_dd*100:.2f}%")
print(f"胜率：{win_rate*100:.2f}%")
```

### 绩效报告

```python
from quantcore import PerformanceReport

# 生成报告
report = PerformanceReport(result)
report.print_report()
```

**输出示例**:
```
============================================================
绩效分析报告
============================================================
初始资金：1000000.00
最终资金：996133.96
总收益：-0.39%
交易次数：92
============================================================
```

---

## 常见问题

### Q1: 如何安装 Rust？

**A**: 访问 [rustup.rs](https://rustup.rs) 下载安装工具，然后运行：
```bash
rustup install stable
```

### Q2: 回测结果为负怎么办？

**A**: 检查以下几点：
1. 手续费和滑点设置是否过高
2. 策略逻辑是否有问题
3. 回测时间段是否合适
4. 是否过度交易

### Q3: 如何优化策略参数？

**A**: 使用网格搜索或随机搜索：
```python
# 网格搜索示例
for fast in [5, 10, 20]:
    for slow in [20, 60, 120]:
        strategy = DualMAStrategy(fast_period=fast, slow_period=slow)
        # 运行回测...
```

### Q4: 支持哪些数据源？

**A**: 目前支持：
- Baostock（免费 A 股数据）
- CSV 文件
- 可扩展自定义数据源

### Q5: 如何贡献代码？

**A**: 欢迎提交 Pull Request 到项目仓库！

---

## 下一步

- [ ] 参数优化工具
- [ ] 实时数据支持
- [ ] 图表可视化
- [ ] 多账户管理

---

**文档版本**: v0.1.0  
**最后更新**: 2026-04-06  
**维护者**: QuantCore Team
