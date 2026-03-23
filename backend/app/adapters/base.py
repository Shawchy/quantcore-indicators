from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import pandas as pd
import asyncio
from functools import partial
from loguru import logger


class DataSourceType(str, Enum):
    """数据源类型枚举"""
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    YFINANCE = "yfinance"
    EFINANCE = "efinance"
    TICKFLOW = "tickflow"
    EASTMONEY = "eastmoney"  # 东方财富


@dataclass
class StockBasicInfo:
    code: str
    name: str
    market: str
    industry: Optional[str] = None
    sector: Optional[str] = None
    area: Optional[str] = None
    list_date: Optional[str] = None
    total_shares: Optional[float] = None
    float_shares: Optional[float] = None


@dataclass
class KLineData:
    code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None
    turnover_rate: Optional[float] = None
    pre_close: Optional[float] = None


@dataclass
class SectorInfo:
    code: str
    name: str
    sector_type: str
    change_pct: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None


@dataclass
class ChipData:
    """股东人数（筹码）数据"""
    code: str
    date: str
    shareholder_count: Optional[int] = None
    avg_shares_per_holder: Optional[float] = None
    top10_holders_ratio: Optional[float] = None


@dataclass
class BillboardEntry:
    code: str
    name: str
    close_price: Optional[float] = None
    change_pct: Optional[float] = None
    turnover_rate: Optional[float] = None  # 换手率
    turnover_amount: Optional[float] = None  # 市场总成交额
    net_amount: Optional[float] = None  # 龙虎榜净买额
    buy_amount: Optional[float] = None  # 龙虎榜买入额
    sell_amount: Optional[float] = None  # 龙虎榜卖出额
    total_amount: Optional[float] = None  # 龙虎榜成交额
    net_ratio: Optional[float] = None  # 净买额占总成交比
    amount_ratio: Optional[float] = None  # 成交额占总成交比
    float_market_cap: Optional[float] = None  # 流通市值
    reason: Optional[str] = None  # 上榜原因
    trade_date: str = ""
    interpretation: Optional[str] = None  # 解读（如：卖一主卖，成功率 48.36%）


@dataclass
class BoardInfo:
    code: str
    name: str
    board_type: str
    board_code: str  # 板块代码（BK 开头）
    close_price: Optional[float] = None
    change_pct: Optional[float] = None
    stock_name: Optional[str] = None  # 股票名称
    stock_code: Optional[str] = None  # 股票代码


@dataclass
class ShareholderInfo:
    """股东信息"""
    code: str
    report_date: str  # 报告期/更新日期
    holder_code: str  # 股东代码
    holder_name: str  # 股东名称
    hold_amount: Optional[float] = None  # 持股数（股）
    hold_ratio: Optional[float] = None  # 持股比例（%）
    change: Optional[str] = None  # 增减描述（不变/新进/数值）
    change_rate: Optional[float] = None  # 变动率（%）


@dataclass
class IndexComponent:
    """指数成分股"""
    index_code: str
    index_name: str
    code: str
    name: str
    weight: Optional[float] = None
    industry: Optional[str] = None


@dataclass
class CapitalFlowItem:
    code: str
    name: str
    close_price: Optional[float] = None
    change_pct: Optional[float] = None
    main_net_amount: Optional[float] = None
    main_net_amount_rate: Optional[float] = None
    buy_elg_amount: Optional[float] = None
    buy_lg_amount: Optional[float] = None
    buy_md_amount: Optional[float] = None
    buy_sm_amount: Optional[float] = None
    trade_date: str = ""


@dataclass
class MarketQuote:
    """市场实时行情"""
    code: str
    name: str
    change_pct: Optional[float] = None
    price: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    open: Optional[float] = None
    change: Optional[float] = None
    turnover_rate: Optional[float] = None
    volume_ratio: Optional[float] = None
    pe_ratio: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None
    prev_close: Optional[float] = None
    total_market_cap: Optional[float] = None
    float_market_cap: Optional[float] = None
    market_type: Optional[str] = None


@dataclass
class StockIndividualInfo:
    """个股详细资料"""
    code: str
    name: str
    latest_price: Optional[float] = None
    total_shares: Optional[float] = None  # 总股本（亿股）
    float_shares: Optional[float] = None  # 流通股本（亿股）
    total_market_cap: Optional[float] = None  # 总市值（亿元）
    float_market_cap: Optional[float] = None  # 流通市值（亿元）
    pe_ratio: Optional[float] = None  # 市盈率（动态）
    pb_ratio: Optional[float] = None  # 市净率
    roe: Optional[float] = None  # ROE（加权）
    eps: Optional[float] = None  # 每股收益
    bps: Optional[float] = None  # 每股净资产
    net_profit: Optional[float] = None  # 净利润（亿元）
    revenue: Optional[float] = None  # 营业收入（亿元）
    gross_margin: Optional[float] = None  # 毛利率
    industry: Optional[str] = None  # 所属行业
    area: Optional[str] = None  # 地区
    list_date: Optional[str] = None  # 上市日期


@dataclass
class DividendInfo:
    """分红送转信息"""
    code: str
    announce_date: Optional[str] = None  # 公告日期
    record_date: Optional[str] = None  # 股权登记日
    ex_dividend_date: Optional[str] = None  # 除权除息日
    plan: Optional[str] = None  # 分配方案
    cash_dividend: Optional[float] = None  # 每股派现（元）
    bonus_shares: Optional[float] = None  # 每股送股
    capital_reserve_transfer: Optional[float] = None  # 每股转增


@dataclass
class FinancialStatement:
    """财务报表数据"""
    code: str
    report_date: Optional[str] = None  # 报告期
    statement_type: Optional[str] = None  # 报表类型（balance/income/cashflow）
    data: Optional[Dict[str, Any]] = None  # 报表数据（键值对）


@dataclass
class PerformanceExpress:
    """业绩快报"""
    code: str
    announce_date: Optional[str] = None  # 公告日期
    report_date: Optional[str] = None  # 报告期
    net_profit: Optional[float] = None  # 净利润（亿元）
    net_profit_yoy: Optional[float] = None  # 净利润同比增长率（%）
    eps: Optional[float] = None  # 每股收益
    roe: Optional[float] = None  # 净资产收益率
    revenue: Optional[float] = None  # 营业收入（亿元）
    revenue_yoy: Optional[float] = None  # 营收同比增长率（%）
    reason: Optional[str] = None  # 业绩变动原因


@dataclass
class FundFlowItem:
    """资金流向明细"""
    code: str
    trade_date: Optional[str] = None
    main_net_amount: Optional[float] = None  # 主力净流入（万元）
    main_net_ratio: Optional[float] = None  # 主力净流入占比（%）
    super_large_net: Optional[float] = None  # 超大单净流入（万元）
    large_net: Optional[float] = None  # 大单净流入（万元）
    medium_net: Optional[float] = None  # 中单净流入（万元）
    small_net: Optional[float] = None  # 小单净流入（万元）


@dataclass
class BoardDetail:
    """板块详情"""
    code: str
    name: str
    board_type: Optional[str] = None
    change_pct: Optional[float] = None
    volume: Optional[float] = None
    amount: Optional[float] = None
    total_market_cap: Optional[float] = None
    avg_pe: Optional[float] = None
    leader_code: Optional[str] = None  # 领涨股代码
    leader_name: Optional[str] = None  # 领涨股名称
    leader_change_pct: Optional[float] = None  # 领涨股涨跌幅
    components: Optional[List[Dict[str, Any]]] = None  # 成分股列表


@dataclass
class IndustryValuation:
    """行业估值数据"""
    code: str
    name: str
    index_value: Optional[float] = None  # 行业指数
    change_pct: Optional[float] = None
    pe_ttm: Optional[float] = None  # 市盈率（TTM）
    pb_ratio: Optional[float] = None  # 市净率
    total_market_cap: Optional[float] = None  # 总市值（亿元）


