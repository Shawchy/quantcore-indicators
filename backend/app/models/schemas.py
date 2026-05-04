from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    success: bool = True
    code: str = "SUCCESS"
    message: str = "操作成功"
    data: Optional[T] = None

    @staticmethod
    def error(message: str = "操作失败", code: str = "ERROR", data=None) -> "ResponseModel":
        return ResponseModel(success=False, code=code, message=message, data=data)


class PageInfo(BaseModel):
    page: int = 1
    page_size: int = 20
    total: int = 0
    total_pages: int = 0


class PagedResponseModel(BaseModel, Generic[T]):
    success: bool = True
    code: str = "SUCCESS"
    message: str = "操作成功"
    data: Optional[List[T]] = None
    page_info: Optional[PageInfo] = None


class StockBasic(BaseModel):
    code: str
    name: str
    market: str
    industry: Optional[str] = None
    list_date: Optional[str] = None


class KLineData(BaseModel):
    code: str
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = None
    turnover_rate: Optional[float] = None
    pre_close: Optional[float] = None  # 昨日收盘价


class TechnicalIndicator(BaseModel):
    code: str
    date: str
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    rsi6: Optional[float] = None
    rsi12: Optional[float] = None
    rsi24: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None


class MarketMoneyflowData(BaseModel):
    """大盘资金流向数据模型"""
    trade_date: str
    close_sh: Optional[float] = None
    pct_change_sh: Optional[float] = None
    close_sz: Optional[float] = None
    pct_change_sz: Optional[float] = None
    net_amount: Optional[float] = None
    net_amount_rate: Optional[float] = None
    buy_elg_amount: Optional[float] = None
    buy_elg_amount_rate: Optional[float] = None
    buy_lg_amount: Optional[float] = None
    buy_lg_amount_rate: Optional[float] = None
    buy_md_amount: Optional[float] = None
    buy_md_amount_rate: Optional[float] = None
    buy_sm_amount: Optional[float] = None
    buy_sm_amount_rate: Optional[float] = None


class BillboardEntry(BaseModel):
    """龙虎榜单条目"""
    code: str
    name: str
    close_price: Optional[float] = None
    change_pct: Optional[float] = None
    turnover_amount: Optional[float] = None
    net_amount: Optional[float] = None
    buy_amount: Optional[float] = None
    sell_amount: Optional[float] = None
    reason: Optional[str] = None
    trade_date: str


class BoardInfo(BaseModel):
    """股票所属板块信息"""
    code: str
    name: str
    board_type: str
    close_price: Optional[float] = None
    change_pct: Optional[float] = None


class ShareholderInfo(BaseModel):
    """股东信息"""
    code: str
    report_date: str  # 报告期/更新日期
    holder_code: str  # 股东代码
    holder_name: str  # 股东名称
    hold_amount: Optional[float] = None  # 持股数（股）
    hold_ratio: Optional[float] = None  # 持股比例（%）
    change: Optional[str] = None  # 增减描述（不变/新进/数值）
    change_rate: Optional[float] = None  # 变动率（%）


class IndexComponent(BaseModel):
    """指数成分股"""
    code: str
    name: str
    weight: Optional[float] = None
    industry: Optional[str] = None


class CapitalFlowItem(BaseModel):
    """资金流向条目"""
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
    trade_date: str


class MarketQuote(BaseModel):
    """市场实时行情数据"""
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


class FinancialPerformance(BaseModel):
    """财务业绩数据（季度）"""
    code: str
    name: str
    report_date: str
    revenue: Optional[float] = None
    revenue_growth: Optional[float] = None
    revenue_qoq: Optional[float] = None
    net_profit: Optional[float] = None
    net_profit_growth: Optional[float] = None
    net_profit_qoq: Optional[float] = None
    eps: Optional[float] = None
    bvps: Optional[float] = None
    roe: Optional[float] = None
    gross_margin: Optional[float] = None
    cfps: Optional[float] = None


class FundInfo(BaseModel):
    """基金基本信息"""
    code: str                    # 基金代码
    name: str                    # 基金简称
    establish_date: Optional[str] = None  # 成立日期
    change_pct: Optional[float] = None    # 涨跌幅（%）
    net_asset_value: Optional[float] = None  # 最新净值
    fund_company: Optional[str] = None       # 基金公司
    nav_update_date: Optional[str] = None    # 净值更新日期
    description: Optional[str] = None         # 简介


class HotKeyword(BaseModel):
    """个股热门关键词"""
    time: str                    # 时间
    stock_code: str             # 股票代码
    concept_name: str           # 概念名称
    concept_code: str           # 概念代码
    heat: int                   # 热度


