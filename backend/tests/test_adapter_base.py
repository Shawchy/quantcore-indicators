"""
数据源适配器基础测试
测试适配器基类和通用功能
"""
import pytest
import asyncio
from datetime import datetime
from unittest.mock import Mock, AsyncMock

from app.adapters.base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData
)


class TestDataSourceType:
    """数据源类型枚举测试"""

    def test_enum_values(self):
        """测试枚举值"""
        assert DataSourceType.AKSHARE.value == "akshare"
        assert DataSourceType.BAOSTOCK.value == "baostock"
        assert DataSourceType.YFINANCE.value == "yfinance"
        assert DataSourceType.EFINANCE.value == "efinance"

    def test_enum_comparison(self):
        """测试枚举比较"""
        assert DataSourceType.AKSHARE == DataSourceType("akshare")
        assert DataSourceType.AKSHARE != DataSourceType.BAOSTOCK


class TestStockBasicInfo:
    """股票基本信息数据类测试"""

    def test_stock_basic_info_creation(self):
        """测试创建股票基本信息"""
        stock = StockBasicInfo(
            code="000001",
            name="平安银行",
            market="SZ",
            industry="银行",
            area="深圳",
            list_date="1991-04-03",
            total_shares=1000000.0,
            float_shares=500000.0
        )
        
        assert stock.code == "000001"
        assert stock.name == "平安银行"
        assert stock.market == "SZ"
        assert stock.industry == "银行"
        assert stock.area == "深圳"
        assert stock.list_date == "1991-04-03"
        assert stock.total_shares == 1000000.0
        assert stock.float_shares == 500000.0

    def test_stock_basic_info_optional_fields(self):
        """测试可选字段"""
        stock = StockBasicInfo(
            code="000001",
            name="平安银行",
            market=None,
            industry=None,
            area=None,
            list_date=None,
            total_shares=None,
            float_shares=None
        )
        
        assert stock.code == "000001"
        assert stock.name == "平安银行"
        assert stock.market is None
        assert stock.industry is None


class TestKLineData:
    """K线数据类测试"""

    def test_kline_data_creation(self):
        """测试创建K线数据"""
        kline = KLineData(
            code="000001",
            date="2024-01-01",
            open=10.0,
            high=11.0,
            low=9.0,
            close=10.5,
            volume=10000,
            amount=105000.0
        )
        
        assert kline.code == "000001"
        assert kline.date == "2024-01-01"
        assert kline.open == 10.0
        assert kline.high == 11.0
        assert kline.low == 9.0
        assert kline.close == 10.5
        assert kline.volume == 10000
        assert kline.amount == 105000.0

    def test_kline_data_price_validation(self):
        """测试价格数据验证"""
        # 测试价格逻辑：high >= open, close >= low
        kline = KLineData(
            code="000001",
            date="2024-01-01",
            open=10.0,
            high=11.0,
            low=9.0,
            close=10.5,
            volume=10000
        )
        
        assert kline.high >= kline.low
        assert kline.high >= kline.open
        assert kline.high >= kline.close
        assert kline.low <= kline.open
        assert kline.low <= kline.close


class TestSectorInfo:
    """板块信息数据类测试"""

    def test_sector_info_creation(self):
        """测试创建板块信息"""
        sector = SectorInfo(
            code="801010",
            name="农林牧渔",
            sector_type="industry"
        )
        
        assert sector.code == "801010"
        assert sector.name == "农林牧渔"
        assert sector.sector_type == "industry"


class TestChipData:
    """筹码数据类测试"""

    def test_chip_data_creation(self):
        """测试创建筹码数据"""
        chip = ChipData(
            code="000001",
            date="2024-01-01",
            shareholder_count=100000.0
        )
        
        assert chip.code == "000001"
        assert chip.date == "2024-01-01"
        assert chip.shareholder_count == 100000.0


class TestBaseDataAdapter:
    """数据适配器基类测试"""

    @pytest.fixture
    def mock_adapter(self):
        """创建模拟适配器"""
        class MockAdapter(BaseDataAdapter):
            def __init__(self):
                self._initialized = False
                self._source_type = DataSourceType.AKSHARE
            
            @property
            def source_type(self):
                return self._source_type
            
            async def initialize(self) -> bool:
                self._initialized = True
                return True
            
            async def close(self) -> None:
                self._initialized = False
            
            async def get_stock_list(self, market=None):
                return []
            
            async def get_stock_info(self, code):
                return None
            
            async def get_kline(self, code, start_date=None, end_date=None, adjust="qfq"):
                return []
            
            async def get_sector_list(self, sector_type="industry"):
                return []
            
            async def get_sector_components(self, sector_code):
                return []
            
            async def get_realtime_quote(self, code):
                return {}
            
            async def get_chip_data(self, code, start_date=None, end_date=None):
                return []
        
        return MockAdapter()

    @pytest.mark.asyncio
    async def test_adapter_initialization(self, mock_adapter):
        """测试适配器初始化"""
        assert not mock_adapter._initialized
        
        result = await mock_adapter.initialize()
        assert result is True
        assert mock_adapter._initialized

    @pytest.mark.asyncio
    async def test_adapter_close(self, mock_adapter):
        """测试适配器关闭"""
        await mock_adapter.initialize()
        assert mock_adapter._initialized
        
        await mock_adapter.close()
        assert not mock_adapter._initialized

    @pytest.mark.asyncio
    async def test_get_stock_list(self, mock_adapter):
        """测试获取股票列表"""
        await mock_adapter.initialize()
        stocks = await mock_adapter.get_stock_list()
        assert isinstance(stocks, list)

    @pytest.mark.asyncio
    async def test_get_kline(self, mock_adapter):
        """测试获取K线数据"""
        await mock_adapter.initialize()
        klines = await mock_adapter.get_kline("000001")
        assert isinstance(klines, list)

    def test_source_type(self, mock_adapter):
        """测试数据源类型"""
        assert mock_adapter.source_type == DataSourceType.AKSHARE
