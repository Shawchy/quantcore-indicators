"""
TickFlow 量化交易系统 - Alembic 迁移环境配置
支持异步 SQLAlchemy 和项目配置
"""

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import engine_from_config, pool
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入项目配置和模型
from app.config import settings
from app.storage.sqlite import Base

# 导入所有模型以确保它们被注册到 Base.metadata
# 这确保 alembic 能检测到所有表的变化
from app.storage.sqlite import (
    StockInfo, KLine, TechnicalIndicatorDB, WatchlistDB,
    ChipData, SectorInfo, Strategy, BacktestRecord, TradeRecord,
    User, RealtimeQuote, MarketRanking, MarketTurnover
)

# this is the Alembic Config object
config = context.config

# 从项目配置读取数据库 URL
database_url = settings.DATABASE_URL

# 将异步 URL 转换为同步 URL (alembic 需要同步连接)
# sqlite+aiosqlite:// -> sqlite://
if database_url.startswith("sqlite+aiosqlite://"):
    sync_database_url = database_url.replace("sqlite+aiosqlite://", "sqlite://")
else:
    sync_database_url = database_url

# 设置 sqlalchemy.url
config.set_main_option("sqlalchemy.url", sync_database_url)

# Interpret the config file for Python logging
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 设置目标 metadata 用于 autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """在离线模式下运行迁移

n    这种模式只使用 URL 而不创建 Engine，
    甚至不需要 DBAPI 可用。
    """
    context.configure(
        url=sync_database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # 启用批量模式 (SQLite 需要)
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection):
    """实际执行迁移"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        # 启用批量模式 (SQLite 需要)
        render_as_batch=True,
        # 比较类型变化
        compare_type=True,
        # 比较服务器默认值
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    """在在线模式下运行迁移

    创建 Engine 并建立连接上下文。
    """
    # 使用同步引擎 (alembic 不支持异步引擎)
    connectable = create_async_engine(
        database_url,
        poolclass=pool.NullPool,
        echo=settings.DEBUG,
    )

    async with connectable.connect() as connection:
        # 使用 run_sync 在异步连接上执行同步操作
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    print(f"Running migrations offline with URL: {sync_database_url}")
    run_migrations_offline()
else:
    print(f"Running migrations online with URL: {database_url}")
    # 使用 asyncio 运行异步函数
    asyncio.run(run_migrations_online())
