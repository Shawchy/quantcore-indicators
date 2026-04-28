//! QuantCore Rust Engine - 高性能量化交易引擎
//!
//! 模块结构：
//! - core: 核心数据结构（Bar, Order, Trade, Position, Portfolio）
//! - engine: 回测引擎和撮合引擎
//! - data: 数据加载和缓存
//! - strategy: 策略框架
//! - performance: 绩效分析
//! - risk: 风险管理
//! - utils: 工具函数

use pyo3::prelude::*;

pub mod core;
pub mod data;
pub mod engine;
pub mod performance;
pub mod risk;
pub mod strategy;
pub mod utils;

// ==================== Python 模块导出 ====================

/// Python 模块入口
#[pymodule]
fn quantcore_engine(m: &Bound<'_, PyModule>) -> PyResult<()> {
    use core::{Bar, Order, OrderSide, OrderStatus, OrderType, Portfolio, Position, Tick, Trade};
    use engine::{BacktestConfig, BacktestEngine, BacktestResult};
    use performance::PerformanceAnalyzer;

    // 数据模型
    m.add_class::<Bar>()?;
    m.add_class::<Tick>()?;
    m.add_class::<Order>()?;
    m.add_class::<Trade>()?;
    m.add_class::<Position>()?;
    m.add_class::<Portfolio>()?;

    // 回测引擎
    m.add_class::<BacktestConfig>()?;
    m.add_class::<BacktestResult>()?;
    m.add_class::<BacktestEngine>()?;

    // 绩效分析
    m.add_class::<PerformanceAnalyzer>()?;

    // 枚举
    m.add_class::<OrderSide>()?;
    m.add_class::<OrderType>()?;
    m.add_class::<OrderStatus>()?;

    // 版本信息
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(hello_quant, m)?)?;

    Ok(())
}

// ==================== 辅助函数 ====================

/// QuantCore Rust 引擎版本
#[pyfunction]
fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// 打印引擎信息
#[pyfunction]
fn hello_quant() -> &'static str {
    "Hello from QuantCore Rust Engine!"
}

// ==================== 测试 ====================

#[cfg(test)]
mod tests {
    use super::*;
    use core::Bar;
    use core::Portfolio;
    use core::Position;

    #[test]
    fn test_version() {
        assert_eq!(version(), "0.1.0");
    }

    #[test]
    fn test_bar() {
        let bar = Bar::new(
            "2024-01-01 10:00:00".to_string(),
            "SH.600000".to_string(),
            10.0,
            10.5,
            9.8,
            10.2,
            1000000,
            10200000.0,
        );

        assert_eq!(bar.symbol, "SH.600000");
        assert_eq!(bar.close, 10.2);
        assert!((bar.average_price() - 10.166666) < 0.001);
    }

    #[test]
    fn test_portfolio() {
        let mut portfolio = Portfolio::new(1000000.0);

        let position = Position::new(
            "SH.600000".to_string(),
            "long".to_string(),
            1000,
            10.0,
            10.2,
        );

        portfolio.add_position(position);

        assert!(portfolio.has_position("SH.600000"));
        assert!((portfolio.market_value() - 10200.0) < 0.01);
    }
}

