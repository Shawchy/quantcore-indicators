/**
 * useKLineCalc Hook
 * 使用 Web Worker 计算指标
 */

import { useState, useCallback, useEffect } from 'react'
import type { KLineData, AllIndicators, IndicatorType } from '@/types/chart'
import { workerPool } from '@/workers/worker.pool'

interface UseKLineCalcOptions {
  data: KLineData[] | null
  indicators?: IndicatorType[]
  useWorker?: boolean
}

interface UseKLineCalcReturn {
  indicators: AllIndicators | null
  calculating: boolean
  error: Error | null
  calculate: (data: KLineData[], indicators: IndicatorType[]) => Promise<void>
}

export function useKLineCalc(options: UseKLineCalcOptions): UseKLineCalcReturn {
  const {
    data,
    indicators = ['MA', 'MACD', 'RSI'],
    useWorker = true
  } = options

  const [calculatedIndicators, setCalculatedIndicators] = useState<AllIndicators | null>(null)
  const [calculating, setCalculating] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  // 计算指标
  const calculate = useCallback(async (
    klineData: KLineData[],
    indicatorTypes: IndicatorType[]
  ) => {
    if (!klineData || klineData.length === 0) {
      setCalculatedIndicators(null)
      return
    }

    setCalculating(true)
    setError(null)

    try {
      if (useWorker) {
        // 使用 Worker 处理数据 - 传入K线数据和指标类型
        const result = await workerPool.postMessage({
          type: 'PROCESS_DATA',
          data: klineData
        })

        // Worker只处理数据格式化，指标计算由后端完成
        // 这里可以添加额外的客户端指标计算逻辑
        setCalculatedIndicators(result)
      } else {
        // 不使用 Worker，直接处理（简单实现）
        // 实际应该调用后端 API 计算
        console.log('直接处理指标计算')
      }
    } catch (err) {
      setError(err instanceof Error ? err : new Error('计算失败'))
    } finally {
      setCalculating(false)
    }
  }, [useWorker])

  // 监听后端返回的指标数据
  useEffect(() => {
    // 数据已经由后端计算好，这里主要是格式化
    if (data && indicators.length > 0) {
      // 后端已经返回了指标数据，不需要额外计算
      // 这个 Hook 主要用于前端二次计算或缓存
    }
  }, [data, indicators])

  return {
    indicators: calculatedIndicators,
    calculating,
    error,
    calculate
  }
}
