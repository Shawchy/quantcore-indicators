"""
统一数据模型定义

提供跨数据源的标准化数据模型，确保数据一致性
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class DataSourceType(str, Enum):
    """数据源类型"""
    EFINANCE = "efinance"
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    TICKFLOW = "tickflow"


class AdjustType(str, Enum):
    """复权类型"""
    QFQ = "qfq"      # 前复权
    HFQ = "hfq"      # 后复权
    NONE = "none"    # 不复权


class MarketType(str, Enum):
    """市场类型"""
    SH = "SH"  # 上海
    SZ = "SZ"  # 深圳
    BJ = "BJ"  # 北京


class UnifiedKLine(BaseModel):
    """统一 K 线数据模型"""
    # 基础信息
    code: str = Field(..., description="股票代码（6 位数字）")
    date: str = Field(..., description="日期（YYYY-MM-DD）")
    time: Optional[str] = Field(None, description="时间（HH:MM:SS）")
    
    # 行情数据
    open: float = Field(..., ge=0, description="开盘价")
    high: float = Field(..., ge=0, description="最高价")
    low: float = Field(..., ge=0, description="最低价")
    close: float = Field(..., ge=0, description="收盘价")
    pre_close: Optional[float] = Field(None, ge=0, description="昨收价")
    
    # 成交量和成交额
    volume: float = Field(..., ge=0, description="成交量（股）")
    amount: Optional[float] = Field(None, ge=0, description="成交额（元）")
    turnover_rate: Optional[float] = Field(None, ge=0, description="换手率（%）")
    
    # 复权信息
    adjust_type: AdjustType = Field(AdjustType.QFQ, description="复权类型")
    adjust_factor: Optional[float] = Field(1.0, description="复权因子")
    
    # 数据来源
    source: DataSourceType = Field(..., description="数据源")
    source_time: Optional[str] = Field(None, description="数据源时间戳")
    
    # 质量评分
    quality_score: float = Field(1.0, ge=0, le=1, description="数据质量评分")
    
    # 元数据
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: Optional[str] = None
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """验证股票代码格式"""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("股票代码必须是 6 位数字")
        return v
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v):
        """验证日期格式"""
        try:
            datetime.strptime(v, "%Y-%m-%d")
            return v
        except ValueError:
            raise ValueError("日期格式必须是 YYYY-MM-DD")
    
    @field_validator('high', 'low')
    @classmethod
    def validate_price_range(cls, v, info):
        """验证价格合理性"""
        # Pydantic V2 中使用 info.data 访问其他字段
        data = info.data
        if 'open' in data and v < data['open'] * 0.9:
            # 价格波动超过 10% 视为异常（A 股涨跌停限制）
            raise ValueError("价格波动异常")
        return v


class UnifiedStockInfo(BaseModel):
    """统一股票基本信息模型"""
    code: str = Field(..., description="股票代码（6 位数字）")
    name: str = Field(..., description="股票名称")
    market: MarketType = Field(..., description="市场类型（SH/SZ/BJ）")
    industry: Optional[str] = Field(None, description="所属行业")
    area: Optional[str] = Field(None, description="所属地区")
    list_date: Optional[str] = Field(None, description="上市日期")
    
    # 股本信息
    total_shares: float = Field(..., ge=0, description="总股本（股）")
    float_shares: float = Field(..., ge=0, description="流通股本（股）")
    
    # 市值信息
    total_market_cap: float = Field(..., ge=0, description="总市值（元）")
    float_market_cap: float = Field(..., ge=0, description="流通市值（元）")
    
    # 估值指标
    pe_ratio: Optional[float] = Field(None, description="市盈率（TTM）")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    dividend_yield: Optional[float] = Field(None, description="股息率（%）")
    
    # 数据来源
    source: DataSourceType = Field(..., description="数据源")
    source_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # 质量评分
    quality_score: float = Field(1.0, ge=0, le=1, description="数据质量评分")
    
    @field_validator('code')
    @classmethod
    def validate_code(cls, v):
        """验证股票代码格式"""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("股票代码必须是 6 位数字")
        return v


class UnifiedRealtimeQuote(BaseModel):
    """统一实时行情模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    
    # 价格信息
    price: float = Field(..., ge=0, description="最新价")
    change: float = Field(..., description="涨跌额")
    change_pct: float = Field(..., description="涨跌幅（%）")
    
    # 价格区间
    high: float = Field(..., ge=0, description="最高价")
    low: float = Field(..., ge=0, description="最低价")
    open: float = Field(..., ge=0, description="开盘价")
    pre_close: float = Field(..., ge=0, description="昨收价")
    
    # 成交信息
    volume: float = Field(..., ge=0, description="成交量（股）")
    amount: float = Field(..., ge=0, description="成交额（元）")
    
    # 买卖盘
    bid1: Optional[float] = Field(None, description="买一价")
    bid1_volume: Optional[float] = Field(None, description="买一量")
    ask1: Optional[float] = Field(None, description="卖一价")
    ask1_volume: Optional[float] = Field(None, description="卖一量")
    
    # 数据来源
    source: DataSourceType = Field(..., description="数据源")
    quote_time: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # 质量评分
    quality_score: float = Field(1.0, ge=0, le=1, description="数据质量评分")


