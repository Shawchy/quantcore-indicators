//! 策略框架模块

pub mod base;
pub mod context;
pub mod runner;

pub use base::Strategy;
pub use context::StrategyContext;
pub use runner::StrategyRunner;

use pyo3::prelude::*;

/// Python 策略包装器
#[pyclass]
pub struct PyStrategy {
    /// 策略名称
    #[pyo3(get)]
    pub name: String,
}

#[pymethods]
impl PyStrategy {
    #[new]
    fn new(name: String) -> Self {
        Self { name }
    }

    fn __repr__(&self) -> String {
        format!("PyStrategy(name={})", self.name)
    }
}
