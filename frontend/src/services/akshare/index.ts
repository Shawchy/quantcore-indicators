/**
 * 东方财富盘口异动和涨停板行情 API 服务
 */
import api from '../api';

/** 异动类型 */
export interface ChangeType {
  key: string;
  name: string;
}

/** 盘口异动数据 */
export interface StockChange {
  time: string;
  code: string;
  name: string;
  board: string;
  related_info: string;
  change_type: string;
}

/** 板块异动数据 */
export interface StockBoardChange {
  board_name: string;
  change_pct: number;
  net_inflow: number;
  change_count: number;
  top_stock_code: string;
  top_stock_name: string;
  top_stock_type: string;
  change_types: Array<{ t: number; ct: number }>;
}

/** 涨停股池数据 */
export interface StockZtPool {
  serial_no: number;
  code: string;
  name: string;
  change_pct: number;
  latest_price: number;
  turnover: number;
  float_mv: number;
  total_mv: number;
  turnover_rate: number;
  seal_fund: number;
  first_seal_time: string;
  last_seal_time: string;
  open_count: number;
  zt_stats: string;
  continuous_count: number;
  industry: string;
}

/** 市场异动汇总 */
export interface MarketChangesSummary {
  timestamp: string;
  total_changes: number;
  rocket_launch: number;
  fast_rebound: number;
  big_buy: number;
  big_sell: number;
  limit_up: number;
  limit_down: number;
  high_dive: number;
}

/** 昨日涨停股池数据 */
export interface StockZtPrevious {
  serial_no: number;
  code: string;
  name: string;
  change_pct: number;
  latest_price: number;
  limit_up_price: number;
  turnover: number;
  float_mv: number;
  total_mv: number;
  turnover_rate: number;
  speed_pct: number;
  amplitude: number;
  yesterday_seal_time: string;
  yesterday_continuous: number;
  zt_stats: string;
  industry: string;
}

/** 强势股池数据 */
export interface StockZtStrong {
  serial_no: number;
  code: string;
  name: string;
  change_pct: number;
  latest_price: number;
  limit_up_price: number;
  turnover: number;
  float_mv: number;
  total_mv: number;
  turnover_rate: number;
  speed_pct: number;
  is_new_high: string;
  volume_ratio: number;
  zt_stats: string;
  reason: string;
  industry: string;
}

/** 次新股池数据 */
export interface StockZtSubNew {
  serial_no: number;
  code: string;
  name: string;
  change_pct: number;
  latest_price: number;
  limit_up_price: number;
  turnover: number;
  float_mv: number;
  total_mv: number;
  turnover_rate: number;
  open_days: number;
  open_date: string;
  list_date: string;
  is_new_high: string;
  zt_stats: string;
  industry: string;
}

/** 千股千评数据 */
export interface StockComment {
  serial_no: number;
  code: string;
  name: string;
  latest_price: number;
  change_pct: number;
  turnover_rate: number;
  pe_ratio: number;
  main_force_cost: number;
  institution_participation: number;
  comprehensive_score: number;
  rise: number;
  current_rank: number;
  attention_index: number;
  trading_day: string;
}

/** 千股千评详情 - 机构参与度 */
export interface StockCommentDetailInstitution {
  trading_day: string;
  institution_participation: number;
}

/** 千股千评详情 - 历史评分 */
export interface StockCommentDetailScore {
  trading_day: string;
  score: number;
}

/** 个股研报数据 */
export interface StockResearchReport {
  serial_no: number;
  stock_code: string;
  stock_name: string;
  report_name: string;
  rating: string;
  institution: string;
  recent_report_count: number;
  forecast_2024_eps: number | null;
  forecast_2024_pe: number | null;
  forecast_2025_eps: number | null;
  forecast_2025_pe: number | null;
  forecast_2026_eps: number | null;
  forecast_2026_pe: number | null;
  industry: string;
  report_date: string;
  report_pdf_url: string;
}

/** 沪深京 A 股公告数据 */
export interface StockNotice {
  code: string;
  name: string;
  notice_title: string;
  notice_type: string;
  notice_date: string;
  url: string;
}

