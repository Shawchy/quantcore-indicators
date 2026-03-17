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
from .akshare_adapter import AkShareAdapter
from .baostock_adapter import BaostockAdapter
from .yfinance_adapter import YFinanceAdapter
from .efinance_adapter import EFinanceAdapter

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
            DataSourceType.TUSHARE: (TushareAdapter, TushareAdapter is not None and bool(settings.TUSHARE_TOKEN)),
            DataSourceType.EFINANCE: (EFinanceAdapter, True),
            DataSourceType.AKSHARE: (AkShareAdapter, True),
            DataSourceType.BAOSTOCK: (BaostockAdapter, True),
            DataSourceType.YFINANCE: (YFinanceAdapter, False),
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
    
    async def get_stock_list(self, source_type: Optional[str] = None) -> list[StockBasicInfo]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_stock_list()
    
    async def get_stock_info(self, code: str, source_type: Optional[str] = None) -> Optional[StockBasicInfo]:
        """获取股票信息（支持自动故障转移）"""
        # 如果指定了数据源，直接使用
        if source_type:
            adapter = self.get_adapter(source_type)
            try:
                return await adapter.get_stock_info(code)
            except Exception as e:
                logger.warning(f"数据源 {source_type} 获取股票信息失败：{e}，尝试切换数据源")
                # 故障转移：使用其他数据源
                return await self._get_stock_info_with_fallback(code, exclude_source=source_type)
        else:
            # 未指定数据源，按优先级尝试所有数据源
            return await self._get_stock_info_with_fallback(code)
    
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
    
    async def close(self) -> None:
        await self._factory.close_all()


data_source_manager = DataSourceManager()
