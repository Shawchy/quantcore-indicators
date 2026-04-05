/**
 * 基金 API 服务
 * 
 * 提供基金基本信息、净值、持仓等接口
 * 优先从缓存和数据库获取数据，减少重复查询
 */
import api from './api'
import fundStorage from './fundStorage'

/** 基金基本信息 */
export interface FundInfo {
  code: string                    // 基金代码
  name: string                    // 基金简称
  establish_date?: string         // 成立日期
  change_pct?: number             // 涨跌幅（%）
  net_asset_value?: number        // 最新净值
  fund_company?: string           // 基金公司
  nav_update_date?: string        // 净值更新日期
  description?: string            // 简介
  type?: string                   // 基金类型
  fund_scale?: number             // 基金规模（亿元）
  rank?: number                   // 同类排行
  performance?: {                 // 阶段涨跌幅
    '1w'?: number                 // 近 1 周
    '1m'?: number                 // 近 1 月
    '3m'?: number                 // 近 3 月
    '6m'?: number                 // 近 6 月
    '1y'?: number                 // 近 1 年
  }
}

/** 基金代码信息 */
export interface FundCodeInfo {
  code: string                    // 基金代码
  name: string                    // 基金简称
}

/** 基金持仓信息 */
export interface FundPositionInfo {
  fund_code: string               // 基金代码
  stock_code: string              // 股票代码
  stock_name: string              // 股票简称
  position_ratio?: number         // 持仓占比（%）
  change?: number                 // 较上期变化（%）
  report_date?: string            // 公开日期
  ratio?: number                  // 占比（%）
}

/** 基金历史净值信息 */
export interface FundHistoryInfo {
  fund_code: string               // 基金代码
  date?: string                   // 日期
  unit_nav?: number               // 单位净值
  accumulated_nav?: number        // 累计净值
  change_pct?: number             // 涨跌幅（%）
}

/** 基金实时估算涨跌幅信息 */
export interface FundRealtimeRateInfo {
  code: string                    // 基金代码
  name: string                    // 基金名称
  net_value?: number              // 最新净值
  nav_date?: string               // 最新净值公开日期
  estimate_time?: string          // 估算时间
  estimate_change_pct?: number    // 估算涨跌幅（%）
}

/** 基金阶段涨跌幅信息 */
export interface FundPeriodChangeInfo {
  fund_code: string               // 基金代码
  period: string                  // 时间段（如：近一周、近一月、近三月等）
  return_rate?: number            // 收益率（%）
  avg_return?: number             // 同类平均（%）
  rank?: number                   // 同类排行
  total_count?: number            // 同类总数
  rank_rate?: number              // 排名百分比（rank/total_count，越低越好）
}

/** 基金资产配置比例信息 */
export interface FundAssetsAllocationInfo {
  fund_code: string               // 基金代码
  report_date?: string            // 公开日期
  stock_ratio?: number            // 股票比重（%）
  bond_ratio?: number             // 债券比重（%）
  cash_ratio?: number             // 现金比重（%）
  other_ratio?: number            // 其他比重（%）
  total_scale?: number            // 总规模（亿元）
  asset_name?: string             // 资产名称
  ratio?: number                  // 占比（%）
}

/** 基金列表查询参数 */
export interface FundListParams {
  fundType?: string      // 基金类型：all/stock/bond/money/index
  fundCompany?: string   // 基金公司名称（模糊匹配）
}

/** 基金类型枚举 */
export enum FundType {
  ALL = '',              // 全部
  BOND = 'zq',           // 债券型
  STOCK = 'gp',          // 股票型
  ETF = 'etf',           // ETF
  MIXED = 'hh',          // 混合型
  INDEX = 'zs',          // 指数型
  FOF = 'fof',           // FOF
  QDII = 'qdii',         // QDII
}

