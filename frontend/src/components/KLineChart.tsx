/**
 * K 线图表组件 - 专业金融风格
 * 配色与 Chakra UI 主题完美协调
 */
import React, { useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { Box, Spinner, Flex } from '@chakra-ui/react'

export interface KLineData {
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount?: number
  turnover_rate?: number
  pre_close?: number  // 昨日收盘价
}

export interface TechnicalIndicator {
  date: string
  macd?: number
  macd_signal?: number
  macd_hist?: number
  rsi6?: number
  rsi12?: number
  rsi24?: number
  ma5?: number
  ma10?: number
  ma20?: number
  ma60?: number
}

export type KLineType = 'daily' | 'weekly' | 'monthly'

interface KLineChartProps {
  data: KLineData[]
  loading?: boolean
  type?: KLineType
  height?: string
  showVolume?: boolean
}

interface IndicatorChartProps {
  data: TechnicalIndicator[]
  loading?: boolean
  height?: string
}

/**
 * K 线图表组件
 */
export const KLineChart: React.FC<KLineChartProps> = ({
  data = [],
  loading = false,
  type = 'daily',
  height = '400px',
  showVolume = true,
}) => {
  // 根据类型生成图表配置
  const option = useMemo(() => {
    if (!data || data.length === 0) {
      return getEmptyOption()
    }

    return getKLineOption(data, type, showVolume)
  }, [data, type, showVolume])

  if (loading) {
    return (
      <Flex justify="center" align="center" h={height}>
        <Spinner size="xl" color="brand.400" />
      </Flex>
    )
  }

  return (
    <Box w="100%" h={height}>
      <ReactECharts
        option={option}
        style={{ height: '100%', width: '100%' }}
        notMerge={true}
        opts={{ renderer: 'canvas' }}
      />
    </Box>
  )
}

/**
 * 技术指标图表组件
 */
export const IndicatorChart: React.FC<IndicatorChartProps> = ({
  data = [],
  loading = false,
  height = '300px',
}) => {
  const option = useMemo(() => {
    if (!data || data.length === 0) {
      return getEmptyOption()
    }

    return getIndicatorOption(data)
  }, [data])

  if (loading) {
    return (
      <Flex justify="center" align="center" h={height}>
        <Spinner size="xl" color="brand.400" />
      </Flex>
    )
  }

  return (
    <Box w="100%" h={height}>
      <ReactECharts
        option={option}
        style={{ height: '100%', width: '100%' }}
        notMerge={true}
        opts={{ renderer: 'canvas' }}
      />
    </Box>
  )
}

/**
 * 获取空数据时的图表配置
 */
const getEmptyOption = () => ({
  title: {
    text: '暂无数据',
    left: 'center',
    top: 'center',
    textStyle: { color: '#a0aec0', fontSize: 14 },
  },
  xAxis: { show: false },
  yAxis: { show: false },
})

/**
 * 格式化日期显示（专业金融风格）
 * 智能分级显示：根据数据类型和上下文动态调整
 */
const formatDate = (dateStr: string, type: KLineType, index: number, allDates: string[]): string => {
  if (!dateStr) return ''
  
  // 标准化日期格式为 YYYY-MM-DD
  const cleanDate = dateStr.replace(/-/g, '')
  const year = cleanDate.substring(0, 4)
  const month = cleanDate.substring(4, 6)
  const day = cleanDate.substring(6, 8)
  
  if (type === 'monthly') {
    // 月线：数据量大时只显示年，否则显示年月
    if (allDates.length > 120) {
      return year  // 超过 10 年数据，只显示年
    }
    return `${year}-${month}`  // 年月格式
  } else if (type === 'weekly') {
    // 周线：智能分级显示
    const prevDate = index > 0 ? allDates[index - 1] : null
    if (prevDate) {
      const prevClean = prevDate.replace(/-/g, '')
      const prevYear = prevClean.substring(0, 4)
      const prevMonth = prevClean.substring(4, 6)
      
      // 新年份，显示年月
      if (year !== prevYear) {
        return `${year}-${month}`
      }
      // 新月份，显示年月 - 日（带年份的月份变化）
      if (month !== prevMonth) {
        return `${year}-${month}-${day}`
      }
    } else {
      // 第一个数据点，显示年月 - 日
      return `${year}-${month}-${day}`
    }
    // 普通周，显示月 - 日
    return `${month}-${day}`
  } else {
    // 日线：智能分级显示
    const prevDate = index > 0 ? allDates[index - 1] : null
    if (prevDate) {
      const prevClean = prevDate.replace(/-/g, '')
      const prevYear = prevClean.substring(0, 4)
      const prevMonth = prevClean.substring(4, 6)
      const prevDay = prevClean.substring(6, 8)
      
      // 新年份，显示完整日期
      if (year !== prevYear) {
        return `${year}-${month}-${day}`
      }
      // 新月份，显示月 - 日
      if (month !== prevMonth) {
        return `${month}-${day}`
      }
      // 每月 1 号，显示月 - 日
      if (day === '01') {
        return `${month}-${day}`
      }
    } else {
      // 第一个数据点，显示完整日期
      return `${year}-${month}-${day}`
    }
    // 普通日期，显示月 - 日
    return `${month}-${day}`
  }
}

/**
 * 获取 K 线图表配置（Chakra UI 协调配色）
 */
const getKLineOption = (
  data: KLineData[],
  type: KLineType,
  showVolume: boolean
) => {
  // 配色方案：基于 Chakra UI 主题，专业协调
  const colors = {
    // 背景 - Chakra UI 浅色主题
    bgColor: '#FFFFFF',
    cardBg: '#FFFFFF',
    // K 线颜色 - 指定配色
    upColor: '#d60a22',        // 上涨红
    downColor: '#037b66',      // 下跌绿
    upBg: 'rgba(214, 10, 34, 0.05)',
    downBg: 'rgba(3, 123, 102, 0.05)',
    // 均线颜色 - 专业金融配色
    ma5Color: '#F59E0B',       // 琥珀色 - 5 日线（醒目）
    ma10Color: '#3B82F6',      // 蓝色 - 10 日线（清晰）
    ma20Color: '#8B5CF6',      // 紫色 - 20 日线（稳重）
    // 辅助色 - Chakra UI 灰度系统
    textColor: '#1A202C',      // Chakra gray.900
    subTextColor: '#4A5568',   // Chakra gray.600
    mutedColor: '#718096',     // Chakra gray.500
    gridColor: '#E2E8F0',      // Chakra gray.200
    axisColor: '#CBD5E0',      // Chakra gray.300
    // 成交量 - 与 K 线统一配色（实心）
    volumeUp: '#d60a22',    // 上涨红（实心）
    volumeDown: '#037b66',  // 下跌绿（实心）
  }

  // 格式化日期显示（FinScope 风格，带索引）
  const allDates = data.map(d => d.date)
  const dates = data.map((k, index) => formatDate(k.date, type, index, allDates))
  const ohlc = data.map((k) => [k.open, k.close, k.low, k.high])
  const volumes = data.map((k) => k.volume)

  const typeLabels = {
    daily: 'K 线',
    weekly: '周 K 线',
    monthly: '月 K 线',
  }

  // 根据数据量智能设置标签间隔（动态显示）
  const dataLength = dates.length
  const getLabelInterval = () => {
    if (dataLength > 300) return Math.floor(dataLength / 60)  // 显示约 60 个标签
    if (dataLength > 200) return Math.floor(dataLength / 50)  // 显示约 50 个标签
    if (dataLength > 100) return Math.floor(dataLength / 30)  // 显示约 30 个标签
    if (dataLength > 50) return Math.floor(dataLength / 20)   // 显示约 20 个标签
    return 0 // 显示所有标签
  }

  const labelInterval = getLabelInterval()
  
  // 最小化时增加间隔，避免重叠
  const minLabelInterval = Math.max(labelInterval, Math.floor(dataLength / 10))

  const gridConfig = showVolume
    ? [
        { left: '5%', right: '5%', bottom: '35%', height: '55%' },
        { left: '5%', right: '5%', top: '72%', height: '20%' },
      ]
    : [{ left: '5%', right: '5%', bottom: '8%', height: '84%' }]

  const xAxisConfig = showVolume
    ? [
        {
          type: 'category',
          data: dates,
          gridIndex: 0,
          axisLine: { 
            show: false,
          },
          axisTick: { show: false },
          axisLabel: { 
            color: colors.subTextColor,
            interval: minLabelInterval,
            rotate: 0,
            fontSize: 9,
            fontWeight: 400,
          },
          splitLine: {
            show: false,
          },
          axisPointer: {
            show: true,
            lineStyle: {
              color: colors.gridColor,
              width: 1,
              type: 'dotted',
            },
          },
        },
        {
          type: 'category',
          data: dates,
          gridIndex: 1,
          axisLine: { 
            show: false,
          },
          axisTick: { show: false },
          axisLabel: { 
            show: false,
          },
          splitLine: {
            show: false,
          },
          axisPointer: {
            show: true,
            lineStyle: {
              color: colors.gridColor,
              width: 1,
              type: 'dotted',
            },
          },
        },
      ]
    : [
        {
          type: 'category',
          data: dates,
          axisLine: { 
            show: false,
          },
          axisTick: { show: false },
          axisLabel: { 
            color: colors.subTextColor,
            interval: minLabelInterval,
            rotate: 0,
            fontSize: 10,
            fontWeight: 400,
          },
          splitLine: {
            show: false,
          },
        },
      ]

  const yAxisConfig = showVolume
    ? [
        {
          scale: true,
          gridIndex: 0,
          axisLine: { 
            show: false,  // 隐藏轴线
          },
          axisTick: { show: false },
          axisLabel: { 
            color: colors.subTextColor,
            fontSize: 10,
            fontWeight: 400,
            formatter: (value: number) => value.toFixed(2),
          },
          splitLine: { 
            show: true,
            lineStyle: { 
              color: colors.gridColor, 
              type: 'solid',
              width: 1,
            },
          },
          splitNumber: 4,
        },
        {
          scale: true,
          gridIndex: 1,
          splitLine: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { show: false },
          splitNumber: 2,
        },
      ]
    : [
        {
          scale: true,
          axisLine: { show: false },
          axisTick: { show: false },
          axisLabel: { 
            color: colors.subTextColor,
            fontSize: 10,
            fontWeight: 400,
            formatter: (value: number) => value.toFixed(2),
          },
          splitLine: { 
            show: true,
            lineStyle: { 
              color: colors.gridColor, 
              type: 'solid',
              width: 1,
            },
          },
          splitNumber: 4,
        },
      ]

  // 计算移动平均线
  const calculateMA = (period: number): (number | '-')[] => {
    const result: (number | '-')[] = []
    for (let i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push('-')
        continue
      }
      const sum = data.slice(i - period + 1, i + 1).reduce((s, d) => s + d.close, 0)
      result.push(+(sum / period).toFixed(2))
    }
    return result
  }

  const ma5 = calculateMA(5)
  const ma10 = calculateMA(10)
  const ma20 = calculateMA(20)

  const seriesConfig: any[] = [
    {
      name: typeLabels[type],
      type: 'candlestick',
      data: ohlc,
      itemStyle: {
        color: colors.upColor,
        color0: colors.downColor,
        borderColor: colors.upColor,
        borderColor0: colors.downColor,
      },
      barWidth: '70%',
    },
    {
      name: 'MA5',
      type: 'line',
      data: ma5,
      smooth: false,
      lineStyle: {
        color: colors.ma5Color,
        width: 1.5,
        type: 'solid',
      },
      symbol: 'none',
      showSymbol: false,
      z: 10,
    },
    {
      name: 'MA10',
      type: 'line',
      data: ma10,
      smooth: false,
      lineStyle: {
        color: colors.ma10Color,
        width: 1.5,
        type: 'solid',
      },
      symbol: 'none',
      showSymbol: false,
      z: 10,
    },
    {
      name: 'MA20',
      type: 'line',
      data: ma20,
      smooth: false,
      lineStyle: {
        color: colors.ma20Color,
        width: 1.5,
        type: 'solid',
      },
      symbol: 'none',
      showSymbol: false,
      z: 10,
    },
  ]

  if (showVolume) {
    seriesConfig.push({
      name: '成交量',
      type: 'bar',
      xAxisIndex: 1,
      yAxisIndex: 1,
      data: volumes,
      itemStyle: {
        color: (params: any) => {
          const idx = params.dataIndex
          const klineData = data[idx]
          if (!klineData) return colors.volumeUp
          const isUp = klineData.close >= klineData.open
          return isUp ? colors.volumeUp : colors.volumeDown
        },
      },
      barWidth: '70%',
    })
  }

  return {
    backgroundColor: colors.bgColor,
    axisPointer: {
      link: { xAxisIndex: 'all' },
      mode: 'axis',
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: { 
        type: 'cross',
        lineStyle: {
          color: colors.gridColor,
          width: 1,
          type: 'dotted',
        },
      },
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: colors.gridColor,
      borderWidth: 1,
      textStyle: { 
        color: colors.textColor,
        fontSize: 11,
        fontWeight: 400,
      },
      extraCssText: 'box-shadow: 0 8px 32px rgba(0, 0, 0, 0.12); border-radius: 8px; padding: 12px 16px;',
      formatter: (params: any[]) => {
        const date = params[0]?.axisValue || ''
        const klineParam = params.find(p => p.seriesName === typeLabels[type])
        if (!klineParam) return date
        
        const [open, close, low, high] = klineParam.data
        const index = klineParam.dataIndex
        const klineData = data[index]
        
        // 使用昨日收盘价计算涨跌（如果没有昨收数据，则使用开盘价）
        const preClose = klineData?.pre_close || open
        const change = close - preClose
        const changePercent = preClose > 0 ? ((change / preClose) * 100).toFixed(2) : '0.00'
        const isUp = change >= 0
        
        const formatVolume = (value: number) => {
          if (value >= 1e8) return (value / 1e8).toFixed(2) + '亿'
          if (value >= 1e4) return (value / 1e4).toFixed(2) + '万'
          return value.toFixed(0)
        }
        
        const formatAmount = (value: number) => {
          if (value >= 1e8) return (value / 1e8).toFixed(2) + '亿'
          if (value >= 1e4) return (value / 1e4).toFixed(2) + '万'
          return value.toFixed(0)
        }
        
        const volume = data[index]?.volume || 0
        const amount = data[index]?.amount || 0
        const turnoverRate = data[index]?.turnover_rate || 0
        
        return `
          <div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
            <div style="font-size: 13px; font-weight: 600; color: ${colors.textColor}; margin-bottom: 10px; padding-bottom: 8px; border-bottom: 1px solid ${colors.gridColor};">
              ${date}
            </div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px 16px; font-size: 12px;">
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: ${colors.mutedColor}; margin-right: 12px;">开盘</span>
                <span style="color: ${open <= close ? colors.upColor : colors.downColor}; font-weight: 600;">${open.toFixed(2)}</span>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: ${colors.mutedColor}; margin-right: 12px;">收盘</span>
                <span style="color: ${close >= open ? colors.upColor : colors.downColor}; font-weight: 600;">${close.toFixed(2)}</span>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: ${colors.mutedColor}; margin-right: 12px;">最高</span>
                <span style="color: ${colors.upColor}; font-weight: 600;">${high.toFixed(2)}</span>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: ${colors.mutedColor}; margin-right: 12px;">最低</span>
                <span style="color: ${colors.downColor}; font-weight: 600;">${low.toFixed(2)}</span>
              </div>
            </div>
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid ${colors.gridColor};">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: ${colors.mutedColor}; font-size: 11px;">涨跌额</span>
                <span style="color: ${isUp ? colors.upColor : colors.downColor}; font-weight: 700; font-size: 13px;">
                  ${change >= 0 ? '+' : ''}${change.toFixed(2)}
                </span>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <span style="color: ${colors.mutedColor}; font-size: 11px;">涨跌幅</span>
                <span style="color: ${isUp ? colors.upColor : colors.downColor}; font-weight: 700; font-size: 13px;">
                  ${changePercent}%
                </span>
              </div>
            </div>
            <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid ${colors.gridColor};">
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: ${colors.mutedColor}; font-size: 11px;">成交量</span>
                <span style="color: ${colors.textColor}; font-weight: 600;">${formatVolume(volume)}手</span>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">
                <span style="color: ${colors.mutedColor}; font-size: 11px;">成交额</span>
                <span style="color: ${colors.textColor}; font-weight: 600;">${formatAmount(amount)}</span>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="color: ${colors.mutedColor}; font-size: 11px;">换手率</span>
                <span style="color: ${colors.textColor}; font-weight: 600;">${turnoverRate.toFixed(2)}%</span>
              </div>
            </div>
          </div>
        `
      },
    },
    legend: {
      data: showVolume 
        ? [typeLabels[type], 'MA5', 'MA10', 'MA20', '成交量'] 
        : [typeLabels[type], 'MA5', 'MA10', 'MA20'],
      top: 10,
      left: '5%',
      itemWidth: 12,
      itemHeight: 12,
      textStyle: { 
        color: colors.subTextColor,
        fontSize: 11,
        fontWeight: 500,
      },
      itemStyle: {
        shadowBlur: 0,
      },
      padding: [5, 15, 5, 5],
    },
    grid: gridConfig,
    xAxis: xAxisConfig,
    yAxis: yAxisConfig,
    dataZoom: showVolume
      ? [
          { 
            type: 'inside', 
            xAxisIndex: [0, 1], 
            start: 50, 
            end: 100,
            zoomOnMouseWheel: true,
            moveOnMouseMove: true,
          },
          {
            show: true,
            xAxisIndex: [0, 1],
            type: 'slider',
            bottom: '3%',
            height: 14,
            backgroundColor: '#EDF2F7',
            fillerColor: 'rgba(49, 151, 149, 0.2)',
            borderColor: '#E2E8F0',
            handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H10.7v-1.2h2.6V24.4z M13.3,22.1H10.7v-6.8h2.6V22.1z',
            handleSize: '80%',
            handleStyle: {
              color: '#319795',
              shadowBlur: 2,
              shadowColor: 'rgba(0, 0, 0, 0.1)',
            },
            textStyle: { color: colors.mutedColor, fontSize: 10 },
          },
        ]
      : [
          { 
            type: 'inside', 
            xAxisIndex: [0], 
            start: 50, 
            end: 100,
            zoomOnMouseWheel: true,
            moveOnMouseMove: true,
          },
          {
            show: true,
            xAxisIndex: [0],
            type: 'slider',
            bottom: '1%',
            height: 14,
            backgroundColor: '#EDF2F7',
            fillerColor: 'rgba(49, 151, 149, 0.2)',
            borderColor: '#E2E8F0',
            handleIcon: 'path://M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H10.7v-1.2h2.6V24.4z M13.3,22.1H10.7v-6.8h2.6V22.1z',
            handleSize: '80%',
            handleStyle: {
              color: '#319795',
              shadowBlur: 2,
              shadowColor: 'rgba(0, 0, 0, 0.1)',
            },
            textStyle: { color: colors.mutedColor, fontSize: 10 },
          },
        ],
    series: seriesConfig,
  }
}

