from typing import Optional, Dict, Any, Type
from enum import Enum
from loguru import logger

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData
)
from .akshare_adapter import AkShareAdapter
from .baostock_adapter import BaostockAdapter
from .yfinance_adapter import YFinanceAdapter

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
        priority_list = getattr(settings, 'DATA_SOURCE_PRIORITY', ['tushare', 'akshare', 'baostock'])
        
        adapters_config = {
            DataSourceType.TUSHARE: (TushareAdapter, TushareAdapter is not None and bool(settings.TUSHARE_TOKEN)),
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
    
    async def get_stock_list(self, source_type: Optional[str] = None) -> list[StockBasicInfo]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_stock_list()
    
    async def get_stock_info(self, code: str, source_type: Optional[str] = None) -> Optional[StockBasicInfo]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_stock_info(code)
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        source_type: Optional[str] = None
    ) -> list[KLineData]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_kline(code, start_date, end_date, adjust)
    
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
    
    async def close(self) -> None:
        await self._factory.close_all()


data_source_manager = DataSourceManager()
