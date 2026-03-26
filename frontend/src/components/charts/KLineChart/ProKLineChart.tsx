/**
 * ProKLineChart 组件
 * 基于 KLineChart 库的专业金融 K 线图组件
 * 文档：https://v9.klinecharts.com/
 */

import React, { useEffect, useRef, useMemo } from 'react'
import { init, dispose } from 'klinecharts'
import { Box, Spinner, Flex, Text } from '@chakra-ui/react'
import type { KLineData } from '@/types'

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
    if (!data || data.length === 0) return []

    return data.map((item, index) => ({
      timestamp: new Date(item.date).getTime(),
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
      volume: item.volume,
      turnover: item.amount || 0,
      // 自定义字段
      _originalIndex: index,
      _date: item.date
    }))
  }, [data])

  // 初始化图表
  useEffect(() => {
    if (!chartRef.current || klineData.length === 0) return

    // 初始化图表实例
    chartInstance.current = init('kline-chart')

    // 应用数据
    chartInstance.current.applyNewData(klineData)

    // 清理函数
    return () => {
      if (chartInstance.current) {
        dispose('kline-chart')
        chartInstance.current = null
      }
    }
  }, [])

  // 更新数据
  useEffect(() => {
    if (!chartInstance.current || klineData.length === 0) return

    chartInstance.current.applyNewData(klineData)
  }, [klineData])

  // 配置图表选项
  useEffect(() => {
    if (!chartInstance.current) return

    // 设置图表配置
    chartInstance.current.setOptions({
      // 主题配置
      theme: {
        backgroundColor: '#ffffff',
        textColor: '#1e293b',
        gridColor: '#e2e8f0',
        crossHairColor: '#94a3b8'
      },

      // K 线柱子配置
      candle: {
        bar: {
          upColor: '#ef4444',      // 上涨红
          downColor: '#10b981',    // 下跌绿
          noChangeColor: '#64748b' // 平盘灰
        },
        area: {
          upColor: 'rgba(239, 68, 68, 0.1)',
          downColor: 'rgba(16, 185, 129, 0.1)'
        }
      },

      // 均线配置
      ma: {
        lines: [
          { period: 5, color: '#f59e0b' },   // MA5 - 琥珀色
          { period: 10, color: '#3b82f6' },  // MA10 - 蓝色
          { period: 20, color: '#8b5cf6' },  // MA20 - 紫色
          { period: 60, color: '#795548' }   // MA60 - 棕色
        ]
      },

      // 成交量配置
      volume: {
        show: showVolume,
        upColor: 'rgba(239, 68, 68, 0.6)',
        downColor: 'rgba(16, 185, 129, 0.6)'
      },

      // 技术指标配置
      technicalIndicators: {
        show: showIndicators,
        indicators: indicators
      },

      // X 轴配置
      xAxis: {
        type: 'category',
        axisLabel: {
          formatter: (timestamp: number) => {
            const date = new Date(timestamp)
            const month = String(date.getMonth() + 1).padStart(2, '0')
            const day = String(date.getDate()).padStart(2, '0')
            return `${month}-${day}`
          }
        }
      },

      // Y 轴配置
      yAxis: {
        scale: true,
        axisLabel: {
          formatter: (value: number) => value.toFixed(2)
        }
      },

      // 工具提示配置
      tooltip: {
        show: true,
        formatter: (data: any) => {
          const date = new Date(data.timestamp)
          const dateStr = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
          
          const change = data.close - data.open
          const changePercent = data.open > 0 ? ((change / data.open) * 100).toFixed(2) : '0.00'
          const isUp = change >= 0

          return `
            <div style="padding: 12px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
              <div style="font-size: 13px; font-weight: 600; color: #1e293b; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid #e2e8f0;">
                ${dateStr}
              </div>
              <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; font-size: 12px;">
                <div style="display: flex; justify-content: space-between;">
                  <span style="color: #64748b;">开盘</span>
                  <span style="color: ${data.close >= data.open ? '#ef4444' : '#10b981'}; font-weight: 600;">${data.open.toFixed(2)}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                  <span style="color: #64748b;">收盘</span>
                  <span style="color: ${data.close >= data.open ? '#ef4444' : '#10b981'}; font-weight: 600;">${data.close.toFixed(2)}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                  <span style="color: #64748b;">最高</span>
                  <span style="color: #ef4444; font-weight: 600;">${data.high.toFixed(2)}</span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                  <span style="color: #64748b;">最低</span>
                  <span style="color: #10b981; font-weight: 600;">${data.low.toFixed(2)}</span>
                </div>
              </div>
              <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 6px;">
                  <span style="color: #64748b; font-size: 11px;">涨跌额</span>
                  <span style="color: ${isUp ? '#ef4444' : '#10b981'}; font-weight: 700; font-size: 13px;">
                    ${change >= 0 ? '+' : ''}${change.toFixed(2)}
                  </span>
                </div>
                <div style="display: flex; justify-content: space-between;">
                  <span style="color: #64748b; font-size: 11px;">涨跌幅</span>
                  <span style="color: ${isUp ? '#ef4444' : '#10b981'}; font-weight: 700; font-size: 13px;">
                    ${changePercent}%
                  </span>
                </div>
              </div>
              <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid #e2e8f0;">
                <div style="display: flex; justify-content: space-between;">
                  <span style="color: #64748b; font-size: 11px;">成交量</span>
                  <span style="color: #1e293b; font-weight: 600;">
                    ${data.volume >= 1e8 ? (data.volume / 1e8).toFixed(2) + '亿' : data.volume >= 1e4 ? (data.volume / 1e4).toFixed(2) + '万' : data.volume.toFixed(0)}
                  </span>
                </div>
              </div>
            </div>
          `
        }
      },

      // 缩放和平移配置
      zoom: {
        enabled: true,
        minScale: 0.2,
        maxScale: 5
      },

      // 十字光标配置
      crosshair: {
        show: true,
        mode: 'cross'
      }
    })
  }, [showVolume, showIndicators, indicators])

  if (loading) {
    return (
      <Flex justify="center" align="center" h={height}>
        <Spinner size="xl" color="blue.500" thickness="3px" />
      </Flex>
    )
  }

  if (!data || data.length === 0) {
    return (
      <Flex justify="center" align="center" h={height} bg="white" borderRadius="lg" border="1px solid #e2e8f0">
        <Text color="gray.400" fontSize="lg">暂无 K 线数据</Text>
      </Flex>
    )
  }

  return (
    <Box w="100%" h={height} position="relative">
      <div
        id="kline-chart"
        style={{
          width: '100%',
          height: '100%',
          borderRadius: '8px',
          overflow: 'hidden'
        }}
        ref={chartRef}
      />
    </Box>
  )
}

export default ProKLineChart
