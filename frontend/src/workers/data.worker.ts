/**
 * 数据处理 Worker
 * 负责处理原始 K 线数据，不阻塞主线程
 */

interface WorkerMessage {
  type: 'PROCESS_DATA' | 'CALC_INDICATORS' | 'FORMAT_DATA'
  data: any
  id?: string
}

interface WorkerResponse {
  type: 'DATA_READY' | 'INDICATORS_READY' | 'ERROR'
  data: any
  id?: string
  error?: string
}

// 处理数据
function processData(rawData: any[]): any[] {
  try {
    return rawData.map(item => ({
      date: item.date || '',
      open: parseFloat(item.open) || 0,
      high: parseFloat(item.high) || 0,
      low: parseFloat(item.low) || 0,
      close: parseFloat(item.close) || 0,
      volume: parseFloat(item.volume) || 0,
      amount: item.amount ? parseFloat(item.amount) : null,
      turnover_rate: item.turnover_rate ? parseFloat(item.turnover_rate) : null
    }))
  } catch (error) {
    console.error('数据处理失败:', error)
    throw error
  }
}

// 格式化指标数据
function formatIndicators(indicators: any): any {
  try {
    const formatted: any = {}
    
    if (indicators.MA) {
      formatted.MA = indicators.MA.map((item: any) => ({
        date: item.date,
        ma5: item.ma5 !== null ? parseFloat(item.ma5) : null,
        ma10: item.ma10 !== null ? parseFloat(item.ma10) : null,
        ma20: item.ma20 !== null ? parseFloat(item.ma20) : null,
        ma60: item.ma60 !== null ? parseFloat(item.ma60) : null
      }))
    }
    
    if (indicators.MACD) {
      formatted.MACD = indicators.MACD.map((item: any) => ({
        date: item.date,
        macd: item.macd !== null ? parseFloat(item.macd) : null,
        macd_signal: item.macd_signal !== null ? parseFloat(item.macd_signal) : null,
        macd_hist: item.macd_hist !== null ? parseFloat(item.macd_hist) : null
      }))
    }
    
    if (indicators.RSI) {
      formatted.RSI = indicators.RSI.map((item: any) => ({
        date: item.date,
        rsi6: item.rsi6 !== null ? parseFloat(item.rsi6) : null,
        rsi12: item.rsi12 !== null ? parseFloat(item.rsi12) : null,
        rsi24: item.rsi24 !== null ? parseFloat(item.rsi24) : null
      }))
    }
    
    if (indicators.KDJ) {
      formatted.KDJ = indicators.KDJ.map((item: any) => ({
        date: item.date,
        kdj_k: item.kdj_k !== null ? parseFloat(item.kdj_k) : null,
        kdj_d: item.kdj_d !== null ? parseFloat(item.kdj_d) : null,
        kdj_j: item.kdj_j !== null ? parseFloat(item.kdj_j) : null
      }))
    }
    
    return formatted
  } catch (error) {
    console.error('指标格式化失败:', error)
    throw error
  }
}

// 合并 K 线和指标数据
function mergeData(kline: any[], indicators: any): any[] {
  try {
    return kline.map((candle, index) => {
      const merged: any = { ...candle }
      
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

// Worker 消息处理
self.onmessage = function(e: MessageEvent<WorkerMessage>) {
  const { type, data, id } = e.data
  
  try {
    switch (type) {
      case 'PROCESS_DATA':
        const processed = processData(data)
        const response: WorkerResponse = {
          type: 'DATA_READY',
          data: processed,
          id
        }
        self.postMessage(response)
        break
      
      case 'FORMAT_DATA':
        const formatted = formatIndicators(data)
        self.postMessage({
          type: 'DATA_READY',
          data: formatted,
          id
        })
        break
      
      case 'CALC_INDICATORS':
        // 所有指标计算已统一使用后端 quantcore-indicators (Rust) 模块
        // 前端不实现指标计算，避免不一致
        self.postMessage({
          type: 'ERROR',
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
