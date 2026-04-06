//! 核心数据结构模块
//!
//! 包含量化交易的基础数据类型：
//! - Bar: K 线数据
//! - Tick:  Tick 数据
//! - Order: 订单
//! - Trade: 成交
//! - Position: 持仓
//! - Portfolio: 投资组合

pub mod bar;
pub mod order;
pub mod portfolio;
pub mod position;
pub mod tick;
pub mod trade;

// 重新导出
pub use bar::Bar;
pub use order::{Order, OrderSide, OrderStatus, OrderType};
pub use portfolio::Portfolio;
pub use position::Position;
pub use tick::Tick;
pub use trade::Trade;
