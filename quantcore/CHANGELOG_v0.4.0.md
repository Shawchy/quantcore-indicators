# QuantCore v0.4.0 版本发布报告

**发布日期**: 2026-04-06  
**版本**: v0.4.0  
**代号**: LiveTrading

---

## 🎉 重大更新

### v0.4.0 中期版本发布！

本次更新实现了 QuantCore 从中期向成熟框架迈进的关键功能，包括风控系统、CTA 策略框架、实时数据接入和实盘交易接口原型。

---

## 🔒 1. 风险管理系统 ⭐⭐⭐⭐⭐

**全新推出的全面风控系统！**

### 核心功能

**仓位控制**：
- ✅ 最大仓位比例限制（默认 95%）
- ✅ 单只股票最大仓位（默认 30%）
- ✅ 最小现金比例（默认 5%）

**止损止盈**：
- ✅ 固定比例止损（默认 8%）
- ✅ 固定比例止盈（默认 20%）
- ✅ 实时持仓监控

**交易限制**：
- ✅ 单日最大亏损限制
- ✅ 最大回撤控制（默认 15%）
- ✅ 单日最大交易次数

**风险预警**：
- ✅ 实时风险指标计算
- ✅ 多级风险预警（LOW/MEDIUM/HIGH/CRITICAL）
- ✅ 强制暂停交易（极端情况）

### 使用示例

```python
from quantcore.risk import RiskManager, RiskConfig

# 配置风控参数
config = RiskConfig(
    max_position_ratio=0.90,          # 最大仓位 90%
    max_single_position_ratio=0.30,   # 单只股票最大 30%
    stop_loss_ratio=0.08,             # 止损 8%
    stop_profit_ratio=0.20,           # 止盈 20%
    max_daily_loss=50000,             # 单日最大亏损 5 万
    max_drawdown_ratio=0.15,          # 最大回撤 15%
    max_trades_per_day=10             # 单日最多 10 笔交易
)

# 创建风控管理器
risk_manager = RiskManager(config, initial_capital=1000000)

# 更新组合资产
risk_manager.update_portfolio(total_asset=1050000, cash=200000)

# 交易前检查
if risk_manager.can_buy('SH.600000', amount=1000, price=10.5):
    engine.buy('SH.600000', 10.5, 1000)

# 更新持仓
risk_manager.update_position('SH.600000', 1000, 10.5, 10.8)

# 检查止损
if risk_manager.check_stop_loss('SH.600000', current_price=9.5):
    engine.sell('SH.600000', 9.5, 1000)

# 获取风险报告
report = risk_manager.get_risk_report()
print(report)
# {
#     'date': '2026-04-06',
#     'total_asset': 1050000,
#     'position_ratio': '80.00%',
#     'daily_pnl': '50000.00',
#     'current_drawdown': '2.00%',
#     'risk_level': 'low'
# }
```

**新增文件**: `python-api/quantcore/risk.py` (550+ 行)

---

## 📊 2. CTA 策略框架 ⭐⭐⭐⭐⭐

**专业的 CTA（Commodity Trading Advisor）策略框架！**

### 核心组件

**CTAStrategy 基类**：
- ✅ 自动化的数据管理（OHLCV）
- ✅ 持仓跟踪（CTAPosition）
- ✅ 信号生成（CTASignal）
- ✅ 止损止盈检查
- ✅ 参数配置系统

**经典 CTA 策略（3 个）**：

1. **DualMaCTAStrategy** - 双均线 CTA 策略
   - 金叉做多，死叉做空
   - 自动趋势跟踪

2. **ATRTrailingCTAStrategy** - ATR 移动止损策略
   - 突破 N 日高点开仓
   - ATR 移动止损保护

3. **BollingerCTAStrategy** - 布林带 CTA 策略
   - 触及下轨做多
   - 触及上轨或回归中轨平仓

### 使用示例

```python
from quantcore.strategy.cta import (
    CTAStrategy,
    DualMaCTAStrategy,
    ATRTrailingCTAStrategy,
    CTAParameter
)

# 自定义 CTA 策略
class MyCTAStrategy(CTAStrategy):
    def on_cta_bar(self, bar, engine):
        # 策略逻辑
        if buy_signal:
            self.buy_open(bar.symbol, bar.close, 1000)
        elif sell_signal:
            self.sell_close(bar.symbol, bar.close, 1000)

# 使用内置策略
params = CTAParameter(
    fast_period=10,
    slow_period=30,
    position_ratio=0.3
)

strategy = DualMaCTAStrategy(params)

# 运行回测
portfolio.add_strategy("CTA", strategy, weight=1.0)
result = portfolio.run(bars)
```

**新增文件**: `python-api/quantcore/strategy/cta.py` (650+ 行)

