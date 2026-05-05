//! 风险监控器

use crate::core::Portfolio;
use pyo3::prelude::*;
use rust_decimal::Decimal;
use rust_decimal::prelude::*;

/// 风险警告级别
#[derive(Debug, Clone)]
#[pyclass]
pub enum RiskLevel {
    /// 正常
    Normal,
    /// 警告
    Warning,
    /// 危险
    Danger,
    /// 紧急
    Critical,
}

#[pymethods]
impl RiskLevel {
    fn to_string(&self) -> &str {
        match self {
            RiskLevel::Normal => "正常",
            RiskLevel::Warning => "警告",
            RiskLevel::Danger => "危险",
            RiskLevel::Critical => "紧急",
        }
    }
}

/// 风险度量
#[derive(Debug, Clone)]
#[pyclass]
pub struct RiskMetrics {
    /// 当前风险级别
    pub level: RiskLevel,
    /// 当前回撤
    pub current_drawdown: f64,
    /// 当前仓位集中度
    pub concentration: f64,
    /// 波动率
    pub volatility: f64,
    /// 风险价值 (VaR)
    pub value_at_risk: f64,
    /// 风险描述
    pub description: String,
}

#[pymethods]
impl RiskMetrics {
    fn level_str(&self) -> &str {
        self.level.to_string()
    }
}

/// 风险监控器
#[pyclass]
pub struct RiskMonitor {
    /// 警告阈值
    warning_threshold: Decimal,
    /// 危险阈值
    danger_threshold: Decimal,
    /// 紧急阈值
    critical_threshold: Decimal,
}

#[pymethods]
impl RiskMonitor {
    /// 创建风险监控器
    #[new]
    #[pyo3(signature = (warning=0.05, danger=0.10, critical=0.15))]
    fn new(warning: f64, danger: f64, critical: f64) -> Self {
        Self {
            warning_threshold: Decimal::from_f64_retain(warning).unwrap_or(Decimal::ZERO),
            danger_threshold: Decimal::from_f64_retain(danger).unwrap_or(Decimal::ZERO),
            critical_threshold: Decimal::from_f64_retain(critical).unwrap_or(Decimal::ZERO),
        }
    }

    /// 监控当前组合风险
    fn monitor(&self, portfolio: &Portfolio) -> RiskMetrics {
        let total_value = portfolio.total_value().to_f64().unwrap_or(0.0);
        let available_cash = portfolio.available_cash().to_f64().unwrap_or(0.0);
        let cash_ratio = if total_value > 0.0 {
            available_cash / total_value
        } else {
            1.0
        };

        // 计算仓位集中度
        let positions = portfolio.get_positions();
        let mut concentration = 0.0;
        if total_value > 0.0 {
            let mut max_position_value = 0.0;
            for pos in positions {
                let pos_value = pos.cost_price.to_f64().unwrap_or(0.0) * pos.quantity as f64;
                if pos_value > max_position_value {
                    max_position_value = pos_value;
                }
            }
            concentration = max_position_value / total_value;
        }

        // 评估风险级别
        let (level, description) = self.evaluate_risk(cash_ratio, concentration);

        RiskMetrics {
            level,
            current_drawdown: 0.0,
            concentration,
            volatility: 0.0,
            value_at_risk: 0.0,
            description,
        }
    }

    /// 检查是否应该触发预警
    fn should_alert(&self, portfolio: &Portfolio) -> bool {
        let metrics = self.monitor(portfolio);
        !matches!(metrics.level, RiskLevel::Normal)
    }

    fn evaluate_risk(&self, cash_ratio: f64, concentration: f64) -> (RiskLevel, String) {
        let cash_decimal = Decimal::from_f64_retain(cash_ratio).unwrap_or(Decimal::ZERO);
        let conc_decimal = Decimal::from_f64_retain(concentration).unwrap_or(Decimal::ZERO);

        // 检查紧急风险
        if conc_decimal >= self.critical_threshold {
            return (
                RiskLevel::Critical,
                format!("仓位过度集中，单只股票占比 {:.2}% 超过紧急阈值 {:.2}%", concentration * 100.0, self.critical_threshold.to_f64().unwrap_or(0.0) * 100.0),
            );
        }

        // 检查危险风险
        if conc_decimal >= self.danger_threshold {
            return (
                RiskLevel::Danger,
                format!("仓位集中度较高，单只股票占比 {:.2}% 超过危险阈值 {:.2}%", concentration * 100.0, self.danger_threshold.to_f64().unwrap_or(0.0) * 100.0),
            );
        }

        // 检查警告风险
        if conc_decimal >= self.warning_threshold {
            return (
                RiskLevel::Warning,
                format!("注意仓位集中度，单只股票占比 {:.2}% 接近警告阈值 {:.2}%", concentration * 100.0, self.warning_threshold.to_f64().unwrap_or(0.0) * 100.0),
            );
        }

        (RiskLevel::Normal, "风险水平正常".to_string())
    }
}

impl Default for RiskMonitor {
    fn default() -> Self {
        Self::new(0.05, 0.10, 0.15)
    }
}
