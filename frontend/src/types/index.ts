export interface StockBasic {
  code: string
  name: string
  market: string
  industry?: string
  sector?: string
  area?: string
  list_date?: string
  total_shares?: number
  float_shares?: number
}

export interface KLineData {
  code: string
  date: string
  open: number
  high: number
  low: number
  close: number
  volume: number
  amount?: number
  turnover_rate?: number
}

export interface TechnicalIndicator {
  code: string
  date: string
  ma5?: number
  ma10?: number
  ma20?: number
  ma60?: number
  rsi6?: number
  rsi12?: number
  rsi24?: number
  macd?: number
  macd_signal?: number
  macd_hist?: number
  boll_upper?: number
  boll_mid?: number
  boll_lower?: number
  k?: number
  d?: number
  j?: number
  atr?: number
}

export interface RealtimeQuote {
  code: string
  name: string
  price: number
  change: number
  change_pct: number
  volume: number
  amount?: number
  high: number
  low: number
  open: number
  prev_close: number
  turnover_rate?: number
}

export interface SectorInfo {
  code: string
  name: string
  sector_type: string
  change_pct?: number
  volume?: number
  amount?: number
}

export interface ChipData {
  code: string
  date: string
  shareholder_count?: number
  avg_shares_per_holder?: number
  control_degree?: number
  top10_holders_ratio?: number
}

export interface WatchlistItem {
  code: string
  note?: string
  created_at: string
  updated_at: string
}

export interface Strategy {
  strategy_id: string
  name: string
  strategy_type: string
  config: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at?: string
}

export interface BacktestRecord {
  backtest_id: string
  strategy_id: string
  start_date: string
  end_date: string
  initial_capital: number
  final_capital?: number
  total_return?: number
  annual_return?: number
  max_drawdown?: number
  sharpe_ratio?: number
  status: string
  created_at: string
}

export interface TradeRecord {
  id: number
  trade_type: string
  code: string
  price: number
  quantity: number
  amount: number
  commission: number
  trade_date: string
}

export interface ApiResponse<T> {
  success: boolean
  code: string
  message: string
  data: T
}

export interface PagedApiResponse<T> {
  success: boolean
  code: string
  message: string
  data: T[]
  page_info: {
    page: number
    page_size: number
    total: number
    total_pages: number
  }
}

export interface ScreenerCondition {
  industry?: string
  market_cap_min?: number
  market_cap_max?: number
  pe_min?: number
  pe_max?: number
  control_degree_min?: number
}

export interface MarketStats {
  total_stocks: number
  industry_distribution: Record<string, number>
  top_industries: [string, number][]
}

export interface OptimizationTask {
  task_id: string
  strategy_id: string
  status: 'pending' | 'running' | 'completed' | 'failed'
  progress: number
  result?: {
    best_params: Record<string, unknown>
    best_score: number
    total_iterations: number
    all_results: Array<{
      iteration: number
      params: Record<string, unknown>
      score: number
    }>
  }
  error?: string
}

export interface PresetCondition {
  id: string
  name: string
  description?: string
  conditions: ScreenerCondition
}

export interface SectorRankingItem extends SectorInfo {
  rank?: number
}

export interface ChipRankingItem extends ChipData {
  name: string
  rank?: number
}

export interface StatCardProps {
  label: string
  value: string | number
  helpText?: string
  size?: 'sm' | 'md' | 'lg'
  colorScheme?: 'default' | 'primary' | 'success' | 'warning' | 'danger'
}

export interface RankBadgeProps {
  rank: number
  size?: 'sm' | 'md' | 'lg'
}