class TechnicalIndicator(BaseModel):
    """技术指标数据模型"""
    code: str = Field(..., description="股票代码")
    date: str = Field(..., description="日期")
    
    # 移动平均线
    ma5: Optional[float] = Field(None, description="5 日均线")
    ma10: Optional[float] = Field(None, description="10 日均线")
    ma20: Optional[float] = Field(None, description="20 日均线")
    ma60: Optional[float] = Field(None, description="60 日均线")
    
    # MACD
    macd: Optional[float] = Field(None, description="MACD 值")
    macd_signal: Optional[float] = Field(None, description="MACD 信号线")
    macd_hist: Optional[float] = Field(None, description="MACD 柱状图")
    
    # RSI
    rsi6: Optional[float] = Field(None, description="RSI(6)")
    rsi12: Optional[float] = Field(None, description="RSI(12)")
    rsi24: Optional[float] = Field(None, description="RSI(24)")
    
    # KDJ
    kdj_k: Optional[float] = Field(None, description="KDJ K 值")
    kdj_d: Optional[float] = Field(None, description="KDJ D 值")
    kdj_j: Optional[float] = Field(None, description="KDJ J 值")
    
    # 布林带
    bb_upper: Optional[float] = Field(None, description="布林带上轨")
    bb_middle: Optional[float] = Field(None, description="布林带中轨")
    bb_lower: Optional[float] = Field(None, description="布林带下轨")
    
    # ATR
    atr: Optional[float] = Field(None, description="ATR 指标")
    
    # 元数据
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())


class ChipData(BaseModel):
    """筹码数据模型"""
    code: str = Field(..., description="股票代码")
    date: str = Field(..., description="日期")
    
    # 股东信息
    shareholder_count: Optional[int] = Field(None, description="股东人数")
    avg_shares_per_holder: Optional[float] = Field(None, description="户均持股数")
    total_shares: Optional[float] = Field(None, description="总股本")
    
    # 筹码集中度
    chip_concentration: Optional[float] = Field(None, description="筹码集中度")
    chip_avg_cost: Optional[float] = Field(None, description="筹码平均成本")
    
    # 数据来源
    source: DataSourceType = Field(..., description="数据源")
    source_time: str = Field(default_factory=lambda: datetime.now().isoformat())


class DataQualityReport(BaseModel):
    """数据质量报告"""
    date: str = Field(..., description="报告日期")
    code: str = Field(..., description="股票代码")
    
    # 一致性检查
    total_sources: int = Field(..., description="参与比对的数据源数量")
    consistent_sources: int = Field(..., description="一致的数据源数量")
    consistency_rate: float = Field(..., ge=0, le=1, description="一致性比率")
    
    # 数据完整性
    completeness_rate: float = Field(..., ge=0, le=1, description="数据完整性比率")
    missing_fields: List[str] = Field(default_factory=list, description="缺失字段列表")
    
    # 异常检测
    has_anomalies: bool = Field(False, description="是否存在异常")
    anomaly_details: List[Dict[str, Any]] = Field(default_factory=list, description="异常详情")
    
    # 综合评分
    overall_score: float = Field(..., ge=0, le=1, description="综合质量评分")
    
    # 建议
    recommendations: List[str] = Field(default_factory=list, description="改进建议")


class StockChanges(BaseModel):
    """盘口异动数据模型"""
    time: str = Field(..., description="异动时间")
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    board: str = Field(..., description="所属板块")
    related_info: str = Field(..., description="相关信息")
    change_type: str = Field(..., description="异动类型")


class StockBoardChange(BaseModel):
    """板块异动数据模型"""
    board_name: str = Field(..., description="板块名称")
    change_pct: float = Field(..., description="涨跌幅（%）")
    net_inflow: float = Field(..., description="主力净流入（万元）")
    change_count: int = Field(..., description="板块异动总次数")
    top_stock_code: str = Field(..., description="最频繁个股代码")
    top_stock_name: str = Field(..., description="最频繁个股名称")
    top_stock_type: str = Field(..., description="最频繁个股类型")
    change_types: List[Dict[str, Any]] = Field(default_factory=list, description="异动类型列表")


class StockZtPool(BaseModel):
    """涨停股池数据模型"""
    serial_no: int = Field(..., description="序号")
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    change_pct: float = Field(..., description="涨跌幅（%）")
    latest_price: float = Field(..., description="最新价")
    turnover: float = Field(..., description="成交额")
    float_mv: float = Field(..., description="流通市值")
    total_mv: float = Field(..., description="总市值")
    turnover_rate: float = Field(..., description="换手率（%）")
    seal_fund: float = Field(..., description="封板资金")
    first_seal_time: str = Field(..., description="首次封板时间")
    last_seal_time: str = Field(..., description="最后封板时间")
    open_count: int = Field(..., description="炸板次数")
    zt_stats: str = Field(..., description="涨停统计")
    continuous_count: int = Field(..., description="连板数")
    industry: str = Field(..., description="所属行业")


class MarketChanges(BaseModel):
    """市场异动汇总"""
    timestamp: str = Field(..., description="时间戳")
    total_changes: int = Field(..., description="总异动次数")
    rocket_launch: int = Field(..., description="火箭发射次数")
    fast_rebound: int = Field(..., description="快速反弹次数")
    big_buy: int = Field(..., description="大笔买入次数")
    big_sell: int = Field(..., description="大笔卖出次数")
    limit_up: int = Field(..., description="封涨停板次数")
    limit_down: int = Field(..., description="封跌停板次数")
    high_dive: int = Field(..., description="高台跳水次数")


class StockZtPrevious(BaseModel):
    """昨日涨停股池数据模型"""
    serial_no: int = Field(..., description="序号")
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    change_pct: float = Field(..., description="涨跌幅（%）")
    latest_price: float = Field(..., description="最新价")
    limit_up_price: float = Field(..., description="涨停价")
    turnover: float = Field(..., description="成交额")
    float_mv: float = Field(..., description="流通市值")
    total_mv: float = Field(..., description="总市值")
    turnover_rate: float = Field(..., description="换手率（%）")
    speed: float = Field(..., description="涨速（%）")
    amplitude: float = Field(..., description="振幅（%）")
    yesterday_seal_time: str = Field(..., description="昨日封板时间")
    yesterday_continuous: int = Field(..., description="昨日连板数")
    zt_stats: str = Field(..., description="涨停统计")
    industry: str = Field(..., description="所属行业")


