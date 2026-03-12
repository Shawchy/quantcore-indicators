/**
 * ECharts 图表配置工具函数
 * 提供通用的图表配置模板，减少代码重复
 */

import { COLORS } from '../constants'

/**
 * 获取柱状图配置
 * @param data - 图表数据数组
 * @param dataKey - 数据项的键名
 * @param labelKey - 标签的键名
 * @param title - 图表标题
 * @returns ECharts 配置对象
 */
export const getBarOption = (
  data: any[],
  dataKey: string = 'change_pct',
  labelKey: string = 'name',
  title?: string
) => {
  const top10 = data.slice(0, 10)

  return {
    backgroundColor: 'transparent',
    title: title
      ? {
          text: title,
          left: 'center',
          textStyle: {
            color: '#1e293b',
            fontSize: 14,
            fontWeight: 'bold',
          },
        }
      : undefined,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' },
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
    },
    grid: { left: '15%', right: '5%', bottom: '10%', top: title ? '15%' : '5%' },
    xAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    yAxis: {
      type: 'category',
      data: top10.map((item) => item[labelKey]).reverse(),
      axisLabel: { width: 80, overflow: 'truncate', color: '#64748b' },
      axisLine: { lineStyle: { color: '#e2e8f0' } },
    },
    series: [
      {
        type: 'bar',
        data: top10
          .map((item) => ({
            value: item[dataKey] || 0,
            itemStyle: {
              color: (params: any) => (params.value >= 0 ? COLORS.UP : COLORS.DOWN),
            },
          }))
          .reverse(),
        barWidth: '60%',
      },
    ],
  }
}

/**
 * 获取 K 线图配置
 * @param dates - 日期数组
 * @param closes - 收盘价数组
 * @param volumes - 成交量数组
 * @returns ECharts 配置对象
 */
export const getKlineOption = (dates: string[], closes: number[], volumes: number[]) => {
  return {
    backgroundColor: 'transparent',
    animation: true,
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' },
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
    },
    grid: { left: '10%', right: '5%', bottom: '15%', top: '5%' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b', rotate: 45 },
    },
    yAxis: [
      {
        type: 'value',
        scale: true,
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b' },
        splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
      },
      {
        type: 'value',
        scale: true,
        axisLine: { lineStyle: { color: '#e2e8f0' } },
        axisLabel: { color: '#64748b' },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        type: 'line',
        data: closes,
        smooth: true,
        symbol: 'none',
        lineStyle: { color: COLORS.PRIMARY, width: 2 },
        areaStyle: {
          type: 'linear' as any,
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
            { offset: 1, color: 'rgba(59, 130, 246, 0.05)' },
          ],
        },
      },
      {
        type: 'bar',
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: {
            type: 'linear' as any,
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(59, 130, 246, 0.5)' },
              { offset: 1, color: 'rgba(59, 130, 246, 0.1)' },
            ],
          } as any,
        },
      },
    ],
  }
}

/**
 * 获取饼图配置
 * @param data - 图表数据数组 [{name, value}]
 * @param title - 图表标题
 * @returns ECharts 配置对象
 */
export const getPieOption = (data: Array<{ name: string; value: number }>, title?: string) => {
  return {
    backgroundColor: 'transparent',
    title: title
      ? {
          text: title,
          left: 'center',
          textStyle: {
            color: '#1e293b',
            fontSize: 14,
            fontWeight: 'bold',
          },
        }
      : undefined,
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
      formatter: '{b}: {c} ({d}%)',
    },
    legend: {
      orient: 'vertical',
      right: '5%',
      top: 'center',
      textStyle: { color: '#64748b' },
    },
    series: [
      {
        type: 'pie',
        radius: ['40%', '70%'],
        center: ['40%', '50%'],
        data: data,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          color: '#64748b',
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.2)',
          },
        },
      },
    ],
  }
}

/**
 * 获取折线图配置
 * @param data - 图表数据数组
 * @param dataKey - 数据项的键名
 * @param labelKey - 标签的键名
 * @param lineColor - 线条颜色
 * @returns ECharts 配置对象
 */
export const getLineOption = (
  data: any[],
  dataKey: string = 'value',
  labelKey: string = 'date',
  lineColor: string = COLORS.PRIMARY
) => {
  const dates = data.map((item) => item[labelKey])
  const values = data.map((item) => item[dataKey] || 0)

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'axis',
      backgroundColor: 'rgba(255, 255, 255, 0.95)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
    },
    grid: { left: '10%', right: '5%', bottom: '10%', top: '5%' },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b', rotate: 45 },
    },
    yAxis: {
      type: 'value',
      scale: true,
      axisLine: { lineStyle: { color: '#e2e8f0' } },
      axisLabel: { color: '#64748b' },
      splitLine: { lineStyle: { color: '#f1f5f9', type: 'dashed' } },
    },
    series: [
      {
        type: 'line',
        data: values,
        smooth: true,
        symbol: 'circle',
        symbolSize: 6,
        lineStyle: { color: lineColor, width: 2 },
        itemStyle: { color: lineColor },
        areaStyle: {
          type: 'linear' as any,
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: lineColor.replace(')', ', 0.3)').replace('rgb', 'rgba') },
            { offset: 1, color: lineColor.replace(')', ', 0.05)').replace('rgb', 'rgba') },
          ],
        } as any,
      },
    ],
  }
}

/**
 * 获取资金流向图配置
 * @param data - 资金流向数据
 * @returns ECharts 配置对象
 */
export const getMoneyFlowOption = (data: {
  super?: number
  big?: number
  mid?: number
  small?: number
}) => {
  const pieData = [
    { name: '超大单', value: data.super || 0 },
    { name: '大单', value: data.big || 0 },
    { name: '中单', value: data.mid || 0 },
    { name: '小单', value: data.small || 0 },
  ]

  return {
    backgroundColor: 'transparent',
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(255, 255, 255, 0.98)',
      borderColor: '#e2e8f0',
      textStyle: { color: '#1e293b' },
      formatter: '{b}: {c} ({d}%)',
    },
    series: [
      {
        type: 'pie',
        radius: ['50%', '70%'],
        center: ['50%', '50%'],
        data: pieData,
        itemStyle: {
          borderRadius: 5,
          borderColor: '#fff',
          borderWidth: 2,
        },
        label: {
          color: '#64748b',
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.2)',
          },
        },
      },
    ],
  }
}
