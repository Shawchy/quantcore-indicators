# 自研量化框架：Rust 引擎 + Python 接口

## 架构设计

### 总体架构

```
┌─────────────────────────────────────────────────┐
│              Python 接口层                       │
│  - 策略开发                                      │
│  - 数据分析                                      │
│  - 可视化                                        │
│  - API 封装                                      │
└─────────────────────────────────────────────────┘
                    ↓↑ (PyO3 FFI)
┌─────────────────────────────────────────────────┐
│              Rust 核心引擎                       │
│  - 回测引擎                                      │
│  - 订单匹配                                      │
│  - 风险管理                                      │
│  - 性能计算                                      │
│  - 数据处理                                      │
└─────────────────────────────────────────────────┘
                    ↓↑
┌─────────────────────────────────────────────────┐
│              数据源层                            │
│  - Baostock                                      │
│  - xtquant                                       │
│  - 其他数据源                                    │
└─────────────────────────────────────────────────┘
```

---

## 技术选型

### Rust 引擎部分

**核心库**：
- **PyO3**: Rust 与 Python 互操作
- **serde**: 序列化/反序列化
- **tokio**: 异步运行时
- **rayon**: 并行计算
- **ndarray**: 数值计算
- **polars**: 数据处理（可选）

**Cargo.toml**：
```toml
[package]
name = "quant-engine"
version = "0.1.0"
edition = "2021"

[lib]
name = "quant_engine"
crate-type = ["cdylib", "rlib"]

[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"
tokio = { version = "1.0", features = ["full"] }
rayon = "1.8"
ndarray = "0.15"
rust_decimal = "1.33"
chrono = "0.4"
thiserror = "1.0"
```

---

### Python 接口部分

**核心库**：
- **pyo3**: 自动绑定生成
- **pandas**: 数据处理
- **numpy**: 数值计算
- **matplotlib**: 可视化

**requirements.txt**：
```
pyo3>=0.20
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
```

---

## 核心模块设计

### 1. 数据模型（Rust）

```rust
// src/models.rs
use pyo3::prelude::*;
use serde::{Deserialize, Serialize};
use rust_decimal::Decimal;
use chrono::{DateTime, Utc};

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct Bar {
    #[pyo3(get)]
    pub timestamp: DateTime<Utc>,
    
    #[pyo3(get)]
    pub open: Decimal,
    
    #[pyo3(get)]
    pub high: Decimal,
    
    #[pyo3(get)]
    pub low: Decimal,
    
    #[pyo3(get)]
    pub close: Decimal,
    
    #[pyo3(get)]
    pub volume: i64,
    
    #[pyo3(get)]
    pub turnover: Decimal,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[pyclass]
pub struct Tick {
    #[pyo3(get)]
    pub timestamp: DateTime<Utc>,
    
    #[pyo3(get)]
    pub last_price: Decimal,
    
    #[pyo3(get)]
    pub volume: i64,
    
    #[pyo3(get)]
    pub turnover: Decimal,
    
    #[pyo3(get)]
    pub bid_prices: Vec<Decimal>,
    
    #[pyo3(get)]
    pub ask_prices: Vec<Decimal>,
    
    #[pyo3(get)]
    pub bid_volumes: Vec<i64>,
    
    #[pyo3(get)]
    pub ask_volumes: Vec<i64>,
}

#[derive(Debug, Clone)]
#[pyclass]
pub struct Order {
    #[pyo3(get)]
    pub order_id: String,
    
    #[pyo3(get)]
    pub code: String,
    
    #[pyo3(get)]
    pub direction: OrderDirection,
    
    #[pyo3(get)]
    pub offset: OrderOffset,
    
    #[pyo3(get)]
    pub price: Decimal,
    
    #[pyo3(get)]
    pub volume: i64,
    
    #[pyo3(get)]
    pub status: OrderStatus,
}

#[derive(Debug, Clone, PartialEq)]
#[pyclass]
pub enum OrderDirection {
    Buy,
    Sell,
}

#[derive(Debug, Clone, PartialEq)]
#[pyclass]
pub enum OrderOffset {
    Open,
    Close,
    CloseToday,
}

#[derive(Debug, Clone, PartialEq)]
#[pyclass]
pub enum OrderStatus {
    Pending,
    Filled,
    PartiallyFilled,
    Cancelled,
    Rejected,
}
```

