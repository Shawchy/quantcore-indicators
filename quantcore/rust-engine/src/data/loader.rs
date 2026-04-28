//! 数据加载器

use super::feed::DataFeed;
use crate::core::Bar;
use pyo3::prelude::*;
use std::collections::HashMap;
use std::sync::Arc;

/// 数据加载器
#[pyclass]
pub struct DataLoader {
    /// 数据源映射
    feeds: HashMap<String, String>,
    /// 数据缓存
    cache: HashMap<String, Vec<Bar>>,
}

#[pymethods]
impl DataLoader {
    /// 创建数据加载器
    #[new]
    fn new() -> Self {
        Self {
            feeds: HashMap::new(),
            cache: HashMap::new(),
        }
    }

    /// 添加数据源
    fn add_feed(&mut self, name: &str, description: &str) {
        self.feeds.insert(name.to_string(), description.to_string());
    }

    /// 加载历史数据
    fn load_history(&self, symbol: &str, start: &str, end: &str) -> PyResult<Vec<Bar>> {
        // 首先检查缓存
        let cache_key = format!("{}_{}_{}", symbol, start, end);
        if let Some(data) = self.cache.get(&cache_key) {
            return Ok(data.clone());
        }

        // 返回空数据（需要外部数据源提供）
        Ok(Vec::new())
    }

    /// 清除缓存
    fn clear_cache(&mut self) {
        self.cache.clear();
    }

    /// 获取已注册的数据源列表
    fn get_feeds(&self) -> Vec<String> {
        self.feeds.keys().cloned().collect()
    }
}

impl Default for DataLoader {
    fn default() -> Self {
        Self::new()
    }
}
