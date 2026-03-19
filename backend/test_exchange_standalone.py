"""
测试交易所数据持久化功能（独立版）

完全独立，不依赖 app 包

运行方式：
    python test_exchange_standalone.py
"""
import sys
import asyncio
from pathlib import Path

# 直接添加路径，避免导入 app 包
sys.path.insert(0, str(Path(__file__).parent / "app" / "adapters"))

# 现在导入存储服务（不会触发 app 导入）
from exchange_storage import ExchangeStorage


def test_storage():
    """测试存储服务"""
    print("=" * 60)
    print("交易所数据持久化服务测试（独立版）")
    print("=" * 60)
    
    # 1. 初始化
    print("\n[测试 1] 初始化存储服务")
    storage = ExchangeStorage()
    print(f"✅ 存储服务初始化成功")
    print(f"   存储目录：{storage.data_dir}")
    
    # 2. 创建测试数据
    print("\n[测试 2] 创建测试数据")
    test_exchanges = [
        {'exchange': 'SH', 'region': 'CN', 'count': 3332},
        {'exchange': 'SZ', 'region': 'CN', 'count': 3895},
        {'exchange': 'BJ', 'region': 'CN', 'count': 299},
        {'exchange': 'SHFE', 'region': 'CN', 'count': 20},
        {'exchange': 'DCE', 'region': 'CN', 'count': 26},
        {'exchange': 'CZCE', 'region': 'CN', 'count': 26},
        {'exchange': 'CFFEX', 'region': 'CN', 'count': 8},
        {'exchange': 'INE', 'region': 'CN', 'count': 5},
        {'exchange': 'GFEX', 'region': 'CN', 'count': 5},
    ]
    print(f"创建 {len(test_exchanges)} 个测试交易所数据")
    
    # 3. 保存数据
    print("\n[测试 3] 保存数据")
    success = storage.save_exchanges(test_exchanges, source='test', expiry_days=7)
    if success:
        print("✅ 数据保存成功")
    else:
        print("❌ 数据保存失败")
        return
    
    # 4. 加载数据
    print("\n[测试 4] 加载数据（从持久化）")
    data = storage.load_exchanges()
    if data:
        exchanges = data.get('exchanges', [])
        metadata = data.get('metadata', {})
        print(f"✅ 数据加载成功")
        print(f"   来源：{metadata.get('source', 'unknown')}")
        print(f"   更新时间：{metadata.get('update_time', 'unknown')}")
        print(f"   交易所数量：{len(exchanges)}")
        print(f"   总标的数：{metadata.get('total_instruments', 0)}")
    else:
        print("❌ 数据加载失败")
        return
    
    # 5. 检查元数据
    print("\n[测试 5] 检查元数据")
    metadata = storage.get_metadata()
    if metadata:
        print(f"✅ 元数据:")
        print(f"   来源：{metadata.get('source', 'unknown')}")
        print(f"   更新时间：{metadata.get('update_time', 'unknown')}")
        print(f"   过期时间：{metadata.get('expiry_time', 'unknown')}")
        print(f"   是否有效：{metadata.get('is_valid', False)}")
    else:
        print("❌ 元数据不存在")
    
    # 6. 数据有效性检查
    print("\n[测试 6] 数据有效性检查")
    is_valid = storage.is_data_valid()
    print(f"数据是否有效：{is_valid}")
    
    # 7. 获取统计数据
    print("\n[测试 7] 获取统计数据")
    stats = storage.get_statistics()
    if stats:
        print(f"✅ 统计数据:")
        print(f"   总交易所数：{stats.get('total_exchanges', 0)}")
        print(f"   总标的数：{stats.get('total_instruments', 0)}")
        if 'stock_exchanges' in stats:
            print(f"   股票交易所：{stats['stock_exchanges'].get('count', 0)} 个")
            print(f"   期货交易所：{stats['futures_exchanges'].get('count', 0)} 个")
    else:
        print("❌ 统计数据获取失败")
    
    # 8. 导出 CSV
    print("\n[测试 8] 导出 CSV")
    csv_path = storage.export_to_csv()
    if csv_path:
        print(f"✅ CSV 文件已导出：{csv_path}")
        print(f"\nCSV 内容预览:")
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            lines = f.readlines()
            for line in lines[:15]:  # 显示前 15 行
                print(f"  {line.strip()}")
    else:
        print("❌ CSV 导出失败")
    
    # 9. 检查文件
    print("\n[测试 9] 检查存储文件")
    print(f"\n存储目录：{storage.data_dir}")
    files = list(storage.data_dir.glob("**/*"))
    print(f"文件数量：{len([f for f in files if f.is_file()])}")
    for file in files:
        if file.is_file():
            size = file.stat().st_size
            rel_path = file.relative_to(storage.data_dir)
            print(f"   📄 {rel_path} ({size} 字节)")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成！")
    print("=" * 60)
    print(f"\n💾 数据存储位置：{storage.data_dir}")


if __name__ == "__main__":
    test_storage()
