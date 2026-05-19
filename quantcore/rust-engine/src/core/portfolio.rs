//! 投资组合模块

use super::position::Position;
use pyo3::prelude::*;
use rust_decimal::Decimal;
use rust_decimal::prelude::*;
use std::str::FromStr;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;

/// 投资组合
#[pyclass]
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Portfolio {
    /// 初始资金
    #[pyo3(get)]
    pub initial_capital: Decimal,

    /// 当前资金
    #[pyo3(get)]
    pub cash: Decimal,

    /// 持仓
    #[pyo3(get)]
    pub positions: HashMap<String, Position>,

    /// 冻结资金
    #[pyo3(get)]
    pub frozen_cash: Decimal,

    /// 总资产
    #[pyo3(get)]
    pub total_asset: Decimal,

    /// 总市值
    #[pyo3(get)]
    pub market_value: Decimal,

    /// 总盈亏
    #[pyo3(get)]
    pub total_pnl: Decimal,

    /// 总盈亏比例
    #[pyo3(get)]
    pub total_pnl_percent: Decimal,
}

#[pymethods]
impl Portfolio {
    /// 创建新投资组合
    #[new]
    #[pyo3(signature = (initial_capital))]
    fn new(initial_capital: f64) -> Self {
        if initial_capital <= 0.0 || initial_capital.is_nan() || initial_capital.is_infinite() {
            log::error!("初始资金无效: {}，将使用 1000000.0", initial_capital);
        }
        let capital = Decimal::from_f64_retain(initial_capital)
            .unwrap_or_else(|| {
                log::error!("初始资金转换失败: {}，使用默认值", initial_capital);
                Decimal::from(1000000)
            });
        Self {
            initial_capital: capital,
            cash: capital,
            positions: HashMap::new(),
            frozen_cash: Decimal::ZERO,
            total_asset: capital,
            market_value: Decimal::ZERO,
            total_pnl: Decimal::ZERO,
            total_pnl_percent: Decimal::ZERO,
        }
    }

    fn __repr__(&self) -> String {
        format!(
            "Portfolio(cash={}, market_value={}, total={}, pnl={:.2}%)",
            self.cash,
            self.market_value,
            self.total_asset,
            self.total_pnl_percent * Decimal::from(100)
        )
    }

    /// 获取持仓数量
    fn position_count(&self) -> usize {
        self.positions.len()
    }

    /// 是否有某个持仓
    fn has_position(&self, symbol: &str) -> bool {
        self.positions.contains_key(symbol)
    }

    /// 获取持仓
    fn get_position(&self, symbol: &str) -> Option<&Position> {
        self.positions.get(symbol)
    }

    /// 获取可变持仓引用
    pub fn get_position_mut(&mut self, symbol: &str) -> Option<&mut Position> {
        self.positions.get_mut(symbol)
    }

    /// 添加持仓
    fn add_position(&mut self, position: Position) {
        self.positions.insert(position.symbol.clone(), position);
    }

    /// 移除持仓
    fn remove_position(&mut self, symbol: &str) -> Option<Position> {
        self.positions.remove(symbol)
    }

    /// 更新组合市值和盈亏
    fn update(&mut self) {
        self.market_value = self.positions.values().map(|p| p.market_value).sum();

        self.total_asset = self.cash + self.market_value;
        self.total_pnl = self.total_asset - self.initial_capital;
        self.total_pnl_percent = if self.initial_capital == Decimal::ZERO {
            Decimal::ZERO
        } else {
            self.total_pnl / self.initial_capital
        };
    }

    /// 获取可用资金
    fn available_cash(&self) -> Decimal {
        self.cash - self.frozen_cash
    }

    /// 实时计算总资产（现金 + 持仓市值）
    fn total_value(&self) -> Decimal {
        let current_market_value: Decimal = self.positions.values().map(|p| p.market_value).sum();
        self.cash + current_market_value
    }

    /// 获取仓位比例
    fn position_ratio(&self) -> Decimal {
        if self.total_asset == Decimal::ZERO {
            Decimal::ZERO
        } else {
            self.market_value / self.total_asset
        }
    }

    /// 买入
    pub fn buy(&mut self, symbol: &str, price: f64, quantity: i64, commission: f64, tax: f64) -> PyResult<()> {
        let price_dec = Decimal::from_str(&format!("{:.4}", price)).unwrap_or_else(|_| {
            log::error!("买入价格转换失败: {}", price);
            Decimal::ZERO
        });
        let amount = price_dec * Decimal::from(quantity);
        let commission_dec = Decimal::from_str(&format!("{:.4}", commission)).unwrap_or_else(|_| {
            log::warn!("佣金转换失败: {}", commission);
            Decimal::ZERO
        });
        let tax_dec = Decimal::from_str(&format!("{:.4}", tax)).unwrap_or_else(|_| {
            log::warn!("税费转换失败: {}", tax);
            Decimal::ZERO
        });
        let total_cost = amount + commission_dec + tax_dec;

        if self.cash < total_cost {
            return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "资金不足：需要 {} 可用 {}",
                total_cost, self.cash
            )));
        }

        self.cash -= total_cost;

        let position = self.positions.entry(symbol.to_string()).or_insert_with(|| {
            Position::new(symbol.to_string(), "long".to_string(), 0, 0.0, 0.0)
        });

        let total_qty = position.quantity + quantity;
        if total_qty > 0 {
            let new_avg = (position.cost_price * Decimal::from(position.quantity) + price_dec * Decimal::from(quantity)) / Decimal::from(total_qty);
            position.cost_price = new_avg;
            position.quantity = total_qty;
        }

        self.update();
        Ok(())
    }

    /// 卖出
    pub fn sell(&mut self, symbol: &str, price: f64, quantity: i64, commission: f64, tax: f64) -> PyResult<()> {
        if let Some(position) = self.positions.get_mut(symbol) {
            if position.quantity < quantity {
                return Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                    "持仓不足：需要 {} 持有 {}",
                    quantity, position.quantity
                )));
            }

            let price_dec = Decimal::from_str(&format!("{:.4}", price)).unwrap_or_else(|_| {
                log::error!("卖出价格转换失败: {}", price);
                Decimal::ZERO
            });
            let revenue = price_dec * Decimal::from(quantity);
            let commission_dec = Decimal::from_str(&format!("{:.4}", commission)).unwrap_or_else(|_| {
                log::warn!("佣金转换失败: {}", commission);
                Decimal::ZERO
            });
            let tax_dec = Decimal::from_str(&format!("{:.4}", tax)).unwrap_or_else(|_| {
                log::warn!("税费转换失败: {}", tax);
                Decimal::ZERO
            });
            let net_revenue = revenue - commission_dec - tax_dec;

            self.cash += net_revenue;
            position.quantity -= quantity;

            if position.quantity == 0 {
                self.positions.remove(symbol);
            }

            self.update();
            Ok(())
        } else {
            Err(PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                "无持仓：{}", symbol
            )))
        }
    }

    /// 获取所有持仓列表
    pub fn get_positions(&self) -> Vec<&Position> {
        self.positions.values().collect()
    }
}
