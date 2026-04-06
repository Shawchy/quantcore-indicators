//! 策略上下文

use crate::core::{Order, Portfolio, Position};
use pyo3::prelude::*;
use rust_decimal::Decimal;

/// 策略上下文
#[pyclass]
pub struct StrategyContext {
    /// 投资组合
    #[pyo3(get)]
    pub portfolio: Portfolio,

    /// 当前时间
    #[pyo3(get)]
    pub current_time: String,
}

#[pymethods]
impl StrategyContext {
    /// 买入
    fn buy(&mut self, _symbol: &str, _price: f64, _volume: i64) -> PyResult<Order> {
        // TODO: 实现买入逻辑
        todo!()
    }

    /// 卖出
    fn sell(&mut self, _symbol: &str, _price: f64, _volume: i64) -> PyResult<Order> {
        // TODO: 实现卖出逻辑
        todo!()
    }

    /// 获取持仓
    fn get_position(&self, symbol: &str) -> Option<&Position> {
        self.portfolio.get_position(symbol)
    }

    /// 获取可用资金
    fn available_cash(&self) -> Decimal {
        self.portfolio.available_cash()
    }
}