@dataclass
class StockRepurchase:
    """股票回购"""
    code: str
    announce_date: Optional[str] = None
    repurchase_amount: Optional[float] = None  # 回购金额（万元）
    repurchase_quantity: Optional[float] = None  # 回购数量（万股）
    repurchase_ratio: Optional[float] = None  # 回购比例（%）
    purpose: Optional[str] = None  # 回购目的
    progress: Optional[str] = None  # 实施进度
    price_range: Optional[str] = None  # 价格区间


@dataclass
class RestrictedShareUnlock:
    """限售股解禁"""
    code: str
    unlock_date: Optional[str] = None
    unlock_quantity: Optional[float] = None  # 解禁数量（万股）
    unlock_ratio: Optional[float] = None  # 解禁比例（%）
    unlock_type: Optional[str] = None  # 解禁类型
    unlock_shares_holder: Optional[str] = None  # 解禁股东


@dataclass
class FinancialPerformance:
    """财务业绩数据（季度）"""
    code: str
    name: str
    report_date: str  # 公告日期
    revenue: Optional[float] = None  # 营业收入
    revenue_growth: Optional[float] = None  # 营业收入同比增长
    revenue_qoq: Optional[float] = None  # 营业收入季度环比
    net_profit: Optional[float] = None  # 净利润
    net_profit_growth: Optional[float] = None  # 净利润同比增长
    net_profit_qoq: Optional[float] = None  # 净利润季度环比
    eps: Optional[float] = None  # 每股收益
    bvps: Optional[float] = None  # 每股净资产
    roe: Optional[float] = None  # 净资产收益率
    gross_margin: Optional[float] = None  # 销售毛利率
    cfps: Optional[float] = None  # 每股经营现金流量


@dataclass
class FundInfo:
    """基金基本信息"""
    code: str                    # 基金代码
    name: str                    # 基金简称
    establish_date: Optional[str] = None  # 成立日期
    change_pct: Optional[float] = None    # 涨跌幅（%）
    net_asset_value: Optional[float] = None  # 最新净值
    fund_company: Optional[str] = None       # 基金公司
    nav_update_date: Optional[str] = None    # 净值更新日期
    description: Optional[str] = None         # 简介


@dataclass
class ChipDistribution:
    """筹码分布数据"""
    code: str
    date: str                    # 日期
    profit_ratio: Optional[float] = None  # 获利比例（%）
    avg_cost: Optional[float] = None  # 平均成本
    cost_90_low: Optional[float] = None  # 90 成本 - 低
    cost_90_high: Optional[float] = None  # 90 成本 - 高
    concentration_90: Optional[float] = None  # 90 集中度
    cost_70_low: Optional[float] = None  # 70 成本 - 低
    cost_70_high: Optional[float] = None  # 70 成本 - 高
    concentration_70: Optional[float] = None  # 70 集中度


@dataclass
class SSESummary:
    """上海证券交易所股票数据总貌"""
    item: str                    # 项目名称
    stock: Optional[float] = None  # 股票总计
    star_market: Optional[float] = None  # 科创板
    main_board: Optional[float] = None  # 主板


@dataclass
class SZSESummary:
    """深圳证券交易所市场总貌"""
    category: str                # 证券类别
    count: Optional[int] = None  # 数量（只）
    turnover_amount: Optional[float] = None  # 成交金额（元）
    total_market_cap: Optional[float] = None  # 总市值
    float_market_cap: Optional[float] = None  # 流通市值


@dataclass
class SZSEAreaSummary:
    """深圳证券交易所地区交易排序"""
    rank: int                    # 序号
    region: str                  # 地区
    total_turnover: Optional[float] = None  # 总交易额（元）
    market_ratio: Optional[float] = None  # 占市场比例（%）
    stock_turnover: Optional[float] = None  # 股票交易额（元）
    fund_turnover: Optional[float] = None  # 基金交易额（元）
    bond_turnover: Optional[float] = None  # 债券交易额（元）
    preferred_stock_turnover: Optional[float] = None  # 优先股交易额（元）- 2025 年新增
    option_turnover: Optional[float] = None  # 期权交易额（元）- 2025 年新增


@dataclass
class SZSESectorSummary:
    """深圳证券交易所股票行业成交数据"""
    project_name: str            # 项目名称
    project_name_en: str         # 项目名称 - 英文
    trading_days: Optional[int] = None  # 交易天数
    turnover_amount: Optional[float] = None  # 成交金额（人民币元）
    turnover_ratio: Optional[float] = None  # 成交金额 - 占总计（%）
    turnover_shares: Optional[float] = None  # 成交股数（股数）
    turnover_shares_ratio: Optional[float] = None  # 成交股数 - 占总计（%）
    turnover_count: Optional[int] = None  # 成交笔数（笔）
    turnover_count_ratio: Optional[float] = None  # 成交笔数 - 占总计（%）


@dataclass
class SSEDealDaily:
    """上海证券交易所每日概况数据"""
    item: str                    # 单日情况项目
    stock: Optional[float] = None  # 股票
    main_board_a: Optional[float] = None  # 主板 A
    main_board_b: Optional[float] = None  # 主板 B
    star_market: Optional[float] = None  # 科创板
    stock_repurchase: Optional[float] = None  # 股票回购


@dataclass
class StockIndividualInfoEM:
    """东方财富个股信息"""
    item: str                    # 项目名称
    value: Optional[float] = None  # 项目值


@dataclass
class StockIndividualBasicInfoXQ:
    """雪球财经个股基本信息"""
    item: str                    # 项目名称
    value: Optional[str] = None  # 项目值（大部分为字符串）
    value_numeric: Optional[float] = None  # 数值型项目值（用于注册资本、发行量等）


@dataclass
class StockZhASpot:
    """沪深京 A 股实时行情数据"""
    serial_number: int           # 序号
    code: str                    # 代码
    name: str                    # 名称
    latest_price: Optional[float] = None  # 最新价
    change_pct: Optional[float] = None  # 涨跌幅（%）
    change_amount: Optional[float] = None  # 涨跌额
    volume: Optional[float] = None  # 成交量（手）
    turnover: Optional[float] = None  # 成交额（元）
    amplitude: Optional[float] = None  # 振幅（%）
    high: Optional[float] = None  # 最高价
    low: Optional[float] = None  # 最低价
    open: Optional[float] = None  # 今开
    prev_close: Optional[float] = None  # 昨收
    volume_ratio: Optional[float] = None  # 量比
    turnover_rate: Optional[float] = None  # 换手率（%）
    pe_ratio_dynamic: Optional[float] = None  # 市盈率 - 动态
    pb_ratio: Optional[float] = None  # 市净率
    total_market_cap: Optional[float] = None  # 总市值（元）
    float_market_cap: Optional[float] = None  # 流通市值（元）
    speed: Optional[float] = None  # 涨速
    change_5min: Optional[float] = None  # 5 分钟涨跌（%）
    change_60d: Optional[float] = None  # 60 日涨跌幅（%）
    change_ytd: Optional[float] = None  # 年初至今涨跌幅（%）


@dataclass
class StockZhASpotSina:
    """新浪财经 - 沪深京 A 股实时行情数据"""
    code: str                    # 代码
    name: str                    # 名称
    latest_price: Optional[float] = None  # 最新价
    change_amount: Optional[float] = None  # 涨跌额
    change_pct: Optional[float] = None  # 涨跌幅（%）
    buy: Optional[float] = None  # 买入价
    sell: Optional[float] = None  # 卖出价
    prev_close: Optional[float] = None  # 昨收
    open: Optional[float] = None  # 今开
    high: Optional[float] = None  # 最高价
    low: Optional[float] = None  # 最低价
    volume: Optional[float] = None  # 成交量（股）
    turnover: Optional[float] = None  # 成交额（元）
    timestamp: Optional[str] = None  # 时间戳


