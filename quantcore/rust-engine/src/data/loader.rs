//! 数据加载器

use super::feed::DataFeed;
use crate::core::Bar;
use pyo3::prelude::*;
use std::collections::HashMap;

/// 数据加载器
#[pyclass]
pub struct DataLoader {
    /// 数据源
    feeds: HashMap<String, Box<dyn DataFeed>>,
}

#[pymethods]
impl DataLoader {
    /// 创建数据加载器
    #[new]
    fn new() -> Self {
        Self {
            feeds: HashMap::new(),
        }
    }

    /// 添加数据源
    fn add_feed(&mut self, name: &str, _feed: PyObject) {
        // TODO: 添加数据源
        // self.feeds.insert(name.to_string(), Box::new(feed));
    }

    /// 加载历史数据
    fn load_history(&self, _symbol: &str, _start: &str, _end: &str) -> PyResult<Vec<Bar>> {
        // TODO: 实现历史数据加载
        Ok(Vec::new())
    }
}

impl Default for DataLoader {
    fn default() -> Self {
        Self::new()
    }
}
