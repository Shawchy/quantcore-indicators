//! QuantCore Rust Engine - 基础数据模型
//!
//! 简化的数据模型，使用 f64 和 String 避免类型转换问题

use pyo3::prelude::*;

// ==================== Bar (K 线数据) ====================

/// K 线数据
#[pyclass]
#[derive(Clone)]
pub struct Bar {
    /// 时间戳（字符串格式：YYYY-MM-DD HH:MM:SS）
    #[pyo3(get)]
    pub timestamp: String,

    /// 证券代码
    #[pyo3(get)]
    pub symbol: String,

    /// 开盘价
    #[pyo3(get)]
    pub open: f64,

    /// 最高价
    #[pyo3(get)]
    pub high: f64,

    /// 最低价
    #[pyo3(get)]
    pub low: f64,

    /// 收盘价
    #[pyo3(get)]
    pub close: f64,

    /// 成交量
    #[pyo3(get)]
    pub volume: i64,

    /// 成交额
    #[pyo3(get)]
    pub turnover: f64,
}

#[pymethods]
impl Bar {
    /// 创建新的 Bar
    #[new]
    #[pyo3(signature = (timestamp, symbol, open, high, low, close, volume, turnover=0.0))]
    fn new(
        timestamp: String,
        symbol: String,
        open: f64,
        high: f64,
        low: f64,
        close: f64,
        volume: i64,
        turnover: f64,
    ) -> Self {
        Self {
            timestamp,
            symbol,
            open,
            high,
            low,
            close,
            volume,
            turnover,
        }
    }

    /// 字符串表示
    fn __repr__(&self) -> String {
        format!(
            "Bar(timestamp='{}', symbol='{}', open={}, high={}, low={}, close={}, volume={})",
            self.timestamp, self.symbol, self.open, self.high, self.low, self.close, self.volume
        )
    }

    /// 获取平均价格
    fn average_price(&self) -> f64 {
        (self.high + self.low + self.close) / 3.0
    }

    /// 获取价格范围
    fn price_range(&self) -> f64 {
        self.high - self.low
    }

    /// 获取涨跌幅
    fn price_change_percent(&self) -> f64 {
        if self.open == 0.0 {
            0.0
        } else {
            (self.close - self.open) / self.open
        }
    }
}

// ==================== Tick (Tick 数据) ====================

/// Tick 数据
#[pyclass]
#[derive(Clone)]
pub struct Tick {
    /// 时间戳
    #[pyo3(get)]
    pub timestamp: String,

    /// 证券代码
    #[pyo3(get)]
    pub symbol: String,

    /// 最新价
    #[pyo3(get)]
    pub last_price: f64,

    /// 买一价
    #[pyo3(get)]
    pub bid_price: f64,

    /// 买一量
    #[pyo3(get)]
    pub bid_volume: i64,

    /// 卖一价
    #[pyo3(get)]
    pub ask_price: f64,

    /// 卖一量
    #[pyo3(get)]
    pub ask_volume: i64,

    /// 成交量
    #[pyo3(get)]
    pub volume: i64,

    /// 成交额
    #[pyo3(get)]
    pub turnover: f64,
}

#[pymethods]
impl Tick {
    #[new]
    #[pyo3(signature = (timestamp, symbol, last_price, bid_price, bid_volume, ask_price, ask_volume, volume, turnover))]
    fn new(
        timestamp: String,
        symbol: String,
        last_price: f64,
        bid_price: f64,
        bid_volume: i64,
        ask_price: f64,
        ask_volume: i64,
        volume: i64,
        turnover: f64,
    ) -> Self {
        Self {
            timestamp,
            symbol,
            last_price,
            bid_price,
            bid_volume,
            ask_price,
            ask_volume,
            volume,
            turnover,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "Tick(timestamp='{}', symbol='{}', price={}, volume={})",
            self.timestamp, self.symbol, self.last_price, self.volume
        )
    }
}

// ==================== Order (订单) ====================

/// 订单方向
#[pyclass]
#[derive(Clone, Debug, PartialEq)]
pub enum OrderSide {
    /// 买入
    Buy,
    /// 卖出
    Sell,
}

/// 订单类型
#[pyclass]
#[derive(Clone, Debug)]
pub enum OrderType {
    /// 市价单
    Market,
    /// 限价单
    Limit,
}