@dataclass
class StockZhAHist:
    """东方财富 - 沪深京 A 股历史行情数据"""
    date: str                    # 交易日
    code: str                    # 股票代码
    open: Optional[float] = None  # 开盘价
    close: Optional[float] = None  # 收盘价
    high: Optional[float] = None  # 最高价
    low: Optional[float] = None  # 最低价
    volume: Optional[float] = None  # 成交量（手）
    turnover: Optional[float] = None  # 成交额（元）
    amplitude: Optional[float] = None  # 振幅（%）
    change_pct: Optional[float] = None  # 涨跌幅（%）
    change_amount: Optional[float] = None  # 涨跌额（元）
    turnover_rate: Optional[float] = None  # 换手率（%）


@dataclass
class StockZhAMinuteSina:
    """新浪财经 - 沪深京 A 股分时数据（1/5/15/30/60 分钟）"""
    day: str                     # 时间
    open: Optional[float] = None  # 开盘价
    high: Optional[float] = None  # 最高价
    low: Optional[float] = None  # 最低价
    close: Optional[float] = None  # 收盘价
    volume: Optional[float] = None  # 成交量
    amount: Optional[float] = None  # 成交额


@dataclass
class StockZhAMinuteEM:
    """东方财富 - 沪深京 A 股分时数据（1/5/15/30/60 分钟）"""
    time: str                    # 时间
    open: Optional[float] = None  # 开盘价
    close: Optional[float] = None  # 收盘价
    high: Optional[float] = None  # 最高价
    low: Optional[float] = None  # 最低价
    volume: Optional[float] = None  # 成交量（手）
    turnover: Optional[float] = None  # 成交额
    change_pct: Optional[float] = None  # 涨跌幅（%）- 仅 5/15/30/60 分钟
    change_amount: Optional[float] = None  # 涨跌额 - 仅 5/15/30/60 分钟
    amplitude: Optional[float] = None  # 振幅（%）- 仅 5/15/30/60 分钟
    turnover_rate: Optional[float] = None  # 换手率（%）- 仅 5/15/30/60 分钟
    avg_price: Optional[float] = None  # 均价 - 仅 1 分钟


@dataclass
class StockIntradayEM:
    """东方财富 - 日内分时数据（最近一个交易日，含盘前）"""
    time: str                    # 时间
    price: Optional[float] = None  # 成交价
    volume: Optional[int] = None  # 手数
    type: Optional[str] = None  # 买卖盘性质（买盘/卖盘/中性盘）


@dataclass
class StockIntradaySina:
    """新浪财经 - 日内分时数据（指定交易日，大单数据）"""
    symbol: str                  # 股票代码
    name: str                    # 股票名称
    ticktime: str                # 时间
    price: Optional[float] = None  # 成交价
    volume: Optional[int] = None  # 成交量（股）
    prev_price: Optional[float] = None  # 前一笔价格
    kind: Optional[str] = None  # 买卖盘性质（D=卖盘，U=买盘，E=集合竞价）


@dataclass
class StockZhAHistPreMinEM:
    """东方财富 - 盘前分钟数据（含盘前和盘中）"""
    time: str                    # 时间
    open: Optional[float] = None  # 开盘价
    close: Optional[float] = None  # 收盘价
    high: Optional[float] = None  # 最高价
    low: Optional[float] = None  # 最低价
    volume: Optional[float] = None  # 成交量（手）
    turnover: Optional[float] = None  # 成交额
    latest_price: Optional[float] = None  # 最新价


@dataclass
class StockZhGrowthComparisonEM:
    """东方财富 - 成长性比较数据（同行比较）"""
    code: str                    # 代码
    name: str                    # 简称
    eps_growth_3y: Optional[float] = None  # 基本每股收益增长率 -3 年复合
    eps_growth_24a: Optional[float] = None  # 基本每股收益增长率 -24A
    eps_growth_ttm: Optional[float] = None  # 基本每股收益增长率 -TTM
    eps_growth_25e: Optional[float] = None  # 基本每股收益增长率 -25E
    eps_growth_26e: Optional[float] = None  # 基本每股收益增长率 -26E
    eps_growth_27e: Optional[float] = None  # 基本每股收益增长率 -27E
    revenue_growth_3y: Optional[float] = None  # 营业收入增长率 -3 年复合
    revenue_growth_24a: Optional[float] = None  # 营业收入增长率 -24A
    revenue_growth_ttm: Optional[float] = None  # 营业收入增长率 -TTM
    revenue_growth_25e: Optional[float] = None  # 营业收入增长率 -25E
    revenue_growth_26e: Optional[float] = None  # 营业收入增长率 -26E
    revenue_growth_27e: Optional[float] = None  # 营业收入增长率 -27E
    net_profit_growth_3y: Optional[float] = None  # 净利润增长率 -3 年复合
    net_profit_growth_24a: Optional[float] = None  # 净利润增长率 -24A
    net_profit_growth_ttm: Optional[float] = None  # 净利润增长率 -TTM
    net_profit_growth_25e: Optional[float] = None  # 净利润增长率 -25E
    net_profit_growth_26e: Optional[float] = None  # 净利润增长率 -26E
    net_profit_growth_27e: Optional[float] = None  # 净利润增长率 -27E
    eps_growth_3y_rank: Optional[float] = None  # 基本每股收益增长率 -3 年复合排名


@dataclass
class StockZhValuationComparisonEM:
    """东方财富 - 估值比较数据（同行比较）"""
    rank: Optional[float] = None  # 排名
    code: str                    # 代码
    name: str                    # 简称
    peg: Optional[float] = None  # PEG
    pe_24a: Optional[float] = None  # 市盈率 -24A
    pe_ttm: Optional[float] = None  # 市盈率 -TTM
    pe_25e: Optional[float] = None  # 市盈率 -25E
    pe_26e: Optional[float] = None  # 市盈率 -26E
    pe_27e: Optional[float] = None  # 市盈率 -27E
    ps_24a: Optional[float] = None  # 市销率 -24A
    ps_ttm: Optional[float] = None  # 市销率 -TTM
    ps_25e: Optional[float] = None  # 市销率 -25E
    ps_26e: Optional[float] = None  # 市销率 -26E
    ps_27e: Optional[float] = None  # 市销率 -27E
    pb_24a: Optional[float] = None  # 市净率 -24A
    pb_mrq: Optional[float] = None  # 市净率 -MRQ
    pcf1_24a: Optional[float] = None  # 市现率 1-24A
    pcf1_ttm: Optional[float] = None  # 市现率 1-TTM
    pcf2_24a: Optional[float] = None  # 市现率 2-24A
    pcf2_ttm: Optional[float] = None  # 市现率 2-TTM
    ev_ebitda_24a: Optional[float] = None  # EV/EBITDA-24A


@dataclass
class StockZhDupontComparisonEM:
    """东方财富 - 杜邦分析比较数据（同行比较）"""
    code: str                    # 代码
    name: str                    # 简称
    roe_3y_avg: Optional[float] = None  # ROE-3 年平均
    roe_22a: Optional[float] = None  # ROE-22A
    roe_23a: Optional[float] = None  # ROE-23A
    roe_24a: Optional[float] = None  # ROE-24A
    net_profit_margin_3y_avg: Optional[float] = None  # 净利率 -3 年平均
    net_profit_margin_22a: Optional[float] = None  # 净利率 -22A
    net_profit_margin_23a: Optional[float] = None  # 净利率 -23A
    net_profit_margin_24a: Optional[float] = None  # 净利率 -24A
    asset_turnover_3y_avg: Optional[float] = None  # 总资产周转率 -3 年平均
    asset_turnover_22a: Optional[float] = None  # 总资产周转率 -22A
    asset_turnover_23a: Optional[float] = None  # 总资产周转率 -23A
    asset_turnover_24a: Optional[float] = None  # 总资产周转率 -24A
    equity_multiplier_3y_avg: Optional[float] = None  # 权益乘数 -3 年平均
    equity_multiplier_22a: Optional[float] = None  # 权益乘数 -22A
    equity_multiplier_23a: Optional[float] = None  # 权益乘数 -23A
    equity_multiplier_24a: Optional[float] = None  # 权益乘数 -24A
    roe_3y_avg_rank: Optional[float] = None  # ROE-3 年平均排名


