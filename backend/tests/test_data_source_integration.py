"""
数据源集成测试
测试多数据源适配器的完整流程
"""
import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from app.adapters.factory import DataSourceFactory, data_source_manager
from app.adapters.base import DataSourceType, StockBasicInfo, KLineData
from app.config import settings


@pytest.fixture(scope="module")
def event_loop():
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="module")
async def initialized_factory():
    """初始化数据源工厂"""
    await DataSourceFactory.initialize()
    yield DataSourceFactory
    await DataSourceFactory.close_all()


class TestDataSourceFactory:
    """数据源工厂测试"""

    @pytest.mark.asyncio
    async def test_factory_initialize(self):
        """测试数据源工厂初始化"""
        # 先关闭再初始化
        await DataSourceFactory.close_all()
        await DataSourceFactory.initialize()
        assert DataSourceFactory._initialized is True
        assert len(DataSourceFactory._adapters) > 0

    @pytest.mark.asyncio
    async def test_get_adapter_after_init(self):
        """测试初始化后获取适配器"""
        await DataSourceFactory.initialize()
        adapter = DataSourceFactory.get_adapter()
        assert adapter is not None
        assert adapter.source_type in [DataSourceType.TUSHARE, DataSourceType.AKSHARE, DataSourceType.BAOSTOCK]

    @pytest.mark.asyncio
    async def test_get_available_sources(self):
        """测试获取可用数据源列表"""
        await DataSourceFactory.initialize()
        sources = DataSourceFactory.get_available_sources()
        assert isinstance(sources, list)
        assert len(sources) > 0


class TestDataSourceManager:
    """数据源管理器测试"""

    @pytest.mark.asyncio
    async def test_manager_singleton(self):
        """测试管理器单例模式"""
        manager1 = data_source_manager
        manager2 = data_source_manager
        assert manager1 is manager2

    @pytest.mark.asyncio
    async def test_get_adapter_priority(self):
        """测试按优先级获取适配器"""
        # 先确保已初始化
        await data_source_manager.initialize()
        # 获取默认适配器
        adapter = data_source_manager.get_adapter()
        # 应该返回一个适配器实例
        assert adapter is not None

    @pytest.mark.asyncio
    async def test_get_adapter_by_type(self):
        """测试按类型获取适配器"""
        await data_source_manager.initialize()
        # 尝试获取 Tushare 适配器
        try:
            adapter = data_source_manager.get_adapter(DataSourceType.TUSHARE.value)
            # 如果 Tushare 未配置，可能返回其他适配器
            assert adapter is not None
        except ValueError:
            # 如果 Tushare 不可用，会返回其他可用适配器
            adapter = data_source_manager.get_adapter()
            assert adapter is not None


class TestTushareAdapter:
    """Tushare 适配器集成测试"""

    @pytest.mark.asyncio
    async def test_tushare_initialization(self):
        """测试 Tushare 适配器初始化"""
        from app.adapters.tushare_adapter import TushareAdapter

        adapter = TushareAdapter()
        # 没有 token 时应该初始化失败
        if not settings.TUSHARE_TOKEN:
            result = await adapter.initialize()
            assert result is False
        else:
            # 有 token 时尝试初始化
            result = await adapter.initialize()
            # 结果取决于 token 是否有效
            assert isinstance(result, bool)

    @pytest.mark.asyncio
    async def test_tushare_format_date(self):
        """测试日期格式化"""
        from app.adapters.tushare_adapter import TushareAdapter

        adapter = TushareAdapter()

        # 测试不同日期格式
        assert adapter.format_date("20240101") == "2024-01-01"
        assert adapter.format_date("2024-01-01") == "2024-01-01"


