//! 仓位限制

use pyo3::prelude::*;
use rust_decimal::Decimal;

/// 仓位限制
#[pyclass]
pub struct PositionLimit {
    /// 证券代码
    #[pyo3(get)]
    pub symbol: String,

    /// 最大仓位比例
    #[pyo3(get)]
    pub max_percent: f64,

    /// 最大数量
    #[pyo3(get)]
    pub max_volume: i64,
}

#[pymethods]
impl PositionLimit {
    #[new]
    #[pyo3(signature = (symbol, max_percent, max_volume))]
    fn new(symbol: String, max_percent: f64, max_volume: i64) -> Self {
        Self {
            symbol,
            max_percent,
            max_volume,
        }
    }
}
