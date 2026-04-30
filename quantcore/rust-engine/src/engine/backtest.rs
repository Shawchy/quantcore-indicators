//! 回测引擎

use super::matching::MatchingEngine;
use crate::core::{Bar, Order, OrderStatus, Portfolio, Trade};
use crate::performance::PerformanceAnalyzer;
use crate::strategy::context::StrategyContext;
use pyo3::prelude::*;
use rust_decimal::Decimal;

/// 回测结果
#[derive(Debug, Clone)]
#[pyclass]
pub struct BacktestResult {
    /// 总收益率
    #[pyo3(get)]
    pub total_return: f64,

    /// 年化收益率
    #[pyo3(get)]
    pub annual_return: f64,

    /// 夏普比率
    #[pyo3(get)]
    pub sharpe_ratio: f64,

    /// 最大回撤
    #[pyo3(get)]
    pub max_drawdown: f64,

    /// 索提诺比率
    #[pyo3(get)]
    pub sortino_ratio: f64,

    /// 卡尔马比率
    #[pyo3(get)]
    pub calmar_ratio: f64,

    /// 胜率
    #[pyo3(get)]
    pub win_rate: f64,

    /// 盈亏比
    #[pyo3(get)]
    pub profit_loss_ratio: f64,

    /// 总交易次数
    #[pyo3(get)]
    pub total_trades: i32,

    /// 成交记录
    #[pyo3(get)]
    pub trades: Vec<Trade>,

    /// 账户值序列
    #[pyo3(get)]
    pub portfolio_values: Vec<f64>,
}

/// 回测配置
#[derive(Debug, Clone)]
#[pyclass]
pub struct BacktestConfig {
    /// 初始资金
    #[pyo3(get, set)]
    pub initial_capital: f64,

    /// 佣金率
    #[pyo3(get, set)]
    pub commission_rate: f64,

    /// 滑点
    #[pyo3(get, set)]
    pub slippage: f64,

    /// 印花税
    #[pyo3(get, set)]
    pub stamp_tax: f64,

    /// 最小手续费
    #[pyo3(get, set)]
    pub min_commission: f64,
}

#[pymethods]
impl BacktestConfig {
    #[new]
    #[pyo3(signature = (initial_capital=1000000.0, commission_rate=0.0003, slippage=0.001, stamp_tax=0.001, min_commission=5.0))]
    fn new(initial_capital: f64, commission_rate: f64, slippage: f64, stamp_tax: f64, min_commission: f64) -> Self {
        Self {
            initial_capital,
            commission_rate,
            slippage,
            stamp_tax,
            min_commission,
        }
    }
}

/// 回测引擎
#[pyclass]
pub struct BacktestEngine {
    /// 投资组合
    portfolio: Portfolio,

    /// 撮合引擎
    matching_engine: MatchingEngine,

    /// 成交记录
    trades: Vec<Trade>,

    /// 账户值序列
    portfolio_values: Vec<f64>,

    /// 初始资金
    initial_capital: f64,
}

#[pymethods]
impl BacktestEngine {
    /// 创建回测引擎
    #[new]
    #[pyo3(signature = (initial_capital=1000000.0))]
    fn new(initial_capital: f64) -> Self {
        Self {
            portfolio: Portfolio::new(initial_capital),
            matching_engine: MatchingEngine::new(),
            trades: Vec::new(),
            portfolio_values: Vec::new(),
            initial_capital,
        }
    }

    /// 运行回测（使用 StrategyContext）
    fn run(
        &mut self,
        bars: Vec<Bar>,
        start_time: &str,
        end_time: &str,
    ) -> PyResult<BacktestResult> {
        if bars.is_empty() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("没有数据可回测"));
        }

        // 创建策略上下文
        let mut ctx = StrategyContext::new(
            Portfolio::new(self.initial_capital),
            start_time.to_string(),
        );

        // 记录初始价值
        self.portfolio_values.push(self.initial_capital);

        // 遍历 K 线数据
        for bar in &bars {
            // 更新当前时间
            ctx.current_time = bar.timestamp.clone();

            // 获取策略上下文中的待处理订单
            let orders_to_process: Vec<Order> = ctx.get_pending_orders().to_vec();

            // 匹配订单
            for mut order in orders_to_process {
                if order.is_active() {
                    // 使用撮合引擎尝试成交
                    if let Some(trade) = self.matching_engine.match_order(&mut order, bar) {
                        // 处理成交
                        self.handle_trade(&trade)?;
                        self.trades.push(trade);
                    }
                }
            }

            // 清除已完成的订单
            ctx.clear_filled_orders();

            // 记录每日账户价值（使用 ctx 中的 portfolio，实时计算）
            let daily_value = ctx.portfolio.total_value().to_f64().unwrap_or(0.0);
            self.portfolio_values.push(daily_value);
        }

        // 计算绩效指标
        let analyzer = PerformanceAnalyzer::new(
            self.trades.clone(),
            self.portfolio_values.clone(),
            0.03, // 无风险利率 3%
        );

        let metrics = analyzer.calculate_metrics()?;

        Ok(BacktestResult {
            total_return: metrics.total_return,
            annual_return: metrics.annual_return,
            sharpe_ratio: metrics.sharpe_ratio,
            max_drawdown: metrics.max_drawdown,
            sortino_ratio: metrics.sortino_ratio,
            calmar_ratio: metrics.calmar_ratio,
            win_rate: metrics.win_rate,
            profit_loss_ratio: metrics.profit_loss_ratio,
            total_trades: metrics.total_trades,
            trades: self.trades.clone(),
            portfolio_values: self.portfolio_values.clone(),
        })
    }

    /// 处理成交
    fn handle_trade(&mut self, trade: &Trade) -> PyResult<()> {
        if trade.side == "buy" {
            self.portfolio.buy(
                &trade.symbol,
                trade.price,
                trade.quantity,
                trade.commission,
                trade.tax,
            )?;
        } else if trade.side == "sell" {
            self.portfolio.sell(
                &trade.symbol,
                trade.price,
                trade.quantity,
                trade.commission,
                trade.tax,
            )?;
        }
        Ok(())
    }
}
