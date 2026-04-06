//! 错误处理

use thiserror::Error;

/// QuantCore 错误类型
#[derive(Error, Debug)]
pub enum QuantError {
    #[error("数据错误：{0}")]
    DataError(String),

    #[error("订单错误：{0}")]
    OrderError(String),

    #[error("风控错误：{0}")]
    RiskError(String),

    #[error("策略错误：{0}")]
    StrategyError(String),

    #[error("IO 错误：{0}")]
    IoError(#[from] std::io::Error),

    #[error("JSON 错误：{0}")]
    JsonError(#[from] serde_json::Error),
}

pub type Result<T> = std::result::Result<T, QuantError>;
