//! 回测引擎模块

pub mod backtest;
pub mod backtest_v2;
pub mod matching;

pub use backtest::{BacktestConfig, BacktestEngine, BacktestResult};
pub use backtest_v2::{BacktestEngineV2, BacktestConfigV2, BacktestResultV2};
pub use matching::MatchingEngine;
