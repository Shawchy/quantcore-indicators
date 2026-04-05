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

  // 转换数据格式为 KLineChart 所需格式
  const klineData = useMemo(() => {
    if (!data || data.length === 0) {
      console.log('[ProKLineChart] 输入数据为空')
      return []
    }

    console.log('[ProKLineChart] 开始转换数据，原始数据量:', data.length)
    console.log('[ProKLineChart] 前 3 条原始数据:', data.slice(0, 3))
    
    const converted = data.map((item) => {
      // 检查 date 字段是否存在
      if (!item.date) {
        console.warn('[ProKLineChart] 缺少 date 字段:', item)
        return null
      }
      
      // 处理日期格式：后端可能返回 '20021107' 或 '2002-11-07'
      let dateStr = item.date
      if (/^\d{8}$/.test(dateStr)) {
        // YYYYMMDD 格式 -> YYYY-MM-DD
        dateStr = `${dateStr.substring(0, 4)}-${dateStr.substring(4, 6)}-${dateStr.substring(6, 8)}`
      }
      
      const timestamp = new Date(dateStr).getTime()
      if (isNaN(timestamp)) {
        console.warn('[ProKLineChart] 无效日期:', item.date, '原始数据:', item)
        return null
      }

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
    
    console.log('[ProKLineChart] 转换后数据量:', converted.length)
    if (converted.length > 0) {
      console.log('[ProKLineChart] 第一条数据:', converted[0])
      console.log('[ProKLineChart] 最后一条数据:', converted[converted.length - 1])
    } else {
      console.error('[ProKLineChart] 转换后数据为空！请检查原始数据格式')
    }
    
    return converted
  }, [data])

  // 初始化图表 - 使用自定义布局配置
  useEffect(() => {
    if (!chartRef.current) {
      console.warn('[ProKLineChart] DOM 未就绪，等待下次渲染')
      return
    }
    
    // 如果没有数据，等待数据加载完成
    if (klineData.length === 0) {
      console.log('[ProKLineChart] 等待数据加载...')
      return
    }

    // 1. 创建图表实例，使用自定义布局
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
    
    if (!chart) {
      console.error('[ProKLineChart] 图表初始化失败')
      return
    }

    console.log('[ProKLineChart] 图表初始化成功，布局：candle' + (showVolume ? ' + VOL' : ''))

    // 2. 设置标的信息
    chart.setSymbol({
      ticker: 'STOCK',
      name: '股票'
    })

    // 3. 设置周期
    const periodMap: Record<string, { span: number; type: 'day' | 'week' | 'month' }> = {
      daily: { span: 1, type: 'day' as const },
      weekly: { span: 1, type: 'week' as const },
      monthly: { span: 1, type: 'month' as const }
    }
    chart.setPeriod(periodMap[type])

    // 4. 设置数据加载器
    chart.setDataLoader({
      getBars: ({ callback }: { callback: (data: any[]) => void }) => {
        // 如果有数据，返回数据
        if (klineData && klineData.length > 0) {
          console.log('[ProKLineChart] 加载数据:', klineData.length, '条')
          callback(klineData)
        } else {
          // 否则返回空数组
          callback([])
        }
      }
    })

    // 5. 清理函数
    return () => {
      console.log('[ProKLineChart] 销毁图表')
      if (chartInstance.current) {
        dispose(chartRef.current as unknown as string)
        chartInstance.current = null
      }
    }
  }, [klineData, type, showVolume]) // 添加依赖项，当数据加载完成或类型变化时重新初始化

  // 更新数据 - 当数据变化时重新加载
  useEffect(() => {
    if (!chartInstance.current || klineData.length === 0) return
    
    console.log('[ProKLineChart] 更新数据:', klineData.length, '条')
    
    // 重新加载数据
    chartInstance.current.setDataLoader({
      getBars: ({ callback }: { callback: (data: any[]) => void }) => {
        callback(klineData)
      }
    })
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
