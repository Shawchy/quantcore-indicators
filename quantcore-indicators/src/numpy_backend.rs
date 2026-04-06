//! NumPy 后端 - 使用 numpy-rs 实现 Python 互操作
//!
//! 适合小到中等规模数据，API 友好

#[cfg(feature = "numpy-backend")]
use numpy::{IntoPyArray, PyArray1, PyArrayMethods};
use pyo3::prelude::*;

// 重新导出核心函数
pub use crate::core::*;

/// 将 `&[f64]` 转换为 NumPy 数组
#[cfg(feature = "numpy-backend")]
pub fn to_numpy_array<'py>(py: Python<'py>, data: &[f64]) -> PyResult<Bound<'py, PyArray1<f64>>> {
    Ok(data.to_vec().into_pyarray(py))
}

/// 从 Python 提取数据并计算 MA，返回 NumPy 数组
#[cfg(feature = "numpy-backend")]
#[pyfunction]
#[pyo3(signature = (prices, period))]
pub fn ma_numpy<'py>(
    py: Python<'py>,
    prices: &Bound<'py, PyAny>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let prices_vec = extract_prices(prices)?;
    let result = ma(&prices_vec, period);
    Ok(result.into_pyarray(py))
}

/// 从 Python 提取数据并计算 RSI，返回 NumPy 数组
#[cfg(feature = "numpy-backend")]
#[pyfunction]
#[pyo3(signature = (prices, period=14))]
pub fn rsi_numpy<'py>(
    py: Python<'py>,
    prices: &Bound<'py, PyAny>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let prices_vec = extract_prices(prices)?;
    let result = rsi(&prices_vec, period);
    Ok(result.into_pyarray(py))
}

/// 辅助函数：从 Python 对象提取价格向量
fn extract_prices(prices: &Bound<'_, PyAny>) -> PyResult<Vec<f64>> {
    use pyo3::types::PyList;

    // 尝试作为 numpy 数组处理
    if let Ok(array) = prices.cast::<PyArray1<f64>>() {
        return Ok(array.to_vec()?);
    }

    // 尝试作为列表处理
    if let Ok(list) = prices.cast::<PyList>() {
        let mut vec = Vec::with_capacity(list.len());
        for item in list.iter() {
            vec.push(item.extract::<f64>()?);
        }
        return Ok(vec);
    }

    Err(pyo3::exceptions::PyTypeError::new_err(
        "prices 必须是 numpy 数组或列表",
    ))
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