class StockChanges(BaseModel):
    """盘口异动数据"""
    time: str                    # 时间
    code: str                   # 代码
    name: str                   # 名称
    board: str                  # 板块
    related_info: str           # 相关信息


class StockBoardChange(BaseModel):
    """板块异动数据"""
    board_name: str                      # 板块名称
    change_pct: Optional[float] = None   # 涨跌幅（%）
    main_net_inflow: Optional[float] = None  # 主力净流入（万元）
    total_changes: Optional[int] = None  # 板块异动总次数
    frequent_stock_code: Optional[str] = None  # 最频繁个股代码
    frequent_stock_name: Optional[str] = None  # 最频繁个股名称
    frequent_type: Optional[str] = None  # 最频繁异动类型
    change_types: Optional[str] = None   # 板块具体异动类型列表（JSON 字符串）


class StockZtPool(BaseModel):
    """涨停股池数据"""
    serial_number: int                    # 序号
    code: str                            # 代码
    name: str                            # 名称
    change_pct: Optional[float] = None   # 涨跌幅（%）
    latest_price: Optional[float] = None  # 最新价
    turnover_amount: Optional[int] = None  # 成交额
    float_market_cap: Optional[float] = None  # 流通市值
    total_market_cap: Optional[float] = None  # 总市值
    turnover_rate: Optional[float] = None  # 换手率（%）
    seal_capital: Optional[int] = None   # 封板资金
    first_seal_time: Optional[str] = None  # 首次封板时间
    last_seal_time: Optional[str] = None   # 最后封板时间
    open_count: Optional[int] = None     # 炸板次数
    zt_statistics: Optional[str] = None  # 涨停统计
    continuous_count: Optional[int] = None  # 连板数
    industry: Optional[str] = None       # 所属行业


class StockZtPoolPrevious(BaseModel):
    """昨日涨停股池数据"""
    serial_number: int                    # 序号
    code: str                            # 代码
    name: str                            # 名称
    change_pct: Optional[float] = None   # 涨跌幅（%）
    latest_price: Optional[float] = None  # 最新价
    limit_up_price: Optional[float] = None  # 涨停价
    turnover_amount: Optional[int] = None  # 成交额
    float_market_cap: Optional[float] = None  # 流通市值
    total_market_cap: Optional[float] = None  # 总市值
    turnover_rate: Optional[float] = None  # 换手率（%）
    speed: Optional[float] = None        # 涨速（%）
    amplitude: Optional[float] = None    # 振幅（%）
    yesterday_seal_time: Optional[str] = None  # 昨日封板时间
    yesterday_continuous_count: Optional[int] = None  # 昨日连板数
    zt_statistics: Optional[str] = None  # 涨停统计
    industry: Optional[str] = None       # 所属行业


class StockZtPoolStrong(BaseModel):
    """强势股池数据"""
    serial_number: int                    # 序号
    code: str                            # 代码
    name: str                            # 名称
    change_pct: Optional[float] = None   # 涨跌幅（%）
    latest_price: Optional[float] = None  # 最新价
    limit_up_price: Optional[float] = None  # 涨停价
    turnover_amount: Optional[int] = None  # 成交额
    float_market_cap: Optional[float] = None  # 流通市值
    total_market_cap: Optional[float] = None  # 总市值
    turnover_rate: Optional[float] = None  # 换手率（%）
    speed: Optional[float] = None        # 涨速（%）
    is_new_high: Optional[str] = None    # 是否新高
    volume_ratio: Optional[float] = None  # 量比
    zt_statistics: Optional[str] = None  # 涨停统计
    reason: Optional[str] = None         # 入选理由
    industry: Optional[str] = None       # 所属行业


class StockZtPoolZbgc(BaseModel):
    """炸板股池数据"""
    serial_number: int                    # 序号
    code: str                            # 代码
    name: str                            # 名称
    change_pct: Optional[float] = None   # 涨跌幅（%）
    latest_price: Optional[float] = None  # 最新价
    limit_up_price: Optional[float] = None  # 涨停价
    turnover_amount: Optional[int] = None  # 成交额
    float_market_cap: Optional[float] = None  # 流通市值
    total_market_cap: Optional[float] = None  # 总市值
    turnover_rate: Optional[float] = None  # 换手率（%）
    speed: Optional[int] = None          # 涨速
    first_seal_time: Optional[str] = None  # 首次封板时间
    open_count: Optional[int] = None     # 炸板次数
    zt_statistics: Optional[str] = None  # 涨停统计
    amplitude: Optional[float] = None    # 振幅
    industry: Optional[str] = None       # 所属行业


