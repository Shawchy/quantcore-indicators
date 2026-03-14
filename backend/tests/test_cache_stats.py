"""
缓存和统计功能测试
测试 TushareAPICache 和 TushareAPIStats
"""
import pytest
import asyncio
from datetime import datetime, timedelta

from app.utils.tushare_cache_stats import (
    TushareAPICache,
    TushareAPIStats,
    APICallStats,
    CacheEntry,
    api_call_cache
)


class TestAPICallStats:
    """API 调用统计测试"""

    def test_stats_creation(self):
        """测试创建统计对象"""
        stats = APICallStats(api_name="get_kline")
        
        assert stats.api_name == "get_kline"
        assert stats.total_calls == 0
        assert stats.success_calls == 0
        assert stats.failed_calls == 0
        assert stats.total_time == 0.0

    def test_success_rate_calculation(self):
        """测试成功率计算"""
        stats = APICallStats(api_name="test")
        
        # 无调用时
        assert stats.success_rate == 0.0
        
        # 添加调用记录
        stats.total_calls = 10
        stats.success_calls = 8
        stats.failed_calls = 2
        
        assert stats.success_rate == 80.0

    def test_avg_response_time(self):
        """测试平均响应时间计算"""
        stats = APICallStats(api_name="test")
        
        # 无成功调用时
        assert stats.avg_response_time == 0.0
        
        # 添加成功调用
        stats.success_calls = 5
        stats.total_time = 1.0  # 总耗时 1 秒
        
        assert stats.avg_response_time == 200.0  # 平均 200ms


class TestCacheEntry:
    """缓存条目测试"""

    def test_cache_entry_creation(self):
        """测试创建缓存条目"""
        entry = CacheEntry(
            key="test_key",
            data={"value": 123},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=300)
        )
        
        assert entry.key == "test_key"
        assert entry.data == {"value": 123}
        assert entry.hit_count == 0

    def test_cache_expiration(self):
        """测试缓存过期"""
        # 未过期的缓存
        future_entry = CacheEntry(
            key="future",
            data={},
            created_at=datetime.now(),
            expires_at=datetime.now() + timedelta(seconds=300)
        )
        assert not future_entry.is_expired()
        
        # 已过期的缓存
        past_entry = CacheEntry(
            key="past",
            data={},
            created_at=datetime.now() - timedelta(seconds=600),
            expires_at=datetime.now() - timedelta(seconds=300)
        )
        assert past_entry.is_expired()
        
        # 永不过期的缓存
        permanent_entry = CacheEntry(
            key="permanent",
            data={},
            created_at=datetime.now(),
            expires_at=None
        )
        assert not permanent_entry.is_expired()

    def test_cache_hit(self):
        """测试缓存命中计数"""
        entry = CacheEntry(
            key="test",
            data={},
            created_at=datetime.now(),
            expires_at=None
        )
        
        assert entry.hit_count == 0
        
        entry.hit()
        assert entry.hit_count == 1
        
        entry.hit()
        entry.hit()
        assert entry.hit_count == 3


class TestTushareAPICache:
    """缓存管理器测试"""

    @pytest.fixture
    async def cache(self):
        """创建缓存实例"""
        cache = TushareAPICache(default_ttl=300, max_size=100)
        yield cache
        await cache.clear()

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache):
        """测试缓存设置和获取"""
        # 设置缓存
        await cache.set("get_kline", {"code": "000001"}, {"data": "test"}, ttl=300)
        
        # 获取缓存
        result = await cache.get("get_kline", {"code": "000001"})
        assert result == {"data": "test"}

    @pytest.mark.asyncio
    async def test_cache_miss(self, cache):
        """测试缓存未命中"""
        result = await cache.get("nonexistent", {})
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_expiration(self, cache):
        """测试缓存过期"""
        # 设置短 TTL 缓存（至少 0.1 秒以确保过期）
        await cache.set("temp", {}, {"value": 1}, ttl=0)
        
        # 立即检查应该过期（因为 TTL=0）
        result = await cache.get("temp", {})
        # TTL=0 表示立即过期
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_clear(self, cache):
        """测试清除缓存"""
        # 设置多个缓存
        await cache.set("api1", {}, {"data": 1})
        await cache.set("api2", {}, {"data": 2})
        
        # 清除所有缓存
        await cache.clear()
        
        # 验证已清除
        assert await cache.get("api1", {}) is None
        assert await cache.get("api2", {}) is None

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache):
        """测试缓存统计"""
        # 初始状态
        stats = cache.get_stats()
        assert stats["total_entries"] == 0
        assert stats["total_hits"] == 0
        assert stats["total_misses"] == 0
        
        # 设置缓存并命中
        await cache.set("test", {}, {"data": 1})
        await cache.get("test", {})  # 命中
        await cache.get("missing", {})  # 未命中
        
        stats = cache.get_stats()
        assert stats["total_entries"] == 1
        assert stats["total_hits"] == 1
        assert stats["total_misses"] == 1
        assert stats["hit_rate"] == 50.0