@dataclass
class StockZhScaleComparisonEM:
    """东方财富 - 公司规模比较数据（同行比较）"""
    code: str                    # 代码
    name: str                    # 简称
    total_market_cap: Optional[float] = None  # 总市值
    total_market_cap_rank: Optional[int] = None  # 总市值排名
    float_market_cap: Optional[float] = None  # 流通市值
    float_market_cap_rank: Optional[int] = None  # 流通市值排名
    revenue: Optional[float] = None  # 营业收入
    revenue_rank: Optional[int] = None  # 营业收入排名
    net_profit: Optional[float] = None  # 净利润
    net_profit_rank: Optional[int] = None  # 净利润排名


@dataclass
class StockYjbbEM:
    """东方财富 - 业绩报表数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 股票代码
    name: str = ""  # 股票简称
    eps: Optional[float] = None  # 每股收益（元）
    total_revenue: Optional[float] = None  # 营业总收入（元）
    revenue_yoy: Optional[float] = None  # 营业收入 - 同比增长（%）
    revenue_qoq: Optional[float] = None  # 营业收入 - 季度环比增长（%）
    net_profit: Optional[float] = None  # 净利润（元）
    net_profit_yoy: Optional[float] = None  # 净利润 - 同比增长（%）
    net_profit_qoq: Optional[float] = None  # 净利润 - 季度环比增长（%）
    net_assets_per_share: Optional[float] = None  # 每股净资产（元）
    roe: Optional[float] = None  # 净资产收益率（%）
    operating_cash_flow_per_share: Optional[float] = None  # 每股经营现金流量（元）
    gross_margin: Optional[float] = None  # 销售毛利率（%）
    industry: Optional[str] = None  # 所处行业
    announce_date: Optional[str] = None  # 最新公告日期


@dataclass
class StockYjkbEM:
    """东方财富 - 业绩快报数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 股票代码
    name: str = ""  # 股票简称
    eps: Optional[float] = None  # 每股收益
    operating_revenue: Optional[float] = None  # 营业收入（元）
    revenue_last_year: Optional[float] = None  # 营业收入 - 去年同期（元）
    revenue_yoy: Optional[str] = None  # 营业收入 - 同比增长（%）
    revenue_qoq: Optional[str] = None  # 营业收入 - 季度环比增长
    net_profit: Optional[float] = None  # 净利润（元）
    net_profit_last_year: Optional[float] = None  # 净利润 - 去年同期（元）
    net_profit_yoy: Optional[str] = None  # 净利润 - 同比增长（%）
    net_profit_qoq: Optional[str] = None  # 净利润 - 季度环比增长
    net_assets_per_share: Optional[float] = None  # 每股净资产
    roe: Optional[float] = None  # 净资产收益率（%）
    industry: Optional[str] = None  # 所处行业
    announce_date: Optional[str] = None  # 公告日期
    market: Optional[str] = None  # 市场板块
    security_type: Optional[str] = None  # 证券类型


@dataclass
class StockYjygEM:
    """东方财富 - 业绩预告数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 股票代码
    name: str = ""  # 股票简称
    forecast_indicator: Optional[str] = None  # 预测指标
    performance_change: Optional[str] = None  # 业绩变动
    forecast_value: Optional[float] = None  # 预测数值（元）
    performance_change_ratio: Optional[float] = None  # 业绩变动幅度（%）
    performance_change_reason: Optional[str] = None  # 业绩变动原因
    forecast_type: Optional[str] = None  # 预告类型（预增、预减、首亏、续亏等）
    last_year_value: Optional[float] = None  # 上年同期值（元）
    announce_date: Optional[str] = None  # 公告日期


@dataclass
class StockIndustryCategoryCNINFO:
    """巨潮资讯 - 行业分类数据"""
    category_code: Optional[str] = None  # 类目编码
    category_name: Optional[str] = None  # 类目名称
    end_date: Optional[str] = None  # 终止日期
    industry_type: Optional[str] = None  # 行业类型
    industry_type_code: Optional[str] = None  # 行业类型编码
    category_name_en: Optional[str] = None  # 类目名称英文
    parent_code: Optional[str] = None  # 父类编码
    level: Optional[int] = None  # 分级


@dataclass
class StockIndustryChangeCNINFO:
    """巨潮资讯 - 上市公司行业归属的变动情况"""
    new_stock_name: Optional[str] = None  # 新证券简称
    industry_mid_class: Optional[str] = None  # 行业中类
    industry_large_class: Optional[str] = None  # 行业大类
    industry_sub_class: Optional[str] = None  # 行业次类
    industry_category: Optional[str] = None  # 行业门类
    org_name: Optional[str] = None  # 机构名称
    industry_code: Optional[str] = None  # 行业编码
    classification_standard: Optional[str] = None  # 分类标准
    classification_standard_code: Optional[str] = None  # 分类标准编码
    stock_code: Optional[str] = None  # 证券代码
    change_date: Optional[str] = None  # 变更日期


@dataclass
class StockZcfzEM:
    """东方财富 - 资产负债表数据（沪深/北交所）"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 股票代码
    name: str = ""  # 股票简称
    monetary_fund: Optional[float] = None  # 资产 - 货币资金（元）
    accounts_receivable: Optional[float] = None  # 资产 - 应收账款（元）
    inventory: Optional[float] = None  # 资产 - 存货（元）
    total_assets: Optional[float] = None  # 资产 - 总资产（元）
    total_assets_yoy: Optional[float] = None  # 资产 - 总资产同比（%）
    accounts_payable: Optional[float] = None  # 负债 - 应付账款（元）
    total_liabilities: Optional[float] = None  # 负债 - 总负债（元）
    advance_receipts: Optional[float] = None  # 负债 - 预收账款（元）
    total_liabilities_yoy: Optional[float] = None  # 负债 - 总负债同比（%）
    asset_liability_ratio: Optional[float] = None  # 资产负债率（%）
    total_equity: Optional[float] = None  # 股东权益合计（元）
    announce_date: Optional[str] = None  # 公告日期


@dataclass
class StockLrbEM:
    """东方财富 - 利润表数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 股票代码
    name: str = ""  # 股票简称
    net_profit: Optional[float] = None  # 净利润（元）
    net_profit_yoy: Optional[float] = None  # 净利润同比（%）
    total_revenue: Optional[float] = None  # 营业总收入（元）
    total_revenue_yoy: Optional[float] = None  # 营业总收入同比（%）
    operating_expense: Optional[float] = None  # 营业总支出 - 营业支出（元）
    selling_expense: Optional[float] = None  # 营业总支出 - 销售费用（元）
    administrative_expense: Optional[float] = None  # 营业总支出 - 管理费用（元）
    financial_expense: Optional[float] = None  # 营业总支出 - 财务费用（元）
    total_operating_expense: Optional[float] = None  # 营业总支出（元）
    operating_profit: Optional[float] = None  # 营业利润（元）
    total_profit: Optional[float] = None  # 利润总额（元）
    announce_date: Optional[str] = None  # 公告日期


@dataclass
class StockXjllEM:
    """东方财富 - 现金流量表数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 股票代码
    name: str = ""  # 股票简称
    net_cash_flow: Optional[float] = None  # 净现金流 - 净现金流（元）
    net_cash_flow_yoy: Optional[float] = None  # 净现金流 - 同比增长（%）
    operating_cash_flow: Optional[float] = None  # 经营性现金流 - 现金流量净额（元）
    operating_cash_flow_ratio: Optional[float] = None  # 经营性现金流 - 净现金流占比（%）
    investing_cash_flow: Optional[float] = None  # 投资性现金流 - 现金流量净额（元）
    investing_cash_flow_ratio: Optional[float] = None  # 投资性现金流 - 净现金流占比（%）
    financing_cash_flow: Optional[float] = None  # 融资性现金流 - 现金流量净额（元）
    financing_cash_flow_ratio: Optional[float] = None  # 融资性现金流 - 净现金流占比（%）
    announce_date: Optional[str] = None  # 公告日期


