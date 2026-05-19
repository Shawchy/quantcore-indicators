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
# from .efinance_adapter import EFinanceAdapter  # 临时禁用，文件有语法错误
EFinanceAdapter = None  # 占位符
from .tickflow_adapter import TickFlowAdapter
from .playwright_adapter import PlaywrightAdapter
from .enhanced_playwright_adapter import EnhancedPlaywrightAdapter
from .smart_switcher import SmartDataSourceSwitcher, FallbackConfig
from .unified_adapter import UnifiedDataAdapter
from .credential_injector import (
    CredentialInjector,
    AkShareWithCredential,
    EfinanceWithCredential,
    UnifiedCredentialManager
)
from .smart_retry import (
    SmartRetryExecutor,
    ErrorClassifier,
    ErrorType,
    RetryDecision,
    RequestFrequencyController,
)
from .smart_router import (
    SmartDataRouter,
    APISensitivity,
)
from .factory import DataSourceFactory, DataSourceManager, data_source_manager
from .strategy_config import (
    UNIFIED_DATA_STRATEGY,
    ADAPTER_CONFIG,
    DataTypeStrategy,
    get_strategy,
    get_priority_sources,
    get_cache_ttl,
    get_client_config,
    validate_strategy_config,
)
from .dynamic_priority import (
    DynamicPriorityManager,
    DataSourcePerformance,
    dynamic_priority_manager,
)
from .batch_optimizer import (
    BatchRequestOptimizer,
    BatchRequest,
    BatchResult,
    batch_optimizer,
)
from .smart_preloader import (
    SmartPreloader,
    UserPattern,
    smart_preloader,
)

__all__ = [
    # 基础类
    "BaseDataAdapter",
    "DataSourceType",
    "StockBasicInfo",
    "KLineData",
    "SectorInfo",
    "ChipData",
    # 适配器
    "AkShareAdapter",
    "BaostockAdapter",
    "YFinanceAdapter",
    "EFinanceAdapter",
    "TickFlowAdapter",
    "PlaywrightAdapter",
    "EnhancedPlaywrightAdapter",
    "UnifiedDataAdapter",
    # 凭证管理
    "CredentialInjector",
    "AkShareWithCredential",
    "EfinanceWithCredential",
    "UnifiedCredentialManager",
    # 智能切换
    "SmartDataSourceSwitcher",
    "FallbackConfig",
    # 重试策略
    "SmartRetryExecutor",
    "ErrorClassifier",
    "ErrorType",
    "RetryDecision",
    "RequestFrequencyController",
    # 智能路由
    "SmartDataRouter",
    "APISensitivity",
    # 数据源管理
    "DataSourceFactory",
    "DataSourceManager",
    "data_source_manager",
    # 统一策略配置
    "UNIFIED_DATA_STRATEGY",
    "ADAPTER_CONFIG",
    "DataTypeStrategy",
    "get_strategy",
    "get_priority_sources",
    "get_cache_ttl",
    "get_client_config",
    "validate_strategy_config",
    # 动态优先级（新增）
    "DynamicPriorityManager",
    "DataSourcePerformance",
    "dynamic_priority_manager",
    # 批量请求优化（新增）
    "BatchRequestOptimizer",
    "BatchRequest",
    "BatchResult",
    "batch_optimizer",
    # 智能预加载（新增）
    "SmartPreloader",
    "UserPattern",
    "smart_preloader",
]
