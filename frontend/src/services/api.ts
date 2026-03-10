import axios from 'axios'
import type { RootState, AppDispatch } from '../store'

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api/v1'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Token 刷新锁
let isRefreshing = false
let failedQueue: Array<{ resolve: (value?: any) => void; reject: (reason?: any) => void }> = []

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

// 获取 store 的函数（延迟导入避免循环依赖）
const getStore = (): { getState: () => RootState; dispatch: AppDispatch } => {
  // 使用动态导入避免循环依赖
  const storeModule = window.__store__ as { getState: () => RootState; dispatch: AppDispatch }
  if (!storeModule) {
    throw new Error('Store not initialized')
  }
  return storeModule
}

// 请求拦截器 - 自动携带 Token
api.interceptors.request.use(
  (config) => {
    try {
      const store = getStore()
      const state = store.getState()
      const token = state.auth.token
      
      if (token) {
        config.headers.Authorization = `Bearer ${token}`
      }
    } catch (error) {
      // Store 未初始化时不阻塞请求
      console.warn('Failed to get auth token:', error)
    }
    
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 - 处理 401 错误和 Token 刷新
api.interceptors.response.use(
  (response) => response.data,
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
        const store = getStore()
        const state = store.getState()
        const refreshToken = state.auth.refreshToken
        
        if (refreshToken) {
          try {
            const response = await axios.post('/api/v1/auth/refresh', {
              refresh_token: refreshToken
            })
            
            const newToken = response.data.access_token
            store.dispatch({
              type: 'auth/setToken',
              payload: {
                access_token: newToken,
                refresh_token: response.data.refresh_token
              }
            })
            
            processQueue(null, newToken)
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return api(originalRequest)
          } catch (refreshError) {
            processQueue(refreshError, null)
            // 刷新失败，跳转到登录页
            store.dispatch({ type: 'auth/localLogout' })
            window.location.href = '/login'
            return Promise.reject(refreshError)
          }
        }
      } catch (storeError) {
        // Store 访问失败
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
  login: (username: string, password: string) =>
    api.post('/auth/login', { username, password }),
  
  logout: () => api.post('/auth/logout'),
  
  refreshToken: (refreshToken: string) =>
    api.post('/auth/refresh', { refresh_token: refreshToken }),
  
  getCurrentUser: () => api.get('/auth/me'),
}

export const stockApi = {
  getBasic: (code: string) => api.get(`/stock/basic/${code}`),
  getKline: (
    code: string,
    params?: {
      startDate?: string
      endDate?: string
      adjust?: string
      priorityLoad?: boolean
    }
  ) =>
    api.get(`/stock/kline/${code}`, {
      params: {
        start_date: params?.startDate,
        end_date: params?.endDate,
        adjust: params?.adjust || 'qfq',
        priority_load: params?.priorityLoad ?? true
      }
    }),
  getIndicators: (code: string, startDate?: string, endDate?: string) =>
    api.get(`/stock/indicators/${code}`, { params: { start_date: startDate, end_date: endDate } }),
  getRealtime: (code: string) => api.get(`/stock/realtime/${code}`),
  search: (keyword: string, limit: number = 20) =>
    api.get('/stock/search', { params: { keyword, limit } }),
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
  getRanking: (sectorType: string = 'industry', sortBy: string = 'change_pct', limit: number = 20) =>
    api.get('/sector/ranking', { params: { sector_type: sectorType, sort_by: sortBy, limit } }),
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
  query: (conditions: any) => api.post('/screener/query', conditions),
  getMarketStats: () => api.get('/screener/market-stats'),
  getSectorStats: (sectorCode: string) => api.get(`/screener/sector-stats/${sectorCode}`),
  getPresetConditions: () => api.get('/screener/preset-conditions'),
}

export const strategyApi = {
  getList: () => api.get('/strategy/list'),
  get: (strategyId: string) => api.get(`/strategy/${strategyId}`),
  create: (config: any) => api.post('/strategy/create', config),
  update: (strategyId: string, config: any) => api.put(`/strategy/${strategyId}`, config),
  delete: (strategyId: string) => api.delete(`/strategy/${strategyId}`),
  optimize: (strategyId: string, paramRanges: any, method: string = 'bayesian') =>
    api.post(`/strategy/${strategyId}/optimize`, paramRanges, { params: { method } }),
}

export const backtestApi = {
  run: (config: any) => api.post('/backtest/run', config),
  getResult: (backtestId: string) => api.get(`/backtest/result/${backtestId}`),
  getPerformance: (backtestId: string) => api.get(`/backtest/performance/${backtestId}`),
  getTrades: (backtestId: string, page: number = 1, pageSize: number = 50) =>
    api.get(`/backtest/trades/${backtestId}`, { params: { page, page_size: pageSize } }),
  getHistory: (limit: number = 20) => api.get('/backtest/history', { params: { limit } }),
}

export default api
