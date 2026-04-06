//! 策略运行器

use super::{Strategy, StrategyContext};
use crate::core::Bar;

/// 策略运行器
pub struct StrategyRunner {
    context: StrategyContext,
}

impl StrategyRunner {
    pub fn new(context: StrategyContext) -> Self {
        Self { context }
    }

    /// 运行策略
    pub fn run(&mut self, strategy: &mut dyn Strategy, bars: &[Bar]) {
        // 初始化
        strategy.on_init(&mut self.context);

        // 处理每个 K 线
        for bar in bars {
            strategy.on_bar(&mut self.context, bar);
        }

        // 结束
        strategy.on_finish(&mut self.context);
    }
}
