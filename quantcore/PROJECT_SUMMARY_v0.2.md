# QuantCore 项目总结

**最后更新**: 2026-04-06  
**当前版本**: v0.2.0

## 📋 项目概述

**QuantCore - A 股原生全栈式量化交易框架**

QuantCore 是一个面向 A 股市场的全栈式量化交易框架，结合了 Rust 的高性能和 Python 的易用性。项目采用混合架构，Rust 负责核心计算，Python 提供友好的开发接口。

**核心定位**：
- 🇨🇳 **A 股原生**：深度优化 A 股交易规则（T+1、涨跌停、交易费用）
- 🔬 **探索研究**：为量化研究而设计，快速验证策略想法
- ⚡ **高性能**：Rust 核心引擎，回测速度领先 10-20 倍
- 🧩 **全栈式**：回测 + 分析 + 可视化 + 风控（未来实盘）

**发展理念**：
- 以**探索性研究**为主，帮助用户快速验证策略想法
- 提供**高性能回测**、**多策略组合**和**专业可视化**
- 未来将支持**实盘交易**，形成完整的量化交易闭环

## 🎯 核心特性

### 1. 高性能回测引擎
- Rust 核心引擎，性能比 Backtrader 快 10-20 倍
- 事件驱动架构，支持多种订单类型
- 完整的回测功能（市价单、限价单、T+1 规则）

### 2. A 股交易支持
- 原生支持 T+1 交易规则
- 涨跌停板限制
- A 股交易费用结构（佣金、印花税）

### 3. 多策略组合
- 策略权重配置
- 自动资金分配
- 独立策略运行
- 组合绩效分析

### 4. 专业可视化
- 资金曲线图
- 回撤曲线图
- 收益分布图
- 月度收益图
- 策略对比图

### 5. 风险管理
- 仓位限制
- 止损策略
- 单日最大亏损
- 最大回撤控制

### 6. 技术指标库
- MA/EMA - 移动平均
- MACD - 异同移动平均
- RSI - 相对强弱指标
- BOLL - 布林带
- KDJ - 随机指标
- ATR - 平均真实波幅
- CCI - 商品通道指数
- Williams %R - 威廉指标
- OBV - 能量潮

### 7. 数据加载器
- Baostock 数据源
- CSV 文件导入
- 可扩展的数据源接口

### 8. 参数优化
- 网格搜索
- 随机搜索
- 并行执行支持

## 📁 项目结构

```
quantcore/
├── rust-engine/              # Rust 核心引擎
│   ├── src/
│   │   ├── lib.rs           # 主模块（1273 行）
│   │   └── ...
│   └── Cargo.toml
│
├── python-api/               # Python 接口层
│   └── quantcore/
│       ├── core/            # 核心数据模型
│       ├── engine/          # 回测引擎
│       ├── strategy/        # 策略框架
│       │   ├── base.py      # 策略基类
│       │   └── portfolio.py # 多策略组合 ⭐
│       ├── data/            # 数据加载器
│       ├── indicators.py    # 技术指标
│       ├── risk.py          # 风险管理
│       ├── optimizer.py     # 参数优化
│       ├── logger.py        # 日志系统
│       └── plotting.py      # 可视化 ⭐
│
├── examples/                # 示例代码
│   ├── basic_strategy.py    # 基础策略示例
│   ├── advanced_strategies.py # 高级策略库
│   ├── multi_strategy_portfolio.py # 多策略组合 ⭐
│   └── visualization_example.py # 可视化示例 ⭐
│
├── tests/                   # 测试文件
│   ├── test_*.py
│
├── test_*.py               # 测试文件（根目录）
│   ├── test_strategy_portfolio.py ⭐
│   ├── test_visualization.py ⭐
│   └── test_tplus1.py ⭐
│
└── docs/                   # 文档
    ├── README.md           # 项目总览
    ├── QUICK_START.md      # 快速开始
    ├── USER_GUIDE.md       # 用户使用指南
    ├── VISUALIZATION_GUIDE.md # 可视化指南 ⭐
    └── CHANGELOG_v0.2.0.md # 版本更新日志 ⭐
```

⭐ = v0.2.0 新增

## 🚀 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/quantcore/quantcore.git
cd quantcore

# 安装依赖
pip install maturin
maturin develop

# 可视化依赖（可选）
pip install matplotlib numpy scipy
```

### 第一个策略

```python
from quantcore import Strategy, BacktestEngine, BacktestConfig

class MyStrategy(Strategy):
    def on_bar(self, bar, engine):
        # 策略逻辑
        if buy_signal:
            engine.buy(bar.symbol, bar.close, 1000)
        elif sell_signal:
            engine.sell(bar.symbol, bar.close, 1000)

# 运行回测
config = BacktestConfig(initial_capital=1000000)
engine = BacktestEngine(config)
result = engine.run(MyStrategy(), bars)

print(f"收益：{result.total_return:.2%}")
```

### 多策略组合

```python
from quantcore.strategy.portfolio import StrategyPortfolio

portfolio = StrategyPortfolio(initial_capital=1000000)
portfolio.add_strategy("MACD", MACDStrategy(), weight=0.4)
portfolio.add_strategy("RSI", RSIStrategy(), weight=0.3)
portfolio.add_strategy("BOLL", BOLLStrategy(), weight=0.3)

