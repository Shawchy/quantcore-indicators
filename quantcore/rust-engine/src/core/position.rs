//! 持仓模块

use pyo3::prelude::*;
use rust_decimal::Decimal;
use serde::{Deserialize, Serialize};

/// 持仓
#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Position {
    /// 证券代码
    #[pyo3(get)]
    pub symbol: String,

    /// 持仓方向（多头/空头）
    #[pyo3(get)]
    pub side: String,

    /// 持仓数量
    #[pyo3(get)]
    pub quantity: i64,

    /// 可用数量（T+1 限制）
    #[pyo3(get)]
    pub available_quantity: i64,

    /// 持仓成本价
    #[pyo3(get)]
    pub cost_price: Decimal,

    /// 当前市价
    #[pyo3(get)]
    pub current_price: Decimal,

    /// 持仓市值
    #[pyo3(get)]
    pub market_value: Decimal,

    /// 持仓成本
    #[pyo3(get)]
    pub cost_value: Decimal,

    /// 浮动盈亏
    #[pyo3(get)]
    pub unrealized_pnl: Decimal,

    /// 浮动盈亏比例
    #[pyo3(get)]
    pub unrealized_pnl_percent: Decimal,

    /// 昨日持仓
    #[pyo3(get)]
    pub yesterday_quantity: i64,

    /// 今日买入
    #[pyo3(get)]
    pub today_long: i64,

    /// 今日卖出
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
        let cost_price = Decimal::from_f64_retain(cost_price).unwrap_or(Decimal::ZERO);
        let current_price = Decimal::from_f64_retain(current_price).unwrap_or(Decimal::ZERO);
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

    /// 更新当前价格
    fn update_price(&mut self, price: f64) {
        let price = Decimal::from_f64_retain(price).unwrap_or(self.current_price);
        self.current_price = price;
        self.market_value = price * Decimal::from(self.quantity);
        self.unrealized_pnl = self.market_value - self.cost_value;
        self.unrealized_pnl_percent = if self.cost_value == Decimal::ZERO {
            Decimal::ZERO
        } else {
            self.unrealized_pnl / self.cost_value
        };
    }

    /// 是否可卖出指定数量
    fn can_sell(&self, quantity: i64) -> bool {
        self.available_quantity >= quantity
    }
}
