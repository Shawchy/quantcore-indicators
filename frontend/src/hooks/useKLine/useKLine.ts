/**
 * useKLine Hook
 * 统一的 K 线图表数据管理 Hook
 */

import { useMemo } from 'react'
import { useKLineData } from './useKLineData'
import { useKLineCalc } from './useKLineCalc'
import { useKLineRender } from './useKLineRender'
import type { KType, IndicatorType, UseKLineReturn } from '@/types/chart'

interface UseKLineOptions {
  code: string
  kType?: KType
  indicators?: IndicatorType[]
  adjust?: 'qfq' | 'hfq' | 'no'
  useWorker?: boolean
  useWebSocket?: boolean
  useCache?: boolean
  enabled?: boolean
}

export function useKLine(options: UseKLineOptions): UseKLineReturn {
  const {
    code,
    kType = 'daily',
    indicators = ['MA', 'MACD', 'RSI'],
    adjust = 'qfq',
    useWorker = true,
    useWebSocket = true,
    useCache = true,
    enabled = true
  } = options

  // 1. 获取数据
  const {
    data,
    indicators: backendIndicators,
    loading,
    error,
    refetch,
    metadata
  } = useKLineData({
    code,
    kType,
    indicators,
    adjust,
    useCache,
    enabled
  })

  // 2. 指标计算（目前主要由后端完成）
  const {
    indicators: calculatedIndicators,
    calculating,
    calculate
  } = useKLineCalc({
    data,
    indicators,
    useWorker
  })

  // 3. 渲染优化
  const {
    renderData,
    rendering,
    config
  } = useKLineRender({
    data,
    indicators: backendIndicators || calculatedIndicators
  })

  // 合并指标数据（后端 + 前端，优先使用后端数据）
  const mergedIndicators = useMemo(() => {
    if (backendIndicators && calculatedIndicators) {
      // 合并两者，后端数据优先
      return {
        ...calculatedIndicators,
        ...backendIndicators
      }
    }
    return backendIndicators || calculatedIndicators
  }, [backendIndicators, calculatedIndicators])

  return {
    data: renderData?.kline || data,
    indicators: mergedIndicators,
    loading: loading || calculating || rendering,
    calculating,
    rendering,
    error,
    refresh: refetch,
    calculate
  }
}

export default useKLine