/// 订单状态
#[pyclass]
#[derive(Clone, Debug, PartialEq)]
pub enum OrderStatus {
    /// 待提交
    Pending,
    /// 已提交
    Submitted,
    /// 部分成交
    PartiallyFilled,
    /// 完全成交
    Filled,
    /// 已取消
    Cancelled,
    /// 已拒绝
    Rejected,
}

/// 订单
#[pyclass]
#[derive(Clone)]
pub struct Order {
    /// 订单 ID
    #[pyo3(get)]
    pub order_id: String,

    /// 证券代码
    #[pyo3(get)]
    pub symbol: String,

    /// 订单方向
    #[pyo3(get)]
    pub side: OrderSide,

    /// 订单类型
    #[pyo3(get)]
    pub order_type: OrderType,

    /// 委托价格
    #[pyo3(get)]
    pub price: f64,

    /// 委托数量
    #[pyo3(get)]
    pub quantity: i64,

    /// 成交数量
    #[pyo3(get)]
    pub filled_quantity: i64,

    /// 订单状态
    #[pyo3(get)]
    pub status: OrderStatus,
}

#[pymethods]
impl Order {
    /// 创建新订单
    #[new]
    #[pyo3(signature = (order_id, symbol, side, order_type, price, quantity))]
    fn new(
        order_id: String,
        symbol: String,
        side: OrderSide,
        order_type: OrderType,
        price: f64,
        quantity: i64,
    ) -> Self {
        Self {
            order_id,
            symbol,
            side,
            order_type,
            price,
            quantity,
            filled_quantity: 0,
            status: OrderStatus::Pending,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "Order(id='{}', symbol='{}', side={:?}, type={:?}, price={}, qty={}, status={:?})",
            self.order_id,
            self.symbol,
            self.side,
            self.order_type,
            self.price,
            self.quantity,
            self.status
        )
    }

    /// 是否已完全成交
    fn is_filled(&self) -> bool {
        self.status == OrderStatus::Filled
    }

    /// 是否活跃（待成交）
    fn is_active(&self) -> bool {
        matches!(
            self.status,
            OrderStatus::Pending | OrderStatus::Submitted | OrderStatus::PartiallyFilled
        )
    }

    /// 获取未成交数量
    fn remaining_quantity(&self) -> i64 {
        self.quantity - self.filled_quantity
    }
}

// ==================== Trade (成交) ====================

/// 成交记录
#[pyclass]
#[derive(Clone)]
pub struct Trade {
    /// 成交 ID
    #[pyo3(get)]
    pub trade_id: String,

    /// 订单 ID
    #[pyo3(get)]
    pub order_id: String,

    /// 证券代码
    #[pyo3(get)]
    pub symbol: String,

    /// 成交方向
    #[pyo3(get)]
    pub side: String,

    /// 成交价格
    #[pyo3(get)]
    pub price: f64,

    /// 成交数量
    #[pyo3(get)]
    pub quantity: i64,

    /// 成交金额
    #[pyo3(get)]
    pub turnover: f64,

    /// 手续费
    #[pyo3(get)]
    pub commission: f64,
}

#[pymethods]
impl Trade {
    #[new]
    #[pyo3(signature = (trade_id, order_id, symbol, side, price, quantity, commission))]
    fn new(
        trade_id: String,
        order_id: String,
        symbol: String,
        side: String,
        price: f64,
        quantity: i64,
        commission: f64,
    ) -> Self {
        let turnover = price * (quantity as f64);
        Self {
            trade_id,
            order_id,
            symbol,
            side,
            price,
            quantity,
            turnover,
            commission,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "Trade(id='{}', symbol='{}', price={}, qty={}, amount={:.2})",
            self.trade_id, self.symbol, self.price, self.quantity, self.turnover
        )
    }

    /// 获取净成交金额（扣除费用）
    fn net_amount(&self) -> f64 {
        self.turnover - self.commission
    }
}

// ==================== Position (持仓) ====================

/// 持仓
#[pyclass]
#[derive(Clone)]
pub struct Position {
    /// 证券代码
    #[pyo3(get)]
    pub symbol: String,

    /// 持仓方向
    #[pyo3(get)]
    pub side: String,

    /// 持仓数量
    #[pyo3(get)]
    pub quantity: i64,

    /// 可用数量
    #[pyo3(get)]
    pub available_quantity: i64,

    /// 持仓成本价
    #[pyo3(get)]
    pub cost_price: f64,

