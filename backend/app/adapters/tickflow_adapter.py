"""
TickFlow 数据源适配器

TickFlow 是一个金融数据服务，提供 A 股、港股、美股等市场的实时行情和历史数据
官网：https://tickflow.tech

特点：
- 免费服务：提供日 K 线数据和标的信息（无需注册）
- 完整服务：需注册获取 API Key，提供实时行情、分钟级 K 线等
- 支持 Python 3.9+
- 数据更新及时，接口简洁

安装：
    pip install "tickflow[all]" --upgrade

使用示例：
    # 免费服务
    tf = TickFlow.free()
    df = tf.klines.get("600000.SH", period="1d", count=100, as_dataframe=True)
    
    # 完整服务
    tf = TickFlow(api_key="your-api-key")
    quotes = tf.quotes.get(symbols=["600000.SH", "000001.SZ"])
"""
import asyncio
from typing import Optional, List, Dict, Any, Union
from loguru import logger

try:
    from tickflow import TickFlow
    TICKFLOW_AVAILABLE = True
except ImportError:
    TICKFLOW_AVAILABLE = False
    logger.warning("tickflow 未安装，请运行：pip install 'tickflow[all]' --upgrade")

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData,
)
from app.models.schemas import (
    BillboardEntry,
    BoardInfo,
    ShareholderInfo,
    IndexComponent,
    CapitalFlowItem,
)
from app.config import settings
from .exchange_storage import exchange_storage