---

### 2. 回测引擎（Rust）

```rust
// src/backtest.rs
use pyo3::prelude::*;
use crate::models::*;
use rayon::prelude::*;
use std::collections::HashMap;

#[pyclass]
pub struct BacktestEngine {
    #[pyo3(get)]
    pub initial_capital: Decimal,
    
    capital: Decimal,
    positions: HashMap<String, Position>,
    orders: Vec<Order>,
    trades: Vec<Trade>,
    bars: Vec<Bar>,
}

#[pyclass]
pub struct Position {
    #[pyo3(get)]
    pub code: String,
    
    #[pyo3(get)]
    pub volume: i64,
    
    #[pyo3(get)]
    pub available_volume: i64,
    
    #[pyo3(get)]
    pub avg_price: Decimal,
    
    #[pyo3(get)]
    pub unrealized_pnl: Decimal,
}

#[pymethods]
impl BacktestEngine {
    #[new]
    fn new(initial_capital: Decimal) -> Self {
        BacktestEngine {
            initial_capital,
            capital: initial_capital,
            positions: HashMap::new(),
            orders: Vec::new(),
            trades: Vec::new(),
            bars: Vec::new(),
        }
    }
    
    fn load_bars(&mut self, bars: Vec<Bar>) {
        self.bars = bars;
    }
    
    fn run(&mut self, strategy: &PyObject, py: Python) -> PyResult<BacktestResult> {
        // 回测主循环
        for bar in &self.bars {
            // 调用策略
            strategy.call_method(py, "on_bar", (bar,), None)?;
            
            // 处理订单
            self.process_orders(bar)?;
            
            // 更新持仓
            self.update_positions(bar)?;
        }
        
        // 计算绩效
        Ok(self.calculate_result())
    }
    
    fn buy(&mut self, code: String, price: Decimal, volume: i64) -> String {
        let order_id = self.generate_order_id();
        let order = Order {
            order_id: order_id.clone(),
            code,
            direction: OrderDirection::Buy,
            offset: OrderOffset::Open,
            price,
            volume,
            status: OrderStatus::Pending,
        };
        self.orders.push(order);
        order_id
    }
    
    fn sell(&mut self, code: String, price: Decimal, volume: i64) -> String {
        let order_id = self.generate_order_id();
        let order = Order {
            order_id: order_id.clone(),
            code,
            direction: OrderDirection::Sell,
            offset: OrderOffset::Close,
            price,
            volume,
            status: OrderStatus::Pending,
        };
        self.orders.push(order);
        order_id
    }
}

#[derive(Debug)]
#[pyclass]
pub struct BacktestResult {
    #[pyo3(get)]
    pub total_return: Decimal,
    
    #[pyo3(get)]
    pub annual_return: Decimal,
    
    #[pyo3(get)]
    pub sharpe_ratio: Decimal,
    
    #[pyo3(get)]
    pub max_drawdown: Decimal,
    
    #[pyo3(get)]
    pub win_rate: Decimal,
    
    #[pyo3(get)]
    pub total_trades: i32,
}
```

---

### 3. 策略接口（Python）

