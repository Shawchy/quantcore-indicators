"""
数据加载器单元测试
测试分层数据加载、任务队列等核心功能
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock

from app.services.data_loader import (
    DataLoader,
    LoadPriority,
    LoadStatus,
    LoadTask,
    LoadProgress,
)


class TestLoadPriority:
    """加载优先级测试"""

    def test_priority_order(self):
        """测试优先级顺序"""
        assert LoadPriority.CURRENT_MONTH.value == 1
        assert LoadPriority.CURRENT_YEAR.value == 2
        assert LoadPriority.LAST_3_YEARS.value == 3
        assert LoadPriority.LAST_5_YEARS.value == 4
        assert LoadPriority.ALL_HISTORY.value == 5

    def test_priority_comparison(self):
        """测试优先级比较"""
        assert LoadPriority.CURRENT_MONTH.value < LoadPriority.CURRENT_YEAR.value
        assert LoadPriority.CURRENT_YEAR.value < LoadPriority.LAST_3_YEARS.value


class TestLoadTask:
    """加载任务测试"""

    def test_task_creation(self):
        """测试任务创建"""
        task = LoadTask(
            code="000001",
            priority=LoadPriority.CURRENT_YEAR,
            start_date="20240101",
            end_date="20241231",
        )

        assert task.code == "000001"
        assert task.priority == LoadPriority.CURRENT_YEAR
        assert task.start_date == "20240101"
        assert task.end_date == "20241231"
        assert task.status == LoadStatus.PENDING
        assert task.progress == 0
        assert task.loaded_count == 0
        assert task.error is None

    def test_task_status_transition(self):
        """测试任务状态转换"""
        task = LoadTask(
            code="000001",
            priority=LoadPriority.CURRENT_YEAR,
            start_date="20240101",
            end_date="20241231",
        )

        # 初始状态
        assert task.status == LoadStatus.PENDING

        # 转换为加载中
        task.status = LoadStatus.LOADING
        assert task.status == LoadStatus.LOADING

        # 转换为完成
        task.status = LoadStatus.COMPLETED
        task.progress = 100
        assert task.status == LoadStatus.COMPLETED
        assert task.progress == 100


class TestDataLoader:
    """数据加载器测试"""

    @pytest.fixture
    def data_loader(self):
        """创建数据加载器实例"""
        return DataLoader()

    @pytest.fixture
    def mock_data_source(self):
        """创建模拟数据源"""
        mock = Mock()
        mock.get_kline = AsyncMock(return_value=[])
        return mock

    @pytest.fixture
    def mock_persistence(self):
        """创建模拟持久化服务"""
        mock = Mock()
        mock.save_klines = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_start_stop(self, data_loader):
        """测试启动和停止"""
        await data_loader.start()
        assert data_loader._running is True
        assert data_loader._worker_task is not None

        await data_loader.stop()
        assert data_loader._running is False

    @pytest.mark.asyncio
    async def test_estimate_total_bars(self, data_loader):
        """测试数据量估算"""
        # 正常日期范围
        count = data_loader._estimate_total_bars("000001", "20240101", "20241231")
        assert count > 0

        # 反向日期范围（结束日期早于开始日期）
        count = data_loader._estimate_total_bars("000001", "20241231", "20240101")
        # 估算可能返回负数，应该处理为0或保持原值
        assert isinstance(count, int)

        # 无效日期格式
        count = data_loader._estimate_total_bars("000001", "invalid", "invalid")
        assert count == 0

    def test_get_load_progress_no_tasks(self, data_loader):
        """测试获取加载进度 - 无任务"""
        progress = data_loader.get_load_progress("000001")
        assert progress is None

    @pytest.mark.asyncio
    async def test_load_kline_priority_current_year(
        self, data_loader, mock_data_source, mock_persistence
    ):
        """测试加载本年度数据"""
        # 模拟返回数据
        from app.adapters.base import KLineData
        mock_klines = [
            KLineData(
                code="000001",
                date="20240101",
                open=10.0,
                high=11.0,
                low=9.0,
                close=10.5,
                volume=10000,
            )
        ]
        mock_data_source.get_kline = AsyncMock(return_value=mock_klines)

        await data_loader.start()

        progress = await data_loader.load_kline_priority(
            code="000001",
            data_source_manager=mock_data_source,
            data_persistence=mock_persistence,
            priority=LoadPriority.CURRENT_YEAR,
        )

        assert progress is not None
        assert progress.code == "000001"
        assert progress.loaded == 1
        assert len(progress.data) == 1

        # 验证持久化被调用
        mock_persistence.save_klines.assert_called_once()

        await data_loader.stop()

    @pytest.mark.asyncio
    async def test_load_kline_priority_empty_data(
        self, data_loader, mock_data_source, mock_persistence
    ):
        """测试加载空数据"""
        mock_data_source.get_kline = AsyncMock(return_value=[])

        await data_loader.start()

        progress = await data_loader.load_kline_priority(
            code="000001",
            data_source_manager=mock_data_source,
            data_persistence=mock_persistence,
            priority=LoadPriority.CURRENT_YEAR,
        )

        assert progress is not None
        assert progress.loaded == 0
        assert progress.status == "complete"

        await data_loader.stop()

    @pytest.mark.asyncio
    async def test_load_kline_priority_error(
        self, data_loader, mock_data_source, mock_persistence
    ):
        """测试加载异常"""
        mock_data_source.get_kline = AsyncMock(side_effect=Exception("Network error"))

        await data_loader.start()

        with pytest.raises(Exception, match="Network error"):
            await data_loader.load_kline_priority(
                code="000001",
                data_source_manager=mock_data_source,
                data_persistence=mock_persistence,
                priority=LoadPriority.CURRENT_YEAR,
            )

        await data_loader.stop()


class TestLoadProgress:
    """加载进度测试"""

    def test_progress_creation(self):
        """测试进度对象创建"""
        progress = LoadProgress(
            code="000001",
            status="partial",
            data=[{"date": "20240101", "close": 10.5}],
            coverage={
                "start_date": "20240101",
                "end_date": "20241231",
                "loaded": 100,
                "total_expected": 250,
            },
            background_loading=True,
            total_expected=250,
            loaded=100,
        )

        assert progress.code == "000001"
        assert progress.status == "partial"
        assert progress.background_loading is True
        assert progress.total_expected == 250
        assert progress.loaded == 100

    def test_progress_percentage(self):
        """测试进度百分比"""
        progress = LoadProgress(
            code="000001",
            status="partial",
            data=[],
            coverage={},
            total_expected=100,
            loaded=50,
        )

        percentage = (progress.loaded / progress.total_expected) * 100
        assert percentage == 50.0
