//! K 线数据模块

use chrono::{DateTime, Utc};
use pyo3::prelude::*;
use rust_decimal::Decimal;
use rust_decimal::prelude::*;
use serde::{Deserialize, Serialize};

fn safe_decimal(value: f64, field_name: &str) -> Decimal {
    if value.is_nan() || value.is_infinite() {
        log::error!("金融数据 {} 包含无效值: {}，将使用 0", field_name, value);
        Decimal::ZERO
    } else {
        Decimal::from_f64_retain(value).unwrap_or_else(|| {
            log::error!("金融数据 {} 转换失败: {}", field_name, value);
            Decimal::ZERO
        })
    }
}

/// K 线数据
#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Bar {
    /// 时间戳
    #[pyo3(get)]
    pub timestamp: DateTime<Utc>,

    /// 开盘价
    #[pyo3(get)]
    pub open: Decimal,

    /// 最高价
    #[pyo3(get)]
    pub high: Decimal,

    /// 最低价
    #[pyo3(get)]
    pub low: Decimal,

    /// 收盘价
    #[pyo3(get)]
    pub close: Decimal,

    /// 成交量
    #[pyo3(get)]
    pub volume: i64,

    /// 成交额（可选，期货/期权可能没有）
    #[pyo3(get)]
    pub turnover: Option<Decimal>,

    /// 持仓量（期货专用）
    #[pyo3(get)]
    pub open_interest: Option<i64>,
}

#[pymethods]
impl Bar {
    /// 创建新的 Bar
    #[new]
    #[pyo3(signature = (timestamp, open, high, low, close, volume, turnover=None, open_interest=None))]
    fn new(
        timestamp: DateTime<Utc>,
        open: f64,
        high: f64,
        low: f64,
        close: f64,
        volume: i64,
        turnover: Option<f64>,
        open_interest: Option<i64>,
    ) -> Self {
        Self {
            timestamp,
            open: safe_decimal(open, "open"),
            high: safe_decimal(high, "high"),
            low: safe_decimal(low, "low"),
            close: safe_decimal(close, "close"),
            volume,
            turnover: turnover.and_then(|v| {
                if v.is_nan() || v.is_infinite() {
                    log::error!("金融数据 turnover 包含无效值: {}", v);
                    None
                } else {
                    Decimal::from_f64_retain(v)
                }
            }),
            open_interest,
        }
    }

    /// 字符串表示
    fn __repr__(&self) -> String {
        format!(
            "Bar(timestamp={}, open={}, high={}, low={}, close={}, volume={})",
            self.timestamp.format("%Y-%m-%d %H:%M:%S"),
            self.open,
            self.high,
            self.low,
            self.close,
            self.volume
        )
    }

    /// 获取平均价格
    fn average_price(&self) -> Decimal {
        (self.high + self.low + self.close) / Decimal::from(3)
    }

    /// 获取价格范围
    fn price_range(&self) -> Decimal {
        self.high - self.low
    }

    /// 获取涨跌幅
    fn price_change_percent(&self) -> Decimal {
        if self.open == Decimal::ZERO {
            Decimal::ZERO
        } else {
            (self.close - self.open) / self.open
        }
    }
}
