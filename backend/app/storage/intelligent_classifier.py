"""
智能数据分类器

根据数据特征自动判断：
1. 是否应该缓存
2. 应该使用哪个缓存层级（L1/L2/L3）
3. 应该设置什么 TTL
4. 是否需要持久化
"""
from enum import Enum
from typing import Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime


class DataFreshness(Enum):
    """数据新鲜度"""
    REALTIME = "realtime"      # 实时数据（秒级更新）
    HOT = "hot"                # 热数据（分钟级更新）
    WARM = "warm"              # 温数据（小时级更新）
    COLD = "cold"              # 冷数据（天级更新）
    STATIC = "static"          # 静态数据（几乎不变）


class AccessPattern(Enum):
    """访问模式"""
    FREQUENT = "frequent"      # 高频访问（>100 次/天）
    MODERATE = "moderate"      # 中频访问（10-100 次/天）
    RARE = "rare"              # 低频访问（<10 次/天）


class DataImportance(Enum):
    """数据重要性"""
    CRITICAL = "critical"      # 核心数据（必须缓存）
    IMPORTANT = "important"    # 重要数据（建议缓存）
    OPTIONAL = "optional"      # 可选数据（按需缓存）


@dataclass
class DataProfile:
    """数据画像"""
    freshness: DataFreshness
    access_pattern: AccessPattern
    importance: DataImportance
    size_estimate: int = 0  # 预估大小（字节）
    update_frequency: int = 0  # 更新频率（秒）


@dataclass
class StorageDecision:
    """存储决策"""
    should_cache: bool
    cache_level: str  # "l1", "l2", "l3", "none"
    ttl_seconds: int
    should_persist: bool
    persist_target: str  # "sqlite", "parquet", "none"
    reason: str


