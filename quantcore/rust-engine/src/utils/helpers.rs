//! 辅助函数

use rust_decimal::Decimal;

/// 格式化金额
pub fn format_amount(amount: Decimal) -> String {
    format!("¥{:.2}", amount)
}

/// 格式化百分比
pub fn format_percent(value: Decimal) -> String {
    format!("{:.2}%", value * Decimal::from(100))
}

/// 四舍五入到指定位数
pub fn round_to(value: Decimal, decimals: u32) -> Decimal {
    let multiplier = Decimal::from(10_i128.pow(decimals));
    (value * multiplier).round() / multiplier
}
