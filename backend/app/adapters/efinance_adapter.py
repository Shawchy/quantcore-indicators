import asyncio
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from loguru import logger
from pydantic import BaseModel

try:
    import efinance as ef
    from efinance.utils import MarketType
    EF_AVAILABLE = True
except ImportError:
    EF_AVAILABLE = False
    logger.warning("efinance 未安装，请运行：pip install efinance")

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData,
    IndexMember
)
from app.models.schemas import (
    BillboardEntry,
    BoardInfo,
    ShareholderInfo,
    IndexComponent,
    CapitalFlowItem
)


class CompanyPerformance(BaseModel):
    """公司业绩表现数据"""
    code: str
    name: str
    report_date: str
    revenue: float  # 营业收入
    revenue_growth: float  # 营业收入同比增长
    revenue_qoq: float  # 营业收入季度环比
    net_profit: float  # 净利润
    net_profit_growth: float  # 净利润同比增长
    net_profit_qoq: float  # 净利润季度环比
    eps: float  # 每股收益
    bps: float  # 每股净资产
    roe: float  # 净资产收益率
    gross_margin: float  # 销售毛利率
    cash_flow_per_share: float  # 每股经营现金流量


class DealDetail(BaseModel):
    """股票成交明细数据"""
    stock_name: str  # 股票名称
    stock_code: str  # 股票代码
    prev_close: float  # 昨收价
    trade_time: str  # 成交时间（HH:MM:SS）
    price: float  # 成交价
    volume: int  # 成交量（手）
    order_count: int  # 成交单数


class HistoryBill(BaseModel):
    """股票历史单子流入流出数据"""
    stock_name: str  # 股票名称
    stock_code: str  # 股票代码
    date: str  # 日期
    main_net_amount: float  # 主力净流入
    small_net_amount: float  # 小单净流入
    medium_net_amount: float  # 中单净流入
    big_net_amount: float  # 大单净流入
    super_net_amount: float  # 超大单净流入
    main_net_ratio: float  # 主力净流入占比
    small_net_ratio: float  # 小单流入净占比
    medium_net_ratio: float  # 中单流入净占比
    big_net_ratio: float  # 大单流入净占比
    super_net_ratio: float  # 超大单流入净占比
    close_price: float  # 收盘价
    change_pct: float  # 涨跌幅
from app.utils.data_validator import validator
from app.utils.tushare_cache_stats import api_call_cache


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


