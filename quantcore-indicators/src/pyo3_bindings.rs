use numpy::{IntoPyArray, PyArray1, PyReadonlyArray1};
use pyo3::prelude::*;
use pyo3::types::PyDict;

use crate::{adx, atr, bollinger_bands, cci, dema, ema, hma, kdj, ma, macd, natr, obv, psar, roc, rsi, tema, williams_r, vwap, wma, stochastic};

#[pyfunction]
#[pyo3(signature = (prices, period))]
fn ma_py<'py>(py: Python<'py>, prices: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = ma(prices.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (prices, period))]
fn ema_py<'py>(py: Python<'py>, prices: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = ema(prices.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (prices, period))]
fn dema_py<'py>(py: Python<'py>, prices: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = dema(prices.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (prices, period))]
fn tema_py<'py>(py: Python<'py>, prices: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = tema(prices.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (prices, period))]
fn hma_py<'py>(py: Python<'py>, prices: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = hma(prices.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (prices, period))]
fn roc_py<'py>(py: Python<'py>, prices: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = roc(prices.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (prices, fast=12, slow=26, signal=9))]
fn macd_py<'py>(py: Python<'py>, prices: PyReadonlyArray1<'_, f64>, fast: usize, slow: usize, signal: usize) -> PyResult<Bound<'py, PyDict>> {
    let result = macd(prices.as_slice()?, fast, slow, signal);
    let dict = PyDict::new(py);
    dict.set_item("macd", result.macd.into_pyarray(py))?;
    dict.set_item("signal", result.signal.into_pyarray(py))?;
    dict.set_item("histogram", result.histogram.into_pyarray(py))?;
    Ok(dict)
}

#[pyfunction]
#[pyo3(signature = (prices, period=14))]
fn rsi_py<'py>(py: Python<'py>, prices: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = rsi(prices.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (prices, period=20, std_dev=2.0))]
fn bollinger_bands_py<'py>(py: Python<'py>, prices: PyReadonlyArray1<'_, f64>, period: usize, std_dev: f64) -> PyResult<Bound<'py, PyDict>> {
    let result = bollinger_bands(prices.as_slice()?, period, std_dev);
    let dict = PyDict::new(py);
    dict.set_item("upper", result.upper.into_pyarray(py))?;
    dict.set_item("middle", result.middle.into_pyarray(py))?;
    dict.set_item("lower", result.lower.into_pyarray(py))?;
    Ok(dict)
}

#[pyfunction]
#[pyo3(signature = (high, low, close, period=14))]
fn atr_py<'py>(py: Python<'py>, high: PyReadonlyArray1<'_, f64>, low: PyReadonlyArray1<'_, f64>, close: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = atr(high.as_slice()?, low.as_slice()?, close.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (high, low, close, period=14))]
fn natr_py<'py>(py: Python<'py>, high: PyReadonlyArray1<'_, f64>, low: PyReadonlyArray1<'_, f64>, close: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = natr(high.as_slice()?, low.as_slice()?, close.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (high, low, close, period=20))]
fn cci_py<'py>(py: Python<'py>, high: PyReadonlyArray1<'_, f64>, low: PyReadonlyArray1<'_, f64>, close: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = cci(high.as_slice()?, low.as_slice()?, close.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (high, low, close, n=9, m1=3, m2=3))]
fn kdj_py<'py>(py: Python<'py>, high: PyReadonlyArray1<'_, f64>, low: PyReadonlyArray1<'_, f64>, close: PyReadonlyArray1<'_, f64>, n: usize, m1: usize, m2: usize) -> PyResult<Bound<'py, PyDict>> {
    let result = kdj(high.as_slice()?, low.as_slice()?, close.as_slice()?, n, m1, m2);
    let dict = PyDict::new(py);
    dict.set_item("k", result.k.into_pyarray(py))?;
    dict.set_item("d", result.d.into_pyarray(py))?;
    dict.set_item("j", result.j.into_pyarray(py))?;
    Ok(dict)
}

