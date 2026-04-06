# QuantCore v0.2.0 版本发布报告

**发布日期**: 2026-04-06  
**版本**: v0.2.0  
**代号**: VisualPortfolio

## 🎯 项目定位

**QuantCore - A 股原生全栈式量化交易框架**

- 🇨🇳 **A 股原生**：深度优化 A 股交易规则（T+1、涨跌停、交易费用）
- 🔬 **探索研究**：为量化研究而设计，快速验证策略想法
- ⚡ **高性能**：Rust 核心引擎，回测速度领先 10-20 倍
- 🧩 **全栈式**：回测 + 分析 + 可视化 + 风控（未来实盘）

**发展理念**：
- 以**探索性研究**为主，帮助用户快速验证策略想法
- 提供**高性能回测**、**多策略组合**和**专业可视化**
- 未来将支持**实盘交易**，形成完整的量化交易闭环

---

## 🎉 重大更新

### 1. 多策略组合支持

全新推出的多策略组合管理功能，让策略分散投资变得简单！

**核心特性**：
- ✅ 策略权重配置（支持自定义权重）
- ✅ 自动资金分配（按权重分配）
- ✅ 独立策略运行（每个策略独立引擎）
- ✅ 组合绩效分析（精确的夏普比率和回撤计算）
- ✅ 策略管理（添加/移除/启用/禁用）

**使用示例**：
```python
from quantcore.strategy.portfolio import StrategyPortfolio

# 创建组合
portfolio = StrategyPortfolio(initial_capital=1000000)

# 添加策略
portfolio.add_strategy("MACD", MACDStrategy(), weight=0.4)
portfolio.add_strategy("RSI", RSIStrategy(), weight=0.3)
portfolio.add_strategy("BOLL", BOLLStrategy(), weight=0.3)

# 运行回测
result = portfolio.run(bars, tplus1=True)

# 查看结果
print(f"组合收益：{result['total_return']:.2%}")
print(f"组合夏普：{result['sharpe_ratio']:.2f}")
```

**新增文件**：
- `python-api/quantcore/strategy/portfolio.py` - 策略组合核心模块
- `test_strategy_portfolio.py` - 完整测试套件（6 个测试用例全部通过）
- `examples/multi_strategy_portfolio.py` - 3 个完整使用示例

### 2. 专业可视化系统

一站式可视化解决方案，让数据分析更直观！

**图表类型**：
1. **资金曲线图** - 展示资产变化趋势，支持基准对比
2. **回撤曲线图** - 直观显示风险，自动标注最大回撤
3. **收益分布图** - 统计分析工具，包含正态拟合
4. **月度收益图** - 季节性分析，绿涨红跌配色
5. **策略对比图** - 多策略性能比较
6. **综合图表集** - 一键生成所有图表

**使用示例**：
```python
from quantcore.plotting import plot_all_charts

# 一键生成所有图表
plot_all_charts(
    result=result,
    title="多策略组合绩效分析",
    save_dir="./output/charts",
    show=True
)
```

**新增文件**：
- `python-api/quantcore/plotting.py` - 可视化核心模块（650+ 行）
- `test_visualization.py` - 4 个测试用例全部通过
- `examples/visualization_example.py` - 3 个完整示例
- `VISUALIZATION_GUIDE.md` - 完整使用指南（400+ 行）
- `requirements_visualization.txt` - 依赖配置

### 3. T+1 交易规则完善

深度优化的 A 股 T+1 交易规则支持！

**核心功能**：
- ✅ 当日买入不可当日卖出
- ✅ 自动持仓状态管理
- ✅ 每日自动更新 T+1 状态
- ✅ 卖出时严格检查可用持仓

**实现细节**：
- `Position` 类新增 T+1 状态字段
- `BacktestEngine` 集成 T+1 检查逻辑
- 每日结束时自动更新持仓状态

**测试验证**：
- `test_tplus1.py` - 完整 T+1 测试
- 测试结果显示 T+1 规则工作正常

## 📊 测试覆盖

### 单元测试

| 测试文件 | 测试用例数 | 通过数 | 状态 |
|---------|-----------|--------|------|
| test_strategy_portfolio.py | 6 | 6 | ✅ 通过 |
| test_visualization.py | 4 | 4 | ✅ 通过 |
| test_tplus1.py | 1 | 1 | ✅ 通过 |
| **总计** | **11** | **11** | **100%** |

### 示例验证

| 示例文件 | 示例数 | 运行状态 |
|---------|--------|----------|
| examples/multi_strategy_portfolio.py | 3 | ✅ 成功 |
| examples/visualization_example.py | 3 | ✅ 成功 |

## 📁 新增文件清单

### 核心模块
- `python-api/quantcore/strategy/portfolio.py` (407 行)
- `python-api/quantcore/plotting.py` (646 行)

### 测试文件
- `test_strategy_portfolio.py` (387 行)
- `test_visualization.py` (396 行)
- `test_tplus1.py` (200 行)

