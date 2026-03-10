import axios from 'axios'

const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.message || error.message || '请求失败'
    return Promise.reject(new Error(message))
  }
)

export const stockApi = {
  getBasic: (code: string) => api.get(`/stock/basic/${code}`),
  getKline: (code: string, startDate?: string, endDate?: string, adjust: string = 'qfq') =>
    api.get(`/stock/kline/${code}`, { params: { start_date: startDate, end_date: endDate, adjust } }),
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
