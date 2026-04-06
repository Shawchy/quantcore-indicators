//! 策略基类

use super::context::StrategyContext;
use crate::core::Bar;
use pyo3::prelude::*;

/// 策略特征
pub trait Strategy: Send + Sync {
    /// 策略初始化
    fn on_init(&mut self, context: &mut StrategyContext);

    /// K 线事件
    fn on_bar(&mut self, context: &mut StrategyContext, bar: &Bar);

    /// 订单事件
    fn on_order(&mut self, context: &mut StrategyContext, order: &crate::core::Order);

    /// 成交事件
    fn on_trade(&mut self, context: &mut StrategyContext, trade: &crate::core::Trade);

    /// 回测结束
    fn on_finish(&mut self, context: &mut StrategyContext);
}