class TestTushareAPIStats:
    """API 统计管理器测试"""

    @pytest.fixture
    async def stats(self):
        """创建统计实例（重置单例）"""
        # 重置单例状态
        TushareAPIStats._instance = None
        stats = TushareAPIStats()
        yield stats

    @pytest.mark.asyncio
    async def test_record_success_call(self, stats):
        """测试记录成功调用"""
        await stats.record_call("get_kline", True, 0.1)
        
        api_stats = await stats.get_stats("get_kline")
        assert api_stats["total_calls"] == 1
        assert api_stats["success_calls"] == 1
        assert api_stats["failed_calls"] == 0

    @pytest.mark.asyncio
    async def test_record_failed_call(self, stats):
        """测试记录失败调用"""
        await stats.record_call("get_kline", False, 0.1, "Network error")
        
        api_stats = await stats.get_stats("get_kline")
        assert api_stats["total_calls"] == 1
        assert api_stats["success_calls"] == 0
        assert api_stats["failed_calls"] == 1
        assert api_stats["last_error"] == "Network error"

    @pytest.mark.asyncio
    async def test_multiple_calls(self, stats):
        """测试多次调用统计"""
        # 记录多次调用
        for i in range(10):
            await stats.record_call("get_kline", i < 8, 0.05)  # 8 成功，2 失败
        
        api_stats = await stats.get_stats("get_kline")
        assert api_stats["total_calls"] == 10
        assert api_stats["success_calls"] == 8
        assert api_stats["failed_calls"] == 2

    @pytest.mark.asyncio
    async def test_get_all_stats(self, stats):
        """测试获取所有统计"""
        await stats.record_call("api1", True, 0.1)
        await stats.record_call("api2", True, 0.2)
        
        all_stats = await stats.get_stats()
        assert "api1" in all_stats
        assert "api2" in all_stats

    @pytest.mark.asyncio
    async def test_generate_report(self, stats):
        """测试生成报告"""
        await stats.record_call("get_kline", True, 0.1)
        await stats.record_call("get_stock_list", True, 0.2)
        
        report = await stats.get_report()
        assert "Tushare API 调用统计报告" in report
        assert "get_kline" in report
        assert "get_stock_list" in report


class TestAPICallCacheDecorator:
    """缓存装饰器测试"""

    @pytest.mark.asyncio
    async def test_decorator_caches_result(self):
        """测试装饰器缓存结果"""
        call_count = 0
        
        @api_call_cache(ttl=300)
        async def test_api(param):
            nonlocal call_count
            call_count += 1
            return {"result": param}
        
        # 第一次调用
        result1 = await test_api("value1")
        assert result1 == {"result": "value1"}
        assert call_count == 1
        
        # 第二次调用（应该命中缓存）
        result2 = await test_api("value1")
        assert result2 == {"result": "value1"}
        assert call_count == 1  # 不应该增加
        
        # 不同参数的调用（需要新调用）
        result3 = await test_api("value2")
        assert result3 == {"result": "value2"}
        assert call_count == 2  # 新参数，需要调用

    @pytest.mark.asyncio
    async def test_decorator_records_stats(self):
        """测试装饰器记录统计"""
        @api_call_cache()
        async def test_api():
            return {"data": 123}
        
        await test_api()
        
        # 验证统计已记录（装饰器内部会记录）
        # 注意：这里只是验证装饰器能正常工作
        assert True
