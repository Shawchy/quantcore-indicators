//! 数据缓存

use crate::core::Bar;
use std::collections::HashMap;

/// 数据缓存
pub struct DataCache {
    /// 内存缓存
    cache: HashMap<String, Vec<Bar>>,

    /// 缓存大小限制
    max_size: usize,
}

impl DataCache {
    pub fn new(max_size: usize) -> Self {
        Self {
            cache: HashMap::new(),
            max_size,
        }
    }

    /// 获取缓存
    pub fn get(&self, key: &str) -> Option<&Vec<Bar>> {
        self.cache.get(key)
    }

    /// 设置缓存
    pub fn set(&mut self, key: String, bars: Vec<Bar>) {
        if self.cache.len() >= self.max_size {
            // 简单的 LRU：清除第一个
            if let Some(first_key) = self.cache.keys().next().cloned() {
                self.cache.remove(&first_key);
            }
        }
        self.cache.insert(key, bars);
    }

    /// 清除缓存
    pub fn clear(&mut self) {
        self.cache.clear();
    }
}

impl Default for DataCache {
    fn default() -> Self {
        Self::new(1000)
    }
}
