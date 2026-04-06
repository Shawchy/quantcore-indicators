# QuantCore 项目概览

## 🎯 项目愿景

打造一款**高性能、模块化、生产级**的 Python 量化交易框架，媲美 Backtrader、Vn.py 等专业框架。

## 📦 项目结构

```
quantcore/
├── README.md                      # 项目介绍
├── QUICK_START.md                 # 快速开始指南
├── IMPLEMENTATION_PLAN.md         # 详细实施计划
├── pyproject.toml                 # Python 项目配置
├── Cargo.toml -> rust-engine/Cargo.toml  # Rust 项目配置
│
├── rust-engine/                   # Rust 核心引擎
│   ├── Cargo.toml                 # Rust 依赖配置
│   └── src/
│       ├── lib.rs                 # 库入口
│       ├── core/                  # 核心数据结构
│       │   ├── bar.rs             # K 线数据
│       │   ├── order.rs           # 订单
│       │   ├── trade.rs           # 成交
│       │   ├── position.rs        # 持仓
│       │   ├── portfolio.rs       # 投资组合
│       │   └── tick.rs            # Tick 数据
│       ├── engine/                # 回测引擎
│       │   ├── backtest.rs        # 回测引擎实现
│       │   ├── matching.rs        # 订单匹配
│       │   └── live.rs            # 实盘引擎（待实现）
│       ├── strategy/              # 策略框架
│       │   ├── base.rs            # 策略基类
│       │   ├── context.rs         # 策略上下文
│       │   └── runner.rs          # 策略运行器
│       ├── data/                  # 数据层
│       │   ├── loader.rs          # 数据加载器
│       │   ├── feed.rs            # 数据源特征
│       │   ├── cache.rs           # 数据缓存
│       │   └── adapters/          # 数据源适配器
│       ├── risk/                  # 风险管理
│       │   ├── manager.rs         # 风险管理器
│       │   ├── limits.rs          # 仓位限制
│       │   └── monitor.rs         # 风险监控
│       ├── performance/           # 绩效分析
│       │   ├── analyzer.rs        # 绩效分析器
│       │   ├── metrics.rs         # 绩效指标
│       │   └── reporter.rs        # 报告生成器
│       └── utils/                 # 工具函数
│           ├── errors.rs          # 错误处理
│           ├── logging.rs         # 日志
│           └── helpers.rs         # 辅助函数
│
├── python-api/                    # Python 接口层
│   └── quantcore/
│       ├── __init__.py            # 包入口
│       ├── core/                  # 核心数据（Python 版本）
│       ├── engine/                # 回测引擎（Python 版本）
│       ├── strategy/              # 策略框架（Python 版本）
│       ├── data/                  # 数据加载（Python 版本）
│       ├── risk/                  # 风险管理（Python 版本）
│       └── performance/           # 绩效分析（Python 版本）
│
├── examples/                      # 示例策略
│   ├── basic_strategies/          # 基础策略
│   ├── advanced_strategies/       # 高级策略
│   └── real-world/                # 实战策略
│
├── benchmarks/                    # 性能测试
│   ├── backtrader_compare/        # 与 Backtrader 对比
│   └── performance_tests/         # 性能测试
│
├── docs/                          # 文档
│   ├── getting-started/           # 入门指南
│   ├── user-guide/                # 用户指南
│   ├── api-reference/             # API 参考
│   └── examples/                  # 示例
│
└── scripts/                       # 构建脚本
    ├── build.py                   # 构建脚本
    ├── test.py                    # 测试脚本
    └── release.py                 # 发布脚本
```

## 🏗️ 架构设计

### 三层架构

```
┌─────────────────────────────────────────────────┐
│              Python 接口层                       │
│  - 策略开发（简单、灵活）                        │
│  - 数据分析（pandas、numpy）                     │
│  - 可视化（matplotlib、plotly）                  │
│  - API 封装（用户友好）                          │
└─────────────────────────────────────────────────┘
                    ↓↑ (PyO3 FFI)
┌─────────────────────────────────────────────────┐
│              Rust 核心引擎                       │
│  - 回测引擎（事件驱动）                          │
│  - 订单匹配（高精度）                            │
│  - 风险管理（实时监控）                          │
│  - 绩效计算（完整指标）                          │
│  - 数据处理（高性能）                            │
└─────────────────────────────────────────────────┘
                    ↓↑
┌─────────────────────────────────────────────────┐
│              数据源层                            │
│  - Baostock（主力）                              │
│  - xtquant（补充）                               │
│  - Tushare（可选）                               │
│  - CSV/Database（本地）                          │
└─────────────────────────────────────────────────┘
```

## 🔧 技术栈

### Rust 引擎

| 组件 | 技术选型 | 用途 |
|------|----------|------|
| **PyO3** | 0.20 | Python 互操作 |
| **serde** | 1.0 | 序列化/反序列化 |
| **tokio** | 1.0 | 异步运行时 |
| **rayon** | 1.8 | 并行计算 |
| **ndarray** | 0.15 | 数值计算 |
| **rust_decimal** | 1.33 | 高精度小数 |
| **chrono** | 0.4 | 日期时间 |
| **thiserror** | 1.0 | 错误处理 |

### Python 接口

| 组件 | 技术选型 | 用途 |
|------|----------|------|
| **pandas** | 2.0+ | 数据处理 |
| **numpy** | 1.24+ | 数值计算 |
| **matplotlib** | 3.7+ | 可视化 |
| **maturin** | 1.3+ | Rust-Python 构建 |

