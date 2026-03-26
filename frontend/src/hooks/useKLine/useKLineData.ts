/**
 * useKLineData Hook
 * 负责获取 K 线数据
 */

import { useState, useEffect, useCallback, useRef } from 'react'
import type { KLineData, AllIndicators, KType, IndicatorType, KLineAPIResponse } from '@/types/chart'

interface UseKLineDataOptions {
  code: string
  kType?: KType
  start_date?: string
  end_date?: string
  indicators?: IndicatorType[]
  adjust?: 'qfq' | 'hfq' | 'no'
  useCache?: boolean
  enabled?: boolean
}

interface UseKLineDataReturn {
  data: KLineData[] | null
  indicators: AllIndicators | null
  loading: boolean
  error: Error | null
  refetch: () => Promise<void>
  metadata?: any
}

// 数据缓存
const dataCache = new Map<string, { data: KLineAPIResponse; timestamp: number }>()
const CACHE_DURATION = 5 * 60 * 1000 // 5 分钟

export function useKLineData(options: UseKLineDataOptions): UseKLineDataReturn {
  const {
    code,
    kType = 'daily',
    start_date,
    end_date,
    indicators = ['MA', 'MACD', 'RSI'],
    adjust = 'qfq',
    useCache = true,
    enabled = true
  } = options

  const [data, setData] = useState<KLineData[] | null>(null)
  const [indicatorData, setIndicatorData] = useState<AllIndicators | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)
  const [metadata, setMetadata] = useState<any>(null)
  
  const abortControllerRef = useRef<AbortController | null>(null)

  // 生成缓存键
  const cacheKey = `${code}_${kType}_${start_date || 'all'}_${end_date || 'all'}_${indicators.join(',')}_${adjust}`

  // 获取数据
  const fetchData = useCallback(async () => {
    // 取消之前的请求
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }

    // 创建新的 AbortController
    abortControllerRef.current = new AbortController()

    // 检查缓存
      if (useCache) {
        const cached = dataCache.get(cacheKey)
        if (cached && Date.now() - cached.timestamp < CACHE_DURATION) {
          setData(cached.data.data)
          setIndicatorData(cached.data.indicators)
          setMetadata(cached.data.metadata)
          return
        }
      }

    setLoading(true)
    setError(null)

    let isAborted = false

    try {
      // 构建 URL
      const params = new URLSearchParams({
        k_type: kType,
        adjust,
        indicators: indicators.join(',')
      })

      if (start_date) params.append('start_date', start_date)
      if (end_date) params.append('end_date', end_date)

      const url = `/api/v1/kline/${code}?${params.toString()}`

      // 发起请求
      const response = await fetch(url, {
        signal: abortControllerRef.current.signal
      })

      if (!response.ok) {
        throw new Error(`HTTP 错误：${response.status}`)
      }

      const result: KLineAPIResponse = await response.json()

      // 更新状态
      setData(result.data)
      setIndicatorData(result.indicators)
      setMetadata(result.metadata)

      // 缓存数据
      if (useCache) {
        dataCache.set(cacheKey, {
          data: result,
          timestamp: Date.now()
        })
      }

    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        console.log('请求已取消')
        isAborted = true
        return
      }
      setError(err instanceof Error ? err : new Error('未知错误'))
    } finally {
      if (!isAborted) {
        setLoading(false)
      }
    }
  }, [code, kType, start_date, end_date, indicators, adjust, useCache, cacheKey])

  // 自动获取数据
  useEffect(() => {
    if (enabled) {
      fetchData()
    }

    // 清理函数
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort()
      }
    }
  }, [enabled, fetchData])

  return {
    data,
    indicators: indicatorData,
    loading,
    error,
    refetch: fetchData,
    metadata
  }
}
