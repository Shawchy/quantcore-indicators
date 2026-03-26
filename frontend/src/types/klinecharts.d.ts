/**
 * KLineChart 库的类型声明
 */

declare module 'klinecharts' {
  export interface KLineData {
    timestamp: number
    open: number
    high: number
    low: number
    close: number
    volume: number
    turnover?: number
    [key: string]: any
  }

  export interface ChartOptions {
    theme?: {
      backgroundColor?: string
      textColor?: string
      gridColor?: string
      crossHairColor?: string
    }
    candle?: {
      bar?: {
        upColor?: string
        downColor?: string
        noChangeColor?: string
      }
      area?: {
        upColor?: string
        downColor?: string
      }
    }
    ma?: {
      lines?: Array<{
        period: number
        color: string
      }>
    }
    volume?: {
      show?: boolean
      upColor?: string
      downColor?: string
    }
    technicalIndicators?: {
      show?: boolean
      indicators?: string[]
    }
    xAxis?: {
      type?: string
      axisLabel?: {
        formatter?: (value: any) => string
      }
    }
    yAxis?: {
      scale?: boolean
      axisLabel?: {
        formatter?: (value: number) => string
      }
    }
    tooltip?: {
      show?: boolean
      formatter?: (data: any) => string
    }
    zoom?: {
      enabled?: boolean
      minScale?: number
      maxScale?: number
    }
    crosshair?: {
      show?: boolean
      mode?: string
    }
  }

  export interface ChartInstance {
    applyNewData(data: KLineData[]): void
    setOptions(options: ChartOptions): void
    dispose(): void
  }

  export function init(domId: string): ChartInstance
  export function dispose(domId: string): void
}