```python
# quant/strategy.py
from quant_engine import BacktestEngine, Bar

class Strategy:
    """策略基类"""
    
    def __init__(self, engine: BacktestEngine):
        self.engine = engine
        self.positions = {}
    
    def on_bar(self, bar: Bar):
        """K 线数据回调"""
        pass
    
    def on_tick(self, tick):
        """Tick 数据回调"""
        pass
    
    def buy(self, code: str, price: float, volume: int):
        """买入"""
        return self.engine.buy(code, price, volume)
    
    def sell(self, code: str, price: float, volume: int):
        """卖出"""
        return self.engine.sell(code, price, volume)


# 示例策略
class MovingAverageStrategy(Strategy):
    """双均线策略"""
    
    def __init__(self, engine, short_period=5, long_period=20):
        super().__init__(engine)
        self.short_period = short_period
        self.long_period = long_period
        self.prices = []
    
    def on_bar(self, bar):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.long_period:
            return
        
        # 计算均线
        short_ma = sum(self.prices[-self.short_period:]) / self.short_period
        long_ma = sum(self.prices[-self.long_period:]) / self.long_period
        
        # 金叉买入
        if short_ma > long_ma and not self.positions.get(bar.code):
            self.buy(bar.code, bar.close, 100)
        
        # 死叉卖出
        elif short_ma < long_ma and self.positions.get(bar.code):
            self.sell(bar.code, bar.close, 100)
```

---

### 4. 数据接口（Python）

```python
# quant/data.py
import pandas as pd
from app.services import get_stock_data

class DataLoader:
    """数据加载器"""
    
    def __init__(self):
        self.data_service = get_stock_data()
    
    def load_bars(self, code: str, start_date: str, end_date: str) -> list:
        """加载 K 线数据"""
        # 从数据服务获取
        df = self.data_service.get_kline(code, start_date, end_date)
        
        # 转换为 Rust Bar 对象
        bars = []
        for _, row in df.iterrows():
            bar = Bar(
                timestamp=row['datetime'],
                open=Decimal(str(row['open'])),
                high=Decimal(str(row['high'])),
                low=Decimal(str(row['low'])),
                close=Decimal(str(row['close'])),
                volume=int(row['volume']),
                turnover=Decimal(str(row.get('turnover', 0)))
            )
            bars.append(bar)
        
        return bars
    
    def load_portfolio_bars(
        self, 
        codes: list, 
        start_date: str, 
        end_date: str
    ) -> dict:
        """加载组合数据"""
        from concurrent.futures import ThreadPoolExecutor
        
        def load_single_code(code):
            return code, self.load_bars(code, start_date, end_date)
        
        with ThreadPoolExecutor() as executor:
            results = list(executor.map(load_single_code, codes))
        
        return dict(results)
```

---

### 5. 绩效分析（Rust）

```rust
// src/performance.rs
use crate::models::*;
use ndarray::Array1;

pub struct PerformanceAnalyzer;

impl PerformanceAnalyzer {
    pub fn calculate_returns(trades: &[Trade]) -> Vec<f64> {
        trades.iter()
            .map(|t| t.pnl.to_f64().unwrap())
            .collect()
    }
    
    pub fn total_return(trades: &[Trade]) -> f64 {
        Self::calculate_returns(trades).iter().sum()
    }
    
    pub fn sharpe_ratio(returns: &[f64], risk_free_rate: f64) -> f64 {
        if returns.is_empty() {
            return 0.0;
        }
        
        let mean_return = returns.iter().sum::<f64>() / returns.len() as f64;
        let variance = returns.iter()
            .map(|r| (r - mean_return).powi(2))
            .sum::<f64>() / returns.len() as f64;
        let std_dev = variance.sqrt();
        
        if std_dev == 0.0 {
            return 0.0;
        }
        
        (mean_return - risk_free_rate) / std_dev * (252.0_f64).sqrt()
    }
    
    pub fn max_drawdown(equity_curve: &[f64]) -> f64 {
        let mut max_drawdown = 0.0;
        let mut peak = equity_curve[0];
        
        for &value in equity_curve {
            if value > peak {
                peak = value;
            }
            let drawdown = (peak - value) / peak;
            if drawdown > max_drawdown {
                max_drawdown = drawdown;
            }
        }
        
        max_drawdown
    }
    
    pub fn win_rate(trades: &[Trade]) -> f64 {
        if trades.is_empty() {
            return 0.0;
        }
        
        let winning_trades = trades.iter()
            .filter(|t| t.pnl > rust_decimal::Decimal::ZERO)
            .count();
        
        winning_trades as f64 / trades.len() as f64
    }
}
```

