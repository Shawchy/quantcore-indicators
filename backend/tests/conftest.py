"""
单元测试配置文件
"""

import pytest
import asyncio
from typing import Generator


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