class IntelligentDataClassifier:
    """智能数据分类器"""
    
    # 数据类型画像
    DATA_PROFILES: Dict[str, DataProfile] = {
        # 实时行情数据
        "realtime_quote": DataProfile(
            freshness=DataFreshness.REALTIME,
            access_pattern=AccessPattern.FREQUENT,
            importance=DataImportance.CRITICAL,
            size_estimate=1024,
            update_frequency=3
        ),
        
        # K 线数据（日线）
        "kline_daily": DataProfile(
            freshness=DataFreshness.HOT,
            access_pattern=AccessPattern.FREQUENT,
            importance=DataImportance.CRITICAL,
            size_estimate=5120,
            update_frequency=300
        ),
        
        # K 线数据（分钟线）
        "kline_minute": DataProfile(
            freshness=DataFreshness.REALTIME,
            access_pattern=AccessPattern.FREQUENT,
            importance=DataImportance.CRITICAL,
            size_estimate=10240,
            update_frequency=60
        ),
        
        # 技术指标
        "indicators": DataProfile(
            freshness=DataFreshness.HOT,
            access_pattern=AccessPattern.MODERATE,
            importance=DataImportance.IMPORTANT,
            size_estimate=2048,
            update_frequency=300
        ),
        
        # 板块数据
        "sector": DataProfile(
            freshness=DataFreshness.HOT,
            access_pattern=AccessPattern.FREQUENT,
            importance=DataImportance.IMPORTANT,
            size_estimate=4096,
            update_frequency=300
        ),
        
        # 资金流向
        "moneyflow": DataProfile(
            freshness=DataFreshness.WARM,
            access_pattern=AccessPattern.MODERATE,
            importance=DataImportance.IMPORTANT,
            size_estimate=8192,
            update_frequency=3600
        ),
        
        # 龙虎榜
        "billboard": DataProfile(
            freshness=DataFreshness.WARM,
            access_pattern=AccessPattern.RARE,
            importance=DataImportance.OPTIONAL,
            size_estimate=16384,
            update_frequency=3600
        ),
        
        # 财务数据
        "financial": DataProfile(
            freshness=DataFreshness.COLD,
            access_pattern=AccessPattern.RARE,
            importance=DataImportance.IMPORTANT,
            size_estimate=32768,
            update_frequency=86400
        ),
        
        # 股东信息
        "shareholder": DataProfile(
            freshness=DataFreshness.COLD,
            access_pattern=AccessPattern.RARE,
            importance=DataImportance.OPTIONAL,
            size_estimate=16384,
            update_frequency=86400
        ),
        
        # 股票列表（静态）
        "stock_list": DataProfile(
            freshness=DataFreshness.STATIC,
            access_pattern=AccessPattern.MODERATE,
            importance=DataImportance.CRITICAL,
            size_estimate=65536,
            update_frequency=604800
        ),
    }
    
    # 缓存层级 TTL 配置
    CACHE_TTL_CONFIG = {
        "l1": {
            "realtime": 60,      # 实时数据：1 分钟
            "hot": 300,          # 热数据：5 分钟
            "warm": 600,         # 温数据：10 分钟
            "cold": 1800,        # 冷数据：30 分钟
            "static": 3600,      # 静态数据：1 小时
        },
        "l2": {
            "realtime": 300,     # 实时数据：5 分钟
            "hot": 1800,         # 热数据：30 分钟
            "warm": 3600,        # 温数据：1 小时
            "cold": 7200,        # 冷数据：2 小时
            "static": 86400,     # 静态数据：1 天
        },
        "l3": {
            "realtime": 3600,    # 实时数据：1 小时
            "hot": 86400,        # 热数据：1 天
            "warm": 604800,      # 温数据：1 周
            "cold": 2592000,     # 冷数据：30 天
            "static": 31536000,  # 静态数据：1 年
        }
    }
    
    @classmethod
    def get_data_profile(cls, data_type: str) -> Optional[DataProfile]:
        """获取数据画像"""
        return cls.DATA_PROFILES.get(data_type)
    
    @classmethod
    def classify(cls, data_type: str, custom_params: Optional[Dict[str, Any]] = None) -> StorageDecision:
        """
        智能分类数据，决定存储策略
        
        Args:
            data_type: 数据类型（如 'kline_daily', 'realtime_quote'）
            custom_params: 自定义参数（可覆盖默认配置）
        
        Returns:
            StorageDecision: 存储决策
        
        示例:
            >>> decision = IntelligentDataClassifier.classify('kline_daily')
            >>> decision.should_cache
            True
            >>> decision.cache_level
            'l2'
            >>> decision.ttl_seconds
            1800
        """
        profile = cls.get_data_profile(data_type)
        
        if not profile:
            # 未知数据类型，使用默认策略
            return StorageDecision(
                should_cache=True,
                cache_level="l2",
                ttl_seconds=300,
                should_persist=True,
                persist_target="sqlite",
                reason="未知数据类型，使用默认策略"
            )
        
        # 应用自定义参数
        if custom_params:
            if "freshness" in custom_params:
                profile.freshness = DataFreshness(custom_params["freshness"])
            if "access_pattern" in custom_params:
                profile.access_pattern = AccessPattern(custom_params["access_pattern"])
            if "importance" in custom_params:
                profile.importance = DataImportance(custom_params["importance"])
        
        # 智能决策逻辑
        should_cache = cls._should_cache(profile)
        cache_level = cls._determine_cache_level(profile)
        ttl_seconds = cls._calculate_ttl(profile, cache_level)
        should_persist = cls._should_persist(profile)
        persist_target = cls._determine_persist_target(profile)
        reason = cls._generate_reason(profile, should_cache, cache_level, should_persist)
        
        return StorageDecision(
            should_cache=should_cache,
            cache_level=cache_level,
            ttl_seconds=ttl_seconds,
            should_persist=should_persist,
            persist_target=persist_target,
            reason=reason
        )
    
    @classmethod
    def _should_cache(cls, profile: DataProfile) -> bool:
        """判断是否应该缓存"""
        # 核心数据必须缓存
        if profile.importance == DataImportance.CRITICAL:
            return True
        
        # 高频访问数据建议缓存
        if profile.access_pattern == AccessPattern.FREQUENT:
            return True
        
        # 实时/热数据建议缓存
        if profile.freshness in [DataFreshness.REALTIME, DataFreshness.HOT]:
            return True
        
        # 低频访问的可选数据不缓存
        if (profile.access_pattern == AccessPattern.RARE and 
            profile.importance == DataImportance.OPTIONAL):
            return False
        
        # 其他情况默认缓存
        return True
    
    @classmethod
    def _determine_cache_level(cls, profile: DataProfile) -> str:
        """确定缓存层级"""
        # L1: 实时 + 核心 + 高频
        if (profile.freshness == DataFreshness.REALTIME and
            profile.importance == DataImportance.CRITICAL and
            profile.access_pattern == AccessPattern.FREQUENT):
            return "l1"
        
        # L2: 热数据 + 重要 + 中高频
        if (profile.freshness in [DataFreshness.HOT, DataFreshness.WARM] and
            profile.importance in [DataImportance.CRITICAL, DataImportance.IMPORTANT]):
            return "l2"
        
        # L3: 温冷数据 + 低频
        if profile.freshness in [DataFreshness.WARM, DataFreshness.COLD]:
            return "l3"
        
        # 静态数据：L3
        if profile.freshness == DataFreshness.STATIC:
            return "l3"
        
        # 默认 L2
        return "l2"
    
    @classmethod
    def _calculate_ttl(cls, profile: DataProfile, cache_level: str) -> int:
        """计算 TTL"""
        freshness_key = profile.freshness.value
        return cls.CACHE_TTL_CONFIG.get(cache_level, {}).get(freshness_key, 300)
    
    @classmethod
    def _should_persist(cls, profile: DataProfile) -> bool:
        """判断是否应该持久化"""
        # 静态数据必须持久化
        if profile.freshness == DataFreshness.STATIC:
            return True
        
        # 冷数据建议持久化
        if profile.freshness == DataFreshness.COLD:
            return True
        
        # 重要数据建议持久化
        if profile.importance in [DataImportance.CRITICAL, DataImportance.IMPORTANT]:
            return True
        
        # 实时数据不持久化（变化太快）
        if profile.freshness == DataFreshness.REALTIME:
            return False
        
        # 其他情况默认持久化
        return True
    
    @classmethod
    def _determine_persist_target(cls, profile: DataProfile) -> str:
        """确定持久化目标"""
        # 大数据量 -> Parquet
        if profile.size_estimate > 10240:  # > 10KB
            return "parquet"
        
        # 结构化数据 -> SQLite
        if profile.importance in [DataImportance.CRITICAL, DataImportance.IMPORTANT]:
            return "sqlite"
        
        # 其他 -> SQLite
        return "sqlite"
    
    @classmethod
    def _generate_reason(cls, profile: DataProfile, should_cache: bool, 
                        cache_level: str, should_persist: bool) -> str:
        """生成决策原因"""
        reasons = []
        
        if should_cache:
            reasons.append(f"缓存：{cache_level.upper()}")
            reasons.append(f"新鲜度={profile.freshness.value}")
            reasons.append(f"访问模式={profile.access_pattern.value}")
        else:
            reasons.append("不缓存")
        
        if should_persist:
            reasons.append(f"持久化：{profile.size_estimate / 1024:.1f}KB")
        
        return ", ".join(reasons)


# 便捷函数
def classify_data(data_type: str, **kwargs) -> StorageDecision:
    """便捷函数：分类数据"""
    return IntelligentDataClassifier.classify(data_type, kwargs)


# 全局实例
data_classifier = IntelligentDataClassifier()
