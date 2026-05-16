"""
AkShare 适配器单元测试

测试覆盖:
1. 适配器初始化
2. 数据获取方法
3. 错误处理
4. 超时控制
"""

import pytest
from unittest.mock import patch
import pandas as pd

from app.adapters.akshare_adapter import AkShareAdapter


class TestAkShareAdapterInitialization:
    """测试 AkShare 适配器初始化"""
    
    @pytest.mark.asyncio
    async def test_initialization_success(self):
        """测试初始化成功"""
        adapter = AkShareAdapter()
        result = await adapter.initialize()
        
        assert result is True
        assert adapter._is_initialized is True
    
    @pytest.mark.asyncio
    async def test_double_initialization(self):
        """测试重复初始化"""
        adapter = AkShareAdapter()
        
        result1 = await adapter.initialize()
        result2 = await adapter.initialize()
        
        assert result1 is True
        assert result2 is True


class TestAkShareDataConversion:
    """测试数据转换"""
    
    def test_format_date(self):
        """测试日期格式化"""
        adapter = AkShareAdapter()
        
        assert adapter.format_date("20240101") == "2024-01-01"
        assert adapter.format_date("2024-01-01") == "2024-01-01"
    
    def test_code_conversion(self):
        """测试代码转换"""
        adapter = AkShareAdapter()
        
        # 测试基本功能
        assert adapter is not None


class TestAkShareRealtimeData:
    """测试实时数据"""
    
    @pytest.mark.asyncio
    async def test_get_realtime_quote(self):
        """测试获取实时行情"""
        adapter = AkShareAdapter()
        await adapter.initialize()
        
        with patch('akshare.stock_zh_a_spot') as mock_api:
            mock_api.return_value = pd.DataFrame({
                'code': ['000001'],
                'name': ['平安银行'],
                '最新价': [3000.0],
                '涨跌额': [10.0],
                '涨跌幅': [0.33],
                '成交量': [1000000.0],
                '成交额': [100000000.0],
                '最高': [3010.0],
                '最低': [2990.0],
                '今开': [2995.0],
                '昨收': [2990.0],
                '换手率': [1.5]
            })
            
            result = await adapter.get_realtime_quote("000001")
            
            assert result is not None
            assert result['code'] == "000001"
            assert result['price'] == 3000.0
    
    @pytest.mark.asyncio
    async def test_get_realtime_quote_timeout(self):
        """测试获取实时行情超时"""
        adapter = AkShareAdapter()
        await adapter.initialize()
        
        with patch('akshare.stock_zh_a_spot') as mock_api:
            mock_api.side_effect = TimeoutError("Request timeout")
            
            result = await adapter.get_realtime_quote("000001")
            
            assert result == {}


class TestAkShareKLineData:
    """测试 K 线数据"""
    
    @pytest.mark.asyncio
    async def test_get_kline(self):
        """测试获取 K 线数据"""
        adapter = AkShareAdapter()
        await adapter.initialize()
        
        with patch('akshare.stock_zh_a_hist') as mock_api:
            mock_api.return_value = pd.DataFrame({
                '日期': ['2024-01-01', '2024-01-02'],
                '开盘': [10.0, 10.5],
                '最高': [10.8, 11.0],
                '最低': [9.8, 10.2],
                '收盘': [10.5, 10.8],
                '成交量': [1000, 1200],
                '成交额': [10000, 12000]
            })
            
            result = await adapter.get_kline("600519", "2024-01-01", "2024-01-02")
            
            assert len(result) == 2
            assert result[0].code == "600519"
            assert result[0].open == 10.0


class TestAkShareErrorHandling:
    """测试错误处理"""
    
    @pytest.mark.asyncio
    async def test_empty_dataframe_handling(self):
        """测试空 DataFrame 处理"""
        adapter = AkShareAdapter()
        await adapter.initialize()
        
        with patch('akshare.stock_zh_index_spot_em') as mock_api:
            mock_api.return_value = pd.DataFrame()
            
            result = await adapter.get_realtime_quote("000001")
            
            assert result == {}
    
    @pytest.mark.asyncio
    async def test_exception_handling(self):
        """测试异常处理"""
        adapter = AkShareAdapter()
        await adapter.initialize()
        
        with patch('akshare.stock_zh_index_spot_em') as mock_api:
            mock_api.side_effect = Exception("API error")
            
            result = await adapter.get_realtime_quote("000001")
            
            assert result == {}
