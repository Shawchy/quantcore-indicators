/**
 * ProKLineChart 组件
 * 基于 KLineChart v10 的专业金融 K 线图组件
 * 文档：https://klinecharts.com/
 */

import React, { useEffect, useRef, useMemo } from 'react'
import { Box, Spinner, Flex, Text } from '@chakra-ui/react'
import type { KLineData } from '@/types'
import * as klinecharts from 'klinecharts'

export type KLineType = 'daily' | 'weekly' | 'monthly'

interface ProKLineChartProps {
  data: KLineData[]
  loading?: boolean
  type?: KLineType
  height?: string
  showVolume?: boolean
  showIndicators?: boolean
  indicators?: string[]
}

export const ProKLineChart: React.FC<ProKLineChartProps> = ({
  data = [],
  loading = false,
  height = '400px',
  showVolume = true,
  showIndicators = true,
  indicators = ['MA', 'MACD', 'RSI']
}) => {
  const chartRef = useRef<HTMLDivElement>(null)
  const chartInstance = useRef<any>(null)

  // 转换数据格式为 KLineChart 所需格式
  const klineData = useMemo(() => {
    if (!data || data.length === 0) {
      return []
    }

    return data.map((item) => ({
      timestamp: new Date(item.date).getTime(),
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
      volume: item.volume,
      turnover: item.amount || 0
    }))
  }, [data])

  // 初始化图表
  useEffect(() => {
    if (!chartRef.current || klineData.length === 0) return

    // 创建图表实例
    chartInstance.current = klinecharts.init(chartRef.current)
    
    if (!chartInstance.current) {
      console.error('[ProKLineChart] 图表初始化失败')
      return
    }

    // 应用数据
    chartInstance.current.applyNewData(klineData)

    // 清理函数
    return () => {
      if (chartInstance.current) {
        chartInstance.current.dispose()
        chartInstance.current = null
      }
    }
  }, [])

  // 更新数据
  useEffect(() => {
    if (!chartInstance.current || klineData.length === 0) return
    
    chartInstance.current.applyNewData(klineData)
  }, [klineData])

  // Loading 状态
  if (loading) {
    return (
      <Flex justify="center" align="center" h={height} w="100%">
        <Spinner size="xl" color="brand.500" />
      </Flex>
    )
  }

  // 无数据状态
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
