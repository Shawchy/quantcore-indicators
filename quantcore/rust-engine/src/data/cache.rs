//! 数据缓存

use crate::core::Bar;
use std::collections::HashMap;

/// 缓存条目（带访问顺序）
struct CacheEntry {
    data: Vec<Bar>,
    access_count: u64,
}

/// 数据缓存（近似 LRU）
pub struct DataCache {
    cache: HashMap<String, CacheEntry>,
    max_size: usize,
    access_counter: u64,
}

impl DataCache {
    pub fn new(max_size: usize) -> Self {
        Self {
            cache: HashMap::new(),
            max_size,
            access_counter: 0,
        }
    }

    pub fn get(&mut self, key: &str) -> Option<&Vec<Bar>> {
        if let Some(entry) = self.cache.get_mut(key) {
            self.access_counter += 1;
            entry.access_count = self.access_counter;
            Some(&entry.data)
        } else {
            None
        }
    }

    pub fn set(&mut self, key: String, bars: Vec<Bar>) {
        if self.cache.len() >= self.max_size {
            if let Some(evict_key) = self.find_lru_key() {
                self.cache.remove(&evict_key);
            }
        }
        self.access_counter += 1;
        self.cache.insert(key, CacheEntry {
            data: bars,
            access_count: self.access_counter,
        });
    }

    pub fn clear(&mut self) {
        self.cache.clear();
    }

    fn find_lru_key(&self) -> Option<String> {
        self.cache
            .iter()
            .min_by_key(|(_, entry)| entry.access_count)
            .map(|(k, _)| k.clone())
    }
}

impl Default for DataCache {
    fn default() -> Self {
        Self::new(1000)
    }
}