/** 资产负债表数据 */
export interface StockBalanceSheet {
  secucode: string;
  security_code: string;
  security_name_abbr: string | null;
  end_date: string | null;
  report_date: string | null;
  total_assets: number | null;
  total_liabilities: number | null;
  total_equity: number | null;
  cash_equivalents: number | null;
  accounts_receivable: number | null;
  inventory: number | null;
  fixed_assets: number | null;
  short_term_borrowings: number | null;
  accounts_payable: number | null;
  long_term_borrowings: number | null;
  retained_earnings: number | null;
  paid_in_capital: number | null;
  extra_fields: Record<string, any>;
}

/** 利润表数据 */
export interface StockProfitSheet {
  secucode: string;
  security_code: string;
  security_name_abbr: string | null;
  end_date: string | null;
  report_date: string | null;
  total_revenue: number | null;
  operating_revenue: number | null;
  operating_cost: number | null;
  operating_profit: number | null;
  total_profit: number | null;
  net_profit: number | null;
  parent_netprofit: number | null;
  deduct_parent_netprofit: number | null;
  operating_tax: number | null;
  sales_expense: number | null;
  admin_expense: number | null;
  rd_expense: number | null;
  finance_expense: number | null;
  other_income: number | null;
  investment_income: number | null;
  non_operating_income: number | null;
  non_operating_expense: number | null;
  income_tax: number | null;
  extra_fields: Record<string, any>;
}

/** 现金流量表数据 */
export interface StockCashFlowSheet {
  secucode: string;
  security_code: string;
  security_name_abbr: string | null;
  end_date: string | null;
  report_date: string | null;
  operating_cash_in: number | null;
  operating_cash_out: number | null;
  operating_net_cash: number | null;
  investing_cash_in: number | null;
  investing_cash_out: number | null;
  investing_net_cash: number | null;
  financing_cash_in: number | null;
  financing_cash_out: number | null;
  financing_net_cash: number | null;
  cash_add: number | null;
  cash_end: number | null;
  depreciation: number | null;
  minority_interest: number | null;
  extra_fields: Record<string, any>;
}

/** 新浪财经财务指标数据 */
export interface StockFinancialIndicator {
  date: string | null;
  diluted_eps: number | null;
  weighted_eps: number | null;
  adjusted_eps: number | null;
  non_recurring_eps: number | null;
  adjusted_net_asset_per_share_before: number | null;
  adjusted_net_asset_per_share_after: number | null;
  operating_cash_flow_per_share: number | null;
  capital_reserve_per_share: number | null;
  undistributed_profit_per_share: number | null;
  adjusted_net_assets_per_share: number | null;
  return_on_total_assets: number | null;
  return_on_main_business: number | null;
  return_on_net_assets: number | null;
  return_on_cost_expense: number | null;
  operating_profit_margin: number | null;
  main_business_cost_ratio: number | null;
  net_profit_margin: number | null;
  share_capital_return_rate: number | null;
  return_on_net_assets_weighted: number | null;
  return_on_assets: number | null;
  gross_profit_margin: number | null;
  three_expense_ratio: number | null;
  non_main_business_ratio: number | null;
  main_profit_ratio: number | null;
  dividend_payout_ratio: number | null;
  investment_return_rate: number | null;
  main_business_profit: number | null;
  roe: number | null;
  weighted_roe: number | null;
  non_recurring_net_profit: number | null;
  revenue_growth_rate: number | null;
  net_profit_growth_rate: number | null;
  net_assets_growth_rate: number | null;
  total_assets_growth_rate: number | null;
  accounts_receivable_turnover: number | null;
  accounts_receivable_turnover_days: number | null;
  inventory_turnover_days: number | null;
  inventory_turnover: number | null;
  fixed_assets_turnover: number | null;
  total_assets_turnover: number | null;
  total_assets_turnover_days: number | null;
  current_assets_turnover: number | null;
  current_assets_turnover_days: number | null;
  equity_turnover: number | null;
  current_ratio: number | null;
  quick_ratio: number | null;
  cash_ratio: number | null;
  interest_payment_multiple: number | null;
  long_term_debt_to_working_capital: number | null;
  equity_ratio: number | null;
  long_term_debt_ratio: number | null;
  equity_to_fixed_assets: number | null;
  debt_to_equity: number | null;
  long_term_assets_to_long_term_capital: number | null;
  capitalization_ratio: number | null;
  fixed_assets_net_value_ratio: number | null;
  capital_fixed_ratio: number | null;
  equity_ratio_percent: number | null;
  liquidation_value_ratio: number | null;
  fixed_assets_ratio: number | null;
  asset_liability_ratio: number | null;
  operating_cash_to_sales: number | null;
  operating_cash_to_assets: number | null;
  operating_cash_to_net_profit: number | null;
  operating_cash_to_debt: number | null;
  cash_flow_ratio: number | null;
  short_term_stock_investment: number | null;
  short_term_bond_investment: number | null;
  short_term_other_investment: number | null;
  long_term_stock_investment: number | null;
  long_term_bond_investment: number | null;
  long_term_other_investment: number | null;
  accounts_receivable_within_1_year: number | null;
  accounts_receivable_1_to_2_years: number | null;
  accounts_receivable_2_to_3_years: number | null;
  accounts_receivable_within_3_years: number | null;
  advances_within_1_year: number | null;
  advances_1_to_2_years: number | null;
  advances_2_to_3_years: number | null;
  advances_within_3_years: number | null;
  other_receivables_within_1_year: number | null;
  other_receivables_1_to_2_years: number | null;
  other_receivables_2_to_3_years: number | null;
  other_receivables_within_3_years: number | null;
  extra_fields: Record<string, any>;
}