export const fundApi = {
  /**
   * 获取基金代码列表（天天基金网）
   * 
   * @param fundType 基金类型
   */
  getFundCodes: (fundType?: FundType | string) =>
    api.get<FundCodeInfo[]>('/fund/codes', {
      params: {
        fund_type: fundType || undefined,
      }
    }),
  
  /**
   * 获取基金持仓占比数据（前十大重仓股）
   * 
   * @param fundCode 基金代码
   * @param dates 日期或日期列表（逗号分隔）
   */
  getFundPosition: (fundCode: string, dates?: string) =>
    api.get<FundPositionInfo[]>(`/fund/${fundCode}/position`, {
      params: {
        dates: dates || undefined,
      }
    }),
  
  /**
   * 获取单只基金历史净值数据
   * 优先从缓存获取，缓存失效时从 API 获取
   * 
   * @param fundCode 基金代码
   * @param pz 页码，默认 40000 获取全部历史数据
   * @param forceRefresh 是否强制刷新缓存
   * 
   * @example
   * // 获取全部历史净值（优先缓存）
   * const history = await fundApi.getFundHistory('161725')
   * 
   * @example
   * // 强制刷新缓存
   * const history = await fundApi.getFundHistory('161725', 40000, true)
   */
  getFundHistory: async (fundCode: string, pz: number = 40000, forceRefresh: boolean = false) => {
    // 优先从缓存获取
    if (!forceRefresh) {
      const cached = await fundStorage.getHistory(fundCode)
      if (cached) {
        console.log(`[缓存] 获取基金 ${fundCode} 历史净值`)
        return { data: cached }
      }
    }
    
    // 从 API 获取
    console.log(`[API] 获取基金 ${fundCode} 历史净值`)
    const response = await api.get<FundHistoryInfo[]>(`/fund/${fundCode}/history`, { params: { pz } })
    
    // 保存到缓存
    if (response.data && response.data.length > 0) {
      await fundStorage.setHistory(fundCode, response.data)
    }
    
    return response
  },
  
  /**
   * 批量获取多只基金历史净值数据
   * 优先从缓存获取，缓存失效时从 API 获取
   * 
   * @param fundCodes 基金代码列表
   * @param pz 页码，默认 40000 获取全部历史数据
   * @param forceRefresh 是否强制刷新缓存
   * 
   * @example
   * // 批量获取多只基金历史净值（优先缓存）
   * const historyDict = await fundApi.getFundHistoryMulti(['161725', '005918'])
   */
  getFundHistoryMulti: async (fundCodes: string[], pz: number = 40000, forceRefresh: boolean = false) => {
    // 检查缓存
    const cachedData: Record<string, FundHistoryInfo[]> = {}
    const missingCodes: string[] = []
    
    if (!forceRefresh) {
      for (const code of fundCodes) {
        const cached = await fundStorage.getHistory(code)
        if (cached) {
          cachedData[code] = cached
        } else {
          missingCodes.push(code)
        }
      }
      
      // 如果全部命中缓存
      if (missingCodes.length === 0) {
        console.log(`[缓存] 批量获取 ${fundCodes.length} 只基金历史净值`)
        return { data: cachedData }
      }
    } else {
      missingCodes.push(...fundCodes)
    }
    
    // 从 API 获取缺失的数据
    if (missingCodes.length > 0) {
      console.log(`[API] 批量获取 ${missingCodes.length} 只基金历史净值`)
      const response = await api.post<Record<string, FundHistoryInfo[]>>('/fund/history/batch', missingCodes, {
        params: { pz }
      })
      
      // 保存到缓存
      if (response.data) {
        const savePromises = Object.entries(response.data).map(([code, data]) =>
          fundStorage.setHistory(code, data)
        )
        await Promise.all(savePromises)
      }
      
      // 合并缓存和 API 数据
      return {
        data: {
          ...cachedData,
          ...response.data,
        }
      }
    }
    
    return { data: cachedData }
  },
  
  /**
   * 获取基金基本信息
   * 优先从缓存获取
   * 
   * @param fundCodes 基金代码（单只或多只）
   */
  getFundBaseInfo: async (fundCodes: string | string[]) => {
    const codeList = Array.isArray(fundCodes) ? fundCodes : [fundCodes]
    
    // 检查缓存
    const cachedData: FundInfo[] = []
    const missingCodes: string[] = []
    
    for (const code of codeList) {
      const cached = await fundStorage.getBaseInfo(code)
      if (cached) {
        cachedData.push(cached)
      } else {
        missingCodes.push(code)
      }
    }
    
    // 如果全部命中缓存
    if (missingCodes.length === 0) {
      console.log(`[缓存] 获取 ${codeList.length} 只基金基本信息`)
      return {
        data: Array.isArray(fundCodes) ? cachedData : cachedData[0],
      }
    }
    
    // 从 API 获取缺失的数据
    const codeParam = missingCodes.join(',')
    console.log(`[API] 获取 ${missingCodes.length} 只基金基本信息`)
    const response = await api.get<FundInfo | FundInfo[]>(`/fund/base-info/${codeParam}`)
    
    // 保存到缓存
    if (response.data) {
      const dataList = Array.isArray(response.data) ? response.data : [response.data]
      const savePromises = dataList.map(info => fundStorage.setBaseInfo(info.code, info))
      await Promise.all(savePromises)
    }
    
    // 合并缓存和 API 数据
    const allData = Array.isArray(response.data) 
      ? [...cachedData, ...response.data]
      : [...cachedData, response.data]
    
    return {
      data: Array.isArray(fundCodes) ? allData : allData[0],
    }
  },
  
  /**
   * 获取基金实时估算涨跌幅度
   * 优先从缓存获取（60 秒有效期）
   * 
   * @param fundCodes 基金代码（单只或多只）
   */
  getFundRealtimeRate: async (fundCodes: string | string[]) => {
    const codeList = Array.isArray(fundCodes) ? fundCodes : [fundCodes]
    
    // 检查缓存
    const cachedData: FundRealtimeRateInfo[] = []
    const missingCodes: string[] = []
    
    for (const code of codeList) {
      const cached = await fundStorage.getRealtimeRate(code)
      if (cached) {
        cachedData.push(cached)
      } else {
        missingCodes.push(code)
      }
    }
    
    // 如果全部命中缓存
    if (missingCodes.length === 0) {
      console.log(`[缓存] 获取 ${codeList.length} 只基金实时估算`)
      return {
        data: Array.isArray(fundCodes) ? cachedData : cachedData[0],
      }
    }
    
    // 从 API 获取缺失的数据
    const codeParam = missingCodes.join(',')
    console.log(`[API] 获取 ${missingCodes.length} 只基金实时估算`)
    const response = await api.get<FundRealtimeRateInfo | FundRealtimeRateInfo[]>(`/fund/realtime-rate/${codeParam}`)
    
    // 保存到缓存
    if (response.data) {
      const dataList = Array.isArray(response.data) ? response.data : [response.data]
      const codes = dataList.map(d => d.code)
      await fundStorage.setRealtimeRate(codes, dataList)
    }
    
    // 合并缓存和 API 数据
    const allData = Array.isArray(response.data)
      ? [...cachedData, ...response.data]
      : [...cachedData, response.data]
    
    return {
      data: Array.isArray(fundCodes) ? allData : allData[0],
    }
  },
  
  /**
   * 获取基金阶段涨跌幅度
   * 优先从缓存获取（7 天有效期）
   * 
   * @param fundCode 基金代码
   */
  getFundPeriodChange: async (fundCode: string) => {
    // 优先从缓存获取
    const cached = await fundStorage.getPeriodChange(fundCode)
    if (cached) {
      console.log(`[缓存] 获取基金 ${fundCode} 阶段涨跌幅`)
      return { data: cached }
    }
    
    // 从 API 获取
    console.log(`[API] 获取基金 ${fundCode} 阶段涨跌幅`)
    const response = await api.get<FundPeriodChangeInfo[]>(`/fund/${fundCode}/period-change`)
    
    // 保存到缓存
    if (response.data && response.data.length > 0) {
      await fundStorage.setPeriodChange(fundCode, response.data)
    }
    
    return response
  },
  
  /**
   * 获取全部有效基金代码列表
   * 从后端获取并验证所有基金代码
   */
  getAllFundCodes: async (): Promise<string[]> => {
    try {
      const response = await api.get<FundCodeInfo[]>('/fund/list', {
        params: { fund_type: 'all' }
      });
      
      if (!response.data || !Array.isArray(response.data)) {
        console.warn('[fundApi] 获取基金代码列表返回空数据');
        return [];
      }
      
      // 提取并验证所有基金代码
      const validCodes = response.data
        .map(item => item.code)
        .filter(code => {
          // 必须是字符串
          if (typeof code !== 'string') return false;
          // 不能包含 'nan'（不区分大小写）
          if (code.toLowerCase().includes('nan')) return false;
          // 必须是 6 位数字
          if (!/^\d{6}$/.test(code)) return false;
          return true;
        });
      
      console.log(`[fundApi] 获取到 ${validCodes.length} 只有效基金（共 ${response.data.length} 只）`);
      return validCodes;
    } catch (error) {
      console.error('[fundApi] 获取基金代码列表失败:', error);
      return [];
    }
  },
  
  /**
   * 获取基金列表（待实现）
   * 
   * @param params 查询参数
   */
  getFundList: (params?: FundListParams) =>
    api.get<FundInfo[]>('/fund/list', {
      params: {
        fund_type: params?.fundType || 'all',
        fund_company: params?.fundCompany,
      }
    }),
  
  /**
   * 获取基金资产配置比例
   * 优先从缓存获取（7 天有效期）
   * 
   * @param fundCode 基金代码
   * @param dates 日期或日期列表（逗号分隔，可选）
   */
  getFundAssetsAllocation: async (fundCode: string, dates?: string) => {
    // 优先从缓存获取（无 dates 参数时使用缓存）
    if (!dates) {
      const cached = await fundStorage.getAssets(fundCode)
      if (cached) {
        console.log(`[缓存] 获取基金 ${fundCode} 资产配置`)
        return { data: cached }
      }
    }
    
    // 从 API 获取
    console.log(`[API] 获取基金 ${fundCode} 资产配置`)
    const response = await api.get<FundAssetsAllocationInfo[]>(`/fund/${fundCode}/assets`, {
      params: { dates: dates || undefined }
    })
    
    // 保存到缓存（只有获取最新数据时才保存）
    if (!dates && response.data && response.data.length > 0) {
      await fundStorage.setAssets(fundCode, response.data)
    }
    
    return response
  },
}

export default fundApi