/**
 * 获取技术指标图表配置
 */
const getIndicatorOption = (data: TechnicalIndicator[]) => {
  const dates = data.map((i) => i.date)
  const macd = data.map((i) => i.macd ?? 0)
  const macdSignal = data.map((i) => i.macd_signal ?? 0)
  const macdHist = data.map((i) => i.macd_hist ?? 0)

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
    },
    legend: {
      data: ['MACD', 'Signal', 'Hist'],
      bottom: 0,
      textStyle: { color: '#64748b' },
    },
    grid: { left: '10%', right: '8%', bottom: '15%' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' },
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    series: [
      {
        name: 'MACD',
        type: 'line',
        data: macd,
        lineStyle: { color: '#2b6cb0' },
        itemStyle: { color: '#2b6cb0' },
      },
      {
        name: 'Signal',
        type: 'line',
        data: macdSignal,
        lineStyle: { color: '#2c5282' },
        itemStyle: { color: '#2c5282' },
      },
      {
        name: 'Hist',
        type: 'bar',
        data: macdHist,
        itemStyle: (params: any) => ({
          color:
            params.value >= 0
              ? 'rgba(239, 68, 68, 0.6)'
              : 'rgba(16, 185, 129, 0.6)',
        }),
      },
    ],
  }
}

export default KLineChart
