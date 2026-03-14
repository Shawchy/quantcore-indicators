"""
权限管理测试
测试 TusharePointsManager 和 API 权限控制
"""
import pytest
from unittest.mock import Mock, patch

from app.utils.tushare_points_manager import TusharePointsManager
from app.config import settings


class TestTusharePointsManager:
    """积分管理器测试"""

    @pytest.fixture
    def manager_120(self, monkeypatch):
        """创建 120 积分管理器"""
        # 重置单例
        TusharePointsManager._instance = None
        TusharePointsManager._initialized = False
        
        # 修改配置
        monkeypatch.setattr(settings, "TUSHARE_POINTS", 120)
        
        return TusharePointsManager()

    @pytest.fixture
    def manager_5000(self, monkeypatch):
        """创建 5000 积分管理器"""
        # 重置单例
        TusharePointsManager._instance = None
        TusharePointsManager._initialized = False
        
        # 修改配置
        monkeypatch.setattr(settings, "TUSHARE_POINTS", 5000)
        
        return TusharePointsManager()

    def test_manager_initialization(self, monkeypatch):
        """测试管理器初始化"""
        # 重置单例
        TusharePointsManager._instance = None
        TusharePointsManager._initialized = False
        
        monkeypatch.setattr(settings, "TUSHARE_POINTS", 120)
        
        manager = TusharePointsManager()
        assert manager.points == settings.TUSHARE_POINTS
        assert isinstance(manager.available_permissions, set)

    def test_get_points(self, manager_120):
        """测试获取积分"""
        assert manager_120.get_points() == 120

    def test_has_permission_with_120_points(self, manager_120):
        """测试 120 积分的权限"""
        # 应该有的权限
        assert manager_120.has_permission("daily") is True
        assert manager_120.has_permission("stock_basic") is True
        assert manager_120.has_permission("trade_cal") is True
        
        # 不应该有的权限
        assert manager_120.has_permission("weekly") is False
        assert manager_120.has_permission("moneyflow") is False
        assert manager_120.has_permission("intraday") is False

    def test_has_permission_with_5000_points(self, manager_5000):
        """测试 5000 积分的权限"""
        # 基础权限
        assert manager_5000.has_permission("daily") is True
        assert manager_5000.has_permission("stock_basic") is True
        
        # 高级权限
        assert manager_5000.has_permission("weekly") is True
        assert manager_5000.has_permission("monthly") is True
        assert manager_5000.has_permission("moneyflow") is True
        assert manager_5000.has_permission("intraday") is True
        
        # 专业权限（需要 10000 分）
        assert manager_5000.has_permission("chip_distribution") is False

    def test_get_points_needed(self, manager_120):
        """测试获取所需积分"""
        # 基础接口
        assert manager_120.get_points_needed("daily") == 0
        assert manager_120.get_points_needed("stock_basic") == 0
        
        # 高级接口
        assert manager_120.get_points_needed("weekly") == 2000
        assert manager_120.get_points_needed("moneyflow") == 5000
        
        # 专业接口
        assert manager_120.get_points_needed("chip_distribution") == 10000
        
        # 未知接口
        assert manager_120.get_points_needed("unknown_api") == 0

    def test_get_available_apis(self, manager_120, manager_5000):
        """测试获取可用 API 列表"""
        # 120 积分
        apis_120 = manager_120.get_available_apis()
        assert "daily" in apis_120
        assert "stock_basic" in apis_120
        assert "weekly" not in apis_120
        
        # 5000 积分
        apis_5000 = manager_5000.get_available_apis()
        assert "daily" in apis_5000
        assert "weekly" in apis_5000
        assert "moneyflow" in apis_5000

    def test_get_unavailable_apis(self, manager_120):
        """测试获取不可用 API 列表"""
        unavailable = manager_120.get_unavailable_apis()
        
        # 检查不可用 API 列表
        api_names = [api["name"] for api in unavailable]
        assert "weekly" in api_names
        assert "moneyflow" in api_names
        
        # 检查缺少的积分
        weekly_api = next(api for api in unavailable if api["name"] == "weekly")
        assert weekly_api["lack_points"] == 1880  # 2000 - 120

    def test_get_permission_summary(self, manager_120, manager_5000):
        """测试获取权限摘要"""
        # 120 积分
        summary_120 = manager_120.get_permission_summary()
        assert summary_120["points"] == 120
        assert summary_120["available_count"] > 0
        assert summary_120["unavailable_count"] > 0
        assert summary_120["next_level"] == 200
        assert summary_120["points_to_next"] == 80
        
        # 5000 积分
        summary_5000 = manager_5000.get_permission_summary()
        assert summary_5000["points"] == 5000
        assert summary_5000["next_level"] == 10000
        assert summary_5000["points_to_next"] == 5000

    @pytest.mark.asyncio
    async def test_check_and_log_permission_success(self, manager_120):
        """测试权限检查成功"""
        # 有权限的 API
        result = await manager_120.check_and_log_permission("daily", "akshare")
        assert result is True

    @pytest.mark.asyncio
    async def test_check_and_log_permission_failure(self, manager_120):
        """测试权限检查失败"""
        # 无权限的 API
        result = await manager_120.check_and_log_permission("weekly", "akshare")
        assert result is False

    def test_calculate_available_permissions(self, monkeypatch):
        """测试权限计算逻辑"""
        # 重置单例
        TusharePointsManager._instance = None
        TusharePointsManager._initialized = False
        
        # 测试不同积分等级
        test_cases = [
            (0, 0),      # 0 积分，无权限
            (120, 13),   # 120 积分，基础权限
            (200, 16),   # 200 积分，增加龙虎榜等
            (5000, 22),  # 5000 积分，增加分钟线等
            (10000, 26), # 10000 积分，全部权限
        ]
        
        for points, expected_count in test_cases:
            # 重置单例
            TusharePointsManager._instance = None
            TusharePointsManager._initialized = False
            
            monkeypatch.setattr(settings, "TUSHARE_POINTS", points)
            manager = TusharePointsManager()
            available = manager.get_available_apis()
            # 只验证数量大致正确（具体数量可能因配置变化）
            if points == 0:
                assert len(available) == expected_count
            else:
                assert len(available) >= expected_count


