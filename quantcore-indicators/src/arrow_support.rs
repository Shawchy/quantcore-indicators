//! Apache Arrow 零拷贝数据交换模块
//!
//! 使用 Arrow 实现 Rust 和 Python 之间的高效数据传输

use arrow::array::{Float64Array, Int64Array};
use arrow::datatypes::{DataType, Field, Schema};
use arrow::record_batch::RecordBatch;
use pyo3::prelude::*;
use pyo3_arrow::PyRecordBatch;

/// 使用 Arrow 数组计算移动平均
pub fn ma_arrow(prices: &Float64Array, period: usize) -> Float64Array {
    let len = prices.len();
    if len < period {
        return Float64Array::from(vec![] as Vec<f64>);
    }

    let mut result = Vec::with_capacity(len - period + 1);

    // 计算第一个 MA
    let mut sum: f64 = (0..period).map(|i| prices.value(i)).sum();
    result.push(sum / period as f64);

    // 滑动窗口
    for i in period..len {
        sum = sum - prices.value(i - period) + prices.value(i);
        result.push(sum / period as f64);
    }

    Float64Array::from(result)
}

/// 使用 Arrow 数组计算 EMA
pub fn ema_arrow(prices: &Float64Array, period: usize) -> Float64Array {
    let len = prices.len();
    if len < period {
        return Float64Array::from(vec![] as Vec<f64>);
    }

    let multiplier = 2.0 / (period as f64 + 1.0);
    let mut result = Vec::with_capacity(len - period + 1);

    // 第一个 EMA 使用 SMA
    let initial_sma: f64 = (0..period).map(|i| prices.value(i)).sum::<f64>() / period as f64;
    result.push(initial_sma);

    // 计算后续 EMA
    for i in period..len {
        let ema = (prices.value(i) - result.last().unwrap()) * multiplier + result.last().unwrap();
        result.push(ema);
    }

    Float64Array::from(result)
}

/// 创建 OHLCV 数据的 Arrow Schema
pub fn create_ohlcv_schema() -> Schema {
    Schema::new(vec![
        Field::new("timestamp", DataType::Int64, false),
        Field::new("open", DataType::Float64, false),
        Field::new("high", DataType::Float64, false),
        Field::new("low", DataType::Float64, false),
        Field::new("close", DataType::Float64, false),
        Field::new("volume", DataType::Int64, false),
    ])
}

/// 创建 OHLCV RecordBatch
pub fn create_ohlcv_batch(
    timestamps: Vec<i64>,
    open: Vec<f64>,
    high: Vec<f64>,
    low: Vec<f64>,
    close: Vec<f64>,
    volume: Vec<i64>,
) -> RecordBatch {
    let schema = create_ohlcv_schema();

    RecordBatch::try_new(
        std::sync::Arc::new(schema),
        vec![
            std::sync::Arc::new(Int64Array::from(timestamps)),
            std::sync::Arc::new(Float64Array::from(open)),
            std::sync::Arc::new(Float64Array::from(high)),
            std::sync::Arc::new(Float64Array::from(low)),
            std::sync::Arc::new(Float64Array::from(close)),
            std::sync::Arc::new(Int64Array::from(volume)),
        ],
    )
    .unwrap()
}

/// 将计算结果转换为 Arrow RecordBatch
pub fn indicators_to_batch(
    timestamps: Vec<i64>,
    close: Vec<f64>,
    ma_values: Vec<f64>,
    rsi_values: Vec<f64>,
) -> RecordBatch {
    let schema = Schema::new(vec![
        Field::new("timestamp", DataType::Int64, false),
        Field::new("close", DataType::Float64, false),
        Field::new("ma", DataType::Float64, true),
        Field::new("rsi", DataType::Float64, true),
    ]);

    // 对齐长度（MA 和 RSI 可能比原始数据短）
    let len = ma_values.len().min(rsi_values.len());
    let offset = close.len() - len;

    RecordBatch::try_new(
        std::sync::Arc::new(schema),
        vec![
            std::sync::Arc::new(Int64Array::from(timestamps[offset..].to_vec())),
            std::sync::Arc::new(Float64Array::from(close[offset..].to_vec())),
            std::sync::Arc::new(Float64Array::from(ma_values)),
            std::sync::Arc::new(Float64Array::from(rsi_values)),
        ],
    )
    .unwrap()
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ma_arrow() {
        let prices = Float64Array::from(vec![1.0, 2.0, 3.0, 4.0, 5.0]);
        let result = ma_arrow(&prices, 3);

        assert_eq!(result.len(), 3);
        assert!((result.value(0) - 2.0).abs() < 1e-10);
        assert!((result.value(1) - 3.0).abs() < 1e-10);
        assert!((result.value(2) - 4.0).abs() < 1e-10);
    }

    #[test]
    fn test_create_ohlcv_batch() {
        let batch = create_ohlcv_batch(
            vec![1, 2, 3],
            vec![100.0, 101.0, 102.0],
            vec![101.0, 102.0, 103.0],
            vec![99.0, 100.0, 101.0],
            vec![100.0, 101.0, 102.0],
            vec![1000, 1100, 1200],
        );

        assert_eq!(batch.num_columns(), 6);
        assert_eq!(batch.num_rows(), 3);
    }
}
