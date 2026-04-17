/**
 * 智能轮询 Hook (useSmartPolling)
 * 
 * 针对爬虫数据源优化的前端数据获取方案：
 * - 动态调整轮询频率（根据市场状态和用户等级）
 * - 批量请求合并（减少API调用）
 * - 增量更新渲染（只刷新变化的字段）
 * - 页面可见性感知（不可见时暂停）
 * - 随机抖动（模拟人类行为）
 * 
 * 使用示例：
 * ```tsx
 * const { data, loading, error } = useSmartPolling({
 *   codes: ['000001', '600000'],
 *   userTier: 'premium',
 *   baseInterval: 30000,
 * });
 * ```
 */

import { useState, useEffect, useCallback, useRef } from 'react';

interface SmartPollingOptions {
  /** 股票代码列表 */
  codes: string[];
  /** 用户等级 (normal/premium/enterprise) */
  userTier?: 'normal' | 'premium' | 'enterprise';
  /** 基础间隔（毫秒） */
  baseInterval?: number;
  /** 随机抖动范围（0-1，表示±百分比） */
  jitterRange?: number;
  /** 波动模式（大盘波动大时加速） */
  volatilityMode?: boolean;
  /** 页面非活跃时暂停 */
  pauseOnBlur?: boolean;
  /** 是否启用增量更新 */
  enableDelta?: boolean;
  /** 强制刷新 */
  forceRefresh?: boolean;
  /** 调试模式（输出日志） */
  debug?: boolean;
}

interface SmartPollingResult {
  /** 行情数据 {code: quoteData} */
  data: Record<string, any>;
  /** 上次更新时间 */
  lastUpdate: Date | null;
  /** 是否正在加载 */
  loading: boolean;
  /** 错误信息 */
  error: string | null;
  /** 是否暂停 */
  isPaused: boolean;
  /** 下次建议间隔（毫秒） */
  nextInterval: number;
  /** 统计信息 */
  stats: {
    totalRequests: number;
    cacheHits: number;
    freshFetches: number;
    errors: number;
  };
  /** 手动触发刷新 */
  refresh: () => void;
  /** 暂停轮询 */
  pause: () => void;
  /** 恢复轮询 */
  resume: () => void;
}