class TickFlowAdapter(BaseDataAdapter):
    """TickFlow 数据源适配器
    
    TickFlow 提供高质量的金融数据服务，包括：
    - 实时行情（完整服务）
    - 历史 K 线（免费和完整服务）
    - 标的信息
    - 交易所、标的池查询
    
    注意：
    - 免费服务仅提供日 K 线（1d、1w、1M、1Q、1Y）和标的信息
    - 完整服务需要 API Key，提供实时行情和分钟级 K 线
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._is_initialized = False
        self._tf: Optional[TickFlow] = None
        
        # 内存缓存
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Dict[str, float] = {}
        # 不同数据的缓存时间（秒）
        self._cache_ttl = {
            'kline': 300,        # K 线：5 分钟
            'stock_list': 3600,  # 股票列表：1 小时
            'stock_info': 600,   # 股票信息：10 分钟
            'quote': 10,         # 实时行情：10 秒（TickFlow 更新快）
            'sector': 300,       # 板块：5 分钟
            'instruments': 3600, # 标的信息：1 小时
            'default': 300       # 默认：5 分钟
        }
        
        # API Key 配置
        self._api_key = config.get('api_key') if config else None
        if not self._api_key:
            self._api_key = getattr(settings, 'TICKFLOW_API_KEY', None)
        
        # 是否使用免费服务
        self._use_free_service = not self._api_key
    
    async def initialize(self) -> bool:
        """初始化 TickFlow 客户端"""
        if self._is_initialized:
            return True
        
        try:
            if not TICKFLOW_AVAILABLE:
                logger.error("tickflow 库未安装")
                return False
            
            # 根据是否有 API Key 决定使用免费服务还是完整服务
            if self._api_key:
                self._tf = TickFlow(api_key=self._api_key)
                logger.info(f"TickFlow 初始化成功（完整服务）")
            else:
                self._tf = TickFlow.free()
                logger.info("TickFlow 初始化成功（免费服务）")
            
            self._is_initialized = True
            
            # 测试连接
            try:
                await self._test_connection()
            except Exception as e:
                logger.warning(f"TickFlow 连接测试失败：{e}")
                # 不返回 False，因为可能是网络临时问题
            
            return True
            
        except Exception as e:
            logger.error(f"TickFlow 初始化失败：{e}")
            return False
    
    async def _test_connection(self) -> None:
        """测试 TickFlow 连接"""
        try:
            # 尝试获取一个标的信息
            instruments = self._tf.instruments.get(symbols=["600000.SH"])
            if instruments:
                logger.debug(f"TickFlow 连接测试成功：{instruments[0].symbol}")
            else:
                logger.debug("TickFlow 连接测试成功（无数据）")
        except Exception as e:
            logger.debug(f"TickFlow 连接测试异常：{e}")
            raise
    
    def _get_from_cache(self, key: str, data_type: str = 'default') -> Optional[Any]:
        """从缓存获取数据"""
        if key in self._cache:
            timestamp = self._cache_timestamp.get(key, 0)
            ttl = self._cache_ttl.get(data_type, self._cache_ttl['default'])
            
            if (time.time() - timestamp) < ttl:
                return self._cache[key]
            else:
                # 缓存过期
                del self._cache[key]
        
        return None
    
    def _set_to_cache(self, key: str, data: Any, data_type: str = 'default') -> None:
        """设置缓存"""
        import time
        self._cache[key] = data
        self._cache_timestamp[key] = time.time()
    
    def _symbol_to_tickflow(self, code: str) -> str:
        """
        将股票代码转换为 TickFlow 格式
        
        TickFlow 格式：代码。市场
        示例：
        - 600000.SH (上交所)
        - 000001.SZ (深交所)
        - 00700.HK (港股)
        
        Args:
            code: 6 位股票代码
        
        Returns:
            TickFlow 格式的股票代码
        """
        code = code.strip().zfill(6)
        
        # 根据代码前缀判断市场
        if code.startswith('6'):
            return f"{code}.SH"
        elif code.startswith('0') or code.startswith('3'):
            return f"{code}.SZ"
        else:
            # 默认深交所
            return f"{code}.SZ"
    
    def _symbol_from_tickflow(self, symbol: str) -> str:
        """
        将 TickFlow 格式转换为标准股票代码
        
        Args:
            symbol: TickFlow 格式的股票代码（如：600000.SH）
        
        Returns:
            6 位股票代码
        """
        if '.' in symbol:
            return symbol.split('.')[0]
        return symbol.zfill(6)
    
    async def close(self) -> None:
        """关闭 TickFlow 客户端"""
        self._tf = None
        self._is_initialized = False
        logger.info("TickFlow 已关闭")
    
    @property
    def is_free_service(self) -> bool:
        """是否使用免费服务"""
        return self._use_free_service
    
    async def get_stock_list(self) -> List[StockBasicInfo]:
        """获取股票列表"""
        try:
            if not self._tf:
                return []
            
            cache_key = 'tickflow_stock_list'
            cached = self._get_from_cache(cache_key, 'stock_list')
            if cached:
                return cached
            
            # TickFlow 没有直接获取全部股票列表的接口
            # 可以通过获取标的池信息来实现
            # 这里返回空列表，建议使用其他数据源获取股票列表
            logger.warning("TickFlow 不支持获取全部股票列表")
            return []
            
        except Exception as e:
            logger.error(f"TickFlow 获取股票列表失败：{e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        """获取股票信息"""
        try:
            if not self._tf:
                return None
            
            symbol = self._symbol_to_tickflow(code)
            cache_key = f'tickflow_stock_info_{symbol}'
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            # 获取标的信息
            instruments = self._tf.instruments.get(symbols=[symbol])
            
            if not instruments or len(instruments) == 0:
                return None
            
            inst = instruments[0]
            
            # 解析数据
            stock_info = StockBasicInfo(
                code=code,
                name=getattr(inst, 'name', ''),
                market=getattr(inst, 'exchange', ''),
                industry=getattr(inst, 'industry', None),
                sector=getattr(inst, 'sector', None),
                area=getattr(inst, 'area', None),
                list_date=getattr(inst, 'list_date', None),
                total_shares=getattr(inst, 'total_shares', None),
                float_shares=getattr(inst, 'float_shares', None),
            )
            
            self._set_to_cache(cache_key, stock_info, 'stock_info')
            logger.info(f"TickFlow 获取股票信息成功：{code}")
            return stock_info
            
        except Exception as e:
            logger.error(f"TickFlow 获取股票信息失败 {code}: {e}")
            return None
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        period: str = 'daily'
    ) -> List[KLineData]:
        """
        获取 K 线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期，格式：YYYY-MM-DD
            end_date: 结束日期，格式：YYYY-MM-DD
            adjust: 复权方式（TickFlow 暂不支持）
            period: K 线周期
                - 'daily': 日线
                - 'weekly': 周线
                - 'monthly': 月线
                - '1m', '5m', '15m', '30m', '60m': 分钟线（需要完整服务）
        
        Returns:
            K 线数据列表
        """
        try:
            if not self._tf:
                return []
            
            symbol = self._symbol_to_tickflow(code)
            cache_key = f'tickflow_kline_{symbol}_{period}_{start_date}_{end_date}'
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 周期映射
            period_map = {
                'daily': '1d',
                'weekly': '1w',
                'monthly': '1M',
                'quarterly': '1Q',
                'yearly': '1Y',
                '1m': '1m',
                '5m': '5m',
                '15m': '15m',
                '30m': '30m',
                '60m': '60m',
            }
            
            tf_period = period_map.get(period, '1d')
            
            # 检查免费服务的限制
            if self._use_free_service and tf_period in ['1m', '5m', '15m', '30m', '60m']:
                logger.warning(f"TickFlow 免费服务不支持分钟级 K 线：{tf_period}")
                return []
            
            # 获取 K 线数据
            # TickFlow 支持通过 count 或 start_time/end_time 获取数据
            df = self._tf.klines.get(
                symbol,
                period=tf_period,
                count=1000,  # 默认获取 1000 条
                as_dataframe=True
            )
            
            if df is None or df.empty:
                logger.warning(f"TickFlow K 线数据为空：{code} (period={period})")
                return []
            
            # 解析数据
            klines = []
            prev_close = None
            
            for _, row in df.iterrows():
                date_str = str(row.get('time', ''))
                
                # 日期格式转换（TickFlow 返回的可能是时间戳或字符串）
                if len(date_str) > 10:
                    # 可能是时间戳或带时间的日期
                    date = date_str[:10].replace('-', '')
                else:
                    date = date_str.replace('-', '')
                
                current_close = float(row.get('close', 0))
                
                kline = KLineData(
                    code=code,
                    date=date,
                    open=float(row.get('open', 0)),
                    high=float(row.get('high', 0)),
                    low=float(row.get('low', 0)),
                    close=current_close,
                    volume=float(row.get('volume', 0)),
                    amount=float(row.get('amount', 0)) if 'amount' in row else None,
                    turnover_rate=float(row.get('turnover_rate', 0)) if 'turnover_rate' in row else None,
                    pre_close=prev_close
                )
                klines.append(kline)
                prev_close = current_close
            
            # 按日期排序
            klines.sort(key=lambda x: x.date)
            
            # 日期过滤
            if start_date or end_date:
                klines = [
                    k for k in klines
                    if (not start_date or k.date >= start_date.replace('-', '')) and
                       (not end_date or k.date <= end_date.replace('-', ''))
                ]
            
            self._set_to_cache(cache_key, klines, 'kline')
            logger.info(f"TickFlow 获取 K 线数据成功 {code} ({period}): {len(klines)}条")
            return klines
            
        except Exception as e:
            logger.error(f"TickFlow 获取 K 线数据失败 {code} (period={period}): {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        """
        获取实时行情
        
        Args:
            code: 股票代码
        
        Returns:
            实时行情数据字典
        
        Note:
            免费服务不支持实时行情
        """
        try:
            if not self._tf:
                return {}
            
            if self._use_free_service:
                logger.warning("TickFlow 免费服务不支持实时行情")
                return {}
            
            symbol = self._symbol_to_tickflow(code)
            cache_key = f'tickflow_quote_{symbol}'
            cached = self._get_from_cache(cache_key, 'quote')
            if cached:
                return cached
            
            # 获取实时行情
            quotes = self._tf.quotes.get(symbols=[symbol])
            
            if not quotes or len(quotes) == 0:
                return {}
            
            quote = quotes[0]
            
            # 解析数据
            result = {
                'code': code,
                'name': quote.get('name', ''),
                'price': quote.get('last_price', 0),
                'change': quote.get('change', 0),
                'change_pct': quote.get('change_percent', 0),
                'open': quote.get('open', 0),
                'high': quote.get('high', 0),
                'low': quote.get('low', 0),
                'prev_close': quote.get('prev_close', 0),
                'volume': quote.get('volume', 0),
                'amount': quote.get('amount', 0),
                'bid': quote.get('bid', 0),
                'ask': quote.get('ask', 0),
                'bid_volume': quote.get('bid_volume', 0),
                'ask_volume': quote.get('ask_volume', 0),
                'total_market_cap': quote.get('total_market_cap', 0),
                'float_market_cap': quote.get('float_market_cap', 0),
                'pe_ratio': quote.get('pe_ratio', 0),
                'pb_ratio': quote.get('pb_ratio', 0),
                'turnover_rate': quote.get('turnover_rate', 0),
                'volume_ratio': quote.get('volume_ratio', 0),
            }
            
            self._set_to_cache(cache_key, result, 'quote')
            logger.info(f"TickFlow 获取实时行情成功：{code}")
            return result
            
        except Exception as e:
            logger.error(f"TickFlow 获取实时行情失败 {code}: {e}")
            return {}
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        """
        获取板块列表
        
        Note:
            TickFlow 暂不支持板块列表查询
        """
        logger.warning("TickFlow 不支持板块列表查询")
        return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        """
        获取板块成分股
        
        Note:
            TickFlow 暂不支持板块成分股查询
        """
        logger.warning("TickFlow 不支持板块成分股查询")
        return []
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        """
        获取股东人数（筹码）数据
        
        Note:
            TickFlow 暂不支持筹码数据
        """
        logger.warning("TickFlow 不支持筹码数据查询")
        return []
    
    async def get_daily_billboard(
        self,
        trade_date: Optional[str] = None
    ) -> List[BillboardEntry]:
        """
        获取龙虎榜单数据
        
        Note:
            TickFlow 暂不支持龙虎榜数据
        """
        logger.warning("TickFlow 不支持龙虎榜数据查询")
        return []
    
    async def get_belong_board(self, code: str) -> List[BoardInfo]:
        """
        获取股票所属板块
        
        Note:
            TickFlow 暂不支持所属板块查询
        """
        logger.warning("TickFlow 不支持所属板块查询")
        return []
    
    async def get_members(self, index_code: str) -> List[IndexComponent]:
        """
        获取指数成分股
        
        Note:
            TickFlow 暂不支持指数成分股查询
        """
        logger.warning("TickFlow 不支持指数成分股查询")
        return []
    
    async def get_today_bill(
        self,
        trade_date: Optional[str] = None
    ) -> List[CapitalFlowItem]:
        """
        获取当日资金流向
        
        Note:
            TickFlow 暂不支持资金流向数据
        """
        logger.warning("TickFlow 不支持资金流向数据查询")
        return []
    
    async def get_history_bill(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[CapitalFlowItem]:
        """
        获取历史资金流向
        
        Note:
            TickFlow 暂不支持历史资金流向数据
        """
        logger.warning("TickFlow 不支持历史资金流向数据查询")
        return []
    
    async def get_top10_stock_holder_info(
        self,
        code: str
    ) -> List[ShareholderInfo]:
        """
        获取前十大股东信息
        
        Note:
            TickFlow 暂不支持股东信息查询
        """
        logger.warning("TickFlow 不支持股东信息查询")
        return []
    
    async def get_market_realtime_quotes(
        self,
        market_types: Optional[List[str]] = None
    ) -> List[Any]:
        """
        获取市场实时行情
        
        Note:
            TickFlow 不支持批量市场实时行情
        """
        logger.warning("TickFlow 不支持批量市场实时行情")
        return []
    
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """获取周线 K 线数据"""
        return await self.get_kline(code, start_date, end_date, adjust, period='weekly')
    
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """获取月线 K 线数据"""
        return await self.get_kline(code, start_date, end_date, adjust, period='monthly')
    
    async def get_instruments(self, symbols: List[str]) -> List[Dict[str, Any]]:
        """
        批量获取标的信息
        
        Args:
            symbols: TickFlow 格式的代码列表（如：["600000.SH", "000001.SZ"]）
        
        Returns:
            标的信息列表
        """
        try:
            if not self._tf:
                return []
            
            instruments = self._tf.instruments.get(symbols=symbols)
            
            if not instruments:
                return []
            
            result = []
            for inst in instruments:
                result.append({
                    'symbol': getattr(inst, 'symbol', ''),
                    'name': getattr(inst, 'name', ''),
                    'exchange': getattr(inst, 'exchange', ''),
                    'type': getattr(inst, 'type', ''),
                    'industry': getattr(inst, 'industry', ''),
                    'list_date': getattr(inst, 'list_date', ''),
                })
            
            return result
            
        except Exception as e:
            logger.error(f"TickFlow 获取标的信息失败：{e}")
            return []
    
    async def get_exchanges(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        获取交易所列表（支持持久化存储）
        
        Args:
            force_refresh: 是否强制刷新，忽略缓存和持久化数据
        
        Returns:
            交易所列表，每项包含：
            - exchange: 交易所代码（如：SH, SZ）
            - region: 所属地区（如：CN）
            - count: 标的数量
        """
        try:
            # 1. 检查是否需要强制刷新
            if not force_refresh:
                # 2. 尝试从持久化存储加载
                logger.debug("尝试从持久化存储加载交易所数据...")
                data = exchange_storage.load_exchanges()
                if data:
                    exchanges = data.get('exchanges', [])
                    metadata = data.get('metadata', {})
                    logger.info(
                        f"✅ 从持久化存储加载交易所数据成功:\n"
                        f"   来源：{metadata.get('source', 'unknown')}\n"
                        f"   更新时间：{metadata.get('update_time', 'unknown')}\n"
                        f"   交易所数量：{len(exchanges)}"
                    )
                    # 同时保存到内存缓存
                    cache_key = 'tickflow_exchanges'
                    self._set_to_cache(cache_key, exchanges, 'instruments')
                    return exchanges
            
            # 3. 持久化数据不存在或已过期，从 API 获取
            if not self._tf:
                logger.warning("TickFlow 未初始化")
                return []
            
            cache_key = 'tickflow_exchanges'
            cached = self._get_from_cache(cache_key, 'instruments')
            if cached and not force_refresh:
                logger.info("从内存缓存获取交易所数据")
                return cached
            
            logger.info("从 TickFlow API 获取交易所数据...")
            
            # 4. 从 TickFlow SDK 获取
            if hasattr(self._tf, 'exchanges') and self._tf.exchanges is not None:
                # 使用 list() 方法获取交易所列表
                if hasattr(self._tf.exchanges, 'list'):
                    exchanges = self._tf.exchanges.list()
                elif hasattr(self._tf.exchanges, 'get'):
                    exchanges = self._tf.exchanges.get()
                else:
                    logger.warning("TickFlow exchanges 对象没有 list() 或 get() 方法")
                    exchanges = None
                
                if exchanges:
                    result = []
                    for exc in exchanges:
                        result.append({
                            'exchange': getattr(exc, 'exchange', getattr(exc, 'code', '')),
                            'region': getattr(exc, 'region', getattr(exc, 'country', '')),
                            'count': getattr(exc, 'count', 0),
                        })
                    
                    # 保存到内存缓存
                    self._set_to_cache(cache_key, result, 'instruments')
                    
                    # 保存到持久化存储（7 天有效期）
                    exchange_storage.save_exchanges(result, source='tickflow', expiry_days=7)
                    
                    logger.info(f"✅ TickFlow 获取交易所列表成功：{len(result)}个")
                    return result
            else:
                # 如果没有 exchanges API，尝试从 instruments 推断
                logger.debug("TickFlow 没有直接的 exchanges API，尝试从标的信息推断")
                
                # 获取一些样本来推断交易所
                sample_instruments = self._tf.instruments.get()
                if sample_instruments:
                    exchange_stats = {}
                    for inst in sample_instruments:
                        exc = getattr(inst, 'exchange', '')
                        if exc:
                            if exc not in exchange_stats:
                                exchange_stats[exc] = 0
                            exchange_stats[exc] += 1
                    
                    result = [
                        {
                            'exchange': exc,
                            'region': 'CN' if exc in ['SH', 'SZ'] else 'UNKNOWN',
                            'count': count
                        }
                        for exc, count in exchange_stats.items()
                    ]
                    
                    # 保存到缓存和持久化存储
                    self._set_to_cache(cache_key, result, 'instruments')
                    exchange_storage.save_exchanges(result, source='tickflow_inferred', expiry_days=7)
                    
                    logger.info(f"TickFlow 推断交易所列表成功：{len(result)}个")
                    return result
            
            return []
            
        except Exception as e:
            logger.error(f"TickFlow 获取交易所列表失败：{e}")
            return []
    
    async def get_exchange_instruments(
        self, 
        exchange: str,
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        获取交易所的标的列表（支持持久化存储）
        
        Args:
            exchange: 交易所代码（如：SH, SZ, SHFE 等）
            force_refresh: 是否强制刷新，忽略缓存和持久化数据
        
        Returns:
            标的列表，每项包含：
            - code: 标的代码
            - exchange: 交易所代码
            - region: 所属地区
            - symbol: TickFlow 格式代码
            - name: 标的名称
            - type: 标的类型（stock, fund, bond 等）
            - ext: 扩展信息（股本、上市日期等）
        """
        try:
            # 1. 检查是否需要强制刷新
            if not force_refresh:
                # 2. 尝试从持久化存储加载
                logger.debug(f"尝试从持久化存储加载交易所 {exchange} 的标的列表...")
                data = exchange_storage.load_exchange_instruments(exchange)
                if data:
                    instruments = data.get('instruments', [])
                    metadata = data.get('metadata', {})
                    logger.info(
                        f"✅ 从持久化存储加载 {exchange} 标的列表成功:\n"
                        f"   来源：{metadata.get('source', 'unknown')}\n"
                        f"   更新时间：{metadata.get('update_time', 'unknown')}\n"
                        f"   标的数量：{len(instruments)}"
                    )
                    # 同时保存到内存缓存
                    cache_key = f'tickflow_instruments_{exchange}'
                    self._set_to_cache(cache_key, instruments, 'instruments')
                    return instruments
            
            # 3. 持久化数据不存在或已过期，从 API 获取
            if not self._tf:
                logger.warning("TickFlow 未初始化")
                return []
            
            cache_key = f'tickflow_instruments_{exchange}'
            cached = self._get_from_cache(cache_key, 'instruments')
            if cached and not force_refresh:
                logger.info(f"从内存缓存获取 {exchange} 标的列表")
                return cached
            
            logger.info(f"从 TickFlow API 获取 {exchange} 交易所标的列表...")
            
            # 4. 从 TickFlow SDK 获取
            if hasattr(self._tf, 'exchanges') and self._tf.exchanges is not None:
                # 使用 get_instruments 方法获取标的列表
                if hasattr(self._tf.exchanges, 'get_instruments'):
                    # 调用 exchanges.get_instruments(exchange_code) 获取标的列表
                    instruments = self._tf.exchanges.get_instruments(exchange)
                else:
                    logger.warning(f"TickFlow exchanges 对象没有 get_instruments() 方法")
                    instruments = None
                
                if instruments:
                    result = []
                    for inst in instruments:
                        # 支持字典和对象两种格式
                        if isinstance(inst, dict):
                            inst_data = {
                                'code': inst.get('code', ''),
                                'exchange': inst.get('exchange', ''),
                                'region': inst.get('region', ''),
                                'symbol': inst.get('symbol', ''),
                                'name': inst.get('name', ''),
                                'type': inst.get('type', ''),
                                'ext': inst.get('ext', {}),
                            }
                        else:
                            inst_data = {
                                'code': getattr(inst, 'code', ''),
                                'exchange': getattr(inst, 'exchange', ''),
                                'region': getattr(inst, 'region', ''),
                                'symbol': getattr(inst, 'symbol', ''),
                                'name': getattr(inst, 'name', ''),
                                'type': getattr(inst, 'type', ''),
                                'ext': getattr(inst, 'ext', {}),
                            }
                        result.append(inst_data)
                    
                    # 保存到内存缓存
                    self._set_to_cache(cache_key, result, 'instruments')
                    
                    # 保存到持久化存储（7 天有效期）
                    exchange_storage.save_exchange_instruments(
                        exchange, 
                        result, 
                        source='tickflow', 
                        expiry_days=7
                    )
                    
                    logger.info(f"✅ TickFlow 获取 {exchange} 标的列表成功：{len(result)}个")
                    return result
            else:
                logger.warning(f"TickFlow 没有 exchanges 模块，无法获取 {exchange} 标的列表")
                return []
            
        except Exception as e:
            logger.error(f"TickFlow 获取 {exchange} 标的列表失败：{e}")
            return []
    
    async def get_instrument_info(
        self,
        symbol: str,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        查询标的元数据（单个标的）
        
        Args:
            symbol: TickFlow 格式的标的代码（如：600177.SH）
            force_refresh: 是否强制刷新
        
        Returns:
            标的元数据，包含：
            - code: 标的代码
            - exchange: 交易所代码
            - region: 所属地区
            - symbol: TickFlow 格式代码
            - name: 标的名称
            - type: 标的类型
            - ext: 扩展信息（股本、上市日期等）
        """
        try:
            # 1. 检查是否需要强制刷新
            if not force_refresh:
                # 2. 尝试从内存缓存加载
                cache_key = f'tickflow_instrument_{symbol}'
                cached = self._get_from_cache(cache_key, 'instruments')
                if cached:
                    logger.info(f"从内存缓存获取 {symbol} 标的信息")
                    return cached
            
            # 3. 从 TickFlow SDK 获取
            if not self._tf:
                logger.warning("TickFlow 未初始化")
                return None
            
            logger.info(f"从 TickFlow API 查询 {symbol} 标的元数据...")
            
            # 使用 instruments.get() 方法
            if hasattr(self._tf, 'instruments') and self._tf.instruments is not None:
                # get() 方法不接受参数，需要使用 batch() 方法
                if hasattr(self._tf.instruments, 'batch'):
                    instruments = self._tf.instruments.batch(symbols=[symbol])
                else:
                    logger.warning("TickFlow instruments 对象没有 batch() 方法")
                    return None
                
                if instruments and len(instruments) > 0:
                    inst = instruments[0]
                    
                    # 支持字典和对象两种格式
                    if isinstance(inst, dict):
                        result = {
                            'code': inst.get('code', ''),
                            'exchange': inst.get('exchange', ''),
                            'region': inst.get('region', ''),
                            'symbol': inst.get('symbol', ''),
                            'name': inst.get('name', ''),
                            'type': inst.get('type', ''),
                            'ext': inst.get('ext', {}),
                        }
                    else:
                        result = {
                            'code': getattr(inst, 'code', ''),
                            'exchange': getattr(inst, 'exchange', ''),
                            'region': getattr(inst, 'region', ''),
                            'symbol': getattr(inst, 'symbol', ''),
                            'name': getattr(inst, 'name', ''),
                            'type': getattr(inst, 'type', ''),
                            'ext': getattr(inst, 'ext', {}),
                        }
                    
                    # 保存到内存缓存
                    self._set_to_cache(cache_key, result, 'instruments')
                    logger.info(f"✅ 查询 {symbol} 标的元数据成功")
                    return result
                else:
                    logger.warning(f"未找到标的 {symbol} 的信息")
                    return None
            else:
                logger.warning("TickFlow 没有 instruments 模块")
                return None
            
        except Exception as e:
            logger.error(f"查询 {symbol} 标的元数据失败：{e}")
            return None
    
    async def get_instruments_batch(
        self,
        symbols: List[str],
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        批量查询标的元数据
        
        Args:
            symbols: TickFlow 格式的标的代码列表（如：["600177.SH", "000001.SZ"]）
            force_refresh: 是否强制刷新
        
        Returns:
            标的元数据列表，格式同 get_instrument_info()
        """
        try:
            if not symbols:
                logger.warning("标的代码列表为空")
                return []
            
            # 1. 检查是否需要强制刷新
            if not force_refresh:
                # 2. 尝试从内存缓存加载
                result = []
                missing_symbols = []
                
                for symbol in symbols:
                    cache_key = f'tickflow_instrument_{symbol}'
                    cached = self._get_from_cache(cache_key, 'instruments')
                    if cached:
                        result.append(cached)
                    else:
                        missing_symbols.append(symbol)
                
                if missing_symbols:
                    # 有未缓存的标的，需要继续查询
                    symbols = missing_symbols
                else:
                    # 全部命中缓存
                    logger.info(f"从内存缓存获取 {len(result)} 个标的信息")
                    return result
            
            # 3. 从 TickFlow SDK 获取
            if not self._tf:
                logger.warning("TickFlow 未初始化")
                return []
            
            logger.info(f"从 TickFlow API 批量查询 {len(symbols)} 个标的元数据...")
            
            # 使用 instruments.batch() 方法
            if hasattr(self._tf, 'instruments') and self._tf.instruments is not None:
                if hasattr(self._tf.instruments, 'batch'):
                    instruments = self._tf.instruments.batch(symbols=symbols)
                elif hasattr(self._tf.instruments, 'get'):
                    # 如果没有 batch 方法，使用 get 方法
                    instruments = self._tf.instruments.get(symbols=symbols)
                else:
                    logger.warning("TickFlow instruments 对象没有 batch() 或 get() 方法")
                    return []
                
                if instruments:
                    result = []
                    for inst in instruments:
                        # 支持字典和对象两种格式
                        if isinstance(inst, dict):
                            inst_data = {
                                'code': inst.get('code', ''),
                                'exchange': inst.get('exchange', ''),
                                'region': inst.get('region', ''),
                                'symbol': inst.get('symbol', ''),
                                'name': inst.get('name', ''),
                                'type': inst.get('type', ''),
                                'ext': inst.get('ext', {}),
                            }
                        else:
                            inst_data = {
                                'code': getattr(inst, 'code', ''),
                                'exchange': getattr(inst, 'exchange', ''),
                                'region': getattr(inst, 'region', ''),
                                'symbol': getattr(inst, 'symbol', ''),
                                'name': getattr(inst, 'name', ''),
                                'type': getattr(inst, 'type', ''),
                                'ext': getattr(inst, 'ext', {}),
                            }
                        
                        result.append(inst_data)
                        
                        # 保存到内存缓存
                        cache_key = f'tickflow_instrument_{inst_data["symbol"]}'
                        self._set_to_cache(cache_key, inst_data, 'instruments')
                    
                    logger.info(f"✅ 批量查询 {len(result)} 个标的元数据成功")
                    return result
                else:
                    logger.warning("批量查询返回空数据")
                    return []
            else:
                logger.warning("TickFlow 没有 instruments 模块")
                return []
            
        except Exception as e:
            logger.error(f"批量查询标的元数据失败：{e}")
            return []
    
    async def get_realtime_quote_single(
        self,
        symbol: str,
        force_refresh: bool = False
    ) -> Optional[Dict[str, Any]]:
        """
        查询单个标的实时行情
        
        Args:
            symbol: TickFlow 格式的标的代码（如：600177.SH）
            force_refresh: 是否强制刷新
        
        Returns:
            实时行情数据，包含：
            - symbol: TickFlow 格式代码
            - last_price: 最新价
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - prev_close: 昨收价
            - volume: 成交量
            - amount: 成交额
            - timestamp: 时间戳
            - region: 所属地区
            - session: 交易时段（pre_market/continuous/after_hours）
            - ext: 扩展信息（涨跌幅、振幅、换手率等）
        """
        try:
            # 1. 检查是否需要强制刷新
            if not force_refresh:
                # 2. 尝试从内存缓存加载（实时行情缓存时间短）
                cache_key = f'tickflow_quote_{symbol}'
                cached = self._get_from_cache(cache_key, 'quote')
                if cached:
                    logger.info(f"从内存缓存获取 {symbol} 实时行情")
                    return cached
            
            # 3. 从 TickFlow SDK 获取
            if not self._tf:
                logger.warning("TickFlow 未初始化")
                return None
            
            logger.info(f"从 TickFlow API 查询 {symbol} 实时行情...")
            
            # 使用 quotes.get() 方法
            if hasattr(self._tf, 'quotes') and self._tf.quotes is not None:
                if hasattr(self._tf.quotes, 'get'):
                    quotes = self._tf.quotes.get(symbols=[symbol])
                else:
                    logger.warning("TickFlow quotes 对象没有 get() 方法")
                    return None
                
                if quotes and len(quotes) > 0:
                    quote = quotes[0]
                    
                    # 支持字典和对象两种格式
                    if isinstance(quote, dict):
                        result = {
                            'symbol': quote.get('symbol', ''),
                            'last_price': quote.get('last_price', 0),
                            'open': quote.get('open', 0),
                            'high': quote.get('high', 0),
                            'low': quote.get('low', 0),
                            'prev_close': quote.get('prev_close', 0),
                            'volume': quote.get('volume', 0),
                            'amount': quote.get('amount', 0),
                            'timestamp': quote.get('timestamp', 0),
                            'region': quote.get('region', ''),
                            'session': quote.get('session', ''),
                            'ext': quote.get('ext', {}),
                        }
                    else:
                        result = {
                            'symbol': getattr(quote, 'symbol', ''),
                            'last_price': getattr(quote, 'last_price', 0),
                            'open': getattr(quote, 'open', 0),
                            'high': getattr(quote, 'high', 0),
                            'low': getattr(quote, 'low', 0),
                            'prev_close': getattr(quote, 'prev_close', 0),
                            'volume': getattr(quote, 'volume', 0),
                            'amount': getattr(quote, 'amount', 0),
                            'timestamp': getattr(quote, 'timestamp', 0),
                            'region': getattr(quote, 'region', ''),
                            'session': getattr(quote, 'session', ''),
                            'ext': getattr(quote, 'ext', {}),
                        }
                    
                    # 保存到内存缓存（实时行情缓存 10 秒）
                    self._set_to_cache(cache_key, result, 'quote')
                    logger.info(f"✅ 查询 {symbol} 实时行情成功")
                    return result
                else:
                    logger.warning(f"未找到标的 {symbol} 的实时行情")
                    return None
            else:
                logger.warning("TickFlow 没有 quotes 模块")
                return None
            
        except Exception as e:
            logger.error(f"查询 {symbol} 实时行情失败：{e}")
            return None
    
    async def get_realtime_quotes_batch(
        self,
        symbols: List[str],
        force_refresh: bool = False
    ) -> List[Dict[str, Any]]:
        """
        批量查询实时行情
        
        Args:
            symbols: TickFlow 格式的标的代码列表（如：["600177.SH", "000001.SZ"]）
            force_refresh: 是否强制刷新
        
        Returns:
            实时行情数据列表，格式同 get_realtime_quote_single()
        """
        try:
            if not symbols:
                logger.warning("标的代码列表为空")
                return []
            
            # 1. 检查是否需要强制刷新
            if not force_refresh:
                # 2. 尝试从内存缓存加载
                result = []
                missing_symbols = []
                
                for symbol in symbols:
                    cache_key = f'tickflow_quote_{symbol}'
                    cached = self._get_from_cache(cache_key, 'quote')
                    if cached:
                        result.append(cached)
                    else:
                        missing_symbols.append(symbol)
                
                if missing_symbols:
                    # 有未缓存的标的，需要继续查询
                    symbols = missing_symbols
                else:
                    # 全部命中缓存
                    logger.info(f"从内存缓存获取 {len(result)} 个标的的实时行情")
                    return result
            
            # 3. 从 TickFlow SDK 获取
            if not self._tf:
                logger.warning("TickFlow 未初始化")
                return []
            
            logger.info(f"从 TickFlow API 批量查询 {len(symbols)} 个标的实时行情...")
            
            # 使用 quotes.get() 方法批量查询
            if hasattr(self._tf, 'quotes') and self._tf.quotes is not None:
                if hasattr(self._tf.quotes, 'get'):
                    quotes = self._tf.quotes.get(symbols=symbols)
                else:
                    logger.warning("TickFlow quotes 对象没有 get() 方法")
                    return []
                
                if quotes:
                    result = []
                    for quote in quotes:
                        # 支持字典和对象两种格式
                        if isinstance(quote, dict):
                            quote_data = {
                                'symbol': quote.get('symbol', ''),
                                'last_price': quote.get('last_price', 0),
                                'open': quote.get('open', 0),
                                'high': quote.get('high', 0),
                                'low': quote.get('low', 0),
                                'prev_close': quote.get('prev_close', 0),
                                'volume': quote.get('volume', 0),
                                'amount': quote.get('amount', 0),
                                'timestamp': quote.get('timestamp', 0),
                                'region': quote.get('region', ''),
                                'session': quote.get('session', ''),
                                'ext': quote.get('ext', {}),
                            }
                        else:
                            quote_data = {
                                'symbol': getattr(quote, 'symbol', ''),
                                'last_price': getattr(quote, 'last_price', 0),
                                'open': getattr(quote, 'open', 0),
                                'high': getattr(quote, 'high', 0),
                                'low': getattr(quote, 'low', 0),
                                'prev_close': getattr(quote, 'prev_close', 0),
                                'volume': getattr(quote, 'volume', 0),
                                'amount': getattr(quote, 'amount', 0),
                                'timestamp': getattr(quote, 'timestamp', 0),
                                'region': getattr(quote, 'region', ''),
                                'session': getattr(quote, 'session', ''),
                                'ext': getattr(quote, 'ext', {}),
                            }
                        
                        result.append(quote_data)
                        
                        # 保存到内存缓存（实时行情缓存 10 秒）
                        cache_key = f'tickflow_quote_{quote_data["symbol"]}'
                        self._set_to_cache(cache_key, quote_data, 'quote')
                    
                    logger.info(f"✅ 批量查询 {len(result)} 个标的实时行情成功")
                    return result
                else:
                    logger.warning("批量查询返回空数据")
                    return []
            else:
                logger.warning("TickFlow 没有 quotes 模块")
                return []
            
        except Exception as e:
            logger.error(f"批量查询实时行情失败：{e}")
            return []


# 导入 time 模块（用于缓存）
import time
