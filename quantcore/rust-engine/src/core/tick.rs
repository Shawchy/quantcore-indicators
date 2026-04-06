//! Tick 数据模块

use chrono::{DateTime, Utc};
use pyo3::prelude::*;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};

/// Tick 数据
#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Tick {
    /// 时间戳
    #[pyo3(get)]
    pub timestamp: DateTime<Utc>,

    /// 证券代码
    #[pyo3(get)]
    pub symbol: String,

    /// 最新价
    #[pyo3(get)]
    pub last_price: Decimal,

    /// 开盘价
    #[pyo3(get)]
    pub open_price: Decimal,

    /// 最高价
    #[pyo3(get)]
    pub high_price: Decimal,

    /// 最低价
    #[pyo3(get)]
    pub low_price: Decimal,

    /// 昨收价
    #[pyo3(get)]
    pub prev_close: Decimal,

    /// 买一价
    #[pyo3(get)]
    pub bid_price_1: Decimal,

    /// 买一量
    #[pyo3(get)]
    pub bid_volume_1: i64,

    /// 卖一价
    #[pyo3(get)]
    pub ask_price_1: Decimal,

    /// 卖一量
    #[pyo3(get)]
    pub ask_volume_1: i64,

    /// 成交量
    #[pyo3(get)]
    pub volume: i64,

    /// 成交额
    #[pyo3(get)]
    pub turnover: Decimal,

    /// 持仓量（期货）
    #[pyo3(get)]
    pub open_interest: Option<i64>,
}

#[pymethods]
impl Tick {
    #[new]
    #[pyo3(signature = (timestamp, symbol, last_price, open_price, high_price, low_price, prev_close, bid_price_1, bid_volume_1, ask_price_1, ask_volume_1, volume, turnover, open_interest=None))]
    fn new(
        timestamp: DateTime<Utc>,
        symbol: String,
        last_price: f64,
        open_price: f64,
        high_price: f64,
        low_price: f64,
        prev_close: f64,
        bid_price_1: f64,
        bid_volume_1: i64,
        ask_price_1: f64,
        ask_volume_1: i64,
        volume: i64,
        turnover: f64,
        open_interest: Option<i64>,
    ) -> Self {
        Self {
            timestamp,
            symbol,
            last_price: Decimal::from_f64_retain(last_price).unwrap_or(Decimal::ZERO),
            open_price: Decimal::from_f64_retain(open_price).unwrap_or(Decimal::ZERO),
            high_price: Decimal::from_f64_retain(high_price).unwrap_or(Decimal::ZERO),
            low_price: Decimal::from_f64_retain(low_price).unwrap_or(Decimal::ZERO),
            prev_close: Decimal::from_f64_retain(prev_close).unwrap_or(Decimal::ZERO),
            bid_price_1: Decimal::from_f64_retain(bid_price_1).unwrap_or(Decimal::ZERO),
            bid_volume_1,
            ask_price_1: Decimal::from_f64_retain(ask_price_1).unwrap_or(Decimal::ZERO),
            ask_volume_1,
            volume,
            turnover: Decimal::from_f64_retain(turnover).unwrap_or(Decimal::ZERO),
            open_interest,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "Tick(symbol={}, price={}, volume={}, time={})",
            self.symbol,
            self.last_price,
            self.volume,
            self.timestamp.format("%H:%M:%S.%f")
        )
    }
}
