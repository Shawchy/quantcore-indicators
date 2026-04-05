from typing import Optional, Dict, Any, Type, Union, List
from enum import Enum
from loguru import logger
import time
import asyncio

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

# 导入统一策略配置
from .strategy_config import (
    UNIFIED_DATA_STRATEGY,
    ADAPTER_CONFIG,
    get_priority_sources,
    get_strategy,
    is_adapter_enabled,
    DataSourceType as StrategyDataSourceType,
)

# 导入优化模块
from .dynamic_priority import dynamic_priority_manager, DataSourcePerformance
from .batch_optimizer import batch_optimizer, BatchRequestOptimizer
from .smart_preloader import smart_preloader, SmartPreloader


class DataSourceFactory:
    """数据源工厂 - 使用统一策略配置"""
    
    _adapters: Dict[DataSourceType, BaseDataAdapter] = {}
    _initialized: bool = False
    
    # 适配器类映射
    _ADAPTER_CLASSES = {
        DataSourceType.AKSHARE: AkShareAdapter,
        DataSourceType.BAOSTOCK: BaostockAdapter,
        DataSourceType.EFINANCE: EFinanceAdapter,
        DataSourceType.TICKFLOW: TickFlowAdapter,
        DataSourceType.YFINANCE: YFinanceAdapter,
    }
    
    @classmethod
    async def initialize(cls, default_source: Optional[str] = None) -> None:
        """初始化数据源工厂 - 使用统一配置"""
        if cls._initialized:
            return
        
        default = default_source or settings.DEFAULT_DATA_SOURCE
        
        # 使用统一策略配置初始化适配器
        for source_type in DataSourceType:
            # 检查适配器是否启用
            strategy_source = StrategyDataSourceType(source_type.value)
            if not is_adapter_enabled(strategy_source):
                logger.debug(f"数据源 {source_type.value} 已禁用，跳过初始化")
                continue
            
            # 特殊处理 TickFlow（需要 API Key）
            if source_type == DataSourceType.TICKFLOW:
                if not settings.TICKFLOW_API_KEY:
                    logger.info("TickFlow API Key 未配置，跳过初始化")
                    continue
            
            adapter_class = cls._ADAPTER_CLASSES.get(source_type)
            if not adapter_class:
                continue
            
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
        """获取适配器"""
        if not cls._initialized:
            raise RuntimeError("数据源工厂未初始化，请先调用 initialize()")
        
        if source_type:
            source = DataSourceType(source_type)
        else:
            source = DataSourceType(settings.DEFAULT_DATA_SOURCE)
        
        if source not in cls._adapters:
            # 使用统一配置获取备选数据源
            fallback_priority = get_priority_sources("stock_list")
            for fallback_source in fallback_priority:
                fallback_type = DataSourceType(fallback_source.value)
                if fallback_type in cls._adapters:
                    logger.warning(f"数据源 {source.value} 不可用，使用 {fallback_source.value} 作为备选")
                    return cls._adapters[fallback_type]
            raise ValueError(f"数据源 {source.value} 不可用")
        
        return cls._adapters[source]
    
    @classmethod
    def get_available_sources(cls) -> list[str]:
        """获取可用数据源列表"""
        return [s.value for s in cls._adapters.keys()]
    
    @classmethod
    async def close_all(cls) -> None:
        """关闭所有数据源"""
        for adapter in cls._adapters.values():
            try:
                await adapter.close()
            except Exception as e:
                logger.error(f"关闭数据源 {adapter.source_type.value} 失败: {e}")
        
        cls._adapters.clear()
        cls._initialized = False
        logger.info("所有数据源已关闭")


