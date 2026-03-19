"""
测试交易所数据持久化功能（简化版，不依赖整个应用）

运行方式：
    python test_exchange_persistence_simple.py
"""
import asyncio
import sys
from pathlib import Path

# 只导入必要的模块，避免导入整个应用
sys.path.insert(0, str(Path(__file__).parent))

# 直接导入存储服务
from app.adapters.exchange_storage import ExchangeStorage


def test_storage_service():
    """测试存储服务"""
    print("=" * 60)
    print("交易所数据持久化服务测试（简化版）")
    print("=" * 60)
    
    # 1. 初始化存储服务
    print("\n[测试 1] 初始化存储服务")
    print("-" * 60)
    
    storage = ExchangeStorage()
    print(f"✅ 存储服务初始化成功")
    print(f"   存储目录：{storage.data_dir}")
    
    # 2. 创建测试数据
    print("\n[测试 2] 创建测试数据")
    print("-" * 60)
    
    test_exchanges = [
        {'exchange': 'SH', 'region': 'CN', 'count': 3332},
        {'exchange': 'SZ', 'region': 'CN', 'count': 3895},
        {'exchange': 'BJ', 'region': 'CN', 'count': 299},
        {'exchange': 'SHFE', 'region': 'CN', 'count': 20},
        {'exchange': 'DCE', 'region': 'CN', 'count': 26},
    ]
    
    # 3. 保存数据
    print("\n[测试 3] 保存测试数据")
    print("-" * 60)
    
    success = storage.save_exchanges(test_exchanges, source='test', expiry_days=7)
    if success:
        print("✅ 数据保存成功")
    else:
        print("❌ 数据保存失败")
        return
    
    # 4. 加载数据
    print("\n[测试 4] 加载数据")
    print("-" * 60)
    
    data = storage.load_exchanges()
    if data:
        exchanges = data.get('exchanges', [])
        metadata = data.get('metadata', {})
        print(f"✅ 数据加载成功")
        print(f"   来源：{metadata.get('source', 'unknown')}")
        print(f"   更新时间：{metadata.get('update_time', 'unknown')}")
        print(f"   交易所数量：{len(exchanges)}")
        
        # 验证数据一致性
        if exchanges == test_exchanges:
            print("✅ 数据一致性验证通过")
        else:
            print("⚠️  数据有差异")
    else:
        print("❌ 数据加载失败")
        return
    
    # 5. 检查元数据
    print("\n[测试 5] 检查元数据")
    print("-" * 60)
    
    metadata = storage.get_metadata()
    if metadata:
        print(f"✅ 元数据:")
        print(f"   来源：{metadata.get('source', 'unknown')}")
        print(f"   更新时间：{metadata.get('update_time', 'unknown')}")
        print(f"   过期时间：{metadata.get('expiry_time', 'unknown')}")
        print(f"   是否有效：{metadata.get('is_valid', False)}")
    else:
        print("❌ 元数据不存在")
    
    # 6. 检查数据有效性
    print("\n[测试 6] 检查数据有效性")
    print("-" * 60)
    
    is_valid = storage.is_data_valid()
    print(f"数据是否有效：{is_valid}")
    
    if is_valid:
        print("✅ 数据有效，可以正常使用")
    else:
        print("⚠️  数据已过期或无效")
    
    # 7. 获取统计数据
    print("\n[测试 7] 获取统计数据")
    print("-" * 60)
    
    stats = storage.get_statistics()
    if stats:
        print(f"✅ 统计数据:")
        print(f"   总交易所数：{stats.get('total_exchanges', 0)}")
        print(f"   总标的数：{stats.get('total_instruments', 0)}")
    else:
        print("❌ 统计数据获取失败")
    
    # 8. 导出 CSV
    print("\n[测试 8] 导出 CSV")
    print("-" * 60)
    
    csv_path = storage.export_to_csv()
    if csv_path:
        print(f"✅ CSV 文件已导出：{csv_path}")
        
        # 显示 CSV 内容
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            print(f"\nCSV 内容预览:\n{content}")
    else:
        print("❌ CSV 导出失败")
    
    # 9. 检查文件
    print("\n[测试 9] 检查存储文件")
    print("-" * 60)
    
    print(f"\n存储目录：{storage.data_dir}")
    print(f"文件列表:")
    for file in storage.data_dir.glob("**/*"):
        if file.is_file():
            size = file.stat().st_size
            rel_path = file.relative_to(storage.data_dir)
            print(f"   📄 {rel_path} ({size} 字节)")
    
    # 10. 测试强制刷新（清除缓存）
    print("\n[测试 10] 测试数据清除")
    print("-" * 60)
    
    clear_success = storage.clear()
    if clear_success:
        print("✅ 数据已清除")
    else:
        print("❌ 数据清除失败")
    
    # 验证清除
    is_valid_after_clear = storage.is_data_valid()
    print(f"清除后数据是否有效：{is_valid_after_clear}")
    
    if not is_valid_after_clear:
        print("✅ 数据清除验证成功")
    else:
        print("⚠️  数据可能未完全清除")
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    # 重新创建数据以便后续使用
    print("\n💾 重新创建测试数据...")
    storage.save_exchanges(test_exchanges, source='test', expiry_days=7)
    print(f"数据存储位置：{storage.data_dir}")


if __name__ == "__main__":
    test_storage_service()
