//! NumPy 后端 - 使用 numpy-rs 实现 Python 互操作
//!
//! 适合小到中等规模数据，API 友好

#[cfg(feature = "numpy-backend")]
use numpy::{IntoPyArray, PyArray1};
use pyo3::prelude::*;

pub use crate::core::*;

#[cfg(feature = "numpy-backend")]
pub fn to_numpy_array<'py>(py: Python<'py>, data: &[f64]) -> PyResult<Bound<'py, PyArray1<f64>>> {
    Ok(data.to_vec().into_pyarray(py))
}

#[cfg(feature = "numpy-backend")]
#[pyfunction]
#[pyo3(signature = (prices, period))]
pub fn ma_numpy<'py>(
    py: Python<'py>,
    prices: &Bound<'py, PyAny>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // 注意：extension-module 特性已通过 numpy-backend 自动启用
    // 此 cfg 检查作为额外的安全保护
    #[cfg(feature = "extension-module")]
    {
        let prices_vec = crate::pyo3_bindings::extract_prices(prices)?;
        let result = ma(&prices_vec, period);
        Ok(result.into_pyarray(py))
    }
    
    // 此分支在正常情况下不应执行（因为 numpy-backend 已包含 extension-module）
    // 仅作为防御性编程的最终保障
    #[cfg(not(feature = "extension-module"))]
    {
        Err(pyo3::exceptions::PyRuntimeError::new_err(
            "Internal error: extension-module feature not enabled. \
             This should not happen when numpy-backend is active. \
             Please report this issue."
        ))
    }
}

#[cfg(feature = "numpy-backend")]
#[pyfunction]
#[pyo3(signature = (prices, period=14))]
pub fn rsi_numpy<'py>(
    py: Python<'py>,
    prices: &Bound<'py, PyAny>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    // 注意：extension-module 特性已通过 numpy-backend 自动启用
    // 此 cfg 检查作为额外的安全保护
    #[cfg(feature = "extension-module")]
    {
        let prices_vec = crate::pyo3_bindings::extract_prices(prices)?;
        let result = rsi(&prices_vec, period);
        Ok(result.into_pyarray(py))
    }
    
    // 此分支在正常情况下不应执行（因为 numpy-backend 已包含 extension-module）
    // 仅作为防御性编程的最终保障
    #[cfg(not(feature = "extension-module"))]
    {
        Err(pyo3::exceptions::PyRuntimeError::new_err(
            "Internal error: extension-module feature not enabled. \
             This should not happen when numpy-backend is active. \
             Please report this issue."
        ))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_core_ma() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = ma(&prices, 3);
        assert_eq!(result.len(), 3);
        assert!((result[0] - 2.0).abs() < 1e-10);
    }
}
