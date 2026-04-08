/**
 * 基金数据管理 Hook
 * 
 * 提供自动缓存管理、数据更新等功能
 * 优化：只在访问基金相关页面时才启用后台更新
 */
import { useEffect, useCallback, useState } from 'react';
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
  /** 是否只在基金页面启用（推荐） */
  onlyOnFundPage?: boolean;
  /** 当前是否在基金页面（由外部传入） */
  isFundPage?: boolean;
}

/**
 * 基金数据管理 Hook（内部实现）
 */
function useFundDataManagementInternal(options: UseFundDataOptions = {}) {
  const {
    enableBackgroundUpdate = true,
    backgroundUpdateInterval = 5 * 60 * 1000, // 5 分钟
    watchlistCodes = [],
    onlyOnFundPage = true, // 默认只在基金页面启用
    isFundPage = false, // 默认不在基金页面
  } = options;

  // 后台更新自选基金数据（优化：只在基金页面启用）
  useEffect(() => {
    // 如果设置了只在基金页面启用，且当前不在基金页面，则跳过
    if (onlyOnFundPage && !isFundPage) {
      return;
    }

    if (!enableBackgroundUpdate || watchlistCodes.length === 0) {
      return;
    }

    console.log('[基金数据管理] 启用后台更新，自选基金数量:', watchlistCodes.length);

    // 立即执行一次
    fundUpdater.updateWatchlistRealtimeData(watchlistCodes);

    // 定期更新
    const interval = setInterval(() => {
      fundUpdater.updateWatchlistRealtimeData(watchlistCodes);
    }, backgroundUpdateInterval);

    return () => {
      clearInterval(interval);
      console.log('[基金数据管理] 停止后台更新');
    };
  }, [
    enableBackgroundUpdate, 
    backgroundUpdateInterval, 
    watchlistCodes,
    onlyOnFundPage,
    isFundPage
  ]);

  // 页面可见性变化时更新数据（优化：只在基金页面启用）
  useEffect(() => {
    // 如果设置了只在基金页面启用，且当前不在基金页面，则跳过
    if (onlyOnFundPage && !isFundPage) {
      return;
    }

    const handleVisibilityChange = () => {
      if (document.visibilityState === 'visible' && watchlistCodes.length > 0) {
        // 页面变为可见时更新数据
        console.log('[基金数据管理] 页面可见，更新数据');
        fundUpdater.updateWatchlistRealtimeData(watchlistCodes);
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);
    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [watchlistCodes, onlyOnFundPage, isFundPage]);

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
 * 基金数据管理 Hook（主 Hook，不依赖 Router）
 * 
 * 使用方式：
 * 1. 在 App 组件中使用（不需要 isFundPage 参数）
 * 2. 在页面组件中使用 FundDataManager 组件自动检测路由
 */
export function useFundDataManagement(options: Omit<UseFundDataOptions, 'isFundPage'> = {}) {
  // 不使用 useLocation，避免 Router 依赖问题
  // 改为由外部组件传入 isFundPage
  return useFundDataManagementInternal({
    ...options,
    isFundPage: false, // 默认不在基金页面，由 FundDataManager 组件控制
  });
}

/**
 * 基金数据管理组件（用于自动检测路由）
 * 
 * 使用方式：
 * <FundDataManager options={{ enableCleanup: true, ... }} />
 */
export function FundDataManager({ options }: { options?: Omit<UseFundDataOptions, 'isFundPage'> }) {
  const [isFundPage, setIsFundPage] = useState(false);
  
  // 检测当前是否在基金页面
  useEffect(() => {
    // 简单检测：检查 URL pathname
    const checkIsFundPage = () => {
      const pathname = window.location.pathname;
      const fundPaths = ['/fund', '/fund/ranking', '/fund/hot-sectors', '/fund/recommended', '/fund/detail'];
      const isFund = fundPaths.some(path => pathname.startsWith(path));
      setIsFundPage(isFund);
    };
    
    // 初始检查
    checkIsFundPage();
    
    // 监听 popstate 事件（浏览器前进/后退）
    window.addEventListener('popstate', checkIsFundPage);
    
    // 监听 hashchange 事件
    window.addEventListener('hashchange', checkIsFundPage);
    
    return () => {
      window.removeEventListener('popstate', checkIsFundPage);
      window.removeEventListener('hashchange', checkIsFundPage);
    };
  }, []);
  
  // 使用内部 Hook
  useFundDataManagementInternal({
    ...options,
    isFundPage,
  });
  
  // 不渲染任何内容
  return null;
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
