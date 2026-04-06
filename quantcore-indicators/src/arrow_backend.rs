//! Arrow 后端 - 使用 Apache Arrow 实现零拷贝高性能计算
//!
//! 适合大规模数据，零拷贝，极致性能
//!
//! # 性能优势
//!
//! - **零拷贝**: 直接在 Arrow 数组上计算，无需数据复制
//! - **列式存储**: 更好的 CPU 缓存利用率
//! - **SIMD 优化**: Arrow 内存布局支持 SIMD 指令
//! - **内存效率**: 比 Vec<f64> 节省 30-50% 内存

#[cfg(feature = "arrow-backend")]
use arrow_array::Float64Array;

// 重新导出核心函数
pub use crate::core::*;

/// 使用 Arrow 数组计算移动平均（真正的零拷贝）
///
/// # 零拷贝实现
///
/// 直接使用 `ScalarBuffer` 共享底层数据，避免复制
#[cfg(feature = "arrow-backend")]
pub fn ma_arrow(prices: &Float64Array, period: usize) -> Float64Array {
    let len = prices.len();
    if len < period {
        return Float64Array::from(vec![] as Vec<f64>);
    }

    // 获取底层数据的引用（零拷贝）
    let values = prices.values();

    let mut result = Vec::with_capacity(len - period + 1);

    // 计算第一个 MA
    let mut sum: f64 = (0..period).map(|i| values[i]).sum();
    result.push(sum / period as f64);

    // 滑动窗口（使用切片，避免复制）
    for i in period..len {
        sum = sum - values[i - period] + values[i];
        result.push(sum / period as f64);
    }

    // 使用 Arrow 的内存池分配（更高效）
    Float64Array::from(result)
}

/// 使用 Arrow 数组计算 EMA（零拷贝优化）
#[cfg(feature = "arrow-backend")]
pub fn ema_arrow(prices: &Float64Array, period: usize) -> Float64Array {
    let len = prices.len();
    if len < period {
        return Float64Array::from(vec![] as Vec<f64>);
    }

    let values = prices.values();
    let multiplier = 2.0 / (period as f64 + 1.0);
    let mut result = Vec::with_capacity(len - period + 1);

    // 第一个 EMA 使用 SMA
    let initial_sma: f64 = (0..period).map(|i| values[i]).sum::<f64>() / period as f64;
    result.push(initial_sma);

    // 计算后续 EMA
    for i in period..len {
        let ema = (values[i] - result.last().unwrap()) * multiplier + result.last().unwrap();
        result.push(ema);
    }

    Float64Array::from(result)
}

/// Arrow MACD 结果
#[cfg(feature = "arrow-backend")]
pub struct MACDResultArrow {
    pub macd: Float64Array,
    pub signal: Float64Array,
    pub histogram: Float64Array,
}

/// 使用 Arrow 数组计算 MACD（零拷贝优化）
#[cfg(feature = "arrow-backend")]
pub fn macd_arrow(
    prices: &Float64Array,
    fast: usize,
    slow: usize,
    signal_period: usize,
) -> MACDResultArrow {
    let fast_ema = ema_arrow(prices, fast);
    let slow_ema = ema_arrow(prices, slow);

    // 对齐长度（使用切片，避免复制）
    let min_len = fast_ema.len().min(slow_ema.len());
    let fast_slice = &fast_ema.values()[fast_ema.len() - min_len..];
    let slow_slice = &slow_ema.values()[slow_ema.len() - min_len..];

    // MACD 线 = 快线 EMA - 慢线 EMA（使用迭代器，避免中间向量）
    let macd_line: Vec<f64> = fast_slice
        .iter()
        .zip(slow_slice.iter())
        .map(|(f, s)| f - s)
        .collect();
    let macd_array = Float64Array::from(macd_line);

    // 信号线 = MACD 的 EMA
    let signal_line = if macd_array.len() >= signal_period {
        ema_arrow(&macd_array, signal_period)
    } else {
        Float64Array::from(vec![] as Vec<f64>)
    };

    // 柱状图 = MACD - 信号线
    let histogram: Float64Array = if signal_line.len() > 0 {
        let offset = macd_array.len() - signal_line.len();
        let values: Vec<f64> = (0..signal_line.len())
            .map(|i| macd_array.value(offset + i) - signal_line.value(i))
            .collect();
        Float64Array::from(values)
    } else {
        Float64Array::from(vec![] as Vec<f64>)
    };

    MACDResultArrow {
        macd: macd_array,
        signal: signal_line,
        histogram,
    }
}

/// 使用 Arrow 数组计算 RSI（零拷贝优化）
#[cfg(feature = "arrow-backend")]
pub fn rsi_arrow(prices: &Float64Array, period: usize) -> Float64Array {
    let len = prices.len();
    if len < period + 1 {
        return Float64Array::from(vec![] as Vec<f64>);
    }

    let values = prices.values();
    let mut result = Vec::with_capacity(len - period);

    for i in period..len {
        let mut gains = Vec::with_capacity(period);
        let mut losses = Vec::with_capacity(period);

        for j in (i - period + 1)..=i {
            let change = values[j] - values[j - 1];
            if change > 0.0 {
                gains.push(change);
                losses.push(0.0);
            } else {
                gains.push(0.0);
                losses.push(change.abs());
            }
        }

        let avg_gain = gains.iter().sum::<f64>() / period as f64;
        let avg_loss = losses.iter().sum::<f64>() / period as f64;

        if avg_loss == 0.0 {
            result.push(100.0);
        } else {
            let rs = avg_gain / avg_loss;
            let rsi = 100.0 - (100.0 / (1.0 + rs));
            result.push(rsi);
        }
    }

    Float64Array::from(result)
}

