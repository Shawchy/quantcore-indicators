//! 订单匹配引擎

use crate::core::{Bar, Order, OrderSide, OrderStatus, OrderType, Trade};
use rust_decimal::Decimal;
use rust_decimal::prelude::*;
use std::str::FromStr;

pub struct MatchingEngine {
    next_order_id: u64,
    next_trade_id: u64,
    commission_rate: Decimal,
    slippage: Decimal,
    stamp_tax: Decimal,
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

    pub fn with_params(
        mut self,
        commission_rate: f64,
        slippage: f64,
        stamp_tax: f64,
        min_commission: f64,
    ) -> Self {
        self.commission_rate = Decimal::from_str(&format!("{:.6}", commission_rate)).unwrap_or(self.commission_rate);
        self.slippage = Decimal::from_str(&format!("{:.6}", slippage)).unwrap_or(self.slippage);
        self.stamp_tax = Decimal::from_str(&format!("{:.6}", stamp_tax)).unwrap_or(self.stamp_tax);
        self.min_commission = Decimal::from_str(&format!("{:.2}", min_commission)).unwrap_or(self.min_commission);
        self
    }

    pub fn match_order(&mut self, order: &mut Order, bar: &Bar) -> Option<Trade> {
        if !order.is_active() {
            return None;
        }

        let fill_price = self.determine_fill_price(order, bar)?;

        if bar.volume <= 0 {
            return None;
        }

        let quantity = order.quantity;
        let turnover = fill_price * Decimal::from(quantity);
        let commission = self.calculate_commission(turnover);
        let tax = self.calculate_tax(turnover, &order.side);

        order.filled_quantity = quantity;
        order.status = OrderStatus::Filled;

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

    pub fn match_order_at_price(&mut self, order: &mut Order, fill_price_f64: f64) -> Option<Trade> {
        if !order.is_active() {
            return None;
        }

        let fill_price = Decimal::from_str(&format!("{:.4}", fill_price_f64)).unwrap_or(Decimal::ZERO);
        if fill_price <= Decimal::ZERO {
            return None;
        }

        let quantity = order.quantity;
        let turnover = fill_price * Decimal::from(quantity);
        let commission = self.calculate_commission(turnover);
        let tax = self.calculate_tax(turnover, &order.side);

        order.filled_quantity = quantity;
        order.status = OrderStatus::Filled;

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

    fn determine_fill_price(&self, order: &Order, bar: &Bar) -> Option<Decimal> {
        match order.order_type {
            OrderType::Market => {
                match order.side {
                    OrderSide::Buy => {
                        let base_price = bar.close;
                        let slip_amount = base_price * self.slippage;
                        Some(base_price + slip_amount)
                    }
                    OrderSide::Sell => {
                        let base_price = bar.close;
                        let slip_amount = base_price * self.slippage;
                        Some(base_price - slip_amount)
                    }
                }
            }
            OrderType::Limit => {
                let limit_price = order.price;
                match order.side {
                    OrderSide::Buy => {
                        if bar.low <= limit_price {
                            let fill_price = limit_price.min(bar.close);
                            Some(fill_price)
                        } else {
                            None
                        }
                    }
                    OrderSide::Sell => {
                        if bar.high >= limit_price {
                            let fill_price = limit_price.max(bar.close);
                            Some(fill_price)
                        } else {
                            None
                        }
                    }
                }
            }
            OrderType::Stop => {
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

    fn calculate_commission(&self, turnover: Decimal) -> Decimal {
        let commission = turnover * self.commission_rate;
        if commission < self.min_commission {
            self.min_commission
        } else {
            commission
        }
    }

    fn calculate_tax(&self, turnover: Decimal, side: &OrderSide) -> Decimal {
        match side {
            OrderSide::Sell => turnover * self.stamp_tax,
            OrderSide::Buy => Decimal::ZERO,
        }
    }

    pub fn generate_order_id(&mut self) -> String {
        let id = self.next_order_id;
        self.next_order_id += 1;
        format!("ORD-{}", id)
    }

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
