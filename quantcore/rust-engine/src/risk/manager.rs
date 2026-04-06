//! 风险管理器

use super::limits::PositionLimit;
use crate::core::{Order, Portfolio};
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
        }
    }

    /// 添加仓位限制
    fn add_limit(&mut self, limit: PositionLimit) {
        self.limits.push(limit);
    }

    /// 检查订单
    fn check_order(&self, _order: &Order, _portfolio: &Portfolio) -> PyResult<()> {
        // TODO: 实现订单检查逻辑
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
}

impl Default for RiskManager {
    fn default() -> Self {
        Self::new()
    }
}