class StockZtStrong(BaseModel):
    """强势股池数据模型"""
    serial_no: int = Field(..., description="序号")
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    change_pct: float = Field(..., description="涨跌幅（%）")
    latest_price: float = Field(..., description="最新价")
    limit_up_price: float = Field(..., description="涨停价")
    turnover: float = Field(..., description="成交额")
    float_mv: float = Field(..., description="流通市值")
    total_mv: float = Field(..., description="总市值")
    turnover_rate: float = Field(..., description="换手率（%）")
    speed: float = Field(..., description="涨速（%）")
    is_new_high: bool = Field(..., description="是否新高")
    volume_ratio: float = Field(..., description="量比")
    zt_stats: str = Field(..., description="涨停统计")
    reason: str = Field(..., description="入选理由")
    industry: str = Field(..., description="所属行业")


class StockZtSubNew(BaseModel):
    """次新股池数据模型"""
    serial_no: int = Field(..., description="序号")
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    change_pct: float = Field(..., description="涨跌幅（%）")
    latest_price: float = Field(..., description="最新价")
    limit_up_price: float = Field(..., description="涨停价")
    turnover: float = Field(..., description="成交额")
    float_mv: float = Field(..., description="流通市值")
    total_mv: float = Field(..., description="总市值")
    turnover_rate: float = Field(..., description="转手率（%）")
    open_days: int = Field(..., description="开板几日")
    open_date: str = Field(..., description="开板日期")
    list_date: str = Field(..., description="上市日期")
    is_new_high: bool = Field(..., description="是否新高")
    zt_stats: str = Field(..., description="涨停统计")
    industry: str = Field(..., description="所属行业")


class DataSourceHealthStatus(BaseModel):
    """数据源健康状态"""
    source: DataSourceType = Field(..., description="数据源")
    status: str = Field(..., description="状态（healthy/degraded/unhealthy/error）")
    response_time: float = Field(..., ge=0, description="响应时间（秒）")
    last_check: str = Field(..., description="最后检查时间")
    error: Optional[str] = Field(None, description="错误信息")
    test_result: str = Field(..., description="测试结果")


class StockComment(BaseModel):
    """千股千评数据模型"""
    serial_no: int = Field(..., description="序号")
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票名称")
    latest_price: float = Field(..., description="最新价")
    change_pct: float = Field(..., description="涨跌幅（%）")
    turnover_rate: float = Field(..., description="换手率（%）")
    pe_ratio: float = Field(..., description="市盈率")
    main_force_cost: float = Field(..., description="主力成本")
    institution_participation: float = Field(..., description="机构参与度（%）")
    comprehensive_score: float = Field(..., description="综合得分")
    rise: int = Field(..., description="上升（正负号）")
    current_rank: int = Field(..., description="目前排名")
    attention_index: float = Field(..., description="关注指数")
    trading_day: str = Field(..., description="交易日")


class StockCommentDetailInstitution(BaseModel):
    """千股千评详情 - 主力控盘 - 机构参与度数据模型"""
    trading_day: str = Field(..., description="交易日")
    institution_participation: float = Field(..., description="机构参与度（%）")


class StockCommentDetailScore(BaseModel):
    """千股千评详情 - 综合评价 - 历史评分数据模型"""
    trading_day: str = Field(..., description="交易日")
    score: float = Field(..., description="评分")


class StockResearchReport(BaseModel):
    """个股研报数据模型"""
    serial_no: int = Field(..., description="序号")
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票简称")
    report_name: str = Field(..., description="报告名称")
    rating: str = Field(..., description="东财评级")
    institution: str = Field(..., description="机构")
    recent_report_count: int = Field(..., description="近一月个股研报数")
    forecast_2024_eps: Optional[float] = Field(None, description="2024 盈利预测 - 收益")
    forecast_2024_pe: Optional[float] = Field(None, description="2024 盈利预测 - 市盈率")
    forecast_2025_eps: Optional[float] = Field(None, description="2025 盈利预测 - 收益")
    forecast_2025_pe: Optional[float] = Field(None, description="2025 盈利预测 - 市盈率")
    forecast_2026_eps: Optional[float] = Field(None, description="2026 盈利预测 - 收益")
    forecast_2026_pe: Optional[float] = Field(None, description="2026 盈利预测 - 市盈率")
    industry: str = Field(..., description="行业")
    report_date: str = Field(..., description="日期")
    report_pdf_url: str = Field(..., description="报告 PDF 链接")


class StockNotice(BaseModel):
    """沪深京 A 股公告数据模型"""
    code: str = Field(..., description="代码")
    name: str = Field(..., description="名称")
    notice_title: str = Field(..., description="公告标题")
    notice_type: str = Field(..., description="公告类型")
    notice_date: str = Field(..., description="公告日期")
    url: str = Field(..., description="网址")


class StockBalanceSheet(BaseModel):
    """资产负债表数据模型（通用）
    
    包含 319 个字段，这里列出主要字段，其他字段使用额外字段存储
    """
    secucode: str = Field(..., description="证券代码")
    security_code: str = Field(..., description="股票代码")
    security_name_abbr: Optional[str] = Field(None, description="证券简称")
    end_date: Optional[str] = Field(None, description="报告期")
    report_date: Optional[str] = Field(None, description="公告日期")
    total_assets: Optional[float] = Field(None, description="资产总计")
    total_liabilities: Optional[float] = Field(None, description="负债合计")
    total_equity: Optional[float] = Field(None, description="所有者权益合计")
    cash_equivalents: Optional[float] = Field(None, description="货币资金")
    accounts_receivable: Optional[float] = Field(None, description="应收账款")
    inventory: Optional[float] = Field(None, description="存货")
    fixed_assets: Optional[float] = Field(None, description="固定资产")
    short_term_borrowings: Optional[float] = Field(None, description="短期借款")
    accounts_payable: Optional[float] = Field(None, description="应付账款")
    long_term_borrowings: Optional[float] = Field(None, description="长期借款")
    retained_earnings: Optional[float] = Field(None, description="未分配利润")
    paid_in_capital: Optional[float] = Field(None, description="实收资本/股本")
    # 其他字段存储在 extra_fields 中
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他财务指标")


