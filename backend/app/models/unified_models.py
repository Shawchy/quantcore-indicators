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
    TUSHARE = "tushare"


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


class DataSourceHealthStatus(BaseModel):
    """数据源健康状态"""
    source: DataSourceType = Field(..., description="数据源")
    status: str = Field(..., description="状态（healthy/degraded/unhealthy/error）")
    response_time: float = Field(..., ge=0, description="响应时间（秒）")
    last_check: str = Field(..., description="最后检查时间")
    error: Optional[str] = Field(None, description="错误信息")
    test_result: str = Field(..., description="测试结果")
