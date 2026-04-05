/**
 * K 线图表类型定义
 */

// K 线数据 - 使用类型联合避免索引签名冲突
export interface KLineData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount?: number
  turnover_rate?: number
  ma5?: number | null
  ma10?: number | null
  ma20?: number | null
  ma60?: number | null
  // 允许其他动态属性
  [key: string]: any
}

// 技术指标数据
export interface IndicatorData {
  date: string
  // 允许其他动态属性
  [key: string]: any
}

// MA 指标
export interface MAData extends IndicatorData {
  ma5: number | null
  ma10: number | null
  ma20: number | null
  ma60: number | null
}

// MACD 指标
export interface MACDData extends IndicatorData {
  macd: number | null
  macd_signal: number | null
  macd_hist: number | null
}

// RSI 指标
export interface RSIData extends IndicatorData {
  rsi6: number | null
  rsi12: number | null
  rsi24: number | null
}

// KDJ 指标
export interface KDJData extends IndicatorData {
  kdj_k: number | null
  kdj_d: number | null
  kdj_j: number | null
}

// BOLL 指标
export interface BOLLData extends IndicatorData {
  boll_upper: number | null
  boll_middle: number | null
  boll_lower: number | null
}

// ATR 指标
export interface ATRData extends IndicatorData {
  atr: number | null
}

// 所有指标集合
export interface AllIndicators {
  MA?: MAData[]
  MACD?: MACDData[]
  RSI?: RSIData[]
  KDJ?: KDJData[]
  BOLL?: BOLLData[]
  ATR?: ATRData[]
}

// K 线类型
export type KType = 'daily' | 'weekly' | 'monthly' | '1m' | '5m' | '15m' | '30m' | '60m'

// 指标类型
export type IndicatorType = 'MA' | 'MACD' | 'RSI' | 'KDJ' | 'BOLL' | 'ATR'

// 图表配置
export interface ChartConfig {
  width: number
  height: number
  candleWidth: number
  candleSpacing: number
  colors: {
    up: string
    down: string
    ma5: string
    ma10: string
    ma20: string
    ma60: string
    grid: string
    text: string
    axis: string
  }
  margins: {
    top: number
    right: number
    bottom: number
    left: number
  }
}

// 渲染数据
export interface RenderData {
  kline: KLineData[]
  indicators?: AllIndicators
  config: ChartConfig
  [key: string]: any // 允许其他动态属性
}

// Worker 消息类型
export interface WorkerMessage {
  type: 'PROCESS_DATA' | 'CALC_INDICATORS' | 'FORMAT_DATA'
  data: any
}

export interface WorkerResponse {
  type: 'DATA_READY' | 'INDICATORS_READY' | 'ERROR'
  data: any
  error?: string
}

// Hook 返回类型
export interface UseKLineReturn {
  data: KLineData[] | null
  indicators: AllIndicators | null
  loading: boolean
  calculating: boolean
  rendering: boolean
  error: Error | null
  refresh: () => Promise<void>
  calculate: (indicators: IndicatorType[]) => Promise<void>
}

// API 响应类型
export interface KLineAPIResponse {
  status: string
  data: KLineData[]
  indicators: AllIndicators
  metadata: {
    code: string
    k_type: string
    count: number
    adjust: string
  }
  performance: {
    fetch_time_ms: number
    calc_time_ms: number
    total_ms: number
  }
}
