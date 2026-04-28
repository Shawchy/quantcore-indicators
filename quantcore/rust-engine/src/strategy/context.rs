//! 策略上下文

use crate::core::{Order, OrderSide, OrderStatus, OrderType, Portfolio, Position};
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

    /// 下一个订单 ID 计数器
    order_counter: u64,

    /// 待处理订单列表
    pending_orders: Vec<Order>,
}

#[pymethods]
impl StrategyContext {
    /// 创建策略上下文
    #[new]
    #[pyo3(signature = (portfolio, current_time))]
    fn new(portfolio: Portfolio, current_time: String) -> Self {
        Self {
            portfolio,
            current_time,
            order_counter: 1,
            pending_orders: Vec::new(),
        }
    }

    /// 买入
    fn buy(&mut self, symbol: &str, price: f64, volume: i64) -> PyResult<Order> {
        if volume <= 0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "买入数量必须大于 0",
            ));
        }

        let order_id = format!("ORD-{}", self.order_counter);
        self.order_counter += 1;

        let order = Order::new(
            order_id,
            "strategy_1".to_string(),
            symbol.to_string(),
            OrderSide::Buy,
            OrderType::Limit,
            price,
            volume,
        );

        self.pending_orders.push(order.clone());

        Ok(order)
    }

    /// 卖出
    fn sell(&mut self, symbol: &str, price: f64, volume: i64) -> PyResult<Order> {
        if volume <= 0 {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "卖出数量必须大于 0",
            ));
        }

        let order_id = format!("ORD-{}", self.order_counter);
        self.order_counter += 1;

        let order = Order::new(
            order_id,
            "strategy_1".to_string(),
            symbol.to_string(),
            OrderSide::Sell,
            OrderType::Limit,
            price,
            volume,
        );

        self.pending_orders.push(order.clone());

        Ok(order)
    }

    /// 获取持仓
    fn get_position(&self, symbol: &str) -> Option<&Position> {
        self.portfolio.get_position(symbol)
    }

    /// 获取可用资金
    fn available_cash(&self) -> Decimal {
        self.portfolio.available_cash()
    }

    /// 获取待处理订单
    fn get_pending_orders(&self) -> &[Order] {
        &self.pending_orders
    }

    /// 清除已完成的订单
    fn clear_filled_orders(&mut self) {
        self.pending_orders.retain(|o| o.is_active());
    }
}
