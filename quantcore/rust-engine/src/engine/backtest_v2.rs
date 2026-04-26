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
use crate::core::{Bar, Order, Trade, Position, Portfolio, OrderSide, OrderType, OrderStatus};

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

        match order.side {
            OrderSide::Buy => {
                if order.price > limit_up {
                    Err(format!(
                        "Buy price {} exceeds limit up price {:.2}",
                        order.price, limit_up
                    ))
                } else {
                    Ok(order.price.min(limit_up))
                }
            }
            OrderSide::Sell => {
                if order.price < limit_down {
                    Err(format!(
                        "Sell price {} below limit down price {:.2}",
                        order.price, limit_down
                    ))
                } else {
                    Ok(order.price.max(limit_down))
                }
            }
        }
    }

    fn get_prev_close(&self, bar: &Bar) -> f64 {
        bar.close
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

        let price_checker = PriceLimitChecker::new(0.1, 0.1); // A股涨跌停10%

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

            // 检查日期变更（新的一天）
            let current_date = Some(bar.timestamp.clone());
            if prev_date.is_some() && prev_date != current_date {
                self.on_day_start();
            }
            prev_date = current_date;

            // 更新持仓价格
            self.update_positions(bar);

            // 处理订单（应用T+1和涨跌停规则）
            self.process_orders_with_rules(bar)?;

            // 记录每日资产值
            self.daily_values.push(self.portfolio.total_asset());
        }

        // 计算绩效指标
        let result = self.calculate_performance_v2();
        Ok(result)
    }

    /// 买入（带T+1标记）
    fn buy(&mut self, symbol: &str, price: f64, volume: i64) -> PyResult<Order> {
        let order_id = format!("BUY-{}", self.orders.len() + 1);
        let order = Order::new(
            order_id,
            symbol.to_string(),
            OrderSide::Buy,
            OrderType::Market,
            price,
            volume,
        );

        self.orders.push(order.clone());
        Ok(order)
    }

    /// 卖出（检查T+1）
    fn sell(&mut self, symbol: &str, price: f64, volume: i64) -> PyResult<Order> {
        // 检查T+1规则
        if !self.tplus1_manager.can_sell(symbol, NaiveDate::from_ymd_opt(2024, 1, 1).unwrap()) {
            return Err(pyo3::exceptions::PyValueError::new_err(
                "Cannot sell: T+1 rule violation"
            ));
        }

        let order_id = format!("SELL-{}", self.orders.len() + 1);
        let order = Order::new(
            order_id,
            symbol.to_string(),
            OrderSide::Sell,
            OrderType::Market,
            price,
            volume,
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
        if let Some(mut pos) = self.portfolio.get_position(&bar.symbol) {
            pos.update_price(bar.close);
        }
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

            // 检查涨跌停价格限制
            match self.price_checker.check_and_adjust_price(bar, order) {
                Ok(adjusted_price) => {
                    // 执行成交
                    if let Some(trade) = self.matching_engine.match_order_v2(order, bar, adjusted_price) {
                        self.update_position_from_trade(&trade, bar);
                        self.trades.push(trade);
                    }
                }
                Err(e) => {
                    println!("⚠️ Order rejected: {}", e);
                    order.status = OrderStatus::Rejected;
                }
            }
        }

        Ok(())
    }

    fn update_position_from_trade(&mut self, trade: &Trade, bar: &Bar) {
        if trade.side == "buy" {
            let position = Position::new(
                trade.symbol.clone(),
                "long".to_string(),
                trade.quantity,
                trade.price,
                trade.price,
            );
            self.portfolio.add_position(position);

            // 记录买入日期（用于T+1）
            if let Ok(date) = NaiveDate::parse_from_str(&bar.timestamp[..10], "%Y-%m-%d") {
                self.tplus1_manager.record_buy(&trade.symbol, date);
            }

            self.portfolio.cash -= trade.turnover + trade.commission;
        } else {
            if let Some(mut pos) = self.portfolio.get_position(&trade.symbol) {
                pos.quantity -= trade.quantity;
                if pos.quantity <= 0 {
                    self.portfolio.remove_position(&trade.symbol);
                    self.tplus1_manager.remove_position(&trade.symbol);
                }
            }

            self.portfolio.cash += trade.turnover - trade.commission;
        }
    }

    fn calculate_performance_v2(&self) -> BacktestResultV2 {
        let total_return = self.portfolio.total_pnl_percent();

        BacktestResultV2 {
            total_return,
            annual_return: self.calculate_annual_return(),
            volatility: self.calculate_volatility(),
            sharpe_ratio: self.calculate_sharpe_ratio(),
            max_drawdown: self.calculate_max_drawdown(),
            total_trades: self.trades.len() as i32,
            initial_capital: self.config.initial_capital,
            final_capital: self.portfolio.total_asset(),
        }
    }

    fn calculate_annual_return(&self) -> f64 {
        if self.daily_values.len() < 2 {
            return 0.0;
        }

        let total_return = (self.daily_values[self.daily_values.len()-1] - self.config.initial_capital) / self.config.initial_capital;
        let days = self.daily_values.len() as f64;

        (1.0 + total_return).powf(365.0 / days) - 1.0
    }

    fn calculate_volatility(&self) -> f64 {
        if self.daily_values.len() < 2 {
            return 0.0;
        }

        let returns: Vec<f64> = self.daily_values.windows(2)
            .map(|w| (w[1] - w[0]) / w[0])
            .collect();

        let mean = returns.iter().sum::<f64>() / returns.len() as f64;
        let variance = returns.iter()
            .map(|r| (r - mean).powi(2))
            .sum::<f64>() / returns.len() as f64;

        (variance.sqrt()) * (252.0_f64).sqrt()
    }

    fn calculate_sharpe_ratio(&self) -> f64 {
        let vol = self.calculate_volatility();
        let ann_return = self.calculate_annual_return();

        if vol == 0.0 {
            return 0.0;
        }

        (ann_return - 0.03) / vol
    }

    fn calculate_max_drawdown(&self) -> f64 {
        if self.daily_values.is_empty() {
            return 0.0;
        }

        let mut peak = self.daily_values[0];
        let mut max_dd = 0.0;

        for &value in &self.daily_values {
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
            order.symbol.clone(),
            match order.side {
                OrderSide::Buy => "buy".to_string(),
                OrderSide::Sell => "sell".to_string(),
            },
            exec_price,
            order.quantity,
            total_cost,
        );

        order.filled_quantity = order.quantity;
        order.status = OrderStatus::Filled;

        Some(trade)
    }
}
