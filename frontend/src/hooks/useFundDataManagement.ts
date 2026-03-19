/**
 * 基金数据管理 Hook
 * 
 * 提供自动缓存管理、数据更新等功能
 */
import { useEffect, useCallback } from 'react';
import fundStorage from '../services/fundStorage';
import { fundCleanup, fundUpdater } from '../services/fundCleanup';

interface UseFundDataOptions {
  /** 是否启用自动清理 */
  enableCleanup?: boolean;
  /** 清理间隔（毫秒），默认 1 小时 */
  cleanupInterval?: number;
  /** 是否启用后台更新 */
  enableBackgroundUpdate?: boolean;
  /** 后台更新间隔（毫秒），默认 5 分钟 */
  backgroundUpdateInterval?: number;
  /** 自选基金代码列表（用于后台更新） */
  watchlistCodes?: string[];
}

/**
 * 基金数据管理 Hook
 */
export function useFundDataManagement(options: UseFundDataOptions = {}) {
  const {
    enableCleanup = true,
    cleanupInterval = 60 * 60 * 1000, // 1 小时
    enableBackgroundUpdate = true,
    backgroundUpdateInterval = 5 * 60 * 1000, // 5 分钟
    watchlistCodes = [],
  } = options;

  // 初始化数据管理
  useEffect(() => {
    if (enableCleanup) {
      // 启动定期清理
      fundCleanup.startPeriodicCleanup(cleanupInterval);
      
      // 页面卸载时停止清理
      return () => {
        fundCleanup.stopPeriodicCleanup();
      };
    }
  }, [enableCleanup, cleanupInterval]);

  // 后台更新自选基金数据
  useEffect(() => {
    if (!enableBackgroundUpdate || watchlistCodes.length === 0) {
      return;
    }

    // 立即执行一次
    fundUpdater.updateWatchlistRealtimeData(watchlistCodes);

    // 定期更新
    const interval = setInterval(() => {
      fundUpdater.updateWatchlistRealtimeData(watchlistCodes);
    }, backgroundUpdateInterval);

    return () => {
      clearInterval(interval);
    };
  }, [enableBackgroundUpdate, backgroundUpdateInterval, watchlistCodes]);

  // 页面可见性变化时更新数据
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && watchlistCodes.length > 0) {
        // 页面变为可见时更新数据
        fundUpdater.updateWatchlistRealtimeData(watchlistCodes);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [watchlistCodes]);

  // 刷新指定基金的缓存
  const refreshFundCache = useCallback(async (fundCode: string) => {
    await fundCleanup.refreshFundCache(fundCode);
  }, []);

  // 清空所有缓存
  const clearAllCache = useCallback(async () => {
    await fundCleanup.clearAllCache();
  }, []);

  // 获取存储统计
  const getStorageStats = useCallback(async () => {
    return await fundStorage.getStats();
  }, []);

  return {
    refreshFundCache,
    clearAllCache,
    getStorageStats,
  };
}

/**
 * 基金数据查询 Hook
 * 
 * 优先从缓存获取数据，自动管理缓存
 */
export function useFundQuery() {
  // 这里可以集成 React Query 或其他数据获取库
  // 目前使用基础的缓存策略
  
  return {
    // 后续可以扩展更多查询功能
  };
}

export default useFundDataManagement;