#[pyfunction]
#[pyo3(signature = (close, volume))]
fn obv_py<'py>(py: Python<'py>, close: PyReadonlyArray1<'_, f64>, volume: PyReadonlyArray1<'_, f64>) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = obv(close.as_slice()?, volume.as_slice()?);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (high, low, close, period=14))]
fn williams_r_py<'py>(py: Python<'py>, high: PyReadonlyArray1<'_, f64>, low: PyReadonlyArray1<'_, f64>, close: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = williams_r(high.as_slice()?, low.as_slice()?, close.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (high, low, close, period=14))]
fn adx_py<'py>(py: Python<'py>, high: PyReadonlyArray1<'_, f64>, low: PyReadonlyArray1<'_, f64>, close: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = adx(high.as_slice()?, low.as_slice()?, close.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (prices, period))]
fn wma_py<'py>(py: Python<'py>, prices: PyReadonlyArray1<'_, f64>, period: usize) -> PyResult<Bound<'py, PyArray1<f64>>> {
    let result = wma(prices.as_slice()?, period);
    Ok(result.into_pyarray(py))
}

#[pyfunction]
#[pyo3(signature = (high, low, close, k_period=14, d_period=3))]
fn stochastic_py<'py>(py: Python<'py>, high: PyReadonlyArray1<'_, f64>, low: PyReadonlyArray1<'_, f64>, close: PyReadonlyArray1<'_, f64>, k_period: usize, d_period: usize) -> PyResult<Bound<'py, PyDict>> {
    let result = stochastic(high.as_slice()?, low.as_slice()?, close.as_slice()?, k_period, d_period);
    let dict = PyDict::new(py);
    dict.set_item("k", result.k.into_pyarray(py))?;
    dict.set_item("d", result.d.into_pyarray(py))?;
    Ok(dict)
}

#[pyfunction]
#[pyo3(signature = (high, low, close, volume))]
fn vwap_py<'py>(py: Python<'py>, high: PyReadonlyArray1<'_, f64>, low: PyReadonlyArray1<'_, f64>, close: PyReadonlyArray1<'_, f64>, volume: PyReadonlyArray1<'_, f64>) -> PyResult<Bound<'py, PyDict>> {
    let result = vwap(high.as_slice()?, low.as_slice()?, close.as_slice()?, volume.as_slice()?);
    let dict = PyDict::new(py);
    dict.set_item("vwap", result.vwap.into_pyarray(py))?;
    Ok(dict)
}

#[pyfunction]
#[pyo3(signature = (high, low, close, step=0.02, max_step=0.2))]
fn psar_py<'py>(py: Python<'py>, high: PyReadonlyArray1<'_, f64>, low: PyReadonlyArray1<'_, f64>, close: PyReadonlyArray1<'_, f64>, step: f64, max_step: f64) -> PyResult<Bound<'py, PyDict>> {
    let result = psar(high.as_slice()?, low.as_slice()?, close.as_slice()?, step, max_step);
    let dict = PyDict::new(py);
    dict.set_item("sar", result.sar.into_pyarray(py))?;
    dict.set_item("trend", result.trend.into_pyarray(py))?;
    Ok(dict)
}

#[pymodule]
pub fn quantcore_indicators(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(ma_py, m)?)?;
    m.add_function(wrap_pyfunction!(ema_py, m)?)?;
    m.add_function(wrap_pyfunction!(dema_py, m)?)?;
    m.add_function(wrap_pyfunction!(tema_py, m)?)?;
    m.add_function(wrap_pyfunction!(hma_py, m)?)?;
    m.add_function(wrap_pyfunction!(wma_py, m)?)?;
    m.add_function(wrap_pyfunction!(roc_py, m)?)?;
    m.add_function(wrap_pyfunction!(macd_py, m)?)?;
    m.add_function(wrap_pyfunction!(rsi_py, m)?)?;
    m.add_function(wrap_pyfunction!(bollinger_bands_py, m)?)?;
    m.add_function(wrap_pyfunction!(atr_py, m)?)?;
    m.add_function(wrap_pyfunction!(natr_py, m)?)?;
    m.add_function(wrap_pyfunction!(cci_py, m)?)?;
    m.add_function(wrap_pyfunction!(kdj_py, m)?)?;
    m.add_function(wrap_pyfunction!(obv_py, m)?)?;
    m.add_function(wrap_pyfunction!(williams_r_py, m)?)?;
    m.add_function(wrap_pyfunction!(adx_py, m)?)?;
    m.add_function(wrap_pyfunction!(stochastic_py, m)?)?;
    m.add_function(wrap_pyfunction!(vwap_py, m)?)?;
    m.add_function(wrap_pyfunction!(psar_py, m)?)?;
    Ok(())
}
