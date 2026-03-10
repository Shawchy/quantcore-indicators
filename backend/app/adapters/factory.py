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
from .tushare_adapter import TushareAdapter
from app.config import settings


class DataSourceFactory:
    _adapters: Dict[DataSourceType, BaseDataAdapter] = {}
    _initialized: bool = False
    
    @classmethod
    async def initialize(cls, default_source: Optional[str] = None) -> None:
        if cls._initialized:
            return
        
        default = default_source or settings.DEFAULT_DATA_SOURCE
        
        adapters_config = {
            DataSourceType.AKSHARE: (AkShareAdapter, True),
            DataSourceType.BAOSTOCK: (BaostockAdapter, True),
            DataSourceType.YFINANCE: (YFinanceAdapter, False),
            DataSourceType.TUSHARE: (TushareAdapter, bool(settings.TUSHARE_TOKEN))
        }
        
        for source_type, (adapter_class, should_init) in adapters_config.items():
            if should_init:
                try:
                    adapter = adapter_class()
                    success = await adapter.initialize()
                    if success:
                        cls._adapters[source_type] = adapter
                        logger.info(f"数据源 {source_type.value} 初始化成功")
                except Exception as e:
                    logger.warning(f"数据源 {source_type.value} 初始化失败: {e}")
        
        cls._initialized = True
        logger.info(f"数据源工厂初始化完成，可用数据源: {[s.value for s in cls._adapters.keys()]}")
    
    @classmethod
    def get_adapter(cls, source_type: Optional[str] = None) -> BaseDataAdapter:
        if not cls._initialized:
            raise RuntimeError("数据源工厂未初始化，请先调用 initialize()")
        
        if source_type:
            source = DataSourceType(source_type)
        else:
            source = DataSourceType(settings.DEFAULT_DATA_SOURCE)
        
        if source not in cls._adapters:
            if DataSourceType.AKSHARE in cls._adapters:
                logger.warning(f"数据源 {source.value} 不可用，使用 AkShare 作为备选")
                return cls._adapters[DataSourceType.AKSHARE]
            raise ValueError(f"数据源 {source.value} 不可用")
        
        return cls._adapters[source]
    
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
    
    async def close(self) -> None:
        await self._factory.close_all()


data_source_manager = DataSourceManager()
