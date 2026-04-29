//! QuantCore Indicators - Rust 核心计算模块
//!
//! 高性能金融指标计算库

// 核心计算模块
mod core;

// PyO3 绑定（始终编译，pyo3_bindings.rs 使用 pyo3::prelude）
pub mod pyo3_bindings;

// 重新导出核心函数
pub use core::*;
