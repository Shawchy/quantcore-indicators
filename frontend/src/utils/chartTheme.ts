/** ECharts 通用 option 形状（与 echarts 版本解耦） */
type EChartsOptionShape = Record<string, unknown>

// 动态导入 echarts 以避免 require 警告
const getEchartsGraphic = () => {
  // eslint-disable-next-line @typescript-eslint/no-require-imports
  const echarts = require('echarts')
  return echarts.graphic
}

export const chartColors = {
  up: '#ef4444',
  down: '#10b981',
  primary: '#3b82f6',
  secondary: '#64748b',
  accent: '#f59e0b',
  background: '#ffffff',
  border: '#e2e8f0',
  text: '#1e293b',
  textSecondary: '#64748b',
  grid: '#f1f5f9',
}

export const getCommonOption = (): EChartsOptionShape => ({
  backgroundColor: chartColors.background,
  tooltip: {
    trigger: 'axis',
    backgroundColor: 'rgba(255, 255, 255, 0.98)',
    borderColor: chartColors.border,
    borderWidth: 1,
    textStyle: {
      color: chartColors.text,
      fontSize: 12,
    },
    axisPointer: {
      type: 'cross',
      lineStyle: {
        color: chartColors.primary,
        width: 1,
        type: 'dashed',
      },
    },
  },
  legend: {
    textStyle: {
      color: chartColors.textSecondary,
      fontSize: 12,
    },
    bottom: 0,
  },
  grid: {
    left: '10%',
    right: '5%',
    bottom: '15%',
    top: '10%',
    containLabel: true,
  },
  xAxis: {
    type: 'category',
    axisLine: {
      lineStyle: {
        color: chartColors.border,
      },
    },
    axisLabel: {
      color: chartColors.textSecondary,
      fontSize: 11,
    },
    axisTick: {
      lineStyle: {
        color: chartColors.border,
      },
    },
  },
  yAxis: {
    type: 'value',
    scale: true,
    axisLine: {
      show: false,
    },
    splitLine: {
      lineStyle: {
        color: chartColors.grid,
        type: 'dashed',
      },
    },
    axisLabel: {
      color: chartColors.textSecondary,
      fontSize: 11,
    },
    axisTick: {
      show: false,
    },
  },
})

export const getCandlestickOption = () => ({
  ...getCommonOption(),
  series: [
    {
      type: 'candlestick',
      itemStyle: {
        color: chartColors.up,
        color0: chartColors.down,
        borderColor: chartColors.up,
        borderColor0: chartColors.down,
      },
    },
  ],
})

export const getLineOption = (
  color = chartColors.primary,
  fillArea = false
) => ({
  ...getCommonOption(),
  series: [
    {
      type: 'line',
      smooth: true,
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: {
        color,
      },
      lineStyle: {
        width: 2,
      },
      areaStyle: fillArea
        ? {
            color: new (getEchartsGraphic().LinearGradient)(0, 0, 0, 1, [
              {
                offset: 0,
                color: color.replace(')', ', 0.3)').replace('rgb', 'rgba'),
              },
              {
                offset: 1,
                color: color.replace(')', ', 0.05)').replace('rgb', 'rgba'),
              },
            ]),
          }
        : undefined,
    },
  ],
})

export const getBarOption = (color = chartColors.primary) => ({
  ...getCommonOption(),
  series: [
    {
      type: 'bar',
      itemStyle: {
        color: new (getEchartsGraphic().LinearGradient)(0, 0, 0, 1, [
          {
            offset: 0,
            color: color,
          },
          {
            offset: 1,
            color: color.replace(')', ', 0.6)').replace('rgb', 'rgba'),
          },
        ]),
        borderRadius: [4, 4, 0, 0],
      },
    },
  ],
})

export const getPieOption = () => ({
  ...getCommonOption(),
  tooltip: {
    trigger: 'item',
    backgroundColor: 'rgba(255, 255, 255, 0.98)',
    borderColor: chartColors.border,
    textStyle: {
      color: chartColors.text,
    },
  },
  legend: {
    orient: 'vertical',
    right: 10,
    top: 'center',
    textStyle: {
      color: chartColors.textSecondary,
    },
  },
  series: [
    {
      type: 'pie',
      radius: ['40%', '70%'],
      center: ['40%', '50%'],
      itemStyle: {
        borderRadius: 8,
        borderColor: chartColors.background,
        borderWidth: 2,
      },
      label: {
        color: chartColors.text,
      },
    },
  ],
})

export const getVolumeOption = () => ({
  ...getCommonOption(),
  series: [
    {
      type: 'bar',
      itemStyle: {
        color: (params: any) => {
          const open = params.data[1]
          const close = params.data[2]
          return close >= open ? chartColors.up : chartColors.down
        },
      },
    },
  ],
})

export const getMACDOption = () => ({
  ...getCommonOption(),
  series: [
    {
      type: 'bar',
      itemStyle: {
        color: (params: any) => {
          const value = params.value
          return value >= 0
            ? chartColors.up.replace(')', ', 0.7)').replace('rgb', 'rgba')
            : chartColors.down.replace(')', ', 0.7)').replace('rgb', 'rgba')
        },
      },
    },
    {
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: {
        width: 1,
      },
    },
    {
      type: 'line',
      smooth: true,
      symbol: 'none',
      lineStyle: {
        width: 1,
        type: 'dashed',
      },
    },
  ],
})

export const theme = {
  colors: chartColors,
  getCommonOption,
  getCandlestickOption,
  getLineOption,
  getBarOption,
  getPieOption,
  getVolumeOption,
  getMACDOption,
}

export default theme
