/**
 * 数据处理 Worker
 * 负责处理原始 K 线数据，不阻塞主线程
 */

interface RawKlineItem {
  date: string
  open: string | number
  high: string | number
  low: string | number
  close: string | number
  volume: string | number
  amount?: string | number
  turnover_rate?: string | number
}

interface KlineItem {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount: number | null
  turnover_rate: number | null
}

interface MARawItem {
  date: string
  ma5: string | number | null
  ma10: string | number | null
  ma20: string | number | null
  ma60: string | number | null
}

interface MAItem {
  date: string
  ma5: number | null
  ma10: number | null
  ma20: number | null
  ma60: number | null
}

interface MACDRawItem {
  date: string
  macd: string | number | null
  macd_signal: string | number | null
  macd_hist: string | number | null
}

interface MACDItem {
  date: string
  macd: number | null
  macd_signal: number | null
  macd_hist: number | null
}

interface RSIRawItem {
  date: string
  rsi6: string | number | null
  rsi12: string | number | null
  rsi24: string | number | null
}

interface RSIItem {
  date: string
  rsi6: number | null
  rsi12: number | null
  rsi24: number | null
}

interface KDJRawItem {
  date: string
  kdj_k: string | number | null
  kdj_d: string | number | null
  kdj_j: string | number | null
}

interface KDJItem {
  date: string
  kdj_k: number | null
  kdj_d: number | null
  kdj_j: number | null
}

interface IndicatorInput {
  MA?: MARawItem[]
  MACD?: MACDRawItem[]
  RSI?: RSIRawItem[]
  KDJ?: KDJRawItem[]
}

interface FormattedIndicators {
  MA?: MAItem[]
  MACD?: MACDItem[]
  RSI?: RSIItem[]
  KDJ?: KDJItem[]
}

interface MergedKlineItem extends KlineItem {
  ma5?: number | null
  ma10?: number | null
  ma20?: number | null
  ma60?: number | null
  macd?: number | null
  macd_signal?: number | null
  macd_hist?: number | null
  rsi6?: number | null
  rsi12?: number | null
  rsi24?: number | null
  kdj_k?: number | null
  kdj_d?: number | null
  kdj_j?: number | null
}

type WorkerMessageData = RawKlineItem[] | IndicatorInput | null

interface WorkerMessage {
  type: 'PROCESS_DATA' | 'CALC_INDICATORS' | 'FORMAT_DATA'
  data: WorkerMessageData
  id?: string
}

type WorkerResponseData = KlineItem[] | FormattedIndicators | null

interface WorkerResponse {
  type: 'DATA_READY' | 'INDICATORS_READY' | 'ERROR'
  data: WorkerResponseData
  id?: string
  error?: string
}

function processData(rawData: RawKlineItem[]): KlineItem[] {
  try {
    return rawData.map(item => ({
      date: item.date || '',
      open: parseFloat(String(item.open)) || 0,
      high: parseFloat(String(item.high)) || 0,
      low: parseFloat(String(item.low)) || 0,
      close: parseFloat(String(item.close)) || 0,
      volume: parseFloat(String(item.volume)) || 0,
      amount: item.amount ? parseFloat(String(item.amount)) : null,
      turnover_rate: item.turnover_rate ? parseFloat(String(item.turnover_rate)) : null
    }))
  } catch (error) {
    console.error('数据处理失败:', error)
    throw error
  }
}

