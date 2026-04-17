"""
因子计算引擎

核心引擎类，管理因子计算的完整生命周期。
"""

from typing import Dict, List, Optional, Any, Union
import time
from loguru import logger

import pandas as pd
import numpy as np

from .calculator import BaseFactorCalculator, FactorResult
from .registry import FactorRegistry, get_registry


class FactorEngine:
    """
    因子计算引擎（工厂模式）
    
    管理和调度所有因子的计算，支持：
    - 批量计算多个因子
    - 并行计算（可选 Ray）
    - 缓存机制
    - 进度跟踪
    
    使用示例：
        engine = FactorEngine()
        engine.initialize()
        
        # 计算单个因子
        result = engine.calculate("MOMENTUM_20", data)
        
        # 批量计算
        results = engine.calculate_batch(data, ["MOMENTUM_20", "VALUE", "VOLATILITY_20"])
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._registry: Optional[FactorRegistry] = None
        self._cache: Dict[str, FactorResult] = {}
        self._cache_ttl: int = config.get("cache_ttl", 300) if config else 300
        self._initialized = False
        
        # 统计信息
        self._stats = {
            "total_calculations": 0,
            "cache_hits": 0,
            "calculation_errors": 0,
            "total_time": 0.0
        }
    
    @property
    def registry(self) -> FactorRegistry:
        """获取注册表"""
        if self._registry is None:
            self._registry = get_registry()
        return self._registry
    
    def initialize(self):
        """初始化引擎"""
        if self._initialized:
            return
        
        logger.info("初始化 FactorEngine...")
        
        # 初始化注册表
        self.registry.initialize()
        
        self._initialized = True
        logger.info("FactorEngine 初始化完成")
    
    def calculate(
        self,
        factor_name: str,
        data: pd.DataFrame,
        use_cache: bool = True,
        **kwargs
    ) -> FactorResult:
        """
        计算单个因子
        
        Args:
            factor_name: 因子名称
            data: 输入数据 DataFrame
            use_cache: 是否使用缓存
            **kwargs: 额外参数
            
        Returns:
            FactorResult: 因子计算结果
        """
        start_time = time.time()
        
        # 检查缓存
        cache_key = f"{factor_name}_{hash(str(data.shape))}"
        if use_cache and cache_key in self._cache:
            self._stats["cache_hits"] += 1
            return self._cache[cache_key]
        
        # 获取计算器
        calculator = self.registry.get(factor_name)
        if calculator is None:
            raise ValueError(f"未找到因子: {factor_name}")
        
        try:
            # 计算
            result = calculator.process(data, **kwargs)
            
            # 更新统计
            self._stats["total_calculations"] += 1
            self._stats["total_time"] += result.calculation_time
            
            # 存入缓存
            if use_cache:
                self._cache[cache_key] = result
            
            return result
            
        except Exception as e:
            self._stats["calculation_errors"] += 1
            logger.error(f"计算因子 {factor_name} 失败: {e}")
            raise
    
    def calculate_batch(
        self,
        data: pd.DataFrame,
        factor_names: Optional[List[str]] = None,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        use_cache: bool = True,
        parallel: bool = False,
        **kwargs
    ) -> pd.DataFrame:
        """
        批量计算多个因子
        
        Args:
            data: 输入数据 DataFrame
            factor_names: 要计算的因子列表（None=全部或按类别/标签过滤）
            category: 按类别过滤 (market/fundamental/alternative/structured)
            tag: 按标签过滤
            use_cache: 是否使用缓存
            parallel: 是否并行计算
            **kwargs: 额外参数
            
        Returns:
            DataFrame: 各股票的因子值（index=股票代码，columns=因子名）
        """
        from .calculator import FactorCategory
        
        # 确定要计算的因子列表
        if factor_names is None:
            cat = FactorCategory(category) if category else None
            factor_names = self.registry.list_factors(
                category=cat,
                tag=tag,
                enabled_only=True
            )
        
        if not factor_names:
            logger.warning("没有可用的因子")
            return pd.DataFrame()
        
        logger.info(f"开始批量计算 {len(factor_names)} 个因子...")
        
        results = {}
        
        if parallel and len(factor_names) > 3:
            results = self._calculate_parallel(data, factor_names, **kwargs)
        else:
            for name in factor_names:
                try:
                    result = self.calculate(name, data, use_cache=use_cache, **kwargs)
                    if result.values is not None and len(result.values) > 0:
                        results[name] = result.values
                except Exception as e:
                    logger.debug(f"因子 {name} 计算跳过: {e}")
                    continue
        
        if results:
            df = pd.DataFrame(results)
            logger.info(f"批量计算完成，生成 {df.shape} 的因子矩阵")
            return df
        
        return pd.DataFrame()
    
    def _calculate_parallel(
        self,
        data: pd.DataFrame,
        factor_names: List[str],
        **kwargs
    ) -> Dict[str, pd.Series]:
        """并行计算因子"""
        try:
            import ray
            
            if not ray.is_initialized():
                ray.init(ignore_reinit_error=True)
            
            @ray.remote
            def calc_remote(engine_state, name, data_shape):
                calculator = engine_state.get(name)
                if calculator:
                    result = calculator.process(data)
                    return name, result.values
                return name, None
            
            futures = [
                calc_remote.remote(
                    {name: self.registry.get(name) for name in factor_names},
                    name,
                    data.shape
                )
                for name in factor_names
            ]
            
            results = {}
            for future in ray.get(futures):
                if future:
                    name, values = future
                    if values is not None:
                        results[name] = values
            
            return results
            
        except ImportError:
            logger.warning("Ray 未安装，使用串行计算")
            return self._calculate_serial(data, factor_names, **kwargs)
    
    def _calculate_serial(
        self,
        data: pd.DataFrame,
        factor_names: List[str],
        **kwargs
    ) -> Dict[str, pd.Series]:
        """串行计算"""
        results = {}
        for name in factor_names:
            try:
                result = self.calculate(name, data, **kwargs)
                if result.values is not None:
                    results[name] = result.values
            except Exception:
                continue
        return results
    
    def calculate_for_symbols(
        self,
        data_dict: Dict[str, pd.DataFrame],
        factor_names: List[str],
        **kwargs
    ) -> Dict[str, pd.DataFrame]:
        """
        为多只股票计算因子
        
        Args:
            data_dict: {symbol: DataFrame} 数据字典
            factor_names: 因子列表
            
        Returns:
            {symbol: DataFrame of factors}
        """
        results = {}
        
        for symbol, data in data_dict.items():
            try:
                factors = self.calculate_batch(data, factor_names, **kwargs)
                if not factors.empty:
                    results[symbol] = factors
            except Exception as e:
                logger.debug(f"计算 {symbol} 因子失败: {e}")
                continue
        
        return results
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        logger.debug("因子缓存已清除")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取引擎统计"""
        return {
            **self._stats,
            "cached_factors": len(self._cache),
            "registered_factors": self.registry.count(),
            "is_initialized": self._initialized
        }
    
    def list_available_factors(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出可用因子及其详细信息
        
        Returns:
            因子列表，每个因子包含名称、类别、描述、标签等
        """
        from .calculator import FactorCategory
        
        cat = FactorCategory(category) if category else None
        names = self.registry.list_factors(category=cat, tag=tag)
        
        factors_info = []
        for name in names:
            spec = self.registry.get_spec(name)
            info = self.registry._factors.get(name)
            
            factors_info.append({
                "name": name,
                "category": spec.category.value if spec else "unknown",
                "description": spec.description if spec else "",
                "frequency": spec.frequency if spec else "",
                "lookback_window": spec.lookback_window if spec else 0,
                "tags": info.tags if info else [],
                "enabled": info.enabled if info else True
            })
        
        return factors_info
    
    def validate_factor(self, factor_name: str, data: pd.DataFrame) -> bool:
        """
        验证因子有效性
        
        检查：
        - 因子是否存在
        - 数据是否完整
        - 结果是否有效
        
        Args:
            factor_name: 因子名称
            data: 测试数据
            
        Returns:
            是否有效
        """
        calculator = self.registry.get(factor_name)
        if calculator is None:
            return False
        
        if not calculator.validate_input(data):
            return False
        
        try:
            result = calculator.process(data)
            if result.values is None or len(result.values) == 0:
                return False
            
            valid_ratio = result.metadata.get("valid_count", 0) / result.metadata.get("total_count", 1)
            return valid_ratio > 0.5
            
        except Exception:
            return False