@dataclass
class StockGgcgEM:
    """东方财富 - 股东增减持数据"""
    code: str = ""  # 代码
    name: str = ""  # 名称
    latest_price: Optional[float] = None  # 最新价
    change_pct: Optional[float] = None  # 涨跌幅（%）
    shareholder_name: Optional[str] = None  # 股东名称
    change_type: Optional[int] = None  # 持股变动信息 - 增减（1=增持，-1=减持）
    change_amount: Optional[float] = None  # 持股变动信息 - 变动数量（万股）
    change_total_ratio: Optional[float] = None  # 持股变动信息 - 占总股本比例（%）
    change_float_ratio: Optional[float] = None  # 持股变动信息 - 占流通股比例（%）
    after_hold_total: Optional[float] = None  # 变动后持股情况 - 持股总数（万股）
    after_hold_total_ratio: Optional[float] = None  # 变动后持股情况 - 占总股本比例（%）
    after_hold_float: Optional[float] = None  # 变动后持股情况 - 持流通股数（万股）
    after_hold_float_ratio: Optional[float] = None  # 变动后持股情况 - 占流通股比例（%）
    start_date: Optional[str] = None  # 变动开始日
    end_date: Optional[str] = None  # 变动截止日
    announce_date: Optional[str] = None  # 公告日


@dataclass
class StockFundFlowIndividual:
    """同花顺 - 个股资金流数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 股票代码
    name: str = ""  # 股票简称
    latest_price: Optional[float] = None  # 最新价
    change_pct: Optional[str] = None  # 涨跌幅（%）
    turnover_rate: Optional[str] = None  # 换手率
    inflow: Optional[float] = None  # 流入资金（元）
    outflow: Optional[float] = None  # 流出资金（元）
    net_flow: Optional[float] = None  # 净额（元）
    turnover_amount: Optional[float] = None  # 成交额（元）
    # 以下为 3 日/5 日/10 日/20 日排行特有字段
    stage_change_pct: Optional[str] = None  # 阶段涨跌幅（%）
    continuous_turnover: Optional[str] = None  # 连续换手率（%）
    net_inflow: Optional[float] = None  # 资金流入净额（元）


@dataclass
class StockFundFlowConcept:
    """同花顺 - 概念资金流数据"""
    serial_number: Optional[int] = None  # 序号
    concept_name: str = ""  # 行业/概念名称
    concept_index: Optional[float] = None  # 行业指数
    change_pct: Optional[float] = None  # 行业 - 涨跌幅（%）
    inflow: Optional[float] = None  # 流入资金（亿）
    outflow: Optional[float] = None  # 流出资金（亿）
    net_flow: Optional[float] = None  # 净额（亿）
    company_count: Optional[int] = None  # 公司家数
    leading_stock: Optional[str] = None  # 领涨股
    leading_change_pct: Optional[float] = None  # 领涨股 - 涨跌幅（%）
    leading_price: Optional[float] = None  # 当前价（元）
    # 以下为 3 日/5 日/10 日/20 日排行特有字段
    stage_change_pct: Optional[str] = None  # 阶段涨跌幅（%）


@dataclass
class StockFundFlowIndustry:
    """同花顺 - 行业资金流数据"""
    serial_number: Optional[int] = None  # 序号
    industry_name: str = ""  # 行业名称
    industry_index: Optional[float] = None  # 行业指数
    change_pct: Optional[str] = None  # 行业 - 涨跌幅（%）
    inflow: Optional[float] = None  # 流入资金（亿）
    outflow: Optional[float] = None  # 流出资金（亿）
    net_flow: Optional[float] = None  # 净额（亿）
    company_count: Optional[int] = None  # 公司家数
    leading_stock: Optional[str] = None  # 领涨股
    leading_change_pct: Optional[str] = None  # 领涨股 - 涨跌幅（%）
    leading_price: Optional[float] = None  # 当前价
    # 以下为 3 日/5 日/10 日/20 日排行特有字段
    stage_change_pct: Optional[str] = None  # 阶段涨跌幅（%）


@dataclass
class StockFundFlowBigDeal:
    """同花顺 - 大单追踪数据"""
    trade_time: Optional[str] = None  # 成交时间
    code: str = ""  # 股票代码
    name: str = ""  # 股票简称
    trade_price: Optional[float] = None  # 成交价格
    volume: Optional[int] = None  # 成交量（股）
    amount: Optional[float] = None  # 成交额（万元）
    deal_type: Optional[str] = None  # 大单性质（买盘/卖盘）
    change_pct: Optional[str] = None  # 涨跌幅（%）
    change_amount: Optional[float] = None  # 涨跌额（元）


@dataclass
class StockIndividualFundFlow:
    """东方财富 - 个股资金流数据"""
    date: Optional[str] = None  # 日期
    close_price: Optional[float] = None  # 收盘价
    change_pct: Optional[float] = None  # 涨跌幅（%）
    main_net_inflow: Optional[float] = None  # 主力净流入 - 净额
    main_net_inflow_ratio: Optional[float] = None  # 主力净流入 - 净占比（%）
    super_order_net_inflow: Optional[float] = None  # 超大单净流入 - 净额
    super_order_net_inflow_ratio: Optional[float] = None  # 超大单净流入 - 净占比（%）
    big_order_net_inflow: Optional[float] = None  # 大单净流入 - 净额
    big_order_net_inflow_ratio: Optional[float] = None  # 大单净流入 - 净占比（%）
    medium_order_net_inflow: Optional[float] = None  # 中单净流入 - 净额
    medium_order_net_inflow_ratio: Optional[float] = None  # 中单净流入 - 净占比（%）
    small_order_net_inflow: Optional[float] = None  # 小单净流入 - 净额
    small_order_net_inflow_ratio: Optional[float] = None  # 小单净流入 - 净占比（%）


@dataclass
class StockIndividualFundFlowRank:
    """东方财富 - 个股资金流排名数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 代码
    name: str = ""  # 名称
    latest_price: Optional[float] = None  # 最新价
    change_pct: Optional[float] = None  # 涨跌幅（%）
    main_net_inflow: Optional[float] = None  # 主力净流入 - 净额
    main_net_inflow_ratio: Optional[float] = None  # 主力净流入 - 净占比（%）
    super_order_net_inflow: Optional[float] = None  # 超大单净流入 - 净额
    super_order_net_inflow_ratio: Optional[float] = None  # 超大单净流入 - 净占比（%）
    big_order_net_inflow: Optional[float] = None  # 大单净流入 - 净额
    big_order_net_inflow_ratio: Optional[float] = None  # 大单净流入 - 净占比（%）
    medium_order_net_inflow: Optional[float] = None  # 中单净流入 - 净额
    medium_order_net_inflow_ratio: Optional[float] = None  # 中单净流入 - 净占比（%）
    small_order_net_inflow: Optional[float] = None  # 小单净流入 - 净额
    small_order_net_inflow_ratio: Optional[float] = None  # 小单净流入 - 净占比（%）


