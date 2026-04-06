//! 订单匹配引擎

use crate::core::{Bar, Order, Trade};
use rust_decimal::Decimal;

/// 订单匹配引擎
pub struct MatchingEngine {
    /// 下一个订单 ID
    next_order_id: u64,

    /// 下一个成交 ID
    next_trade_id: u64,
}

impl MatchingEngine {
    pub fn new() -> Self {
        Self {
            next_order_id: 1,
            next_trade_id: 1,
        }
    }

    /// 匹配订单
    pub fn match_order(&mut self, order: &mut Order, bar: &Bar) -> Option<Trade> {
        // TODO: 实现订单匹配逻辑
        // 1. 检查订单是否可以成交
        // 2. 根据订单类型（市价/限价）确定成交价
        // 3. 考虑滑点
        // 4. 计算手续费
        // 5. 生成成交记录

        None
    }

    /// 生成订单 ID
    pub fn generate_order_id(&mut self) -> String {
        let id = self.next_order_id;
        self.next_order_id += 1;
        format!("ORD-{}", id)
    }

    /// 生成成交 ID
    pub fn generate_trade_id(&mut self) -> String {
        let id = self.next_trade_id;
        self.next_trade_id += 1;
        format!("TRD-{}", id)
    }
}

impl Default for MatchingEngine {
    fn default() -> Self {
        Self::new()
    }
}
