/**
 * 系统常量配置文件
 */

// 股票市场代码
export const MARKET_CODES = {
  SHANGHAI: 'SH',
  SHENZHEN: 'SZ',
} as const

// 指数代码配置
export const INDEX_CODES = {
  SHANGHAI: '000001',      // 上证指数
  SHENZHEN: '399001',      // 深证成指
  GEM: '399006',           // 创业板指
  CHI_NEXT: '399006',      // 创业板指别名
} as const

// 板块类型
export const SECTOR_TYPES = {
  INDUSTRY: 'industry',    // 行业板块
  CONCEPT: 'concept',      // 概念板块
} as const

// 搜索限制
export const SEARCH_LIMITS = {
  DEFAULT: 20,
  MAX: 1000,
} as const

// K 线数据配置
export const KLINE_CONFIG = {
  DEFAULT_ADJUST: 'qfq',   // 默认前复权
  DEFAULT_DAYS: 30,        // 默认获取 30 天数据
} as const

// 缓存配置
export const CACHE_CONFIG = {
  SHORT: 5 * 60 * 1000,    // 5 分钟
  MEDIUM: 30 * 60 * 1000,  // 30 分钟
  LONG: 60 * 60 * 1000,    // 1 小时
} as const

// 颜色配置
export const COLORS = {
  UP: '#ef4444',           // 上涨 - 红色
  DOWN: '#22c55e',         // 下跌 - 绿色
  FLAT: '#64748b',         // 平盘 - 灰色
  PRIMARY: '#3b82f6',      // 主色 - 蓝色
} as const

// API 超时配置
export const API_TIMEOUT = {
  SHORT: 10000,            // 10 秒
  DEFAULT: 30000,          // 30 秒
  LONG: 60000,             // 60 秒
} as const

// 分页配置
export const PAGINATION = {
  DEFAULT_PAGE_SIZE: 20,
  MAX_PAGE_SIZE: 100,
} as const

// 股票代码正则
export const STOCK_CODE_REGEX = /^[0-9]{6}$/

// 日期格式
export const DATE_FORMATS = {
  YYYYMMDD: 'YYYYMMDD',
  YYYY_MM_DD: 'YYYY-MM-DD',
  ISO: 'ISO',
} as const
