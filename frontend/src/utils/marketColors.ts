/**
 * 市场颜色配置
 * 根据全球不同股票市场的涨跌颜色规则进行配置
 */

export type MarketType = 'A' | 'HK' | 'US' | 'TW' | 'JP'

export interface MarketColorConfig {
  rise: string      // 上涨颜色
  fall: string      // 下跌颜色
  neutral: string   // 持平颜色
}

/**
 * 不同市场的颜色规则
 * - A 股（沪深）：上涨红色，下跌绿色，持平白色/灰色
 * - 港股：上涨绿色，下跌红色，持平白色
 * - 美股/欧美：上涨绿色，下跌红色，持平白色
 * - 中国台湾：上涨红色，下跌绿色，持平白色
 * - 日本：上涨红色，下跌绿色，持平白色
 */
export const MARKET_COLORS: Record<MarketType, MarketColorConfig> = {
  A: {    // A 股（沪深）
    rise: 'red.500',
    fall: 'green.500',
    neutral: 'gray.500',
  },
  HK: {   // 港股
    rise: 'green.500',
    fall: 'red.500',
    neutral: 'gray.500',
  },
  US: {   // 美股/欧美
    rise: 'green.500',
    fall: 'red.500',
    neutral: 'gray.500',
  },
  TW: {   // 中国台湾
    rise: 'red.500',
    fall: 'green.500',
    neutral: 'gray.500',
  },
  JP: {   // 日本
    rise: 'red.500',
    fall: 'green.500',
    neutral: 'gray.500',
  },
}

/**
 * 根据市场类型和涨跌值获取颜色
 * @param change 涨跌值（正数为上涨，负数为下跌，0 为持平）
 * @param marketType 市场类型，默认为 A 股
 * @returns 颜色值
 */
export function getMarketColor(
  change: number | null | undefined, 
  marketType: MarketType = 'A'
): string {
  if (change === null || change === undefined) {
    return MARKET_COLORS[marketType].neutral
  }
  
  const config = MARKET_COLORS[marketType]
  
  if (change > 0) {
    return config.rise
  } else if (change < 0) {
    return config.fall
  } else {
    return config.neutral
  }
}

/**
 * 获取 A 股颜色（简化版本，默认使用 A 股规则）
 * @param change 涨跌值
 * @returns 颜色值
 */
export function getAStockColor(change: number | null | undefined): string {
  return getMarketColor(change, 'A')
}

/**
 * 根据市场类型获取涨跌文本前缀
 * @param change 涨跌值
 * @param marketType 市场类型
 * @returns 带正负号的文本
 */
export function getChangeText(change: number | null | undefined, marketType: MarketType = 'A'): string {
  if (change === null || change === undefined) {
    return '-'
  }
  
  // A 股、台股、日股：上涨显示 +，下跌显示 -
  // 港股、美股：上涨显示 +，下跌显示 -（国际通用）
  if (change > 0) {
    return `+${change.toFixed(2)}`
  } else if (change < 0) {
    return `${change.toFixed(2)}`
  } else {
    return '0.00'
  }
}
