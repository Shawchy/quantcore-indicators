"""
因子存储模块

提供因子的持久化存储功能：
- FactorDatabase: 因子数据库接口
- ParquetBackend: Parquet 存储引擎
- SQLiteMeta: 元数据管理
"""

from .factor_db import FactorDatabase
from .parquet_backend import ParquetBackend
from .sqlite_meta import SQLiteMetadata

__all__ = [
    "FactorDatabase",
    "ParquetBackend",
    "SQLiteMetadata",
]
