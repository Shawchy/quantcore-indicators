"""
存储层重构测试脚本

测试新的 UnifiedStorageService 和 CacheService 功能
"""
import asyncio
import traceback
from datetime import datetime, timedelta
from loguru import logger

print("开始导入 storage_service...")
try:
    from app.storage.storage_service import storage_service
    print("✓ storage_service 导入成功")
except Exception as e:
    print(f"✗ storage_service 导入失败：{e}")
    traceback.print_exc()
    exit(1)

print("开始导入 cache_service...")
try:
    from app.services.cache_service import cache_service
    print("✓ cache_service 导入成功")
except Exception as e:
    print(f"✗ cache_service 导入失败：{e}")
    traceback.print_exc()
    exit(1)


async def test_storage_service_basic():
    """测试 storage_service 基本功能"""
    print("\n=== 测试 storage_service 基本功能 ===")
    
    # 测试 1: 获取不存在的 K 线数据（应该返回空列表）
    print("\n1. 测试获取 K 线数据（空数据）")
    code = "000001"
    start_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    end_date = datetime.now().strftime("%Y-%m-%d")
    
    klines = await storage_service.get_kline(
        code=code,
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
        use_cache=True
    )
    
    print(f"   获取 {code} 的 K 线数据：{len(klines) if klines else 0} 条")
    
    # 测试 2: 保存测试数据
    print("\n2. 测试保存 K 线数据")
    test_klines = [
        {
            "code": code,
            "date": (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d"),
            "open": 10.0 + i * 0.1,
            "high": 10.5 + i * 0.1,
            "low": 9.5 + i * 0.1,
            "close": 10.2 + i * 0.1,
            "volume": 1000000,
            "amount": 10000000,
            "turnover_rate": 1.5,
            "pre_close": 10.0
        }
        for i in range(5)
    ]
    
    saved_count = await storage_service.save_kline(
        code=code,
        klines=test_klines,
        adjust="qfq",
        sync_to_parquet=True
    )
    print(f"   保存了 {saved_count} 条数据")
    
    # 测试 3: 再次获取（应该从缓存或数据库命中）
    print("\n3. 测试缓存/数据库命中")
    klines = await storage_service.get_kline(
        code=code,
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
        use_cache=True
    )
    print(f"   获取 {code} 的 K 线数据：{len(klines) if klines else 0} 条")
    
    # 测试 4: 获取缓存统计
    print("\n4. 测试获取缓存统计")
    cache_stats = await storage_service.get_cache_stats()
    print(f"   缓存统计：{cache_stats}")
    
    # 测试 5: 获取存储统计
    print("\n5. 测试获取存储统计")
    storage_stats = await storage_service.get_storage_stats()
    print(f"   存储统计：{storage_stats}")
    
    print("\n=== storage_service 测试完成 ===\n")


async def test_cache_service_basic():
    """测试 cache_service 基本功能"""
    print("\n=== 测试 cache_service 基本功能 ===")
    
    # 测试 1: get_or_fetch 模式
    print("\n1. 测试 get_or_fetch 模式")
    
    async def fetch_data(key: str):
        print(f"   实际获取数据：{key}")
        return {"key": key, "value": "test_data", "timestamp": datetime.now().isoformat()}
    
    # 第一次调用（应该调用 fetch_func）
    result1 = await cache_service.get_or_fetch(
        key="test_key_1",
        fetch_func=lambda: fetch_data("test_key_1"),
        data_type="kline"
    )
    print(f"   第一次获取：{result1}")
    
    # 第二次调用（应该从缓存命中）
    result2 = await cache_service.get_or_fetch(
        key="test_key_1",
        fetch_func=lambda: fetch_data("test_key_1"),
        data_type="kline"
    )
    print(f"   第二次获取（缓存）：{result2}")
    
    # 测试 2: 手动 set/get
    print("\n2. 测试手动 set/get")
    await cache_service.set("manual_key", {"data": "test"}, data_type="kline")
    result = await cache_service.get("manual_key", data_type="kline")
    print(f"   手动获取：{result}")
    
    # 测试 3: 获取统计
    print("\n3. 测试获取缓存统计")
    stats = cache_service.get_stats()
    print(f"   缓存统计：{stats}")
    
    # 测试 4: 清除缓存
    print("\n4. 测试清除缓存")
    await cache_service.clear(data_type="kline")
    print("   已清除 kline 类型缓存")
    
    print("\n=== cache_service 测试完成 ===\n")


async def main():
    """主测试函数"""
    print("=" * 60)
    print("存储层重构测试")
    print("=" * 60)
    
    try:
        # 测试 cache_service
        await test_cache_service_basic()
        
        # 测试 storage_service
        await test_storage_service_basic()
        
        print("\n" + "=" * 60)
        print("所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
