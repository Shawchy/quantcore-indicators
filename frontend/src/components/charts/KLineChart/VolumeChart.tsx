/**
 * VolumeChart 组件
 * 成交量图表
 */

import React, { useEffect, useRef } from 'react'
import type { KLineData } from '@/types/chart'

interface VolumeChartProps {
  data: KLineData[] | null
  height?: string
}

export const VolumeChart: React.FC<VolumeChartProps> = ({
  data,
  height = '100px'
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas || !data) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 调整 Canvas 大小
    const dpr = window.devicePixelRatio || 1
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * dpr
    canvas.height = rect.height * dpr
    ctx.scale(dpr, dpr)

    // 清空画布
    ctx.clearRect(0, 0, rect.width, rect.height)

    // 计算最大成交量
    const maxVolume = Math.max(...data.map(d => d.volume))

    // 绘制成交量柱状图
    const barWidth = (rect.width / data.length) * 0.8
    const spacing = (rect.width / data.length) * 0.2

    data.forEach((candle, index) => {
      const x = index * (barWidth + spacing) + spacing / 2
      const barHeight = (candle.volume / maxVolume) * (rect.height - 10)
      const y = rect.height - barHeight - 5

      const isUp = candle.close >= candle.open
      ctx.fillStyle = isUp ? '#ef232a' : '#14cf1a'

      ctx.fillRect(x, y, barWidth, barHeight)
    })

    // 绘制 Y 轴标签
    ctx.fillStyle = '#666'
    ctx.font = '10px Arial'
    ctx.textAlign = 'right'
    ctx.fillText((maxVolume / 10000).toFixed(0) + '万', rect.width - 2, 12)
    ctx.fillText('0', rect.width - 2, rect.height - 5)

  }, [data])

  return (
    <canvas
      ref={canvasRef}
      style={{ width: '100%', height }}
    />
  )
}

export default VolumeChart
