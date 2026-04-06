//! 数据源特征

use crate::core::Bar;
use std::sync::Arc;

/// 数据源特征
pub trait DataFeed: Send + Sync {
    /// 获取历史数据
    fn get_historical(
        &self,
        symbol: &str,
        start: &str,
        end: &str,
    ) -> Result<Vec<Bar>, Box<dyn std::error::Error>>;

    /// 订阅实时数据
    fn subscribe(
        &self,
        symbol: &str,
    ) -> Result<Arc<dyn Iterator<Item = Bar> + Send + Sync>, Box<dyn std::error::Error>>;

    /// 数据源名称
    fn name(&self) -> &str;
}