/** 沪深京 A 股股票列表 */
export interface StockInfoA {
  code: string;
  name: string;
}

/** 上海证券交易所股票列表 */
export interface StockInfoSH {
  security_code: string;
  security_abbr: string;
  company_name: string;
  list_date: string;
  extra_fields?: Record<string, any>;
}

/** 深圳证券交易所股票列表 */
export interface StockInfoSZ {
  board: string;
  stock_code: string;
  stock_abbr: string;
  list_date: string;
  total_shares: number | null;
  circulating_shares: number | null;
  industry: string;
  extra_fields?: Record<string, any>;
}

/** 北京证券交易所股票列表 */
export interface StockInfoBJ {
  security_code: string;
  security_abbr: string;
  total_shares: number;
  circulating_shares: number;
  list_date: string;
  industry: string;
  region: string;
  report_date: string;
  extra_fields?: Record<string, any>;
}

/** 申万行业分类变动历史 */
export interface StockIndustryClfHistSW {
  symbol: string;
  start_date: string;
  industry_code: string;
  update_time: string;
  extra_fields?: Record<string, any>;
}

/** 行业市盈率 */
export interface StockIndustryPERatio {
  change_date: string;
  industry_class: string;
  industry_level: number;
  industry_code: string;
  industry_name: string;
  company_count: number | null;
  calc_company_count: number | null;
  total_market_cap: number | null;
  net_profit: number | null;
  pe_static_weighted: number | null;
  pe_static_median: number | null;
  pe_static_arithmetic: number | null;
  extra_fields?: Record<string, any>;
}

/** 股东人数及持股集中度 */
export interface StockHoldNumCNInfo {
  security_code: string;
  security_abbr: string;
  change_date: string;
  current_holder_count: number | null;
  previous_holder_count: number | null;
  holder_count_growth: number | null;
  current_avg_shares: number | null;
  previous_avg_shares: number | null;
  avg_shares_growth: number | null;
  extra_fields?: Record<string, any>;
}

/** 美港目标价 */
export interface StockPriceJS {
  date: string;
  stock_name: string;
  rating: string | null;
  previous_target: number | null;
  latest_target: number | null;
  institution: string;
  extra_fields?: Record<string, any>;
}

/** 乐咕乐股 - 大盘拥挤度 */
export interface StockAConestionLG {
  date: string;
  close: number | null;
  congestion: number | null;
  extra_fields?: Record<string, any>;
}

/** 乐咕乐股 - 股债利差 */
export interface StockEBSLG {
  date: string;
  hs300_index: number | null;
  ebs: number | null;
  ebs_ma: number | null;
  extra_fields?: Record<string, any>;
}

/** 乐咕乐股 - 巴菲特指标 */
export interface StockBuffettIndexLG {
  date: string;
  close: number | null;
  total_market_cap: number | null;
  gdp: number | null;
  decile_10y: number | null;
  decile_all: number | null;
  extra_fields?: Record<string, any>;
}

/** 百度股市通-A 股估值数据 */
export interface StockZhValuationBaidu {
  date: string;
  value: number | null;
  extra_fields?: Record<string, any>;
}