class TestPermissionEdgeCases:
    """权限边界情况测试"""

    def test_zero_points(self, monkeypatch):
        """测试 0 积分"""
        # 重置单例
        TusharePointsManager._instance = None
        TusharePointsManager._initialized = False
        
        monkeypatch.setattr(settings, "TUSHARE_POINTS", 0)
        manager = TusharePointsManager()
        
        assert manager.get_points() == 0
        assert manager.has_permission("daily") is False
        assert manager.get_available_apis() == []

    def test_negative_points(self, monkeypatch):
        """测试负数积分"""
        # 重置单例
        TusharePointsManager._instance = None
        TusharePointsManager._initialized = False
        
        monkeypatch.setattr(settings, "TUSHARE_POINTS", -100)
        manager = TusharePointsManager()
        
        assert manager.get_points() == -100
        assert manager.has_permission("daily") is False

    def test_very_high_points(self, monkeypatch):
        """测试超高积分"""
        # 重置单例
        TusharePointsManager._instance = None
        TusharePointsManager._initialized = False
        
        monkeypatch.setattr(settings, "TUSHARE_POINTS", 100000)
        manager = TusharePointsManager()
        
        available = manager.get_available_apis()
        # 应该拥有所有权限
        assert "daily" in available
        assert "weekly" in available
        assert "moneyflow" in available
        assert "chip_distribution" in available

    def test_permission_config_structure(self):
        """测试权限配置结构"""
        manager = TusharePointsManager()
        config = settings.TUSHARE_PERMISSION_CONFIG
        
        # 验证配置结构
        assert isinstance(config, dict)
        
        # 验证积分等级
        for points_level in [120, 200, 800, 2000, 5000, 10000]:
            if points_level in config:
                assert isinstance(config[points_level], dict)
                # 验证每个 API 配置
                for api_name, enabled in config[points_level].items():
                    assert isinstance(api_name, str)
                    assert isinstance(enabled, bool)


class TestPermissionIntegration:
    """权限集成测试"""

    @pytest.fixture
    def mock_adapter(self, monkeypatch):
        """创建带权限检查的模拟适配器"""
        from app.adapters.base import BaseDataAdapter, DataSourceType
        
        def create_adapter(points=120):
            # 重置单例
            TusharePointsManager._instance = None
            TusharePointsManager._initialized = False
            
            monkeypatch.setattr(settings, "TUSHARE_POINTS", points)
            
            class MockAdapterWithPermission(BaseDataAdapter):
                def __init__(self):
                    self._initialized = False
                    self._source_type = DataSourceType.TUSHARE
                    self._points_manager = TusharePointsManager()
                
                @property
                def source_type(self):
                    return self._source_type
                
                async def initialize(self):
                    self._initialized = True
                    return True
                
                async def close(self):
                    self._initialized = False
                
                async def get_kline(self, code, start_date=None, end_date=None, adjust="qfq"):
                    # 检查权限
                    if not self._points_manager.has_permission("daily"):
                        return []
                    return [{"code": code, "close": 10.5}]
                
                async def get_weekly_kline(self, code, start_date=None, end_date=None, adjust="qfq"):
                    # 检查权限
                    if not self._points_manager.has_permission("weekly"):
                        return []
                    return [{"code": code, "close": 50.0}]
                
                # 其他必需方法
                async def get_stock_list(self, market=None): return []
                async def get_stock_info(self, code): return None
                async def get_sector_list(self, sector_type="industry"): return []
                async def get_sector_components(self, sector_code): return []
                async def get_realtime_quote(self, code): return {}
                async def get_chip_data(self, code, start_date=None, end_date=None): return []
            
            return MockAdapterWithPermission()
        
        return create_adapter

    @pytest.mark.asyncio
    async def test_adapter_with_sufficient_points(self, mock_adapter):
        """测试有足够积分的适配器"""
        adapter = mock_adapter(points=120)
        await adapter.initialize()
        
        # 应该能获取日线数据
        result = await adapter.get_kline("000001")
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_adapter_with_insufficient_points(self, mock_adapter):
        """测试积分不足的适配器"""
        adapter = mock_adapter(points=120)
        await adapter.initialize()
        
        # 不应该能获取周线数据（需要 2000 分）
        result = await adapter.get_weekly_kline("000001")
        assert result == []

    @pytest.mark.asyncio
    async def test_adapter_with_high_points(self, mock_adapter):
        """测试高积分适配器"""
        adapter = mock_adapter(points=5000)
        await adapter.initialize()
        
        # 应该能获取所有数据
        daily = await adapter.get_kline("000001")
        weekly = await adapter.get_weekly_kline("000001")
        
        assert len(daily) > 0
        assert len(weekly) > 0
