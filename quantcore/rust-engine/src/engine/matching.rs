//! 订单匹配引擎

use crate::core::{Bar, Order, OrderSide, OrderStatus, OrderType, Trade};
use rust_decimal::Decimal;

/// 订单匹配引擎
pub struct MatchingEngine {
    /// 下一个订单 ID
    next_order_id: u64,

    /// 下一个成交 ID
    next_trade_id: u64,

    /// 佣金率
    commission_rate: Decimal,

    /// 滑点
    slippage: Decimal,

    /// 印花税（卖出收取）
    stamp_tax: Decimal,

    /// 最小手续费
    min_commission: Decimal,
}

impl MatchingEngine {
    pub fn new() -> Self {
        Self {
            next_order_id: 1,
            next_trade_id: 1,
            commission_rate: Decimal::from_str("0.0003").unwrap(),
            slippage: Decimal::from_str("0.001").unwrap(),
            stamp_tax: Decimal::from_str("0.001").unwrap(),
            min_commission: Decimal::from(5),
        }
    }

    /// 设置交易参数
    pub fn with_params(
        mut self,
        commission_rate: f64,
        slippage: f64,
        stamp_tax: f64,
        min_commission: f64,
    ) -> Self {
        self.commission_rate = Decimal::from_f64_retain(commission_rate).unwrap_or(self.commission_rate);
        self.slippage = Decimal::from_f64_retain(slippage).unwrap_or(self.slippage);
        self.stamp_tax = Decimal::from_f64_retain(stamp_tax).unwrap_or(self.stamp_tax);
        self.min_commission = Decimal::from_f64_retain(min_commission).unwrap_or(self.min_commission);
        self
    }

    /// 匹配订单
    pub fn match_order(&mut self, order: &mut Order, bar: &Bar) -> Option<Trade> {
        // 1. 检查订单是否可以成交
        if !order.is_active() {
            return None;
        }

        // 2. 根据订单类型确定成交价
        let fill_price = self.determine_fill_price(order, bar)?;

        // 3. 检查成交量是否足够
        if bar.volume <= 0 {
            return None;
        }

        // 4. 计算手续费
        let quantity = order.quantity;
        let turnover = fill_price * Decimal::from(quantity);
        let commission = self.calculate_commission(turnover);
        let tax = self.calculate_tax(turnover, &order.side);

        // 5. 更新订单状态
        order.filled_quantity = quantity;
        order.status = OrderStatus::Filled;

        // 6. 生成成交记录
        let trade_id = self.generate_trade_id();
        let side_str = match order.side {
            OrderSide::Buy => "buy",
            OrderSide::Sell => "sell",
        };

        Some(Trade::new(
            trade_id,
            order.order_id.clone(),
            order.strategy_id.clone(),
            order.symbol.clone(),
            side_str.to_string(),
            fill_price.to_f64().unwrap_or(0.0),
            quantity,
            commission.to_f64().unwrap_or(0.0),
            tax.to_f64().unwrap_or(0.0),
        ))
    }

    /// 确定成交价格
    fn determine_fill_price(&self, order: &Order, bar: &Bar) -> Option<Decimal> {
        match order.order_type {
            OrderType::Market => {
                // 市价单：使用收盘价加滑点
                let base_price = bar.close;
                let slip_amount = base_price * self.slippage;
                Some(base_price + slip_amount)
            }
            OrderType::Limit => {
                // 限价单：检查是否满足价格条件
                let limit_price = order.price;

                // 判断订单方向
                match order.side {
                    OrderSide::Buy => {
                        // 买入：bar.low <= limit_price 时可以成交
                        if bar.low <= limit_price {
                            // 以限价和收盘价中较低者成交
                            let fill_price = limit_price.min(bar.close);
                            Some(fill_price)
                        } else {
                            None
                        }
                    }
                    OrderSide::Sell => {
                        // 卖出：bar.high >= limit_price 时可以成交
                        if bar.high >= limit_price {
                            // 以限价和收盘价中较高者成交
                            let fill_price = limit_price.max(bar.close);
                            Some(fill_price)
                        } else {
                            None
                        }
                    }
                }
            }
            OrderType::Stop => {
                // 止损单：价格触及止损价时转为市价单
                let stop_price = order.price;
                match order.side {
                    OrderSide::Buy => {
                        if bar.high >= stop_price {
                            let base_price = bar.close;
                            let slip_amount = base_price * self.slippage;
                            Some(base_price + slip_amount)
                        } else {
                            None
                        }
                    }
                    OrderSide::Sell => {
                        if bar.low <= stop_price {
                            let base_price = bar.close;
                            let slip_amount = base_price * self.slippage;
                            Some(base_price - slip_amount)
                        } else {
                            None
                        }
                    }
                }
            }
            OrderType::StopLimit => {
                // 止损限价单：价格触发后以限价成交
                let stop_price = order.price;
                let limit_price = order.limit_price;
                match order.side {
                    OrderSide::Buy => {
                        if bar.high >= stop_price && bar.low <= limit_price {
                            Some(limit_price.min(bar.close))
                        } else {
                            None
                        }
                    }
                    OrderSide::Sell => {
                        if bar.low <= stop_price && bar.high >= limit_price {
                            Some(limit_price.max(bar.close))
                        } else {
                            None
                        }
                    }
                }
            }
        }
    }

    /// 计算手续费
    fn calculate_commission(&self, turnover: Decimal) -> Decimal {
        let commission = turnover * self.commission_rate;
        if commission < self.min_commission {
            self.min_commission
        } else {
            commission
        }
    }

    /// 计算印花税（仅卖出）
    fn calculate_tax(&self, turnover: Decimal, side: &OrderSide) -> Decimal {
        match side {
            OrderSide::Sell => turnover * self.stamp_tax,
            OrderSide::Buy => Decimal::ZERO,
        }
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