/** 东方财富网 - 个股估值数据 */
export interface StockValueEM {
  report_date: string;
  close_price: number | null;
  change_pct: number | null;
  total_mv: number | null;
  float_mv: number | null;
  total_shares: number | null;
  float_shares: number | null;
  pe_ttm: number | null;
  pe_static: number | null;
  pb: number | null;
  peg: number | null;
  pc: number | null;
  ps: number | null;
  extra_fields?: Record<string, any>;
}

/** 百度股市通 - 涨跌投票数据 */
export interface StockZhVoteBaidu {
  period: string;
  vote_up: number | null;
  vote_down: number | null;
  vote_up_ratio: number | null;
  vote_down_ratio: number | null;
  extra_fields?: Record<string, any>;
}

/** 乐咕乐股 - 创新高/新低统计数据 */
export interface StockAHighLowStatistics {
  date: string;
  close: number | null;
  high20: number | null;
  low20: number | null;
  high60: number | null;
  low60: number | null;
  high120: number | null;
  low120: number | null;
  extra_fields?: Record<string, any>;
}

/** 乐咕乐股 - 破净股统计数据 */
export interface StockABelowNetAssetStatistics {
  date: string;
  below_net_asset: number | null;
  total_company: number | null;
  below_net_asset_ratio: number | null;
  extra_fields?: Record<string, any>;
}

/** 东方财富网 - 大宗交易市场统计 */
export interface StockDzjySctj {
  index: number | null;
  date: string;
  sh_index: number | null;
  sh_change_pct: number | null;
  total_amount: number | null;
  premium_amount: number | null;
  premium_ratio: number | null;
  discount_amount: number | null;
  discount_ratio: number | null;
  extra_fields?: Record<string, any>;
}

/** 东方财富网 - 大宗交易每日明细 */
export interface StockDzjyMrmx {
  index: number | null;
  date: string;
  stock_code: string;
  stock_name: string;
  change_pct: number | null;
  close_price: number | null;
  deal_price: number | null;
  premium_ratio: number | null;
  volume: number | null;
  amount: number | null;
  amount_ratio: number | null;
  buyer_dept: string | null;
  seller_dept: string | null;
  extra_fields?: Record<string, any>;
}

/** 平安证券 - 融资融券标的证券及保证金比例 */
export interface StockMarginRatioPa {
  stock_code: string;
  stock_name: string;
  margin_ratio: number | null;
  short_ratio: number | null;
  extra_fields?: Record<string, any>;
}

/** 东方财富网 - 融资融券账户统计 */
export interface StockMarginAccountInfo {
  date: string;
  margin_balance: number | null;
  short_balance: number | null;
  margin_buy: number | null;
  short_sell: number | null;
  broker_count: number | null;
  branch_count: number | null;
  individual_count: number | null;
  institution_count: number | null;
  active_count: number | null;
  debt_count: number | null;
  collateral_value: number | null;
  collateral_ratio: number | null;
  extra_fields?: Record<string, any>;
}

/** 上海证券交易所 - 融资融券汇总 */
export interface StockMarginSse {
  credit_trade_date: string;
  margin_balance: number | null;
  margin_buy: number | null;
  short_remaining: number | null;
  short_remaining_amount: number | null;
  short_sell: number | null;
  total_margin_short_balance: number | null;
  extra_fields?: Record<string, any>;
}

/** 上海证券交易所 - 融资融券明细 */
export interface StockMarginDetailSse {
  credit_trade_date: string;
  stock_code: string;
  stock_name: string;
  margin_balance: number | null;
  margin_buy: number | null;
  margin_repay: number | null;
  short_remaining: number | null;
  short_sell: number | null;
  short_repay: number | null;
  extra_fields?: Record<string, any>;
}

/** 深圳证券交易所 - 融资融券汇总 */
export interface StockMarginSzse {
  margin_buy: number | null;
  margin_balance: number | null;
  short_sell: number | null;
  short_remaining: number | null;
  short_balance: number | null;
  total_margin_short_balance: number | null;
  extra_fields?: Record<string, any>;
}

/** 深圳证券交易所 - 融资融券明细 */
export interface StockMarginDetailSzse {
  stock_code: string;
  stock_name: string;
  margin_buy: number | null;
  margin_balance: number | null;
  short_sell: number | null;
  short_remaining: number | null;
  short_balance: number | null;
  total_margin_short_balance: number | null;
  extra_fields?: Record<string, any>;
}

