import axios from 'axios'
import { useAuthStore } from '../store/authStore'
import type { ScreenerCondition, StrategyCreateRequest, StrategyUpdateRequest, StrategyOptimizeRequest, BacktestRunRequest } from '../types'

const API_BASE_URL = import.meta.env?.VITE_API_BASE_URL ?? '/api/v1'

/** 登录/刷新接口返回的 Token 结构（与后端 Token 模型一致） */
export interface AuthToken {
  access_token: string
  refresh_token: string
  token_type?: string
}

/** 当前用户信息（与后端 User 模型一致） */
export interface ApiUser {
  user_id: number
  username: string
  email?: string
  role: string
  is_active?: boolean
}

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 30 秒超时
  headers: {
    'Content-Type': 'application/json',
  },
  // 优化重试配置
  timeoutErrorMessage: '请求超时，请检查网络连接或稍后重试',
})

// Token 刷新锁
let isRefreshing = false
// eslint-disable-next-line @typescript-eslint/no-explicit-any
let failedQueue: Array<{ resolve: (value?: any) => void; reject: (reason?: any) => void }> = []

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const processQueue = (error: any, token: string | null = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

// 请求拦截器 - 自动携带 Token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理 401 错误和 Token 刷新
api.interceptors.response.use(
  (response) => {
    // 后端返回格式：{ success: true, code: 'SUCCESS', message: '...', data: {...} }
    // 直接返回 data 字段，方便组件使用
    return response.data?.data ?? response.data
  },
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then(token => {
            originalRequest.headers.Authorization = `Bearer ${token}`
            return api(originalRequest)
          })
          .catch(err => Promise.reject(err))
      }
      
      originalRequest._retry = true
      isRefreshing = true
      
      try {
        const refreshToken = useAuthStore.getState().refreshToken
        
        if (refreshToken) {
          try {
            const baseURL = import.meta.env?.VITE_API_BASE_URL ?? '/api/v1'
            const response = await axios.post<AuthToken>(
              `${baseURL}/auth/refresh`,
              { refresh_token: refreshToken }
            )
            const data = response.data
            const newToken = data.access_token
            useAuthStore.setState({
              token: newToken,
              refreshToken: data.refresh_token,
            })
            
            processQueue(null, newToken)
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return api(originalRequest)
          } catch (refreshError) {
            processQueue(refreshError, null)
            console.error('Token 刷新失败:', refreshError)
            useAuthStore.setState({
              token: null,
              refreshToken: null,
              user: null,
              isAuthenticated: false,
            })
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        }
      } catch (storeError) {
        // Store 访问失败
        // eslint-disable-next-line no-console
        console.error('Failed to access store:', storeError)
        processQueue(storeError, null)
      } finally {
        isRefreshing = false
      }
    }
    
    const message = error.response?.data?.message || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export const authApi = {
  login: (username: string, password: string): Promise<AuthToken> =>
    api.post('/auth/login', { username, password }),
  
  logout: () => api.post('/auth/logout'),
  
  refreshToken: (refreshToken: string): Promise<AuthToken> =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  
  getCurrentUser: (): Promise<ApiUser> => api.get('/auth/me'),
}

export const stockApi = {
  getBasic: (code: string) => api.get(`/stock/${code}`),
  getKline: (
    code: string,
    params?: {
      startDate?: string
      endDate?: string
      adjust?: string
      priorityLoad?: boolean
    }
  ) =>
    api.get(`/stock/${code}/kline`, {
      params: {
        start_date: params?.startDate,
        end_date: params?.endDate,
        adjust: params?.adjust || 'qfq',
        priority_load: params?.priorityLoad ?? true,
      },
      timeout: 120000, // K 线数据加载需要更长时间（2 分钟）
    }),
  getWeeklyKline: (
    code: string,
    params?: {
      startDate?: string
      endDate?: string
      adjust?: string
    }
  ) =>
    api.get(`/stock/${code}/kline/weekly`, {
      params: {
        start_date: params?.startDate,
        end_date: params?.endDate,
        adjust: params?.adjust || 'qfq'
      },
      timeout: 120000, // 周线数据加载（2 分钟）
    }),
  getMonthlyKline: (
    code: string,
    params?: {
      startDate?: string
      endDate?: string
      adjust?: string
    }
  ) =>
    api.get(`/stock/${code}/kline/monthly`, {
      params: {
        start_date: params?.startDate,
        end_date: params?.endDate,
        adjust: params?.adjust || 'qfq'
      },
      timeout: 120000, // 月线数据加载（2 分钟）
    }),
  getIndicators: (code: string, startDate?: string, endDate?: string) =>
    api.get(`/stock/${code}/indicators`, { params: { start_date: startDate, end_date: endDate } }),
  getRealtime: (code: string) => api.get(`/stock/${code}/realtime`),
  search: (keyword: string, limit: number = 20) =>
    api.get('/stock/search', { params: { keyword, limit } }),
}

// 大盘指数 API
export const marketIndexApi = {
  getKline: (indexCode: string = '000001', startDate?: string, endDate?: string) =>
    api.get('/stock/market/index', { params: { index_code: indexCode, start_date: startDate, end_date: endDate } }),
  getRealtime: (indexCodes: string = '000001,399001,399006') =>
    api.get('/stock/market/realtime', { params: { index_codes: indexCodes } }),
}

export const watchlistApi = {
  getList: () => api.get('/watchlist/list'),
  add: (code: string, note?: string) => api.post('/watchlist/add', { code, note }),
  remove: (code: string) => api.delete(`/watchlist/remove/${code}`),
  update: (code: string, note: string) => api.put(`/watchlist/update/${code}`, { note }),
  getQuotes: () => api.get('/watchlist/quotes'),
}

export const sectorApi = {
  getList: (sectorType: string = 'industry') => api.get('/sector/list', { params: { sector_type: sectorType } }),
  getRanking: (sectorType: string = 'industry', sortBy: string = 'change_pct', limit: number = 20, tradeDate?: string) =>
    api.get('/sector/ranking', { params: { sector_type: sectorType, sort_by: sortBy, limit, ...(tradeDate && { trade_date: tradeDate }) } }),
  getComponents: (sectorCode: string) => api.get(`/sector/components/${sectorCode}`),
  getLeaders: (sectorCode: string, topN: number = 5) =>
    api.get(`/sector/leaders/${sectorCode}`, { params: { top_n: topN } }),
}

export const chipApi = {
  getData: (code: string, startDate?: string, endDate?: string) =>
    api.get(`/chip/data/${code}`, { params: { start_date: startDate, end_date: endDate } }),
  getControlDegree: (code: string, startDate?: string, endDate?: string) =>
    api.get(`/chip/control-degree/${code}`, { params: { start_date: startDate, end_date: endDate } }),
  screen: (minControl: number = 0.5, maxControl: number = 1.0, limit: number = 50) =>
    api.get('/chip/screen', { params: { min_control_degree: minControl, max_control_degree: maxControl, limit } }),
  getRanking: (sortOrder: string = 'desc', limit: number = 50) =>
    api.get('/chip/ranking', { params: { sort_order: sortOrder, limit } }),
}

export const screenerApi = {
  query: (conditions: ScreenerCondition) => api.post('/screener/query', conditions),
  getMarketStats: (tradeDate?: string) => api.get('/screener/market-stats', { params: { trade_date: tradeDate } }),
  getSectorStats: (sectorCode: string) => api.get(`/screener/sector-stats/${sectorCode}`),
  getPresetConditions: () => api.get('/screener/preset-conditions'),
  getEffectiveDate: () => api.get('/screener/effective-date'),
  getTradingDays: (limit: number = 20) => api.get('/screener/trading-days', { params: { limit } }),
}

export const strategyApi = {
  getList: () => api.get('/strategy/list'),
  get: (strategyId: string) => api.get(`/strategy/${strategyId}`),
  create: (config: StrategyCreateRequest) => api.post('/strategy/create', config),
  update: (strategyId: string, config: StrategyUpdateRequest) => api.put(`/strategy/${strategyId}`, config),
  delete: (strategyId: string) => api.delete(`/strategy/${strategyId}`),
  optimize: (strategyId: string, paramRanges: StrategyOptimizeRequest, method: string = 'bayesian') =>
    api.post(`/strategy/${strategyId}/optimize`, paramRanges, { params: { method } }),
}

export const backtestApi = {
  run: (config: BacktestRunRequest) => api.post('/backtest/run', config),
  getResult: (backtestId: string) => api.get(`/backtest/result/${backtestId}`),
  getPerformance: (backtestId: string) => api.get(`/backtest/performance/${backtestId}`),
  getTrades: (backtestId: string, page: number = 1, pageSize: number = 50) =>
    api.get(`/backtest/trades/${backtestId}`, { params: { page, page_size: pageSize } }),
  getHistory: (limit: number = 20) => api.get('/backtest/history', { params: { limit } }),
}

// 市场行情 API - 实时涨跌幅排名
export const marketApi = {
  getRanking: (topN: number = 50, src: string = 'sina') =>
    api.get('/market/market-ranking', { params: { top_n: topN, src } }),
  getOverview: () => api.get('/market/market-overview'),
  getSectorPerformance: (sectorType: string = 'industry') =>
    api.get('/market/sector-performance', { params: { sector_type: sectorType } }),
  getHistory: (rankingType: string, startDate?: string, endDate?: string, limit: number = 100) =>
    api.get('/market/market-ranking/history', { params: { ranking_type: rankingType, start_date: startDate, end_date: endDate, limit } }),
}

// 实时盘口 API
export const realtimeApi = {
  getQuote: (code: string, src: string = 'sina') =>
    api.get(`/realtime/quote/${code}`, { params: { src } }),
  getTickData: (code: string, src: string = 'dc', limit: number = 100) =>
    api.get(`/realtime/tick/${code}`, { params: { src, limit } }),
}

// 资金流向 API
export const moneyflowApi = {
  getMarketMoneyflow: (params?: {
    trade_date?: string
    start_date?: string
    end_date?: string
    days?: number
  }) =>
    api.get('/moneyflow/market', { params }),
  getMarketMoneyflowSummary: () =>
    api.get('/moneyflow/market/summary'),
  getMarketMoneyflowTrend: (days: number = 10) =>
    api.get('/moneyflow/market/trend', { params: { days } }),
}

// 数据源控制 API
export const dataSourceApi = {
  getStatus: () =>
    api.get('/data-source/status'),
  setMode: (mode: 'online' | 'offline') =>
    api.post('/data-source/mode', null, { params: { mode } }),
  toggleSource: (source: string, enabled: boolean) =>
    api.post('/data-source/toggle', null, { params: { source, enabled } }),
  reset: () =>
    api.post('/data-source/reset'),
}

// 数据加载进度 API
export const loadingProgressApi = {
  getTasks: (status?: string, dataType?: string) =>
    api.get('/loading/tasks', { params: { status, data_type: dataType } }),
  getTask: (taskId: string) =>
    api.get(`/loading/task/${taskId}`),
  removeTask: (taskId: string) =>
    api.delete(`/loading/task/${taskId}`),
  cleanupTasks: (maxAgeHours: number = 24) =>
    api.post('/loading/cleanup', null, { params: { max_age_hours: maxAgeHours } }),
}

// 龙虎榜 API
export const billboardApi = {
  getDaily: (tradeDate?: string) =>
    api.get('/billboard/billboard', { params: { trade_date: tradeDate } }),
  getStockHistory: (code: string, startDate?: string, endDate?: string) =>
    api.get(`/billboard/billboard/${code}`, { params: { start_date: startDate, end_date: endDate } }),
}

// 资金流向 API
export const capitalFlowApi = {
  getToday: (tradeDate?: string) =>
    api.get('/capital-flow/capital-flow/today', { params: { trade_date: tradeDate } }),
  getStockHistory: (code: string, startDate?: string, endDate?: string) =>
    api.get(`/capital-flow/capital-flow/${code}`, { params: { start_date: startDate, end_date: endDate } }),
}

// 板块信息 API
export const boardApi = {
  getStockBoards: (code: string) =>
    api.get(`/board/stock/${code}/boards`),
}

// 指数成分 API
export const indexApi = {
  getComponents: (code: string) =>
    api.get(`/index/index/${code}/components`),
}

// 股东信息 API
export const shareholderApi = {
  getTop10: (code: string) =>
    api.get(`/shareholder/stock/${code}/shareholders`),
}

// 市场实时行情 API（已禁用）
// export const marketQuotesApi = {
//   getMarketQuotes: (marketTypes?: string) =>
//     api.get('/market-quotes/market-quotes', { params: { market_types: marketTypes } }),
//   getSpecificMarketQuotes: (marketType: string, limit?: number) =>
//     api.get(`/market-quotes/market-quotes/${marketType}`, { params: { limit } }),
// }

export default api
