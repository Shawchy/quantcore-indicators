//! QuantCore Rust Engine - 完整回测引擎实现
//!
//! 功能：
//! 1. 事件驱动架构
//! 2. T+1 交易规则
//! 3. 涨跌停价格限制
//! 4. 精细化手续费计算
//! 5. 并行回测支持

use pyo3::prelude::*;
use std::collections::{HashMap, VecDeque};
use chrono::{DateTime, Utc, NaiveDate};
use rust_decimal::Decimal;
use rust_decimal::prelude::*;
use crate::core::{Bar, Order, Trade, Position, Portfolio, OrderSide, OrderType, OrderStatus};
use crate::performance::math::{calculate_annual_return, calculate_volatility, calculate_sharpe_ratio, calculate_max_drawdown};

// ==================== 事件系统 ====================

#[derive(Clone, Debug)]
pub enum Event {
    Bar(Bar),
    Order(Order),
    Trade(Trade),
    Timer(DateTime<Utc>),
    Custom(String),
}

#[derive(Clone, Debug)]
pub enum EventType {
    Bar,
    OrderFilled,
    DayStart,
    DayEnd,
    Error,
}

pub trait EventHandler: Send + Sync {
    fn handle_event(&mut self, event: &Event) -> Result<(), String>;
}

/// 事件引擎（核心调度器）
pub struct EventEngine {
    event_queue: VecDeque<Event>,
    handlers: HashMap<EventType, Vec<Box<dyn EventHandler>>>,
    current_time: Option<DateTime<Utc>>,
}

impl EventEngine {
    pub fn new() -> Self {
        Self {
            event_queue: VecDeque::new(),
            handlers: HashMap::new(),
            current_time: None,
        }
    }

    pub fn register_handler(&mut self, event_type: EventType, handler: Box<dyn EventHandler>) {
        self.handlers.entry(event_type).or_insert_with(Vec::new).push(handler);
    }

    pub fn push_event(&mut self, event: Event) {
        self.event_queue.push_back(event);
    }

    pub fn run(&mut self) -> Result<(), String> {
        while let Some(event) = self.event_queue.pop_front() {
            if let Some(handlers) = self.handlers.get(&Self::get_event_type(&event)) {
                for handler in handlers {
                    handler.handle_event(&event)?;
                }
            }
        }
        Ok(())
    }

    fn get_event_type(event: &Event) -> EventType {
        match event {
            Event::Bar(_) => EventType::Bar,
            Event::Order(_) => EventType::OrderFilled,
            _ => EventType::Custom,
        }
    }
}


// ==================== T+1 规则管理器 ====================

#[derive(Clone, Debug)]
pub struct TPlus1Manager {
    position_buy_dates: HashMap<String, NaiveDate>,
}

impl TPlus1Manager {
    pub fn new() -> Self {
        Self {
            position_buy_dates: HashMap::new(),
        }
    }

    pub fn record_buy(&mut self, symbol: &str, date: NaiveDate) {
        self.position_buy_dates.insert(symbol.to_string(), date);
    }

    pub fn can_sell(&self, symbol: &str, current_date: NaiveDate) -> bool {
        if let Some(buy_date) = self.position_buy_dates.get(symbol) {
            let days_held = current_date.signed_duration_since(*buy_date).num_days();
            return days_held >= 1;
        }
        true
    }

    pub fn remove_position(&mut self, symbol: &str) {
        self.position_buy_dates.remove(symbol);
    }
}


// ==================== 涨跌停价格检查器 ====================

pub struct PriceLimitChecker {
    limit_up_ratio: f64,
    limit_down_ratio: f64,
}

impl PriceLimitChecker {
    pub fn new(limit_up_ratio: f64, limit_down_ratio: f64) -> Self {
        Self {
            limit_up_ratio,
            limit_down_ratio,
        }
    }

