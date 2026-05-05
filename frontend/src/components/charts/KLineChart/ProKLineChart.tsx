/**
 * ProKLineChart 组件
 * 基于 KLineChart v10 的专业金融 K 线图组件
 * 文档：https://klinecharts.com/
 * 
 * 参考官方示例：https://klinecharts.com/guide/quick-start
 */

import React, { useEffect, useRef, useMemo } from 'react'
import { Box, Spinner, Flex, Text } from '@chakra-ui/react'
import type { KLineData } from '@/types'
import { init, dispose } from 'klinecharts'

export type KLineType = 'daily' | 'weekly' | 'monthly'

interface ProKLineChartProps {
  data: KLineData[]
  loading?: boolean
  type?: KLineType
  height?: string
  showVolume?: boolean
}

export const ProKLineChart: React.FC<ProKLineChartProps> = ({
  data = [],
  loading = false,
  type = 'daily',
  height = '500px',
  showVolume = true
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<any>(null)

  const klineData = useMemo(() => {
    if (!data || data.length === 0) return []

    const converted = data.map((item) => {
      if (!item.date) return null
      
      let dateStr = item.date
      if (/^\d{8}$/.test(dateStr)) {
        dateStr = `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
      }
      
      const timestamp = new Date(dateStr).getTime()
      if (isNaN(timestamp)) return null

      return {
        timestamp,
        open: Number(item.open) || 0,
        high: Number(item.high) || 0,
        low: Number(item.low) || 0,
        close: Number(item.close) || 0,
        volume: Number(item.volume) || 0,
        turnover: Number(item.amount) || 0
      }
    }).filter(Boolean)
    
    return converted
  }, [data])

  useEffect(() => {
    if (!chartRef.current) return
    if (klineData.length === 0) return

    const chart = init(chartRef.current as HTMLElement, {
      layout: [
        {
          type: 'candle' as const,
          content: ['MA'],
          options: { order: Number.MIN_SAFE_INTEGER }
        },
        ...(showVolume ? [{
          type: 'indicator' as const,
          content: ['VOL'],
          options: { order: 10 }
        }] : []),
        {
          type: 'xAxis' as const,
          options: { order: 9 }
        }
      ]
    })
    chartInstance.current = chart
    
    if (!chart) return

    chart.setSymbol({
      ticker: 'STOCK',
      name: '股票'
    })

    const periodMap: Record<string, { span: number; type: 'day' | 'week' | 'month' }> = {
      daily: { span: 1, type: 'day' as const },
      weekly: { span: 1, type: 'week' as const },
      monthly: { span: 1, type: 'month' as const }
    }
    chart.setPeriod(periodMap[type])

    chart.setDataLoader({
      getBars: ({ callback }: { callback: (data: any[]) => void }) => {
        if (klineData && klineData.length > 0) {
          callback(klineData)
        } else {
          callback([])
        }
      }
    })

    return () => {
      if (chartInstance.current) {
        dispose(chartRef.current as unknown as string)
        chartInstance.current = null
      }
    }
  }, [klineData, type, showVolume])

  useEffect(() => {
    if (!chartInstance.current || klineData.length === 0) return
    
    chartInstance.current.setDataLoader({
      getBars: ({ callback }: { callback: (data: any[]) => void }) => {
        callback(klineData)
      }
    })
  }, [klineData])

  if (loading) {
    return (
      <Flex justify="center" align="center" h={height} w="100%">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    )
  }

  if (klineData.length === 0) {
    return (
      <Flex justify="center" align="center" h={height} w="100%" bg="gray.50">
        <Text color="gray.500">暂无数据</Text>
      </Flex>
    )
  }

  return <Box ref={chartRef} h={height} w="100%" />
}

export default ProKLineChart
