//! PyO3 Python 绑定模块 (PyO3 0.28 版本)
//!
//! 将 Rust 核心计算功能暴露给 Python

use numpy::{IntoPyArray, PyArray1, PyArrayMethods};
use pyo3::prelude::*;
use pyo3::types::{PyDict, PyList};

use crate::{adx, atr, bollinger_bands, cci, ema, kdj, ma, macd, obv, rsi, williams_r};

/// 辅助函数：从 Python 对象提取价格向量
fn extract_prices(prices: &Bound<'_, PyAny>) -> PyResult<Vec<f64>> {
    // 尝试作为 numpy 数组处理
    if let Ok(array) = prices.downcast::<PyArray1<f64>>() {
        return Ok(array.to_vec()?);
    }

    // 尝试作为列表处理
    if let Ok(list) = prices.downcast::<PyList>() {
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

/// 辅助函数：从 Python 对象提取成交量向量
fn extract_volume(volume: &Bound<'_, PyAny>) -> PyResult<Vec<i64>> {
    // 尝试作为 numpy 数组处理
    if let Ok(array) = volume.downcast::<PyArray1<i64>>() {
        return Ok(array.to_vec()?);
    }

    // 尝试作为列表处理
    if let Ok(list) = volume.downcast::<PyList>() {
        let mut vec = Vec::with_capacity(list.len());
        for item in list.iter() {
            vec.push(item.extract::<i64>()?);
        }
        return Ok(vec);
    }

    Err(pyo3::exceptions::PyTypeError::new_err(
        "volume 必须是 numpy 数组或列表",
    ))
}

/// 移动平均 (Moving Average)
#[pyfunction]
#[pyo3(signature = (prices, period))]
fn ma_py<'py>(
    py: Python<'py>,
    prices: &Bound<'_, PyAny>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let prices_vec = extract_prices(prices)?;
    let result = ma(&prices_vec, period);
    Ok(result.into_pyarray(py))
}

/// 指数移动平均 (Exponential Moving Average)
#[pyfunction]
#[pyo3(signature = (prices, period))]
fn ema_py<'py>(
    py: Python<'py>,
    prices: &Bound<'_, PyAny>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let prices_vec = extract_prices(prices)?;
    let result = ema(&prices_vec, period);
    Ok(result.into_pyarray(py))
}

/// MACD 指标
#[pyfunction]
#[pyo3(signature = (prices, fast=12, slow=26, signal=9))]
fn macd_py(
    py: Python,
    prices: &Bound<'_, PyAny>,
    fast: usize,
    slow: usize,
    signal: usize,
) -> PyResult<Py<PyAny>> {
    let prices_vec = extract_prices(prices)?;
    let result = macd(&prices_vec, fast, slow, signal);

    let dict = PyDict::new(py);
    dict.set_item("macd", result.macd.into_pyarray(py))?;
    dict.set_item("signal", result.signal.into_pyarray(py))?;
    dict.set_item("histogram", result.histogram.into_pyarray(py))?;

    Ok(dict.unbind().into_any())
}

/// RSI 指标
#[pyfunction]
#[pyo3(signature = (prices, period=14))]
fn rsi_py<'py>(
    py: Python<'py>,
    prices: &Bound<'_, PyAny>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let prices_vec = extract_prices(prices)?;
    let result = rsi(&prices_vec, period);
    Ok(result.into_pyarray(py))
}

/// 布林带指标
#[pyfunction]
#[pyo3(signature = (prices, period=20, std_dev=2.0))]
fn bollinger_bands_py(
    py: Python,
    prices: &Bound<'_, PyAny>,
    period: usize,
    std_dev: f64,
) -> PyResult<Py<PyAny>> {
    let prices_vec = extract_prices(prices)?;
    let result = bollinger_bands(&prices_vec, period, std_dev);

    let dict = PyDict::new(py);
    dict.set_item("upper", result.upper.into_pyarray(py))?;
    dict.set_item("middle", result.middle.into_pyarray(py))?;
    dict.set_item("lower", result.lower.into_pyarray(py))?;

    Ok(dict.unbind().into_any())
}