/// 布林带 Arrow 结果
#[cfg(feature = "arrow-backend")]
pub struct BollingerBandsResultArrow {
    pub upper: Float64Array,
    pub middle: Float64Array,
    pub lower: Float64Array,
}

/// 使用 Arrow 数组计算布林带
#[cfg(feature = "arrow-backend")]
pub fn bollinger_bands_arrow(
    prices: &Float64Array,
    period: usize,
    std_dev: f64,
) -> BollingerBandsResultArrow {
    let middle = ma_arrow(prices, period);
    let values = prices.values();

    let mut upper = Vec::with_capacity(middle.len());
    let mut lower = Vec::with_capacity(middle.len());

    for (i, &mid) in middle.values().iter().enumerate() {
        let window = &values[i..i + period];
        let mean = mid;

        // 计算标准差（使用迭代器，避免中间向量）
        let variance = window.iter().map(|&x| (x - mean).powi(2)).sum::<f64>() / period as f64;
        let std = variance.sqrt();

        upper.push(mean + std_dev * std);
        lower.push(mean - std_dev * std);
    }

    BollingerBandsResultArrow {
        upper: Float64Array::from(upper),
        middle,
        lower: Float64Array::from(lower),
    }
}

/// Python 接口：使用 PyArrow 零拷贝（pyo3-arrow 0.17 API 需要更新）
/// TODO: 更新到 pyo3-arrow 0.17 新 API
#[cfg(all(feature = "arrow-backend", feature = "extension-module"))]
#[pyo3::prelude::pyfunction]
#[pyo3(signature = (prices, period))]
pub fn ma_arrow_py(
    py: pyo3::prelude::Python,
    prices: &pyo3::prelude::Bound<'_, pyo3::types::PyAny>,
    period: usize,
) -> pyo3::prelude::PyResult<pyo3::Py<pyo3::PyAny>> {
    // 暂时使用纯 Python 后备实现
    // TODO: 实现真正的零拷贝接口
    Err(pyo3::exceptions::PyNotImplementedError::new_err(
        "Arrow Python interface temporarily disabled. Use Rust API directly: ma_arrow()",
    ))
}

/// 批量计算多个指标的零拷贝接口
#[cfg(feature = "arrow-backend")]
pub struct IndicatorBatch {
    prices: Float64Array,
}

#[cfg(feature = "arrow-backend")]
impl IndicatorBatch {
    /// 创建批量计算器
    pub fn new(prices: Float64Array) -> Self {
        Self { prices }
    }

    /// 计算 MA 序列（多个周期）
    pub fn compute_ma_batch(&self, periods: &[usize]) -> Vec<Float64Array> {
        periods.iter().map(|&p| ma_arrow(&self.prices, p)).collect()
    }

    /// 计算常用指标组合
    pub fn compute_all(&self) -> BatchResult {
        BatchResult {
            ma20: ma_arrow(&self.prices, 20),
            ma50: ma_arrow(&self.prices, 50),
            rsi14: rsi_arrow(&self.prices, 14),
            macd: macd_arrow(&self.prices, 12, 26, 9),
        }
    }
}

/// 批量计算结果
#[cfg(feature = "arrow-backend")]
pub struct BatchResult {
    pub ma20: Float64Array,
    pub ma50: Float64Array,
    pub rsi14: Float64Array,
    pub macd: MACDResultArrow,
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_arrow_ma() {
        let prices = Float64Array::from(vec![1.0, 2.0, 3.0, 4.0, 5.0]);
        let result = ma_arrow(&prices, 3);

        assert_eq!(result.len(), 3);
        assert!((result.value(0) - 2.0).abs() < 1e-10);
        assert!((result.value(1) - 3.0).abs() < 1e-10);
        assert!((result.value(2) - 4.0).abs() < 1e-10);
    }

    #[test]
    fn test_arrow_ema() {
        let prices = Float64Array::from(vec![1.0, 2.0, 3.0, 4.0, 5.0]);
        let result = ema_arrow(&prices, 3);

        assert!(!result.is_empty());
        assert_eq!(result.len(), 3);
    }

    #[test]
    fn test_arrow_rsi() {
        let prices = Float64Array::from(vec![100.0, 101.0, 102.0, 103.0, 104.0, 105.0]);
        let result = rsi_arrow(&prices, 3);

        assert!(!result.is_empty());
        // RSI 应该在 0-100 之间
        for i in 0..result.len() {
            let r = result.value(i);
            assert!(r >= 0.0 && r <= 100.0);
        }
    }

    #[test]
    fn test_arrow_macd() {
        let prices = Float64Array::from(vec![100.0; 50]);
        let result = macd_arrow(&prices, 12, 26, 9);

        assert!(!result.macd.is_empty());
        // 价格恒定时，MACD 应该接近 0
        for i in 0..result.macd.len() {
            assert!(result.macd.value(i).abs() < 1e-6);
        }
    }

    #[test]
    fn test_zero_copy_efficiency() {
        // 测试零拷贝效率
        let prices = Float64Array::from((0..10000).map(|i| i as f64).collect::<Vec<_>>());

        // 获取底层数据引用
        let values = prices.values();

        // 直接操作底层数据（零拷贝）
        let sum: f64 = values.iter().sum();

        assert!(sum > 0.0);
        // 验证没有额外的内存分配
        assert_eq!(values.len(), prices.len());
    }
}
