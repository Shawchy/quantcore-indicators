"""
存储服务的单元测试
测试市场排行持久化、缓存管理等核心存储功能
"""
import pytest
import asyncio
from datetime import datetime, timedelta

from app.storage.storage_service import StorageService
from app.storage.parquet_manager import ParquetManager
from app.storage.sqlite import MarketRanking


class TestStorageServiceInit:
    """存储服务初始化测试"""

    @pytest.mark.asyncio
    async def test_create_storage_service(self):
        """测试创建存储服务"""
        service = StorageService()
        assert service is not None
        assert service.cache_manager is not None
        assert service.parquet_manager is not None

    @pytest.mark.asyncio
    async def test_close_storage_service(self):
        """测试关闭存储服务"""
        service = StorageService()
        await service.close()
        # 关闭后应该无错误


class TestCacheManager:
    """缓存管理器测试"""

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """测试缓存设置和获取"""
        service = StorageService()
        try:
            await service.cache_manager.set("test_key", {"data": "test"})
            result = await service.cache_manager.get("test_key")
            assert result is not None
            assert result.get("data") == "test"
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_cache_miss(self):
        """测试缓存未命中"""
        service = StorageService()
        try:
            result = await service.cache_manager.get("nonexistent_key")
            assert result is None
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_cache_delete(self):
        """测试缓存删除"""
        service = StorageService()
        try:
            await service.cache_manager.set("to_delete", {"data": "test"})
            deleted = await service.cache_manager.delete("to_delete")
            assert deleted is True
            result = await service.cache_manager.get("to_delete")
            assert result is None
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_cache_stats(self):
        """测试缓存统计"""
        service = StorageService()
        try:
            await service.cache_manager.set("stat_key", {"data": "test"})
            stats = service.cache_manager.get_all_stats()
            assert "total_hits" in stats
            assert "total_misses" in stats
            assert "cached_keys" in stats
            assert stats["cached_keys"] >= 1
        finally:
            await service.close()


class TestMarketRankingPersistence:
    """市场排行持久化测试"""

    @pytest.mark.asyncio
    async def test_save_market_ranking(self):
        """测试保存市场排行数据"""
        service = StorageService()
        try:
            ranking_data = {
                "gainers": [
                    {"code": "000001", "name": "平安银行", "price": 15.50, "change": 1.2, "change_pct": 8.39, "volume": 1000000, "amount": 15500000, "open": 14.50, "high": 15.80, "low": 14.30, "prev_close": 14.30, "turnover_rate": 2.5},
                    {"code": "000002", "name": "万科A", "price": 12.30, "change": 0.8, "change_pct": 6.95, "volume": 800000, "amount": 9840000, "open": 11.60, "high": 12.50, "low": 11.50, "prev_close": 11.50, "turnover_rate": 1.8},
                ]
            }

            saved = await service.save_market_ranking(ranking_data, "gainers", "efinance")
            assert saved == 2
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_save_empty_ranking(self):
        """测试保存空排行数据"""
        service = StorageService()
        try:
            ranking_data = {"losers": []}
            saved = await service.save_market_ranking(ranking_data, "losers", "akshare")
            assert saved == 0
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_get_market_ranking_history(self):
        """测试获取市场排行历史"""
        service = StorageService()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            
            # 先保存数据
            ranking_data = {
                "amount": [
                    {"code": "600519", "name": "贵州茅台", "price": 1800.00, "change": 50.0, "change_pct": 2.85, "volume": 50000, "amount": 90000000, "open": 1760.00, "high": 1820.00, "low": 1750.00, "prev_close": 1750.00, "turnover_rate": 0.5}
                ]
            }
            await service.save_market_ranking(ranking_data, "amount", "efinance")

            # 查询历史
            history = await service.get_market_ranking_history(
                ranking_type="amount",
                start_date=today,
                end_date=today,
                limit=10
            )
            assert isinstance(history, list)
            if len(history) > 0:
                assert history[0]["ts_code"] == "600519"
                assert history[0]["name"] == "贵州茅台"
        finally:
            await service.close()

    @pytest.mark.asyncio
    async def test_save_and_update_ranking(self):
        """测试保存和更新排行数据（重复保存应更新）"""
        service = StorageService()
        try:
            today = datetime.now().strftime("%Y-%m-%d")
            ranking_data = {
                "turnover": [
                    {"code": "300750", "name": "宁德时代", "price": 200.00, "change": 5.0, "change_pct": 2.56, "volume": 200000, "amount": 40000000, "open": 196.00, "high": 205.00, "low": 195.00, "prev_close": 195.00, "turnover_rate": 5.0}
                ]
            }

            # 第一次保存
            saved1 = await service.save_market_ranking(ranking_data, "turnover", "akshare")
            assert saved1 == 1

            # 第二次保存（同一日期同一代码）应更新
            ranking_data["turnover"][0]["price"] = 205.00
            saved2 = await service.save_market_ranking(ranking_data, "turnover", "akshare")
            assert saved2 == 1

            # 验证更新后的数据
            history = await service.get_market_ranking_history(
                ranking_type="turnover",
                start_date=today,
                end_date=today,
                limit=10
            )
            assert len(history) == 1
            assert history[0]["price"] == 205.00
        finally:
            await service.close()


class TestParquetManager:
    """Parquet 管理器测试"""

    @pytest.mark.asyncio
    async def test_get_storage_stats(self):
        """测试获取存储统计"""
        service = StorageService()
        try:
            stats = await service.get_storage_stats()
            assert isinstance(stats, dict)
        finally:
            await service.close()


class TestStorageServiceIntegration:
    """存储服务集成测试"""

    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """测试完整工作流：缓存 + 持久化 + 查询"""
        service = StorageService()
        try:
            # 1. 保存到缓存
            await service.cache_manager.set("temp_data", {"price": 100.0})
            
            # 2. 从缓存读取
            cached = await service.cache_manager.get("temp_data")
            assert cached["price"] == 100.0
            
            # 3. 保存到数据库
            ranking_data = {
                "gainers": [
                    {"code": "000001", "name": "平安银行", "price": 15.50, "change": 1.2, "change_pct": 8.39, "volume": 1000000, "amount": 15500000, "open": 14.50, "high": 15.80, "low": 14.30, "prev_close": 14.30, "turnover_rate": 2.5}
                ]
            }
            saved = await service.save_market_ranking(ranking_data, "gainers", "efinance")
            assert saved == 1
            
            # 4. 查询数据库
            today = datetime.now().strftime("%Y-%m-%d")
            history = await service.get_market_ranking_history("gainers", today, today)
            assert len(history) >= 1

        finally:
            await service.close()