---

## 项目结构

```
quant-framework/
├── rust-engine/              # Rust 引擎
│   ├── Cargo.toml
│   ├── src/
│   │   ├── lib.rs           # Python 模块入口
│   │   ├── models.rs        # 数据模型
│   │   ├── backtest.rs      # 回测引擎
│   │   ├── performance.rs   # 绩效分析
│   │   ├── risk.rs          # 风险管理
│   │   └── utils.rs         # 工具函数
│   └── tests/
│       └── test_engine.rs
│
├── python-api/              # Python 接口
│   ├── setup.py
│   ├── quant/
│   │   ├── __init__.py
│   │   ├── engine.py        # 引擎封装
│   │   ├── strategy.py      # 策略基类
│   │   ├── data.py          # 数据接口
│   │   ├── analyzer.py      # 分析工具
│   │   └── examples/        # 示例策略
│   │       ├── ma_strategy.py
│   │       └── momentum_strategy.py
│   └── tests/
│       └── test_api.py
│
├── docs/                    # 文档
│   ├── installation.md
│   ├── quickstart.md
│   └── api_reference.md
│
└── examples/                # 示例
    ├── simple_backtest.py
    └── portfolio_optimization.py
```

---

## 实现步骤

### 阶段 1：基础架构（2-3 周）

1. **Rust 环境搭建**
   - 安装 Rust
   - 配置 PyO3
   - 创建项目结构

2. **核心数据模型**
   - Bar、Tick、Order
   - Position、Trade
   - 枚举类型

3. **Python 绑定**
   - PyO3 配置
   - 自动绑定生成
   - 类型转换

---

### 阶段 2：回测引擎（3-4 周）

1. **回测核心**
   - 事件循环
   - 订单处理
   - 持仓管理

2. **订单匹配**
   - 限价单
   - 市价单
   - 成交逻辑

3. **绩效计算**
   - 收益率
   - 夏普比率
   - 最大回撤

---

### 阶段 3：策略框架（2-3 周）

1. **策略基类**
   - 生命周期方法
   - 交易接口
   - 数据访问

2. **技术指标**
   - 移动平均
   - MACD
   - RSI

3. **示例策略**
   - 双均线策略
   - 动量策略
   - 均值回归

---

### 阶段 4：优化完善（2-3 周）

1. **性能优化**
   - 并行计算
   - 内存优化
   - 缓存策略

2. **风险管理**
   - 仓位限制
   - 止损止盈
   - 风控规则

3. **文档示例**
   - 使用文档
   - API 文档
   - 示例代码

---

## 性能对比

### 回测速度对比（预估）

| 框架 | 语言 | 1000 只股票×5 年 | 相对速度 |
|------|------|----------------|---------|
| **AKQuant** | Python | ~30 秒 | 1x |
| **Backtrader** | Python | ~20 秒 | 1.5x |
| **自研框架** | Rust+Python | ~2 秒 | **15x** |

### 内存占用对比（预估）

| 框架 | 内存占用 | 相对占用 |
|------|---------|---------|
| **AKQuant** | ~500MB | 1x |
| **Backtrader** | ~400MB | 0.8x |
| **自研框架** | ~100MB | **0.2x** |

---

## 优势分析

### ✅ 技术优势

1. **性能卓越**
   - Rust 编译型语言，速度快
   - 并行计算能力强
   - 内存占用低

2. **类型安全**
   - 编译时检查
   - 减少运行时错误
   - 代码质量高

3. **Python 生态**
   - 保留 Python 易用性
   - 可使用 pandas、numpy
   - 丰富的可视化库

4. **可扩展性**
   - 模块化设计
   - 易于添加新功能
   - 支持自定义数据源

---