class EFinanceAdapter(BaseDataAdapter):
    """efinance 数据源适配器
    
    efinance 是一个免费的金融数据接口库，提供 A 股、基金、期货等数据
    GitHub: https://github.com/Micro-sun/efinance
    
    特点：
    - 完全免费，无需注册
    - 数据来源于东方财富
    - 支持 A 股、基金、期货、债券等
    - 实时行情、历史 K 线、财务数据等
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._is_initialized = False
        
        # 内存缓存
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Dict[str, float] = {}
        # 不同数据的缓存时间（秒）
        self._cache_ttl = {
            'kline': 300,        # K 线：5 分钟
            'stock_list': 1800,  # 股票列表：30 分钟
            'stock_info': 600,   # 股票信息：10 分钟
            'quote': 60,         # 实时行情：1 分钟
            'sector': 300,       # 板块：5 分钟
            'default': 300       # 默认：5 分钟
        }
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.EFINANCE
    
    async def initialize(self) -> bool:
        """初始化适配器"""
        if not EF_AVAILABLE:
            logger.warning("efinance 模块不可用，跳过初始化")
            return False
        
        try:
            # efinance 无需初始化，直接可用
            self._is_initialized = True
            logger.info("efinance 适配器初始化成功")
            return True
        except Exception as e:
            logger.error(f"efinance 适配器初始化失败：{e}")
            return False
    
    async def close(self):
        """关闭连接"""
        self._is_initialized = False
        self._cache.clear()
        self._cache_timestamp.clear()
        logger.info("efinance 适配器已关闭")
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存 key"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return "_".join(key_parts)
    
    def _get_from_cache(self, key: str, ttl_type: str = 'default') -> Optional[Any]:
        """从缓存获取数据"""
        import time
        if key not in self._cache:
            return None
        
        timestamp = self._cache_timestamp.get(key, 0)
        ttl = self._cache_ttl.get(ttl_type, self._cache_ttl['default'])
        
        if time.time() - timestamp > ttl:
            del self._cache[key]
            del self._cache_timestamp[key]
            return None
        
        return self._cache[key]
    
    def _set_to_cache(self, key: str, value: Any, ttl_type: str = 'default'):
        """设置缓存"""
        import time
        self._cache[key] = value
        self._cache_timestamp[key] = time.time()
    
    async def get_stock_list(self) -> List[StockBasicInfo]:
        """获取股票列表"""
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('stock_list')
            cached = self._get_from_cache(cache_key, 'stock_list')
            if cached:
                return cached
            
            # 获取沪深 A 股实时行情，从中提取股票基本信息
            df = ef.stock.get_realtime_quotes()
            
            stocks = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', '')).zfill(6)
                # 过滤掉非 A 股数据
                if not code or not code.isdigit():
                    continue
                
                # 安全转换浮点数，处理 '-' 等无效值
                def safe_float(value, default=0.0):
                    try:
                        v = float(value) if value not in ('-', '', None) else default
                        return v
                    except (ValueError, TypeError):
                        return default
                
                price = safe_float(getattr(row, '最新价', 1), 1.0)
                if price == 0:
                    price = 1.0
                
                stocks.append(StockBasicInfo(
                    code=code,
                    name=getattr(row, '股票名称', ''),
                    market='SH' if code.startswith('6') else 'SZ',
                    industry='',
                    area='',
                    list_date='',
                    total_shares=safe_float(getattr(row, '总市值', 0)) / price,
                    float_shares=safe_float(getattr(row, '流通市值', 0)) / price
                ))
            
            self._set_to_cache(cache_key, stocks, 'stock_list')
            logger.info(f"获取股票列表成功：{len(stocks)}只")
            return stocks
            
        except Exception as e:
            logger.error(f"获取股票列表失败：{e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        """获取股票信息"""
        try:
            if not EF_AVAILABLE:
                return None
            
            cache_key = self._get_cache_key('stock_info', code=code)
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            # 获取股票信息
            df = ef.stock.get_base_info(code.zfill(6))
            
            if df is None or (hasattr(df, 'empty') and df.empty):
                return None
            
            # 单只股票返回 Series
            if hasattr(df, 'dtype'):
                # 安全获取数值，处理 NaN
                def safe_get(series, key, default=0.0):
                    val = series.get(key, default)
                    if val is None or (isinstance(val, float) and str(val) == 'nan'):
                        return default
                    return val
                
                latest_price = safe_get(df, '最新价', 1.0)
                if latest_price == 0:
                    latest_price = 1.0
                
                total_shares_raw = safe_get(df, '总市值', 0.0)
                float_shares_raw = safe_get(df, '流通市值', 0.0)
                
                stock = StockBasicInfo(
                    code=code.zfill(6),
                    name=df.get('股票名称', '') or '',
                    market='SH' if code.startswith('6') else 'SZ',
                    industry=df.get('所处行业', '') or '',
                    area='',
                    list_date='',
                    total_shares=total_shares_raw / latest_price if total_shares_raw > 0 else 0.0,
                    float_shares=float_shares_raw / latest_price if float_shares_raw > 0 else 0.0
                )
            else:
                return None
            
            self._set_to_cache(cache_key, stock, 'stock_info')
            return stock
            
        except Exception as e:
            logger.error(f"获取股票信息失败 {code}: {e}")
            return None
    
    async def get_stocks_base_info(self, stock_codes: List[str]) -> List[StockBasicInfo]:
        """
        批量获取多只股票的基本信息
        
        Args:
            stock_codes: 股票代码列表，如 ['600519', '000858']
        
        Returns:
            股票基本信息列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            if not stock_codes:
                return []
            
            # 生成缓存 key
            codes_key = '_'.join(sorted(stock_codes))
            cache_key = self._get_cache_key('stocks_base_info', codes=codes_key)
            cached = self._get_from_cache(cache_key, 'stock_list')
            if cached:
                return cached
            
            # 批量获取股票信息
            df = ef.stock.get_base_info(stock_codes)
            
            if df is None or (hasattr(df, 'empty') and df.empty):
                return []
            
            stocks = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', '')).zfill(6)
                if not code:
                    continue
                
                # 安全转换浮点数
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                # 获取最新价用于计算股本
                latest_price = safe_float(getattr(row, '最新价', 1.0), 1.0)
                if latest_price == 0:
                    latest_price = 1.0
                
                total_shares_raw = safe_float(getattr(row, '总市值', 0.0), 0.0)
                float_shares_raw = safe_float(getattr(row, '流通市值', 0.0), 0.0)
                
                stocks.append(StockBasicInfo(
                    code=code,
                    name=getattr(row, '股票名称', '') or '',
                    market='SH' if code.startswith('6') else 'SZ',
                    industry=getattr(row, '所处行业', '') or '',
                    area='',
                    list_date='',
                    total_shares=total_shares_raw / latest_price if total_shares_raw > 0 else 0.0,
                    float_shares=float_shares_raw / latest_price if float_shares_raw > 0 else 0.0
                ))
            
            self._set_to_cache(cache_key, stocks, 'stock_list')
            logger.info(f"批量获取股票信息成功：{len(stocks)}只")
            return stocks
            
        except Exception as e:
            logger.error(f"批量获取股票信息失败：{e}")
            return []
    
    async def get_deal_detail(self, stock_code: str, max_count: int = 1000000) -> List[DealDetail]:
        """
        获取股票最新交易日成交明细
        
        Args:
            stock_code: 股票代码或股票名称，如 '600519' 或 '贵州茅台'
            max_count: 最近的最大数据条数，默认 1000000
            
        Returns:
            成交明细数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> deals = await adapter.get_deal_detail('600519')
            >>> for deal in deals[:5]:
            ...     print(f"{deal.trade_time} - {deal.price:.2f}元 - {deal.volume}手")
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('deal_detail', code=stock_code, max_count=max_count)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 获取成交明细数据
            df = ef.stock.get_deal_detail(stock_code, max_count=max_count)
            
            if df.empty:
                return []
            
            deals = []
            for row in df.itertuples(index=False):
                # 安全转换数值
                def safe_int(value, default=0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return int(value)
                    except (ValueError, TypeError):
                        return default
                
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                stock_code_raw = str(getattr(row, '股票代码', '')).zfill(6)
                if not stock_code_raw:
                    continue
                
                deals.append(DealDetail(
                    stock_name=getattr(row, '股票名称', '') or '',
                    stock_code=stock_code_raw,
                    prev_close=safe_float(getattr(row, '昨收', 0), 0.0),
                    trade_time=str(getattr(row, '时间', '') or ''),
                    price=safe_float(getattr(row, '成交价', 0), 0.0),
                    volume=safe_int(getattr(row, '成交量', 0), 0),
                    order_count=safe_int(getattr(row, '单数', 0), 0)
                ))
            
            self._set_to_cache(cache_key, deals, 'kline')
            logger.info(f"获取 {stock_code} 成交明细成功：{len(deals)}条")
            return deals
            
        except Exception as e:
            logger.error(f"获取成交明细失败 {stock_code}: {e}")
            return []
    
    async def get_history_bill(self, stock_code: str) -> List[HistoryBill]:
        """
        获取单只股票历史单子流入流出数据
        
        Args:
            stock_code: 股票代码
            
        Returns:
            历史单子流入流出数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> bills = await adapter.get_history_bill('600519')
            >>> for bill in bills[:5]:
            ...     print(f"{bill.date} - 主力净流入：{bill.main_net_amount/1e8:.2f}亿")
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('history_bill', code=stock_code)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 获取历史单子流入流出数据
            df = ef.stock.get_history_bill(stock_code)
            
            if df.empty:
                return []
            
            bills = []
            for row in df.itertuples(index=False):
                # 安全转换数值
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                stock_code_raw = str(getattr(row, '股票代码', '')).zfill(6)
                if not stock_code_raw:
                    continue
                
                date_raw = getattr(row, '日期', '')
                if date_raw:
                    if isinstance(date_raw, str):
                        date = date_raw.split(' ')[0].replace('-', '')
                    else:
                        date = str(date_raw)[:10].replace('-', '')
                    if len(date) == 10:  # YYYY-MM-DD 格式
                        date = date.replace('-', '')
                else:
                    date = ''
                
                bills.append(HistoryBill(
                    stock_name=getattr(row, '股票名称', '') or '',
                    stock_code=stock_code_raw,
                    date=date,
                    main_net_amount=safe_float(getattr(row, '主力净流入', 0), 0.0),
                    small_net_amount=safe_float(getattr(row, '小单净流入', 0), 0.0),
                    medium_net_amount=safe_float(getattr(row, '中单净流入', 0), 0.0),
                    big_net_amount=safe_float(getattr(row, '大单净流入', 0), 0.0),
                    super_net_amount=safe_float(getattr(row, '超大单净流入', 0), 0.0),
                    main_net_ratio=safe_float(getattr(row, '主力净流入占比', 0), 0.0),
                    small_net_ratio=safe_float(getattr(row, '小单流入净占比', 0), 0.0),
                    medium_net_ratio=safe_float(getattr(row, '中单流入净占比', 0), 0.0),
                    big_net_ratio=safe_float(getattr(row, '大单流入净占比', 0), 0.0),
                    super_net_ratio=safe_float(getattr(row, '超大单流入净占比', 0), 0.0),
                    close_price=safe_float(getattr(row, '收盘价', 0), 0.0),
                    change_pct=safe_float(getattr(row, '涨跌幅', 0), 0.0)
                ))
            
            self._set_to_cache(cache_key, bills, 'kline')
            logger.info(f"获取 {stock_code} 历史资金流向成功：{len(bills)}条")
            return bills
            
        except Exception as e:
            logger.error(f"获取历史资金流向失败 {stock_code}: {e}")
            return []
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        klt: int = 101,
        fqt: int = 1,
        market_type: Optional[str] = None,
        adjust: Optional[str] = None
    ) -> List[KLineData]:
        """
        获取股票 K 线数据（支持多种周期和复权方式）
        
        Args:
            code: 股票代码或名称，如 '600519' 或 '贵州茅台'
            start_date: 开始日期，格式：YYYY-MM-DD 或 YYYYMMDD，默认 '1900-01-01'
            end_date: 结束日期，格式：YYYY-MM-DD 或 YYYYMMDD，默认 '2050-01-01'
            klt: 时间间隔（秒），默认 101（日线）
                - 1: 分钟
                - 5: 5 分钟
                - 15: 15 分钟
                - 30: 30 分钟
                - 60: 60 分钟
                - 101: 日
                - 102: 周
                - 103: 月
            fqt: 复权方式，默认 1（前复权）
                - 0: 不复权
                - 1: 前复权
                - 2: 后复权
            market_type: 市场类型，可选值：
                - 'A_stock': A 股（默认）
                - 'Hongkong': 港股
                - 'London_stock_exchange': 英股
                - 'US_stock': 美股
            adjust: 兼容旧参数，如果提供则转换为 fqt
                - 'qfq': 前复权 (fqt=1)
                - 'hfq': 后复权 (fqt=2)
                - None: 不复权 (fqt=0)
        
        Returns:
            K 线数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> # 获取日线数据（前复权）
            >>> klines = await adapter.get_kline('600519')
            >>> # 获取周线数据（不复权）
            >>> weekly = await adapter.get_kline('600519', klt=102, fqt=0)
            >>> # 获取 60 分钟 K 线
            >>> hourly = await adapter.get_kline('600519', klt=60)
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            # 兼容旧的 adjust 参数
            if adjust is not None and fqt == 1:
                if adjust == 'qfq':
                    fqt = 1
                elif adjust == 'hfq':
                    fqt = 2
                else:
                    fqt = 0
            
            # 格式化日期
            beg = start_date.replace('-', '') if start_date else '19000101'
            if len(beg) == 8 and '-' not in beg:
                pass  # 已经是 YYYYMMDD 格式
            elif len(beg) == 10:
                beg = beg.replace('-', '')
            
            end = end_date.replace('-', '') if end_date else '20500101'
            if len(end) == 8 and '-' not in end:
                pass
            elif len(end) == 10:
                end = end.replace('-', '')
            
            cache_key = self._get_cache_key('kline', code=code, start=beg, end=end, klt=klt, fqt=fqt)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 构建参数
            kwargs = {
                'beg': beg,
                'end': end,
                'klt': klt,
                'fqt': fqt,
                'use_id_cache': True
            }
            
            # 处理市场类型
            if market_type:
                try:
                    market_enum = getattr(MarketType, market_type, None)
                    if market_enum:
                        kwargs['market_type'] = market_enum
                except Exception:
                    logger.warning(f"无效的市场类型：{market_type}")
            
            # 获取 K 线数据
            df = ef.stock.get_quote_history(code.zfill(6), **kwargs)
            
            if df.empty:
                return []
            
            klines = []
            prev_close = None
            for row in df.itertuples(index=False):
                # 获取日期字段
                date_raw = str(getattr(row, '时间', getattr(row, '日期', '')))
                
                if not date_raw or date_raw == '':
                    logger.warning(f"K 线数据日期为空：{code}")
                    continue
                
                # 统一格式为 YYYYMMDD
                if len(date_raw) == 10 and '-' in date_raw:
                    date = date_raw.replace('-', '')
                elif len(date_raw) == 8:
                    date = date_raw
                else:
                    logger.warning(f"K 线数据日期格式异常：{date_raw}")
                    continue
                
                # 安全转换浮点数
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                current_close = safe_float(getattr(row, '收盘', 0), 0.0)
                klines.append(KLineData(
                    code=code,
                    date=date,
                    open=safe_float(getattr(row, '开盘', 0), 0.0),
                    high=safe_float(getattr(row, '最高', 0), 0.0),
                    low=safe_float(getattr(row, '最低', 0), 0.0),
                    close=current_close,
                    volume=safe_float(getattr(row, '成交量', 0), 0.0),
                    amount=safe_float(getattr(row, '成交额', 0), 0.0),
                    turnover_rate=safe_float(getattr(row, '换手率', 0), 0.0),
                    pre_close=prev_close
                ))
                prev_close = current_close
            
            # 按日期排序
            klines.sort(key=lambda x: x.date)
            
            self._set_to_cache(cache_key, klines, 'kline')
            logger.info(f"获取 K 线数据成功 {code}: {len(klines)}条 (klt={klt}, fqt={fqt})")
            return klines
            
        except Exception as e:
            logger.error(f"获取 K 线数据失败 {code}: {e}")
            return []
    
    async def get_multi_kline(
        self,
        stock_codes: List[str],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        klt: int = 101,
        fqt: int = 1,
        market_type: Optional[str] = None
    ) -> Dict[str, List[KLineData]]:
        """
        批量获取多只股票的 K 线数据
        
        Args:
            stock_codes: 股票代码列表，如 ['600519', '300750']
            start_date: 开始日期，格式：YYYY-MM-DD 或 YYYYMMDD
            end_date: 结束日期，格式：YYYY-MM-DD 或 YYYYMMDD
            klt: 时间间隔，默认 101（日线）
            fqt: 复权方式，默认 1（前复权）
            market_type: 市场类型
        
        Returns:
            字典，key 为股票代码，value 为 K 线数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> klines = await adapter.get_multi_kline(['600519', '300750'])
            >>> for code, data in klines.items():
            ...     print(f"{code}: {len(data)}条 K 线数据")
        """
        try:
            if not EF_AVAILABLE:
                return {}
            
            if not stock_codes:
                return {}
            
            # 生成缓存 key
            codes_key = '_'.join(sorted(stock_codes))
            cache_key = self._get_cache_key('multi_kline', codes=codes_key, start=start_date, end=end_date, klt=klt, fqt=fqt)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 格式化日期
            beg = start_date.replace('-', '') if start_date else '19000101'
            if len(beg) == 10:
                beg = beg.replace('-', '')
            
            end = end_date.replace('-', '') if end_date else '20500101'
            if len(end) == 10:
                end = end.replace('-', '')
            
            # 构建参数
            kwargs = {
                'beg': beg,
                'end': end,
                'klt': klt,
                'fqt': fqt,
                'use_id_cache': True
            }
            
            # 处理市场类型
            if market_type:
                try:
                    market_enum = getattr(MarketType, market_type, None)
                    if market_enum:
                        kwargs['market_type'] = market_enum
                except Exception:
                    logger.warning(f"无效的市场类型：{market_type}")
            
            # 批量获取 K 线数据
            result_dict = ef.stock.get_quote_history(stock_codes, **kwargs)
            
            if not result_dict:
                return {}
            
            all_klines = {}
            for code, df in result_dict.items():
                if df.empty:
                    all_klines[code] = []
                    continue
                
                klines = []
                prev_close = None
                for row in df.itertuples(index=False):
                    date_raw = str(getattr(row, '时间', getattr(row, '日期', '')))
                    
                    if not date_raw or date_raw == '':
                        continue
                    
                    if len(date_raw) == 10 and '-' in date_raw:
                        date = date_raw.replace('-', '')
                    elif len(date_raw) == 8:
                        date = date_raw
                    else:
                        continue
                    
                    def safe_float(value, default=0.0):
                        try:
                            if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                                return default
                            return float(value)
                        except (ValueError, TypeError):
                            return default
                    
                    current_close = safe_float(getattr(row, '收盘', 0), 0.0)
                    klines.append(KLineData(
                        code=code,
                        date=date,
                        open=safe_float(getattr(row, '开盘', 0), 0.0),
                        high=safe_float(getattr(row, '最高', 0), 0.0),
                        low=safe_float(getattr(row, '最低', 0), 0.0),
                        close=current_close,
                        volume=safe_float(getattr(row, '成交量', 0), 0.0),
                        amount=safe_float(getattr(row, '成交额', 0), 0.0),
                        turnover_rate=safe_float(getattr(row, '换手率', 0), 0.0),
                        pre_close=prev_close
                    ))
                    prev_close = current_close
                
                klines.sort(key=lambda x: x.date)
                all_klines[code] = klines
            
            self._set_to_cache(cache_key, all_klines, 'kline')
            logger.info(f"批量获取 K 线数据成功：{len(all_klines)}只股票")
            return all_klines
            
        except Exception as e:
            logger.error(f"批量获取 K 线数据失败：{e}")
            return {}
    
    @api_call_cache(ttl=1800)  # 缓存 30 分钟
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fqt: int = 1,
        market_type: Optional[str] = None,
        adjust: Optional[str] = None
    ) -> List[KLineData]:
        """
        获取周 K 线数据（带重试机制）
        
        Args:
            code: 股票代码或名称
            start_date: 开始日期，格式：YYYY-MM-DD 或 YYYYMMDD
            end_date: 结束日期，格式：YYYY-MM-DD 或 YYYYMMDD
            fqt: 复权方式，默认 1（前复权）
                - 0: 不复权
                - 1: 前复权
                - 2: 后复权
            market_type: 市场类型
            adjust: 兼容旧参数
        
        Returns:
            周 K 线数据列表
        """
        # 直接调用优化后的 get_kline 方法
        return await self.get_kline(
            code=code,
            start_date=start_date,
            end_date=end_date,
            klt=102,  # 周线
            fqt=fqt,
            market_type=market_type,
            adjust=adjust
        )
    
    @api_call_cache(ttl=1800)  # 缓存 30 分钟
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        fqt: int = 1,
        market_type: Optional[str] = None,
        adjust: Optional[str] = None
    ) -> List[KLineData]:
        """
        获取月 K 线数据（带重试机制）
        
        Args:
            code: 股票代码或名称
            start_date: 开始日期，格式：YYYY-MM-DD 或 YYYYMMDD
            end_date: 结束日期，格式：YYYY-MM-DD 或 YYYYMMDD
            fqt: 复权方式，默认 1（前复权）
                - 0: 不复权
                - 1: 前复权
                - 2: 后复权
            market_type: 市场类型
            adjust: 兼容旧参数
        
        Returns:
            月 K 线数据列表
        """
        # 直接调用优化后的 get_kline 方法
        return await self.get_kline(
            code=code,
            start_date=start_date,
            end_date=end_date,
            klt=103,  # 月线
            fqt=fqt,
            market_type=market_type,
            adjust=adjust
        )
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        """
        获取沪深市场股票最新行情快照
        
        Args:
            code: 股票代码，如 '600519'
            
        Returns:
            实时行情数据字典，包含以下字段：
            - code: 股票代码
            - name: 股票名称
            - price: 最新价
            - change: 涨跌额
            - change_pct: 涨跌幅
            - prev_close: 昨收价
            - open: 今开价
            - high: 最高价
            - low: 最低价
            - volume: 成交量（手）
            - amount: 成交额（元）
            - turnover_rate: 换手率（%）
            - avg_price: 均价
            - limit_up: 涨停价
            - limit_down: 跌停价
            - quote_time: 时间戳
            - bid_prices: 买盘价格列表 [买 1，买 2，买 3，买 4，买 5]
            - ask_prices: 卖盘价格列表 [卖 1，卖 2，卖 3，卖 4，卖 5]
            - bid_volumes: 买盘数量列表 [买 1 量，买 2 量，买 3 量，买 4 量，买 5 量]
            - ask_volumes: 卖盘数量列表 [卖 1 量，卖 2 量，卖 3 量，卖 4 量，卖 5 量]
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> quote = await adapter.get_realtime_quote('600519')
            >>> print(f"贵州茅台最新价：{quote['price']}元，涨跌幅：{quote['change_pct']}%")
        """
        try:
            if not EF_AVAILABLE:
                return {}
            
            cache_key = self._get_cache_key('quote', code=code)
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                return cached
            
            # 获取实时行情快照
            series = ef.stock.get_quote_snapshot(code.zfill(6))
            
            if series is None or len(series) == 0:
                return {}
            
            # 安全转换浮点数
            def safe_float(value, default=0.0):
                try:
                    if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                        return default
                    return float(value)
                except (ValueError, TypeError):
                    return default
            
            # 安全转换整数
            def safe_int(value, default=0):
                try:
                    if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                        return default
                    return int(float(value))
                except (ValueError, TypeError):
                    return default
            
            # 获取五档买卖盘数据
            bid_prices = []
            ask_prices = []
            bid_volumes = []
            ask_volumes = []
            
            for i in range(1, 6):
                # 买盘数据
                bid_price = series.get(f'买{i}价', None)
                bid_vol = series.get(f'买{i}数量', None)
                if bid_price is not None:
                    bid_prices.append(safe_float(bid_price, 0.0))
                    bid_volumes.append(safe_int(bid_vol, 0))
                else:
                    bid_prices.append(0.0)
                    bid_volumes.append(0)
                
                # 卖盘数据
                ask_price = series.get(f'卖{i}价', None)
                ask_vol = series.get(f'卖{i}数量', None)
                if ask_price is not None:
                    ask_prices.append(safe_float(ask_price, 0.0))
                    ask_volumes.append(safe_int(ask_vol, 0))
                else:
                    ask_prices.append(0.0)
                    ask_volumes.append(0)
            
            quote = {
                'code': code,
                'name': series.get('名称', '') or '',
                'price': safe_float(series.get('最新价', 0), 0.0),
                'change': safe_float(series.get('涨跌额', 0), 0.0),
                'change_pct': safe_float(series.get('涨跌幅', 0), 0.0),
                'high': safe_float(series.get('最高', 0), 0.0),
                'low': safe_float(series.get('最低', 0), 0.0),
                'open': safe_float(series.get('今开', 0), 0.0),
                'prev_close': safe_float(series.get('昨收', 0), 0.0),
                'volume': safe_int(series.get('成交量', 0), 0),
                'amount': safe_float(series.get('成交额', 0), 0.0),
                'turnover_rate': safe_float(series.get('换手率', 0), 0.0),
                'avg_price': safe_float(series.get('均价', 0), 0.0),
                'limit_up': safe_float(series.get('涨停价', 0), 0.0),
                'limit_down': safe_float(series.get('跌停价', 0), 0.0),
                'quote_time': series.get('时间', '') or '',
                'bid_prices': bid_prices,  # [买 1, 买 2, 买 3, 买 4, 买 5]
                'ask_prices': ask_prices,  # [卖 1, 卖 2, 卖 3, 卖 4, 卖 5]
                'bid_volumes': bid_volumes,  # [买 1 量，买 2 量，买 3 量，买 4 量，买 5 量]
                'ask_volumes': ask_volumes,  # [卖 1 量，卖 2 量，卖 3 量，卖 4 量，卖 5 量]
                'bid1_price': bid_prices[0] if bid_prices[0] > 0 else None,
                'bid1_volume': bid_volumes[0] if bid_volumes[0] > 0 else None,
                'ask1_price': ask_prices[0] if ask_prices[0] > 0 else None,
                'ask1_volume': ask_volumes[0] if ask_volumes[0] > 0 else None
            }
            
            self._set_to_cache(cache_key, quote, 'quote')
            logger.info(f"获取实时行情成功 {code}: {quote['price']}元 ({quote['change_pct']}%)")
            return quote
            
        except Exception as e:
            logger.error(f"获取实时行情失败 {code}: {e}")
            return {}
    
    async def get_latest_quote(self, stock_codes: List[str]) -> List[Dict[str, Any]]:
        """
        获取沪深市场多只股票的实时涨幅情况
        
        Args:
            stock_codes: 股票代码列表，如 ['600519', '300750']
            
        Returns:
            多只股票的实时行情数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> quotes = await adapter.get_latest_quote(['600519', '300750'])
            >>> for quote in quotes:
            ...     print(f"{quote['name']}: {quote['price']}元 ({quote['change_pct']}%)")
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            if not stock_codes:
                return []
            
            # 生成缓存 key
            codes_key = '_'.join(sorted(stock_codes))
            cache_key = self._get_cache_key('latest_quote', codes=codes_key)
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                return cached
            
            # 批量获取实时行情
            df = ef.stock.get_latest_quote(stock_codes)
            
            if df.empty:
                return []
            
            quotes = []
            for row in df.itertuples(index=False):
                # 安全转换数值
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                code = str(getattr(row, '代码', '')).zfill(6)
                if not code:
                    continue
                
                quotes.append({
                    'code': code,
                    'name': getattr(row, '名称', '') or '',
                    'change_pct': safe_float(getattr(row, '涨跌幅', 0), 0.0),
                    'price': safe_float(getattr(row, '最新价', 0), 0.0),
                    'high': safe_float(getattr(row, '最高', 0), 0.0),
                    'low': safe_float(getattr(row, '最低', 0), 0.0),
                    'open': safe_float(getattr(row, '今开', 0), 0.0),
                    'change': safe_float(getattr(row, '涨跌额', 0), 0.0),
                    'turnover_rate': safe_float(getattr(row, '换手率', 0), 0.0),
                    'volume_ratio': safe_float(getattr(row, '量比', 0), 0.0),
                    'pe_ratio_dynamic': safe_float(getattr(row, '动态市盈率', 0), 0.0),
                    'volume': safe_float(getattr(row, '成交量', 0), 0.0),
                    'amount': safe_float(getattr(row, '成交额', 0), 0.0),
                    'prev_close': safe_float(getattr(row, '昨日收盘', 0), 0.0),
                    'total_market_cap': safe_float(getattr(row, '总市值', 0), 0.0),
                    'float_market_cap': safe_float(getattr(row, '流通市值', 0), 0.0),
                    'market_type': getattr(row, '市场类型', '') or '',
                    'quote_id': getattr(row, '行情 ID', '') or ''
                })
            
            self._set_to_cache(cache_key, quotes, 'quote')
            logger.info(f"批量获取实时行情成功：{len(quotes)}只")
            return quotes
            
        except Exception as e:
            logger.error(f"批量获取实时行情失败：{e}")
            return []
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        """获取板块列表"""
        try:
            if not EF_AVAILABLE:
                return []
            
            # 获取行业板块或概念板块
            if sector_type == "industry":
                fs = '行业板块'
            else:
                fs = '概念板块'
            
            df = ef.stock.get_realtime_quotes(fs)
            
            sectors = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', ''))
                name = getattr(row, '股票名称', '')
                if code and name:
                    sectors.append(SectorInfo(
                        code=code,
                        name=name,
                        sector_type=sector_type
                    ))
            
            logger.info(f"获取板块列表成功：{len(sectors)}个")
            return sectors
            
        except Exception as e:
            logger.error(f"获取板块列表失败：{e}")
            return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        """获取板块成分股"""
        try:
            if not EF_AVAILABLE:
                return []
            
            # 使用 get_belong_board 反向查询成分股
            # efinance 没有直接的板块成分股接口，这里返回空列表
            logger.warning(f"efinance 暂不支持获取板块成分股 {sector_code}")
            return []
            
        except Exception as e:
            logger.error(f"获取板块成分股失败 {sector_code}: {e}")
            return []
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        """获取筹码数据"""
        try:
            if not EF_AVAILABLE:
                return []
            
            # 获取全市场股东人数数据，然后筛选指定股票
            df = ef.stock.get_latest_holder_number()
            
            if df.empty:
                return []
            
            # 筛选指定股票
            stock_df = df[df['股票代码'] == code.zfill(6)]
            
            chip_data = []
            for row in stock_df.itertuples(index=False):
                date = str(getattr(row, '公告日期', ''))
                if len(date) >= 10:
                    date = date[:10].replace('-', '')
                
                if start_date and date < start_date.replace('-', ''):
                    continue
                if end_date and date > end_date.replace('-', ''):
                    continue
                
                chip_data.append(ChipData(
                    code=code,
                    date=date,
                    shareholder_count=float(getattr(row, '股东人数', 0) or 0)
                ))
            
            # 按日期排序
            chip_data.sort(key=lambda x: x.date)
            
            logger.info(f"获取筹码数据成功 {code}: {len(chip_data)}条")
            return chip_data
            
        except Exception as e:
            logger.error(f"获取筹码数据失败 {code}: {e}")
            return []
    
    async def get_daily_billboard(
        self, 
        start_date: Optional[str] = None, 
        end_date: Optional[str] = None
    ) -> List[BillboardEntry]:
        """
        获取指定日期区间的龙虎榜详情数据
        
        Args:
            start_date: 开始日期，格式：YYYY-MM-DD
                - None: 最新一个榜单公开日（默认）
                - "2021-08-27": 2021 年 8 月 27 日
            
            end_date: 结束日期，格式：YYYY-MM-DD
                - None: 最新一个榜单公开日（默认）
                - "2021-08-31": 2021 年 8 月 31 日
            
        Returns:
            龙虎榜详情数据列表
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> # 获取最新龙虎榜
            >>> latest = await adapter.get_daily_billboard()
            >>> # 获取指定日期区间
            >>> bills = await adapter.get_daily_billboard('2021-08-20', '2021-08-27')
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            # 生成缓存 key
            date_key = f"{start_date or 'latest'}_{end_date or 'latest'}"
            cache_key = self._get_cache_key('billboard', date=date_key)
            cached = self._get_from_cache(cache_key, 'default')
            if cached:
                return cached
            
            # 获取龙虎榜数据（支持日期范围）
            df = ef.stock.get_daily_billboard(start_date, end_date)
            
            if df.empty:
                return []
            
            entries = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', ''))
                if not code:
                    continue
                
                # 安全转换浮点数
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                code_padded = code.zfill(6)
                trade_date = str(getattr(row, '上榜日期', '') or '')
                
                entries.append(BillboardEntry(
                    code=code_padded,
                    name=getattr(row, '股票名称', '') or '',
                    close_price=safe_float(getattr(row, '收盘价', 0), 0.0),
                    change_pct=safe_float(getattr(row, '涨跌幅', 0), 0.0),
                    turnover_rate=safe_float(getattr(row, '换手率', 0), 0.0),
                    turnover_amount=safe_float(getattr(row, '市场总成交额', 0), 0.0),
                    net_amount=safe_float(getattr(row, '龙虎榜净买额', 0), 0.0),
                    buy_amount=safe_float(getattr(row, '龙虎榜买入额', 0), 0.0),
                    sell_amount=safe_float(getattr(row, '龙虎榜卖出额', 0), 0.0),
                    total_amount=safe_float(getattr(row, '龙虎榜成交额', 0), 0.0),
                    net_ratio=safe_float(getattr(row, '净买额占总成交比', 0), 0.0),
                    amount_ratio=safe_float(getattr(row, '成交额占总成交比', 0), 0.0),
                    float_market_cap=safe_float(getattr(row, '流通市值', 0), 0.0),
                    reason=getattr(row, '上榜原因', '') or '',
                    trade_date=trade_date,
                    interpretation=getattr(row, '解读', '') or ''  # 如：卖一主卖，成功率 48.36%
                ))
            
            self._set_to_cache(cache_key, entries, 'default')
            date_range = f"{start_date} 至 {end_date}" if start_date and end_date else "最新"
            logger.info(f"获取龙虎榜数据成功（{date_range}）：{len(entries)}条")
            return entries
            
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败：{e}")
            return []
    
    async def get_belong_board(self, code: str) -> List[BoardInfo]:
        """
        获取股票所属板块
        
        Args:
            code: 股票代码
            
        Returns:
            所属板块列表，包含行业板块、概念板块、地域板块、指数板块等
        
        Examples:
            >>> adapter = EFinanceAdapter()
            >>> boards = await adapter.get_belong_board('600519')
            >>> for board in boards:
            ...     print(f"{board.name} - {board.board_type} - {board.change_pct}%")
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('board', code=code)
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            # 获取股票所属板块
            df = ef.stock.get_belong_board(code.zfill(6))
            
            if df.empty:
                return []
            
            boards = []
            for row in df.itertuples(index=False):
                # 获取板块类型
                board_type_raw = getattr(row, '板块类型', '')
                if board_type_raw == '1':
                    board_type_name = '行业板块'
                elif board_type_raw == '2':
                    board_type_name = '概念板块'
                elif board_type_raw == '3':
                    board_type_name = '地域板块'
                else:
                    board_type_name = '其他'
                
                board_code = str(getattr(row, '板块代码', '')).zfill(6)
                
                boards.append(BoardInfo(
                    code=board_code,
                    name=getattr(row, '板块名称', ''),
                    board_type=board_type_name,
                    board_code=board_code,
                    close_price=float(getattr(row, '板块价格', 0) or 0),
                    change_pct=float(getattr(row, '板块涨幅', 0) or 0),
                    stock_name=getattr(row, '股票名称', ''),
                    stock_code=str(getattr(row, '股票代码', '')).zfill(6)
                ))
            
            self._set_to_cache(cache_key, boards, 'stock_info')
            logger.info(f"获取股票 {code} 所属板块成功：{len(boards)}个")
            return boards
            
        except Exception as e:
            logger.error(f"获取股票所属板块失败 {code}: {e}")
            return []
    
    async def get_members(self, index_code: str) -> List[IndexMember]:
        """
        获取指数成分股信息
        
        Args:
            index_code: 指数名称或指数代码，如 '000300' 或 '沪深 300'
            
        Returns:
            指数成分股列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('members', code=index_code)
            cached = self._get_from_cache(cache_key, 'stock_list')
            if cached:
                return cached
            
            # 获取指数成分股
            df = ef.stock.get_members(index_code)
            
            if df.empty:
                return []
            
            members = []
            for row in df.itertuples(index=False):
                # 安全转换浮点数
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                stock_code = str(getattr(row, '股票代码', '')).zfill(6)
                if not stock_code:
                    continue
                
                members.append(IndexMember(
                    index_code=str(getattr(row, '指数代码', '')).zfill(6),
                    index_name=getattr(row, '指数名称', '') or '',
                    stock_code=stock_code,
                    stock_name=getattr(row, '股票名称', '') or '',
                    weight=safe_float(getattr(row, '股票权重', None), None)
                ))
            
            self._set_to_cache(cache_key, members, 'stock_list')
            logger.info(f"获取指数 {index_code} 成分股成功：{len(members)}只")
            return members
            
        except Exception as e:
            logger.error(f"获取指数成分股失败 {index_code}: {e}")
            return []
    
    async def get_today_bill(self, trade_date: Optional[str] = None) -> List[CapitalFlowItem]:
        """获取当日资金流向
        
        Args:
            trade_date: 交易日期，格式：YYYY-MM-DD，默认今日
            
        Returns:
            资金流向数据列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('today_bill', date=trade_date)
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                return cached
            
            # 获取当日资金流向
            df = ef.stock.get_today_bill(trade_date)
            
            if df.empty:
                return []
            
            flows = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', ''))
                if not code:
                    continue
                
                flows.append(CapitalFlowItem(
                    code=code.zfill(6),
                    name=getattr(row, '股票名称', ''),
                    close_price=float(getattr(row, '最新价', 0) or 0),
                    change_pct=float(getattr(row, '涨跌幅', 0) or 0),
                    main_net_amount=float(getattr(row, '主力净流入', 0) or 0),
                    main_net_amount_rate=float(getattr(row, '主力净流入率', 0) or 0),
                    buy_elg_amount=float(getattr(row, '超大单净流入', 0) or 0),
                    buy_lg_amount=float(getattr(row, '大单净流入', 0) or 0),
                    buy_md_amount=float(getattr(row, '中单净流入', 0) or 0),
                    buy_sm_amount=float(getattr(row, '小单净流入', 0) or 0),
                    trade_date=trade_date or ''
                ))
            
            self._set_to_cache(cache_key, flows, 'quote')
            logger.info(f"获取当日资金流向成功：{len(flows)}条")
            return flows
            
        except Exception as e:
            logger.error(f"获取当日资金流向失败：{e}")
            return []
    
    async def get_history_bill(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[CapitalFlowItem]:
        """获取历史资金流向
        
        Args:
            code: 股票代码
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            
        Returns:
            历史资金流向数据列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('history_bill', code=code, start=start_date, end=end_date)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 获取历史资金流向 - efinance 只接受股票代码
            df = ef.stock.get_history_bill(code.zfill(6))
            
            if df.empty:
                return []
            
            flows = []
            for row in df.itertuples(index=False):
                date = str(getattr(row, '时间', ''))
                if len(date) == 10:
                    date = date.replace('-', '')
                
                # 根据日期范围筛选
                if start_date and date < start_date.replace('-', ''):
                    continue
                if end_date and date > end_date.replace('-', ''):
                    continue
                
                flows.append(CapitalFlowItem(
                    code=code,
                    name='',
                    close_price=float(getattr(row, '最新价', 0) or 0),
                    change_pct=float(getattr(row, '涨跌幅', 0) or 0),
                    main_net_amount=float(getattr(row, '主力净流入', 0) or 0),
                    main_net_amount_rate=float(getattr(row, '主力净流入率', 0) or 0),
                    buy_elg_amount=float(getattr(row, '超大单净流入', 0) or 0),
                    buy_lg_amount=float(getattr(row, '大单净流入', 0) or 0),
                    buy_md_amount=float(getattr(row, '中单净流入', 0) or 0),
                    buy_sm_amount=float(getattr(row, '小单净流入', 0) or 0),
                    trade_date=date
                ))
            
            # 按日期排序
            flows.sort(key=lambda x: x.trade_date)
            
            self._set_to_cache(cache_key, flows, 'kline')
            logger.info(f"获取 {code} 历史资金流向成功：{len(flows)}条")
            return flows
            
        except Exception as e:
            logger.error(f"获取历史资金流向失败 {code}: {e}")
            return []
    
    async def get_top10_stock_holder_info(self, code: str) -> List[ShareholderInfo]:
        """获取前十大股东信息
        
        Args:
            code: 股票代码
            
        Returns:
            前十大股东信息列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('shareholder', code=code)
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            # 获取前十大股东信息
            df = ef.stock.get_top10_stock_holder_info(code.zfill(6))
            
            if df.empty:
                return []
            
            def safe_parse_amount(value):
                """安全解析持股数量，支持'亿'、'万'等单位"""
                try:
                    if value is None or value == '' or value == '-':
                        return None
                    value_str = str(value)
                    if '亿' in value_str:
                        return float(value_str.replace('亿', '')) * 100000000
                    elif '万' in value_str:
                        return float(value_str.replace('万', '')) * 10000
                    else:
                        return float(value_str)
                except (ValueError, TypeError):
                    return None
            
            def safe_parse_ratio(value):
                """安全解析百分比，支持'%'符号"""
                try:
                    if value is None or value == '' or value == '-':
                        return 0.0
                    value_str = str(value)
                    if '%' in value_str:
                        return float(value_str.replace('%', ''))
                    else:
                        return float(value_str)
                except (ValueError, TypeError):
                    return 0.0
            
            shareholders = []
            for row in df.itertuples(index=False):
                shareholders.append(ShareholderInfo(
                    code=code,
                    shareholder_name=getattr(row, '股东名称', ''),
                    shareholder_type=getattr(row, '股东类型', ''),
                    hold_amount=safe_parse_amount(getattr(row, '持股数', None)),
                    hold_ratio=safe_parse_ratio(getattr(row, '持股比例', None)),
                    change_amount=safe_parse_amount(getattr(row, '持股变化', None)),
                    change_ratio=safe_parse_ratio(getattr(row, '持股变化比例', None)),
                    report_date=getattr(row, '报告期', '')
                ))
            
            self._set_to_cache(cache_key, shareholders, 'stock_info')
            logger.info(f"获取 {code} 前十大股东信息成功：{len(shareholders)}条")
            return shareholders
            
        except Exception as e:
            logger.error(f"获取前十大股东信息失败 {code}: {e}")
            return []
    
    async def get_all_company_performance(self, date: Optional[str] = None) -> List[CompanyPerformance]:
        """
        获取沪深市场股票某一季度的表现情况
        
        Args:
            date: 报告发布日期，可选
                - None: 最新季报
                - '2021-06-30': 2021 年 Q2 季度报
                - '2021-03-31': 2021 年 Q1 季度报
        
        Returns:
            公司业绩表现数据列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('performance', date=date or 'latest')
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 获取业绩表现数据
            df = ef.stock.get_all_company_performance(date)
            
            if df.empty:
                return []
            
            performances = []
            for row in df.itertuples(index=False):
                # 安全转换数值
                def safe_float(value, default=0.0):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                code = str(getattr(row, '股票代码', '')).zfill(6)
                if not code:
                    continue
                
                # 处理公告日期
                report_date_raw = getattr(row, '公告日期', '')
                if report_date_raw:
                    if isinstance(report_date_raw, str):
                        report_date = report_date_raw.split(' ')[0].replace('-', '')
                    else:
                        report_date = str(report_date_raw)[:10].replace('-', '')
                else:
                    report_date = ''
                
                performances.append(CompanyPerformance(
                    code=code,
                    name=getattr(row, '股票简称', ''),
                    report_date=report_date,
                    revenue=safe_float(getattr(row, '营业收入', 0)),
                    revenue_growth=safe_float(getattr(row, '营业收入同比增长', 0)),
                    revenue_qoq=safe_float(getattr(row, '营业收入季度环比', 0)),
                    net_profit=safe_float(getattr(row, '净利润', 0)),
                    net_profit_growth=safe_float(getattr(row, '净利润同比增长', 0)),
                    net_profit_qoq=safe_float(getattr(row, '净利润季度环比', 0)),
                    eps=safe_float(getattr(row, '每股收益', 0)),
                    bps=safe_float(getattr(row, '每股净资产', 0)),
                    roe=safe_float(getattr(row, '净资产收益率', 0)),
                    gross_margin=safe_float(getattr(row, '销售毛利率', 0)),
                    cash_flow_per_share=safe_float(getattr(row, '每股经营现金流量', 0))
                ))
            
            self._set_to_cache(cache_key, performances, 'kline')
            logger.info(f"获取公司业绩表现成功：{len(performances)}条，报告期：{date or '最新'}")
            return performances
            
        except Exception as e:
            logger.error(f"获取公司业绩表现失败：{e}")
            return []
    
    async def get_all_report_dates(self) -> List[str]:
        """
        获取所有可选的报告发布日期
        
        Returns:
            报告日期列表，格式：YYYY-MM-DD
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('report_dates')
            cached = self._get_from_cache(cache_key, 'stock_list')
            if cached:
                return cached
            
            # 获取所有报告日期
            dates = ef.stock.get_all_report_dates()
            
            if not dates:
                return []
            
            # 转换为字符串列表
            date_list = [str(d) for d in dates]
            
            self._set_to_cache(cache_key, date_list, 'stock_list')
            logger.info(f"获取报告日期列表成功：{len(date_list)}个")
            return date_list
            
        except Exception as e:
            logger.error(f"获取报告日期列表失败：{e}")
            return []
    
    async def get_market_realtime_quotes(self, market_types: Optional[List[str]] = None) -> List[MarketQuote]:
        """
        获取市场实时行情数据
        
        Args:
            market_types: 市场类型列表，可选值：
                - '沪深 A 股'（默认，不传参数）
                - '沪 A', '深 A', '北 A'
                - '创业板', '科创板'
                - 'ETF', 'LOF'
                - '行业板块', '概念板块'
                - '港股', '美股', '中概股'
                - '可转债', '期货'
                - '沪深系列指数', '上证系列指数', '深证系列指数'
        
        Returns:
            List[MarketQuote]: 市场实时行情列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            # efinance 对某些市场类型不支持，需要过滤
            # 根据 API 文档，支持的市场类型
            supported_types = [
                '沪深 A 股', '沪 A', '深 A', '北 A',  # A 股
                '创业板', '科创板',  # 板块
                'ETF', 'LOF',  # 基金
                '行业板块', '概念板块',  # 板块
                '港股', '美股', '中概股',  # 境外
                '可转债', '期货',  # 其他
                '沪深系列指数', '上证系列指数', '深证系列指数'  # 指数
            ]
            
            # 过滤市场类型
            if market_types:
                valid_types = [t for t in market_types if t in supported_types]
                if not valid_types:
                    logger.warning(f"efinance 不支持的市场类型：{market_types}，使用默认沪深 A 股")
                    # 使用默认（不传参数）
                    market_types = None
                elif len(valid_types) == 1:
                    # 单个市场类型
                    market_types = valid_types[0]
                else:
                    # 多个市场类型
                    market_types = valid_types
            else:
                # 不传参数，默认获取沪深 A 股（最稳定）
                market_types = None
            
            # 构建缓存 key
            cache_key = self._get_cache_key('market_quotes', types='_'.join(market_types) if market_types else 'all')
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                logger.debug(f"从缓存获取市场实时行情：{cache_key}")
                return cached
            
            # 调用 efinance API，添加重试机制和超时控制
            max_retries = 3
            df = None
            for attempt in range(max_retries):
                try:
                    # 添加超时控制（15 秒）
                    df = await asyncio.wait_for(
                        asyncio.get_event_loop().run_in_executor(
                            None,
                            lambda: ef.stock.get_realtime_quotes(market_types if market_types else None)
                        ),
                        timeout=15
                    )
                    break
                except asyncio.TimeoutError:
                    logger.warning(f"获取市场实时行情超时（15 秒），重试 {attempt + 1}/{max_retries}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(2)  # 等待 2 秒后重试
                    else:
                        raise
                except Exception as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"获取市场实时行情失败，重试 {attempt + 1}/{max_retries}: {e}")
                        await asyncio.sleep(1)  # 等待 1 秒后重试
                    else:
                        raise
            
            if df is None or df.empty:
                logger.warning(f"efinance 返回空数据：{market_types}")
                return []
            
            quotes = []
            for row in df.itertuples(index=False):
                # 安全转换浮点数
                def safe_float(value, default=None):
                    try:
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and str(value) == 'nan'):
                            return default
                        return float(value)
                    except (ValueError, TypeError):
                        return default
                
                code = str(getattr(row, '股票代码', '')).zfill(6)
                if not code:
                    continue
                
                quotes.append(MarketQuote(
                    code=code,
                    name=getattr(row, '股票名称', ''),
                    change_pct=safe_float(getattr(row, '涨跌幅', None)),
                    price=safe_float(getattr(row, '最新价', None)),
                    high=safe_float(getattr(row, '最高', None)),
                    low=safe_float(getattr(row, '最低', None)),
                    open=safe_float(getattr(row, '今开', None)),
                    change=safe_float(getattr(row, '涨跌额', None)),
                    turnover_rate=safe_float(getattr(row, '换手率', None)),
                    volume_ratio=safe_float(getattr(row, '量比', None)),
                    pe_ratio=safe_float(getattr(row, '动态市盈率', None)),
                    volume=safe_float(getattr(row, '成交量', None)),
                    amount=safe_float(getattr(row, '成交额', None)),
                    prev_close=safe_float(getattr(row, '昨日收盘', None)),
                    total_market_cap=safe_float(getattr(row, '总市值', None)),
                    float_market_cap=safe_float(getattr(row, '流通市值', None)),
                    market_type=getattr(row, '市场类型', None)
                ))
            
            # 保存到缓存（5 分钟）
            self._set_to_cache(cache_key, quotes, 'quote')
            logger.info(f"获取市场实时行情成功：{len(quotes)}条，市场类型：{market_types or '沪深 A 股（默认）'}")
            return quotes
            
        except asyncio.TimeoutError:
            logger.error(f"获取市场实时行情超时（15 秒）：{market_types}")
            return []
        except Exception as e:
            logger.error(f"获取市场实时行情失败：{e}")
            # 降级策略：尝试使用默认市场类型（沪深 A 股）
            if market_types is not None:
                logger.warning(f"尝试使用默认市场类型（沪深 A 股）重试...")
                try:
                    return await self.get_market_realtime_quotes(None)
                except Exception as fallback_error:
                    logger.error(f"使用默认市场类型重试失败：{fallback_error}")
            return []
