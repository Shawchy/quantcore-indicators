from pydantic_settings import BaseSettings
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Quant Analysis System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    API_PREFIX: str = "/api/v1"
    
    DATABASE_URL: str = "sqlite+aiosqlite:///./data/sqlite/quant.db"
    
    DATA_DIR: str = "./data"
    SQLITE_DIR: str = "./data/sqlite"
    PARQUET_DIR: str = "./data/parquet"
    
    CACHE_TTL: int = 300
    MAX_CACHE_SIZE: int = 1000
    
    DEFAULT_DATA_SOURCE: str = "akshare"
    
    BACKTEST_INITIAL_CAPITAL: float = 1000000.0
    BACKTEST_COMMISSION: float = 0.0003
    BACKTEST_SLIPPAGE: float = 0.0001
    
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/quant.log"
    
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    TUSHARE_TOKEN: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