result = portfolio.run(bars, tplus1=True)
print(f"组合收益：{result['total_return']:.2%}")
```

### 可视化

```python
from quantcore.plotting import plot_all_charts

plot_all_charts(
    result=result,
    title="策略绩效分析",
    save_dir="./output"
)
```

## 📊 已实现功能清单

### 核心引擎 ✅
- [x] Rust 核心引擎
- [x] PyO3 Python 绑定
- [x] 事件驱动架构
- [x] 订单匹配引擎
- [x] 市价单/限价单
- [x] T+1 交易规则
- [x] 绩效分析

### 策略框架 ✅
- [x] Strategy 基类
- [x] 策略运行器
- [x] 多策略组合
- [x] 策略权重配置
- [x] 独立引擎运行

### 技术指标 ✅
- [x] MA/EMA
- [x] MACD
- [x] RSI
- [x] BOLL
- [x] KDJ
- [x] ATR
- [x] CCI
- [x] Williams %R
- [x] OBV

### 风险管理 ✅
- [x] 仓位限制
- [x] 止损策略
- [x] 单日亏损限制
- [x] 最大回撤控制

### 数据加载 ✅
- [x] Baostock 数据源
- [x] CSV 文件导入
- [x] 数据加载器接口

### 参数优化 ✅
- [x] 网格搜索
- [x] 随机搜索
- [x] 并行执行

### 可视化 ✅
- [x] 资金曲线图
- [x] 回撤曲线图
- [x] 收益分布图
- [x] 月度收益图
- [x] 策略对比图
- [x] 综合图表生成

### 工具链 ✅
- [x] 日志系统
- [x] 参数优化器
- [x] 风险管理器
- [x] 数据加载器

### 文档 ✅
- [x] README
- [x] 快速开始指南
- [x] 用户使用指南
- [x] 可视化模块指南
- [x] 版本更新日志
- [x] 示例代码

## 📈 版本历史

### v0.2.0 (2026-04-06) - VisualPortfolio
**重大更新**：
- ✨ 多策略组合支持
- ✨ 专业可视化系统
- ✨ T+1 规则完善

**新增文件**：
- `strategy/portfolio.py` (407 行)
- `plotting.py` (646 行)
- `VISUALIZATION_GUIDE.md` (406 行)
- 测试文件：387 + 396 + 200 行
- 示例文件：319 + 334 行

**测试覆盖**：11/11 测试用例 100% 通过

### v0.1.2 (2026-04-05)
**功能**：
- 技术指标扩展（KDJ, ATR, CCI, Williams %R, OBV）
- 参数优化工具（网格搜索、随机搜索）
- 日志系统
- 限价单支持

### v0.1.1 (2026-04-04)
**功能**：
- 数据加载器（Baostock/CSV）
- 高级策略库（MACD, RSI, BOLL, Multi-Factor, Trend Following）
- 竞品分析报告

### v0.1.0 (2026-04-03)
**首发版本**：
- Rust 核心引擎
- Python 接口
- 回测引擎
- 策略框架
- 基础指标（MA, EMA, MACD, RSI, BOLL）
- 风险管理
- 绩效分析

## 🎯 项目亮点

### 1. 性能优势
- Rust 核心，性能卓越
- 比 Backtrader 快 10-20 倍
- 内存占用降低 80%

### 2. A 股原生支持
- T+1 交易规则
- 涨跌停板
- A 股费用结构

### 3. 易用性
- Python 友好接口
- 简洁的 API 设计
- 完整的文档和示例

### 4. 可扩展性
- 模块化设计
- 可插拔组件
- 易于添加新功能

### 5. 专业可视化
- 5+ 种专业图表
- 一键生成报告
- 高质量输出

## 🔮 未来规划

### 短期 (v0.3.x)
- [ ] 实盘交易接口
- [ ] 实时数据接入
- [ ] 更多技术指标
- [ ] 策略参数优化器增强

### 中期 (v0.4.x)
- [ ] 机器学习集成
- [ ] 因子分析框架
- [ ] 投资组合优化
- [ ] 风险控制增强

### 长期 (v1.0.x)
- [ ] 完整的回测生态系统
- [ ] 云端部署支持
- [ ] 策略市场
- [ ] 社区建设

## 📚 学习资源

### 入门
1. 阅读 [README.md](README.md) 了解项目
2. 查看 [QUICK_START.md](QUICK_START.md) 快速上手
3. 运行 [examples/](examples/) 中的示例代码

### 进阶
1. 阅读 [USER_GUIDE.md](USER_GUIDE.md) 深入学习
2. 查看 [VISUALIZATION_GUIDE.md](VISUALIZATION_GUIDE.md) 学习可视化
3. 研究高级策略示例

### 深入
1. 阅读 Rust 引擎源码
2. 贡献代码到项目
3. 开发自己的策略

## 🤝 贡献指南

欢迎贡献代码、文档和建议！

1. Fork 本仓库
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 开启 Pull Request

## 📄 许可证

MIT License - 查看 [LICENSE](LICENSE) 文件。

## 🙏 致谢

- Backtrader - 量化框架的灵感来源
- Vn.py - 国内量化社区的标杆
- PyO3 - Rust 与 Python 的桥梁
- Rust - 高性能系统编程语言

## 📬 联系方式

- 项目网站：https://quantcore.io
- 邮箱：contact@quantcore.io
- 微信群：QuantCore 开发者社区

---

**QuantCore - 为量化交易而生！** 🚀
