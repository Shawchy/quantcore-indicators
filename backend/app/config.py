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
    
    DEFAULT_DATA_SOURCE: str = "tushare"  # 优先使用 Tushare
    
    BACKTEST_INITIAL_CAPITAL: float = 1000000.0
    BACKTEST_COMMISSION: float = 0.0003
    BACKTEST_SLIPPAGE: float = 0.0001
    
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "./logs/quant.log"
    
    CORS_ORIGINS: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    
    TUSHARE_TOKEN: Optional[str] = None  # 从环境变量读取
    TUSHARE_POINTS: int = 120  # Tushare 积分，默认 120 分（注册 + 完善信息）
    
    # 数据源优先级（从高到低）
    DATA_SOURCE_PRIORITY: list[str] = ["tushare", "akshare", "baostock"]
    
    # Tushare 积分权限配置
    TUSHARE_PERMISSION_CONFIG: dict = {
        # 120 分免费权限（注册 + 完善信息）
        120: {
            "daily": True,  # 日线行情（非复权）
            "adj_factor": True,  # 复权因子
            "stock_basic": True,  # 股票列表
            "index_basic": True,  # 指数列表
            "index_daily": True,  # 指数日线
            "index_weight": True,  # 成分股
            "fund_basic": True,  # 基金基础
            "dividend": True,  # 分红送股
            "trade_cal": True,  # 交易日历
            "suspend_d": True,  # 停复牌
            "macro_data": True,  # 宏观数据（GDP、CPI 等）
        },
        # 200 分权限
        200: {
            "top_list": True,  # 龙虎榜
            "block_trade": True,  # 大宗交易
            "margin_detail": True,  # 融资融券
        },
        # 800 分权限
        800: {
            "forecast": True,  # 业绩预告
            "express": True,  # 业绩快报
            "dividend_detail": True,  # 分红详细
        },
        # 2000 分权限
        2000: {
            "weekly": True,  # 周线行情
            "monthly": True,  # 月线行情
            "finance_full": True,  # 完整财务三大表
        },
        # 5000 分权限
        5000: {
            "intraday": True,  # 分钟线（1/5/15/30/60min）
            "moneyflow": True,  # 资金流向
        },
        # 10000 分权限
        10000: {
            "chip_distribution": True,  # 筹码分布
            "profit_forecast": True,  # 盈利预测
            "broker_recommend": True,  # 券商金股
            "level2": True,  # Level-2 数据
        },
    }
    
    # JWT 认证配置
    SECRET_KEY: str  # 必须设置，建议使用：openssl rand -hex 32
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 小时
    
    # 默认用户密码（开发环境）
    DEFAULT_ADMIN_PASSWORD: str = "admin123"
    DEFAULT_USER_PASSWORD: str = "user123"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
