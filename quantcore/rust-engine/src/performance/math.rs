//! 绩效计算工具函数
//!
//! 提供回测和绩效分析共用的计算方法

/// 计算年化收益率
pub fn calculate_annual_return(daily_values: &[f64], initial_capital: f64) -> f64 {
    if daily_values.len() < 2 || initial_capital <= 0.0 {
        return 0.0;
    }

    let total_return = (daily_values[daily_values.len() - 1] - initial_capital) / initial_capital;
    let days = daily_values.len() as f64;

    (1.0 + total_return).powf(365.0 / days) - 1.0
}

/// 计算波动率（年化）
pub fn calculate_volatility(daily_values: &[f64]) -> f64 {
    if daily_values.len() < 2 {
        return 0.0;
    }

    let returns: Vec<f64> = daily_values
        .windows(2)
        .map(|w| (w[1] - w[0]) / w[0])
        .collect();

    let mean = returns.iter().sum::<f64>() / returns.len() as f64;
    let variance = returns
        .iter()
        .map(|r| (r - mean).powi(2))
        .sum::<f64>()
        / returns.len() as f64;

    variance.sqrt() * 252.0_f64.sqrt()
}

/// 计算 Sharpe 比率
pub fn calculate_sharpe_ratio(daily_values: &[f64], initial_capital: f64, risk_free_rate: f64) -> f64 {
    let vol = calculate_volatility(daily_values);
    let ann_return = calculate_annual_return(daily_values, initial_capital);

    if vol == 0.0 {
        return 0.0;
    }

    (ann_return - risk_free_rate) / vol
}

/// 计算最大回撤
pub fn calculate_max_drawdown(daily_values: &[f64]) -> f64 {
    if daily_values.is_empty() {
        return 0.0;
    }

    let mut peak = daily_values[0];
    let mut max_dd = 0.0;

    for &value in daily_values {
        if value > peak {
            peak = value;
        }
        let dd = (peak - value) / peak;
        if dd > max_dd {
            max_dd = dd;
        }
    }

    max_dd
}
