"""
统一数据源策略配置

整合分散在多个文件中的策略配置：
- config.py: DATA_SOURCE_BY_TYPE, DATA_SOURCE_PRIORITY
- factory.py: DataSourceFactory 初始化逻辑
- smart_router.py: API_CONFIGS

使用统一的策略配置，简化维护和管理。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class DataSourceType(str, Enum):
    """数据源类型"""
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    EFINANCE = "efinance"
    TICKFLOW = "tickflow"
    YFINANCE = "yfinance"
    PLAYWRIGHT = "playwright"


class APISensitivity(str, Enum):
    """API 敏感度级别"""
    LOW = "low"           # 低敏感 - 使用 curl_cffi
    MEDIUM = "medium"     # 中敏感 - 优先 curl_cffi，失败用 playwright
    HIGH = "high"         # 高敏感 - 直接使用 playwright


@dataclass
class DataTypeStrategy:
    """数据类型策略配置"""
    # 数据源优先级列表
    priority: List[DataSourceType]
    
    # API 敏感度
    sensitivity: APISensitivity = APISensitivity.LOW
    
    # 首选客户端
    preferred_client: str = "curl_cffi"
    
    # 降级客户端（可选）
    fallback_client: Optional[str] = None
    
    # 缓存 TTL（秒）
    cache_ttl: int = 300
    
    # 是否启用故障转移
    enable_fallback: bool = True
    
    # 是否启用健康检查
    enable_health_check: bool = True
    
    # 数据一致性容差
    consistency_tolerance: float = 0.01


# =============================================================================
# 统一数据源策略配置
# =============================================================================

UNIFIED_DATA_STRATEGY: Dict[str, DataTypeStrategy] = {
    # =========================================================================
    # 实时行情类
    # =========================================================================
    "realtime_quote": DataTypeStrategy(
        priority=[
            DataSourceType.EFINANCE,
            DataSourceType.AKSHARE,
            DataSourceType.TICKFLOW,
        ],
        sensitivity=APISensitivity.HIGH,
        preferred_client="playwright",
        fallback_client=None,
        cache_ttl=60,  # 实时数据缓存 60 秒
    ),
    
    "market_quotes": DataTypeStrategy(
        priority=[
            DataSourceType.AKSHARE,
            DataSourceType.EFINANCE,
        ],
        sensitivity=APISensitivity.MEDIUM,
        preferred_client="curl_cffi",
        fallback_client="playwright",
        cache_ttl=60,
    ),
    
    # =========================================================================
    # K 线数据类
    # =========================================================================
    "kline": DataTypeStrategy(
        priority=[
            DataSourceType.TICKFLOW,
            DataSourceType.AKSHARE,
            DataSourceType.EFINANCE,
            DataSourceType.BAOSTOCK,
        ],
        sensitivity=APISensitivity.LOW,
        preferred_client="curl_cffi",
        fallback_client=None,
        cache_ttl=300,  # K 线缓存 5 分钟
    ),
    
    "index_kline": DataTypeStrategy(
        priority=[
            DataSourceType.AKSHARE,
            DataSourceType.BAOSTOCK,
        ],
        sensitivity=APISensitivity.LOW,
        preferred_client="curl_cffi",
        cache_ttl=300,
    ),
    
    # =========================================================================
    # 分时/Tick 数据类
    # =========================================================================
    "tick": DataTypeStrategy(
        priority=[
            DataSourceType.TICKFLOW,
            DataSourceType.EFINANCE,
        ],
        sensitivity=APISensitivity.MEDIUM,
        preferred_client="curl_cffi",
        fallback_client="playwright",
        cache_ttl=60,
    ),
    
    # =========================================================================
    # 股票基础信息类
    # =========================================================================
    "stock_list": DataTypeStrategy(
        priority=[
            DataSourceType.AKSHARE,
            DataSourceType.EFINANCE,
        ],
        sensitivity=APISensitivity.HIGH,
        preferred_client="playwright",
        cache_ttl=3600,  # 股票列表缓存 1 小时
    ),
    
    "stock_info": DataTypeStrategy(
        priority=[
            DataSourceType.EFINANCE,
            DataSourceType.AKSHARE,
            DataSourceType.TICKFLOW,
        ],
        sensitivity=APISensitivity.LOW,
        preferred_client="curl_cffi",
        cache_ttl=3600,
    ),
    
    # =========================================================================
    # 板块数据类
    # =========================================================================
    "sector": DataTypeStrategy(
        priority=[
            DataSourceType.AKSHARE,
            DataSourceType.EFINANCE,
        ],
        sensitivity=APISensitivity.MEDIUM,
        preferred_client="curl_cffi",
        fallback_client="playwright",
        cache_ttl=300,
    ),
    
    "sector_list": DataTypeStrategy(
        priority=[
            DataSourceType.AKSHARE,
            DataSourceType.EFINANCE,
        ],
        sensitivity=APISensitivity.HIGH,
        preferred_client="playwright",
        cache_ttl=3600,
    ),
    
    # =========================================================================
    # 特色数据类
    # =========================================================================
    "chip": DataTypeStrategy(
        priority=[
            DataSourceType.AKSHARE,
        ],
        sensitivity=APISensitivity.LOW,
        preferred_client="curl_cffi",
        cache_ttl=600,  # 筹码数据缓存 10 分钟
    ),
    
    "moneyflow": DataTypeStrategy(
        priority=[
            DataSourceType.EFINANCE,
            DataSourceType.AKSHARE,
        ],
        sensitivity=APISensitivity.MEDIUM,
        preferred_client="curl_cffi",
        fallback_client="playwright",
        cache_ttl=120,
    ),
    
    "billboard": DataTypeStrategy(
        priority=[
            DataSourceType.AKSHARE,
            DataSourceType.EFINANCE,
        ],
        sensitivity=APISensitivity.LOW,
        preferred_client="curl_cffi",
        cache_ttl=600,
    ),
    
    # =========================================================================
    # 财务数据类
    # =========================================================================
    "financial": DataTypeStrategy(
        priority=[
            DataSourceType.AKSHARE,
            DataSourceType.BAOSTOCK,
        ],
        sensitivity=APISensitivity.LOW,
        preferred_client="curl_cffi",
        cache_ttl=3600,  # 财务数据缓存 1 小时
    ),
    
    "fund": DataTypeStrategy(
        priority=[
            DataSourceType.EFINANCE,
            DataSourceType.AKSHARE,
        ],
        sensitivity=APISensitivity.LOW,
        preferred_client="curl_cffi",
        cache_ttl=3600,
    ),
    
    # =========================================================================
    # 资金流向类
    # =========================================================================
    "fund_flow": DataTypeStrategy(
        priority=[
            DataSourceType.EFINANCE,
            DataSourceType.AKSHARE,
        ],
        sensitivity=APISensitivity.MEDIUM,
        preferred_client="curl_cffi",
        fallback_client="playwright",
        cache_ttl=120,
    ),
    
    "main_fund_flow": DataTypeStrategy(
        priority=[
            DataSourceType.EFINANCE,
            DataSourceType.AKSHARE,
        ],
        sensitivity=APISensitivity.MEDIUM,
        preferred_client="curl_cffi",
        fallback_client="playwright",
        cache_ttl=120,
    ),
    
    # =========================================================================
    # 历史数据类
    # =========================================================================
    "quote_history": DataTypeStrategy(
        priority=[
            DataSourceType.TICKFLOW,
            DataSourceType.AKSHARE,
            DataSourceType.BAOSTOCK,
        ],
        sensitivity=APISensitivity.LOW,
        preferred_client="curl_cffi",
        cache_ttl=3600,
    ),
}


# =============================================================================
# 数据源适配器配置
# =============================================================================

ADAPTER_CONFIG: Dict[DataSourceType, Dict[str, Any]] = {
    DataSourceType.AKSHARE: {
        "enabled": True,
        "requires_auth": False,
        "supports_realtime": True,
        "supports_historical": True,
        "rate_limit": 100,  # 每分钟请求数限制
    },
    DataSourceType.BAOSTOCK: {
        "enabled": True,
        "requires_auth": False,
        "supports_realtime": False,
        "supports_historical": True,
        "rate_limit": 50,
    },
    DataSourceType.EFINANCE: {
        "enabled": True,
        "requires_auth": False,
        "supports_realtime": True,
        "supports_historical": True,
        "rate_limit": 80,
    },
    DataSourceType.TICKFLOW: {
        "enabled": True,
        "requires_auth": True,  # 需要 API Key
        "supports_realtime": True,
        "supports_historical": True,
        "rate_limit": 200,
    },
    DataSourceType.YFINANCE: {
        "enabled": False,  # 默认不启用
        "requires_auth": False,
        "supports_realtime": False,
        "supports_historical": True,
        "rate_limit": 100,
    },
    DataSourceType.PLAYWRIGHT: {
        "enabled": True,
        "requires_auth": False,
        "supports_realtime": True,
        "supports_historical": True,
        "rate_limit": 30,  # Playwright 较慢，限制更严格
    },
}


# =============================================================================
# 健康检查配置
# =============================================================================

HEALTH_CHECK_CONFIG = {
    "interval": 300,  # 健康检查间隔（秒）
    "timeout": 10,    # 健康检查超时（秒）
    "failure_threshold": 3,  # 连续失败次数阈值
    "recovery_threshold": 2,  # 恢复检查次数
    "cooldown_period": 300,  # 冷却时间（秒）
}


# =============================================================================
# 辅助函数
# =============================================================================

def get_strategy(data_type: str) -> Optional[DataTypeStrategy]:
    """获取指定数据类型的策略配置"""
    return UNIFIED_DATA_STRATEGY.get(data_type)


def get_priority_sources(data_type: str) -> List[DataSourceType]:
    """获取指定数据类型的数据源优先级列表"""
    strategy = get_strategy(data_type)
    if strategy:
        return strategy.priority
    # 默认优先级
    return [
        DataSourceType.EFINANCE,
        DataSourceType.AKSHARE,
        DataSourceType.BAOSTOCK,
    ]


def get_cache_ttl(data_type: str) -> int:
    """获取指定数据类型的缓存 TTL"""
    strategy = get_strategy(data_type)
    if strategy:
        return strategy.cache_ttl
    return 300  # 默认 5 分钟


def get_client_config(data_type: str) -> Dict[str, Any]:
    """获取指定数据类型的客户端配置"""
    strategy = get_strategy(data_type)
    if strategy:
        return {
            "preferred": strategy.preferred_client,
            "fallback": strategy.fallback_client,
            "sensitivity": strategy.sensitivity.value,
        }
    return {
        "preferred": "curl_cffi",
        "fallback": None,
        "sensitivity": "low",
    }


def is_adapter_enabled(source_type: DataSourceType) -> bool:
    """检查数据源适配器是否启用"""
    config = ADAPTER_CONFIG.get(source_type)
    return config.get("enabled", False) if config else False


def get_all_data_types() -> List[str]:
    """获取所有支持的数据类型"""
    return list(UNIFIED_DATA_STRATEGY.keys())


def validate_strategy_config() -> List[str]:
    """验证策略配置的有效性，返回错误信息列表"""
    errors = []
    
    for data_type, strategy in UNIFIED_DATA_STRATEGY.items():
        # 检查优先级列表不能为空
        if not strategy.priority:
            errors.append(f"{data_type}: 优先级列表不能为空")
        
        # 检查缓存 TTL 必须为正数
        if strategy.cache_ttl <= 0:
            errors.append(f"{data_type}: 缓存 TTL 必须为正数")
        
        # 检查敏感度与客户端配置一致性
        if strategy.sensitivity == APISensitivity.HIGH and strategy.preferred_client != "playwright":
            errors.append(f"{data_type}: 高敏感 API 应该使用 playwright 客户端")
    
    return errors


# 初始化时验证配置
if __name__ == "__main__":
    errors = validate_strategy_config()
    if errors:
        print("策略配置验证失败:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("策略配置验证通过")
        print(f"\n共配置 {len(UNIFIED_DATA_STRATEGY)} 种数据类型")
        print(f"共配置 {len(ADAPTER_CONFIG)} 个数据源适配器")