    /// 当前市价
    #[pyo3(get)]
    pub current_price: f64,
}

#[pymethods]
impl Position {
    #[new]
    #[pyo3(signature = (symbol, side, quantity, cost_price, current_price))]
    fn new(
        symbol: String,
        side: String,
        quantity: i64,
        cost_price: f64,
        current_price: f64,
    ) -> Self {
        Self {
            symbol,
            side,
            quantity,
            available_quantity: quantity,
            cost_price,
            current_price,
        }
    }

    fn __repr__(&self) -> String {
        let pnl_percent = self.unrealized_pnl_percent() * 100.0;
        format!(
            "Position(symbol='{}', qty={}, cost={}, current={}, pnl={:.2}%)",
            self.symbol, self.quantity, self.cost_price, self.current_price, pnl_percent
        )
    }

    /// 获取持仓成本
    fn cost_value(&self) -> f64 {
        self.cost_price * (self.quantity as f64)
    }

    /// 获取持仓市值
    fn market_value(&self) -> f64 {
        self.current_price * (self.quantity as f64)
    }

    /// 获取浮动盈亏
    fn unrealized_pnl(&self) -> f64 {
        self.market_value() - self.cost_value()
    }

    /// 获取浮动盈亏比例
    fn unrealized_pnl_percent(&self) -> f64 {
        let cost = self.cost_value();
        if cost == 0.0 {
            0.0
        } else {
            self.unrealized_pnl() / cost
        }
    }

    /// 更新当前价格
    fn update_price(&mut self, price: f64) {
        self.current_price = price;
    }

    /// 是否可卖出指定数量
    fn can_sell(&self, quantity: i64) -> bool {
        self.available_quantity >= quantity
    }
}

// ==================== Portfolio (投资组合) ====================

/// 投资组合
#[pyclass]
#[derive(Clone)]
pub struct Portfolio {
    /// 初始资金
    #[pyo3(get)]
    pub initial_capital: f64,

    /// 当前资金
    #[pyo3(get)]
    pub cash: f64,

    /// 持仓
    #[pyo3(get)]
    pub positions: Vec<Position>,

    /// 冻结资金
    #[pyo3(get)]
    pub frozen_cash: f64,
}

#[pymethods]
impl Portfolio {
    /// 创建新投资组合
    #[new]
    #[pyo3(signature = (initial_capital))]
    fn new(initial_capital: f64) -> Self {
        Self {
            initial_capital,
            cash: initial_capital,
            positions: Vec::new(),
            frozen_cash: 0.0,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "Portfolio(cash={:.2}, market_value={:.2}, total={:.2}, pnl={:.2}%)",
            self.cash,
            self.market_value(),
            self.total_asset(),
            self.total_pnl_percent() * 100.0
        )
    }

    /// 获取持仓数量
    fn position_count(&self) -> usize {
        self.positions.len()
    }

    /// 是否有某个持仓
    fn has_position(&self, symbol: &str) -> bool {
        self.positions.iter().any(|p| p.symbol == symbol)
    }

    /// 获取持仓
    fn get_position(&self, symbol: &str) -> Option<Position> {
        self.positions.iter().find(|p| p.symbol == symbol).cloned()
    }

    /// 添加持仓
    fn add_position(&mut self, position: Position) {
        // 如果已有该持仓，更新；否则添加
        if let Some(pos) = self
            .positions
            .iter_mut()
            .find(|p| p.symbol == position.symbol)
        {
            pos.quantity += position.quantity;
            pos.available_quantity += position.available_quantity;
        } else {
            self.positions.push(position);
        }
    }

    /// 移除持仓
    fn remove_position(&mut self, symbol: &str) -> Option<Position> {
        if let Some(index) = self.positions.iter().position(|p| p.symbol == symbol) {
            Some(self.positions.remove(index))
        } else {
            None
        }
    }

    /// 获取总市值
    fn market_value(&self) -> f64 {
        self.positions.iter().map(|p| p.market_value()).sum()
    }

    /// 获取总资产
    fn total_asset(&self) -> f64 {
        self.cash + self.market_value()
    }

    /// 获取总盈亏
    fn total_pnl(&self) -> f64 {
        self.total_asset() - self.initial_capital
    }

    /// 获取总盈亏比例
    fn total_pnl_percent(&self) -> f64 {
        if self.initial_capital == 0.0 {
            0.0
        } else {
            self.total_pnl() / self.initial_capital
        }
    }

