"""
统一数据适配器基类

集成统一数据模型、存储路由、指标计算等功能的适配器基类
所有数据源适配器应继承此基类以获得统一功能
"""
from typing import Optional, List, Dict, Any, Type
from abc import ABC, abstractmethod
from datetime import datetime
from loguru import logger
import pandas as pd

from app.models.unified_models import (
    UnifiedKLine,
    DataSourceType,
    AdjustType,
    UnifiedRealtimeQuote
)
from app.utils.data_normalizer import DataNormalizer
from app.storage.storage_router import StorageRouter
from app.storage.parquet_manager import ParquetManager
from app.services.indicators_manager import IndicatorsManager
from app.utils.cross_source_validator import CrossSourceValidator
from app.utils.data_source_health import DataSourceHealthChecker

from .base import BaseDataAdapter
from .efinance_adapter import EFinanceAdapter
from .akshare_adapter import AkShareAdapter
from .baostock_adapter import BaostockAdapter
from .tickflow_adapter import TickFlowAdapter

# 延迟导入以避免循环依赖
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.utils.data_source_health import DataSourceHealthChecker


class UnifiedDataAdapter(BaseDataAdapter, ABC):
    """
    统一数据适配器基类
    
    提供以下功能：
    - 统一数据模型（UnifiedKLine）
    - 数据标准化转换
    - 智能存储路由（SQLite + Parquet）
    - 技术指标计算
    - 跨数据源校验
    - 健康状态监控
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 存储路由（90 天热数据阈值）
        self.storage_router = StorageRouter(hot_threshold_days=90)
        self.parquet_manager = ParquetManager()
        
        # 指标计算（优先使用 pandas-ta）
        self.indicators_manager = IndicatorsManager(prefer_talib=False)
        
        # 校验器（1% 容差率）
        self.validator = CrossSourceValidator(tolerance=0.01)
        
        # 健康检查器（延迟导入）
        from app.utils.data_source_health import DataSourceHealthChecker
        self.health_checker = DataSourceHealthChecker()
        
        # 降级策略配置
        self._fallback_chain = []
        self._setup_fallback_chain()
        
        logger.info(f"统一适配器初始化完成：{self.source_type.value}")
        logger.info(f"降级链路：{' -> '.join([s.value for s in self._fallback_chain])}")
    
    def _setup_fallback_chain(self):
        """设置数据源降级链路
        
        优先级：TickFlow > AkShare > EFinance > BaoStock > YFinance
        """
        self._fallback_chain = [
            DataSourceType.TICKFLOW,
            DataSourceType.AKSHARE,
            DataSourceType.EFINANCE,
            DataSourceType.BAOSTOCK,
            DataSourceType.YFINANCE
        ]
    
    @property
    @abstractmethod
    def source_type(self) -> DataSourceType:
        """返回数据源类型"""
        pass
    
    async def get_unified_kline(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust_type: str = "qfq",
        save_to_storage: bool = True,
        calculate_indicators: bool = False
    ) -> List[UnifiedKLine]:
        """
        获取统一格式的 K 线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            adjust_type: 复权类型（qfq/hfq/qfq）
            save_to_storage: 是否保存到存储
            calculate_indicators: 是否计算技术指标
            
        Returns:
            统一格式的 K 线数据列表
        """
        logger.info(f"获取 {code} K 线数据：{start_date} - {end_date}")
        
        # 步骤 1: 从子类获取原始数据
        raw_klines = await self._fetch_raw_kline(code, start_date, end_date)
        logger.info(f"获取原始数据：{len(raw_klines)} 条")
        
        # 步骤 2: 标准化为统一格式
        unified_klines = []
        for data in raw_klines:
            # 如果已经是字典，进行标准化；如果已经是 UnifiedKLine，直接使用
            if isinstance(data, dict):
                kline = DataNormalizer.normalize_kline(data, self.source_type)
                if kline:
                    unified_klines.append(kline)
            elif hasattr(data, 'model_dump'):
                # 如果已经是 Pydantic 模型，转换为字典再标准化
                kline = DataNormalizer.normalize_kline(data.model_dump(), self.source_type)
                if kline:
                    unified_klines.append(kline)
            else:
                # 未知格式，记录警告
                logger.warning(f"未知数据格式：{type(data)}")
        
        logger.info(f"标准化完成：{len(unified_klines)} 条")
        if len(raw_klines) > 0 and len(unified_klines) == 0:
            logger.error(f"标准化失败：原始数据{len(raw_klines)}条，但标准化后为 0 条")
            # 调试：显示第一条数据的结构
            if len(raw_klines) > 0:
                first = raw_klines[0]
                if hasattr(first, 'model_dump'):
                    logger.debug(f"数据示例：{first.model_dump()}")
                else:
                    logger.debug(f"数据示例：{first}")
        
        # 步骤 3: 数据验证
        valid_count = 0
        for kline in unified_klines:
            if DataNormalizer.validate_kline(kline):
                valid_count += 1
            else:
                logger.warning(f"数据验证失败：{kline.code} {kline.date}")
        
        logger.info(f"数据验证通过：{valid_count}/{len(unified_klines)} 条")
        
        # 步骤 4: 智能存储
        if save_to_storage and unified_klines:
            for kline in unified_klines:
                await self.storage_router.save_kline(
                    code,
                    kline.model_dump(),
                    adjust_type
                )
            logger.info(f"存储完成：{len(unified_klines)} 条")
        
        # 步骤 5: 计算技术指标（可选）
        if calculate_indicators and len(unified_klines) > 30:
            df = self._klines_to_dataframe(unified_klines)
            df_with_indicators = self.indicators_manager.calculate_all_indicators(df)
            logger.info(f"指标计算完成，数据形状：{df_with_indicators.shape}")
            
            # 将指标数据附加到 K 线对象
            self._attach_indicators(unified_klines, df_with_indicators)
        
        return unified_klines
    
    async def get_unified_kline_batch(
        self,
        codes: List[str],
        start_date: str,
        end_date: str,
        adjust_type: str = "qfq",
        save_to_storage: bool = True,
        max_concurrent: int = 3
    ) -> Dict[str, List[UnifiedKLine]]:
        """
        批量获取统一格式 K 线数据
        
        Args:
            codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            adjust_type: 复权类型
            save_to_storage: 是否保存到存储
            max_concurrent: 最大并发数
            
        Returns:
            字典：{code: [UnifiedKLine]}
        """
        logger.info(f"批量获取 {len(codes)} 只股票的 K 线数据")
        
        results = {}
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def fetch_with_semaphore(code):
            async with semaphore:
                try:
                    klines = await self.get_unified_kline(
                        code, start_date, end_date, adjust_type, save_to_storage
                    )
                    return code, klines
                except Exception as e:
                    logger.error(f"获取 {code} 数据失败：{e}")
                    return code, []
        
        tasks = [fetch_with_semaphore(code) for code in codes]
        results_list = await asyncio.gather(*tasks)
        
        for code, klines in results_list:
            results[code] = klines
        
        success_count = sum(1 for klines in results.values() if klines)
        total_count = sum(len(klines) for klines in results.values())
        
        logger.info(f"批量获取完成：成功 {success_count}/{len(codes)}，共 {total_count} 条数据")
        
        return results
    
    async def validate_across_sources(
        self,
        code: str,
        date: str,
        other_adapter: 'UnifiedDataAdapter'
    ) -> Dict[str, Any]:
        """
        跨数据源一致性校验
        
        Args:
            code: 股票代码
            date: 日期
            other_adapter: 另一个数据源适配器
            
        Returns:
            校验结果
        """
        logger.info(f"跨数据源校验：{code} {date}")
        
        # 从两个数据源获取数据
        klines_self = await self.get_unified_kline(code, date, date, save_to_storage=False)
        klines_other = await other_adapter.get_unified_kline(code, date, date, save_to_storage=False)
        
        if not klines_self or not klines_other:
            return {
                "status": "error",
                "message": "数据源数据不足"
            }
        
        # 校验
        result = await self.validator.validate(
            code,
            date,
            [klines_self, klines_other],
            [self.source_type, other_adapter.source_type]
        )
        
        return result
    
    async def check_health(self) -> Dict[str, Any]:
        """
        检查数据源健康状态
        
        Returns:
            健康状态
        """
        result = await self.health_checker.check_all_sources()
        return result.get(self.source_type.value, {})
    
    async def get_kline_with_fallback(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust: str = "qfq",
        exclude_sources: Optional[List[DataSourceType]] = None
    ) -> tuple[Optional['UnifiedDataAdapter'], List[UnifiedKLine]]:
        """带降级策略的 K 线获取
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            exclude_sources: 要排除的数据源列表
            
        Returns:
            (使用的适配器，K 线数据列表)
        """
        exclude_set = set(exclude_sources) if exclude_sources else set()
        
        for source_type in self._fallback_chain:
            if source_type in exclude_set:
                logger.debug(f"跳过数据源：{source_type.value}")
                continue
            
            try:
                # 获取对应适配器
                adapter = self._get_adapter_for_source(source_type)
                if not adapter:
                    logger.warning(f"无法获取数据源适配器：{source_type.value}")
                    continue
                
                logger.info(f"尝试从 {source_type.value} 获取数据...")
                
                # 获取数据
                klines = await adapter.get_unified_kline(
                    code, start_date, end_date,
                    adjust_type=adjust,
                    save_to_storage=False
                )
                
                if klines:
                    logger.info(f"成功从 {source_type.value} 获取 {len(klines)} 条数据")
                    return (adapter, klines)
                else:
                    logger.debug(f"{source_type.value} 返回空数据")
                    
            except Exception as e:
                logger.error(f"从 {source_type.value} 获取数据失败：{e}")
                continue
        
        logger.error(f"所有数据源都无法获取 K 线数据 {code}")
        return (None, [])
    
    def _get_adapter_for_source(self, source_type: DataSourceType) -> Optional['UnifiedDataAdapter']:
        """根据数据源类型获取对应的适配器实例
        
        Args:
            source_type: 数据源类型
            
        Returns:
            适配器实例或 None
        """
        # 这里需要根据实际项目结构调整
        # 示例实现：
        adapter_map = {
            DataSourceType.TICKFLOW: TickFlowAdapter,
            DataSourceType.AKSHARE: AkShareAdapter,
            DataSourceType.EFINANCE: EFinanceAdapter,
            DataSourceType.BAOSTOCK: BaostockAdapter,
            # Tushare 和 YFinance 需要根据实际情况添加
        }
        
        adapter_class = adapter_map.get(source_type)
        if adapter_class:
            return adapter_class()
        
        return None
    
    @abstractmethod
    async def _fetch_raw_kline(
        self,
        code: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """
        获取原始 K 线数据（子类实现）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            原始 K 线数据列表
        """
        pass
    
    def _klines_to_dataframe(self, klines: List[UnifiedKLine]) -> pd.DataFrame:
        """
        将统一 K 线数据转换为 DataFrame
        
        Args:
            klines: 统一 K 线数据列表
            
        Returns:
            pandas DataFrame
        """
        data = []
        for k in klines:
            data.append({
                "date": k.date,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "volume": k.volume,
                "amount": k.amount if k.amount else k.volume * k.close
            })
        
        df = pd.DataFrame(data)
        df.set_index("date", inplace=True)
        return df
    
    def _attach_indicators(
        self,
        klines: List[UnifiedKLine],
        df_with_indicators: pd.DataFrame
    ):
        """
        将指标数据附加到 K 线对象
        
        Args:
            klines: 统一 K 线数据列表
            df_with_indicators: 包含指标的 DataFrame
        """
        # 将指标数据添加到 K 线对象的额外字段
        for i, kline in enumerate(klines):
            if i < len(df_with_indicators):
                row = df_with_indicators.iloc[i]
                # 可以添加到 kline 的 extra 字段或创建新字段
                # 这里简化处理，仅记录日志
                pass


# 导入 asyncio（在文件顶部可能缺失）
import asyncio


class EFinanceUnifiedAdapter(EFinanceAdapter, UnifiedDataAdapter):
    """
    efinance 统一适配器
    
    继承 EFinanceAdapter 和 UnifiedDataAdapter，获得统一功能
    """
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.EFINANCE
    
    async def _fetch_raw_kline(
        self,
        code: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """从 efinance 获取原始 K 线数据"""
        # 调用父类 EFinanceAdapter 的方法
        if hasattr(super(), 'get_kline'):
            # get_kline 返回的是 KLineData 对象列表，需要转换为字典
            klines = await super().get_kline(code, start_date, end_date)
            return [k.model_dump() if hasattr(k, 'model_dump') else k for k in klines]
        else:
            # 如果没有现成方法，使用现有逻辑
            return await self._get_kline_data(code, start_date, end_date)


class AkShareUnifiedAdapter(AkShareAdapter, UnifiedDataAdapter):
    """
    akshare 统一适配器
    """
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.AKSHARE
    
    async def _fetch_raw_kline(
        self,
        code: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """从 akshare 获取原始 K 线数据"""
        if hasattr(super(), 'get_kline'):
            klines = await super().get_kline(code, start_date, end_date)
            return [k.model_dump() if hasattr(k, 'model_dump') else k for k in klines]
        else:
            return await self._get_kline_data(code, start_date, end_date)


class BaostockUnifiedAdapter(BaostockAdapter, UnifiedDataAdapter):
    """
    baostock 统一适配器
    """
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.BAOSTOCK
    
    async def _fetch_raw_kline(
        self,
        code: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """从 baostock 获取原始 K 线数据"""
        if hasattr(super(), 'get_kline'):
            klines = await super().get_kline(code, start_date, end_date)
            return [k.model_dump() if hasattr(k, 'model_dump') else k for k in klines]
        else:
            return await self._get_kline_data(code, start_date, end_date)


class TickFlowUnifiedAdapter(TickFlowAdapter, UnifiedDataAdapter):
    """
    TickFlow 统一适配器
    """
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.TICKFLOW
    
    async def _fetch_raw_kline(
        self,
        code: str,
        start_date: str,
        end_date: str
    ) -> List[Dict[str, Any]]:
        """从 TickFlow 获取原始 K 线数据"""
        if hasattr(super(), 'get_kline'):
            klines = await super().get_kline(code, start_date, end_date)
            return [k.model_dump() if hasattr(k, 'model_dump') else k for k in klines]
        else:
            return await self._get_kline_data(code, start_date, end_date)
