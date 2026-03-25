/**
 * CanvasChart 组件
 * 基于 Canvas 的高性能 K 线图渲染引擎
 */

import React, { useEffect, useRef, useCallback } from 'react'
import type { RenderData, KLineData } from '@/types/chart'

interface CanvasChartProps {
  data: RenderData | null
  onZoom?: (scale: number) => void
  onPan?: (offset: number) => void
}

export const CanvasChart: React.FC<CanvasChartProps> = ({
  data,
  onZoom,
  onPan
}) => {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const animationFrameRef = useRef<number>()
  const isDragging = useRef(false)
  const lastMouseX = useRef(0)
  const [scrollOffset, setScrollOffset] = useState(0)
  const [visibleCount, setVisibleCount] = useState(100)

  // 计算可见区域的数据
  const visibleData = useMemo(() => {
    if (!data?.kline) return null
    
    const startIndex = Math.max(0, scrollOffset)
    const endIndex = Math.min(data.kline.length, scrollOffset + visibleCount)
    const sliced = data.kline.slice(startIndex, endIndex)
    
    // 保留原始索引用于绘制
    return sliced.map((item, idx) => ({
      ...item,
      _originalIndex: startIndex + idx
    }))
  }, [data, scrollOffset, visibleCount])

  // 价格转 Y 坐标
  const priceToY = useCallback((price: number, config: any) => {
    const { minPrice, maxPrice, height, margins } = config
    const priceRange = maxPrice - minPrice
    const chartHeight = height - margins.top - margins.bottom
    
    if (priceRange === 0) return margins.top + chartHeight / 2
    
    const y = margins.top + chartHeight - ((price - minPrice) / priceRange) * chartHeight
    return y
  }, [])

  // 绘制 K 线
  const drawKLines = useCallback((
    ctx: CanvasRenderingContext2D,
    kline: (KLineData & { _originalIndex?: number })[],
    config: any
  ) => {
    const { candleWidth, candleSpacing, colors } = config

    kline.forEach((candle, index) => {
      const x = index * (candleWidth + candleSpacing) + candleSpacing
      const centerX = x + candleWidth / 2
      
      const yOpen = priceToY(candle.open, config)
      const yClose = priceToY(candle.close, config)
      const yHigh = priceToY(candle.high, config)
      const yLow = priceToY(candle.low, config)

      const isUp = candle.close >= candle.open

      // 绘制影线
      ctx.beginPath()
      ctx.moveTo(centerX, yHigh)
      ctx.lineTo(centerX, yLow)
      ctx.strokeStyle = isUp ? colors.up : colors.down
      ctx.lineWidth = 1
      ctx.stroke()

      // 绘制实体
      ctx.fillStyle = isUp ? colors.up : colors.down
      const bodyTop = Math.min(yOpen, yClose)
      const bodyHeight = Math.max(Math.abs(yClose - yOpen), 1) // 至少 1 像素
      ctx.fillRect(x, bodyTop, candleWidth, bodyHeight)
    })
  }, [priceToY])

  // 绘制均线
  const drawMovingAverages = useCallback((
    ctx: CanvasRenderingContext2D,
    kline: (KLineData & { _originalIndex?: number })[],
    config: any
  ) => {
    const { candleWidth, candleSpacing, colors } = config

    // MA5
    ctx.beginPath()
    ctx.strokeStyle = colors.ma5
    ctx.lineWidth = 1.5
    kline.forEach((candle, index) => {
      if (candle.ma5 !== null && candle.ma5 !== undefined) {
        const x = index * (candleWidth + candleSpacing) + candleWidth / 2
        const y = priceToY(candle.ma5, config)
        if (index === 0 || kline[index - 1].ma5 === null) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      }
    })
    ctx.stroke()

    // MA10
    ctx.beginPath()
    ctx.strokeStyle = colors.ma10
    kline.forEach((candle, index) => {
      if (candle.ma10 !== null && candle.ma10 !== undefined) {
        const x = index * (candleWidth + candleSpacing) + candleWidth / 2
        const y = priceToY(candle.ma10, config)
        if (index === 0 || kline[index - 1].ma10 === null) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      }
    })
    ctx.stroke()

    // MA20
    ctx.beginPath()
    ctx.strokeStyle = colors.ma20
    kline.forEach((candle, index) => {
      if (candle.ma20 !== null && candle.ma20 !== undefined) {
        const x = index * (candleWidth + candleSpacing) + candleWidth / 2
        const y = priceToY(candle.ma20, config)
        if (index === 0 || kline[index - 1].ma20 === null) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      }
    })
    ctx.stroke()

    // MA60
    ctx.beginPath()
    ctx.strokeStyle = colors.ma60
    kline.forEach((candle, index) => {
      if (candle.ma60 !== null && candle.ma60 !== undefined) {
        const x = index * (candleWidth + candleSpacing) + candleWidth / 2
        const y = priceToY(candle.ma60, config)
        if (index === 0 || kline[index - 1].ma60 === null) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      }
    })
    ctx.stroke()
  }, [priceToY])

  // 绘制网格
  const drawGrid = useCallback((
    ctx: CanvasRenderingContext2D,
    config: any
  ) => {
    const { width, height, margins, colors } = config
    const chartWidth = width - margins.left - margins.right
    const chartHeight = height - margins.top - margins.bottom

    ctx.strokeStyle = colors.grid
    ctx.lineWidth = 0.5

    // 横向网格线
    for (let i = 0; i <= 4; i++) {
      const y = margins.top + (chartHeight / 4) * i
      ctx.beginPath()
      ctx.moveTo(margins.left, y)
      ctx.lineTo(width - margins.right, y)
      ctx.stroke()
    }

    // 纵向网格线
    for (let i = 0; i <= 6; i++) {
      const x = margins.left + (chartWidth / 6) * i
      ctx.beginPath()
      ctx.moveTo(x, margins.top)
      ctx.lineTo(x, height - margins.bottom)
      ctx.stroke()
    }
  }, [])

  // 绘制坐标轴
  const drawAxes = useCallback((
    ctx: CanvasRenderingContext2D,
    kline: KLineData[],
    config: any
  ) => {
    const { width, height, margins, colors } = config
    const chartHeight = height - margins.top - margins.bottom

    ctx.fillStyle = colors.text
    ctx.font = '10px Arial'
    ctx.textAlign = 'left'

    // Y 轴标签（价格）
    for (let i = 0; i <= 4; i++) {
      const price = config.maxPrice - (config.priceRange / 4) * i
      const y = margins.top + (chartHeight / 4) * i
      ctx.fillText(price.toFixed(2), width - margins.right + 5, y + 4)
    }

    // X 轴标签（日期）
    ctx.textAlign = 'center'
    const step = Math.max(1, Math.floor(kline.length / 6))
    kline.forEach((candle, index) => {
      if (index % step === 0) {
        const x = margins.left + index * (config.candleWidth + config.candleSpacing) + config.candleWidth / 2
        const date = candle.date.substring(5) // 只显示月 - 日
        ctx.fillText(date, x, height - margins.bottom + 20)
      }
    })
  }, [])

  // 主渲染函数 - 只执行一次，使用视口裁剪优化
  const render = useCallback(() => {
    const canvas = canvasRef.current
    if (!canvas || !visibleData) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // 清空画布
    ctx.clearRect(0, 0, canvas.width, canvas.height)

    // 计算价格范围（仅基于可见数据）
    const prices = visibleData.flatMap(c => [c.open, c.high, c.low, c.close])
    const minPrice = Math.min(...prices) * 0.99
    const maxPrice = Math.max(...prices) * 1.01
    const priceRange = maxPrice - minPrice

    const config = {
      ...data!.config,
      minPrice,
      maxPrice,
      priceRange
    }

    // 绘制背景
    ctx.fillStyle = '#ffffff'
    ctx.fillRect(0, 0, canvas.width, canvas.height)

    // 绘制网格
    drawGrid(ctx, config)

    // 绘制 K 线（仅绘制可见区域）
    drawKLines(ctx, visibleData, config)

    // 绘制均线（仅绘制可见区域）
    if (visibleData[0]?.ma5 !== undefined) {
      drawMovingAverages(ctx, visibleData, config)
    }

    // 绘制坐标轴（基于可见数据）
    drawAxes(ctx, visibleData, config)
  }, [visibleData, data, drawKLines, drawMovingAverages, drawGrid, drawAxes])

  // 启动渲染 - 只在数据变化时渲染一次
  useEffect(() => {
    if (data) {
      render()
    }
  }, [data, render])

  // 响应式调整
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const resizeCanvas = () => {
      const dpr = window.devicePixelRatio || 1
      const rect = canvas.getBoundingClientRect()

      canvas.width = rect.width * dpr
      canvas.height = rect.height * dpr

      const ctx = canvas.getContext('2d')
      if (ctx) {
        ctx.scale(dpr, dpr)
      }
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    return () => {
      window.removeEventListener('resize', resizeCanvas)
    }
  }, [])

  // 鼠标拖拽平移
  const handleMouseDown = (e: React.MouseEvent) => {
    isDragging.current = true
    lastMouseX.current = e.clientX
  }

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging.current || !onPan) return

    const deltaX = e.clientX - lastMouseX.current
    onPan(deltaX)
    lastMouseX.current = e.clientX
  }

  const handleMouseUp = () => {
    isDragging.current = false
  }

  const handleWheel = (e: React.WheelEvent) => {
    if (!onZoom) return

    const scale = e.deltaY > 0 ? 0.9 : 1.1
    onZoom(scale)
  }

  return (
    <canvas
      ref={canvasRef}
      style={{ width: '100%', height: '100%', cursor: 'crosshair' }}
      onMouseDown={handleMouseDown}
      onMouseMove={handleMouseMove}
      onMouseUp={handleMouseUp}
      onMouseLeave={handleMouseUp}
      onWheel={handleWheel}
    />
  )
}
