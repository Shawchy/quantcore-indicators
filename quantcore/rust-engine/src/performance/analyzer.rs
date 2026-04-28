//! 绩效分析器

use super::metrics::PerformanceMetrics;
use crate::core::{OrderSide, Trade};
use pyo3::prelude::*;

/// 绩效分析器
#[pyclass]
pub struct PerformanceAnalyzer {
    /// 成交记录
    trades: Vec<Trade>,

    /// 账户值序列
    portfolio_values: Vec<f64>,

    /// 无风险利率（年化）
    risk_free_rate: f64,

    /// 基准收益率序列（可选，用于计算超额收益）
    /// 如果为空，则使用无风险利率作为基准
    benchmark_returns: Vec<f64>,
}

#[pymethods]
impl PerformanceAnalyzer {
    /// 创建绩效分析器
    #[new]
    #[pyo3(signature = (trades, portfolio_values, risk_free_rate=0.03, benchmark_returns=None))]
    fn new(
        trades: Vec<Trade>, 
        portfolio_values: Vec<f64>, 
        risk_free_rate: f64,
        benchmark_returns: Option<Vec<f64>>,
    ) -> Self {
        Self {
            trades,
            portfolio_values,
            risk_free_rate,
            benchmark_returns: benchmark_returns.unwrap_or_default(),
        }
    }

    /// 计算绩效指标
    fn calculate_metrics(&self) -> PyResult<PerformanceMetrics> {
        let total_return = self.calculate_total_return();
        let annual_return = self.calculate_annual_return();
        let volatility = self.calculate_volatility();
        let sharpe = self.calculate_sharpe_ratio();
        let max_dd = self.calculate_max_drawdown();
        let sortino = self.calculate_sortino_ratio();
        let calmar = if max_dd.abs() > 0.0001 {
            annual_return / max_dd.abs()
        } else {
            0.0
        };
        let (win_rate, profit_loss_ratio, total_trades, winning, losing) = self.calculate_trade_stats();

        // 计算基准收益和超额收益
        let benchmark_return = self.calculate_benchmark_return();
        let excess_return = total_return - benchmark_return;

        Ok(PerformanceMetrics {
            total_return,
            annual_return,
            benchmark_return,
            excess_return,
            volatility,
            sharpe_ratio: sharpe,
            max_drawdown: max_dd,
            sortino_ratio: sortino,
            calmar_ratio: calmar,
            win_rate,
            profit_loss_ratio,
            total_trades,
        })
    }

    /// 计算夏普比率
    fn sharpe_ratio(&self) -> f64 {
        self.calculate_sharpe_ratio()
    }

    /// 计算最大回撤
    fn max_drawdown(&self) -> f64 {
        self.calculate_max_drawdown()
    }

    /// 计算总收益率
    fn calculate_total_return(&self) -> f64 {
        if self.portfolio_values.len() < 2 {
            return 0.0;
        }
        let initial = self.portfolio_values[0];
        let final_val = self.portfolio_values[self.portfolio_values.len() - 1];
        if initial == 0.0 {
            return 0.0;
        }
        (final_val - initial) / initial
    }

    /// 计算年化收益率
    fn calculate_annual_return(&self) -> f64 {
        let total_return = self.calculate_total_return();
        let days = self.portfolio_values.len();
        if days < 2 {
            return 0.0;
        }
        // 假设每个 portfolio_value 代表一天
        let years = days as f64 / 252.0; // 252 个交易日/年
        if years <= 0.0 || total_return <= -1.0 {
            return 0.0;
        }
        (1.0 + total_return).powf(1.0 / years) - 1.0
    }

    /// 计算波动率（年化）
    fn calculate_volatility(&self) -> f64 {
        if self.portfolio_values.len() < 2 {
            return 0.0;
        }

        // 计算日收益率
        let mut returns = Vec::with_capacity(self.portfolio_values.len() - 1);
        for i in 1..self.portfolio_values.len() {
            let prev = self.portfolio_values[i - 1];
            if prev == 0.0 {
                returns.push(0.0);
            } else {
                returns.push((self.portfolio_values[i] - prev) / prev);
            }
        }

        // 计算标准差
        let mean = returns.iter().sum::<f64>() / returns.len() as f64;
        let variance = returns.iter().map(|r| (r - mean).powi(2)).sum::<f64>() / returns.len() as f64;
        let daily_std = variance.sqrt();

        // 年化波动率
        daily_std * (252.0_f64).sqrt()
    }

    /// 计算夏普比率
    fn calculate_sharpe_ratio(&self) -> f64 {
        let annual_return = self.calculate_annual_return();
        let volatility = self.calculate_volatility();
        if volatility == 0.0 {
            return 0.0;
        }
        (annual_return - self.risk_free_rate) / volatility
    }