/** 深圳证券交易所 - 标的证券信息 */
export interface StockMarginUnderlyingInfoSzse {
  stock_code: string;
  stock_name: string;
  margin_target: string;
  short_target: string;
  margin_available_today: string;
  short_available_today: string;
  short_sell_price_restriction: string;
  price_limit: string;
  extra_fields?: Record<string, any>;
}

/** 东方财富网 - 盈利预测 */
export interface StockProfitForecastEm {
  serial_number: number | null;
  stock_code: string;
  stock_name: string;
  report_count: number | null;
  buy_rating: number | null;
  add_rating: number | null;
  neutral_rating: number | null;
  reduce_rating: number | null;
  sell_rating: number | null;
  eps_2022: number | null;
  eps_2023: number | null;
  eps_2024: number | null;
  eps_2025: number | null;
  extra_fields?: Record<string, any>;
}

/** 东方财富 - 行业板块 */
export interface StockBoardIndustryNameEm {
  rank: number | null;
  board_name: string;
  board_code: string;
  latest_price: number | null;
  change_amount: number | null;
  change_percent: number | null;
  total_market_value: number | null;
  turnover_rate: number | null;
  rise_count: number | null;
  fall_count: number | null;
  leading_stock: string;
  leading_stock_change_percent: number | null;
  extra_fields?: Record<string, any>;
}

/** 东方财富 - 行业板块实时行情 */
export interface StockBoardIndustrySpotEm {
  item: string;
  value: number | null;
  extra_fields?: Record<string, any>;
}

/** 东方财富 - 行业板块成份股 */
export interface StockBoardIndustryConsEm {
  serial_number: number | null;
  stock_code: string;
  stock_name: string;
  latest_price: number | null;
  change_percent: number | null;
  change_amount: number | null;
  volume: number | null;
  amount: number | null;
  amplitude: number | null;
  high: number | null;
  low: number | null;
  open: number | null;
  prev_close: number | null;
  turnover_rate: number | null;
  pe_ratio_dynamic: number | null;
  pb_ratio: number | null;
  extra_fields?: Record<string, any>;
}