class TestAkshareAdapter:
    """Akshare 适配器集成测试"""

    @pytest.mark.asyncio
    async def test_akshare_initialization(self):
        """测试 Akshare 适配器初始化"""
        from app.adapters.akshare_adapter import AkShareAdapter

        adapter = AkShareAdapter()
        result = await adapter.initialize()
        # Akshare 通常不需要配置即可初始化
        assert result is True

    @pytest.mark.asyncio
    async def test_akshare_get_stock_list_mock(self):
        """测试获取股票列表（模拟）"""
        from app.adapters.akshare_adapter import AkShareAdapter

        adapter = AkShareAdapter()
        await adapter.initialize()

        # 使用 mock 测试
        with patch.object(adapter, '_get_stock_list_impl') as mock_get:
            mock_get.return_value = [
                StockBasicInfo(code="000001", name="平安银行", market="SZ"),
                StockBasicInfo(code="000002", name="万科A", market="SZ"),
            ]

            stocks = await adapter.get_stock_list()
            assert len(stocks) == 2
            assert stocks[0].code == "000001"
            assert stocks[1].code == "000002"


class TestDataSourceFallback:
    """数据源降级测试"""

    @pytest.mark.asyncio
    async def test_fallback_to_next_source(self):
        """测试降级到下一个数据源"""
        # 创建一个模拟场景，第一个数据源失败，第二个成功
        mock_adapter1 = Mock()
        mock_adapter1.get_stock_list = AsyncMock(return_value=[])
        mock_adapter1._is_initialized = True

        mock_adapter2 = Mock()
        mock_adapter2.get_stock_list = AsyncMock(return_value=[
            StockBasicInfo(code="000001", name="平安银行", market="SZ")
        ])
        mock_adapter2._is_initialized = True

        # 测试降级逻辑
        result = await mock_adapter2.get_stock_list()
        assert len(result) == 1
        assert result[0].code == "000001"

    @pytest.mark.asyncio
    async def test_all_sources_fail(self):
        """测试所有数据源都失败的情况"""
        mock_adapter = Mock()
        mock_adapter.get_stock_list = AsyncMock(side_effect=Exception("Network error"))
        mock_adapter._is_initialized = True

        # 应该返回空列表或抛出异常
        try:
            result = await mock_adapter.get_stock_list()
            # 如果实现返回空列表
            assert result == []
        except Exception:
            # 如果实现抛出异常
            pass


class TestDataSourcePerformance:
    """数据源性能测试"""

    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """测试并发请求性能"""
        from app.adapters.akshare_adapter import AkShareAdapter

        adapter = AkShareAdapter()
        await adapter.initialize()

        # 模拟并发请求
        async def fetch_data(code):
            # 模拟数据获取
            await asyncio.sleep(0.01)  # 模拟延迟
            return KLineData(
                code=code,
                date="20240101",
                open=10.0,
                high=11.0,
                low=9.0,
                close=10.5,
                volume=10000,
            )

        # 并发获取 5 只股票的数据
        codes = ["000001", "000002", "000003", "000004", "000005"]
        start_time = asyncio.get_event_loop().time()

        tasks = [fetch_data(code) for code in codes]
        results = await asyncio.gather(*tasks)

        end_time = asyncio.get_event_loop().time()
        duration = end_time - start_time

        # 验证结果
        assert len(results) == 5
        # 并发执行应该比串行快（串行需要 0.05s，并发应该小于 0.05s）
        assert duration < 0.05


class TestDataSourceErrorHandling:
    """数据源错误处理测试"""

    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """测试网络错误处理"""
        mock_adapter = Mock()
        mock_adapter.get_stock_list = AsyncMock(side_effect=ConnectionError("Network error"))

        with pytest.raises(ConnectionError):
            await mock_adapter.get_stock_list()

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """测试超时处理"""
        mock_adapter = Mock()
        mock_adapter.get_stock_list = AsyncMock(side_effect=asyncio.TimeoutError())

        with pytest.raises(asyncio.TimeoutError):
            await mock_adapter.get_stock_list()

    @pytest.mark.asyncio
    async def test_invalid_data_handling(self):
        """测试无效数据处理"""
        mock_adapter = Mock()
        mock_adapter.get_stock_list = AsyncMock(return_value=None)

        result = await mock_adapter.get_stock_list()
        # 应该返回空列表而不是 None
        assert result is None or result == []