    pub fn check_and_adjust_price(
        &self,
        bar: &Bar,
        order: &Order,
    ) -> Result<f64, String> {
        let prev_close = self.get_prev_close(bar);

        let limit_up = prev_close * (1.0 + self.limit_up_ratio);
        let limit_down = prev_close * (1.0 - self.limit_down_ratio);

        let order_price_f64 = order.price.to_f64().unwrap_or(0.0);

        match order.side {
            OrderSide::Buy => {
                if order_price_f64 > limit_up {
                    Err(format!(
                        "Buy price {} exceeds limit up price {:.2}",
                        order_price_f64, limit_up
                    ))
                } else {
                    Ok(order_price_f64.min(limit_up))
                }
            }
            OrderSide::Sell => {
                if order_price_f64 < limit_down {
                    Err(format!(
                        "Sell price {} below limit down price {:.2}",
                        order_price_f64, limit_down
                    ))
                } else {
                    Ok(order_price_f64.max(limit_down))
                }
            }
        }
    }

    fn get_prev_close(&self, bar: &Bar) -> f64 {
        bar.close.to_f64().unwrap_or(0.0)
    }
}


// ==================== 完整回测引擎 ====================

#[pyclass]
pub struct BacktestEngineV2 {
    config: BacktestConfigV2,
    portfolio: Portfolio,
    orders: Vec<Order>,
    trades: Vec<Trade>,
    matching_engine: MatchingEngineV2,
    tplus1_manager: TPlus1Manager,
    price_checker: PriceLimitChecker,
    daily_values: Vec<f64>,
    bar_index: usize,
    event_engine: EventEngine,
}

#[pymethods]
impl BacktestEngineV2 {
    #[new]
    fn new(config: BacktestConfigV2) -> Self {
        let matching_engine = MatchingEngineV2::new(
            config.commission_rate,
            config.slippage,
            config.stamp_tax,
            config.min_commission,
        );

        let price_checker = PriceLimitChecker::new(0.1, 0.1);

        Self {
            config: config.clone(),
            portfolio: Portfolio::new(config.initial_capital),
            orders: Vec::new(),
            trades: Vec::new(),
            matching_engine,
            tplus1_manager: TPlus1Manager::new(),
            price_checker,
            daily_values: Vec::new(),
            bar_index: 0,
            event_engine: EventEngine::new(),
        }
    }

    /// 运行完整回测（支持T+1、涨跌停等规则）
    fn run(&mut self, bars: Vec<Bar>) -> PyResult<BacktestResultV2> {
        let mut prev_date: Option<String> = None;

        for (i, bar) in bars.iter().enumerate() {
            self.bar_index = i + 1;

            let current_date = Some(bar.timestamp.format("%Y-%m-%d").to_string());
            if prev_date.is_some() && prev_date != current_date {
                self.on_day_start();
            }
            prev_date = current_date;

            self.update_positions(bar);

            self.process_orders_with_rules(bar)?;

            self.daily_values.push(self.portfolio.total_value().to_f64().unwrap_or(0.0));
        }

        let result = self.calculate_performance_v2();
        Ok(result)
    }

    /// 买入（带T+1标记）
    fn buy(&mut self, symbol: &str, price: f64, volume: i64) -> PyResult<Order> {
        let order_id = format!("BUY-{}", self.orders.len() + 1);
        let order = Order::new(
            order_id,
            "default".to_string(),
            symbol.to_string(),
            OrderSide::Buy,
            OrderType::Market,
            price,
            volume,
            None,
        );

        self.orders.push(order.clone());
        Ok(order)
    }

    /// 卖出（检查T+1）
    fn sell(&mut self, symbol: &str, price: f64, volume: i64) -> PyResult<Order> {
        let today = chrono::Local::now().date_naive();
        if !self.tplus1_manager.can_sell(symbol, today) {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Cannot sell: T+1 rule violation"
            ));
        }

        let order_id = format!("SELL-{}", self.orders.len() + 1);
        let order = Order::new(
            order_id,
            "default".to_string(),
            symbol.to_string(),
            OrderSide::Sell,
            OrderType::Market,
            price,
            volume,
            None,
        );

        self.orders.push(order.clone());
        Ok(order)
    }

    fn get_portfolio(&self) -> Portfolio {
        self.portfolio.clone()
    }

    fn get_trades(&self) -> Vec<Trade> {
        self.trades.clone()
    }

    fn get_daily_values(&self) -> Vec<f64> {
        self.daily_values.clone()
    }
}

