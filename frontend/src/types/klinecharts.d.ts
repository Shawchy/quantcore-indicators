/**
 * klinecharts 库的类型声明
 * 用于补充官方类型定义的不足
 */

declare module 'klinecharts' {
  // 图表实例类型
  export interface ChartInstance {
    // 设置标的信息
    setSymbol(symbol: {
      ticker: string
      name: string
    }): void

    // 设置周期
    setPeriod(period: {
      span: number
      type: 'day' | 'week' | 'month' | 'minute'
    }): void

    // 设置数据加载器
    setDataLoader(loader: {
      getBars: (options: { callback: (data: any[]) => void }) => void
    }): void

    // 应用新数据
    applyNewData(data: any[]): void

    // 添加更多数据
    addData(data: any[]): void

    // 更新最后一条数据
    updateData(data: any): void

    // 获取图表配置
    getOptions(): any

    // 设置图表配置
    setOptions(options: any): void

    // 销毁图表
    dispose(): void

    // 获取图表宽度
    getWidth(): number

    // 获取图表高度
    getHeight(): number

    // 滚动到指定位置
    scrollTo(position: number): void

    // 缩放
    zoom(scale: number): void

    // 重置
    reset(): void
  }

  // 初始化选项
  export interface InitOptions {
    layout?: Array<{
      type: 'candle' | 'indicator' | 'xAxis' | 'yAxis'
      content?: string[]
      options?: {
        order?: number
        [key: string]: any
      }
    }>
    [key: string]: any
  }

  // K 线数据项
  export interface KLineDataItem {
    timestamp: number
    open: number
    high: number
    low: number
    close: number
    volume: number
    turnover?: number
    [key: string]: any
  }

  // 初始化图表
  export function init(container: HTMLElement, options?: InitOptions): ChartInstance
  export function init(container: string, options?: InitOptions): ChartInstance

  // 获取图表实例
  export function getInstance(id: string): ChartInstance | null

  // 销毁图表
  export function dispose(id: string): void

  // 获取所有图表实例
  export function getAllInstances(): ChartInstance[]

  // 设置全局配置
  export function setGlobalOptions(options: any): void

  // 获取全局配置
  export function getGlobalOptions(): any

  // 注册指标
  export function registerIndicator(indicator: any): void

  // 注册样式
  export function registerStyle(style: any): void
}
