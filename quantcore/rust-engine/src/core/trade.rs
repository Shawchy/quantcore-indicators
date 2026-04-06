//! 成交模块

use chrono::{DateTime, Utc};
use pyo3::prelude::*;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};

/// 成交记录
#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Trade {
    /// 成交 ID
    #[pyo3(get)]
    pub trade_id: String,

    /// 订单 ID
    #[pyo3(get)]
    pub order_id: String,

    /// 策略 ID
    #[pyo3(get)]
    pub strategy_id: String,

    /// 证券代码
    #[pyo3(get)]
    pub symbol: String,

    /// 成交方向
    #[pyo3(get)]
    pub side: String,

    /// 成交价格
    #[pyo3(get)]
    pub price: Decimal,

    /// 成交数量
    #[pyo3(get)]
    pub quantity: i64,

    /// 成交金额
    #[pyo3(get)]
    pub turnover: Decimal,

    /// 手续费
    #[pyo3(get)]
    pub commission: Decimal,

    /// 印花税
    #[pyo3(get)]
    pub tax: Decimal,

    /// 成交时间
    #[pyo3(get)]
    pub timestamp: DateTime<Utc>,
}

#[pymethods]
impl Trade {
    #[new]
    #[pyo3(signature = (trade_id, order_id, strategy_id, symbol, side, price, quantity, commission, tax))]
    fn new(
        trade_id: String,
        order_id: String,
        strategy_id: String,
        symbol: String,
        side: String,
        price: f64,
        quantity: i64,
        commission: f64,
        tax: f64,
    ) -> Self {
        let turnover =
            Decimal::from_f64_retain(price as f64 * quantity as f64).unwrap_or(Decimal::ZERO);
        Self {
            trade_id,
            order_id,
            strategy_id,
            symbol,
            side,
            price: Decimal::from_f64_retain(price).unwrap_or(Decimal::ZERO),
            quantity,
            turnover,
            commission: Decimal::from_f64_retain(commission).unwrap_or(Decimal::ZERO),
            tax: Decimal::from_f64_retain(tax).unwrap_or(Decimal::ZERO),
            timestamp: Utc::now(),
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "Trade(id={}, symbol={}, price={}, qty={}, time={})",
            self.trade_id,
            self.symbol,
            self.price,
            self.quantity,
            self.timestamp.format("%Y-%m-%d %H:%M:%S")
        )
    }

    /// 获取净成交金额（扣除费用）
    fn net_amount(&self) -> Decimal {
        self.turnover - self.commission - self.tax
    }
}
