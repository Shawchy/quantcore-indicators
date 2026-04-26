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
    if period < 2 || prices.len() < period {
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
    if period < 2 || prices.len() < period {
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
    if fast < 2 || slow < 2 || signal_period < 2 {
        return MACDResult {
            macd: vec![],
            signal: vec![],
            histogram: vec![],
        };
    }
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

/// RSI 指标 (Relative Strength Index)
///
/// 使用 Wilder 平滑递推法，复杂度 O(n)
pub fn rsi(prices: &[f64], period: usize) -> Vec<f64> {
    if period < 2 || prices.len() < period + 1 {
        return vec![];
    }

    let mut avg_gain = 0.0;
    let mut avg_loss = 0.0;

    for i in 1..=period {
        let change = prices[i] - prices[i - 1];
        if change > 0.0 {
            avg_gain += change;
        } else {
            avg_loss += change.abs();
        }
    }
    avg_gain /= period as f64;
    avg_loss /= period as f64;

    let mut result = Vec::with_capacity(prices.len() - period);
    result.push(if avg_loss == 0.0 {
        100.0
    } else {
        100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
    });

    for i in (period + 1)..prices.len() {
        let change = prices[i] - prices[i - 1];
        let gain = if change > 0.0 { change } else { 0.0 };
        let loss = if change < 0.0 { change.abs() } else { 0.0 };
        avg_gain = (avg_gain * (period - 1) as f64 + gain) / period as f64;
        avg_loss = (avg_loss * (period - 1) as f64 + loss) / period as f64;
        result.push(if avg_loss == 0.0 {
            100.0
        } else {
            100.0 - 100.0 / (1.0 + avg_gain / avg_loss)
        });
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
    if period < 2 {
        return BollingerBandsResult {
            upper: vec![],
            middle: vec![],
            lower: vec![],
        };
    }
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
    if period < 2
        || high_prices.len() < 2
        || high_prices.len() != low_prices.len()
        || high_prices.len() != close_prices.len()
    {
        return vec![];
    }

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
///
/// 使用预计算典型价格 + 滑动窗口，复杂度 O(n)
pub fn cci(
    high_prices: &[f64],
    low_prices: &[f64],
    close_prices: &[f64],
    period: usize,
) -> Vec<f64> {
    if period < 2
        || high_prices.len() < period
        || high_prices.len() < 2
        || high_prices.len() != low_prices.len()
        || high_prices.len() != close_prices.len()
    {
        return vec![];
    }

    let tp: Vec<f64> = high_prices
        .iter()
        .zip(low_prices.iter())
        .zip(close_prices.iter())
        .map(|((&h, &l), &c)| (h + l + c) / 3.0)
        .collect();

    let mut sum_tp: f64 = tp[..period].iter().sum();
    let mut result = Vec::with_capacity(tp.len() - period + 1);

    for i in 0..=tp.len() - period {
        let avg_tp = sum_tp / period as f64;
        let mean_deviation: f64 =
            tp[i..i + period].iter().map(|&x| (x - avg_tp).abs()).sum::<f64>() / period as f64;

        let cci_value = if mean_deviation > 0.0 {
            (tp[i + period - 1] - avg_tp) / (0.015 * mean_deviation)
        } else {
            0.0
        };
        result.push(cci_value);

        if i + period < tp.len() {
            sum_tp = sum_tp - tp[i] + tp[i + period];
        }
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
    if n < 2
        || m1 < 2
        || m2 < 2
        || high_prices.len() < n
        || high_prices.len() < 2
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
    if period < 2
        || high_prices.len() < period
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
    if period < 2
        || high_prices.len() < period + 1
        || high_prices.len() < 2
        || high_prices.len() != low_prices.len()
        || high_prices.len() != close_prices.len()
    {
        return vec![];
    }

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
    fn test_ma_period_validation() {
        let prices = vec![1.0, 2.0, 3.0];
        assert!(ma(&prices, 0).is_empty());
        assert!(ma(&prices, 1).is_empty());
        assert!(ma(&prices, 5).is_empty());
    }

    #[test]
    fn test_ma_boundary_conditions() {
        let prices = vec![1.0, 2.0];
        let result = ma(&prices, 2);
        assert_eq!(result.len(), 1);
        assert!((result[0] - 1.5).abs() < 1e-10);

        let prices = vec![10.0, 20.0, 30.0];
        let result = ma(&prices, 3);
        assert_eq!(result.len(), 1);
        assert!((result[0] - 20.0).abs() < 1e-10);
    }

    #[test]
    fn test_ema() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = ema(&prices, 3);
        assert!(!result.is_empty());
        assert_eq!(result.len(), 3);
    }

    #[test]
    fn test_ema_period_validation() {
        let prices = vec![1.0, 2.0, 3.0];
        assert!(ema(&prices, 0).is_empty());
        assert!(ema(&prices, 1).is_empty());
    }

    #[test]
    fn test_ema_boundary_conditions() {
        let prices = vec![1.0, 2.0];
        let result = ema(&prices, 2);
        assert_eq!(result.len(), 1);
        assert!((result[0] - 1.5).abs() < 1e-10);
    }

    #[test]
    fn test_ema_constant() {
        let prices = vec![5.0, 5.0, 5.0, 5.0, 5.0];
        let result = ema(&prices, 3);
        for &v in &result {
            assert!((v - 5.0).abs() < 1e-10);
        }
    }

    #[test]
    fn test_macd() {
        let prices: Vec<f64> = (0..50).map(|i| 100.0 + i as f64 * 0.5).collect();
        let result = macd(&prices, 12, 26, 9);
        assert!(!result.macd.is_empty());
        assert!(result.macd.len() >= result.signal.len());
    }

    #[test]
    fn test_macd_period_validation() {
        let prices = vec![1.0, 2.0, 3.0, 4.0, 5.0];
        let result = macd(&prices, 1, 26, 9);
        assert!(result.macd.is_empty());
    }

    #[test]
    fn test_rsi() {
        let prices = vec![100.0, 101.0, 102.0, 103.0, 104.0, 105.0];
        let result = rsi(&prices, 3);
        assert!(!result.is_empty());
        for &r in &result {
            assert!(r >= 0.0 && r <= 100.0);
        }
    }

    #[test]
    fn test_rsi_period_validation() {
        let prices = vec![1.0, 2.0, 3.0];
        assert!(rsi(&prices, 0).is_empty());
        assert!(rsi(&prices, 1).is_empty());
    }

    #[test]
    fn test_rsi_boundary_conditions() {
        let prices = vec![100.0, 101.0, 102.0];
        let result = rsi(&prices, 2);
        assert_eq!(result.len(), 1);
        assert!(result[0] >= 0.0 && result[0] <= 100.0);

        let prices = vec![100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 
                         110.0, 111.0, 112.0, 113.0, 114.0];
        let result = rsi(&prices, 14);
        assert_eq!(result.len(), 1);
        assert!(result[0] >= 0.0 && result[0] <= 100.0);
    }

    #[test]
    fn test_rsi_uptrend() {
        let prices: Vec<f64> = (0..20).map(|i| 100.0 + i as f64).collect();
        let result = rsi(&prices, 14);
        assert!(!result.is_empty());
        assert!(*result.last().unwrap() > 50.0);
    }

    #[test]
    fn test_rsi_downtrend() {
        let prices: Vec<f64> = (0..20).map(|i| 120.0 - i as f64).collect();
        let result = rsi(&prices, 14);
        assert!(!result.is_empty());
        assert!(*result.last().unwrap() < 50.0);
    }

    // ============================================================
    // RSI 边界条件专项测试
    // 验证 Issue: "RSI算法边界检查不完整"
    // 问题：可能缺少 prices.len() >= 2 的显式检查
    // ============================================================

    /// 测试1: 单元素数组 (len=1) - 应安全返回空
    #[test]
    fn test_rsi_single_element() {
        let prices = vec![100.0];
        
        // period=2, len=1: 应该返回空（数据不足）
        assert!(rsi(&prices, 2).is_empty(), "单元素+period=2应返回空");
        
        // period=14, len=1: 应该返回空
        assert!(rsi(&prices, 14).is_empty(), "单元素+period=14应返回空");
    }

    /// 测试2: 两元素数组 + 最小period (len=2, period=2)
    #[test]
    fn test_rsi_two_elements_min_period() {
        let prices = vec![100.0, 101.0];
        
        // len=2, period=2: 当前检查 len < period+1 → 2 < 3 → true，应该返回空
        let result = rsi(&prices, 2);
        assert!(result.is_empty(), "两元素+period=2应返回空（需要至少3个点计算变化）");
    }

    /// 测试3: 两元素数组 + 大period (len=2, period=14)
    #[test]
    fn test_rsi_two_elements_large_period() {
        let prices = vec![100.0, 101.0];
        
        // len=2, period=14: 明显不足，应返回空
        assert!(rsi(&prices, 14).is_empty(), "两元素+大period应返回空");
    }

    /// 测试4: 最小有效输入 (len=3, period=2)
    /// 这是理论上能产生结果的最小输入
    #[test]
    fn test_rsi_minimal_valid_input() {
        let prices = vec![100.0, 101.0, 102.0];
        
        let result = rsi(&prices, 2);
        
        // 应该产生 1 个 RSI 值 (len - period = 3 - 2 = 1)
        assert_eq!(result.len(), 1, "最小有效输入应产生1个RSI值");
        assert!(result[0].is_finite(), "RSI值应为有限数");
        assert!(result[0] >= 0.0 && result[0] <= 100.0, "RSI应在[0,100]范围");
    }

    /// 测试5: 精确边界 - len = period + 1
    #[test]
    fn test_rsi_exact_boundary_len_eq_period_plus_one() {
        let n = 15;
        let period = 14;
        let prices: Vec<f64> = (0..n).map(|i| 100.0 + i as f64 * 0.5).collect();
        
        let result = rsi(&prices, period);
        
        // 应该产生 n - period = 15 - 14 = 1 个结果
        assert_eq!(result.len(), 1, "len=period+1时应产生1个RSI值");
        assert!(result[0].is_finite());
        assert!(result[0] >= 0.0 && result[0] <= 100.0);
    }

    /// 测试6: 精确边界 - len = period (刚好不够)
    #[test]
    fn test_rsi_exact_boundary_len_eq_period() {
        let n = 14;
        let period = 14;
        let prices: Vec<f64> = (0..n).map(|i| 100.0 + i as f64).collect();
        
        // len=14, period=14: 检查 len < period+1 → 14 < 15 → true，应返回空
        let result = rsi(&prices, period);
        assert!(result.is_empty(), "len=period时数据不足，应返回空");
    }

    /// 测试7: 空数组
    #[test]
    fn test_rsi_empty_array() {
        let prices: Vec<f64> = vec![];
        
        // 空数组应该安全处理
        assert!(rsi(&prices, 2).is_empty(), "空数组应返回空");
        assert!(rsi(&prices, 14).is_empty(), "空数组+大period应返回空");
    }

    /// 测试8: 常数价格 (无变化)
    /// 当所有价格相同时，所有 change=0，avg_loss=0，RSI应为特殊值
    #[test]
    fn test_rsi_constant_prices() {
        let n = 20;
        let prices = vec![100.0; n];
        
        let result = rsi(&prices, 14);
        
        // 不为空
        assert!(!result.is_empty(), "常数价格不应返回空");
        
        // 当无变化时，avg_gain=0, avg_loss=0
        // 代码中: if avg_loss == 0 { 100.0 } else { ... }
        for (i, &val) in result.iter().enumerate() {
            assert!(
                val == 100.0,
                "常数价格的RSI[{}]应为100.0（无下跌），实际: {}", i, val
            );
        }
    }

    /// 测试9: 极端上涨趋势
    /// 连续大幅上涨，RSI应接近100
    #[test]
    fn test_rsi_extreme_uptrend() {
        let n = 20;
        let prices: Vec<f64> = (0..n).map(|i| 100.0 + i as f64 * 10.0).collect();
        
        let result = rsi(&prices, 14);
        
        assert!(!result.is_empty());
        
        // 最后一个值应该很高（接近100）
        let last_rsi = *result.last().unwrap();
        assert!(
            last_rsi > 80.0,
            "极端上涨趋势的最终RSI应>80，实际: {:.2}", last_rsi
        );
    }

    /// 测试10: 极端下跌趋势
    /// 连续大幅下跌，RSI应接近0
    #[test]
    fn test_rsi_extreme_downtrend() {
        let n = 20;
        let prices: Vec<f64> = (0..n).map(|i| 200.0 - i as f64 * 10.0).collect();
        
        let result = rsi(&prices, 14);
        
        assert!(!result.is_empty());
        
        // 最后一个值应该很低（接近0）
        let last_rsi = *result.last().unwrap();
        assert!(
            last_rsi < 20.0,
            "极端下跌趋势的最终RSI应<20，实际: {:.2}", last_rsi
        );
    }

    #[test]
    fn test_bollinger_bands() {
        let prices: Vec<f64> = (0..30).map(|i| 100.0 + (i as f64 * 0.1).sin() * 5.0).collect();
        let result = bollinger_bands(&prices, 20, 2.0);
        assert!(!result.upper.is_empty());
        assert_eq!(result.upper.len(), result.middle.len());
        assert_eq!(result.middle.len(), result.lower.len());
        for i in 0..result.upper.len() {
            assert!(result.upper[i] >= result.middle[i]);
            assert!(result.middle[i] >= result.lower[i]);
        }
    }

    #[test]
    fn test_bollinger_bands_period_validation() {
        let prices = vec![1.0, 2.0, 3.0];
        let result = bollinger_bands(&prices, 1, 2.0);
        assert!(result.upper.is_empty());
    }

    #[test]
    fn test_atr() {
        let high = vec![105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0, 115.0, 116.0, 117.0, 118.0, 119.0, 120.0];
        let low = vec![100.0, 101.0, 102.0, 103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0, 115.0];
        let close = vec![103.0, 104.0, 105.0, 106.0, 107.0, 108.0, 109.0, 110.0, 111.0, 112.0, 113.0, 114.0, 115.0, 116.0, 117.0, 118.0];
        let result = atr(&high, &low, &close, 14);
        assert!(!result.is_empty());
        for &v in &result {
            assert!(v >= 0.0);
        }
    }

    #[test]
    fn test_atr_period_validation() {
        let high = vec![105.0, 106.0];
        let low = vec![100.0, 101.0];
        let close = vec![103.0, 104.0];
        assert!(atr(&high, &low, &close, 1).is_empty());
    }

    #[test]
    fn test_cci() {
        let high: Vec<f64> = (0..25).map(|i| 105.0 + i as f64 * 0.5).collect();
        let low: Vec<f64> = (0..25).map(|i| 100.0 + i as f64 * 0.5).collect();
        let close: Vec<f64> = (0..25).map(|i| 103.0 + i as f64 * 0.5).collect();
        let result = cci(&high, &low, &close, 20);
        assert!(!result.is_empty());
    }

    #[test]
    fn test_cci_period_validation() {
        let high = vec![105.0, 106.0];
        let low = vec![100.0, 101.0];
        let close = vec![103.0, 104.0];
        assert!(cci(&high, &low, &close, 1).is_empty());
    }

    #[test]
    fn test_kdj() {
        let high: Vec<f64> = (0..15).map(|i| 105.0 + i as f64).collect();
        let low: Vec<f64> = (0..15).map(|i| 100.0 + i as f64).collect();
        let close: Vec<f64> = (0..15).map(|i| 103.0 + i as f64).collect();
        let result = kdj(&high, &low, &close, 9, 3, 3);
        assert!(!result.k.is_empty());
        assert_eq!(result.k.len(), result.d.len());
        assert_eq!(result.d.len(), result.j.len());
        for &v in &result.k {
            assert!(v >= 0.0 && v <= 100.0);
        }
        for &v in &result.d {
            assert!(v >= 0.0 && v <= 100.0);
        }
    }

    #[test]
    fn test_kdj_period_validation() {
        let high = vec![105.0];
        let low = vec![100.0];
        let close = vec![103.0];
        let result = kdj(&high, &low, &close, 1, 3, 3);
        assert!(result.k.is_empty());
    }

    #[test]
    fn test_obv() {
        let close = vec![100.0, 101.0, 100.5, 102.0, 101.5];
        let volume = vec![1000i64, 1500, 800, 2000, 1200];
        let result = obv(&close, &volume);
        assert_eq!(result.len(), 5);
        assert!((result[0] - 0.0).abs() < 1e-10);
        assert!(result[1] > result[0]);
    }

    #[test]
    fn test_obv_uptrend() {
        let close: Vec<f64> = (0..10).map(|i| 100.0 + i as f64).collect();
        let volume = vec![1000i64; 10];
        let result = obv(&close, &volume);
        for i in 1..result.len() {
            assert!(result[i] >= result[i - 1]);
        }
    }

    #[test]
    fn test_williams_r() {
        let high: Vec<f64> = (0..20).map(|i| 110.0 - i as f64 * 0.5).collect();
        let low: Vec<f64> = (0..20).map(|i| 100.0 - i as f64 * 0.5).collect();
        let close: Vec<f64> = (0..20).map(|i| 105.0 - i as f64 * 0.5).collect();
        let result = williams_r(&high, &low, &close, 14);
        assert!(!result.is_empty());
        for &v in &result {
            assert!(v >= -100.0 && v <= 0.0);
        }
    }

    #[test]
    fn test_williams_r_period_validation() {
        let high = vec![105.0];
        let low = vec![100.0];
        let close = vec![103.0];
        assert!(williams_r(&high, &low, &close, 1).is_empty());
    }

    #[test]
    fn test_adx() {
        let high: Vec<f64> = (0..30).map(|i| 110.0 + (i as f64 * 0.3).sin() * 3.0).collect();
        let low: Vec<f64> = (0..30).map(|i| 100.0 + (i as f64 * 0.3).sin() * 2.0).collect();
        let close: Vec<f64> = (0..30).map(|i| 105.0 + (i as f64 * 0.3).sin() * 2.5).collect();
        let result = adx(&high, &low, &close, 14);
        assert!(!result.is_empty());
        for &v in &result {
            assert!(v >= 0.0 && v <= 100.0);
        }
    }

    #[test]
    fn test_adx_period_validation() {
        let high = vec![105.0, 106.0];
        let low = vec![100.0, 101.0];
        let close = vec![103.0, 104.0];
        assert!(adx(&high, &low, &close, 1).is_empty());
    }

    // ============================================================
    // CCI 边界条件专项测试
    // 验证 Issue: "CCI指标滑动窗口实现不完整"
    // 问题：sum_tp 的更新逻辑在循环边界处可能出错
    // ============================================================

    /// 测试1: 最小有效数据集 (period=2, len=2)
    #[test]
    fn test_cci_minimal_data() {
        let high = vec![105.0, 106.0];
        let low = vec![100.0, 101.0];
        let close = vec![103.0, 104.0];

        let result = cci(&high, &low, &close, 2);

        // 应该产生 2 - 2 + 1 = 1 个结果
        assert_eq!(result.len(), 1, "最小数据集应该产生1个CCI值");
        
        // 结果应该是有限数
        assert!(result[0].is_finite(), "CCI值应为有限数，实际: {}", result[0]);
    }

    /// 测试2: 精确边界 (period=3, len=5)
    /// 验证：最后一次迭代 i=2 时，i+period=5 == tp.len()
    /// 此时不应更新 sum_tp（避免越界）
    #[test]
    fn test_cci_exact_boundary() {
        let high = vec![105.0, 106.0, 107.0, 108.0, 109.0];
        let low = vec![100.0, 101.0, 102.0, 103.0, 104.0];
        let close = vec![103.0, 104.0, 105.0, 106.0, 107.0];

        let result = cci(&high, &low, &close, 3);

        // 应该产生 5 - 3 + 1 = 3 个结果
        assert_eq!(result.len(), 3, "应产生3个CCI值");
        
        // 所有结果应该是有限数
        for (i, &val) in result.iter().enumerate() {
            assert!(
                val.is_finite(), 
                "CCI[{}] 应为有限数，实际: {}", i, val
            );
        }
    }

    /// 测试3: 大周期接近数据长度 (period=len-1)
    #[test]
    fn test_cci_large_period() {
        let n = 10;
        let high: Vec<f64> = (0..n).map(|i| 105.0 + i as f64 * 0.5).collect();
        let low: Vec<f64> = (0..n).map(|i| 100.0 + i as f64 * 0.5).collect();
        let close: Vec<f64> = (0..n).map(|i| 103.0 + i as f64 * 0.5).collect();

        let period = n - 1; // period = 9
        let result = cci(&high, &low, &close, period);

        // 应该产生 n - period + 1 = 10 - 9 + 1 = 2 个结果
        assert_eq!(
            result.len(), 
            2, 
            "大周期时应产生2个CCI值，实际: {}", result.len()
        );
        
        for (i, &val) in result.iter().enumerate() {
            assert!(
                val.is_finite(),
                "CCI[{}] 在大周期情况下应为有限数", i
            );
        }
    }

    /// 测试4: 常数数据 (mean_deviation = 0)
    /// 当所有价格相同时，mean_deviation=0，CCI应返回0
    #[test]
    fn test_cci_constant_data() {
        let n = 20;
        let high = vec![105.0; n];
        let low = vec![100.0; n];
        let close = vec![103.0; n];

        let result = cci(&high, &low, &close, 14);

        assert!(!result.is_empty(), "常数数据不应返回空结果");
        
        for (i, &val) in result.iter().enumerate() {
            // 当 mean_deviation = 0 时，代码应返回 0.0
            assert!(
                val == 0.0,
                "常数数据的CCI[{}]应为0.0，实际: {}", i, val
            );
        }
    }

    /// 测试5: 极端边界 - period == 数据长度
    #[test]
    fn test_cci_period_equals_length() {
        let n = 15;
        let high: Vec<f64> = (0..n).map(|i| 105.0 + i as f64 * 0.3).collect();
        let low: Vec<f64> = (0..n).map(|i| 100.0 + i as f64 * 0.3).collect();
        let close: Vec<f64> = (0..n).map(|i| 103.0 + i as f64 * 0.3).collect();

        let result = cci(&high, &low, &close, n);

        // 应该产生 n - n + 1 = 1 个结果
        assert_eq!(
            result.len(), 
            1,
            "period==len时应产生1个CCI值，实际: {}", result.len()
        );
        
        assert!(
            result[0].is_finite(),
            "唯一CCI值应为有限数，实际: {}", result[0]
        );
    }

    /// 测试6: 性能压力测试 - 大数据量
    #[test]
    fn test_cci_large_dataset_stress() {
        let n = 10000;
        
        let high: Vec<f64> = (0..n)
            .map(|i| 100.0 + 10.0 * (i as f64 * 0.01).sin())
            .collect();
        let low: Vec<f64> = (0..n)
            .map(|i| 90.0 + 8.0 * (i as f64 * 0.01).sin())
            .collect();
        let close: Vec<f64> = (0..n)
            .map(|i| 95.0 + 9.0 * (i as f64 * 0.01).sin())
            .collect();

        let result = cci(&high, &low, &close, 20);

        // 应该产生 10000 - 20 + 1 = 9981 个结果
        assert_eq!(result.len(), n - 20 + 1);
        
        // 抽样检查部分结果
        let sample_indices = [0, 100, 5000, 9980];
        for &idx in &sample_indices {
            if idx < result.len() {
                assert!(
                    result[idx].is_finite(),
                    "大数据量CCI[{}]应为有限数", idx
                );
            }
        }
    }
}
