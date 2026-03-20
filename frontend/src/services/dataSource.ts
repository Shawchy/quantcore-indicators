/**
 * 数据源管理 API 服务
 * 
 * 提供数据源健康检查、优先级配置、性能统计等功能
 */
import api from './api'

/** 数据源健康状态 */
export interface DataSourceHealth {
  name: string
  status: 'healthy' | 'degraded' | 'unavailable'
  response_time_ms: number
  success_rate: number
  last_check: string
  error_message?: string
}

/** 数据源统计信息 */
export interface DataSourceStats {
  total_requests: number
  failed_requests: number
  avg_response_time_ms: number
  cache_hit_rate: number
}

/** 数据源性能统计 */
export interface PerformanceStats {
  stats: Record<string, DataSourceStats>
  recommended_priority: string[]
  recommendation_reason: string
}

/** 数据源配置选项 */
export interface DataSourceConfig {
  sourcePriority?: string  // 优先级列表，如："efinance,akshare"
  sourceExclude?: string   // 排除的数据源，如："yfinance"
  fallback?: boolean       // 是否允许故障转移
}

export const dataSourceApi = {
  /**
   * 获取所有数据源健康状态
   */
  getHealth: () =>
    api.get<Record<string, DataSourceHealth>>('/data-source/health'),
  
  /**
   * 获取可用数据源列表
   */
  getAvailableSources: () =>
    api.get<string[]>('/data-source/sources'),
  
  /**
   * 切换默认数据源
   * 
   * @param sourceName 数据源名称
   * @param setAsDefault 是否设为默认
   */
  switchSource: (sourceName: string, setAsDefault = true) =>
    api.post('/data-source/switch', null, {
      params: { source_name: sourceName, set_as_default: setAsDefault }
    }),
  
  /**
   * 获取数据源统计信息
   * 
   * @param sourceName 数据源名称
   */
  getStats: (sourceName: string) =>
    api.get<DataSourceStats>(`/data-source/stats/${sourceName}`),
  
  /**
   * 获取性能统计（含推荐优先级）
   */
  getPerformanceStats: () =>
    api.get<PerformanceStats>('/data-source/performance-stats'),
}

export default dataSourceApi