    /// 计算最大回撤
    fn calculate_max_drawdown(&self) -> f64 {
        if self.portfolio_values.is_empty() {
            return 0.0;
        }

        let mut peak = self.portfolio_values[0];
        let mut max_dd = 0.0;

        for &value in &self.portfolio_values {
            if value > peak {
                peak = value;
            }
            let drawdown = (peak - value) / peak;
            if drawdown > max_dd {
                max_dd = drawdown;
            }
        }

        max_dd
    }

    /// 计算索提诺比率
    fn calculate_sortino_ratio(&self) -> f64 {
        if self.portfolio_values.len() < 2 {
            return 0.0;
        }

        // 计算下行标准差
        let mut downside_returns = Vec::new();
        for i in 1..self.portfolio_values.len() {
            let prev = self.portfolio_values[i - 1];
            if prev == 0.0 {
                continue;
            }
            let ret = (self.portfolio_values[i] - prev) / prev;
            if ret < 0.0 {
                downside_returns.push(ret);
            }
        }

        if downside_returns.is_empty() {
            return 0.0;
        }

        let downside_variance = downside_returns.iter().map(|r| r.powi(2)).sum::<f64>() / downside_returns.len() as f64;
        let downside_std = downside_variance.sqrt() * (252.0_f64).sqrt();

        if downside_std == 0.0 {
            return 0.0;
        }

        let annual_return = self.calculate_annual_return();
        (annual_return - self.risk_free_rate) / downside_std
    }

    /// 计算交易统计
    fn calculate_trade_stats(&self) -> (f64, f64, i32, i32, i32) {
        let total_trades = self.trades.len() as i32;
        if total_trades == 0 {
            return (0.0, 0.0, 0, 0, 0);
        }

        let mut winning = 0;
        let mut losing = 0;
        let mut total_profit = 0.0;
        let mut total_loss = 0.0;

        // 按 symbol 配对买卖
        use std::collections::HashMap;
        let mut position_tracker: HashMap<String, (f64, i64)> = HashMap::new();

        for trade in &self.trades {
            let symbol = trade.symbol.clone();
            let price = trade.price.to_f64().unwrap_or(0.0);
            let qty = trade.quantity;

            let entry = position_tracker.entry(symbol).or_insert((0.0, 0));

            if trade.side == "buy" {
                // 加权平均成本
                let total_cost = entry.0 * entry.1 as f64 + price * qty as f64;
                entry.1 += qty;
                if entry.1 > 0 {
                    entry.0 = total_cost / entry.1 as f64;
                }
            } else if trade.side == "sell" {
                if entry.1 > 0 {
                    let pnl = (price - entry.0) * qty as f64;
                    if pnl > 0.0 {
                        winning += 1;
                        total_profit += pnl;
                    } else {
                        losing += 1;
                        total_loss += pnl.abs();
                    }
                    entry.1 -= qty;
                }
            }
        }

        let win_rate = if total_trades > 0 {
            winning as f64 / total_trades as f64
        } else {
            0.0
        };

        let profit_loss_ratio = if losing > 0 && total_loss > 0.0 {
            (total_profit / winning as f64) / (total_loss / losing as f64)
        } else if winning > 0 {
            f64::INFINITY
        } else {
            0.0
        };

        (win_rate, profit_loss_ratio, total_trades, winning, losing)
    }

    /// 计算基准收益率
    /// 
    /// 计算逻辑：
    /// 1. 如果提供了 benchmark_returns 序列，计算累计收益率（需处理长度匹配）
    /// 2. 如果未提供，使用无风险利率作为基准（按 252 个交易日年化）
    fn calculate_benchmark_return(&self) -> f64 {
        if !self.benchmark_returns.is_empty() {
            // 使用提供的基准收益率序列计算累计收益
            // 假设 benchmark_returns 是日收益率序列
            let benchmark_len = self.benchmark_returns.len();
            let portfolio_len = self.portfolio_values.len();
            
            // 处理长度不匹配的情况
            if benchmark_len != portfolio_len {
                // 记录警告（实际应用中应该使用 logger）
                eprintln!(
                    "警告：基准序列长度 ({}) 与投资组合期数 ({}) 不匹配，将使用较短者",
                    benchmark_len, portfolio_len
                );
                
                // 使用较短的长度，避免数据错位
                let actual_len = benchmark_len.min(portfolio_len);
                self.benchmark_returns
                    .iter()
                    .take(actual_len)
                    .fold(1.0, |acc, &r| acc * (1.0 + r)) - 1.0
            } else {
                // 长度匹配，直接计算
                self.benchmark_returns.iter().fold(1.0, |acc, &r| acc * (1.0 + r)) - 1.0
            }
        } else {
            // 使用无风险利率作为基准（按 252 个交易日年化）
            // 金融行业标准：252 个交易日/年
            let trading_days = self.portfolio_values.len().max(1) as f64;
            let years = trading_days / 252.0;
            (1.0 + self.risk_free_rate).powf(years) - 1.0
        }
    }
}