export function useSmartPolling(options: SmartPollingOptions): SmartPollingResult {
  const {
    codes = [],
    userTier = 'normal',
    baseInterval = 30000,
    jitterRange = 0.3,
    volatilityMode = true,
    pauseOnBlur = true,
    enableDelta = true,
    forceRefresh = false,
    debug = false,
  } = options;

  const [data, setData] = useState<Record<string, any>>({});
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isPaused, setIsPaused] = useState(false);
  const [nextInterval, setNextInterval] = useState(baseInterval);

  const statsRef = useRef({
    totalRequests: 0,
    cacheHits: 0,
    freshFetches: 0,
    errors: 0,
  });

  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const prevDataRef = useRef<Record<string, any>>({});
  const abortRef = useRef<AbortController | null>(null);

  /**
   * 计算智能间隔
   * 根据市场状态、波动程度、用户等级动态调整
   */
  const calculateInterval = useCallback((): number => {
    let interval = baseInterval;

    // 添加随机抖动（模拟人类行为的随机性）
    if (jitterRange > 0) {
      const jitter = (Math.random() - 0.5) * 2 * jitterRange;
      interval *= (1 + jitter);
    }

    // 波动模式：根据上次数据变化幅度调整
    if (volatilityMode && Object.keys(prevDataRef.current).length > 0) {
      const maxChange = Math.max(
        ...Object.values(prevDataRef.current).map((d: any) =>
          Math.abs(d.change_pct || 0)
        )
      );

      // 波动>2%时加快一倍，平稳时减慢
      if (maxChange > 2) {
        interval *= 0.6; // 加速
        debug && console.log(`[SmartPolling] 波动加大(${maxChange}%)，加速至 ${Math.round(interval)}ms`);
      } else if (maxChange < 0.3) {
        interval *= 1.4; // 减速
        debug && console.log(`[SmartPolling] 市场平稳(${maxChange}%)，减速至 ${Math.round(interval)}ms`);
      }
    }

    // 用户等级调整
    const tierMultipliers: Record<string, number> = {
      normal: 1.0,
      premium: 0.7,
      enterprise: 0.5,
    };
    interval *= tierMultipliers[userTier] || 1.0;

    // 确保最小间隔（保护数据源）
    interval = Math.max(interval, 10000); // 最少10秒

    return Math.round(interval);
  }, [baseInterval, jitterRange, volatilityMode, userTier, debug]);

  /**
   * 数据获取函数
   */
  const fetchData = useCallback(async () => {
    if (codes.length === 0) return;

    // 取消之前的请求
    if (abortRef.current) {
      abortRef.current.abort();
    }
    abortRef.current = new AbortController();

    setLoading(true);
    setError(null);
    statsRef.current.totalRequests++;

    try {
      const startTime = performance.now();

      const response = await fetch('/api/v1/realtime/batch', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          codes,
          user_tier: userTier,
          force_refresh: forceRefresh,
          include_delta: enableDelta,
        }),
        signal: abortRef.current.signal,
      });

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('请求过于频繁，请稍后再试');
        }
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const result = await response.json();

      const elapsed = performance.now() - startTime;
      debug && console.log(`[SmartPolling] 请求完成 (${elapsed.toFixed(0)}ms)`);

      if (result.success) {
        // 更新统计
        if (result.cached_count > 0) {
          statsRef.current.cacheHits += result.cached_count;
        }
        if (result.fresh_count > 0) {
          statsRef.current.freshFetches += result.fresh_count;
        }

        // 处理增量更新
        if (enableDelta && result.delta && Object.keys(prevDataRef.current).length > 0) {
          applyDeltaUpdate(result.data, result.delta);
        } else {
          setData(result.data);
        }

        prevDataRef.current = result.data;
        setLastUpdate(new Date());
        setNextInterval(result.next_interval * 1000 || calculateInterval());

        debug &&
          console.log('[SmartPolling]', {
            cached: result.cached_count,
            fresh: result.fresh_count,
            nextInterval: result.next_interval,
          });
      } else {
        throw new Error(result.message || '获取数据失败');
      }
    } catch (err: any) {
      if (err.name === 'AbortError') {
        debug && console.log('[SmartPolling] 请求被取消');
        return;
      }

      statsRef.current.errors++;
      const errorMessage = err.message || '网络错误';
      setError(errorMessage);
      console.error('[SmartPolling] 错误:', errorMessage);

      // 错误后延长间隔（退避策略）
      const backoffInterval = nextInterval * 2;
      setNextInterval(Math.min(backoffInterval, 300000)); // 最长5分钟
    } finally {
      setLoading(false);
    }
  }, [codes, userTier, forceRefresh, enableDelta, debug, calculateInterval, nextInterval]);

  /**
   * 应用增量更新到状态
   */
  const applyDeltaUpdate = (newData: Record<string, any>, delta: any) => {
    if (!delta || !delta.changed_codes) {
      setData(newData);
      return;
    }

    setData((prevData) => {
      const updated = { ...prevData };

      // 只更新变化的字段
      for (const code of delta.changed_codes) {
        if (newData[code]) {
          updated[code] = {
            ...updated[code],
            ...newData[code],
          };
        }
      }

      // 新增的股票
      for (const code of Object.keys(newData)) {
        if (!prevData[code]) {
          updated[code] = newData[code];
        }
      }

      return updated;
    });

    debug &&
      console.log('[SmartPolling] 增量更新:', {
        changedCodes: delta.changed_codes?.length,
        totalChanges: delta.total_changes,
      });
  };

  /**
   * 手动刷新
   */
  const refresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  /**
   * 暂停轮询
   */
  const pause = useCallback(() => {
    setIsPaused(true);
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    debug && console.log('[SmartPolling] 已暂停');
  }, [debug]);

  /**
   * 恢复轮询
   */
  const resume = useCallback(() => {
    setIsPaused(false);
    fetchData(); // 立即获取一次
    debug && console.log('[SmartPolling] 已恢复');
  }, [fetchData, debug]);

  // 主效应：设置定时器
  useEffect(() => {
    if (isPaused || codes.length === 0) return;

    // 立即执行一次
    fetchData();

    // 设置定时器
    intervalRef.current = setInterval(() => {
      if (!isPaused) {
        fetchData();
      }
    }, nextInterval);

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [codes.join(','), nextInterval, isPaused, fetchData]);

  // 页面可见性监听
  useEffect(() => {
    if (!pauseOnBlur) return;

    const handleVisibilityChange = () => {
      if (document.hidden) {
        pause();
      } else {
        resume();
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [pauseOnBlur, pause, resume]);

  // 组件卸载清理
  useEffect(() => {
    return () => {
      if (abortRef.current) {
        abortRef.current.abort();
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, []);

  return {
    data,
    lastUpdate,
    loading,
    error,
    isPaused,
    nextInterval,
    stats: statsRef.current,
    refresh,
    pause,
    resume,
  };
}

export default useSmartPolling;
