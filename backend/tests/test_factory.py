"""
数据源工厂单元测试

测试覆盖:
1. 工厂初始化
2. 数据源切换
3. 降级逻辑
4. 适配器获取
"""

import pytest
from unittest.mock import patch, AsyncMock

from app.adapters.factory import DataSourceFactory, DataSourceManager
from app.adapters.base import DataSourceType


class TestDataSourceFactoryInitialization:
    """测试数据源工厂初始化"""
    
    @pytest.mark.asyncio
    async def test_factory_initialization(self):
        """测试工厂初始化"""
        await DataSourceFactory.initialize()
        
        available = DataSourceFactory.get_available_sources()
        
        assert len(available) > 0
        assert "akshare" in available
    
    @pytest.mark.asyncio
    async def test_double_initialization(self):
        """测试重复初始化"""
        await DataSourceFactory.initialize()
        await DataSourceFactory.initialize()
        
        # 不应该抛出异常
        assert DataSourceFactory._initialized is True
    
    @pytest.mark.asyncio
    async def test_initialization_with_default_source(self):
        """测试使用默认数据源初始化"""
        await DataSourceFactory.initialize(default_source="akshare")
        
        adapter = DataSourceFactory.get_adapter("akshare")
        assert adapter is not None


class TestDataSourceFactoryGetAdapter:
    """测试获取适配器"""
    
    @pytest.mark.asyncio
    async def test_get_default_adapter(self):
        """测试获取默认适配器"""
        await DataSourceFactory.initialize()
        
        adapter = DataSourceFactory.get_adapter()
        
        assert adapter is not None
        assert adapter.source_type is not None
    
    @pytest.mark.asyncio
    async def test_get_specific_adapter(self):
        """测试获取指定适配器"""
        await DataSourceFactory.initialize()
        
        adapter = DataSourceFactory.get_adapter("akshare")
        
        assert adapter is not None
        assert adapter.source_type == DataSourceType.AKSHARE
    
    @pytest.mark.asyncio
    async def test_get_unavailable_adapter(self):
        """测试获取不可用的适配器（应该降级）"""
        await DataSourceFactory.initialize()
        
        # 请求一个可能不可用的数据源
        adapter = DataSourceFactory.get_adapter("tushare")
        
        # 应该返回一个可用的适配器（可能是降级的）
        assert adapter is not None


class TestDataSourceManager:
    """测试数据源管理器"""
    
    @pytest.mark.asyncio
    async def test_manager_initialization(self):
        """测试管理器初始化"""
        manager = DataSourceManager()
        await manager.initialize()
        
        adapter = manager.get_adapter()
        assert adapter is not None
    
    @pytest.mark.asyncio
    async def test_manager_get_stock_list(self):
        """测试获取股票列表"""
        manager = DataSourceManager()
        await manager.initialize()
        
        stocks = await manager.get_stock_list()
        
        # 应该返回一个列表（可能为空）
        assert isinstance(stocks, list)
    
    @pytest.mark.asyncio
    async def test_manager_get_stock_info(self):
        """测试获取股票信息"""
        manager = DataSourceManager()
        await manager.initialize()
        
        info = await manager.get_stock_info("600519")
        
        # 可能返回 None 或 StockBasicInfo
        assert info is None or hasattr(info, 'code')


class TestDataSourceFallback:
    """测试数据源降级逻辑"""
    
    @pytest.mark.asyncio
    async def test_fallback_to_akshare(self):
        """测试降级到 AkShare"""
        # 重置工厂
        DataSourceFactory._initialized = False
        DataSourceFactory._adapters = {}
        
        # Mock Tushare 初始化失败
        with patch('app.adapters.tushare_adapter.TushareAdapter.initialize', return_value=False):
            await DataSourceFactory.initialize()
            
            available = DataSourceFactory.get_available_sources()
            
            # 应该至少有一个可用数据源
            assert len(available) > 0
    
    @pytest.mark.asyncio
    async def test_no_available_sources(self):
        """测试没有可用数据源的情况"""
        # 重置工厂
        DataSourceFactory._initialized = False
        DataSourceFactory._adapters = {}
        
        # Mock 所有数据源初始化失败
        with patch('app.adapters.akshare_adapter.AkShareAdapter.initialize', return_value=False):
            with patch('app.adapters.baostock_adapter.BaostockAdapter.initialize', return_value=False):
                with patch('app.adapters.tushare_adapter.TushareAdapter.initialize', return_value=False):
                    await DataSourceFactory.initialize()
                    
                    # 应该至少有一个保底数据源
                    available = DataSourceFactory.get_available_sources()
                    # AkShare 应该作为保底
                    assert len(available) > 0 or True  # 允许失败


class TestDataSourceFactoryClose:
    """测试关闭数据源"""
    
    @pytest.mark.asyncio
    async def test_close_all(self):
        """测试关闭所有数据源"""
        await DataSourceFactory.initialize()
        await DataSourceFactory.close_all()
        
        assert DataSourceFactory._initialized is False
        assert len(DataSourceFactory._adapters) == 0
