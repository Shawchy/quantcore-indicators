import asyncio
from typing import Optional, List, Dict, Any
from loguru import logger
from pydantic import BaseModel

try:
    import efinance as ef
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
    ChipData
)
from app.models.schemas import (
    BillboardEntry,
    BoardInfo,
    ShareholderInfo,
    IndexComponent,
    CapitalFlowItem
)
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
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """获取 K 线数据"""
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('kline', code=code, start=start_date, end=end_date, adjust=adjust)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 获取 K 线数据
            # period: 1 分钟=1, 5 分钟=5, 15 分钟=15, 30 分钟=30, 60 分钟=60, 日=101, 周=102, 月=103
            period = 101  # 日线
            
            # efinance 直接传股票代码即可，会自动识别市场
            df = ef.stock.get_quote_history(
                code.zfill(6),
                period=period,
                beg=start_date.replace('-', '') if start_date else '19000101',
                end=end_date.replace('-', '') if end_date else '20500101'
            )
            
            if df.empty:
                return []
            
            klines = []
            prev_close = None
            for row in df.itertuples(index=False):
                # 获取日期字段（可能是 '时间'、'日期' 等）
                date_raw = str(getattr(row, '时间', getattr(row, '日期', '')))
                
                # 处理日期格式
                if not date_raw or date_raw == '':
                    logger.warning(f"K 线数据日期为空：{code}")
                    continue
                
                # 统一格式为 YYYYMMDD
                if len(date_raw) == 10 and '-' in date_raw:  # 2024-01-15
                    date = date_raw.replace('-', '')
                elif len(date_raw) == 8:  # 20240115
                    date = date_raw
                else:
                    logger.warning(f"K 线数据日期格式异常：{date_raw}")
                    continue
                
                current_close = float(getattr(row, '收盘', 0) or 0)
                klines.append(KLineData(
                    code=code,
                    date=date,
                    open=float(getattr(row, '开盘', 0) or 0),
                    high=float(getattr(row, '最高', 0) or 0),
                    low=float(getattr(row, '最低', 0) or 0),
                    close=current_close,
                    volume=float(getattr(row, '成交量', 0) or 0),
                    amount=float(getattr(row, '成交额', 0) or 0),
                    turnover_rate=float(getattr(row, '换手率', 0) or 0),
                    pre_close=prev_close  # 上一日的收盘价
                ))
                prev_close = current_close
            
            # 按日期排序
            klines.sort(key=lambda x: x.date)
            
            self._set_to_cache(cache_key, klines, 'kline')
            logger.info(f"获取 K 线数据成功 {code}: {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.error(f"获取 K 线数据失败 {code}: {e}")
            return []
    
    @api_call_cache(ttl=1800)  # 缓存 30 分钟
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """获取周 K 线数据（带重试机制）"""
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('kline_weekly', code=code, start=start_date, end=end_date, adjust=adjust)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # period: 周=102
            period = 102
            
            # 重试机制：最多重试 3 次
            df = None
            for attempt in range(3):
                try:
                    df = ef.stock.get_quote_history(
                        code.zfill(6),
                        period=period,
                        beg=start_date.replace('-', '') if start_date else '19000101',
                        end=end_date.replace('-', '') if end_date else '20500101'
                    )
                    break  # 成功则跳出
                except Exception as retry_error:
                    if attempt < 2:
                        logger.debug(f"获取周 K 线数据失败，重试 {attempt+1}/3: {retry_error}")
                        await asyncio.sleep(0.5 * (attempt + 1))  # 递增延迟
                    else:
                        raise retry_error
            
            if df is None or df.empty:
                return []
            
            klines = []
            prev_close = None
            for row in df.itertuples(index=False):
                date_raw = str(getattr(row, '时间', getattr(row, '日期', '')))
                
                if not date_raw or date_raw == '':
                    logger.warning(f"周 K 线数据日期为空：{code}")
                    continue
                
                if len(date_raw) == 10 and '-' in date_raw:
                    date = date_raw.replace('-', '')
                elif len(date_raw) == 8:
                    date = date_raw
                else:
                    logger.warning(f"周 K 线数据日期格式异常：{date_raw}")
                    continue
                
                current_close = float(getattr(row, '收盘', 0) or 0)
                klines.append(KLineData(
                    code=code,
                    date=date,
                    open=float(getattr(row, '开盘', 0) or 0),
                    high=float(getattr(row, '最高', 0) or 0),
                    low=float(getattr(row, '最低', 0) or 0),
                    close=current_close,
                    volume=float(getattr(row, '成交量', 0) or 0),
                    amount=float(getattr(row, '成交额', 0) or 0),
                    turnover_rate=float(getattr(row, '换手率', 0) or 0),
                    pre_close=prev_close  # 上一周的收盘价
                ))
                prev_close = current_close
            
            klines.sort(key=lambda x: x.date)
            self._set_to_cache(cache_key, klines, 'kline')
            logger.info(f"获取周 K 线数据成功 {code}: {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.warning(f"获取周 K 线数据失败 {code}（网络不稳定）: {e}")
            return []
    
    @api_call_cache(ttl=1800)  # 缓存 30 分钟
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """获取月 K 线数据（带重试机制）"""
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('kline_monthly', code=code, start=start_date, end=end_date, adjust=adjust)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # period: 月=103
            period = 103
            
            # 重试机制：最多重试 3 次
            df = None
            for attempt in range(3):
                try:
                    df = ef.stock.get_quote_history(
                        code.zfill(6),
                        period=period,
                        beg=start_date.replace('-', '') if start_date else '19000101',
                        end=end_date.replace('-', '') if end_date else '20500101'
                    )
                    break  # 成功则跳出
                except Exception as retry_error:
                    if attempt < 2:
                        logger.debug(f"获取月 K 线数据失败，重试 {attempt+1}/3: {retry_error}")
                        await asyncio.sleep(0.5 * (attempt + 1))
                    else:
                        raise retry_error
            
            if df is None or df.empty:
                return []
            
            klines = []
            prev_close = None
            for row in df.itertuples(index=False):
                date_raw = str(getattr(row, '时间', getattr(row, '日期', '')))
                
                if not date_raw or date_raw == '':
                    logger.warning(f"月 K 线数据日期为空：{code}")
                    continue
                
                if len(date_raw) == 10 and '-' in date_raw:
                    date = date_raw.replace('-', '')
                elif len(date_raw) == 8:
                    date = date_raw
                else:
                    logger.warning(f"月 K 线数据日期格式异常：{date_raw}")
                    continue
                
                current_close = float(getattr(row, '收盘', 0) or 0)
                klines.append(KLineData(
                    code=code,
                    date=date,
                    open=float(getattr(row, '开盘', 0) or 0),
                    high=float(getattr(row, '最高', 0) or 0),
                    low=float(getattr(row, '最低', 0) or 0),
                    close=current_close,
                    volume=float(getattr(row, '成交量', 0) or 0),
                    amount=float(getattr(row, '成交额', 0) or 0),
                    turnover_rate=float(getattr(row, '换手率', 0) or 0),
                    pre_close=prev_close  # 上一月的收盘价
                ))
                prev_close = current_close
            
            klines.sort(key=lambda x: x.date)
            self._set_to_cache(cache_key, klines, 'kline')
            logger.info(f"获取月 K 线数据成功 {code}: {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.warning(f"获取月 K 线数据失败 {code}（网络不稳定）: {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        """获取实时行情"""
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
            
            quote = {
                'code': code,
                'name': series.get('名称', ''),
                'price': float(series.get('最新价', 0) or 0),
                'change': float(series.get('涨跌额', 0) or 0),
                'change_pct': float(series.get('涨跌幅', 0) or 0),
                'high': float(series.get('最高', 0) or 0),
                'low': float(series.get('最低', 0) or 0),
                'open': float(series.get('今开', 0) or 0),
                'prev_close': float(series.get('昨收', 0) or 0),
                'volume': float(series.get('成交量', 0) or 0),
                'amount': float(series.get('成交额', 0) or 0),
                'turnover_rate': float(series.get('换手率', 0) or 0),
                'quote_time': series.get('时间', '')
            }
            
            self._set_to_cache(cache_key, quote, 'quote')
            logger.debug(f"获取实时行情成功 {code}: {quote['price']}")
            return quote
            
        except Exception as e:
            logger.error(f"获取实时行情失败 {code}: {e}")
            return {}
    
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
    
    async def get_daily_billboard(self, trade_date: Optional[str] = None) -> List[BillboardEntry]:
        """获取龙虎榜单数据
        
        Args:
            trade_date: 交易日期，格式：YYYY-MM-DD，默认今日
            
        Returns:
            龙虎榜单数据列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('billboard', date=trade_date)
            cached = self._get_from_cache(cache_key, 'default')
            if cached:
                return cached
            
            # 获取龙虎榜数据
            df = ef.stock.get_daily_billboard(trade_date)
            
            if df.empty:
                return []
            
            entries = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', ''))
                if not code:
                    continue
                
                entries.append(BillboardEntry(
                    code=code.zfill(6),
                    name=getattr(row, '股票名称', ''),
                    close_price=float(getattr(row, '收盘价', 0) or 0),
                    change_pct=float(getattr(row, '涨跌幅', 0) or 0),
                    turnover_amount=float(getattr(row, '成交额', 0) or 0),
                    net_amount=float(getattr(row, '净流入额', 0) or 0),
                    buy_amount=float(getattr(row, '买入额', 0) or 0),
                    sell_amount=float(getattr(row, '卖出额', 0) or 0),
                    reason=getattr(row, '上榜原因', ''),
                    trade_date=trade_date or ''
                ))
            
            self._set_to_cache(cache_key, entries, 'default')
            logger.info(f"获取龙虎榜数据成功：{len(entries)}条")
            return entries
            
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败：{e}")
            return []
    
    async def get_belong_board(self, code: str) -> List[BoardInfo]:
        """获取股票所属板块
        
        Args:
            code: 股票代码
            
        Returns:
            所属板块列表
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
                board_type = getattr(row, '板块类型', '')
                if board_type == '1':
                    board_type_name = '行业板块'
                elif board_type == '2':
                    board_type_name = '概念板块'
                elif board_type == '3':
                    board_type_name = '地域板块'
                else:
                    board_type_name = '其他'
                
                boards.append(BoardInfo(
                    code=str(getattr(row, '板块代码', '')).zfill(6),
                    name=getattr(row, '板块名称', ''),
                    board_type=board_type_name,
                    close_price=float(getattr(row, '板块价格', 0) or 0),
                    change_pct=float(getattr(row, '板块涨跌幅', 0) or 0)
                ))
            
            self._set_to_cache(cache_key, boards, 'stock_info')
            logger.info(f"获取股票 {code} 所属板块成功：{len(boards)}个")
            return boards
            
        except Exception as e:
            logger.error(f"获取股票所属板块失败 {code}: {e}")
            return []
    
    async def get_members(self, index_code: str) -> List[IndexComponent]:
        """获取指数成分股
        
        Args:
            index_code: 指数代码
            
        Returns:
            成分股列表
        """
        try:
            if not EF_AVAILABLE:
                return []
            
            cache_key = self._get_cache_key('members', code=index_code)
            cached = self._get_from_cache(cache_key, 'sector')
            if cached:
                return cached
            
            # 获取指数成分股
            df = ef.stock.get_members(index_code)
            
            if df.empty:
                return []
            
            components = []
            for row in df.itertuples(index=False):
                code = str(getattr(row, '股票代码', ''))
                if not code:
                    continue
                
                components.append(IndexComponent(
                    code=code.zfill(6),
                    name=getattr(row, '股票名称', ''),
                    weight=float(getattr(row, '权重', 0) or 0),
                    industry=getattr(row, '行业', '')
                ))
            
            self._set_to_cache(cache_key, components, 'sector')
            logger.info(f"获取指数 {index_code} 成分股成功：{len(components)}只")
            return components
            
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
