from typing import Optional, Dict, Any, Type, List
from enum import Enum
from loguru import logger

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData,
    BillboardEntry,
    BoardInfo,
    ShareholderInfo,
    IndexComponent,
    CapitalFlowItem,
    MarketQuote
)
from typing import Union, List, Dict, Any, Optional
from .akshare_adapter import AkShareAdapter
from .baostock_adapter import BaostockAdapter
from .yfinance_adapter import YFinanceAdapter
from .efinance_adapter import EFinanceAdapter
from .tickflow_adapter import TickFlowAdapter
from .unified_adapter import (
    EFinanceUnifiedAdapter,
    AkShareUnifiedAdapter,
    BaostockUnifiedAdapter,
    TickFlowUnifiedAdapter
)

try:
    from .tushare_adapter import TushareAdapter
except ImportError:
    TushareAdapter = None

from app.config import settings


class DataSourceFactory:
    _adapters: Dict[DataSourceType, BaseDataAdapter] = {}
    _initialized: bool = False
    
    @classmethod
    async def initialize(cls, default_source: Optional[str] = None) -> None:
        if cls._initialized:
            return
        
        default = default_source or settings.DEFAULT_DATA_SOURCE
        
        # 按照优先级初始化数据源
        priority_list = getattr(settings, 'DATA_SOURCE_PRIORITY', ['tushare', 'efinance', 'akshare', 'baostock'])
        
        adapters_config = {
            DataSourceType.TUSHARE: (TushareAdapter, False),  # Tushare 默认不主动初始化（需要 Token）
            DataSourceType.EFINANCE: (EFinanceAdapter, True),
            DataSourceType.AKSHARE: (AkShareAdapter, True),
            DataSourceType.BAOSTOCK: (BaostockAdapter, True),
            DataSourceType.YFINANCE: (YFinanceAdapter, False),
            DataSourceType.TICKFLOW: (TickFlowAdapter, True),  # TickFlow 始终可用（免费服务）
        }
        
        # 按优先级顺序初始化
        for source_type_name in priority_list:
            try:
                source_type = DataSourceType(source_type_name)
            except ValueError:
                logger.warning(f"未知的数据源类型：{source_type_name}")
                continue
            
            if source_type in adapters_config:
                adapter_class, should_init = adapters_config[source_type]
                if should_init:
                    try:
                        adapter = adapter_class()
                        success = await adapter.initialize()
                        if success:
                            cls._adapters[source_type] = adapter
                            logger.info(f"数据源 {source_type.value} 初始化成功（优先级：{priority_list.index(source_type_name) + 1})")
                        else:
                            logger.warning(f"数据源 {source_type.value} 初始化失败，尝试下一个")
                    except Exception as e:
                        logger.warning(f"数据源 {source_type.value} 初始化异常：{e}，尝试下一个")
        
        # 如果没有数据源初始化成功，尝试初始化 AkShare 作为保底
        if not cls._adapters and DataSourceType.AKSHARE in adapters_config:
            try:
                adapter = AkShareAdapter()
                success = await adapter.initialize()
                if success:
                    cls._adapters[DataSourceType.AKSHARE] = adapter
                    logger.info("使用 AkShare 作为保底数据源")
            except Exception as e:
                logger.error(f"AkShare 保底数据源初始化失败：{e}")
        
        cls._initialized = True
        available_sources = [s.value for s in cls._adapters.keys()]
        logger.info(f"数据源工厂初始化完成，可用数据源：{available_sources}")
        
        # 记录当前使用的数据源
        if available_sources:
            logger.info(f"当前默认数据源：{default} (实际使用：{available_sources[0] if default not in available_sources else default})")
    
    @classmethod
    def get_adapter(cls, source_type: Optional[str] = None) -> BaseDataAdapter:
        if not cls._initialized:
            raise RuntimeError("数据源工厂未初始化，请先调用 initialize()")
        
        if source_type:
            try:
                source = DataSourceType(source_type)
            except ValueError:
                logger.warning(f"未知的数据源类型：{source_type}，使用默认数据源")
                source = None
        else:
            source = DataSourceType(settings.DEFAULT_DATA_SOURCE)
        
        # 优先使用请求的数据源
        if source and source in cls._adapters:
            return cls._adapters[source]
        
        # 如果请求的数据源不可用，按优先级选择第一个可用的
        if cls._adapters:
            available_source = next(iter(cls._adapters.values()))
            if source:
                logger.warning(f"数据源 {source.value} 不可用，使用 {available_source.source_type.value}")
            return available_source
        
        # 如果没有可用数据源，抛出异常
        raise ValueError(f"没有可用的数据源，请检查配置")
    
    @classmethod
    def get_available_sources(cls) -> list[str]:
        return [s.value for s in cls._adapters.keys()]
    
    @classmethod
    def get_unified_adapter(cls, source_type: Optional[str] = None) -> 'UnifiedDataAdapter':
        """
        获取统一数据适配器（支持新特性）
        
        Args:
            source_type: 数据源类型
            
        Returns:
            统一数据适配器实例
        """
        if not cls._initialized:
            raise RuntimeError("数据源工厂未初始化，请先调用 initialize()")
        
        source = source_type or settings.DEFAULT_DATA_SOURCE
        
        # 映射到对应的统一适配器
        unified_adapters = {
            DataSourceType.EFINANCE: EFinanceUnifiedAdapter,
            DataSourceType.AKSHARE: AkShareUnifiedAdapter,
            DataSourceType.BAOSTOCK: BaostockUnifiedAdapter,
            DataSourceType.TICKFLOW: TickFlowUnifiedAdapter,
        }
        
        try:
            source_enum = DataSourceType(source)
            if source_enum in unified_adapters:
                adapter = unified_adapters[source_enum]()
                logger.info(f"使用统一适配器：{source_enum.value}")
                return adapter
            else:
                logger.warning(f"数据源 {source} 不支持统一适配器，使用普通适配器")
                return cls.get_adapter(source_type)
        except ValueError:
            logger.warning(f"未知的数据源类型：{source}，使用默认适配器")
            return cls.get_adapter(None)
    
    @classmethod
    async def close_all(cls) -> None:
        for adapter in cls._adapters.values():
            try:
                await adapter.close()
            except Exception as e:
                logger.error(f"关闭数据源 {adapter.source_type.value} 失败: {e}")
        
        cls._adapters.clear()
        cls._initialized = False
        logger.info("所有数据源已关闭")