@dataclass
class StockMarketFundFlow:
    """东方财富 - 大盘资金流数据"""
    date: Optional[str] = None  # 日期
    shanghai_close: Optional[float] = None  # 上证 - 收盘价
    shanghai_change_pct: Optional[float] = None  # 上证 - 涨跌幅（%）
    shenzhen_close: Optional[float] = None  # 深证 - 收盘价
    shenzhen_change_pct: Optional[float] = None  # 深证 - 涨跌幅（%）
    main_net_inflow: Optional[float] = None  # 主力净流入 - 净额
    main_net_inflow_ratio: Optional[float] = None  # 主力净流入 - 净占比（%）
    super_order_net_inflow: Optional[float] = None  # 超大单净流入 - 净额
    super_order_net_inflow_ratio: Optional[float] = None  # 超大单净流入 - 净占比（%）
    big_order_net_inflow: Optional[float] = None  # 大单净流入 - 净额
    big_order_net_inflow_ratio: Optional[float] = None  # 大单净流入 - 净占比（%）
    medium_order_net_inflow: Optional[float] = None  # 中单净流入 - 净额
    medium_order_net_inflow_ratio: Optional[float] = None  # 中单净流入 - 净占比（%）
    small_order_net_inflow: Optional[float] = None  # 小单净流入 - 净额
    small_order_net_inflow_ratio: Optional[float] = None  # 小单净流入 - 净占比（%）


@dataclass
class StockSectorFundFlowRank:
    """东方财富 - 板块资金流排名数据"""
    serial_number: Optional[int] = None  # 序号
    name: str = ""  # 名称
    change_pct: Optional[float] = None  # 涨跌幅（%）
    main_net_inflow: Optional[float] = None  # 主力净流入 - 净额
    main_net_inflow_ratio: Optional[float] = None  # 主力净流入 - 净占比（%）
    super_order_net_inflow: Optional[float] = None  # 超大单净流入 - 净额
    super_order_net_inflow_ratio: Optional[float] = None  # 超大单净流入 - 净占比（%）
    big_order_net_inflow: Optional[float] = None  # 大单净流入 - 净额
    big_order_net_inflow_ratio: Optional[float] = None  # 大单净流入 - 净占比（%）
    medium_order_net_inflow: Optional[float] = None  # 中单净流入 - 净额
    medium_order_net_inflow_ratio: Optional[float] = None  # 中单净流入 - 净占比（%）
    small_order_net_inflow: Optional[float] = None  # 小单净流入 - 净额
    small_order_net_inflow_ratio: Optional[float] = None  # 小单净流入 - 净占比（%）
    main_net_inflow_max_stock: Optional[str] = None  # 主力净流入最大股


@dataclass
class StockMainFundFlow:
    """东方财富 - 主力净流入排名数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 代码
    name: str = ""  # 名称
    latest_price: Optional[float] = None  # 最新价
    today_main_ratio: Optional[float] = None  # 今日排行榜 - 主力净占比（%）
    today_rank: Optional[int] = None  # 今日排行榜 - 今日排名
    today_change_pct: Optional[float] = None  # 今日排行榜 - 今日涨跌（%）
    day5_main_ratio: Optional[float] = None  # 5 日排行榜 - 主力净占比（%）
    day5_rank: Optional[int] = None  # 5 日排行榜 - 5 日排名
    day5_change_pct: Optional[float] = None  # 5 日排行榜 - 5 日涨跌（%）
    day10_main_ratio: Optional[float] = None  # 10 日排行榜 - 主力净占比（%）
    day10_rank: Optional[int] = None  # 10 日排行榜 - 10 日排名
    day10_change_pct: Optional[float] = None  # 10 日排行榜 - 10 日涨跌（%）
    sector: Optional[str] = None  # 所属板块


@dataclass
class StockSectorFundFlowSummary:
    """东方财富 - 行业个股资金流数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 代码
    name: str = ""  # 名称
    latest_price: Optional[float] = None  # 最新价
    change_pct: Optional[float] = None  # 涨跌幅（%）
    main_net_inflow: Optional[float] = None  # 主力净流入 - 净额
    main_net_inflow_ratio: Optional[float] = None  # 主力净流入 - 净占比（%）
    super_order_net_inflow: Optional[float] = None  # 超大单净流入 - 净额
    super_order_net_inflow_ratio: Optional[float] = None  # 超大单净流入 - 净占比（%）
    big_order_net_inflow: Optional[float] = None  # 大单净流入 - 净额
    big_order_net_inflow_ratio: Optional[float] = None  # 大单净流入 - 净占比（%）
    medium_order_net_inflow: Optional[float] = None  # 中单净流入 - 净额
    medium_order_net_inflow_ratio: Optional[float] = None  # 中单净流入 - 净占比（%）
    small_order_net_inflow: Optional[float] = None  # 小单净流入 - 净额
    small_order_net_inflow_ratio: Optional[float] = None  # 小单净流入 - 净占比（%）


@dataclass
class StockSectorFundFlowHist:
    """东方财富 - 行业/概念历史资金流数据"""
    date: Optional[str] = None  # 日期
    main_net_inflow: Optional[float] = None  # 主力净流入 - 净额
    main_net_inflow_ratio: Optional[float] = None  # 主力净流入 - 净占比（%）
    super_order_net_inflow: Optional[float] = None  # 超大单净流入 - 净额
    super_order_net_inflow_ratio: Optional[float] = None  # 超大单净流入 - 净占比（%）
    big_order_net_inflow: Optional[float] = None  # 大单净流入 - 净额
    big_order_net_inflow_ratio: Optional[float] = None  # 大单净流入 - 净占比（%）
    medium_order_net_inflow: Optional[float] = None  # 中单净流入 - 净额
    medium_order_net_inflow_ratio: Optional[float] = None  # 中单净流入 - 净占比（%）
    small_order_net_inflow: Optional[float] = None  # 小单净流入 - 净额
    small_order_net_inflow_ratio: Optional[float] = None  # 小单净流入 - 净占比（%）


@dataclass
class StockReportFundHold:
    """东方财富 - 基金持仓汇总数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 股票代码
    name: str = ""  # 股票简称
    fund_count: Optional[int] = None  # 持有基金家数（家）
    total_shares: Optional[int] = None  # 持股总数（股）
    market_value: Optional[float] = None  # 持股市值（元）
    change_type: Optional[str] = None  # 持股变化（新进/增持/减持/退出）
    change_shares: Optional[int] = None  # 持股变动数值（股）
    change_ratio: Optional[float] = None  # 持股变动比例（%）


@dataclass
class StockReportFundHoldDetail:
    """东方财富 - 基金持仓明细数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 股票代码
    name: str = ""  # 股票简称
    shares: Optional[int] = None  # 持股数（股）
    market_value: Optional[float] = None  # 持股市值（元）
    ratio_of_total_shares: Optional[float] = None  # 占总股本比例（%）
    ratio_of_float_shares: Optional[float] = None  # 占流通股本比例（%）