class StockZtPoolDtgc(BaseModel):
    """跌停股池数据"""
    serial_number: int                    # 序号
    code: str                            # 代码
    name: str                            # 名称
    change_pct: Optional[float] = None   # 涨跌幅（%）
    latest_price: Optional[float] = None  # 最新价
    turnover_amount: Optional[int] = None  # 成交额
    float_market_cap: Optional[float] = None  # 流通市值
    total_market_cap: Optional[float] = None  # 总市值
    pe_ratio_dynamic: Optional[float] = None  # 动态市盈率
    turnover_rate: Optional[float] = None  # 换手率（%）
    seal_capital: Optional[int] = None   # 封单资金
    last_seal_time: Optional[str] = None  # 最后封板时间
    on_board_amount: Optional[int] = None  # 板上成交额
    continuous_limit_down: Optional[int] = None  # 连续跌停
    open_count: Optional[int] = None     # 开板次数
    industry: Optional[str] = None       # 所属行业


class MarketActivity(BaseModel):
    """赚钱效应分析数据"""
    item: str                    # 指标名称
    value: str                   # 指标值


class FinancialNews(BaseModel):
    """财经新闻数据"""
    title: str                   # 标题
    summary: Optional[str] = None  # 摘要
    publish_time: Optional[str] = None  # 发布时间
    link: Optional[str] = None    # 链接


class GlobalNews(BaseModel):
    """全球财经快讯数据"""
    title: str                   # 标题
    summary: Optional[str] = None  # 摘要
    publish_time: Optional[str] = None  # 发布时间
    link: Optional[str] = None    # 链接


class GlobalNewsSina(BaseModel):
    """新浪财经快讯数据"""
    time: str                    # 时间
    content: str                 # 内容


class GlobalNewsFutu(BaseModel):
    """富途牛牛快讯数据"""
    title: str                   # 标题
    content: Optional[str] = None  # 内容
    publish_time: Optional[str] = None  # 发布时间
    link: Optional[str] = None    # 链接


class StockRankCxg(BaseModel):
    """创新高股票数据"""
    serial_number: int                    # 序号
    code: str                            # 股票代码
    name: str                            # 股票简称
    change_pct: Optional[float] = None   # 涨跌幅（%）
    turnover_rate: Optional[float] = None  # 换手率（%）
    latest_price: Optional[float] = None  # 最新价（元）
    previous_high: Optional[float] = None  # 前期高点
    previous_high_date: Optional[str] = None  # 前期高点日期


class StockRankCxd(BaseModel):
    """创新低股票数据"""
    serial_number: int                    # 序号
    code: str                            # 股票代码
    name: str                            # 股票简称
    change_pct: Optional[float] = None   # 涨跌幅（%）
    turnover_rate: Optional[float] = None  # 换手率（%）
    latest_price: Optional[float] = None  # 最新价（元）
    previous_low: Optional[float] = None  # 前期低点
    previous_low_date: Optional[str] = None  # 前期低点日期


class StockRankLxsz(BaseModel):
    """连续上涨股票数据"""
    serial_number: int                    # 序号
    code: str                            # 股票代码
    name: str                            # 股票简称
    close_price: Optional[float] = None  # 收盘价（元）
    high_price: Optional[float] = None   # 最高价（元）
    low_price: Optional[float] = None    # 最低价（元）
    continuous_days: Optional[int] = None  # 连涨天数
    continuous_change_pct: Optional[float] = None  # 连续涨跌幅（%）
    total_turnover_rate: Optional[float] = None  # 累计换手率（%）
    industry: Optional[str] = None       # 所属行业


class StockRankLxxd(BaseModel):
    """连续下跌股票数据"""
    serial_number: int                    # 序号
    code: str                            # 股票代码
    name: str                            # 股票简称
    close_price: Optional[float] = None  # 收盘价（元）
    high_price: Optional[float] = None   # 最高价（元）
    low_price: Optional[float] = None    # 最低价（元）
    continuous_days: Optional[int] = None  # 连跌天数
    continuous_change_pct: Optional[float] = None  # 连续涨跌幅（%）
    total_turnover_rate: Optional[float] = None  # 累计换手率（%）
    industry: Optional[str] = None       # 所属行业


class StockRankCxfl(BaseModel):
    """持续放量股票数据"""
    serial_number: int                    # 序号
    code: str                            # 股票代码
    name: str                            # 股票简称
    change_pct: Optional[float] = None   # 涨跌幅（%）
    latest_price: Optional[float] = None  # 最新价（元）
    volume: Optional[str] = None         # 成交量（股）
    base_volume: Optional[str] = None    # 基准日成交量（股）
    continuous_days: Optional[int] = None  # 放量天数
    stage_change_pct: Optional[float] = None  # 阶段涨跌幅（%）
    industry: Optional[str] = None       # 所属行业


