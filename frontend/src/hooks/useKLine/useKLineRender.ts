/**
 * useKLineRender Hook
 * 负责图表渲染优化（防抖、节流）
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import type { KLineData, AllIndicators, ChartConfig, RenderData } from '@/types/chart'

interface UseKLineRenderOptions {
  data: KLineData[] | null
  indicators?: AllIndicators | null
  width?: number
  height?: number
  candleWidth?: number
}

interface UseKLineRenderReturn {
  renderData: RenderData | null
  rendering: boolean
  config: ChartConfig | null
}

// 默认配置
const defaultConfig: ChartConfig = {
  width: 800,
  height: 500,
  candleWidth: 10,
  candleSpacing: 2,
  colors: {
    up: '#ef232a',      // 红色（A 股上涨）
    down: '#14cf1a',    // 绿色（A 股下跌）
    ma5: '#ff9800',
    ma10: '#2196f3',
    ma20: '#9c27b0',
    ma60: '#795548',
    grid: '#e0e0e0',
    text: '#333333',
    axis: '#999999'
  },
  margins: {
    top: 20,
    right: 60,
    bottom: 30,
    left: 10
  }
}

// 防抖函数
function debounce<T extends (...args: any[]) => any>(
  fn: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timer: ReturnType<typeof setTimeout> | null = null
  
  return (...args: Parameters<T>) => {
    if (timer) clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}

export function useKLineRender(options: UseKLineRenderOptions): UseKLineRenderReturn {
  const {
    data,
    indicators,
    width = 800,
    height = 500,
    candleWidth = 10
  } = options

  const [renderData, setRenderData] = useState<RenderData | null>(null)
  const [rendering, setRendering] = useState(false)

  // 生成图表配置
  const config = useMemo<ChartConfig>(() => {
    return {
      ...defaultConfig,
      width,
      height,
      candleWidth
    }
  }, [width, height, candleWidth])

  // 渲染函数
  const doRender = useCallback(() => {
    if (!data || !config) {
      setRenderData(null)
      return
    }

    setRendering(true)

    // 使用 requestAnimationFrame 优化渲染
    requestAnimationFrame(() => {
      const merged: RenderData = {
        kline: data,
        indicators: indicators || undefined,
        config
      }

      setRenderData(merged)
      setRendering(false)
    })
  }, [data, indicators, config])

  // 防抖渲染
  const debouncedRender = useCallback(
    debounce(() => {
      doRender()
    }, 100),
    [doRender]
  )

  // 监听数据变化，自动渲染
  useEffect(() => {
    if (data && data.length > 0) {
      debouncedRender()
    }
  }, [data, indicators, debouncedRender])

  return {
    renderData,
    rendering,
    config
  }
}