class StockProfitSheet(BaseModel):
    """利润表数据模型（通用）
    
    包含 203-204 个字段，这里列出主要字段，其他字段使用额外字段存储
    """
    secucode: str = Field(..., description="证券代码")
    security_code: str = Field(..., description="股票代码")
    security_name_abbr: Optional[str] = Field(None, description="证券简称")
    end_date: Optional[str] = Field(None, description="报告期")
    report_date: Optional[str] = Field(None, description="公告日期")
    total_revenue: Optional[float] = Field(None, description="营业总收入")
    operating_revenue: Optional[float] = Field(None, description="营业收入")
    operating_cost: Optional[float] = Field(None, description="营业成本")
    operating_profit: Optional[float] = Field(None, description="营业利润")
    total_profit: Optional[float] = Field(None, description="利润总额")
    net_profit: Optional[float] = Field(None, description="净利润")
    parent_netprofit: Optional[float] = Field(None, description="归属于母公司所有者的净利润")
    deduct_parent_netprofit: Optional[float] = Field(None, description="扣除非经常性损益后的净利润")
    operating_tax: Optional[float] = Field(None, description="税金及附加")
    sales_expense: Optional[float] = Field(None, description="销售费用")
    admin_expense: Optional[float] = Field(None, description="管理费用")
    rd_expense: Optional[float] = Field(None, description="研发费用")
    finance_expense: Optional[float] = Field(None, description="财务费用")
    other_income: Optional[float] = Field(None, description="其他收益")
    investment_income: Optional[float] = Field(None, description="投资收益")
    non_operating_income: Optional[float] = Field(None, description="营业外收入")
    non_operating_expense: Optional[float] = Field(None, description="营业外支出")
    income_tax: Optional[float] = Field(None, description="所得税费用")
    # 其他字段存储在 extra_fields 中
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他财务指标")


class StockCashFlowSheet(BaseModel):
    """现金流量表数据模型（通用）
    
    包含 252-315 个字段，这里列出主要字段，其他字段使用额外字段存储
    """
    secucode: str = Field(..., description="证券代码")
    security_code: str = Field(..., description="股票代码")
    security_name_abbr: Optional[str] = Field(None, description="证券简称")
    end_date: Optional[str] = Field(None, description="报告期")
    report_date: Optional[str] = Field(None, description="公告日期")
    operating_cash_in: Optional[float] = Field(None, description="经营活动现金流入小计")
    operating_cash_out: Optional[float] = Field(None, description="经营活动现金流出小计")
    operating_net_cash: Optional[float] = Field(None, description="经营活动产生的现金流量净额")
    investing_cash_in: Optional[float] = Field(None, description="投资活动现金流入小计")
    investing_cash_out: Optional[float] = Field(None, description="投资活动现金流出小计")
    investing_net_cash: Optional[float] = Field(None, description="投资活动产生的现金流量净额")
    financing_cash_in: Optional[float] = Field(None, description="筹资活动现金流入小计")
    financing_cash_out: Optional[float] = Field(None, description="筹资活动现金流出小计")
    financing_net_cash: Optional[float] = Field(None, description="筹资活动产生的现金流量净额")
    cash_add: Optional[float] = Field(None, description="现金及现金等价物净增加额")
    cash_end: Optional[float] = Field(None, description="期末现金及现金等价物余额")
    depreciation: Optional[float] = Field(None, description="固定资产折旧")
    minority_interest: Optional[float] = Field(None, description="少数股东权益")
    # 其他字段存储在 extra_fields 中
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他财务指标")


