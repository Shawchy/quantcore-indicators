"""
单元测试配置文件
"""

import pytest
import asyncio
import os
import sys
from typing import Generator

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# 设置测试环境变量
os.environ.setdefault("SECRET_KEY", "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2")
os.environ.setdefault("DEBUG", "true")
os.environ.setdefault("LOG_LEVEL", "ERROR")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def sample_stock_code() -> str:
    """示例股票代码"""
    return "600519"


@pytest.fixture
def sample_date_range() -> tuple:
    """示例日期范围"""
    return ("2024-01-01", "2024-12-31")


@pytest.fixture
def mock_kline_data():
    """模拟 K 线数据"""
    return [
        {
            "code": "000001",
            "date": "2024-01-01",
            "open": 10.0,
            "high": 11.0,
            "low": 9.0,
            "close": 10.5,
            "volume": 10000,
            "amount": 105000.0,
        },
        {
            "code": "000001",
            "date": "2024-01-02",
            "open": 10.5,
            "high": 12.0,
            "low": 10.0,
            "close": 11.5,
            "volume": 15000,
            "amount": 172500.0,
        },
    ]


@pytest.fixture
def mock_stock_basic_info():
    """模拟股票基本信息"""
    return {
        "code": "000001",
        "name": "平安银行",
        "market": "SZ",
        "industry": "银行",
        "area": "深圳",
    }