    /// 获取可用资金
    fn available_cash(&self) -> f64 {
        self.cash - self.frozen_cash
    }

    /// 获取仓位比例
    fn position_ratio(&self) -> f64 {
        let total = self.total_asset();
        if total == 0.0 {
            0.0
        } else {
            self.market_value() / total
        }
    }
}

// ==================== 绩效分析 ====================

/// 绩效分析器
#[pyclass]
pub struct PerformanceAnalyzer {
    trades: Vec<Trade>,
    portfolio_values: Vec<f64>,
    initial_capital: f64,
}

#[pymethods]
impl PerformanceAnalyzer {
    #[new]
    fn new(trades: Vec<Trade>, portfolio_values: Vec<f64>, initial_capital: f64) -> Self {
        Self {
            trades,
            portfolio_values,
            initial_capital,
        }
    }

    /// 计算总收益
    fn total_return(&self) -> f64 {
        if self.portfolio_values.is_empty() {
            0.0
        } else {
            let final_value = self.portfolio_values[self.portfolio_values.len() - 1];
            (final_value - self.initial_capital) / self.initial_capital
        }
    }

    /// 计算年化收益
    fn annual_return(&self, days: i32) -> f64 {
        let total = self.total_return();
        if days <= 0 {
            total
        } else {
            (1.0 + total).powf(365.0 / days as f64) - 1.0
        }
    }

    /// 计算波动率
    fn volatility(&self) -> f64 {
        if self.portfolio_values.len() < 2 {
            0.0
        } else {
            // 计算日收益率
            let mut returns = Vec::new();
            for i in 1..self.portfolio_values.len() {
                let ret = (self.portfolio_values[i] - self.portfolio_values[i - 1])
                    / self.portfolio_values[i - 1];
                returns.push(ret);
            }

            // 计算标准差
            let mean = returns.iter().sum::<f64>() / returns.len() as f64;
            let variance =
                returns.iter().map(|r| (r - mean).powi(2)).sum::<f64>() / returns.len() as f64;
            variance.sqrt() * (252.0_f64).sqrt() // 年化
        }
    }

    /// 计算夏普比率
    fn sharpe_ratio(&self, risk_free_rate: f64) -> f64 {
        let vol = self.volatility();
        if vol == 0.0 {
            0.0
        } else {
            (self.annual_return(365) - risk_free_rate) / vol
        }
    }