class StockRankCxsl(BaseModel):
    """持续缩量股票数据"""
    serial_number: int                    # 序号
    code: str                            # 股票代码
    name: str                            # 股票简称
    change_pct: Optional[float] = None   # 涨跌幅（%）
    latest_price: Optional[float] = None  # 最新价（元）
    volume: Optional[str] = None         # 成交量（股）
    base_volume: Optional[str] = None    # 基准日成交量（股）
    continuous_days: Optional[int] = None  # 缩量天数
    stage_change_pct: Optional[float] = None  # 阶段涨跌幅（%）
    industry: Optional[str] = None       # 所属行业


class StockRankXstp(BaseModel):
    """向上突破股票数据"""
    serial_number: int                    # 序号
    code: str                            # 股票代码
    name: str                            # 股票简称
    latest_price: Optional[float] = None  # 最新价（元）
    turnover_amount: Optional[str] = None  # 成交额（元）
    volume: Optional[str] = None         # 成交量（股）
    change_pct: Optional[float] = None   # 涨跌幅（%）
    turnover_rate: Optional[float] = None  # 换手率（%）


class StockRankXxtp(BaseModel):
    """向下突破股票数据"""
    serial_number: int                    # 序号
    code: str                            # 股票代码
    name: str                            # 股票简称
    latest_price: Optional[float] = None  # 最新价（元）
    turnover_amount: Optional[str] = None  # 成交额（元）
    volume: Optional[str] = None         # 成交量（股）
    change_pct: Optional[float] = None   # 涨跌幅（%）
    turnover_rate: Optional[float] = None  # 换手率（%）


class StockRankLjqs(BaseModel):
    """量价齐升股票数据"""
    serial_number: int                    # 序号
    code: str                            # 股票代码
    name: str                            # 股票简称
    latest_price: Optional[float] = None  # 最新价（元）
    continuous_days: Optional[int] = None  # 量价齐升天数
    stage_change_pct: Optional[float] = None  # 阶段涨幅（%）
    total_turnover_rate: Optional[float] = None  # 累计换手率（%）
    industry: Optional[str] = None       # 所属行业


class StockRankLjqd(BaseModel):
    """量价齐跌股票数据"""
    serial_number: int                    # 序号
    code: str                            # 股票代码
    name: str                            # 股票简称
    latest_price: Optional[float] = None  # 最新价（元）
    continuous_days: Optional[int] = None  # 量价齐跌天数
    stage_change_pct: Optional[float] = None  # 阶段涨幅（%）
    total_turnover_rate: Optional[float] = None  # 累计换手率（%）
    industry: Optional[str] = None       # 所属行业


class StockHotFollow(BaseModel):
    """雪球关注排行榜数据"""
    code: str                    # 股票代码
    name: str                    # 股票简称
    follow: Optional[float] = None  # 关注数
    latest_price: Optional[float] = None  # 最新价（元）


class StockHotTweet(BaseModel):
    """雪球讨论排行榜数据"""
    code: str                    # 股票代码
    name: str                    # 股票简称
    follow: Optional[float] = None  # 关注数（讨论数）
    latest_price: Optional[float] = None  # 最新价（元）


class StockHotDeal(BaseModel):
    """雪球交易排行榜数据"""
    code: str                    # 股票代码
    name: str                    # 股票简称
    follow: Optional[float] = None  # 关注数（交易数）
    latest_price: Optional[float] = None  # 最新价（元）


class StockHotRankEm(BaseModel):
    """东方财富人气榜数据"""
    current_rank: int                    # 当前排名
    code: str                    # 代码
    name: str                    # 股票名称
    latest_price: Optional[float] = None  # 最新价
    change: Optional[float] = None  # 涨跌额
    change_pct: Optional[float] = None  # 涨跌幅（%）


class StockHotUpEm(BaseModel):
    """东方财富飙升榜数据"""
    rank_change: int                    # 排名较昨日变动
    current_rank: int                    # 当前排名
    code: str                    # 代码
    name: str                    # 股票名称
    latest_price: Optional[float] = None  # 最新价
    change: Optional[float] = None  # 涨跌额
    change_pct: Optional[float] = None  # 涨跌幅（%）


