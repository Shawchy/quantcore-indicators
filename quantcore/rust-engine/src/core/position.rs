//! 持仓模块

use pyo3::prelude::*;
use rust_decimal::Decimal;
use rust_decimal::prelude::*;
use serde::{Deserialize, Serialize};

fn safe_price(value: f64, field: &str) -> Decimal {
    if value.is_nan() || value.is_infinite() {
        log::error!("持仓数据 {} 包含无效值: {}", field, value);
        Decimal::ZERO
    } else {
        Decimal::from_f64_retain(value).unwrap_or_else(|| {
            log::error!("持仓数据 {} 转换失败: {}", field, value);
            Decimal::ZERO
        })
    }
}

#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Position {
    #[pyo3(get)]
    pub symbol: String,
    #[pyo3(get)]
    pub side: String,
    #[pyo3(get)]
    pub quantity: i64,
    #[pyo3(get)]
    pub available_quantity: i64,
    #[pyo3(get)]
    pub cost_price: Decimal,
    #[pyo3(get)]
    pub current_price: Decimal,
    #[pyo3(get)]
    pub market_value: Decimal,
    #[pyo3(get)]
    pub cost_value: Decimal,
    #[pyo3(get)]
    pub unrealized_pnl: Decimal,
    #[pyo3(get)]
    pub unrealized_pnl_percent: Decimal,
    #[pyo3(get)]
    pub yesterday_quantity: i64,
    #[pyo3(get)]
    pub today_long: i64,
    #[pyo3(get)]
    pub today_short: i64,
}

#[pymethods]
impl Position {
    #[new]
    #[pyo3(signature = (symbol, side, quantity, cost_price, current_price))]
    fn new(
        symbol: String,
        side: String,
        quantity: i64,
        cost_price: f64,
        current_price: f64,
    ) -> Self {
        let cost_price = safe_price(cost_price, "cost_price");
        let current_price = safe_price(current_price, "current_price");
        let cost_value = cost_price * Decimal::from(quantity);
        let market_value = current_price * Decimal::from(quantity);
        let unrealized_pnl = market_value - cost_value;
        let unrealized_pnl_percent = if cost_value == Decimal::ZERO {
            Decimal::ZERO
        } else {
            unrealized_pnl / cost_value
        };

        Self {
            symbol,
            side,
            quantity,
            available_quantity: quantity,
            cost_price,
            current_price,
            market_value,
            cost_value,
            unrealized_pnl,
            unrealized_pnl_percent,
            yesterday_quantity: quantity,
            today_long: 0,
            today_short: 0,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "Position(symbol={}, qty={}, cost={}, current={}, pnl={:.2}%)",
            self.symbol,
            self.quantity,
            self.cost_price,
            self.current_price,
            self.unrealized_pnl_percent * Decimal::from(100)
        )
    }

    fn update_price(&mut self, price: f64) {
        let new_price = if price.is_nan() || price.is_infinite() {
            log::error!("持仓 {} 更新价格无效: {}", self.symbol, price);
            return;
        } else {
            Decimal::from_f64_retain(price).unwrap_or(self.current_price)
        };
        self.current_price = new_price;
        self.market_value = new_price * Decimal::from(self.quantity);
        self.unrealized_pnl = self.market_value - self.cost_value;
        self.unrealized_pnl_percent = if self.cost_value == Decimal::ZERO {
            Decimal::ZERO
        } else {
            self.unrealized_pnl / self.cost_value
        };
    }

    fn can_sell(&self, quantity: i64) -> bool {
        self.available_quantity >= quantity
    }
}
