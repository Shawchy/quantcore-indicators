//! QuantCore Indicators - Rust 核心计算模块
//!
//! 提供高性能金融指标计算，支持 NumPy 和 Arrow 双后端
//!
//! # 后端选择
//!
//! - **NumPy 后端** (默认): 适合小到中等规模数据，API 友好
//! - **Arrow 后端**: 适合大规模数据，零拷贝，极致性能
//!
//! # 使用示例
//!
//! ```rust
//! use quantcore_indicators::{ma, ema, rsi};
//!
//! // 使用核心计算
//! let prices = vec![100.0, 101.0, 102.0, 103.0, 104.0];
//! let ma_values = ma(&prices, 3);
//! assert_eq!(ma_values.len(), 3);
//! ```
//!
//! # Arrow 后端示例 (需要启用 arrow-backend 特性)
//!
//! ```rust,ignore
//! // 需要：cargo test --features arrow-backend
//! use quantcore_indicators::ma_arrow;
//! use arrow_array::Float64Array;
//!
//! let prices_array = Float64Array::from(vec![100.0, 101.0, 102.0, 103.0, 104.0]);
//! let ma_array = ma_arrow(&prices_array, 3);
//! assert_eq!(ma_array.len(), 3);
//! ```

use pyo3::prelude::*;

// 核心计算模块
mod core;

// 后端模块
#[cfg(feature = "numpy-backend")]
pub mod numpy_backend;

#[cfg(feature = "arrow-backend")]
pub mod arrow_backend;

// 重新导出核心函数
pub use core::*;

// 重新导出后端特定函数
#[cfg(feature = "numpy-backend")]
pub use numpy_backend::*;

#[cfg(feature = "arrow-backend")]
pub use arrow_backend::*;

// PyO3 绑定（仅在构建 Python 模块时）
#[cfg(feature = "extension-module")]
pub mod pyo3_bindings;