class StockFinancialIndicator(BaseModel):
    """新浪财经财务指标数据模型
    
    包含 86 个财务指标字段，这里列出主要字段，其他字段使用额外字段存储
    """
    date: Optional[str] = Field(None, description="日期")
    diluted_eps: Optional[float] = Field(None, description="摊薄每股收益 (元)")
    weighted_eps: Optional[float] = Field(None, description="加权每股收益 (元)")
    adjusted_eps: Optional[float] = Field(None, description="每股收益_调整后 (元)")
    non_recurring_eps: Optional[float] = Field(None, description="扣除非经常性损益后的每股收益 (元)")
    adjusted_net_asset_per_share_before: Optional[float] = Field(None, description="每股净资产_调整前 (元)")
    adjusted_net_asset_per_share_after: Optional[float] = Field(None, description="每股净资产_调整后 (元)")
    operating_cash_flow_per_share: Optional[float] = Field(None, description="每股经营性现金流 (元)")
    capital_reserve_per_share: Optional[float] = Field(None, description="每股资本公积金 (元)")
    undistributed_profit_per_share: Optional[float] = Field(None, description="每股未分配利润 (元)")
    adjusted_net_assets_per_share: Optional[float] = Field(None, description="调整后的每股净资产 (元)")
    
    # 盈利能力指标
    return_on_total_assets: Optional[float] = Field(None, description="总资产利润率 (%)")
    return_on_main_business: Optional[float] = Field(None, description="主营业务利润率 (%)")
    return_on_net_assets: Optional[float] = Field(None, description="总资产净利润率 (%)")
    return_on_cost_expense: Optional[float] = Field(None, description="成本费用利润率 (%)")
    operating_profit_margin: Optional[float] = Field(None, description="营业利润率 (%)")
    main_business_cost_ratio: Optional[float] = Field(None, description="主营业务成本率 (%)")
    net_profit_margin: Optional[float] = Field(None, description="销售净利率 (%)")
    share_capital_return_rate: Optional[float] = Field(None, description="股本报酬率 (%)")
    return_on_net_assets_weighted: Optional[float] = Field(None, description="加权净资产报酬率 (%)")
    return_on_assets: Optional[float] = Field(None, description="资产报酬率 (%)")
    gross_profit_margin: Optional[float] = Field(None, description="销售毛利率 (%)")
    three_expense_ratio: Optional[float] = Field(None, description="三项费用比重")
    non_main_business_ratio: Optional[float] = Field(None, description="非主营比重")
    main_profit_ratio: Optional[float] = Field(None, description="主营利润比重")
    dividend_payout_ratio: Optional[float] = Field(None, description="股息发放率 (%)")
    investment_return_rate: Optional[float] = Field(None, description="投资收益率 (%)")
    main_business_profit: Optional[float] = Field(None, description="主营业务利润 (元)")
    roe: Optional[float] = Field(None, description="净资产收益率 (%)")
    weighted_roe: Optional[float] = Field(None, description="加权净资产收益率 (%)")
    non_recurring_net_profit: Optional[float] = Field(None, description="扣除非经常性损益后的净利润 (元)")
    
    # 成长能力指标
    revenue_growth_rate: Optional[float] = Field(None, description="主营业务收入增长率 (%)")
    net_profit_growth_rate: Optional[float] = Field(None, description="净利润增长率 (%)")
    net_assets_growth_rate: Optional[float] = Field(None, description="净资产增长率 (%)")
    total_assets_growth_rate: Optional[float] = Field(None, description="总资产增长率 (%)")
    
    # 营运能力指标
    accounts_receivable_turnover: Optional[float] = Field(None, description="应收账款周转率 (次)")
    accounts_receivable_turnover_days: Optional[float] = Field(None, description="应收账款周转天数 (天)")
    inventory_turnover_days: Optional[float] = Field(None, description="存货周转天数 (天)")
    inventory_turnover: Optional[float] = Field(None, description="存货周转率 (次)")
    fixed_assets_turnover: Optional[float] = Field(None, description="固定资产周转率 (次)")
    total_assets_turnover: Optional[float] = Field(None, description="总资产周转率 (次)")
    total_assets_turnover_days: Optional[float] = Field(None, description="总资产周转天数 (天)")
    current_assets_turnover: Optional[float] = Field(None, description="流动资产周转率 (次)")
    current_assets_turnover_days: Optional[float] = Field(None, description="流动资产周转天数 (天)")
    equity_turnover: Optional[float] = Field(None, description="股东权益周转率 (次)")
    
    # 偿债能力指标
    current_ratio: Optional[float] = Field(None, description="流动比率")
    quick_ratio: Optional[float] = Field(None, description="速动比率")
    cash_ratio: Optional[float] = Field(None, description="现金比率 (%)")
    interest_payment_multiple: Optional[float] = Field(None, description="利息支付倍数")
    long_term_debt_to_working_capital: Optional[float] = Field(None, description="长期债务与营运资金比率 (%)")
    equity_ratio: Optional[float] = Field(None, description="股东权益比率 (%)")
    long_term_debt_ratio: Optional[float] = Field(None, description="长期负债比率 (%)")
    equity_to_fixed_assets: Optional[float] = Field(None, description="股东权益与固定资产比率 (%)")
    debt_to_equity: Optional[float] = Field(None, description="负债与所有者权益比率 (%)")
    long_term_assets_to_long_term_capital: Optional[float] = Field(None, description="长期资产与长期资金比率 (%)")
    capitalization_ratio: Optional[float] = Field(None, description="资本化比率 (%)")
    fixed_assets_net_value_ratio: Optional[float] = Field(None, description="固定资产净值率 (%)")
    capital_fixed_ratio: Optional[float] = Field(None, description="资本固定化比率 (%)")
    equity_ratio_percent: Optional[float] = Field(None, description="产权比率 (%)")
    liquidation_value_ratio: Optional[float] = Field(None, description="清算价值比率 (%)")
    fixed_assets_ratio: Optional[float] = Field(None, description="固定资产比重 (%)")
    asset_liability_ratio: Optional[float] = Field(None, description="资产负债率 (%)")
    
    # 现金流量指标
    operating_cash_to_sales: Optional[float] = Field(None, description="经营现金净流量对销售收入比率 (%)")
    operating_cash_to_assets: Optional[float] = Field(None, description="资产的经营现金流量回报率 (%)")
    operating_cash_to_net_profit: Optional[float] = Field(None, description="经营现金净流量与净利润的比率 (%)")
    operating_cash_to_debt: Optional[float] = Field(None, description="经营现金净流量对负债比率 (%)")
    cash_flow_ratio: Optional[float] = Field(None, description="现金流量比率 (%)")
    
    # 投资明细
    short_term_stock_investment: Optional[float] = Field(None, description="短期股票投资 (元)")
    short_term_bond_investment: Optional[float] = Field(None, description="短期债券投资 (元)")
    short_term_other_investment: Optional[float] = Field(None, description="短期其它经营性投资 (元)")
    long_term_stock_investment: Optional[float] = Field(None, description="长期股票投资 (元)")
    long_term_bond_investment: Optional[float] = Field(None, description="长期债券投资 (元)")
    long_term_other_investment: Optional[float] = Field(None, description="长期其它经营性投资 (元)")
    
    # 应收款项明细
    accounts_receivable_within_1_year: Optional[float] = Field(None, description="1 年以内应收帐款 (元)")
    accounts_receivable_1_to_2_years: Optional[float] = Field(None, description="1-2 年以内应收帐款 (元)")
    accounts_receivable_2_to_3_years: Optional[float] = Field(None, description="2-3 年以内应收帐款 (元)")
    accounts_receivable_within_3_years: Optional[float] = Field(None, description="3 年以内应收帐款 (元)")
    advances_within_1_year: Optional[float] = Field(None, description="1 年以内预付货款 (元)")
    advances_1_to_2_years: Optional[float] = Field(None, description="1-2 年以内预付货款 (元)")
    advances_2_to_3_years: Optional[float] = Field(None, description="2-3 年以内预付货款 (元)")
    advances_within_3_years: Optional[float] = Field(None, description="3 年以内预付货款 (元)")
    other_receivables_within_1_year: Optional[float] = Field(None, description="1 年以内其它应收款 (元)")
    other_receivables_1_to_2_years: Optional[float] = Field(None, description="1-2 年以内其它应收款 (元)")
    other_receivables_2_to_3_years: Optional[float] = Field(None, description="2-3 年以内其它应收款 (元)")
    other_receivables_within_3_years: Optional[float] = Field(None, description="3 年以内其它应收款 (元)")
    
    # 其他字段存储在 extra_fields 中
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他财务指标")