class DataSourceManager:
    """数据源管理器 - 使用统一策略配置和智能优化"""
    
    def __init__(self, default_source: Optional[str] = None):
        self._default_source = default_source or settings.DEFAULT_DATA_SOURCE
        self._factory = DataSourceFactory
        self._dynamic_priority = dynamic_priority_manager
        self._batch_optimizer = batch_optimizer
        self._smart_preloader = smart_preloader
        self._enable_optimization = True
    
    async def initialize(self) -> None:
        """初始化数据源管理器"""
        await self._factory.initialize(self._default_source)
        
        # 启动优化模块
        if self._enable_optimization:
            await self._dynamic_priority.start()
            await self._smart_preloader.start()
            logger.info("数据源优化模块已启动")
    
    async def close(self) -> None:
        """关闭所有数据源和优化模块"""
        # 关闭优化模块
        if self._enable_optimization:
            await self._dynamic_priority.stop()
            await self._smart_preloader.stop()
            logger.info("数据源优化模块已停止")
        
        # 关闭数据源
        await self._factory.close_all()
    
    def get_adapter(self, source_type: Optional[str] = None) -> BaseDataAdapter:
        """获取适配器"""
        return self._factory.get_adapter(source_type)
    
    def _get_source_priority(self, data_type: str) -> List[str]:
        """
        获取指定数据类型的数据源优先级列表 - 使用动态优先级
        
        Args:
            data_type: 数据类型（如 'kline', 'realtime_quote' 等）
        
        Returns:
            数据源优先级列表
        """
        # 使用动态优先级（如果启用优化）
        if self._enable_optimization:
            priority_sources = self._dynamic_priority.get_priority(data_type)
        else:
            priority_sources = get_priority_sources(data_type)
        
        available = self._factory.get_available_sources()
        
        # 过滤掉不可用的数据源
        filtered = [s.value for s in priority_sources if s.value in available]
        
        # 如果没有可用的，返回默认优先级
        if not filtered:
            default_priority = get_priority_sources("stock_list")
            filtered = [s.value for s in default_priority if s.value in available]
        
        return filtered
    
    def _get_cache_ttl(self, data_type: str) -> int:
        """获取数据类型的缓存 TTL - 使用统一策略配置"""
        from .strategy_config import get_cache_ttl
        return get_cache_ttl(data_type)
    
    async def _try_sources(self, data_type: str, method_name: str, *args, **kwargs) -> Any:
        """
        按优先级尝试多个数据源 - 使用统一策略配置和性能统计
        
        Args:
            data_type: 数据类型
            method_name: 方法名
            *args, **kwargs: 方法参数
        
        Returns:
            数据结果或 None
        """
        source_priority = self._get_source_priority(data_type)
        strategy = get_strategy(data_type)
        last_error = None
        
        for i, source in enumerate(source_priority):
            start_time = time.time()
            source_type_enum = StrategyDataSourceType(source)
            
            try:
                adapter = self.get_adapter(source)
                method = getattr(adapter, method_name)
                result = await method(*args, **kwargs)
                
                # 记录成功
                response_time = time.time() - start_time
                if self._enable_optimization:
                    self._dynamic_priority.record_request(
                        source=source_type_enum,
                        data_type=data_type,
                        success=True,
                        response_time=response_time
                    )
                
                if result is not None:
                    logger.debug(f"数据源 {source} {method_name} 成功，耗时: {response_time:.3f}s")
                    return result
                    
            except Exception as e:
                last_error = e
                response_time = time.time() - start_time
                
                # 记录失败
                if self._enable_optimization:
                    self._dynamic_priority.record_request(
                        source=source_type_enum,
                        data_type=data_type,
                        success=False,
                        response_time=response_time
                    )
                
                logger.warning(f"数据源 {source} {method_name} 失败: {e}")
                
                # 检查是否启用故障转移
                if strategy and not strategy.enable_fallback:
                    logger.info(f"{data_type} 禁用故障转移，停止尝试")
                    break
                
                continue
        
        if last_error:
            logger.error(f"所有数据源 {method_name} 失败")
        return None
    
    # ===== 股票相关方法 =====
    
    async def get_stock_list(self, source_type: Optional[str] = None) -> list[StockBasicInfo]:
        """获取股票列表"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_stock_list()
        result = await self._try_sources("stock_list", "get_stock_list")
        return result or []
    
    async def get_stock_info(self, code: str, source_type: Optional[str] = None) -> Optional[StockBasicInfo]:
        """获取股票信息"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_stock_info(code)
        return await self._try_sources("stock_info", "get_stock_info", code)
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq",
        source_type: Optional[str] = None
    ) -> list[KLineData]:
        """获取 K 线数据"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_kline(code, start_date, end_date, adjust=adjust)
        
        result = await self._try_sources("kline", "get_kline", code, start_date, end_date, adjust=adjust)
        return result or []
    
    async def get_market_index_kline(
        self,
        index_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list[KLineData]:
        """获取指数 K 线数据"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_market_index_kline(index_code, start_date, end_date)
        
        result = await self._try_sources("index_kline", "get_market_index_kline", index_code, start_date, end_date)
        return result or []
    
    async def get_realtime_quote(self, code: str, source_type: Optional[str] = None) -> Dict[str, Any]:
        """获取实时行情"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_realtime_quote(code)
        
        result = await self._try_sources("realtime_quote", "get_realtime_quote", code)
        return result or {}
    
    async def get_market_realtime_quotes(
        self,
        market_types: Optional[list] = None,
        source_type: Optional[str] = None
    ) -> list:
        """获取市场实时行情列表"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_market_realtime_quotes(market_types)
        
        result = await self._try_sources("market_quotes", "get_market_realtime_quotes", market_types)
        return result or []
    
    # ===== 板块相关方法 =====
    
    async def get_sector_list(self, sector_type: str = "industry", source_type: Optional[str] = None) -> list[SectorInfo]:
        """获取板块列表"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_sector_list(sector_type)
        
        result = await self._try_sources("sector", "get_sector_list", sector_type)
        return result or []
    
    async def get_sector_components(self, sector_code: str, source_type: Optional[str] = None) -> list[str]:
        """获取板块成分股"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_sector_components(sector_code)
        
        result = await self._try_sources("sector", "get_sector_components", sector_code)
        return result or []
    
    # ===== 筹码相关方法 =====
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list[ChipData]:
        """获取筹码数据"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_chip_data(code, start_date, end_date)
        
        result = await self._try_sources("chip", "get_chip_data", code, start_date, end_date)
        return result or []
    
    # ===== 基金相关方法 =====
    
    async def get_fund_codes(
        self,
        fund_type: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list[dict]:
        """获取基金代码列表"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_fund_codes(fund_type)
        
        result = await self._try_sources("fund", "get_fund_codes", fund_type)
        return result or []
    
    async def get_fund_base_info(
        self,
        fund_codes: Union[str, list[str]],
        source_type: Optional[str] = None
    ) -> Union[FundInfo, list[FundInfo]]:
        """获取基金基本信息"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_fund_base_info(fund_codes)
        
        result = await self._try_sources("fund", "get_fund_base_info", fund_codes)
        return result
    
    async def get_fund_realtime_increase_rate(
        self,
        fund_codes: Union[str, list[str]],
        source_type: Optional[str] = None
    ) -> Union[dict, list[dict]]:
        """获取基金实时涨跌幅"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_fund_realtime_increase_rate(fund_codes)
        
        result = await self._try_sources("fund", "get_fund_realtime_increase_rate", fund_codes)
        return result or {}
    
    async def get_fund_quote_history(
        self,
        fund_code: str,
        pz: int = 40000,
        source_type: Optional[str] = None
    ) -> list[dict]:
        """获取基金历史行情"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_fund_quote_history(fund_code, pz)
        
        result = await self._try_sources("fund", "get_fund_quote_history", fund_code, pz)
        return result or []
    
    async def get_fund_quote_history_multi(
        self,
        fund_codes: list[str],
        pz: int = 40000,
        source_type: Optional[str] = None
    ) -> dict:
        """获取多只基金历史行情"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_fund_quote_history_multi(fund_codes, pz)
        
        result = await self._try_sources("fund", "get_fund_quote_history_multi", fund_codes, pz)
        return result or {}
    
    async def get_fund_invest_position(
        self,
        fund_code: str,
        dates: Optional[Union[str, list[str]]] = None,
        source_type: Optional[str] = None
    ) -> list[dict]:
        """获取基金持仓信息"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_fund_invest_position(fund_code, dates)
        
        result = await self._try_sources("fund", "get_fund_invest_position", fund_code, dates)
        return result or []
    
    async def get_fund_period_change(
        self,
        fund_code: str,
        source_type: Optional[str] = None
    ) -> list[dict]:
        """获取基金阶段涨跌幅"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_fund_period_change(fund_code)
        
        result = await self._try_sources("fund", "get_fund_period_change", fund_code)
        return result or []
    
    async def get_fund_types_percentage(
        self,
        fund_code: str,
        dates: Optional[Union[str, list[str]]] = None,
        source_type: Optional[str] = None
    ) -> list[dict]:
        """获取基金持仓类型占比"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_fund_types_percentage(fund_code, dates)
        
        result = await self._try_sources("fund", "get_fund_types_percentage", fund_code, dates)
        return result or []
    
    # ===== 资金流向相关方法 =====
    
    async def get_belong_board(
        self,
        code: str,
        source_type: Optional[str] = None
    ) -> list:
        """获取股票所属板块"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_belong_board(code)
        
        result = await self._try_sources("billboard", "get_belong_board", code)
        return result or []
    
    async def get_today_bill(
        self,
        trade_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list:
        """获取今日资金流向"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_today_bill(trade_date)
        
        result = await self._try_sources("moneyflow", "get_today_bill", trade_date)
        return result or []
    
    async def get_history_bill(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        source_type: Optional[str] = None
    ) -> list:
        """获取历史资金流向"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_history_bill(code, start_date, end_date)
        
        result = await self._try_sources("moneyflow", "get_history_bill", code, start_date, end_date)
        return result or []
    
    # ===== 财务相关方法 =====
    
    async def get_top10_stock_holder_info(
        self,
        code: str,
        top: int = 10,
        source_type: Optional[str] = None
    ) -> list:
        """获取前十大股东信息"""
        if source_type:
            adapter = self.get_adapter(source_type)
            return await adapter.get_top10_stock_holder_info(code, top)
        
        result = await self._try_sources("financial", "get_top10_stock_holder_info", code, top)
        return result or []
    
    # ===== 优化相关方法 =====
    
    def enable_optimization(self, enabled: bool = True):
        """启用或禁用优化"""
        self._enable_optimization = enabled
        logger.info(f"数据源优化已{'启用' if enabled else '禁用'}")
    
    def record_user_request(self, user_id: str, data_type: str, code: Optional[str] = None):
        """记录用户请求（用于智能预加载）"""
        if self._enable_optimization:
            self._smart_preloader.record_user_request(user_id, data_type, code)
    
    def get_preloaded_data(self, data_type: str, code: str) -> Optional[Any]:
        """获取预加载的数据"""
        if self._enable_optimization:
            return self._smart_preloader.get_preloaded_data(data_type, code)
        return None
    
    def get_strategy_info(self, data_type: str) -> Optional[Dict[str, Any]]:
        """获取数据类型的策略信息"""
        from .strategy_config import get_strategy, get_client_config
        
        strategy = get_strategy(data_type)
        if not strategy:
            return None
        
        client_config = get_client_config(data_type)
        
        return {
            "data_type": data_type,
            "priority": [s.value for s in strategy.priority],
            "sensitivity": strategy.sensitivity.value,
            "preferred_client": client_config["preferred"],
            "fallback_client": client_config["fallback"],
            "cache_ttl": strategy.cache_ttl,
            "enable_fallback": strategy.enable_fallback,
            "enable_health_check": strategy.enable_health_check,
        }
    
    def get_all_strategies(self) -> Dict[str, Dict[str, Any]]:
        """获取所有数据类型的策略信息"""
        from .strategy_config import get_all_data_types
        
        return {
            data_type: self.get_strategy_info(data_type)
            for data_type in get_all_data_types()
        }
    
    def get_optimization_stats(self) -> Dict[str, Any]:
        """获取优化统计信息"""
        if not self._enable_optimization:
            return {"optimization_enabled": False}
        
        return {
            "optimization_enabled": True,
            "dynamic_priority": self._dynamic_priority.get_priority_report(),
            "smart_preloader": self._smart_preloader.get_stats(),
            "batch_optimizer": self._batch_optimizer.get_stats(),
        }
    
    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        if not self._enable_optimization:
            return {"optimization_enabled": False}
        
        return self._dynamic_priority.get_priority_report()


# 全局数据源管理器实例
data_source_manager = DataSourceManager()
