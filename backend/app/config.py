import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, computed_field
from typing import Optional
from functools import lru_cache


def get_default_data_dir() -> str:
    """获取默认数据目录（用户主目录下的 .quant 文件夹）"""
    return os.path.join(Path.home(), ".quant")


class Settings(BaseSettings):
    """应用配置类
    
    使用 Pydantic V2 的 SettingsConfigDict 替代旧的 class Config
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # 忽略额外的环境变量
    )
    
    APP_NAME: str = "Quant Analysis System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False  # 生产环境应关闭 DEBUG 模式
    
    API_PREFIX: str = "/api/v1"
    
    # 数据根目录（可通过环境变量覆盖，默认使用用户主目录）
    DATA_DIR: str = os.getenv("QUANT_DATA_DIR", get_default_data_dir())
    
    # 数据库URL（可通过环境变量覆盖，默认基于 DATA_DIR）
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        f"sqlite+aiosqlite:///{os.path.join(DATA_DIR, 'sqlite', 'quant.db')}"
    )
    
    # 各数据子目录（使用 computed_field 确保基于实际的 DATA_DIR）
    @computed_field
    @property
    def SQLITE_DIR(self) -> str:
        """SQLite 目录（基于 DATA_DIR）"""
        return os.getenv("QUANT_SQLITE_DIR", os.path.join(self.DATA_DIR, "sqlite"))
    
    @computed_field
    @property
    def PARQUET_DIR(self) -> str:
        """Parquet 目录（基于 DATA_DIR）"""
        return os.getenv("QUANT_PARQUET_DIR", os.path.join(self.DATA_DIR, "parquet"))
    
    @computed_field
    @property
    def LOG_DIR(self) -> str:
        """日志目录（基于 DATA_DIR）"""
        return os.getenv("QUANT_LOG_DIR", os.path.join(self.DATA_DIR, "logs"))
    
    CACHE_TTL: int = 300
    MAX_CACHE_SIZE: int = 1000
    
    DEFAULT_DATA_SOURCE: str = "efinance"  # 默认使用 EFinance（完全免费）
    
    BACKTEST_INITIAL_CAPITAL: float = 1000000.0
    BACKTEST_COMMISSION: float = 0.0003
    BACKTEST_SLIPPAGE: float = 0.0001
    
    LOG_LEVEL: str = os.getenv("QUANT_LOG_LEVEL", "INFO")
    
    @computed_field
    @property
    def LOG_FILE(self) -> str:
        """日志文件路径（基于 LOG_DIR）"""
        return os.path.join(self.LOG_DIR, "quant.log")
    
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    TICKFLOW_API_KEY: Optional[str] = None  # TickFlow API Key（可选，不填则使用免费服务）
    
    # 数据源优先级（从高到低）
    DATA_SOURCE_PRIORITY: list[str] = ["efinance", "akshare", "baostock", "tickflow"]
    
    # 数据存储配置
    @computed_field
    @property
    def STORAGE_CONFIG(self) -> dict:
        """存储配置（动态基于目录配置）"""
        return {
            "hot_threshold_days": int(os.getenv("QUANT_HOT_THRESHOLD_DAYS", 90)),  # 热数据阈值（天）
            "parquet_base_dir": self.PARQUET_DIR,
            "sqlite_db": os.path.join(self.SQLITE_DIR, "quant.db"),
            "cache_ttl": {
                "realtime": int(os.getenv("QUANT_CACHE_TTL_REALTIME", 60)),  # 实时行情缓存 TTL（秒）
                "kline": int(os.getenv("QUANT_CACHE_TTL_KLINE", 300)),  # K 线缓存 TTL（秒）
                "indicators": int(os.getenv("QUANT_CACHE_TTL_INDICATORS", 300)),  # 指标缓存 TTL（秒）
                "sector": int(os.getenv("QUANT_CACHE_TTL_SECTOR", 300)),  # 板块缓存 TTL（秒）
                "chip": int(os.getenv("QUANT_CACHE_TTL_CHIP", 600)),  # 筹码缓存 TTL（秒）
                "backtest": int(os.getenv("QUANT_CACHE_TTL_BACKTEST", 3600)),  # 回测缓存 TTL（秒）
            }
        }
    
    # 技术指标配置
    INDICATORS_CONFIG: dict = {
        "prefer_talib": True,  # 优先使用 TA-Lib（如果可用）
        "use_pandas_ta": True,  # 使用 pandas-ta
    }
    
    # 数据源配置
    DATA_SOURCE_CONFIG: dict = {
        "health_check_interval": 300,  # 健康检查间隔（秒）
        "consistency_tolerance": 0.01,  # 数据一致性容差（1%）
        "priority": ["efinance", "akshare", "baostock", "tickflow"],
    }
    
    # 按数据类型分组的数据源优先级配置
    # 格式: {数据类型: [优先数据源列表]}
    # 说明: 每种数据类型会按顺序尝试数据源，直到成功获取数据
    DATA_SOURCE_BY_TYPE: dict = {
        # 实时行情类 - efinance 最快但易限流，akshare 作为备用
        "realtime_quote": ["efinance", "akshare", "tickflow"],
        
        # 市场行情列表 - akshare 更稳定
        "market_quotes": ["akshare", "efinance"],
        
        # K线数据 - tickflow 个股K线和分时最优，akshare 稳定，baostock 历史数据好
        "kline": ["tickflow", "akshare", "efinance", "baostock"],
        
        # 分时数据 - tickflow 专长
        "tick": ["tickflow", "efinance"],
        
        # 指数K线 - akshare 专门接口，baostock 也有
        "index_kline": ["akshare", "baostock"],
        
        # 板块数据 - akshare 接口丰富
        "sector": ["akshare", "efinance"],
        
        # 筹码数据 - akshare 专用
        "chip": ["akshare"],
        
        # 资金流向 - efinance 专长
        "moneyflow": ["efinance", "akshare"],
        
        # 龙虎榜 - akshare 数据全
        "billboard": ["akshare", "efinance"],
        
        # 财务数据 - akshare 接口丰富，baostock 也有
        "financial": ["akshare", "baostock"],
        
        # 基金数据 - efinance 专长
        "fund": ["efinance", "akshare"],
        
        # 股票列表 - akshare 稳定
        "stock_list": ["akshare", "efinance"],
        
        # 股票信息 - efinance 实时性好
        "stock_info": ["efinance", "akshare"],
    }
    
    # JWT 认证配置
    SECRET_KEY: str  # 必须设置，建议使用：openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时
    
    # 默认用户密码（开发环境）
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    DEFAULT_USER_PASSWORD: str = "user123"


@lru_cache()
def get_settings() -> Settings:
    return Settings()


def ensure_directories():
    """确保所有数据目录存在"""
    from loguru import logger
    
    settings = get_settings()
    directories = [
        settings.DATA_DIR,
        settings.SQLITE_DIR,
        settings.PARQUET_DIR,
        settings.LOG_DIR,
    ]
    
    for directory in directories:
        try:
            Path(directory).mkdir(parents=True, exist_ok=True)
            logger.debug(f"目录已确保存在: {directory}")
        except Exception as e:
            logger.warning(f"创建目录失败 {directory}: {e}")


settings = get_settings()

# 应用启动时自动创建目录
ensure_directories()
