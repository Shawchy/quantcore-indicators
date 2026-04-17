"""
因子注册中心

管理所有因子的注册、查询和发现。
"""

from typing import Dict, List, Optional, Type
from dataclasses import dataclass, field
from loguru import logger

from .calculator import (
    BaseFactorCalculator,
    FactorCategory,
    FactorSpec,
    MomentumCalculator,
    ReversalCalculator,
    VolatilityCalculator,
    LiquidityCalculator,
    ValueCalculator,
    QualityCalculator,
    GrowthCalculator,
    SentimentCalculator,
    FundFlowCalculator,
    EventDriverCalculator,
)


@dataclass
class RegisteredFactor:
    """已注册的因子信息"""
    spec: FactorSpec
    calculator: BaseFactorCalculator
    enabled: bool = True
    tags: List[str] = field(default_factory=list)


class FactorRegistry:
    """
    因子注册中心（单例模式）
    
    管理所有可用的因子计算器，支持：
    - 因子注册与注销
    - 按类别查询
    - 标签过滤
    - 依赖关系管理
    """
    
    _instance: Optional['FactorRegistry'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._factors: Dict[str, RegisteredFactor] = {}
            cls._instance._initialized = False
        return cls._instance
    
    @classmethod
    def get_instance(cls) -> 'FactorRegistry':
        """获取单例实例"""
        return cls()
    
    def initialize(self):
        """初始化默认因子库"""
        if self._initialized:
            return
        
        logger.info("初始化因子注册中心...")
        
        # Market Data Factors
        for period in [5, 10, 20, 60, 120, 250]:
            self.register(MomentumCalculator(period), tags=["momentum", "market"])
            self.register(ReversalCalculator(period), tags=["reversal", "market"])
            self.register(VolatilityCalculator(period), tags=["volatility", "market", "low_vol"])
        
        self.register(LiquidityCalculator("amihud"), tags=["liquidity", "market"])
        self.register(LiquidityCalculator("turnover"), tags=["liquidity", "market"])
        
        # Fundamental Data Factors
        self.register(ValueCalculator(["pe", "pb"]), tags=["value", "fundamental"])
        self.register(ValueCalculator(["pe", "pb", "ps"]), tags=["value", "fundamental", "comprehensive"])
        self.register(QualityCalculator(["roe", "gross_margin"]), tags=["quality", "fundamental"])
        self.register(GrowthCalculator(["revenue_growth", "net_profit_growth"]), tags=["growth", "fundamental"])
        
        # Alternative Data Factors
        self.register(SentimentCalculator("news"), tags=["sentiment", "alternative", "nlp"])
        self.register(SentimentCalculator("social"), tags=["sentiment", "alternative", "nlp"])
        self.register(FundFlowCalculator("main_net"), tags=["fund_flow", "alternative"])
        self.register(FundFlowCalculator("northbound"), tags=["northbound", "alternative"])
        self.register(FundFlowCalculator("lhb"), tags=["lhb", "alternative"])
        self.register(EventDriverCalculator("limit_up"), tags=["event", "alternative"])
        self.register(EventDriverCalculator("lhb_appear"), tags=["event", "alternative"])
        
        self._initialized = True
        logger.info(f"因子注册完成，共 {len(self._factors)} 个因子")
    
    def register(self, calculator: BaseFactorCalculator, tags: List[str] = None):
        """
        注册因子计算器
        
        Args:
            calculator: 因子计算器实例
            tags: 标签列表
        """
        factor_info = RegisteredFactor(
            spec=calculator.spec,
            calculator=calculator,
            tags=tags or []
        )
        self._factors[calculator.spec.name] = factor_info
        
        if not hasattr(self, '_category_index'):
            self._category_index: Dict[FactorCategory, List[str]] = {}
        
        category = calculator.spec.category
        if category not in self._category_index:
            self._category_index[category] = []
        self._category_index[category].append(calculator.spec.name)
    
    def unregister(self, name: str) -> bool:
        """
        注销因子
        
        Args:
            name: 因子名称
            
        Returns:
            是否成功注销
        """
        if name in self._factors:
            del self._factors[name]
            return True
        return False
    
    def get(self, name: str) -> Optional[BaseFactorCalculator]:
        """
        获取因子计算器
        
        Args:
            name: 因子名称
            
        Returns:
            因子计算器或 None
        """
        factor_info = self._factors.get(name)
        if factor_info and factor_info.enabled:
            return factor_info.calculator
        return None
    
    def get_spec(self, name: str) -> Optional[FactorSpec]:
        """获取因子规格"""
        factor_info = self._factors.get(name)
        if factor_info:
            return factor_info.spec
        return None
    
    def list_factors(
        self,
        category: Optional[FactorCategory] = None,
        tag: Optional[str] = None,
        enabled_only: bool = True
    ) -> List[str]:
        """
        列出因子名称
        
        Args:
            category: 因子类别过滤
            tag: 标签过滤
            enabled_only: 是否只返回启用的因子
            
        Returns:
            因子名称列表
        """
        results = []
        
        for name, info in self._factors.items():
            if enabled_only and not info.enabled:
                continue
            
            if category and info.spec.category != category:
                continue
            
            if tag and tag not in info.tags:
                continue
            
            results.append(name)
        
        return sorted(results)
    
    def list_by_category(self) -> Dict[FactorCategory, List[str]]:
        """按类别列出因子"""
        result: Dict[FactorCategory, List[str]] = {}
        
        for name, info in self._factors.items():
            if not info.enabled:
                continue
            
            cat = info.spec.category
            if cat not in result:
                result[cat] = []
            result[cat].append(name)
        
        return result
    
    def list_tags(self) -> List[str]:
        """列出所有标签"""
        tags = set()
        for info in self._factors.values():
            tags.update(info.tags)
        return sorted(tags)
    
    def search(self, query: str) -> List[str]:
        """
        搜索因子（按名称、描述、标签）
        
        Args:
            query: 搜索关键词
            
        Returns:
            匹配的因子列表
        """
        query_lower = query.lower()
        results = []
        
        for name, info in self._factors.items():
            if (query_lower in name.lower() or 
                query_lower in info.spec.description.lower() or
                any(query_lower in t.lower() for t in info.tags)):
                results.append(name)
        
        return sorted(results)
    
    def enable(self, name: str) -> bool:
        """启用因子"""
        info = self._factors.get(name)
        if info:
            info.enabled = True
            return True
        return False
    
    def disable(self, name: str) -> bool:
        """禁用因子"""
        info = self._factors.get(name)
        if info:
            info.enabled = False
            return True
        return False
    
    def count(self, enabled_only: bool = True) -> int:
        """获取因子数量"""
        if enabled_only:
            return sum(1 for info in self._factors.values() if info.enabled)
        return len(self._factors)
    
    def get_dependencies(self, name: str) -> List[str]:
        """获取因子依赖"""
        spec = self.get_spec(name)
        if spec:
            return spec.dependencies
        return []


# 全局注册表实例
registry = FactorRegistry()


def get_registry() -> FactorRegistry:
    """获取全局因子注册表"""
    reg = FactorRegistry.get_instance()
    if not reg._initialized:
        reg.initialize()
    return reg
