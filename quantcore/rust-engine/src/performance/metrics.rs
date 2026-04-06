//! 绩效指标

use pyo3::prelude::*;

/// 绩效指标
#[pyclass]
pub struct PerformanceMetrics {
    /// 总收益
    #[pyo3(get)]
    pub total_return: f64,

    /// 年化收益
    #[pyo3(get)]
    pub annual_return: f64,

    /// 基准收益
    #[pyo3(get)]
    pub benchmark_return: f64,

    /// 超额收益
    #[pyo3(get)]
    pub excess_return: f64,

    /// 波动率
    #[pyo3(get)]
    pub volatility: f64,

    /// 夏普比率
    #[pyo3(get)]
    pub sharpe_ratio: f64,

    /// 最大回撤
    #[pyo3(get)]
    pub max_drawdown: f64,

    /// 索提诺比率
    #[pyo3(get)]
    pub sortino_ratio: f64,

    /// 卡尔玛比率
    #[pyo3(get)]
    pub calmar_ratio: f64,

    /// 胜率
    #[pyo3(get)]
    pub win_rate: f64,

    /// 盈亏比
    #[pyo3(get)]
    pub profit_loss_ratio: f64,

    /// 交易次数
    #[pyo3(get)]
    pub total_trades: i32,
}

#[pymethods]
impl PerformanceMetrics {
    #[new]
    fn new() -> Self {
        Self {
            total_return: 0.0,
            annual_return: 0.0,
            benchmark_return: 0.0,
            excess_return: 0.0,
            volatility: 0.0,
            sharpe_ratio: 0.0,
            max_drawdown: 0.0,
            sortino_ratio: 0.0,
            calmar_ratio: 0.0,
            win_rate: 0.0,
            profit_loss_ratio: 0.0,
            total_trades: 0,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "PerformanceMetrics(total_return={:.2}%, sharpe={:.2f}, max_dd={:.2}%)",
            self.total_return * 100.0,
            self.sharpe_ratio,
            self.max_drawdown * 100.0
        )
    }
}

impl Default for PerformanceMetrics {
    fn default() -> Self {
        Self::new()
    }
}
