//! 核心计算模块 - 与后端无关的纯 Rust 实现
//!
//! 这些函数是后端无关的，可以被 NumPy 和 Arrow 后端复用

/// 移动平均 (Moving Average)
///
/// # Arguments
/// * `prices` - 价格序列
/// * `period` - 周期
///
/// # Returns
/// MA 值向量
pub fn ma(prices: &[f64], period: usize) -> Vec<f64> {
    if prices.len() < period {
        return vec![];
    }

    let mut result = Vec::with_capacity(prices.len() - period + 1);

    // 计算第一个 MA
    let mut sum: f64 = prices[..period].iter().sum();
    result.push(sum / period as f64);

    // 滑动窗口计算后续 MA
    for i in period..prices.len() {
        sum = sum - prices[i - period] + prices[i];
        result.push(sum / period as f64);
    }

    result
}

/// 指数移动平均 (Exponential Moving Average)
pub fn ema(prices: &[f64], period: usize) -> Vec<f64> {
    if prices.len() < period {
        return vec![];
    }

    let multiplier = 2.0 / (period as f64 + 1.0);
    let mut result = Vec::with_capacity(prices.len() - period + 1);

    // 第一个 EMA 使用 SMA
    let initial_sma: f64 = prices[..period].iter().sum::<f64>() / period as f64;
    result.push(initial_sma);

    // 计算后续 EMA
    for i in period..prices.len() {
        let ema = (prices[i] - result.last().unwrap()) * multiplier + result.last().unwrap();
        result.push(ema);
    }

    result
}

/// MACD 指标结果
pub struct MACDResult {
    pub macd: Vec<f64>,
    pub signal: Vec<f64>,
    pub histogram: Vec<f64>,
}

/// MACD 指标
pub fn macd(prices: &[f64], fast: usize, slow: usize, signal_period: usize) -> MACDResult {
    let fast_ema = ema(prices, fast);
    let slow_ema = ema(prices, slow);

    // 对齐长度
    let min_len = fast_ema.len().min(slow_ema.len());
    let fast_ema = fast_ema[fast_ema.len() - min_len..].to_vec();
    let slow_ema = slow_ema[slow_ema.len() - min_len..].to_vec();

    // MACD 线 = 快线 EMA - 慢线 EMA
    let macd_line: Vec<f64> = fast_ema
        .iter()
        .zip(slow_ema.iter())
        .map(|(f, s)| f - s)
        .collect();

    // 信号线 = MACD 的 EMA
    let signal_line = if macd_line.len() >= signal_period {
        ema(&macd_line, signal_period)
    } else {
        vec![]
    };

    // 柱状图 = MACD - 信号线
    let histogram: Vec<f64> = if !signal_line.is_empty() {
        macd_line[macd_line.len() - signal_line.len()..]
            .iter()
            .zip(signal_line.iter())
            .map(|(m, s)| m - s)
            .collect()
    } else {
        vec![]
    };

    MACDResult {
        macd: macd_line,
        signal: signal_line,
        histogram,
    }
}