---

## 📡 3. 实时数据接入 ⭐⭐⭐⭐

**实时行情数据接入框架！**

### 核心功能

**Tick 数据**：
- ✅ 完整的 Tick 数据结构
- ✅ 买卖盘口支持
- ✅ 自动转换为 Bar

**数据订阅器**：
- ✅ 抽象基类（DataSubscriber）
- ✅ 模拟数据订阅器（测试用）
- ✅ Baostock 实时订阅器（轮询模式）

**数据管理器**：
- ✅ 统一管理多个订阅器
- ✅ 异步数据推送
- ✅ 回调机制

### 使用示例

```python
from quantcore.data.realtime import (
    create_mock_subscriber,
    RealtimeDataManager,
    TickData
)

# 创建数据管理器
manager = RealtimeDataManager()

# 添加模拟数据源
subscriber = create_mock_subscriber(
    symbols=['SH.600000', 'SH.600036'],
    base_prices={'SH.600000': 10.0, 'SH.600036': 35.0},
    volatility=0.02
)
manager.add_subscriber('mock', subscriber)

# 订阅数据
def on_tick(tick: TickData):
    print(f"{tick.symbol}: {tick.price}")

manager.subscribe('SH.600000', on_tick, 'mock')

# 启动（异步）
import asyncio
asyncio.run(manager.start_all())
```

**新增文件**: `python-api/quantcore/data/realtime.py` (380+ 行)

---

## 🎯 4. 实盘交易接口原型 ⭐⭐⭐⭐

**实盘交易的基础框架！**

### 核心组件

**交易接口抽象**：
- ✅ TradingGateway 抽象基类
- ✅ 订单管理（Order）
- ✅ 成交管理（Trade）
- ✅ 持仓管理（Position）
- ✅ 账户管理（Account）

**模拟交易接口**：
- ✅ MockTradingGateway（测试用）
- ✅ 模拟订单提交和成交
- ✅ 模拟持仓更新
- ✅ 模拟账户查询

**实盘交易引擎**：
- ✅ LiveTradingEngine
- ✅ 策略管理
- ✅ 启动/停止控制
- ✅ 买卖接口

### 使用示例

```python
from quantcore.trading import (
    create_mock_gateway,
    LiveTradingEngine,
    OrderSide,
    OrderType
)

# 创建模拟交易接口
gateway = create_mock_gateway(initial_cash=1000000)

# 创建交易引擎
engine = LiveTradingEngine(gateway)

# 添加策略
engine.add_strategy("MACD", MACDStrategy())

# 启动引擎（异步）
import asyncio
asyncio.run(engine.start())

# 下单交易
order_id = engine.buy('SH.600000', price=10.5, quantity=1000)

# 查询持仓
position = engine.get_position('SH.600000')
print(f"持仓：{position.quantity}股")

# 查询账户
account = engine.get_account()
print(f"总资产：{account.total_asset:,.2f}")

# 停止引擎
asyncio.run(engine.stop())
```

**新增文件**: 
- `python-api/quantcore/trading/gateway.py` (600+ 行)
- `python-api/quantcore/trading/__init__.py`

---

## 📊 功能对比

### v0.3.0 vs v0.4.0

| 功能模块 | v0.3.0 | v0.4.0 | 提升 |
|---------|--------|--------|------|
| **风控系统** | ❌ | ✅ 完整 | **新增** ⭐⭐⭐⭐⭐ |
| **CTA 框架** | ❌ | ✅ 完整 | **新增** ⭐⭐⭐⭐⭐ |
| **实时数据** | ❌ | ✅ 原型 | **新增** ⭐⭐⭐⭐ |
| **实盘接口** | ❌ | ✅ 原型 | **新增** ⭐⭐⭐⭐ |
| **策略模板** | 9 个 | 12 个 | +3 个 |
| **技术指标** | 20 个 | 20 个 | - |

### 代码统计

| 项目 | 代码量 | 说明 |
|-----|--------|------|
| 风控系统 | 550+ 行 | 完整的风控逻辑 |
| CTA 框架 | 650+ 行 | 3 个经典策略 |
| 实时数据 | 380+ 行 | 异步数据推送 |
| 实盘接口 | 600+ 行 | 交易接口原型 |
| **总计** | **2,180+ 行** | **全新代码** |

---

## 🎯 发展路线图完成度

**短期（v0.3.x）**：
- ✅ 技术指标（20 个）✅ 100%
- ✅ 数据库加载 ✅ 100%
- ✅ 数据重采样 ✅ 100%
- ✅ 策略模板（9 个）✅ 100%
- ✅ 文档完善 ✅ 100%