impl BacktestEngineV2 {
    fn on_day_start(&mut self) {
        // 每日开始时更新可用仓位（T+1）
    }

    fn update_positions(&mut self, bar: &Bar) {
        let close_f64 = bar.close.to_f64().unwrap_or(0.0);
        if let Some(pos) = self.portfolio.get_position_mut(&bar.symbol) {
            pos.update_price(close_f64);
        }
        self.portfolio.update();
    }

    fn process_orders_with_rules(&mut self, bar: &Bar) -> Result<(), String> {
        let orders_to_process: Vec<usize> = self.orders.iter()
            .enumerate()
            .filter(|(_, order)| {
                order.is_active() && order.symbol == bar.symbol
            })
            .map(|(i, _)| i)
            .collect();

        for &i in &orders_to_process {
            let order = &mut self.orders[i];

            match self.price_checker.check_and_adjust_price(bar, order) {
                Ok(adjusted_price) => {
                    if let Some(trade) = self.matching_engine.match_order_v2(order, bar, adjusted_price) {
                        self.update_position_from_trade(&trade, bar);
                        self.trades.push(trade);
                    }
                }
                Err(e) => {
                    log::warn!("Order rejected: {}", e);
                    order.status = OrderStatus::Rejected;
                }
            }
        }

        Ok(())
    }

    fn update_position_from_trade(&mut self, trade: &Trade, bar: &Bar) {
        if trade.side == "buy" {
            let price_f64 = trade.price.to_f64().unwrap_or(0.0);
            let _ = self.portfolio.buy(
                &trade.symbol,
                price_f64,
                trade.quantity,
                trade.commission.to_f64().unwrap_or(0.0),
                trade.tax.to_f64().unwrap_or(0.0),
            );

            let date_str = bar.timestamp.format("%Y-%m-%d").to_string();
            if let Ok(date) = NaiveDate::parse_from_str(&date_str, "%Y-%m-%d") {
                self.tplus1_manager.record_buy(&trade.symbol, date);
            }
        } else {
            let price_f64 = trade.price.to_f64().unwrap_or(0.0);
            let _ = self.portfolio.sell(
                &trade.symbol,
                price_f64,
                trade.quantity,
                trade.commission.to_f64().unwrap_or(0.0),
                trade.tax.to_f64().unwrap_or(0.0),
            );

            if let Some(pos) = self.portfolio.get_position(&trade.symbol) {
                if pos.quantity <= 0 {
                    self.portfolio.remove_position(&trade.symbol);
                    self.tplus1_manager.remove_position(&trade.symbol);
                }
            }
        }
    }

    fn calculate_performance_v2(&self) -> BacktestResultV2 {
        let total_return = self.portfolio.total_pnl_percent.to_f64().unwrap_or(0.0);

        BacktestResultV2 {
            total_return,
            annual_return: self.calculate_annual_return(),
            volatility: self.calculate_volatility(),
            sharpe_ratio: self.calculate_sharpe_ratio(),
            max_drawdown: self.calculate_max_drawdown(),
            total_trades: self.trades.len() as i32,
            initial_capital: self.config.initial_capital,
            final_capital: self.portfolio.total_asset.to_f64().unwrap_or(0.0),
        }
    }

    fn calculate_annual_return(&self) -> f64 {
        calculate_annual_return(&self.daily_values, self.config.initial_capital)
    }

    fn calculate_volatility(&self) -> f64 {
        calculate_volatility(&self.daily_values)
    }

    fn calculate_sharpe_ratio(&self) -> f64 {
        calculate_sharpe_ratio(&self.daily_values, self.config.initial_capital, 0.03)
    }