/// ATR 指标
#[pyfunction]
#[pyo3(signature = (high, low, close, period=14))]
fn atr_py<'py>(
    py: Python<'py>,
    high: &Bound<'_, PyAny>,
    low: &Bound<'_, PyAny>,
    close: &Bound<'_, PyAny>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let high_vec = extract_prices(high)?;
    let low_vec = extract_prices(low)?;
    let close_vec = extract_prices(close)?;

    let result = atr(&high_vec, &low_vec, &close_vec, period);
    Ok(result.into_pyarray(py))
}

/// CCI 指标
#[pyfunction]
#[pyo3(signature = (high, low, close, period=20))]
fn cci_py<'py>(
    py: Python<'py>,
    high: &Bound<'_, PyAny>,
    low: &Bound<'_, PyAny>,
    close: &Bound<'_, PyAny>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let high_vec = extract_prices(high)?;
    let low_vec = extract_prices(low)?;
    let close_vec = extract_prices(close)?;

    let result = cci(&high_vec, &low_vec, &close_vec, period);
    Ok(result.into_pyarray(py))
}

/// KDJ 指标
#[pyfunction]
#[pyo3(signature = (high, low, close, n=9, m1=3, m2=3))]
fn kdj_py(
    py: Python,
    high: &Bound<'_, PyAny>,
    low: &Bound<'_, PyAny>,
    close: &Bound<'_, PyAny>,
    n: usize,
    m1: usize,
    m2: usize,
) -> PyResult<Py<PyAny>> {
    let high_vec = extract_prices(high)?;
    let low_vec = extract_prices(low)?;
    let close_vec = extract_prices(close)?;

    let result = kdj(&high_vec, &low_vec, &close_vec, n, m1, m2);

    let dict = PyDict::new(py);
    dict.set_item("k", result.k.into_pyarray(py))?;
    dict.set_item("d", result.d.into_pyarray(py))?;
    dict.set_item("j", result.j.into_pyarray(py))?;

    Ok(dict.unbind().into_any())
}

/// OBV 指标
#[pyfunction]
#[pyo3(signature = (close, volume))]
fn obv_py<'py>(
    py: Python<'py>,
    close: &Bound<'_, PyAny>,
    volume: &Bound<'_, PyAny>,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let close_vec = extract_prices(close)?;
    let volume_vec = extract_volume(volume)?;

    let result = obv(&close_vec, &volume_vec);
    Ok(result.into_pyarray(py))
}

/// Williams %R 指标
#[pyfunction]
#[pyo3(signature = (high, low, close, period=14))]
fn williams_r_py<'py>(
    py: Python<'py>,
    high: &Bound<'_, PyAny>,
    low: &Bound<'_, PyAny>,
    close: &Bound<'_, PyAny>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let high_vec = extract_prices(high)?;
    let low_vec = extract_prices(low)?;
    let close_vec = extract_prices(close)?;

    let result = williams_r(&high_vec, &low_vec, &close_vec, period);
    Ok(result.into_pyarray(py))
}

/// ADX 指标
#[pyfunction]
#[pyo3(signature = (high, low, close, period=14))]
fn adx_py<'py>(
    py: Python<'py>,
    high: &Bound<'_, PyAny>,
    low: &Bound<'_, PyAny>,
    close: &Bound<'_, PyAny>,
    period: usize,
) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let high_vec = extract_prices(high)?;
    let low_vec = extract_prices(low)?;
    let close_vec = extract_prices(close)?;

    let result = adx(&high_vec, &low_vec, &close_vec, period);
    Ok(result.into_pyarray(py))
}

/// Python 模块定义
#[pymodule]
pub fn quantcore_indicators(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(ma_py, m)?)?;
    m.add_function(wrap_pyfunction!(ema_py, m)?)?;
    m.add_function(wrap_pyfunction!(macd_py, m)?)?;
    m.add_function(wrap_pyfunction!(rsi_py, m)?)?;
    m.add_function(wrap_pyfunction!(bollinger_bands_py, m)?)?;
    m.add_function(wrap_pyfunction!(atr_py, m)?)?;
    m.add_function(wrap_pyfunction!(cci_py, m)?)?;
    m.add_function(wrap_pyfunction!(kdj_py, m)?)?;
    m.add_function(wrap_pyfunction!(obv_py, m)?)?;
    m.add_function(wrap_pyfunction!(williams_r_py, m)?)?;
    m.add_function(wrap_pyfunction!(adx_py, m)?)?;

    Ok(())
}