/** 盘口异动 API */
export const eastMoneyApi = {
  /**
   * 获取盘口异动数据
   * @param symbol 异动类型
   */
  getStockChanges: (symbol: string = '大笔买入') =>
    api.get<StockChange[]>('/akshare/changes', { params: { symbol } }),

  /**
   * 获取板块异动详情
   */
  getBoardChanges: () =>
    api.get<StockBoardChange[]>('/akshare/board-changes'),

  /**
   * 获取涨停股池数据
   * @param date 日期，格式 YYYYMMDD，默认为今日
   */
  getZtPool: (date?: string) =>
    api.get<StockZtPool[]>('/akshare/zt-pool', { params: { date } }),

  /**
   * 获取市场异动汇总
   */
  getMarketChangesSummary: () =>
    api.get<MarketChangesSummary>('/akshare/market-changes-summary'),

  /**
   * 获取所有异动类型列表
   */
  getChangeTypes: () =>
    api.get<ChangeType[]>('/akshare/change-types'),

  /**
   * 获取昨日涨停股池数据
   * @param date 日期，格式 YYYYMMDD，默认为昨日
   */
  getZtPoolPrevious: (date?: string) =>
    api.get<StockZtPrevious[]>('/akshare/zt-pool-previous', { params: { date } }),

  /**
   * 获取强势股池数据
   * @param date 日期，格式 YYYYMMDD，默认为今日
   */
  getZtPoolStrong: (date?: string) =>
    api.get<StockZtStrong[]>('/akshare/zt-pool-strong', { params: { date } }),

  /**
   * 获取次新股池数据
   * @param date 日期，格式 YYYYMMDD，默认为今日
   */
  getZtPoolSubNew: (date?: string) =>
    api.get<StockZtSubNew[]>('/akshare/zt-pool-sub-new', { params: { date } }),

  /**
   * 获取千股千评数据
   */
  getStockComment: () =>
    api.get<StockComment[]>('/akshare/stock-comment'),

  /**
   * 获取千股千评详情 - 主力控盘 - 机构参与度
   * @param symbol 股票代码，如"600000"
   */
  getStockCommentDetailInstitution: (symbol: string) =>
    api.get<StockCommentDetailInstitution[]>(`/akshare/stock-comment-detail-institution/${symbol}`),

  /**
   * 获取千股千评详情 - 综合评价 - 历史评分
   * @param symbol 股票代码，如"600000"
   */
  getStockCommentDetailScore: (symbol: string) =>
    api.get<StockCommentDetailScore[]>(`/akshare/stock-comment-detail-score/${symbol}`),

  /**
   * 获取个股研报数据
   * @param symbol 股票代码，如"000001"
   */
  getStockResearchReport: (symbol: string) =>
    api.get<StockResearchReport[]>(`/akshare/stock-research-report/${symbol}`),

  /**
   * 获取沪深京 A 股公告
   * @param symbol 公告类型，默认为"全部"
   * @param date 日期，格式 YYYYMMDD，默认为今日
   */
  getStockNoticeReport: (symbol: string = '全部', date?: string) =>
    api.get<StockNotice[]>('/akshare/stock-notice-report', { params: { symbol, date } }),

  /**
   * 获取资产负债表 - 按报告期
   * @param symbol 股票代码，如"SH600519"
   */
  getBalanceSheetReport: (symbol: string) =>
    api.get<StockBalanceSheet[]>(`/akshare/balance-sheet-report/${symbol}`),

  /**
   * 获取资产负债表 - 按年度
   * @param symbol 股票代码，如"SH600519"
   */
  getBalanceSheetYearly: (symbol: string) =>
    api.get<StockBalanceSheet[]>(`/akshare/balance-sheet-yearly/${symbol}`),

  /**
   * 获取利润表 - 按报告期
   * @param symbol 股票代码，如"SH600519"
   */
  getProfitSheetReport: (symbol: string) =>
    api.get<StockProfitSheet[]>(`/akshare/profit-sheet-report/${symbol}`),

  /**
   * 获取利润表 - 按年度
   * @param symbol 股票代码，如"SH600519"
   */
  getProfitSheetYearly: (symbol: string) =>
    api.get<StockProfitSheet[]>(`/akshare/profit-sheet-yearly/${symbol}`),

  /**
   * 获取利润表 - 按单季度
   * @param symbol 股票代码，如"SH600519"
   */
  getProfitSheetQuarterly: (symbol: string) =>
    api.get<StockProfitSheet[]>(`/akshare/profit-sheet-quarterly/${symbol}`),

  /**
   * 获取现金流量表 - 按报告期
   * @param symbol 股票代码，如"SH600519"
   */
  getCashFlowSheetReport: (symbol: string) =>
    api.get<StockCashFlowSheet[]>(`/akshare/cash-flow-sheet-report/${symbol}`),

  /**
   * 获取现金流量表 - 按年度
   * @param symbol 股票代码，如"SH600519"
   */
  getCashFlowSheetYearly: (symbol: string) =>
    api.get<StockCashFlowSheet[]>(`/akshare/cash-flow-sheet-yearly/${symbol}`),

  /**
   * 获取现金流量表 - 按单季度
   * @param symbol 股票代码，如"SH600519"
   */
  getCashFlowSheetQuarterly: (symbol: string) =>
    api.get<StockCashFlowSheet[]>(`/akshare/cash-flow-sheet-quarterly/${symbol}`),

  /**
   * 获取新浪财经财务指标
   * @param symbol 股票代码，如"600004"
   * @param startYear 开始年份，如"2020"
   */
  getFinancialIndicator: (symbol: string, startYear?: string) =>
    api.get<StockFinancialIndicator[]>(`/akshare/financial-indicator/${symbol}`, {
      params: { start_year: startYear || '2020' }
    }),

  /**
   * 获取沪深京 A 股股票列表
   */
  getStockInfoA: () =>
    api.get<StockInfoA[]>('/akshare/stock-info-a'),

  /**
   * 获取上海证券交易所股票列表
   * @param symbol 板块类型：主板 A 股、主板 B 股、科创板
   */
  getStockInfoSH: (symbol: string = '主板 A 股') =>
    api.get<StockInfoSH[]>(`/akshare/stock-info-sh/${encodeURIComponent(symbol)}`),

  /**
   * 获取深圳证券交易所股票列表
   * @param symbol 板块类型：A 股列表、B 股列表、CDR 列表、AB 股列表
   */
  getStockInfoSZ: (symbol: string = 'A 股列表') =>
    api.get<StockInfoSZ[]>(`/akshare/stock-info-sz/${encodeURIComponent(symbol)}`),

  /**
   * 获取北京证券交易所股票列表
   */
  getStockInfoBJ: () =>
    api.get<StockInfoBJ[]>('/akshare/stock-info-bj'),

  /**
   * 获取申万行业分类变动历史
   */
  getStockIndustryClfHistSW: () =>
    api.get<StockIndustryClfHistSW[]>('/akshare/stock-industry-clf-hist-sw'),

  /**
   * 获取行业市盈率
   * @param symbol 行业分类类型：证监会行业分类、国证行业分类
   * @param date 交易日，格式 YYYYMMDD
   */
  getStockIndustryPERatio: (symbol: string, date?: string) =>
    api.get<StockIndustryPERatio[]>(
      `/akshare/stock-industry-pe-ratio/${encodeURIComponent(symbol)}`,
      { params: { date } }
    ),

  /**
   * 获取股东人数及持股集中度
   * @param date 报告期，格式 YYYYMMDD，如：20210630
   */
  getStockHoldNumCNInfo: (date: string) =>
    api.get<StockHoldNumCNInfo[]>(`/akshare/stock-hold-num-cninfo`, {
      params: { date }
    }),

  /**
   * 获取美港目标价
   * @param symbol 市场类型：us（美股）、hk（港股），默认为 us
   */
  getStockPriceJS: (symbol: string = 'us') =>
    api.get<StockPriceJS[]>(`/akshare/stock-price-js`, {
      params: { symbol }
    }),

  /**
   * 获取乐咕乐股 - 大盘拥挤度
   */
  getStockAConestionLG: () =>
    api.get<StockAConestionLG[]>('/akshare/stock-a-congestion-lg'),

  /**
   * 获取乐咕乐股 - 股债利差
   */
  getStockEBSLG: () =>
    api.get<StockEBSLG[]>('/akshare/stock-ebs-lg'),

  /**
   * 获取乐咕乐股 - 巴菲特指标
   */
  getStockBuffettIndexLG: () =>
    api.get<StockBuffettIndexLG[]>('/akshare/stock-buffett-index-lg'),

  /**
   * 获取百度股市通-A 股估值数据
   * @param symbol A 股代码，如：002044
   * @param indicator 估值指标：总市值、市盈率 (TTM)、市盈率 (静)、市净率、市现率
   * @param period 时间范围：近一年、近三年、近五年、近十年、全部
   */
  getStockZhValuationBaidu: (symbol: string, indicator?: string, period?: string) =>
    api.get<StockZhValuationBaidu[]>(
      `/akshare/stock-zh-valuation-baidu/${symbol}`,
      { params: { indicator: indicator || '总市值', period: period || '近一年' } }
    ),

  /**
   * 获取东方财富网 - 个股估值数据
   * @param symbol A 股代码，如：300766
   */
  getStockValueEM: (symbol: string) =>
    api.get<StockValueEM[]>(`/akshare/stock-value-em/${symbol}`),

  /**
   * 获取百度股市通 - 涨跌投票数据
   * @param symbol A 股股票或指数代码，如：000001
   * @param indicator 类型：指数、股票
   */
  getStockZhVoteBaidu: (symbol: string, indicator?: string) =>
    api.get<StockZhVoteBaidu[]>(
      `/akshare/stock-zh-vote-baidu/${symbol}`,
      { params: { indicator: indicator || '股票' } }
    ),

  /**
   * 获取乐咕乐股 - 创新高/新低统计数据
   * @param symbol 市场：all=全部 A 股，sz50=上证 50，hs300=沪深 300，zz500=中证 500
   */
  getStockAHighLowStatistics: (symbol?: string) =>
    api.get<StockAHighLowStatistics[]>('/akshare/stock-a-high-low-statistics', {
      params: { symbol: symbol || 'all' }
    }),

  /**
   * 获取乐咕乐股 - 破净股统计数据
   * @param symbol 市场：全部 A 股、沪深 300、上证 50、中证 500
   */
  getStockABelowNetAssetStatistics: (symbol?: string) =>
    api.get<StockABelowNetAssetStatistics[]>('/akshare/stock-a-below-net-asset-statistics', {
      params: { symbol: symbol || '全部 A 股' }
    }),

  /**
   * 获取东方财富网 - 大宗交易市场统计
   */
  getStockDzjySctj: () =>
    api.get<StockDzjySctj[]>('/akshare/stock-dzjy-sctj'),

  /**
   * 获取东方财富网 - 大宗交易每日明细
   * @param symbol 证券类型：A 股、B 股、基金、债券
   * @param start_date 开始日期，格式：YYYYMMDD
   * @param end_date 结束日期，格式：YYYYMMDD
   */
  getStockDzjyMrmx: (symbol?: string, start_date?: string, end_date?: string) =>
    api.get<StockDzjyMrmx[]>('/akshare/stock-dzjy-mrmx', {
      params: { symbol: symbol || 'A 股', start_date, end_date }
    }),

  /**
   * 获取融资融券 - 标的证券名单及保证金比例
   * @param symbol 交易所：深市、沪市、北交所
   * @param date 交易日期，格式：YYYYMMDD
   */
  getStockMarginRatioPa: (symbol?: string, date?: string) =>
    api.get<StockMarginRatioPa[]>('/akshare/stock-margin-ratio-pa', {
      params: { symbol: symbol || '深市', date }
    }),

  /**
   * 获取东方财富网 - 融资融券账户统计
   */
  getStockMarginAccountInfo: () =>
    api.get<StockMarginAccountInfo[]>('/akshare/stock-margin-account-info'),

  /**
   * 获取上海证券交易所 - 融资融券汇总
   * @param startDate 开始日期，格式 YYYYMMDD
   * @param endDate 结束日期，格式 YYYYMMDD
   */
  getStockMarginSse: (startDate: string, endDate: string) =>
    api.get<StockMarginSse[]>('/akshare/stock-margin-sse', {
      params: { start_date: startDate, end_date: endDate }
    }),

  /**
   * 获取上海证券交易所 - 融资融券明细
   * @param date 交易日期，格式 YYYYMMDD
   */
  getStockMarginDetailSse: (date: string) =>
    api.get<StockMarginDetailSse[]>(`/akshare/stock-margin-detail-sse/${date}`),

  /**
   * 获取深圳证券交易所 - 融资融券汇总
   * @param date 交易日期，格式 YYYYMMDD
   */
  getStockMarginSzse: (date: string) =>
    api.get<StockMarginSzse[]>(`/akshare/stock-margin-szse/${date}`),

  /**
   * 获取深圳证券交易所 - 融资融券明细
   * @param date 交易日期，格式 YYYYMMDD
   */
  getStockMarginDetailSzse: (date: string) =>
    api.get<StockMarginDetailSzse[]>(`/akshare/stock-margin-detail-szse/${date}`),

  /**
   * 获取深圳证券交易所 - 标的证券信息
   * @param date 交易日期，格式 YYYYMMDD
   */
  getStockMarginUnderlyingInfoSzse: (date: string) =>
    api.get<StockMarginUnderlyingInfoSzse[]>(`/akshare/stock-margin-underlying-info-szse/${date}`),

  /**
   * 获取东方财富网 - 盈利预测
   * @param symbol 行业板块名称，默认为空（获取全部数据）
   */
  getStockProfitForecastEm: (symbol?: string) =>
    api.get<StockProfitForecastEm[]>('/akshare/stock-profit-forecast-em', {
      params: { symbol: symbol || '' }
    }),

  /**
   * 获取东方财富 - 行业板块
   */
  getStockBoardIndustryNameEm: () =>
    api.get<StockBoardIndustryNameEm[]>('/akshare/stock-board-industry-name-em'),

  /**
   * 获取东方财富 - 行业板块实时行情
   * @param symbol 板块名称，如"小金属"
   */
  getStockBoardIndustrySpotEm: (symbol: string) =>
    api.get<StockBoardIndustrySpotEm[]>(`/akshare/stock-board-industry-spot-em/${symbol}`),

  /**
   * 获取东方财富 - 行业板块成份股
   * @param symbol 板块名称或板块代码，如"小金属"或"BK1027"
   */
  getStockBoardIndustryConsEm: (symbol: string) =>
    api.get<StockBoardIndustryConsEm[]>(`/akshare/stock-board-industry-cons-em/${symbol}`),
};

export default eastMoneyApi;