### ✅ 业务优势

1. **自主可控**
   - 完全自研
   - 不依赖第三方
   - 可定制性强

2. **数据源灵活**
   - 支持 Baostock
   - 支持 xtquant
   - 支持自定义

3. **学习价值**
   - 掌握 Rust
   - 理解量化框架
   - 提升技术水平

---

### ⚠️ 挑战

1. **开发周期长**
   - 预计 2-3 个月
   - 需要持续维护

2. **技术门槛高**
   - 需要 Rust 技能
   - FFI 编程复杂

3. **生态建设**
   - 需要编写文档
   - 需要示例代码
   - 需要社区支持

---

## 与现有框架对比

| 特性 | AKQuant | Backtrader | 自研框架 |
|------|---------|------------|---------|
| **性能** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **易用性** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **灵活性** | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **学习曲线** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ |
| **社区支持** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| **数据源** | akshare | 自定义 | 自定义 |
| **实盘支持** | ✅ | ❌ | 待开发 |
| **开发语言** | Python | Python | Rust+Python |

---

## 最终建议

### 推荐方案：分阶段实施

#### 阶段 1：原型验证（2 周）
- ✅ 实现基础数据模型
- ✅ 实现简单回测引擎
- ✅ 验证 PyO3 绑定
- ✅ 性能测试

**目标**：验证技术可行性

---

#### 阶段 2：核心功能（4 周）
- ✅ 完善回测引擎
- ✅ 实现绩效分析
- ✅ 策略框架
- ✅ 基础文档

**目标**：可用的回测工具

---

#### 阶段 3：功能完善（4 周）
- ✅ 风险管理
- ✅ 多策略支持
- ✅ 并行回测
- ✅ 完整文档

**目标**：生产级工具

---

#### 阶段 4：生态建设（持续）
- ✅ 示例策略库
- ✅ 社区建设
- ✅ 性能优化
- ✅ 功能扩展

**目标**：成为主流框架

---

### 决策建议

**✅ 推荐自研，如果**：
- 有 Rust 开发经验
- 对性能要求高
- 长期维护意愿
- 学习新技术热情

**❌ 不推荐自研，如果**：
- 项目时间紧张
- 缺乏 Rust 经验
- 只需简单回测
- 短期使用

---

### 替代方案

**方案 1：使用现有框架**
- Backtrader（回测）
- Vn.py（实盘）
- 快速上线

**方案 2：混合方案**
- 核心模块用 Rust
- 策略层用 Python
- 平衡性能和开发效率

---

## 总结

### 技术可行性

**✅ 完全可行**
- PyO3 成熟稳定
- Rust 性能优异
- Python 生态丰富

### 商业价值

**⭐⭐⭐⭐**
- 自主可控
- 性能优势
- 差异化竞争

### 学习价值

**⭐⭐⭐⭐⭐**
- 掌握 Rust
- 理解量化框架
- 提升技术水平

### 推荐指数

**⭐⭐⭐⭐**（4/5）

**建议**：
- 如果时间和资源允许，强烈推荐自研
- 从简单原型开始，逐步完善
- 保持与现有数据源的兼容性
- 注重文档和示例建设

---

## 快速开始

### 1. 创建 Rust 项目

```bash
cargo new --lib quant-engine
cd quant-engine
```

### 2. 添加依赖

```toml
[dependencies]
pyo3 = { version = "0.20", features = ["extension-module"] }
```

### 3. 编写第一个 Rust 函数

```rust
// src/lib.rs
use pyo3::prelude::*;

#[pyfunction]
fn hello_quant() -> &'static str {
    "Hello from Rust Quant Engine!"
}

#[pymodule]
fn quant_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(hello_quant, m)?)?;
    Ok(())
}
```

### 4. Python 调用

```python
import quant_engine

print(quant_engine.hello_quant())
# 输出：Hello from Rust Quant Engine!
```

---

**开始你的 Rust+Python 量化框架之旅吧！** 🚀