@dataclass
class StockLhbDetailEm:
    """东方财富 - 龙虎榜详情数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 代码
    name: str = ""  # 名称
    list_date: Optional[str] = None  # 上榜日
    interpretation: Optional[str] = None  # 解读
    close_price: Optional[float] = None  # 收盘价
    change_pct: Optional[float] = None  # 涨跌幅（%）
    net_buy_amount: Optional[float] = None  # 龙虎榜净买额（元）
    buy_amount: Optional[float] = None  # 龙虎榜买入额（元）
    sell_amount: Optional[float] = None  # 龙虎榜卖出额（元）
    total_amount: Optional[float] = None  # 龙虎榜成交额（元）
    market_total_amount: Optional[int] = None  # 市场总成交额（元）
    net_buy_ratio: Optional[float] = None  # 净买额占总成交比（%）
    total_amount_ratio: Optional[float] = None  # 成交额占总成交比（%）
    turnover_rate: Optional[float] = None  # 换手率（%）
    float_market_cap: Optional[float] = None  # 流通市值（元）
    list_reason: Optional[str] = None  # 上榜原因
    after_1d_change_pct: Optional[float] = None  # 上榜后 1 日涨跌幅（%）
    after_2d_change_pct: Optional[float] = None  # 上榜后 2 日涨跌幅（%）
    after_5d_change_pct: Optional[float] = None  # 上榜后 5 日涨跌幅（%）
    after_10d_change_pct: Optional[float] = None  # 上榜后 10 日涨跌幅（%）


@dataclass
class StockLhbStockStatisticEm:
    """东方财富 - 个股上榜统计数据"""
    serial_number: Optional[int] = None  # 序号
    code: str = ""  # 代码
    name: str = ""  # 名称
    recent_list_date: Optional[str] = None  # 最近上榜日
    close_price: Optional[float] = None  # 收盘价
    change_pct: Optional[float] = None  # 涨跌幅
    list_count: Optional[int] = None  # 上榜次数
    net_buy_amount: Optional[float] = None  # 龙虎榜净买额
    buy_amount: Optional[float] = None  # 龙虎榜买入额
    sell_amount: Optional[float] = None  # 龙虎榜卖出额
    total_amount: Optional[float] = None  # 龙虎榜总成交额
    buyer_institution_count: Optional[int] = None  # 买方机构次数
    seller_institution_count: Optional[int] = None  # 卖方机构次数
    institution_net_buy_amount: Optional[float] = None  # 机构买入净额
    institution_buy_amount: Optional[float] = None  # 机构买入总额
    institution_sell_amount: Optional[float] = None  # 机构卖出总额
    change_pct_1m: Optional[float] = None  # 近 1 个月涨跌幅
    change_pct_3m: Optional[float] = None  # 近 3 个月涨跌幅
    change_pct_6m: Optional[float] = None  # 近 6 个月涨跌幅
    change_pct_1y: Optional[float] = None  # 近 1 年涨跌幅


@dataclass
class StockInstituteRecommend:
    """新浪财经 - 机构推荐池数据"""
    code: str = ""  # 股票代码
    name: str = ""  # 股票名称
    rating: Optional[str] = None  # 最新评级
    target_price: Optional[float] = None  # 目标价
    rating_date: Optional[str] = None  # 评级日期
    composite_rating: Optional[str] = None  # 综合评级
    avg_change_pct: Optional[float] = None  # 平均涨幅（%）
    industry: Optional[str] = None  # 行业


@dataclass
class StockInstituteRecommendDetail:
    """新浪财经 - 股票评级记录数据"""
    code: str = ""  # 股票代码
    name: str = ""  # 股票名称
    target_price: Optional[float] = None  # 目标价
    rating: Optional[str] = None  # 最新评级
    institution: Optional[str] = None  # 评级机构
    analyst: Optional[str] = None  # 分析师
    industry: Optional[str] = None  # 行业
    rating_date: Optional[str] = None  # 评级日期


@dataclass
class StockRankForecastCninfo:
    """巨潮资讯 - 投资评级数据"""
    sec_code: str = ""  # 证券代码
    sec_name: str = ""  # 证券简称
    publish_date: Optional[str] = None  # 发布日期
    institution_name: Optional[str] = None  # 研究机构简称
    researcher_name: Optional[str] = None  # 研究员名称
    rating: Optional[str] = None  # 投资评级
    is_first_rating: Optional[str] = None  # 是否首次评级
    rating_change: Optional[str] = None  # 评级变化
    prev_rating: Optional[str] = None  # 前一次投资评级
    target_price_lower: Optional[float] = None  # 目标价格 - 下限
    target_price_upper: Optional[float] = None  # 目标价格 - 上限


@dataclass
class LimitUpPool:
    """涨停股池条目"""
    code: str
    name: str
    change_pct: float
    latest_price: float
    turnover_rate: float
    limit_up_count: int  # 连板数
    first_limit_time: str  # 首次涨停时间
    last_limit_time: str  # 最后涨停时间
    seal_amount: float  # 封板资金（万元）
    industry: Optional[str] = None  # 所属行业
    open_count: Optional[int] = None  # 开板次数
    seal_ratio: Optional[float] = None  # 封成比（封单量/成交量）


@dataclass
class LimitDownStock:
    """跌停股"""
    code: str
    name: str
    change_pct: float
    latest_price: float
    continuous_limit_down: int  # 连续跌停天数
    open_count: int  # 开板次数
    turnover_rate: Optional[float] = None  # 换手率
    seal_amount: Optional[float] = None  # 封单金额（万元）
    industry: Optional[str] = None  # 所属行业


@dataclass
class BrokenLimitStock:
    """炸板股（曾涨停但未封住）"""
    code: str
    name: str
    change_pct: float
    latest_price: float
    highest_price: float  # 最高价（涨停价）
    turnover_rate: Optional[float] = None  # 换手率
    industry: Optional[str] = None  # 所属行业
    limit_time: Optional[str] = None  # 涨停时间


@dataclass
class HighLowStatistics:
    """创新高/新低统计"""
    date: str
    index_close: float  # 大盘收盘点位
    high_20: int  # 创 20 日新高
    low_20: int  # 创 20 日新低
    high_60: int  # 创 60 日新高
    low_60: int  # 创 60 日新低
    high_120: int  # 创 120 日新高
    low_120: int  # 创 120 日新低


@dataclass
class LHBEntry:
    """龙虎榜条目"""
    code: str
    name: str
    trade_date: str
    close_price: float
    change_pct: float
    turnover_rate: float
    total_turnover: float  # 总成交额（万元）
    net_buy: float  # 净买入（万元）
    buy_amount: float  # 买入总额（万元）
    sell_amount: float  # 卖出总额（万元）
    reason: Optional[str] = None  # 上榜原因
    buyer_seats: Optional[int] = None  # 买方席位数
    seller_seats: Optional[int] = None  # 卖方席位数


@dataclass
class LHBDetail:
    """龙虎榜明细（买卖席位）"""
    code: str
    name: str
    trade_date: str
    rank: int  # 排名（1-5）
    side: str  # 'buy' or 'sell'
    broker_name: str  # 营业部名称
    amount: float  # 金额（万元）
    ratio: Optional[float] = None  # 占比（%）


@dataclass
class InstitutionalTrading:
    """机构买卖统计"""
    code: str
    name: str
    trade_date: str
    institutional_buy: float  # 机构买入（万元）
    institutional_sell: float  # 机构卖出（万元）
    institutional_net: float  # 机构净买（万元）
    institutional_buy_seats: int  # 机构买入席位数
    institutional_sell_seats: int  # 机构卖出席位数


@dataclass
class FinancialIndicator:
    """财务分析主要指标"""
    code: str
    report_date: str
    eps: Optional[float] = None  # 每股收益
    roe: Optional[float] = None  # 净资产收益率
    roa: Optional[float] = None  # 总资产收益率
    gross_margin: Optional[float] = None  # 销售毛利率
    net_margin: Optional[float] = None  # 销售净利率
    debt_ratio: Optional[float] = None  # 资产负债率
    current_ratio: Optional[float] = None  # 流动比率
    quick_ratio: Optional[float] = None  # 速动比率
    inventory_turnover: Optional[float] = None  # 存货周转率
    receivables_turnover: Optional[float] = None  # 应收账款周转率


@dataclass
class HistoricalDividend:
    """历史分红数据"""
    code: str
    announce_date: str
    record_date: Optional[str] = None
    ex_dividend_date: Optional[str] = None
    cash_dividend: Optional[float] = None  # 每股派现（税前）
    bonus_shares: Optional[float] = None  # 每股送股
    capital_reserve_transfer: Optional[float] = None  # 每股转增
    total_dividend: Optional[float] = None  # 分红总额（万元）


@dataclass
class RestrictedReleaseDetail:
    """限售解禁详情"""
    code: str
    unlock_date: str
    unlock_quantity: float  # 解禁数量（万股）
    unlock_ratio: float  # 解禁比例（%）
    unlock_value: Optional[float] = None  # 解禁市值（万元）
    holder_name: Optional[str] = None  # 解禁股东
    unlock_type: Optional[str] = None  # 解禁类型
    sale_restriction_date: Optional[str] = None  # 减持起始日


@dataclass
class StockChanges:
    """盘口异动数据"""
    code: str
    name: str
    change_type: str  # 异动类型（快速拉升、大幅下跌等）
    change_time: str  # 异动时间
    price: float  # 当前价
    change_pct: float  # 涨跌幅
    volume_ratio: Optional[float] = None  # 量比
    turnover_rate: Optional[float] = None  # 换手率
    reason: Optional[str] = None  # 异动原因


class BaseDataAdapter(ABC):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._is_initialized = False
    
    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        pass
    
    @abstractmethod
    async def close(self) -> None:
        pass
    
    # ========== 上下文管理器支持 ==========
    
    async def __aenter__(self) -> 'BaseDataAdapter':
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """异步上下文管理器出口"""
        await self.close()
    
    def __enter__(self) -> 'BaseDataAdapter':
        """同步上下文管理器入口"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        if loop.is_running():
            import nest_asyncio
            nest_asyncio.apply()
        
        loop.run_until_complete(self.initialize())
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """同步上下文管理器出口"""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(self.close())
    
    @abstractmethod
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        pass
    
    @abstractmethod
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        pass
    
    @abstractmethod
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        period: str = "daily"
    ) -> List[KLineData]:
        """获取 K 线数据（支持多种周期）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权方式（qfq/hfq/no）
            period: K 线周期，可选：
                - '1m': 1 分钟
                - '5m': 5 分钟
                - '15m': 15 分钟
                - '30m': 30 分钟
                - '60m': 60 分钟
                - 'daily': 日线
                - 'weekly': 周线
                - 'monthly': 月线
        """
        pass
    
    @abstractmethod
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        pass
    
    @abstractmethod
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        pass
    
    @abstractmethod
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        pass
    
    @abstractmethod
    async def get_sector_components(self, sector_code: str) -> List[str]:
        pass
    
    @abstractmethod
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        pass
    
    @abstractmethod
    async def get_daily_billboard(self, trade_date: Optional[str] = None) -> List[BillboardEntry]:
        pass
    
    @abstractmethod
    async def get_belong_board(self, code: str) -> List[BoardInfo]:
        pass
    
    @abstractmethod
    async def get_members(self, index_code: str) -> List[IndexComponent]:
        """获取指数成分股
        
        Args:
            index_code: 指数代码或指数名称
        
        Returns:
            指数成分股列表
        """
        pass
    
    @abstractmethod
    async def get_today_bill(self, trade_date: Optional[str] = None) -> List[CapitalFlowItem]:
        pass
    
    @abstractmethod
    async def get_history_bill(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[CapitalFlowItem]:
        pass
    
    @abstractmethod
    async def get_top10_stock_holder_info(self, code: str) -> List[ShareholderInfo]:
        pass
    
    @abstractmethod
    async def get_market_realtime_quotes(self, market_types: Optional[List[str]] = None) -> List[MarketQuote]:
        pass
    
    @abstractmethod
    async def get_financial_performance(
        self,
        code: str,
        report_date: Optional[str] = None,
        report_type: str = "quarterly"
    ) -> List[FinancialPerformance]:
        """获取财务业绩数据
        
        Args:
            code: 股票代码
            report_date: 报告日期，格式 'YYYY-MM-DD'
                - None: 获取最新季报
                - '2024-03-31': 获取 2024 年一季报
                - '2023-12-31': 获取 2023 年年报
            report_type: 报告类型
        
        Returns:
            财务业绩数据列表
        """
        pass
    
    def normalize_code(self, code: str) -> str:
        return code.strip().upper()
    
    def format_date(self, date: str) -> str:
        if len(date) == 8:
            return f"{date[:4]}-{date[4:6]}-{date[6:8]}"
        return date
    
    def kline_to_dataframe(self, klines: List[KLineData]) -> pd.DataFrame:
        if not klines:
            return pd.DataFrame()
        
        data = [
            {
                "code": k.code,
                "date": k.date,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "volume": k.volume,
                "amount": k.amount,
                "turnover_rate": k.turnover_rate
            }
            for k in klines
        ]
        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values("date").reset_index(drop=True)
        return df
    
    # ========== 批量接口基础方法（默认实现，子类可覆盖） ==========
    
    async def get_kline_batch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        adjust: str = "qfq",
        batch_size: int = 10,
        max_concurrent: int = 3
    ) -> Dict[str, List[KLineData]]:
        """批量获取 K 线数据（默认实现，子类可覆盖）
        
        Args:
            codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权方式
            batch_size: 每批次处理的股票数量
            max_concurrent: 最大并发数
            
        Returns:
            K 线数据字典 {code: [KLineData]}
        """
        from asyncio import Semaphore
        
        semaphore = Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(code: str) -> tuple[str, List[KLineData]]:
            async with semaphore:
                try:
                    klines = await self.get_kline(code, start_date, end_date, adjust)
                    return (code, klines)
                except Exception as e:
                    logger.error(f"批量获取 K 线失败 {code}: {e}")
                    return (code, [])
        
        # 分批处理
        all_results = {}
        for i in range(0, len(codes), batch_size):
            batch = codes[i:i + batch_size]
            tasks = [fetch_with_semaphore(code) for code in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    continue
                code, klines = result
                if klines:
                    all_results[code] = klines
            
            # 批次间延迟，避免触发限流
            if i + batch_size < len(codes):
                await asyncio.sleep(1.0)
        
        return all_results
    
    async def get_stock_info_batch(
        self,
        codes: List[str],
        batch_size: int = 20,
        max_concurrent: int = 5
    ) -> Dict[str, StockBasicInfo]:
        """批量获取股票基本信息（默认实现，子类可覆盖）
        
        Args:
            codes: 股票代码列表
            batch_size: 每批次处理的股票数量
            max_concurrent: 最大并发数
            
        Returns:
            股票信息字典 {code: StockBasicInfo}
        """
        from asyncio import Semaphore
        
        semaphore = Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(code: str) -> tuple[str, Optional[StockBasicInfo]]:
            async with semaphore:
                try:
                    info = await self.get_stock_info(code)
                    return (code, info)
                except Exception as e:
                    logger.error(f"批量获取股票信息失败 {code}: {e}")
                    return (code, None)
        
        # 分批处理
        all_results = {}
        for i in range(0, len(codes), batch_size):
            batch = codes[i:i + batch_size]
            tasks = [fetch_with_semaphore(code) for code in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    continue
                code, info = result
                if info:
                    all_results[code] = info
            
            # 批次间延迟
            if i + batch_size < len(codes):
                await asyncio.sleep(0.5)
        
        return all_results
    
    async def get_realtime_quote_batch(
        self,
        codes: List[str],
        batch_size: int = 50,
        max_concurrent: int = 5
    ) -> Dict[str, Dict[str, Any]]:
        """批量获取实时行情（默认实现，子类可覆盖）
        
        Args:
            codes: 股票代码列表
            batch_size: 每批次处理的股票数量
            max_concurrent: 最大并发数
            
        Returns:
            实时行情字典 {code: {}}
        """
        from asyncio import Semaphore
        
        semaphore = Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(code: str) -> tuple[str, Dict[str, Any]]:
            async with semaphore:
                try:
                    quote = await self.get_realtime_quote(code)
                    return (code, quote)
                except Exception as e:
                    logger.error(f"批量获取实时行情失败 {code}: {e}")
                    return (code, {})
        
        # 分批处理
        all_results = {}
        for i in range(0, len(codes), batch_size):
            batch = codes[i:i + batch_size]
            tasks = [fetch_with_semaphore(code) for code in batch]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in results:
                if isinstance(result, Exception):
                    continue
                code, quote = result
                if quote:
                    all_results[code] = quote
            
            # 批次间延迟
            if i + batch_size < len(codes):
                await asyncio.sleep(0.5)
        
        return all_results