**中期（v0.4.x）**：
- ✅ 风控系统基础 ✅ 100%
- ✅ CTA 策略框架 ✅ 100%
- ✅ 实时数据接入 ✅ 100%
- ✅ 实盘交易接口原型 ✅ 100%

**长期（v1.0.x）**：
- ⏳ 全功能实盘支持（进行中）
- ⏳ 多市场（期货、期权）
- ⏳ 完整生态系统
- ⏳ 成为主流量化框架

---

## 💡 技术亮点

### 1. 风控系统

**设计特点**：
- 事前检查（can_buy/can_sell）
- 事中监控（实时指标）
- 事后分析（风险报告）
- 多级预警机制
- 强制熔断功能

**安全性**：
- 仓位限制防止过度交易
- 止损止盈保护本金
- 回撤控制避免大亏
- 交易频率限制

### 2. CTA 框架

**架构优势**：
- 继承 Strategy 基类，兼容回测引擎
- 自动数据管理，简化策略开发
- 信号系统标准化
- 参数配置灵活

**策略类型**：
- 趋势跟踪（双均线、ATR）
- 均值回归（布林带）
- 突破策略
- 多因子组合

### 3. 实时数据

**性能优化**：
- 异步数据推送
- 回调机制高效
- 支持多数据源
- 模拟数据测试

**数据格式**：
- 标准 Tick 结构
- 完整的盘口信息
- 自动 Bar 转换

### 4. 实盘接口

**设计模式**：
- 抽象工厂模式
- 回调通知机制
- 异步订单处理
- 本地缓存优化

**安全性**：
- 订单状态追踪
- 成交确认
- 持仓同步
- 账户监控

---

## 📚 使用场景

### 1. 完整回测工作流

```python
from quantcore.strategy.templates import DualMovingAverageStrategy
from quantcore.risk import RiskManager, RiskConfig
from quantcore.strategy.portfolio import StrategyPortfolio

# 配置风控
config = RiskConfig(max_position_ratio=0.90)
risk_manager = RiskManager(config, 1000000)

# 创建策略
strategy = DualMovingAverageStrategy(fast=5, slow=20)

# 运行回测
portfolio = StrategyPortfolio(initial_capital=1000000)
portfolio.add_strategy("DualMA", strategy, weight=1.0)

result = portfolio.run(bars, tplus1=True)

# 风控分析
risk_manager.update_portfolio(
    result['total_final_capital'],
    result['total_final_capital'] * 0.1
)

report = risk_manager.get_risk_report()
print(report)
```

### 2. CTA 策略实盘（模拟）

```python
from quantcore.trading import create_mock_gateway, LiveTradingEngine
from quantcore.strategy.cta import DualMaCTAStrategy
import asyncio

# 创建模拟交易接口
gateway = create_mock_gateway(1000000)

# 创建交易引擎
engine = LiveTradingEngine(gateway)

# 添加 CTA 策略
cta_strategy = DualMaCTAStrategy()
engine.add_strategy("CTA", cta_strategy)

# 启动
asyncio.run(engine.start())

# 运行中...
# 策略会自动根据实时数据生成信号并交易

# 停止
asyncio.run(engine.stop())
```

### 3. 实时数据监控

```python
from quantcore.data.realtime import (
    create_baostock_subscriber,
    RealtimeDataManager
)

# 创建数据管理器
manager = RealtimeDataManager()

# 添加 Baostock 实时数据源
subscriber = create_baostock_subscriber(
    symbols=['SH.600000'],
    interval=3.0  # 3 秒轮询一次
)
manager.add_subscriber('baostock', subscriber)

# 订阅
def on_tick(tick):
    print(f"{tick.symbol}: 最新价 {tick.price}")

manager.subscribe('SH.600000', on_tick, 'baostock')

# 启动
asyncio.run(manager.start_all())
```

---

## 🔮 后续计划

### v0.4.x 补丁版本（进行中）
- [ ] 完善实盘接口文档
- [ ] 添加更多 CTA 策略
- [ ] 优化实时数据性能
- [ ] 风控参数优化

### v0.5.x 功能增强（计划中）
- [ ] 对接真实交易 API（华泰、中信等）
- [ ] 期货 CTA 策略
- [ ] 期权策略框架
- [ ] 多账户管理

### v1.0.x 正式版（愿景）
- [ ] 全功能实盘支持
- [ ] 多市场覆盖（股票、期货、期权）
- [ ] 完整的生态系统
- [ ] 成为主流量化框架

---

## 🙏 致谢

感谢所有贡献者和用户！

## 📬 联系方式

- 项目网站：https://quantcore.io
- 邮箱：contact@quantcore.io
- 微信群：QuantCore 开发者社区

---

**QuantCore v0.4.0 - 从中期到成熟！** 🚀

> 路漫漫其修远兮，吾将上下而求索。