class StockInfoA(BaseModel):
    """沪深京 A 股股票列表数据模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票简称")


class StockInfoSH(BaseModel):
    """上海证券交易所股票列表数据模型"""
    security_code: str = Field(..., description="证券代码")
    security_abbr: str = Field(..., description="证券简称")
    company_name: str = Field(..., description="公司全称")
    list_date: str = Field(..., description="上市日期")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockInfoSZ(BaseModel):
    """深圳证券交易所股票列表数据模型"""
    board: str = Field(..., description="板块")
    stock_code: str = Field(..., description="A 股代码")
    stock_abbr: str = Field(..., description="A 股简称")
    list_date: str = Field(..., description="A 股上市日期")
    total_shares: int = Field(None, description="A 股总股本")
    circulating_shares: int = Field(None, description="A 股流通股本")
    industry: str = Field(..., description="所属行业")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockInfoBJ(BaseModel):
    """北京证券交易所股票列表数据模型"""
    security_code: str = Field(..., description="证券代码")
    security_abbr: str = Field(..., description="证券简称")
    total_shares: int = Field(..., description="总股本")
    circulating_shares: int = Field(..., description="流通股本")
    list_date: str = Field(..., description="上市日期")
    industry: str = Field(..., description="所属行业")
    region: str = Field(..., description="地区")
    report_date: str = Field(..., description="报告日期")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockIndustryClfHistSW(BaseModel):
    """申万行业分类变动历史数据模型"""
    symbol: str = Field(..., description="股票代码")
    start_date: str = Field(..., description="计入日期")
    industry_code: str = Field(..., description="申万行业代码")
    update_time: str = Field(..., description="更新日期")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockIndustryPERatio(BaseModel):
    """行业市盈率数据模型"""
    change_date: str = Field(..., description="变动日期")
    industry_class: str = Field(..., description="行业分类")
    industry_level: int = Field(..., description="行业层级")
    industry_code: str = Field(..., description="行业编码")
    industry_name: str = Field(..., description="行业名称")
    company_count: Optional[float] = Field(None, description="公司数量")
    calc_company_count: Optional[float] = Field(None, description="纳入计算公司数量")
    total_market_cap: Optional[float] = Field(None, description="总市值 - 静态（亿元）")
    net_profit: Optional[float] = Field(None, description="净利润 - 静态（亿元）")
    pe_static_weighted: Optional[float] = Field(None, description="静态市盈率 - 加权平均")
    pe_static_median: Optional[float] = Field(None, description="静态市盈率 - 中位数")
    pe_static_arithmetic: Optional[float] = Field(None, description="静态市盈率 - 算术平均")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockHoldNumCNInfo(BaseModel):
    """股东人数及持股集中度数据模型"""
    security_code: str = Field(..., description="证券代码")
    security_abbr: str = Field(..., description="证券简称")
    change_date: str = Field(..., description="变动日期")
    current_holder_count: Optional[int] = Field(None, description="本期股东人数")
    previous_holder_count: Optional[float] = Field(None, description="上期股东人数")
    holder_count_growth: Optional[float] = Field(None, description="股东人数增幅（%）")
    current_avg_shares: Optional[int] = Field(None, description="本期人均持股数量（万股）")
    previous_avg_shares: Optional[float] = Field(None, description="上期人均持股数量（万股）")
    avg_shares_growth: Optional[float] = Field(None, description="人均持股数量增幅（%）")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockPriceJS(BaseModel):
    """美港目标价数据模型"""
    date: str = Field(..., description="日期")
    stock_name: str = Field(..., description="个股名称")
    rating: Optional[str] = Field(None, description="评级")
    previous_target: Optional[float] = Field(None, description="先前目标价")
    latest_target: Optional[float] = Field(None, description="最新目标价")
    institution: str = Field(..., description="机构名称")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockAConestionLG(BaseModel):
    """乐咕乐股 - 大盘拥挤度数据模型"""
    date: str = Field(..., description="日期")
    close: Optional[float] = Field(None, description="收盘价")
    congestion: Optional[float] = Field(None, description="拥挤度")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockEBSLG(BaseModel):
    """乐咕乐股 - 股债利差数据模型"""
    date: str = Field(..., description="日期")
    hs300_index: Optional[float] = Field(None, description="沪深 300 指数")
    ebs: Optional[float] = Field(None, description="股债利差")
    ebs_ma: Optional[float] = Field(None, description="股债利差均线")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockBuffettIndexLG(BaseModel):
    """乐咕乐股 - 巴菲特指标数据模型"""
    date: str = Field(..., description="交易日")
    close: Optional[float] = Field(None, description="收盘价")
    total_market_cap: Optional[float] = Field(None, description="总市值（亿元）")
    gdp: Optional[float] = Field(None, description="上年度 GDP（亿元）")
    decile_10y: Optional[float] = Field(None, description="近十年分位数")
    decile_all: Optional[float] = Field(None, description="总历史分位数")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockZhValuationBaidu(BaseModel):
    """百度股市通-A 股估值数据模型"""
    date: str = Field(..., description="日期")
    value: Optional[float] = Field(None, description="估值指标值")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockValueEM(BaseModel):
    """东方财富网 - 个股估值数据模型"""
    report_date: str = Field(..., description="数据日期")
    close_price: Optional[float] = Field(None, description="当日收盘价（元）")
    change_pct: Optional[float] = Field(None, description="当日涨跌幅（%）")
    total_mv: Optional[float] = Field(None, description="总市值（元）")
    float_mv: Optional[float] = Field(None, description="流通市值（元）")
    total_shares: Optional[float] = Field(None, description="总股本（股）")
    float_shares: Optional[float] = Field(None, description="流通股本（股）")
    pe_ttm: Optional[float] = Field(None, description="市盈率 (TTM)")
    pe_static: Optional[float] = Field(None, description="市盈率 (静)")
    pb: Optional[float] = Field(None, description="市净率")
    peg: Optional[float] = Field(None, description="PEG 值")
    pc: Optional[float] = Field(None, description="市现率")
    ps: Optional[float] = Field(None, description="市销率")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockZhVoteBaidu(BaseModel):
    """百度股市通 - 涨跌投票数据模型"""
    period: str = Field(..., description="周期（今日/本周/本月/今年）")
    vote_up: Optional[int] = Field(None, description="看涨票数")
    vote_down: Optional[int] = Field(None, description="看跌票数")
    vote_up_ratio: Optional[float] = Field(None, description="看涨比例（%）")
    vote_down_ratio: Optional[float] = Field(None, description="看跌比例（%）")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockAHighLowStatistics(BaseModel):
    """乐咕乐股 - 创新高/新低统计数据模型"""
    date: str = Field(..., description="交易日")
    close: Optional[float] = Field(None, description="相关指数收盘价")
    high20: Optional[int] = Field(None, description="20 日新高数量")
    low20: Optional[int] = Field(None, description="20 日新低数量")
    high60: Optional[int] = Field(None, description="60 日新高数量")
    low60: Optional[int] = Field(None, description="60 日新低数量")
    high120: Optional[int] = Field(None, description="120 日新高数量")
    low120: Optional[int] = Field(None, description="120 日新低数量")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockABelowNetAssetStatistics(BaseModel):
    """乐咕乐股 - 破净股统计数据模型"""
    date: str = Field(..., description="交易日")
    below_net_asset: Optional[int] = Field(None, description="破净股家数")
    total_company: Optional[int] = Field(None, description="总公司数")
    below_net_asset_ratio: Optional[float] = Field(None, description="破净股比率")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockDzjySctj(BaseModel):
    """东方财富网 - 大宗交易市场统计数据模型"""
    index: Optional[int] = Field(None, description="序号")
    date: str = Field(..., description="交易日期")
    sh_index: Optional[float] = Field(None, description="上证指数")
    sh_change_pct: Optional[float] = Field(None, description="上证指数涨跌幅（%）")
    total_amount: Optional[float] = Field(None, description="大宗交易成交总额（元）")
    premium_amount: Optional[float] = Field(None, description="溢价成交总额（元）")
    premium_ratio: Optional[float] = Field(None, description="溢价成交总额占比（%）")
    discount_amount: Optional[float] = Field(None, description="折价成交总额（元）")
    discount_ratio: Optional[float] = Field(None, description="折价成交总额占比（%）")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockDzjyMrmx(BaseModel):
    """东方财富网 - 大宗交易每日明细数据模型（A 股）"""
    index: Optional[int] = Field(None, description="序号")
    date: str = Field(..., description="交易日期")
    stock_code: str = Field(..., description="证券代码")
    stock_name: str = Field(..., description="证券简称")
    change_pct: Optional[float] = Field(None, description="涨跌幅（%）")
    close_price: Optional[float] = Field(None, description="收盘价（元）")
    deal_price: Optional[float] = Field(None, description="成交价（元）")
    premium_ratio: Optional[float] = Field(None, description="折溢率（%）")
    volume: Optional[int] = Field(None, description="成交量（股）")
    amount: Optional[float] = Field(None, description="成交额（元）")
    amount_ratio: Optional[float] = Field(None, description="成交额/流通市值（%）")
    buyer_dept: Optional[str] = Field(None, description="买方营业部")
    seller_dept: Optional[str] = Field(None, description="卖方营业部")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockMarginRatioPa(BaseModel):
    """平安证券 - 融资融券标的证券及保证金比例数据模型"""
    stock_code: str = Field(..., description="证券代码")
    stock_name: str = Field(..., description="证券简称")
    margin_ratio: Optional[float] = Field(None, description="融资比例")
    short_ratio: Optional[float] = Field(None, description="融券比例")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockMarginAccountInfo(BaseModel):
    """东方财富网 - 融资融券账户统计数据模型"""
    date: str = Field(..., description="日期")
    margin_balance: Optional[float] = Field(None, description="融资余额（亿）")
    short_balance: Optional[float] = Field(None, description="融券余额（亿）")
    margin_buy: Optional[float] = Field(None, description="融资买入额（亿）")
    short_sell: Optional[float] = Field(None, description="融券卖出额（亿）")
    broker_count: Optional[int] = Field(None, description="证券公司数量（家）")
    branch_count: Optional[int] = Field(None, description="营业部数量（家）")
    individual_count: Optional[float] = Field(None, description="个人投资者数量（万名）")
    institution_count: Optional[int] = Field(None, description="机构投资者数量（家）")
    active_count: Optional[float] = Field(None, description="参与交易的投资者数量（万名）")
    debt_count: Optional[float] = Field(None, description="有融资融券负债的投资者数量（万名）")
    collateral_value: Optional[float] = Field(None, description="担保物总价值（亿）")
    collateral_ratio: Optional[float] = Field(None, description="平均维持担保比例（%）")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockMarginSse(BaseModel):
    """上海证券交易所 - 融资融券汇总数据模型"""
    credit_trade_date: str = Field(..., description="信用交易日期")
    margin_balance: Optional[int] = Field(None, description="融资余额（元）")
    margin_buy: Optional[int] = Field(None, description="融资买入额（元）")
    short_remaining: Optional[int] = Field(None, description="融券余量")
    short_remaining_amount: Optional[int] = Field(None, description="融券余量金额（元）")
    short_sell: Optional[int] = Field(None, description="融券卖出量")
    total_margin_short_balance: Optional[int] = Field(None, description="融资融券余额（元）")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockMarginDetailSse(BaseModel):
    """上海证券交易所 - 融资融券明细数据模型"""
    credit_trade_date: str = Field(..., description="信用交易日期")
    stock_code: str = Field(..., description="标的证券代码")
    stock_name: str = Field(..., description="标的证券简称")
    margin_balance: Optional[int] = Field(None, description="融资余额（元）")
    margin_buy: Optional[int] = Field(None, description="融资买入额（元）")
    margin_repay: Optional[int] = Field(None, description="融资偿还额（元）")
    short_remaining: Optional[int] = Field(None, description="融券余量")
    short_sell: Optional[int] = Field(None, description="融券卖出量")
    short_repay: Optional[int] = Field(None, description="融券偿还量")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockMarginSzse(BaseModel):
    """深圳证券交易所 - 融资融券汇总数据模型"""
    margin_buy: Optional[float] = Field(None, description="融资买入额（亿元）")
    margin_balance: Optional[float] = Field(None, description="融资余额（亿元）")
    short_sell: Optional[float] = Field(None, description="融券卖出量（亿股/亿份）")
    short_remaining: Optional[float] = Field(None, description="融券余量（亿股/亿份）")
    short_balance: Optional[float] = Field(None, description="融券余额（亿元）")
    total_margin_short_balance: Optional[float] = Field(None, description="融资融券余额（亿元）")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockMarginDetailSzse(BaseModel):
    """深圳证券交易所 - 融资融券明细数据模型"""
    stock_code: str = Field(..., description="证券代码")
    stock_name: str = Field(..., description="证券简称")
    margin_buy: Optional[int] = Field(None, description="融资买入额（元）")
    margin_balance: Optional[int] = Field(None, description="融资余额（元）")
    short_sell: Optional[int] = Field(None, description="融券卖出量（股/份）")
    short_remaining: Optional[int] = Field(None, description="融券余量（股/份）")
    short_balance: Optional[int] = Field(None, description="融券余额（元）")
    total_margin_short_balance: Optional[int] = Field(None, description="融资融券余额（元）")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockMarginUnderlyingInfoSzse(BaseModel):
    """深圳证券交易所 - 标的证券信息数据模型"""
    stock_code: str = Field(..., description="证券代码")
    stock_name: str = Field(..., description="证券简称")
    margin_target: str = Field(..., description="融资标的（Y/N）")
    short_target: str = Field(..., description="融券标的（Y/N）")
    margin_available_today: str = Field(..., description="当日可融资（Y/N）")
    short_available_today: str = Field(..., description="当日可融券（Y/N）")
    short_sell_price_restriction: str = Field(..., description="融券卖出价格限制")
    price_limit: str = Field(..., description="涨跌幅限制")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockProfitForecastEm(BaseModel):
    """东方财富网 - 盈利预测数据模型"""
    serial_number: Optional[int] = Field(None, description="序号")
    stock_code: str = Field(..., description="代码")
    stock_name: str = Field(..., description="名称")
    report_count: Optional[int] = Field(None, description="研报数")
    buy_rating: Optional[float] = Field(None, description="买入评级数量")
    add_rating: Optional[float] = Field(None, description="增持评级数量")
    neutral_rating: Optional[float] = Field(None, description="中性评级数量")
    reduce_rating: Optional[int] = Field(None, description="减持评级数量")
    sell_rating: Optional[int] = Field(None, description="卖出评级数量")
    eps_2022: Optional[float] = Field(None, description="2022 预测每股收益")
    eps_2023: Optional[float] = Field(None, description="2023 预测每股收益")
    eps_2024: Optional[float] = Field(None, description="2024 预测每股收益")
    eps_2025: Optional[float] = Field(None, description="2025 预测每股收益")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockBoardIndustryNameEm(BaseModel):
    """东方财富 - 行业板块数据模型"""
    rank: Optional[int] = Field(None, description="排名")
    board_name: str = Field(..., description="板块名称")
    board_code: str = Field(..., description="板块代码")
    latest_price: Optional[float] = Field(None, description="最新价")
    change_amount: Optional[float] = Field(None, description="涨跌额")
    change_percent: Optional[float] = Field(None, description="涨跌幅（%）")
    total_market_value: Optional[int] = Field(None, description="总市值")
    turnover_rate: Optional[float] = Field(None, description="换手率（%）")
    rise_count: Optional[int] = Field(None, description="上涨家数")
    fall_count: Optional[int] = Field(None, description="下跌家数")
    leading_stock: str = Field(..., description="领涨股票")
    leading_stock_change_percent: Optional[float] = Field(None, description="领涨股票涨跌幅（%）")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockBoardIndustrySpotEm(BaseModel):
    """东方财富 - 行业板块实时行情数据模型"""
    item: str = Field(..., description="项目")
    value: Optional[float] = Field(None, description="数值")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")


class StockBoardIndustryConsEm(BaseModel):
    """东方财富 - 行业板块成份股数据模型"""
    serial_number: Optional[int] = Field(None, description="序号")
    stock_code: str = Field(..., description="代码")
    stock_name: str = Field(..., description="名称")
    latest_price: Optional[float] = Field(None, description="最新价")
    change_percent: Optional[float] = Field(None, description="涨跌幅（%）")
    change_amount: Optional[float] = Field(None, description="涨跌额")
    volume: Optional[float] = Field(None, description="成交量（手）")
    amount: Optional[float] = Field(None, description="成交额")
    amplitude: Optional[float] = Field(None, description="振幅（%）")
    high: Optional[float] = Field(None, description="最高")
    low: Optional[float] = Field(None, description="最低")
    open: Optional[float] = Field(None, description="今开")
    prev_close: Optional[float] = Field(None, description="昨收")
    turnover_rate: Optional[float] = Field(None, description="换手率（%）")
    pe_ratio_dynamic: Optional[float] = Field(None, description="市盈率 - 动态")
    pb_ratio: Optional[float] = Field(None, description="市净率")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")
