from typing import Optional, Dict, Any, Type, Union, List
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
from app.models.schemas import FundInfo
from .akshare_adapter import AkShareAdapter
from .baostock_adapter import BaostockAdapter
from .yfinance_adapter import YFinanceAdapter
from .efinance_adapter import EFinanceAdapter
from .tickflow_adapter import TickFlowAdapter
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
            DataSourceType.EFINANCE: (EFinanceAdapter, True),
            DataSourceType.TICKFLOW: (TickFlowAdapter, bool(settings.TICKFLOW_API_KEY)),  # 有 API Key 则启用
            DataSourceType.YFINANCE: (YFinanceAdapter, False),
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
        adjust: str = "qfk",
        source_type: Optional[str] = None
    ) -> list[KLineData]:
        adapter = self.get_adapter(source_type)
        # 将 adjust 转换为 fqt 参数传递给适配器
        fqt_map = {'qfk': 1, 'qfq': 1, 'hfq': 2, '': 0}
        fqt = fqt_map.get(adjust, 1)
        return await adapter.get_kline(code, start_date, end_date, fqt=fqt)
    
    async def get_market_index_kline(
        self,
        index_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list[KLineData]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_market_index_kline(index_code, start_date, end_date)
    
    async def get_realtime_quote(self, code: str, source_type: Optional[str] = None) -> Dict[str, Any]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_realtime_quote(code)
    
    async def get_market_realtime_quotes(
        self,
        market_types: Optional[list] = None,
        source_type: Optional[str] = None
    ) -> list:
        adapter = self.get_adapter(source_type)
        return await adapter.get_market_realtime_quotes(market_types)
    
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
    
    # ===== 基金相关方法 =====
    
    async def get_fund_codes(
        self,
        fund_type: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list[dict]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_fund_codes(fund_type)
    
    async def get_fund_base_info(
        self,
        fund_codes: Union[str, list[str]],
        source_type: Optional[str] = None
    ) -> Union[FundInfo, list[FundInfo]]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_fund_base_info(fund_codes)
    
    async def get_fund_realtime_increase_rate(
        self,
        fund_codes: Union[str, list[str]],
        source_type: Optional[str] = None
    ) -> Union[dict, list[dict]]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_fund_realtime_increase_rate(fund_codes)
    
    async def get_fund_quote_history(
        self,
        fund_code: str,
        pz: int = 40000,
        source_type: Optional[str] = None
    ) -> list[dict]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_fund_quote_history(fund_code, pz)
    
    async def get_fund_quote_history_multi(
        self,
        fund_codes: list[str],
        pz: int = 40000,
        source_type: Optional[str] = None
    ) -> dict:
        adapter = self.get_adapter(source_type)
        return await adapter.get_fund_quote_history_multi(fund_codes, pz)
    
    async def get_fund_invest_position(
        self,
        fund_code: str,
        dates: Optional[Union[str, list[str]]] = None,
        source_type: Optional[str] = None
    ) -> list[dict]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_fund_invest_position(fund_code, dates)
    
    async def get_fund_period_change(
        self,
        fund_code: str,
        source_type: Optional[str] = None
    ) -> list[dict]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_fund_period_change(fund_code)
    
    async def get_fund_types_percentage(
        self,
        fund_code: str,
        dates: Optional[Union[str, list[str]]] = None,
        source_type: Optional[str] = None
    ) -> list[dict]:
        adapter = self.get_adapter(source_type)
        return await adapter.get_fund_types_percentage(fund_code, dates)
    
    async def get_belong_board(
        self,
        code: str,
        source_type: Optional[str] = None
    ) -> list:
        adapter = self.get_adapter(source_type)
        return await adapter.get_belong_board(code)
    
    async def get_today_bill(
        self,
        trade_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list:
        adapter = self.get_adapter(source_type)
        return await adapter.get_today_bill(trade_date)
    
    async def get_history_bill(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list:
        adapter = self.get_adapter(source_type)
        return await adapter.get_history_bill(code, start_date, end_date)
    
    async def get_top10_stock_holder_info(
        self,
        code: str,
        top: int = 10,
        source_type: Optional[str] = None
    ) -> list:
        adapter = self.get_adapter(source_type)
        return await adapter.get_top10_stock_holder_info(code, top)
    
    async def close(self) -> None:
        await self._factory.close_all()


data_source_manager = DataSourceManager()
