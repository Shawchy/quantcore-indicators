import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator, computed_field
from typing import Optional
from functools import lru_cache


def get_default_data_dir() -> str:
    """获取默认数据目录（用户主目录下的 .quant 文件夹）"""
    return os.path.join(Path.home(), ".quant")


@lru_cache(maxsize=1)
def get_project_root() -> str:
    """获取项目根目录（backend 的上一级目录）"""
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def get_quantcore_path() -> str:
    """获取 QuantCore Python API 路径"""
    return os.path.join(get_project_root(), 'quantcore', 'python-api')


def get_quantcore_indicators_path() -> str:
    """获取 QuantCore Indicators Python 路径"""
    return os.path.join(get_project_root(), 'quantcore-indicators', 'python')


class Settings(BaseSettings):
    """应用配置类
    
    使用 Pydantic V2 的 SettingsConfigDict 替代旧的 class Config
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    APP_NAME: str = "Quant Analysis System"
    APP_VERSION: str = "1.0.0"
    # DEBUG 模式说明：
    # - True: 启用详细日志、SQL 回显、开发模式安全提示
    # - False: 生产模式，关闭调试输出，使用安全配置
    # - 环境变量覆盖：DEBUG=True/False
    DEBUG: bool = False
    
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
    
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"]
    
    TICKFLOW_API_KEY: Optional[str] = None  # TickFlow API Key（可选，不填则使用免费服务）
    
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
    
    # JWT 认证配置
    # 优先读取 QUANT_SECRET_KEY（向后兼容），其次读取 SECRET_KEY
    SECRET_KEY: str = os.getenv("QUANT_SECRET_KEY") or os.getenv("SECRET_KEY", "")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时
    
    @field_validator("SECRET_KEY")
    @classmethod
    def check_secret_key(cls, v):
        if not v:
            raise ValueError(
                "SECRET_KEY 未设置！请通过以下方式之一配置：\n"
                "  1. 设置环境变量：export SECRET_KEY=$(openssl rand -hex 32)\n"
                "     （也支持 QUANT_SECRET_KEY 环境变量名，向后兼容）\n"
                "  2. 复制 .env.example 为 .env 并填写 SECRET_KEY：cp .env.example .env"
            )
        insecure_keys = {"change-me", "your-super-secret-key", "secret-key", "example", "test"}
        v_lower = v.lower()
        for insecure in insecure_keys:
            if insecure in v_lower:
                raise ValueError(f"SECRET_KEY 不能使用不安全的默认值！请使用 openssl rand -hex 32 生成安全密钥。")
        if len(v) < 32:
            raise ValueError("SECRET_KEY 长度必须至少 32 个字符！请使用 openssl rand -hex 32 生成安全密钥。")
        return v
    
    # 默认用户密码（开发环境，生产环境应通过环境变量覆盖）
    DEFAULT_ADMIN_PASSWORD: str = os.getenv("QUANT_DEFAULT_ADMIN_PASSWORD", "admin123")
    DEFAULT_USER_PASSWORD: str = os.getenv("QUANT_DEFAULT_USER_PASSWORD", "user123")


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
