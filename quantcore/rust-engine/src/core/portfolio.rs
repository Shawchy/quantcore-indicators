//! 投资组合模块

use super::position::Position;
use pyo3::prelude::*;
use rust_decimal::Decimal;
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
        let capital = Decimal::from_f64_retain(initial_capital).unwrap_or(Decimal::ZERO);
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

    /// 获取仓位比例
    fn position_ratio(&self) -> Decimal {
        if self.total_asset == Decimal::ZERO {
            Decimal::ZERO
        } else {
            self.market_value / self.total_asset
        }
    }
}
