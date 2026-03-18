/**
 * 股票相关 API 服务
 * 
 * 提供股票列表、K 线数据、实时行情等接口
 */
import api from './api'
import type { DataSourceConfig } from './dataSource'

/** 股票基本信息 */
export interface StockBasic {
  code: string
  name: string
  market: string
  industry?: string
  area?: string
  list_date?: string
  total_shares?: number
  float_shares?: number
}

/** K 线数据 */
export interface KLineData {
  code: string
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount?: number
  turnover_rate?: number
  pre_close?: number
}

/** 实时行情 */
export interface RealtimeQuote {
  code: string
  name: string
  price: number
  change: number
  change_pct: number
  high: number
  low: number
  open: number
  prev_close: number
  volume: number
  amount: number
  turnover_rate: number
  [key: string]: any
}

/** K 线查询参数 */
export interface KLineParams extends DataSourceConfig {
  period?: string
  startDate?: string
  endDate?: string
  adjust?: string
  priorityLoad?: boolean
}

/** 获取股票列表参数 */
export interface StockListParams extends DataSourceConfig {
  // 可以添加过滤参数
  market?: string
  industry?: string
}

export const stockApi = {
  /**
   * 获取股票列表（支持多数据源优先级控制）
   * 
   * @param params 查询参数
   */
  getStockList: (params?: StockListParams) =>
    api.get<StockBasic[]>('/stock/list', {
      params: {
        source: 'auto',
        source_priority: params?.sourcePriority || '',
        source_exclude: params?.sourceExclude || '',
        fallback: params?.fallback ?? true,
        market: params?.market,
        industry: params?.industry,
      }
    }),
  
  /**
   * 获取单只股票基本信息
   * 
   * @param code 股票代码
   */
  getStockInfo: (code: string) =>
    api.get<StockBasic>(`/stock/${code}`),
  
  /**
   * 获取 K 线数据（支持多数据源优先级控制）
   * 
   * @param code 股票代码
   * @param params K 线参数
   */
  getKline: (code: string, params?: KLineParams) =>
    api.get<KLineData[]>(`/stock/${code}/kline`, {
      params: {
        period: params?.period || 'daily',
        start_date: params?.startDate,
        end_date: params?.endDate,
        adjust: params?.adjust || 'qfq',
        priority_load: params?.priorityLoad ?? true,
        source: 'auto',
        source_priority: params?.sourcePriority || '',
        source_exclude: params?.sourceExclude || '',
        fallback: params?.fallback ?? true,
      },
      timeout: 120000, // 2 分钟超时
    }),
  
  /**
   * 获取实时行情
   * 
   * @param code 股票代码
   */
  getRealtimeQuote: (code: string) =>
    api.get<RealtimeQuote>(`/stock/${code}/realtime`),
}

export default stockApi
