"""
测试交易所数据存储功能（新架构）

验证使用 storage_manager 统一管理交易所数据

运行方式：
    python test_exchange_storage_new.py
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.storage.unified_storage import storage_manager, DataCategory


async def test_exchange_storage():
    """测试交易所数据存储"""
    print("=" * 60)
    print("交易所数据存储功能测试（新架构）")
    print("=" * 60)
    
    # 1. 获取交易所存储器
    print("\n[测试 1] 获取交易所存储器")
    print("-" * 60)
    
    exchange_storage = storage_manager.get_exchange_storage()
    print(f"✅ 存储器初始化成功")
    print(f"   分类：{exchange_storage.category.value}")
    print(f"   缓存 TTL: {exchange_storage._cache.ttl} 秒")
    
    # 2. 测试保存数据
    print("\n[测试 2] 保存交易所数据")
    print("-" * 60)
    
    test_data = [
        {
            'exchange': 'SH',
            'region': 'CN',
            'count': 2000,
            'name': '上海证券交易所'
        },
        {
            'exchange': 'SZ',
            'region': 'CN',
            'count': 2500,
            'name': '深圳证券交易所'
        },
        {
            'exchange': 'HKEX',
            'region': 'HK',
            'count': 2500,
            'name': '香港交易所'
        }
    ]
    
    success = await exchange_storage.set("exchanges", test_data)
    print(f"✅ 数据保存成功：{success}")
    
    # 3. 测试读取数据（从缓存）
    print("\n[测试 3] 读取数据（缓存命中）")
    print("-" * 60)
    
    data = await exchange_storage.get("exchanges")
    if data:
        print(f"✅ 从缓存读取成功：{len(data)}项")
        for item in data:
            print(f"   - {item['exchange']}: {item['name']} ({item['count']}项)")
    else:
        print("❌ 读取失败")
    
    # 4. 测试 JSON 文件持久化
    print("\n[测试 4] 检查 JSON 文件持久化")
    print("-" * 60)
    
    from app.config import settings
    import json
    
    data_dir = Path(settings.PARQUET_DIR)
    exchanges_file = data_dir / "exchanges.json"
    
    if exchanges_file.exists():
        with open(exchanges_file, 'r', encoding='utf-8') as f:
            file_data = json.load(f)
        print(f"✅ JSON 文件存在")
        print(f"   文件路径：{exchanges_file}")
        print(f"   文件大小：{exchanges_file.stat().st_size} 字节")
        print(f"   数据项数：{len(file_data) if isinstance(file_data, list) else 'unknown'}")
    else:
        print("⚠️ JSON 文件不存在（可能未写入）")
    
    # 5. 测试缓存统计
    print("\n[测试 5] 缓存统计信息")
    print("-" * 60)
    
    stats = exchange_storage.get_stats()
    print(f"L1 缓存命中：{stats.get('l1_hits', 0)}")
    print(f"L2 数据库命中：{stats.get('l2_hits', 0)}")
    print(f"L3 Parquet 命中：{stats.get('l3_hits', 0)}")
    print(f"缓存命中率：{stats.get('hit_rate', 'N/A')}")
    
    # 6. 测试强制刷新
    print("\n[测试 6] 测试缓存统计")
    print("-" * 60)
    
    # 再次读取（统计命中）
    data = await exchange_storage.get("exchanges")
    if data:
        print(f"✅ 再次读取成功：{len(data)}项")
        
        # 获取最新统计
        stats = exchange_storage.get_stats()
        print(f"L1 缓存命中：{stats.get('l1_hits', 0)}")
        print(f"L2 数据库命中：{stats.get('l2_hits', 0)}")
        print(f"缓存命中率：{stats.get('hit_rate', 'N/A')}")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_exchange_storage())