    /// 计算最大回撤
    fn max_drawdown(&self) -> f64 {
        if self.portfolio_values.is_empty() {
            0.0
        } else {
            let mut max_dd = 0.0;
            let mut peak = self.portfolio_values[0];

            for &value in &self.portfolio_values {
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

    /// 计算胜率
    fn win_rate(&self) -> f64 {
        if self.trades.is_empty() {
            0.0
        } else {
            let winning_trades = self
                .trades
                .iter()
                .filter(|t| {
                    if t.side == "buy" {
                        true // 买入不算盈亏
                    } else {
                        // 卖出时计算盈亏（简化逻辑）
                        true
                    }
                })
                .count();
            winning_trades as f64 / self.trades.len() as f64
        }
    }

    /// 获取交易统计
    fn get_trade_stats(&self) -> (i32, i32, i32) {
        let total = self.trades.len() as i32;
        let buys = self.trades.iter().filter(|t| t.side == "buy").count() as i32;
        let sells = self.trades.iter().filter(|t| t.side == "sell").count() as i32;
        (total, buys, sells)
    }
}

// ==================== 回测引擎 ====================

/// 回测配置
#[pyclass]
#[derive(Clone)]
pub struct BacktestConfig {
    /// 初始资金
    #[pyo3(get)]
    pub initial_capital: f64,

    /// 佣金率
    #[pyo3(get)]
    pub commission_rate: f64,

    /// 滑点
    #[pyo3(get)]
    pub slippage: f64,

    /// 印花税（卖出收取）
    #[pyo3(get)]
    pub stamp_tax: f64,

    /// 最小手续费
    #[pyo3(get)]
    pub min_commission: f64,
}

#[pymethods]
impl BacktestConfig {
    #[new]
    #[pyo3(signature = (initial_capital, commission_rate=0.0003, slippage=0.001, stamp_tax=0.001, min_commission=5.0))]
    fn new(
        initial_capital: f64,
        commission_rate: f64,
        slippage: f64,
        stamp_tax: f64,
        min_commission: f64,
    ) -> Self {
        Self {
            initial_capital,
            commission_rate,
            slippage,
            stamp_tax,
            min_commission,
        }
    }
}

/// 回测结果
#[pyclass]
#[derive(Clone)]
pub struct BacktestResult {
    /// 总收益
    #[pyo3(get)]
    pub total_return: f64,

    /// 总交易次数
    #[pyo3(get)]
    pub total_trades: i32,

    /// 初始资金
    #[pyo3(get)]
    pub initial_capital: f64,

    /// 最终资金
    #[pyo3(get)]
    pub final_capital: f64,
}

#[pymethods]
impl BacktestResult {
    fn __repr__(&self) -> String {
        format!(
            "BacktestResult(total_return={:.2}%, trades={}, final_capital={:.2})",
            self.total_return * 100.0,
            self.total_trades,
            self.final_capital
        )
    }
}

/// 订单匹配引擎
#[pyclass]
pub struct MatchingEngine {
    commission_rate: f64,
    slippage: f64,
    stamp_tax: f64,
    min_commission: f64,
    next_trade_id: u32,
}

#[pymethods]
impl MatchingEngine {
    #[new]
    #[pyo3(signature = (commission_rate=0.0003, slippage=0.001, stamp_tax=0.001, min_commission=5.0))]
    fn new(commission_rate: f64, slippage: f64, stamp_tax: f64, min_commission: f64) -> Self {
        Self {
            commission_rate,
            slippage,
            stamp_tax,
            min_commission,
            next_trade_id: 1,
        }
    }

    /// 匹配订单（简化版：市价单立即成交）
    fn match_order(&mut self, order: &mut Order, bar: &Bar) -> Option<Trade> {
        // 简化逻辑：市价单立即按当前价格成交
        if !order.is_active() {
            return None;
        }

        // 计算成交价（考虑滑点）
        let mut exec_price = bar.close;
        if order.side == OrderSide::Buy {
            exec_price = bar.close * (1.0 + self.slippage);
        } else {
            exec_price = bar.close * (1.0 - self.slippage);
        }

        // 生成成交
        let turnover = exec_price * (order.quantity as f64);
        let commission = (turnover * self.commission_rate).max(self.min_commission);

        // 印花税（仅卖出收取）
        let tax = if order.side == OrderSide::Sell {
            turnover * self.stamp_tax
        } else {
            0.0
        };

        let total_cost = commission + tax;

        // 创建成交记录
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

        // 更新订单状态
        order.filled_quantity = order.quantity;
        order.status = OrderStatus::Filled;

        Some(trade)
    }
}

/// 回测引擎
#[pyclass]
pub struct BacktestEngine {
    config: BacktestConfig,
    portfolio: Portfolio,
    orders: Vec<Order>,
    trades: Vec<Trade>,
    matching_engine: MatchingEngine,
    bar_index: usize,
}

#[pymethods]
impl BacktestEngine {
    /// 创建回测引擎
    #[new]
    fn new(config: BacktestConfig) -> Self {
        let matching_engine = MatchingEngine::new(
            config.commission_rate,
            config.slippage,
            config.stamp_tax,
            config.min_commission,
        );

        Self {
            config: config.clone(),
            portfolio: Portfolio::new(config.initial_capital),
            orders: Vec::new(),
            trades: Vec::new(),
            matching_engine,
            bar_index: 0,
        }
    }

    /// 买入
    fn buy(&mut self, symbol: &str, price: f64, volume: i64) -> Order {
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
        order
    }

    /// 卖出
    fn sell(&mut self, symbol: &str, price: f64, volume: i64) -> Order {
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
        order
    }

    /// 处理订单（撮合）
    fn process_orders(&mut self, bar: &Bar) {
        let mut orders_to_process: Vec<usize> = Vec::new();

        // 找出所有活跃订单
        for (i, order) in self.orders.iter().enumerate() {
            if order.is_active() && order.symbol == bar.symbol {
                orders_to_process.push(i);
            }
        }

        // 处理订单
        for &i in &orders_to_process {
            let order = &mut self.orders[i];
            if let Some(trade) = self.matching_engine.match_order(order, bar) {
                // 更新持仓
                self.update_position(&trade);
                self.trades.push(trade);
            }
        }
    }

    /// 更新持仓
    fn update_position(&mut self, trade: &Trade) {
        if trade.side == "buy" {
            // 买入：增加持仓
            let position = Position::new(
                trade.symbol.clone(),
                "long".to_string(),
                trade.quantity,
                trade.price,
                trade.price,
            );
            self.portfolio.add_position(position);
        } else {
            // 卖出：减少持仓
            if let Some(mut pos) = self.portfolio.get_position(&trade.symbol) {
                pos.quantity -= trade.quantity;
                if pos.quantity <= 0 {
                    self.portfolio.remove_position(&trade.symbol);
                }
            }
        }

        // 更新资金
        if trade.side == "buy" {
            self.portfolio.cash -= trade.turnover + trade.commission;
        } else {
            self.portfolio.cash += trade.turnover - trade.commission;
        }
    }

    /// 运行回测
    fn run(&mut self, bars: Vec<Bar>) -> BacktestResult {
        // 简化版回测流程
        for bar in bars {
            self.bar_index += 1;

            // 处理订单
            self.process_orders(&bar);

            // 更新持仓价格
            if self.portfolio.has_position(&bar.symbol) {
                if let Some(mut pos) = self.portfolio.get_position(&bar.symbol) {
                    pos.update_price(bar.close);
                }
            }
        }

        // 计算结果
        BacktestResult {
            total_return: self.portfolio.total_pnl_percent(),
            total_trades: self.trades.len() as i32,
            initial_capital: self.config.initial_capital,
            final_capital: self.portfolio.total_asset(),
        }
    }

    /// 获取投资组合
    fn get_portfolio(&self) -> Portfolio {
        self.portfolio.clone()
    }

    /// 获取订单列表
    fn get_orders(&self) -> Vec<Order> {
        self.orders.clone()
    }

    /// 获取成交列表
    fn get_trades(&self) -> Vec<Trade> {
        self.trades.clone()
    }
}

// ==================== 模块导出 ====================

/// Python 模块入口
#[pymodule]
fn quantcore_engine(_py: Python, m: &PyModule) -> PyResult<()> {
    // 版本信息
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(hello_quant, m)?)?;
    m.add_function(wrap_pyfunction!(add, m)?)?;

    // 数据模型
    m.add_class::<Bar>()?;
    m.add_class::<Tick>()?;
    m.add_class::<Order>()?;
    m.add_class::<Trade>()?;
    m.add_class::<Position>()?;
    m.add_class::<Portfolio>()?;

    // 回测引擎
    m.add_class::<BacktestConfig>()?;
    m.add_class::<BacktestResult>()?;
    m.add_class::<MatchingEngine>()?;
    m.add_class::<BacktestEngine>()?;

    // 绩效分析
    m.add_class::<PerformanceAnalyzer>()?;

    // 枚举
    m.add_class::<OrderSide>()?;
    m.add_class::<OrderType>()?;
    m.add_class::<OrderStatus>()?;

    Ok(())
}

// ==================== 辅助函数 ====================

/// QuantCore Rust 引擎版本
#[pyfunction]
fn version() -> &'static str {
    "0.1.0"
}

/// 打印引擎信息
#[pyfunction]
fn hello_quant() -> &'static str {
    "Hello from QuantCore Rust Engine!"
}

/// 简单的加法函数（用于测试）
#[pyfunction]
fn add(a: f64, b: f64) -> f64 {
    a + b
}

// ==================== 测试 ====================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_version() {
        assert_eq!(version(), "0.1.0");
    }

    #[test]
    fn test_add() {
        assert_eq!(add(2.0, 3.0), 5.0);
    }

    #[test]
    fn test_bar() {
        let bar = Bar::new(
            "2024-01-01 10:00:00".to_string(),
            "SH.600000".to_string(),
            10.0,
            10.5,
            9.8,
            10.2,
            1000000,
            10200000.0,
        );

        assert_eq!(bar.symbol, "SH.600000");
        assert_eq!(bar.close, 10.2);
        assert!((bar.average_price() - 10.166666) < 0.001);
    }

    #[test]
    fn test_portfolio() {
        let mut portfolio = Portfolio::new(1000000.0);

        let position = Position::new(
            "SH.600000".to_string(),
            "long".to_string(),
            1000,
            10.0,
            10.2,
        );

        portfolio.add_position(position);

        assert!(portfolio.has_position("SH.600000"));
        assert!((portfolio.market_value() - 10200.0) < 0.01);
    }
}
