//! 订单模块

use chrono::{DateTime, Utc};
use pyo3::prelude::*;
use rust_decimal::Decimal;
use rust_decimal::prelude::*;
use serde::{Deserialize, Serialize};

/// 订单方向
#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum OrderSide {
    /// 买入
    Buy,
    /// 卖出
    Sell,
}

/// 订单类型
#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum OrderType {
    /// 市价单
    Market,
    /// 限价单
    Limit,
    /// 止损单
    Stop,
    /// 止盈单
    StopLimit,
}

/// 订单状态
#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
pub enum OrderStatus {
    /// 待提交
    Pending,
    /// 已提交
    Submitted,
    /// 部分成交
    PartiallyFilled,
    /// 完全成交
    Filled,
    /// 已取消
    Cancelled,
    /// 已拒绝
    Rejected,
}

/// 订单
#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Order {
    /// 订单 ID
    #[pyo3(get)]
    pub order_id: String,

    /// 策略 ID
    #[pyo3(get)]
    pub strategy_id: String,

    /// 证券代码
    #[pyo3(get)]
    pub symbol: String,

    /// 订单方向
    #[pyo3(get)]
    pub side: OrderSide,

    /// 订单类型
    #[pyo3(get)]
    pub order_type: OrderType,

    /// 委托价格（止损单为触发价，限价单为限价）
    #[pyo3(get)]
    pub price: Decimal,

    /// 限价（仅止损限价单有效）
    #[pyo3(get)]
    pub limit_price: Decimal,

    /// 委托数量
    #[pyo3(get)]
    pub quantity: i64,

    /// 成交数量
    #[pyo3(get)]
    pub filled_quantity: i64,

    /// 订单状态
    #[pyo3(get)]
    pub status: OrderStatus,

    /// 创建时间
    #[pyo3(get)]
    pub created_at: DateTime<Utc>,

    /// 更新时间
    #[pyo3(get)]
    pub updated_at: DateTime<Utc>,
}

#[pymethods]
impl Order {
    /// 创建新订单
    #[new]
    #[pyo3(signature = (order_id, strategy_id, symbol, side, order_type, price, quantity, limit_price=None))]
    fn new(
        order_id: String,
        strategy_id: String,
        symbol: String,
        side: OrderSide,
        order_type: OrderType,
        price: f64,
        quantity: i64,
        limit_price: Option<f64>,
    ) -> Self {
        let now = Utc::now();
        let price_dec = if price.is_nan() || price.is_infinite() {
            log::error!("订单价格无效: {}", price);
            Decimal::ZERO
        } else {
            Decimal::from_f64_retain(price).unwrap_or_else(|| {
                log::error!("订单价格转换失败: {}", price);
                Decimal::ZERO
            })
        };
        let limit_price_val = limit_price
            .and_then(|p| {
                if p.is_nan() || p.is_infinite() {
                    log::error!("限价无效: {}", p);
                    None
                } else {
                    Decimal::from_f64_retain(p)
                }
            })
            .unwrap_or(price_dec);
        Self {
            order_id,
            strategy_id,
            symbol,
            side,
            order_type,
            price: price_dec,
            limit_price: limit_price_val,
            quantity,
            filled_quantity: 0,
            status: OrderStatus::Pending,
            created_at: now,
            updated_at: now,
        }
    }

    /// 字符串表示
    fn __repr__(&self) -> String {
        format!(
            "Order(id={}, symbol={}, side={:?}, type={:?}, price={}, qty={}, status={:?})",
            self.order_id,
            self.symbol,
            self.side,
            self.order_type,
            self.price,
            self.quantity,
            self.status
        )
    }

    /// 是否已完全成交
    fn is_filled(&self) -> bool {
        self.status == OrderStatus::Filled
    }

    /// 是否活跃（待成交）
    fn is_active(&self) -> bool {
        matches!(
            self.status,
            OrderStatus::Pending | OrderStatus::Submitted | OrderStatus::PartiallyFilled
        )
    }

    /// 获取未成交数量
    fn remaining_quantity(&self) -> i64 {
        self.quantity - self.filled_quantity
    }
}
