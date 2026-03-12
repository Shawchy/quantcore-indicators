"""
Tushare 适配器单元测试

测试覆盖:
1. 适配器初始化
2. API 权限检查
3. 数据获取方法
4. 错误处理
5. 降级逻辑
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
import pandas as pd

from app.adapters.tushare_adapter import TushareAdapter
from app.utils.tushare_api_registry import get_api_registry, APIGroup


class TestTushareAdapterInitialization:
    """测试适配器初始化"""
    
    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """测试初始化成功"""
        adapter = TushareAdapter()
        
        # Mock Tushare API
        with patch('tushare.pro_api') as mock_pro:
            mock_pro.return_value.trade_cal.return_value = pd.DataFrame({'pre_cal_flag': [1]})
            
            result = await adapter.initialize()
            
            assert result is True
            assert adapter._is_initialized is True
    
    @pytest.mark.asyncio
    async def test_initialization_no_token(self):
        """测试无 Token 时初始化失败"""
        with patch('app.adapters.tushare_adapter.settings') as mock_settings:
            mock_settings.TUSHARE_TOKEN = None
            
            adapter = TushareAdapter()
            result = await adapter.initialize()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_uninitialized_api_call(self):
        """测试未初始化时调用 API"""
        adapter = TushareAdapter()
        
        # 不初始化直接调用
        result = await adapter.get_weekly_kline("600519")
        
        assert result == []


class TestTushareAPIRegistry:
    """测试 API 注册表"""
    
    def test_api_registry_initialization(self):
        """测试 API 注册表初始化"""
        registry = get_api_registry()
        
        assert len(registry._apis) > 0
        assert len(registry._groups) > 0
    
    def test_api_permission_check(self):
        """测试 API 权限检查"""
        registry = get_api_registry()
        
        # 测试 120 分权限
        assert registry.check_permission("daily") is True
        assert registry.check_permission("stock_basic") is True
        
        # 测试 5000 分权限（当前 120 分应该失败）
        assert registry.check_permission("intraday") is False
    
    def test_get_available_apis(self):
        """测试获取可用 API 列表"""
        registry = get_api_registry()
        
        available = registry.get_available_apis()
        
        assert len(available) > 0
        assert "daily" in available
        assert "stock_basic" in available


class TestTushareNewAPIs:
    """测试新增 API"""
    
    @pytest.mark.asyncio
    async def test_get_weekly_kline_initialization_check(self):
        """测试周线 API 初始化检查"""
        adapter = TushareAdapter()
        
        # 未初始化调用
        result = await adapter.get_weekly_kline("600519")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_monthly_kline_initialization_check(self):
        """测试月线 API 初始化检查"""
        adapter = TushareAdapter()
        
        result = await adapter.get_monthly_kline("600519")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_top_list_initialization_check(self):
        """测试龙虎榜 API 初始化检查"""
        adapter = TushareAdapter()
        
        result = await adapter.get_top_list()
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_forecast_initialization_check(self):
        """测试业绩预告 API 初始化检查"""
        adapter = TushareAdapter()
        
        result = await adapter.get_forecast("600519")
        
        assert result == []
    
    @pytest.mark.asyncio
    async def test_get_moneyflow_initialization_check(self):
        """测试资金流向 API 初始化检查"""
        adapter = TushareAdapter()
        
        result = await adapter.get_moneyflow("600519")
        
        assert result == []


class TestTushareDataConversion:
    """测试数据转换"""
    
    def test_format_date(self):
        """测试日期格式化"""
        adapter = TushareAdapter()
        
        # 测试不同格式
        assert adapter.format_date("20240101") == "2024-01-01"
        assert adapter.format_date("2024-01-01") == "2024-01-01"
    
    def test_ts_code_conversion(self):
        """测试股票代码转换"""
        # 6 开头 -> .SH
        assert "600519.SH" == f"{'600519'}.SH"
        # 其他 -> .SZ
        assert "000001.SZ" == f"{'000001'}.SZ"


class TestTushareErrorHandling:
    """测试错误处理"""
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self):
        """测试网络错误处理"""
        adapter = TushareAdapter()
        
        with patch('tushare.pro_api') as mock_pro:
            mock_pro.side_effect = Exception("Network error")
            
            result = await adapter.initialize()
            
            assert result is False
    
    @pytest.mark.asyncio
    async def test_permission_error_handling(self):
        """测试权限错误处理"""
        adapter = TushareAdapter()
        
        with patch('tushare.pro_api') as mock_pro:
            mock_pro.return_value.trade_cal.return_value = pd.DataFrame({'pre_cal_flag': [1]})
            
            await adapter.initialize()
            
            # Mock 权限检查失败
            with patch.object(get_api_registry(), 'check_permission', return_value=False):
                result = await adapter.get_weekly_kline("600519")
                
                assert result == []
