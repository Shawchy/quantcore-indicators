//! 回测引擎

use super::matching::MatchingEngine;
use crate::core::{Bar, Order, OrderStatus, Portfolio, Trade};
use crate::performance::PerformanceAnalyzer;
use crate::strategy::context::StrategyContext;
use pyo3::prelude::*;
use rust_decimal::Decimal;
use rust_decimal::prelude::*;

#[derive(Debug, Clone)]
#[pyclass]
pub struct BacktestResult {
    #[pyo3(get)]
    pub total_return: f64,

    #[pyo3(get)]
    pub annual_return: f64,

    #[pyo3(get)]
    pub sharpe_ratio: f64,

    #[pyo3(get)]
    pub max_drawdown: f64,

    #[pyo3(get)]
    pub sortino_ratio: f64,

    #[pyo3(get)]
    pub calmar_ratio: f64,

    #[pyo3(get)]
    pub win_rate: f64,

    #[pyo3(get)]
    pub profit_loss_ratio: f64,

    #[pyo3(get)]
    pub total_trades: i32,

    #[pyo3(get)]
    pub trades: Vec<Trade>,

    #[pyo3(get)]
    pub portfolio_values: Vec<f64>,
}

#[derive(Debug, Clone)]
#[pyclass]
pub struct BacktestConfig {
    #[pyo3(get, set)]
    pub initial_capital: f64,

    #[pyo3(get, set)]
    pub commission_rate: f64,

    #[pyo3(get, set)]
    pub slippage: f64,

    #[pyo3(get, set)]
    pub stamp_tax: f64,

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

#[pyclass]
pub struct BacktestEngine {
    portfolio: Portfolio,
    matching_engine: MatchingEngine,
    trades: Vec<Trade>,
    portfolio_values: Vec<f64>,
    initial_capital: f64,
    slippage: f64,
}

#[pymethods]
impl BacktestEngine {
    #[new]
    #[pyo3(signature = (initial_capital=1000000.0, slippage=0.001))]
    fn new(initial_capital: f64, slippage: f64) -> Self {
        Self {
            portfolio: Portfolio::new(initial_capital),
            matching_engine: MatchingEngine::new(),
            trades: Vec::new(),
            portfolio_values: Vec::new(),
            initial_capital,
            slippage,
        }
    }

    fn run(
        &mut self,
        bars: Vec<Bar>,
        start_time: &str,
        end_time: &str,
    ) -> PyResult<BacktestResult> {
        if bars.is_empty() {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>("没有数据可回测"));
        }

        let mut ctx = StrategyContext::new(
            Portfolio::new(self.initial_capital),
            start_time.to_string(),
        );

        self.portfolio_values.push(self.initial_capital);

        let mut pending_orders: Vec<Order> = Vec::new();

        for (i, bar) in bars.iter().enumerate() {
            ctx.current_time = bar.timestamp.format("%Y-%m-%d %H:%M:%S").to_string();

            if !pending_orders.is_empty() {
                let open_price = bar.open.to_f64().unwrap_or(0.0);
                if open_price > 0.0 {
                    for mut order in pending_orders.drain(..) {
                        let fill_price = match order.side {
                            crate::core::OrderSide::Buy => open_price * (1.0 + self.slippage),
                            crate::core::OrderSide::Sell => open_price * (1.0 - self.slippage),
                        };
                        if let Some(trade) = self.matching_engine.match_order_at_price(&mut order, fill_price) {
                            self.handle_trade(&trade)?;
                            self.trades.push(trade);
                        }
                    }
                }
            }

            let orders_to_process: Vec<Order> = ctx.get_pending_orders().to_vec();
            for mut order in orders_to_process {
                if order.is_active() {
                    if let Some(trade) = self.matching_engine.match_order(&mut order, bar) {
                        self.handle_trade(&trade)?;
                        self.trades.push(trade);
                    } else {
                        pending_orders.push(order);
                    }
                }
            }

            ctx.clear_filled_orders();

            let daily_value = ctx.portfolio.total_value().to_f64().unwrap_or(0.0);
            self.portfolio_values.push(daily_value);
        }

        let analyzer = PerformanceAnalyzer::new(
            self.trades.clone(),
            self.portfolio_values.clone(),
            0.03,
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

    fn handle_trade(&mut self, trade: &Trade) -> PyResult<()> {
        let price_f64 = trade.price.to_f64().unwrap_or(0.0);
        let commission_f64 = trade.commission.to_f64().unwrap_or(0.0);
        let tax_f64 = trade.tax.to_f64().unwrap_or(0.0);
        if trade.side == "buy" {
            self.portfolio.buy(
                &trade.symbol,
                price_f64,
                trade.quantity,
                commission_f64,
                tax_f64,
            )?;
        } else if trade.side == "sell" {
            self.portfolio.sell(
                &trade.symbol,
                price_f64,
                trade.quantity,
                commission_f64,
                tax_f64,
            )?;
        }
        Ok(())
    }
}
