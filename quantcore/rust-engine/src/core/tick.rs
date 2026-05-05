//! Tick 数据模块

use chrono::{DateTime, Utc};
use pyo3::prelude::*;
use rust_decimal::Decimal;
use rust_decimal::prelude::*;
use serde::{Deserialize, Serialize};

fn safe_tick_price(value: f64, field: &str) -> Decimal {
    if value.is_nan() || value.is_infinite() {
        log::error!("Tick 数据 {} 包含无效值: {}", field, value);
        Decimal::ZERO
    } else {
        Decimal::from_f64_retain(value).unwrap_or_else(|| {
            log::error!("Tick 数据 {} 转换失败: {}", field, value);
            Decimal::ZERO
        })
    }
}

#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Tick {
    #[pyo3(get)]
    pub timestamp: DateTime<Utc>,
    #[pyo3(get)]
    pub symbol: String,
    #[pyo3(get)]
    pub last_price: Decimal,
    #[pyo3(get)]
    pub open_price: Decimal,
    #[pyo3(get)]
    pub high_price: Decimal,
    #[pyo3(get)]
    pub low_price: Decimal,
    #[pyo3(get)]
    pub prev_close: Decimal,
    #[pyo3(get)]
    pub bid_price_1: Decimal,
    #[pyo3(get)]
    pub bid_volume_1: i64,
    #[pyo3(get)]
    pub ask_price_1: Decimal,
    #[pyo3(get)]
    pub ask_volume_1: i64,
    #[pyo3(get)]
    pub volume: i64,
    #[pyo3(get)]
    pub turnover: Decimal,
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
            last_price: safe_tick_price(last_price, "last_price"),
            open_price: safe_tick_price(open_price, "open_price"),
            high_price: safe_tick_price(high_price, "high_price"),
            low_price: safe_tick_price(low_price, "low_price"),
            prev_close: safe_tick_price(prev_close, "prev_close"),
            bid_price_1: safe_tick_price(bid_price_1, "bid_price_1"),
            bid_volume_1,
            ask_price_1: safe_tick_price(ask_price_1, "ask_price_1"),
            ask_volume_1,
            volume,
            turnover: safe_tick_price(turnover, "turnover"),
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