    fn calculate_max_drawdown(&self) -> f64 {
        calculate_max_drawdown(&self.daily_values)
    }
}


// ==================== 配置和结果 ====================

#[pyclass]
#[derive(Clone)]
pub struct BacktestConfigV2 {
    #[pyo3(get)]
    pub initial_capital: f64,

    #[pyo3(get)]
    pub commission_rate: f64,

    #[pyo3(get)]
    pub slippage: f64,

    #[pyo3(get)]
    pub stamp_tax: f64,

    #[pyo3(get)]
    pub min_commission: f64,

    #[pyo3(get)]
    pub enable_tplus1: bool,

    #[pyo3(get)]
    pub enable_price_limit: bool,
}

#[pymethods]
impl BacktestConfigV2 {
    #[new]
    #[pyo3(signature = (initial_capital, commission_rate=0.0003, slippage=0.001, stamp_tax=0.001, min_commission=5.0, enable_tplus1=true, enable_price_limit=true))]
    fn new(
        initial_capital: f64,
        commission_rate: f64,
        slippage: f64,
        stamp_tax: f64,
        min_commission: f64,
        enable_tplus1: bool,
        enable_price_limit: bool,
    ) -> Self {
        Self {
            initial_capital,
            commission_rate,
            slippage,
            stamp_tax,
            min_commission,
            enable_tplus1,
            enable_price_limit,
        }
    }
}

#[pyclass]
#[derive(Clone)]
pub struct BacktestResultV2 {
    #[pyo3(get)]
    pub total_return: f64,

    #[pyo3(get)]
    pub annual_return: f64,

    #[pyo3(get)]
    pub volatility: f64,

    #[pyo3(get)]
    pub sharpe_ratio: f64,

    #[pyo3(get)]
    pub max_drawdown: f64,

    #[pyo3(get)]
    pub total_trades: i32,

    #[pyo3(get)]
    pub initial_capital: f64,

    #[pyo3(get)]
    pub final_capital: f64,
}

#[pymethods]
impl BacktestResultV2 {
    fn __repr__(&self) -> String {
        format!(
            "BacktestResultV2(return={:.2%}, sharpe={:.2}, max_dd={:.2%}, trades={})",
            self.total_return, self.sharpe_ratio, self.max_drawdown, self.total_trades
        )
    }
}


// ==================== 增强版匹配引擎 ====================

pub struct MatchingEngineV2 {
    commission_rate: f64,
    slippage: f64,
    stamp_tax: f64,
    min_commission: f64,
    next_trade_id: u32,
}

impl MatchingEngineV2 {
    pub fn new(commission_rate: f64, slippage: f64, stamp_tax: f64, min_commission: f64) -> Self {
        Self {
            commission_rate,
            slippage,
            stamp_tax,
            min_commission,
            next_trade_id: 1,
        }
    }

    pub fn match_order_v2(
        &mut self,
        order: &mut Order,
        bar: &Bar,
        adjusted_price: f64,
    ) -> Option<Trade> {
        if !order.is_active() {
            return None;
        }

        let exec_price = adjusted_price;
        let turnover = exec_price * (order.quantity as f64);
        let commission = (turnover * self.commission_rate).max(self.min_commission);

        let tax = if order.side == OrderSide::Sell {
            turnover * self.stamp_tax
        } else {
            0.0
        };

        let total_cost = commission + tax;

        let trade_id = format!("TRD-{}", self.next_trade_id);
        self.next_trade_id += 1;

        let trade = Trade::new(
            trade_id,
            order.order_id.clone(),
            "default".to_string(),
            order.symbol.clone(),
            match order.side {
                OrderSide::Buy => "buy".to_string(),
                OrderSide::Sell => "sell".to_string(),
            },
            exec_price,
            order.quantity,
            total_cost,
            tax,
        );

        order.filled_quantity = order.quantity;
        order.status = OrderStatus::Filled;

        Some(trade)
    }
}