/// RSI 指标
pub fn rsi(prices: &[f64], period: usize) -> Vec<f64> {
    if prices.len() < period + 1 {
        return vec![];
    }

    let mut result = Vec::with_capacity(prices.len() - period);

    for i in period..prices.len() {
        let mut gains = Vec::with_capacity(period);
        let mut losses = Vec::with_capacity(period);

        for j in (i - period + 1)..=i {
            let change = prices[j] - prices[j - 1];
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

    result
}

/// 布林带指标结果
pub struct BollingerBandsResult {
    pub upper: Vec<f64>,
    pub middle: Vec<f64>,
    pub lower: Vec<f64>,
}

/// 布林带指标
pub fn bollinger_bands(prices: &[f64], period: usize, std_dev: f64) -> BollingerBandsResult {
    let middle = ma(prices, period);
    let mut upper = Vec::with_capacity(middle.len());
    let mut lower = Vec::with_capacity(middle.len());

    for (i, &mid) in middle.iter().enumerate() {
        let window = &prices[i..i + period];
        let mean = mid;

        // 计算标准差
        let variance = window.iter().map(|&x| (x - mean).powi(2)).sum::<f64>() / period as f64;
        let std = variance.sqrt();

        upper.push(mean + std_dev * std);
        lower.push(mean - std_dev * std);
    }

    BollingerBandsResult {
        upper,
        middle,
        lower,
    }
}

/// ATR 指标 (Average True Range)
pub fn atr(
    high_prices: &[f64],
    low_prices: &[f64],
    close_prices: &[f64],
    period: usize,
) -> Vec<f64> {
    if high_prices.len() < 2
        || high_prices.len() != low_prices.len()
        || high_prices.len() != close_prices.len()
    {
        return vec![];
    }

    // 计算真实波幅 (True Range)
    let mut tr = Vec::with_capacity(high_prices.len() - 1);
    for i in 1..high_prices.len() {
        let hl = high_prices[i] - low_prices[i];
        let hc = (high_prices[i] - close_prices[i - 1]).abs();
        let lc = (low_prices[i] - close_prices[i - 1]).abs();
        tr.push(hl.max(hc).max(lc));
    }

    // 计算 ATR (使用 EMA 平滑)
    if tr.len() < period {
        return vec![];
    }

    ema(&tr, period)
}

/// CCI 指标 (Commodity Channel Index)
pub fn cci(
    high_prices: &[f64],
    low_prices: &[f64],
    close_prices: &[f64],
    period: usize,
) -> Vec<f64> {
    if high_prices.len() < period
        || high_prices.len() != low_prices.len()
        || high_prices.len() != close_prices.len()
    {
        return vec![];
    }

    let mut result = Vec::with_capacity(high_prices.len() - period + 1);

    for i in (period - 1)..high_prices.len() {
        // 计算典型价格
        let tp: Vec<f64> = (i - period + 1..=i)
            .map(|j| (high_prices[j] + low_prices[j] + close_prices[j]) / 3.0)
            .collect();

        // 计算平均典型价格
        let avg_tp = tp.iter().sum::<f64>() / period as f64;

        // 计算平均偏差
        let mean_deviation: f64 =
            tp.iter().map(|&x| (x - avg_tp).abs()).sum::<f64>() / period as f64;

        // 计算 CCI
        let current_tp = (high_prices[i] + low_prices[i] + close_prices[i]) / 3.0;
        let cci_value = if mean_deviation > 0.0 {
            (current_tp - avg_tp) / (0.015 * mean_deviation)
        } else {
            0.0
        };

        result.push(cci_value);
    }

    result
}

/// KDJ 指标结果
pub struct KDJResult {
    pub k: Vec<f64>,
    pub d: Vec<f64>,
    pub j: Vec<f64>,
}

/// KDJ 指标
pub fn kdj(
    high_prices: &[f64],
    low_prices: &[f64],
    close_prices: &[f64],
    n: usize,
    m1: usize,
    m2: usize,
) -> KDJResult {
    if high_prices.len() < n
        || high_prices.len() != low_prices.len()
        || high_prices.len() != close_prices.len()
    {
        return KDJResult {
            k: vec![],
            d: vec![],
            j: vec![],
        };
    }

    // 计算 RSV (未成熟随机值)
    let mut rsv = Vec::with_capacity(high_prices.len() - n + 1);
    for i in (n - 1)..high_prices.len() {
        let highest = high_prices[i - n + 1..=i]
            .iter()
            .cloned()
            .fold(f64::NEG_INFINITY, f64::max);
        let lowest = low_prices[i - n + 1..=i]
            .iter()
            .cloned()
            .fold(f64::INFINITY, f64::min);
        let close = close_prices[i];

        let rsv_value = if highest != lowest {
            (close - lowest) / (highest - lowest) * 100.0
        } else {
            50.0
        };
        rsv.push(rsv_value);
    }

    // 计算 K, D, J
    let mut k = Vec::with_capacity(rsv.len());
    let mut d = Vec::with_capacity(rsv.len());
    let mut j = Vec::with_capacity(rsv.len());

    let mut prev_k = 50.0;
    let mut prev_d = 50.0;

    for &rsv_val in &rsv {
        let k_val = (m2 - 1) as f64 / m2 as f64 * prev_k + 1.0 / m2 as f64 * rsv_val;
        let d_val = (m1 - 1) as f64 / m1 as f64 * prev_d + 1.0 / m1 as f64 * k_val;
        let j_val = 3.0 * k_val - 2.0 * d_val;

        k.push(k_val);
        d.push(d_val);
        j.push(j_val);

        prev_k = k_val;
        prev_d = d_val;
    }

    KDJResult { k, d, j }
}

/// OBV 指标 (On-Balance Volume)
pub fn obv(close_prices: &[f64], volumes: &[i64]) -> Vec<f64> {
    if close_prices.len() != volumes.len() || close_prices.len() < 2 {
        return vec![];
    }

    let mut result = Vec::with_capacity(close_prices.len());
    let mut obv = 0.0;

    result.push(obv);

    for i in 1..close_prices.len() {
        if close_prices[i] > close_prices[i - 1] {
            obv += volumes[i] as f64;
        } else if close_prices[i] < close_prices[i - 1] {
            obv -= volumes[i] as f64;
        }
        result.push(obv);
    }

    result
}

/// Williams %R 指标
pub fn williams_r(
    high_prices: &[f64],
    low_prices: &[f64],
    close_prices: &[f64],
    period: usize,
) -> Vec<f64> {
    if high_prices.len() < period
        || high_prices.len() != low_prices.len()
        || high_prices.len() != close_prices.len()
    {
        return vec![];
    }

    let mut result = Vec::with_capacity(high_prices.len() - period + 1);

    for i in (period - 1)..high_prices.len() {
        let highest = high_prices[i - period + 1..=i]
            .iter()
            .cloned()
            .fold(f64::NEG_INFINITY, f64::max);
        let lowest = low_prices[i - period + 1..=i]
            .iter()
            .cloned()
            .fold(f64::INFINITY, f64::min);
        let close = close_prices[i];

        let wr = if highest != lowest {
            (highest - close) / (highest - lowest) * -100.0
        } else {
            -50.0
        };

        result.push(wr);
    }

    result
}

/// ADX 指标 (Average Directional Index)
pub fn adx(
    high_prices: &[f64],
    low_prices: &[f64],
    close_prices: &[f64],
    period: usize,
) -> Vec<f64> {
    if high_prices.len() < period + 1
        || high_prices.len() != low_prices.len()
        || high_prices.len() != close_prices.len()
    {
        return vec![];
    }

    // 计算 +DI 和 -DI
    let mut plus_dm = Vec::with_capacity(high_prices.len() - 1);
    let mut minus_dm = Vec::with_capacity(high_prices.len() - 1);
    let mut tr = Vec::with_capacity(high_prices.len() - 1);

    for i in 1..high_prices.len() {
        let plus_diff = high_prices[i] - high_prices[i - 1];
        let minus_diff = low_prices[i - 1] - low_prices[i];

        let (pdm, mdm) = if plus_diff > minus_diff && plus_diff > 0.0 {
            (plus_diff, 0.0)
        } else if minus_diff > plus_diff && minus_diff > 0.0 {
            (0.0, minus_diff)
        } else {
            (0.0, 0.0)
        };

        plus_dm.push(pdm);
        minus_dm.push(mdm);

        let hl = high_prices[i] - low_prices[i];
        let hc = (high_prices[i] - close_prices[i - 1]).abs();
        let lc = (low_prices[i] - close_prices[i - 1]).abs();
        tr.push(hl.max(hc).max(lc));
    }

    // 计算平滑的 +DM, -DM, TR
    let mut smoothed_plus_dm = Vec::with_capacity(plus_dm.len());
    let mut smoothed_minus_dm = Vec::with_capacity(minus_dm.len());
    let mut smoothed_tr = Vec::with_capacity(tr.len());

    // 第一个值为初始和
    let mut sum_plus: f64 = plus_dm[..period].iter().sum();
    let mut sum_minus: f64 = minus_dm[..period].iter().sum();
    let mut sum_tr: f64 = tr[..period].iter().sum();

    smoothed_plus_dm.push(sum_plus);
    smoothed_minus_dm.push(sum_minus);
    smoothed_tr.push(sum_tr);

    // 平滑
    for i in period..plus_dm.len() {
        sum_plus = sum_plus - plus_dm[i - period] + plus_dm[i];
        sum_minus = sum_minus - minus_dm[i - period] + minus_dm[i];
        sum_tr = sum_tr - tr[i - period] + tr[i];

        smoothed_plus_dm.push(sum_plus);
        smoothed_minus_dm.push(sum_minus);
        smoothed_tr.push(sum_tr);
    }

    // 计算 +DI 和 -DI
    let plus_di: Vec<f64> = smoothed_plus_dm
        .iter()
        .zip(smoothed_tr.iter())
        .map(|(pdm, tr)| if *tr > 0.0 { pdm / tr * 100.0 } else { 0.0 })
        .collect();

    let minus_di: Vec<f64> = smoothed_minus_dm
        .iter()
        .zip(smoothed_tr.iter())
        .map(|(mdm, tr)| if *tr > 0.0 { mdm / tr * 100.0 } else { 0.0 })
        .collect();

    // 计算 DX
    let mut dx = Vec::with_capacity(plus_di.len());
    for (pdi, mdi) in plus_di.iter().zip(minus_di.iter()) {
        let sum = pdi + mdi;
        let diff = (pdi - mdi).abs();
        dx.push(if sum > 0.0 { diff / sum * 100.0 } else { 0.0 });
    }

    // 计算 ADX (DX 的 EMA)
    if dx.len() < period {
        return vec![];
    }

    ema(&dx, period)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_ma() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = ma(&prices, 3);
        assert_eq!(result.len(), 3);
        assert!((result[0] - 2.0).abs() < 1e-10);
        assert!((result[1] - 3.0).abs() < 1e-10);
        assert!((result[2] - 4.0).abs() < 1e-10);
    }

    #[test]
    fn test_ema() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = ema(&prices, 3);
        assert!(!result.is_empty());
        assert_eq!(result.len(), 3);
    }

    #[test]
    fn test_rsi() {
        let prices = vec![100.0, 101.0, 102.0, 103.0, 104.0, 105.0];
        let result = rsi(&prices, 3);
        assert!(!result.is_empty());
        // RSI 应该在 0-100 之间
        for &r in &result {
            assert!(r >= 0.0 && r <= 100.0);
        }
    }
}