### 示例文件
- `examples/multi_strategy_portfolio.py` (319 行)
- `examples/visualization_example.py` (334 行)

### 文档
- `VISUALIZATION_GUIDE.md` (406 行)
- `requirements_visualization.txt` (14 行)
- `CHANGELOG_v0.2.0.md` (本文件)

### 更新文件
- `README.md` - 添加多策略组合和可视化示例
- `python-api/quantcore/core/__init__.py` - Position 类 T+1 支持
- `python-api/quantcore/engine/__init__.py` - BacktestEngine T+1 集成

## 🔧 技术亮点

### 1. 架构设计

**多策略组合架构**：
```
StrategyPortfolio（组合层）
    ↓
StrategyConfig × N（策略配置）
    ↓
BacktestEngine × N（独立引擎）
    ↓
汇总绩效分析
```

**可视化模块架构**：
```
plotting.py
├── plot_equity_curve()
├── plot_drawdown_curve()
├── plot_return_distribution()
├── plot_monthly_returns()
├── plot_strategy_comparison()
└── plot_all_charts()
```

### 2. 性能优化

- **独立引擎运行**：每个策略独立引擎，避免状态污染
- **精确绩效计算**：基于组合净值曲线计算夏普比率和回撤
- **批量图表生成**：一次性生成所有图表，提高效率

### 3. 用户体验

- **简洁 API**：3-5 行代码即可生成完整分析报告
- **智能格式化**：Y 轴自动显示 K/M 单位
- **专业美观**：合理的布局和配色
- **完整文档**：400+ 行使用指南

## 📈 功能对比

### v0.1.x vs v0.2.0

| 功能 | v0.1.x | v0.2.0 | 提升 |
|------|--------|--------|------|
| 单策略回测 | ✅ | ✅ | - |
| T+1 规则 | 基础 | 完善 | ⭐⭐⭐ |
| 多策略组合 | ❌ | ✅ | ⭐⭐⭐⭐⭐ |
| 资金曲线图 | ❌ | ✅ | ⭐⭐⭐⭐⭐ |
| 回撤分析 | ❌ | ✅ | ⭐⭐⭐⭐⭐ |
| 收益分布 | ❌ | ✅ | ⭐⭐⭐⭐ |
| 策略对比 | ❌ | ✅ | ⭐⭐⭐⭐⭐ |
| 综合图表 | ❌ | ✅ | ⭐⭐⭐⭐⭐ |

## 🎯 使用场景

### 1. 策略分散投资

通过多策略组合实现风险分散：
```python
portfolio = StrategyPortfolio(initial_capital=1000000)
portfolio.add_strategy("Trend", TrendStrategy(), weight=0.5)
portfolio.add_strategy("MeanReversion", MeanReversionStrategy(), weight=0.5)
```

### 2. 策略性能对比

快速对比多个策略的表现：
```python
results = {
    'MACD': {'daily_values': macd_values},
    'RSI': {'daily_values': rsi_values}
}
plot_strategy_comparison(results)
```

### 3. 完整绩效报告

一键生成专业绩效分析报告：
```python
plot_all_charts(result, title="策略绩效分析")
```

## 🚀 快速开始

### 安装依赖

```bash
# 核心依赖
pip install maturin

# 可视化依赖（可选）
pip install matplotlib numpy scipy
```

### 运行第一个多策略组合

```python
from quantcore.strategy.portfolio import StrategyPortfolio
from quantcore.plotting import plot_all_charts

# 创建组合
portfolio = StrategyPortfolio(initial_capital=1000000)

# 添加策略
portfolio.add_strategy("MACD", MACDStrategy(), weight=0.4)
portfolio.add_strategy("RSI", RSIStrategy(), weight=0.3)
portfolio.add_strategy("BOLL", BOLLStrategy(), weight=0.3)

# 运行
result = portfolio.run(bars, tplus1=True)

# 可视化
plot_all_charts(result, title="多策略组合")
```

## 📚 文档资源

- [README.md](README.md) - 项目总览
- [QUICK_START.md](QUICK_START.md) - 快速开始
- [USER_GUIDE.md](USER_GUIDE.md) - 用户使用指南
- [VISUALIZATION_GUIDE.md](VISUALIZATION_GUIDE.md) - 可视化模块指南
- [examples/](examples/) - 完整示例代码

## 🐛 已知问题

无严重已知问题。

## 🔮 未来计划

### v0.3.0 (计划中)
- [ ] 实盘交易接口
- [ ] 实时数据接入
- [ ] 策略参数优化器
- [ ] 更多技术指标
- [ ] 机器学习集成

### v0.2.x (补丁版本)
- [ ] Bug 修复
- [ ] 性能优化
- [ ] 文档完善
- [ ] 更多示例

## 🙏 致谢

感谢所有贡献者和用户！

## 📬 联系方式

- 项目网站：https://quantcore.io
- 邮箱：contact@quantcore.io
- 微信群：QuantCore 开发者社区

---

**开始你的量化交易之旅！** 🚀

> 种一棵树最好的时间是十年前，其次是现在。
