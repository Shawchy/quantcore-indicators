//! 绩效分析模块

pub mod analyzer;
pub mod math;
pub mod metrics;
pub mod reporter;

pub use analyzer::PerformanceAnalyzer;
pub use math::{calculate_annual_return, calculate_volatility, calculate_sharpe_ratio, calculate_max_drawdown};
pub use metrics::PerformanceMetrics;