class DataSourceManager:
    def __init__(self, default_source: Optional[str] = None):
        self._default_source = default_source or settings.DEFAULT_DATA_SOURCE
        self._factory = DataSourceFactory
    
    async def initialize(self) -> None:
        await self._factory.initialize(self._default_source)
    
    def get_adapter(self, source_type: Optional[str] = None) -> BaseDataAdapter:
        return self._factory.get_adapter(source_type)
    
    def get_available_sources(self) -> list[str]:
        """获取所有可用的数据源列表"""
        return self._factory.get_available_sources()
    
    async def get_index_basic(
        self,
        ts_code: Optional[str] = None,
        name: Optional[str] = None,
        market: Optional[str] = None,
        publisher: Optional[str] = None,
        category: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取指数基础信息"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_index_basic'):
            return await adapter.get_index_basic(ts_code, name, market, publisher, category)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持指数基础信息查询")
            return []
    
    async def get_stock_list(
        self,
        source_type: Optional[str] = None,
        source_priority: Optional[str] = None,
        source_exclude: Optional[str] = None,
        fallback: bool = True
    ) -> list[StockBasicInfo]:
        """
        获取股票列表（支持优先级参数）
        
        Args:
            source_type: 指定数据源
            source_priority: 临时优先级（逗号分隔）
            source_exclude: 排除的数据源
            fallback: 是否允许故障转移
        """
        # 解析优先级列表
        priority_list = self._parse_priority_list(
            source_type=source_type,
            source_priority=source_priority,
            source_exclude=source_exclude
        )
        
        # 按优先级尝试
        return await self._get_with_priority(
            operation="get_stock_list",
            priority_list=priority_list,
            fallback=fallback
        )
    
    async def get_stock_info(
        self,
        code: str,
        source_type: Optional[str] = None,
        source_priority: Optional[str] = None,
        source_exclude: Optional[str] = None,
        fallback: bool = True
    ) -> Optional[StockBasicInfo]:
        """
        获取股票信息（支持优先级参数）
        
        Args:
            code: 股票代码
            source_type: 指定数据源
            source_priority: 临时优先级（逗号分隔）
            source_exclude: 排除的数据源
            fallback: 是否允许故障转移
        """
        # 解析优先级列表
        priority_list = self._parse_priority_list(
            source_type=source_type,
            source_priority=source_priority,
            source_exclude=source_exclude
        )
        
        # 按优先级尝试
        result = await self._get_with_priority(
            operation="get_stock_info",
            code=code,
            priority_list=priority_list,
            fallback=fallback
        )
        
        return result
    
    def _parse_priority_list(
        self,
        source_type: Optional[str] = None,
        source_priority: Optional[str] = None,
        source_exclude: Optional[str] = None
    ) -> List[str]:
        """
        解析优先级列表
        
        优先级顺序：
        1. source_type（强制指定）
        2. source_priority（临时优先级）
        3. 系统配置的 DATA_SOURCE_PRIORITY
        4. 默认优先级
        """
        # 1. 如果强制指定了数据源
        if source_type and source_type != "auto":
            return [source_type]
        
        # 2. 如果提供了临时优先级
        if source_priority:
            priority_list = [s.strip() for s in source_priority.split(",") if s.strip()]
        else:
            # 3. 使用系统配置的优先级
            priority_config = getattr(
                settings, 
                'DATA_SOURCE_PRIORITY', 
                'efinance,tushare,akshare,baostock'
            )
            # 如果是列表直接返回，如果是字符串则分割
            if isinstance(priority_config, list):
                priority_list = priority_config
            else:
                priority_list = [s.strip() for s in priority_config.split(",") if s.strip()]
        
        # 4. 排除指定的数据源
        if source_exclude:
            exclude_list = [s.strip() for s in source_exclude.split(",") if s.strip()]
            priority_list = [s for s in priority_list if s not in exclude_list]
        
        # 5. 过滤不可用的数据源
        available_sources = self.get_available_sources()
        priority_list = [s for s in priority_list if s in available_sources]
        
        if not priority_list:
            logger.warning("没有可用的数据源")
            # 保底：使用任意可用数据源
            priority_list = available_sources
        
        logger.debug(f"解析后的优先级列表：{priority_list}")
        return priority_list
    
    async def _get_with_priority(
        self,
        operation: str,
        priority_list: List[str],
        fallback: bool = True,
        **kwargs
    ):
        """
        按优先级尝试所有数据源
        
        Args:
            operation: 操作名称（get_stock_info/get_kline 等）
            priority_list: 数据源优先级列表
            fallback: 是否允许故障转移
            **kwargs: 传递给具体方法的参数
        """
        last_error = None
        
        for source in priority_list:
            try:
                logger.debug(f"尝试从数据源 {source} 获取：{kwargs.get('code', '')}")
                adapter = self.get_adapter(source)
                
                # 根据操作调用对应方法
                if operation == "get_stock_list":
                    result = await adapter.get_stock_list()
                elif operation == "get_stock_info":
                    result = await adapter.get_stock_info(kwargs.get('code'))
                elif operation == "get_kline":
                    result = await adapter.get_kline(
                        kwargs.get('code'),
                        kwargs.get('start_date'),
                        kwargs.get('end_date'),
                        kwargs.get('adjust', 'qfq'),
                        period=kwargs.get('period', 'daily')
                    )
                elif operation == "get_realtime_quote":
                    result = await adapter.get_realtime_quote(kwargs.get('code'))
                else:
                    logger.error(f"未知操作：{operation}")
                    return None
                
                if result:
                    logger.info(f"从数据源 {source} 成功获取：{kwargs.get('code', '')}")
                    return result
                else:
                    logger.debug(f"数据源 {source} 返回空数据：{kwargs.get('code', '')}")
                    
            except Exception as e:
                logger.warning(f"数据源 {source} 失败：{kwargs.get('code', '')}: {e}")
                last_error = e
                
                if not fallback:
                    # 不允许故障转移，直接抛出
                    raise
        
        # 所有数据源都失败
        if last_error:
            logger.error(f"所有数据源失败：{kwargs.get('code', '')}, 最后错误：{last_error}")
            if fallback:
                return None
            raise last_error
        else:
            logger.warning(f"所有数据源返回空数据：{kwargs.get('code', '')}")
            return None
    
    async def _get_stock_info_with_fallback(
        self,
        code: str,
        exclude_source: Optional[str] = None
    ) -> Optional[StockBasicInfo]:
        """按优先级尝试所有数据源获取股票信息"""
        available_sources = self.get_available_sources()
        
        # 排除失败的数据源
        if exclude_source and exclude_source in available_sources:
            available_sources = [s for s in available_sources if s != exclude_source]
        
        last_error = None
        for source in available_sources:
            try:
                logger.debug(f"尝试从数据源 {source} 获取股票信息：{code}")
                adapter = self.get_adapter(source)
                info = await adapter.get_stock_info(code)
                
                if info:
                    logger.debug(f"从数据源 {source} 成功获取股票信息：{code}")
                    return info
                else:
                    logger.debug(f"数据源 {source} 返回空数据：{code}")
            except Exception as e:
                logger.warning(f"数据源 {source} 获取股票信息失败：{code}: {e}")
                last_error = e
                continue
        
        # 所有数据源都失败
        if last_error:
            logger.error(f"所有数据源获取股票信息失败：{code}, 最后错误：{last_error}")
            return None
        else:
            logger.warning(f"所有数据源返回空数据：{code}")
            return None
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        source_type: Optional[str] = None
    ) -> list[KLineData]:
        """获取 K 线数据（支持自动故障转移）"""
        # 如果指定了数据源，直接使用
        if source_type:
            adapter = self.get_adapter(source_type)
            try:
                return await adapter.get_kline(code, start_date, end_date, adjust)
            except Exception as e:
                logger.warning(f"数据源 {source_type} 获取 K 线失败：{e}，尝试切换数据源")
                # 故障转移：使用其他数据源
                return await self._get_kline_with_fallback(code, start_date, end_date, adjust, exclude_source=source_type)
        else:
            # 未指定数据源，按优先级尝试所有数据源
            return await self._get_kline_with_fallback(code, start_date, end_date, adjust)
    
    async def _get_kline_with_fallback(
        self,
        code: str,
        start_date: Optional[str],
        end_date: Optional[str],
        adjust: str,
        exclude_source: Optional[str] = None
    ) -> list[KLineData]:
        """按优先级尝试所有数据源获取 K 线数据"""
        # 获取所有可用的数据源（按优先级排序）
        available_sources = self.get_available_sources()
        
        # 排除失败的数据源
        if exclude_source and exclude_source in available_sources:
            available_sources = [s for s in available_sources if s != exclude_source]
        
        last_error = None
        for source in available_sources:
            try:
                logger.debug(f"尝试从数据源 {source} 获取 K 线数据：{code}")
                adapter = self.get_adapter(source)
                klines = await adapter.get_kline(code, start_date, end_date, adjust)
                
                if klines and len(klines) > 0:
                    logger.info(f"从数据源 {source} 成功获取 K 线数据：{code}, {len(klines)} 条")
                    return klines
                else:
                    logger.debug(f"数据源 {source} 返回空数据：{code}")
            except Exception as e:
                logger.warning(f"数据源 {source} 获取 K 线失败：{code}: {e}")
                last_error = e
                continue
        
        # 所有数据源都失败
        if last_error:
            logger.error(f"所有数据源获取 K 线失败：{code}, 最后错误：{last_error}")
            raise last_error
        else:
            logger.warning(f"所有数据源返回空数据：{code}")
            return []
    
    async def get_realtime_quote(self, code: str, source_type: Optional[str] = None) -> Dict[str, Any]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_realtime_quote(code)
    
    async def get_sector_list(self, sector_type: str = "industry", source_type: Optional[str] = None) -> list[SectorInfo]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_sector_list(sector_type)
    
    async def get_sector_components(self, sector_code: str, source_type: Optional[str] = None) -> list[str]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_sector_components(sector_code)
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list[ChipData]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_chip_data(code, start_date, end_date)
    
    async def get_market_index_kline(
        self,
        index_code: str = "000001",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list[KLineData]:
        """获取大盘指数 K 线数据"""
        adapter = self.get_adapter(source_type)
        # 检查适配器是否有此方法
        if hasattr(adapter, 'get_market_index_kline'):
            return await adapter.get_market_index_kline(index_code, start_date, end_date)
        else:
            # 如果适配器不支持，使用普通 K 线方法
            return await adapter.get_kline(index_code, start_date, end_date, adjust="")
    
    async def get_stock_intraday_em(
        self,
        symbol: str,
        source_type: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """获取东方财富个股分时数据"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_stock_intraday_em'):
            return await adapter.get_stock_intraday_em(symbol)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持东方财富分时数据")
            return []
    
    async def get_stock_intraday_sina(
        self,
        symbol: str,
        date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """获取新浪财经个股分时数据（大单数据）"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_stock_intraday_sina'):
            return await adapter.get_stock_intraday_sina(symbol, date)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持新浪财经分时数据")
            return []
    
    async def get_stock_zh_a_minute(
        self,
        symbol: str,
        period: str = '1',
        adjust: str = '',
        source_type: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """获取新浪财经分时数据（支持多频率和复权）"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_stock_zh_a_minute'):
            return await adapter.get_stock_zh_a_minute(symbol, period, adjust)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持新浪财经分时数据")
            return []
    
    async def get_stock_zh_a_hist_min_em(
        self,
        symbol: str,
        period: str = '5',
        adjust: str = '',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list[Dict[str, Any]]:
        """获取东方财富分时数据（支持多频率、复权和时间范围）"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_stock_zh_a_hist_min_em'):
            return await adapter.get_stock_zh_a_hist_min_em(
                symbol, period, adjust, start_date, end_date
            )
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持东方财富分时数据")
            return []
    
    async def get_daily_billboard(
        self,
        trade_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> List[BillboardEntry]:
        """获取龙虎榜单数据"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_daily_billboard'):
            return await adapter.get_daily_billboard(trade_date)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持龙虎榜数据")
            return []
    
    async def get_belong_board(
        self,
        code: str,
        source_type: Optional[str] = None
    ) -> List[BoardInfo]:
        """获取股票所属板块"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_belong_board'):
            return await adapter.get_belong_board(code)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取股票所属板块")
            return []
    
    async def get_members(
        self,
        index_code: str,
        source_type: Optional[str] = None
    ) -> List[IndexComponent]:
        """获取指数成分股"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_members'):
            return await adapter.get_members(index_code)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取指数成分股")
            return []
    
    async def get_today_bill(
        self,
        trade_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> List[CapitalFlowItem]:
        """获取当日资金流向"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_today_bill'):
            return await adapter.get_today_bill(trade_date)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取当日资金流向")
            return []
    
    async def get_history_bill(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> List[CapitalFlowItem]:
        """获取历史资金流向"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_history_bill'):
            return await adapter.get_history_bill(code, start_date, end_date)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取历史资金流向")
            return []
    
    async def get_top10_stock_holder_info(
        self,
        code: str,
        source_type: Optional[str] = None
    ) -> List[ShareholderInfo]:
        """获取前十大股东信息"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_top10_stock_holder_info'):
            return await adapter.get_top10_stock_holder_info(code)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取前十大股东信息")
            return []
    
    async def get_market_realtime_quotes(
        self,
        market_types: Optional[List[str]] = None,
        source_type: Optional[str] = None
    ) -> List[MarketQuote]:
        """获取市场实时行情"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_market_realtime_quotes'):
            return await adapter.get_market_realtime_quotes(market_types)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取市场实时行情")
            return []
    
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        source_type: Optional[str] = None
    ) -> list[KLineData]:
        """获取周线 K 线数据（支持自动故障转移）"""
        if source_type:
            adapter = self.get_adapter(source_type)
            try:
                return await adapter.get_weekly_kline(code, start_date, end_date, adjust)
            except Exception as e:
                logger.warning(f"数据源 {source_type} 获取周线失败：{e}，尝试切换数据源")
                return await self._get_weekly_kline_with_fallback(code, start_date, end_date, adjust, exclude_source=source_type)
        else:
            return await self._get_weekly_kline_with_fallback(code, start_date, end_date, adjust)
    
    async def _get_weekly_kline_with_fallback(
        self,
        code: str,
        start_date: Optional[str],
        end_date: Optional[str],
        adjust: str,
        exclude_source: Optional[str] = None
    ) -> list[KLineData]:
        """按优先级尝试所有数据源获取周线数据"""
        available_sources = self.get_available_sources()
        
        if exclude_source and exclude_source in available_sources:
            available_sources = [s for s in available_sources if s != exclude_source]
        
        last_error = None
        for source in available_sources:
            try:
                logger.debug(f"尝试从数据源 {source} 获取周线数据：{code}")
                adapter = self.get_adapter(source)
                klines = await adapter.get_weekly_kline(code, start_date, end_date, adjust)
                
                if klines and len(klines) > 0:
                    logger.info(f"从数据源 {source} 成功获取周线数据：{code}, {len(klines)}条")
                    return klines
                else:
                    logger.debug(f"数据源 {source} 返回空数据：{code}，继续尝试其他数据源")
                    # 返回空数据也视为失败，继续尝试下一个数据源
                    last_error = Exception(f"数据源 {source} 返回空数据")
                    continue
            except PermissionError as pe:
                # 权限不足，正常降级
                logger.debug(f"数据源 {source} 权限不足：{code}: {pe}")
                last_error = pe
                continue
            except Exception as e:
                logger.warning(f"数据源 {source} 获取周线失败：{code}: {e}")
                last_error = e
                continue
        
        if last_error:
            # 区分权限不足和其他错误
            if isinstance(last_error, PermissionError):
                logger.warning(f"所有数据源权限不足：{code}，请升级积分或检查网络")
            else:
                logger.error(f"所有数据源获取周线失败：{code}, 最后错误：{last_error}")
            raise last_error
        else:
            logger.warning(f"所有数据源返回空数据：{code}")
            return []
    
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        source_type: Optional[str] = None
    ) -> list[KLineData]:
        """获取月线 K 线数据（支持自动故障转移）"""
        if source_type:
            adapter = self.get_adapter(source_type)
            try:
                return await adapter.get_monthly_kline(code, start_date, end_date, adjust)
            except Exception as e:
                logger.warning(f"数据源 {source_type} 获取月线失败：{e}，尝试切换数据源")
                return await self._get_monthly_kline_with_fallback(code, start_date, end_date, adjust, exclude_source=source_type)
        else:
            return await self._get_monthly_kline_with_fallback(code, start_date, end_date, adjust)
    
    async def _get_monthly_kline_with_fallback(
        self,
        code: str,
        start_date: Optional[str],
        end_date: Optional[str],
        adjust: str,
        exclude_source: Optional[str] = None
    ) -> list[KLineData]:
        """按优先级尝试所有数据源获取月线数据"""
        available_sources = self.get_available_sources()
        
        if exclude_source and exclude_source in available_sources:
            available_sources = [s for s in available_sources if s != exclude_source]
        
        last_error = None
        for source in available_sources:
            try:
                logger.debug(f"尝试从数据源 {source} 获取月线数据：{code}")
                adapter = self.get_adapter(source)
                klines = await adapter.get_monthly_kline(code, start_date, end_date, adjust)
                
                if klines and len(klines) > 0:
                    logger.info(f"从数据源 {source} 成功获取月线数据：{code}, {len(klines)}条")
                    return klines
                else:
                    logger.debug(f"数据源 {source} 返回空数据：{code}，继续尝试其他数据源")
                    # 返回空数据也视为失败，继续尝试下一个数据源
                    last_error = Exception(f"数据源 {source} 返回空数据")
                    continue
            except PermissionError as pe:
                # 权限不足，正常降级
                logger.debug(f"数据源 {source} 权限不足：{code}: {pe}")
                last_error = pe
                continue
            except Exception as e:
                logger.warning(f"数据源 {source} 获取月线失败：{code}: {e}")
                last_error = e
                continue
        
        if last_error:
            # 区分权限不足和其他错误
            if isinstance(last_error, PermissionError):
                logger.warning(f"所有数据源权限不足：{code}，请升级积分或检查网络")
            else:
                logger.error(f"所有数据源获取月线失败：{code}, 最后错误：{last_error}")
            raise last_error
        else:
            logger.warning(f"所有数据源返回空数据：{code}")
            return []
    
    async def get_fund_base_info(
        self,
        fund_codes: Union[str, List[str]],
        source_type: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]], None]:
        """获取基金基本信息"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_fund_base_info'):
            return await adapter.get_fund_base_info(fund_codes)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取基金基本信息")
            return None if isinstance(fund_codes, str) else []
    
    async def get_fund_codes(
        self,
        fund_type: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """获取基金代码列表"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_fund_codes'):
            return await adapter.get_fund_codes(fund_type)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取基金代码列表")
            return []
    
    async def get_fund_invest_position(
        self,
        fund_code: str,
        dates: Optional[Union[str, List[str]]] = None,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取基金持仓占比"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_fund_invest_position'):
            return await adapter.get_fund_invest_position(fund_code, dates)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取基金持仓占比")
            return []
    
    async def get_fund_quote_history(
        self,
        fund_code: str,
        pz: int = 40000,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取基金历史净值"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_fund_quote_history'):
            return await adapter.get_fund_quote_history(fund_code, pz)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取基金历史净值")
            return []
    
    async def get_fund_quote_history_multi(
        self,
        fund_codes: List[str],
        pz: int = 40000,
        source_type: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """批量获取基金历史净值"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_fund_quote_history_multi'):
            return await adapter.get_fund_quote_history_multi(fund_codes, pz)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持批量获取基金历史净值")
            return {}
    
    async def get_fund_realtime_increase_rate(
        self,
        fund_codes: Union[str, List[str]],
        source_type: Optional[str] = None
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """获取基金实时估算涨跌幅"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_fund_realtime_increase_rate'):
            return await adapter.get_fund_realtime_increase_rate(fund_codes)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取基金实时估算涨跌幅")
            return {} if isinstance(fund_codes, str) else []
    
    async def get_fund_period_change(
        self,
        fund_code: str,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取基金阶段涨跌幅"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_fund_period_change'):
            return await adapter.get_fund_period_change(fund_code)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取基金阶段涨跌幅")
            return []
    
    async def get_fund_types_percentage(
        self,
        fund_code: str,
        dates: Optional[Union[str, List[str]]] = None,
        source_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """获取基金资产配置比例"""
        adapter = self.get_adapter(source_type)
        if hasattr(adapter, 'get_fund_types_percentage'):
            return await adapter.get_fund_types_percentage(fund_code, dates)
        else:
            logger.warning(f"数据源 {adapter.source_type.value} 不支持获取基金资产配置比例")
            return []
    
    async def close(self) -> None:
        await self._factory.close_all()


data_source_manager = DataSourceManager()
