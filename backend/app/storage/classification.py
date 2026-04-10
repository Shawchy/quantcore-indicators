"""
统一数据分类系统

整合原分散在多个文件的分类逻辑:
- DataFreshness (storage_service.py)
- HotTier (hot_spot_tracker.py)  
- DataPartition (data_partition_manager.py)

提供单一数据源: UNIFIED_DATA_CONFIGS
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional


class DataTier(Enum):
    """统一数据层级（融合新鲜度/热度/分区）"""
    REALTIME = ("realtime", 0, 60)       # 实时: 秒级更新, TTL=60s
    HOT = ("hot", 1, 300)                # 热门: 高频访问, TTL=5min
    WARM = ("warm", 2, 1800)             # 温热: 中频访问, TTL=30min
    COLD = ("cold", 3, 7200)             # 冷门: 低频访问, TTL=2h
    ARCHIVED = ("archived", 4, 86400)    # 归档: 极少访问, TTL=24h

    def __init__(self, key: str, priority: int, default_ttl: int):
        self._key = key
        self.priority = priority
        self.default_ttl = default_ttl

    @property
    def key(self) -> str:
        """返回字符串键（兼容 .value 用法）"""
        return self._key

    def __str__(self):
        return self._key

    @classmethod
    def from_access_rate(cls, rate_per_hour: float) -> 'DataTier':
        """根据访问频率推断层级"""
        if rate_per_hour > 500:
            return cls.HOT
        elif rate_per_hour > 100:
            return cls.WARM
        else:
            return cls.COLD

    @classmethod
    def from_age_days(cls, age_days: int) -> 'DataTier':
        """根据数据年龄推断层级"""
        if age_days <= 1:
            return cls.REALTIME
        elif age_days <= 90:
            return cls.HOT
        elif age_days <= 730:  # 2年
            return cls.WARM
        elif age_days <= 1825:  # 5年
            return cls.COLD
        else:
            return cls.ARCHIVED


@dataclass
class UnifiedDataConfig:
    """统一的数据配置"""
    tier: DataTier
    max_cache_size: int
    ttl: int
    l2_enabled: bool
    storage_target: str       # 'memory', 'sqlite', 'parquet', 'compressed'
    compression: Optional[str] = None
    description: str = ""


UNIFIED_DATA_CONFIGS: Dict[str, UnifiedDataConfig] = {
    "realtime": UnifiedDataConfig(
        tier=DataTier.REALTIME,
        max_cache_size=500,
        ttl=60,
        l2_enabled=True,
        storage_target='memory',
        description='实时行情数据'
    ),
    "kline": UnifiedDataConfig(
        tier=DataTier.HOT,
        max_cache_size=1000,
        ttl=300,
        l2_enabled=True,
        storage_target='sqlite',
        description='K线数据（日/周/月）'
    ),
    "kline_minute": UnifiedDataConfig(
        tier=DataTier.REALTIME,
        max_cache_size=500,
        ttl=60,
        l2_enabled=True,
        storage_target='sqlite',
        description='分钟K线数据'
    ),
    "indicators": UnifiedDataConfig(
        tier=DataTier.HOT,
        max_cache_size=500,
        ttl=300,
        l2_enabled=True,
        storage_target='sqlite',
        description='技术指标数据'
    ),
    "sector": UnifiedDataConfig(
        tier=DataTier.HOT,
        max_cache_size=200,
        ttl=3600,
        l2_enabled=True,
        storage_target='sqlite',
        description='板块/行业数据'
    ),
    "chip": UnifiedDataConfig(
        tier=DataTier.WARM,
        max_cache_size=300,
        ttl=600,
        l2_enabled=True,
        storage_target='parquet',
        description='筹码分布数据'
    ),
    "moneyflow": UnifiedDataConfig(
        tier=DataTier.WARM,
        max_cache_size=200,
        ttl=1800,
        l2_enabled=False,
        storage_target='parquet',
        description='资金流向数据'
    ),
    "billboard": UnifiedDataConfig(
        tier=DataTier.WARM,
        max_cache_size=100,
        ttl=1800,
        l2_enabled=False,
        storage_target='parquet',
        description='龙虎榜数据'
    ),
    "financial": UnifiedDataConfig(
        tier=DataTier.COLD,
        max_cache_size=100,
        ttl=7200,
        l2_enabled=False,
        storage_target='parquet',
        compression='zstd',
        description='财务报表数据'
    ),
    "screener": UnifiedDataConfig(
        tier=DataTier.HOT,
        max_cache_size=100,
        ttl=120,
        l2_enabled=False,
        storage_target='memory',
        description='选股结果缓存'
    ),
    "backtest": UnifiedDataConfig(
        tier=DataTier.COLD,
        max_cache_size=50,
        ttl=3600,
        l2_enabled=False,
        storage_target='parquet',
        description='回测结果数据'
    ),
}


def get_config(data_type: str) -> UnifiedDataConfig:
    """获取数据类型配置（带默认值）"""
    return UNIFIED_DATA_CONFIGS.get(
        data_type,
        UnifiedDataConfig(
            tier=DataTier.WARM,
            max_cache_size=200,
            ttl=300,
            l2_enabled=False,
            storage_target='parquet',
            description=f'未知类型: {data_type}'
        )
    )


def get_tier(data_type: str) -> DataTier:
    """快速获取数据层级"""
    config = get_config(data_type)
    return config.tier