## 📊 功能模块

### 1. 数据层 (Data Layer)

**功能**:
- ✅ 多数据源支持（Baostock、xtquant、Tushare）
- ✅ 数据标准化（统一数据格式）
- ✅ 数据缓存（内存 + 磁盘）
- ⏳ 实时数据流

**文件**:
- `rust-engine/src/data/loader.rs` - 数据加载器
- `rust-engine/src/data/feed.rs` - 数据源特征
- `rust-engine/src/data/cache.rs` - 数据缓存
- `rust-engine/src/data/adapters/` - 数据源适配器

### 2. 回测引擎 (Backtest Engine)

**功能**:
- ✅ 事件驱动架构
- ✅ 订单匹配引擎
- ✅ 支持多种订单类型
- ✅ A 股规则支持（T+1、涨跌停）
- ⏳ 并行回测
- ⏳ 多品种支持

**文件**:
- `rust-engine/src/engine/backtest.rs` - 回测引擎
- `rust-engine/src/engine/matching.rs` - 订单匹配
- `rust-engine/src/engine/live.rs` - 实盘引擎（待实现）

### 3. 策略框架 (Strategy Framework)

**功能**:
- ✅ 策略基类
- ✅ 策略生命周期管理
- ✅ 策略上下文
- ⏳ 内置指标库（20+）
- ⏳ 策略组合
- ⏳ 参数优化

**文件**:
- `rust-engine/src/strategy/base.rs` - 策略基类
- `rust-engine/src/strategy/context.rs` - 策略上下文
- `rust-engine/src/strategy/runner.rs` - 策略运行器

### 4. 风险管理 (Risk Management)

**功能**:
- ✅ 仓位管理
- ✅ 止损止盈
- ✅ 单日亏损限制
- ✅ 最大回撤限制
- ⏳ 实时风险监控
- ⏳ VaR 计算

**文件**:
- `rust-engine/src/risk/manager.rs` - 风险管理器
- `rust-engine/src/risk/limits.rs` - 仓位限制
- `rust-engine/src/risk/monitor.rs` - 风险监控

### 5. 绩效分析 (Performance Analysis)

**功能**:
- ✅ 基础指标计算
- ✅ 交易统计
- ⏳ 完整指标体系
- ⏳ 归因分析
- ⏳ 报告生成（HTML、PDF）

**文件**:
- `rust-engine/src/performance/analyzer.rs` - 绩效分析器
- `rust-engine/src/performance/metrics.rs` - 绩效指标
- `rust-engine/src/performance/reporter.rs` - 报告生成器

## 🚀 实施进度

### 第一阶段：基础架构（第 1-2 个月）

**状态**: 🟢 进行中

**完成**:
- ✅ 项目目录结构
- ✅ Rust 项目配置
- ✅ Python 项目配置
- ✅ 核心数据模型（Bar、Order、Trade、Position、Portfolio）
- ✅ 回测引擎骨架
- ✅ 策略框架骨架
- ✅ README 文档
- ✅ 实施计划文档

**待完成**:
- ⏳ 订单匹配引擎实现
- ⏳ 数据加载器实现
- ⏳ PyO3 绑定
- ⏳ 示例策略

### 第二阶段：功能完善（第 3-5 个月）

**计划**:
- ⏳ 内置指标库（20+）
- ⏳ 风险管理系统
- ⏳ 并行回测支持
- ⏳ 参数优化工具
- ⏳ 50+ 示例策略

### 第三阶段：实盘支持（第 6-8 个月）

**计划**:
- ⏳ CTP 接口（期货）
- ⏳ XTP 接口（股票）
- ⏳ 实盘引擎
- ⏳ 监控系统
- ⏳ 生产环境部署

## 📈 性能目标

| 指标 | Backtrader | QuantCore（目标） | 提升 |
|------|------------|------------------|------|
| 回测速度 | 100 秒 | 5 秒 | **20 倍** |
| 内存占用 | 500MB | 100MB | **80% 降低** |
| 并行回测（10 策略） | 15 分钟 | 30 秒 | **30 倍** |
| 支持数据量 | 100 万条 | 1 亿条 | **100 倍** |

## 🎓 学习资源

### 官方文档

- [README.md](README.md) - 项目介绍
- [QUICK_START.md](QUICK_START.md) - 快速开始
- [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) - 实施计划

### 外部资源

- **Rust**: [The Rust Programming Language](https://doc.rust-lang.org/book/)
- **PyO3**: [PyO3 User Guide](https://pyo3.rs/)
- **量化交易**: [量化交易：如何建立自己的算法交易事业](https://book.douban.com/subject/35016898/)

### 参考项目

- **Backtrader**: https://github.com/mementum/backtrader
- **Vn.py**: https://github.com/vnpy/vnpy
- **RQAlpha**: https://github.com/ricequant/rqalpha

## 🤝 参与贡献

### 如何贡献

1. Fork 仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 贡献方向

- 🐛 修复 Bug
- ✨ 新增功能
- 📚 完善文档
- 🧪 编写测试
- 🎨 优化性能
- 💡 提供建议

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📬 联系方式

- **项目网站**: https://quantcore.io
- **邮箱**: contact@quantcore.io
- **GitHub**: https://github.com/quantcore/quantcore
- **微信群**: QuantCore 开发者社区

---

**开始你的量化交易之旅！** 🚀

> 种一棵树最好的时间是十年前，其次是现在。