function formatIndicators(indicators: IndicatorInput): FormattedIndicators {
  try {
    const formatted: FormattedIndicators = {}

    if (indicators.MA) {
      formatted.MA = indicators.MA.map((item: MARawItem) => ({
        date: item.date,
        ma5: item.ma5 !== null ? parseFloat(String(item.ma5)) : null,
        ma10: item.ma10 !== null ? parseFloat(String(item.ma10)) : null,
        ma20: item.ma20 !== null ? parseFloat(String(item.ma20)) : null,
        ma60: item.ma60 !== null ? parseFloat(String(item.ma60)) : null
      }))
    }

    if (indicators.MACD) {
      formatted.MACD = indicators.MACD.map((item: MACDRawItem) => ({
        date: item.date,
        macd: item.macd !== null ? parseFloat(String(item.macd)) : null,
        macd_signal: item.macd_signal !== null ? parseFloat(String(item.macd_signal)) : null,
        macd_hist: item.macd_hist !== null ? parseFloat(String(item.macd_hist)) : null
      }))
    }

    if (indicators.RSI) {
      formatted.RSI = indicators.RSI.map((item: RSIRawItem) => ({
        date: item.date,
        rsi6: item.rsi6 !== null ? parseFloat(String(item.rsi6)) : null,
        rsi12: item.rsi12 !== null ? parseFloat(String(item.rsi12)) : null,
        rsi24: item.rsi24 !== null ? parseFloat(String(item.rsi24)) : null
      }))
    }

    if (indicators.KDJ) {
      formatted.KDJ = indicators.KDJ.map((item: KDJRawItem) => ({
        date: item.date,
        kdj_k: item.kdj_k !== null ? parseFloat(String(item.kdj_k)) : null,
        kdj_d: item.kdj_d !== null ? parseFloat(String(item.kdj_d)) : null,
        kdj_j: item.kdj_j !== null ? parseFloat(String(item.kdj_j)) : null
      }))
    }

    return formatted
  } catch (error) {
    console.error('指标格式化失败:', error)
    throw error
  }
}

function mergeData(kline: KlineItem[], indicators: FormattedIndicators): MergedKlineItem[] {
  try {
    return kline.map((candle, index) => {
      const merged: MergedKlineItem = { ...candle }

      if (indicators.MA && indicators.MA[index]) {
        merged.ma5 = indicators.MA[index].ma5
        merged.ma10 = indicators.MA[index].ma10
        merged.ma20 = indicators.MA[index].ma20
        merged.ma60 = indicators.MA[index].ma60
      }

      if (indicators.MACD && indicators.MACD[index]) {
        merged.macd = indicators.MACD[index].macd
        merged.macd_signal = indicators.MACD[index].macd_signal
        merged.macd_hist = indicators.MACD[index].macd_hist
      }

      if (indicators.RSI && indicators.RSI[index]) {
        merged.rsi6 = indicators.RSI[index].rsi6
        merged.rsi12 = indicators.RSI[index].rsi12
        merged.rsi24 = indicators.RSI[index].rsi24
      }

      if (indicators.KDJ && indicators.KDJ[index]) {
        merged.kdj_k = indicators.KDJ[index].kdj_k
        merged.kdj_d = indicators.KDJ[index].kdj_d
        merged.kdj_j = indicators.KDJ[index].kdj_j
      }

      return merged
    })
  } catch (error) {
    console.error('数据合并失败:', error)
    throw error
  }
}

self.onmessage = function(e: MessageEvent<WorkerMessage>) {
  const { type, data, id } = e.data

  try {
    switch (type) {
      case 'PROCESS_DATA':
        const processed = processData(data as RawKlineItem[])
        const response: WorkerResponse = {
          type: 'DATA_READY',
          data: processed,
          id
        }
        self.postMessage(response)
        break

      case 'FORMAT_DATA':
        const formatted = formatIndicators(data as IndicatorInput)
        self.postMessage({
          type: 'DATA_READY',
          data: formatted,
          id
        })
        break

      case 'CALC_INDICATORS':
        self.postMessage({
          type: 'ERROR',
          data: null,
          error: '指标计算已统一使用后端 quantcore-indicators (Rust) 模块，请通过 API 获取指标数据',
          id
        })
        break

      default:
        throw new Error(`未知的消息类型：${type}`)
    }
  } catch (error) {
    const errorResponse: WorkerResponse = {
      type: 'ERROR',
      data: null,
      error: error instanceof Error ? error.message : '未知错误',
      id
    }
    self.postMessage(errorResponse)
  }
}