class StockIndexSpot(BaseModel):
    """股票指数实时行情数据"""
    serial_number: int                    # 序号
    code: str                    # 代码
    name: str                    # 名称
    latest_price: Optional[float] = None  # 最新价
    change: Optional[float] = None  # 涨跌额
    change_pct: Optional[float] = None  # 涨跌幅（%）
    volume: Optional[float] = None  # 成交量
    amount: Optional[float] = None  # 成交额
    amplitude: Optional[float] = None  # 振幅（%）
    high: Optional[float] = None  # 最高
    low: Optional[float] = None  # 最低
    open: Optional[float] = None  # 今开
    pre_close: Optional[float] = None  # 昨收
    volume_ratio: Optional[float] = None  # 量比


class StockIndexDaily(BaseModel):
    """股票指数历史行情数据（日频）"""
    date: str                    # 日期
    open: Optional[float] = None  # 开盘价
    close: Optional[float] = None  # 收盘价
    high: Optional[float] = None  # 最高价
    low: Optional[float] = None  # 最低价
    volume: Optional[int] = None  # 成交量
    amount: Optional[float] = None  # 成交额


class StockIndexHist(BaseModel):
    """股票指数历史行情数据（通用）"""
    date: str                    # 交易日
    open: Optional[float] = None  # 开盘价
    close: Optional[float] = None  # 收盘价
    high: Optional[float] = None  # 最高价
    low: Optional[float] = None  # 最低价
    volume: Optional[int] = None  # 成交量（手）
    amount: Optional[float] = None  # 成交额（元）
    amplitude: Optional[float] = None  # 振幅（%）
    change_pct: Optional[float] = None  # 涨跌幅（%）
    change: Optional[float] = None  # 涨跌额（元）
    turnover_rate: Optional[float] = None  # 换手率（%）


class StockIndexHistMin(BaseModel):
    """股票指数分时行情数据"""
    time: str                    # 时间
    open: Optional[float] = None  # 开盘价
    close: Optional[float] = None  # 收盘价
    high: Optional[float] = None  # 最高价
    low: Optional[float] = None  # 最低价
    volume: Optional[int] = None  # 成交量（手）
    amount: Optional[float] = None  # 成交额（元）
    avg_price: Optional[float] = None  # 均价


class SWIndexFirst(BaseModel):
    """申万一级行业信息数据"""
    industry_code: str                    # 行业代码
    industry_name: str                    # 行业名称
    component_count: Optional[int] = None  # 成份个数
    static_pe: Optional[float] = None  # 静态市盈率
    pe_ttm: Optional[float] = None  # TTM(滚动) 市盈率
    pb: Optional[float] = None  # 市净率
    static_dividend_yield: Optional[float] = None  # 静态股息率


class SWIndexSecond(BaseModel):
    """申万二级行业信息数据"""
    industry_code: str                    # 行业代码
    industry_name: str                    # 行业名称
    parent_industry: str                    # 上级行业
    component_count: Optional[int] = None  # 成份个数
    static_pe: Optional[float] = None  # 静态市盈率
    pe_ttm: Optional[float] = None  # TTM(滚动) 市盈率
    pb: Optional[float] = None  # 市净率
    static_dividend_yield: Optional[float] = None  # 静态股息率


class SWIndexThird(BaseModel):
    """申万三级行业信息数据"""
    industry_code: str                    # 行业代码
    industry_name: str                    # 行业名称
    parent_industry: str                    # 上级行业
    component_count: Optional[int] = None  # 成份个数
    static_pe: Optional[float] = None  # 静态市盈率
    pe_ttm: Optional[float] = None  # TTM(滚动) 市盈率
    pb: Optional[float] = None  # 市净率
    static_dividend_yield: Optional[float] = None  # 静态股息率


class SWIndexThirdCons(BaseModel):
    """申万三级行业成份数据"""
    serial_number: int                    # 序号
    stock_code: str                    # 股票代码
    stock_name: str                    # 股票简称
    include_date: str                    # 纳入时间
    sw_level1: str                    # 申万 1 级
    sw_level2: str                    # 申万 2 级
    sw_level3: str                    # 申万 3 级
    price: Optional[float] = None  # 价格
    pe: Optional[float] = None  # 市盈率
    pe_ttm: Optional[float] = None  # 市盈率 ttm
    pb: Optional[float] = None  # 市净率
    dividend_yield: Optional[float] = None  # 股息率（%）
    market_cap: Optional[float] = None  # 市值（亿元）
    net_profit_yoy_0930: Optional[float] = None  # 归母净利润同比增长 (09-30)（%）
    net_profit_yoy_0630: Optional[float] = None  # 归母净利润同比增长 (06-30)（%）
    revenue_yoy_0930: Optional[float] = None  # 营业收入同比增长 (09-30)（%）
    revenue_yoy_0630: Optional[float] = None  # 营业收入同比增长 (06-30)（%）
