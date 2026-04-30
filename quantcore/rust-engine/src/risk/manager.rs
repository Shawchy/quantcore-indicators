//! 风险管理器

use super::limits::PositionLimit;
use crate::core::{Order, OrderSide, Portfolio};
use pyo3::prelude::*;
use rust_decimal::Decimal;

/// 风险管理器
#[pyclass]
pub struct RiskManager {
    /// 仓位限制
    limits: Vec<PositionLimit>,

    /// 单日最大亏损
    daily_loss_limit: Decimal,

    /// 最大回撤限制
    max_drawdown_limit: Decimal,

    /// 累计日亏损
    daily_loss: Decimal,

    /// 历史最高账户价值
    peak_value: Decimal,
}

#[pymethods]
impl RiskManager {
    /// 创建风险管理器
    #[new]
    fn new() -> Self {
        Self {
            limits: Vec::new(),
            daily_loss_limit: Decimal::from(50000),
            max_drawdown_limit: Decimal::from_f64_retain(0.15).unwrap_or(Decimal::ZERO),
            daily_loss: Decimal::ZERO,
            peak_value: Decimal::ZERO,
        }
    }

    /// 添加仓位限制
    fn add_limit(&mut self, limit: PositionLimit) {
        self.limits.push(limit);
    }

    /// 检查订单
    fn check_order(&self, order: &Order, portfolio: &Portfolio) -> PyResult<()> {
        // 1. 检查仓位限制
        for limit in &self.limits {
            if limit.symbol == order.symbol || limit.symbol.is_empty() {
                let current_position = portfolio
                    .get_position(&order.symbol)
                    .map(|p| p.quantity)
                    .unwrap_or(0);

                let new_quantity = match order.side {
                    OrderSide::Buy => current_position + order.quantity,
                    OrderSide::Sell => current_position - order.quantity,
                };

                if new_quantity > limit.max_volume {
                    return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                        "超出仓位限制：{} 当前 {} + 委托 {} > 上限 {}",
                        order.symbol, current_position, order.quantity, limit.max_volume
                    )));
                }
            }
        }

        // 2. 检查订单金额
        let order_value = order.price * Decimal::from(order.quantity);
        let available_cash = portfolio.available_cash();

        if order.side == OrderSide::Buy && order_value > available_cash {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "资金不足：订单金额 {} > 可用资金 {}",
                order_value, available_cash
            )));
        }

        // 3. 检查每日亏损限制（严格大于才阻止）
        if self.daily_loss > self.daily_loss_limit {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(
                "已达到单日最大亏损限制，停止交易",
            ));
        }

        // 4. 检查回撤限制
        let current_value = portfolio.total_asset;
        if self.peak_value > Decimal::ZERO {
            let drawdown = (self.peak_value - current_value) / self.peak_value;
            if drawdown > self.max_drawdown_limit {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                    "超出最大回撤限制：当前 {:.2}% > 限制 {:.2}%",
                    drawdown * Decimal::from(100),
                    self.max_drawdown_limit * Decimal::from(100)
                )));
            }
        }

        Ok(())
    }

    /// 设置单日最大亏损
    fn set_daily_loss_limit(&mut self, amount: f64) {
        self.daily_loss_limit = Decimal::from_f64_retain(amount).unwrap_or(self.daily_loss_limit);
    }

    /// 设置最大回撤
    fn set_max_drawdown(&mut self, percent: f64) {
        self.max_drawdown_limit =
            Decimal::from_f64_retain(percent).unwrap_or(self.max_drawdown_limit);
    }

    /// 更新每日亏损
    pub fn update_daily_loss(&mut self, loss: Decimal) {
        self.daily_loss += loss;
    }

    /// 更新峰值
    pub fn update_peak(&mut self, value: Decimal) {
        if value > self.peak_value {
            self.peak_value = value;
        }
    }

    /// 重置每日亏损（新交易日调用）
    pub fn reset_daily_loss(&mut self) {
        self.daily_loss = Decimal::ZERO;
    }
}

impl Default for RiskManager {
    fn default() -> Self {
        Self::new()
    }
}
