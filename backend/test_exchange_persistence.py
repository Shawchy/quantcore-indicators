"""
测试交易所数据持久化功能

运行方式：
    python test_exchange_persistence.py
"""
import asyncio
import os
from pathlib import Path
from app.adapters.exchange_storage import ExchangeStorage
from app.adapters.tickflow_adapter import TickFlowAdapter


async def test_persistence():
    """测试持久化功能"""
    print("=" * 60)
    print("交易所数据持久化功能测试")
    print("=" * 60)
    
    # 1. 测试存储服务
    print("\n[测试 1] 测试 ExchangeStorage 服务")
    print("-" * 60)
    
    storage = ExchangeStorage()
    print(f"✅ 存储服务初始化成功")
    print(f"   存储目录：{storage.data_dir}")
    
    # 2. 测试从 TickFlow 获取并保存数据
    print("\n[测试 2] 从 TickFlow 获取并保存数据")
    print("-" * 60)
    
    config = {}
    adapter = TickFlowAdapter(config)
    await adapter.initialize()
    
    # 第一次获取（会从 API 获取并保存）
    print("\n第一次获取（从 API）:")
    exchanges1 = await adapter.get_exchanges()
    print(f"获取到 {len(exchanges1)} 个交易所")
    
    # 3. 测试从持久化加载
    print("\n[测试 3] 从持久化存储加载数据")
    print("-" * 60)
    
    # 第二次获取（应该从持久化加载）
    print("\n第二次获取（从持久化）:")
    exchanges2 = await adapter.get_exchanges()
    print(f"获取到 {len(exchanges2)} 个交易所")
    
    # 验证数据一致性
    if exchanges1 == exchanges2:
        print("✅ 数据一致性验证通过")
    else:
        print("❌ 数据不一致")
    
    # 4. 测试强制刷新
    print("\n[测试 4] 测试强制刷新")
    print("-" * 60)
    
    print("\n强制刷新（重新从 API 获取）:")
    exchanges3 = await adapter.get_exchanges(force_refresh=True)
    print(f"获取到 {len(exchanges3)} 个交易所")
    
    # 5. 测试元数据
    print("\n[测试 5] 测试元数据")
    print("-" * 60)
    
    metadata = storage.get_metadata()
    if metadata:
        print(f"✅ 元数据:")
        print(f"   来源：{metadata.get('source', 'unknown')}")
        print(f"   更新时间：{metadata.get('update_time', 'unknown')}")
        print(f"   过期时间：{metadata.get('expiry_time', 'unknown')}")
        print(f"   交易所数量：{metadata.get('count', 0)}")
        print(f"   是否有效：{metadata.get('is_valid', False)}")
    else:
        print("❌ 元数据不存在")
    
    # 6. 测试统计数据
    print("\n[测试 6] 测试统计数据")
    print("-" * 60)
    
    stats = storage.get_statistics()
    if stats:
        print(f"✅ 统计数据:")
        print(f"   总交易所数：{stats.get('total_exchanges', 0)}")
        print(f"   总标的数：{stats.get('total_instruments', 0)}")
        print(f"   股票交易所：{stats.get('stock_exchanges', {}).get('count', 0)} 个，{stats.get('stock_exchanges', {}).get('instruments', 0)} 个标的")
        print(f"   期货交易所：{stats.get('futures_exchanges', {}).get('count', 0)} 个，{stats.get('futures_exchanges', {}).get('instruments', 0)} 个标的")
    else:
        print("❌ 统计数据不存在")
    
    # 7. 测试导出 CSV
    print("\n[测试 7] 测试导出 CSV")
    print("-" * 60)
    
    csv_path = storage.export_to_csv()
    if csv_path:
        print(f"✅ CSV 文件已导出：{csv_path}")
        # 显示文件内容
        with open(csv_path, 'r', encoding='utf-8-sig') as f:
            content = f.read()
            print(f"\nCSV 内容预览:\n{content[:500]}")
    else:
        print("❌ CSV 导出失败")
    
    # 8. 检查存储的文件
    print("\n[测试 8] 检查存储的文件")
    print("-" * 60)
    
    print(f"\n存储目录：{storage.data_dir}")
    print(f"文件列表:")
    for file in storage.data_dir.glob("**/*"):
        if file.is_file():
            size = file.stat().st_size
            print(f"   📄 {file.relative_to(storage.data_dir)} ({size} 字节)")
    
    # 9. 测试数据验证
    print("\n[测试 9] 测试数据验证")
    print("-" * 60)
    
    is_valid = storage.is_data_valid()
    print(f"数据是否有效：{is_valid}")
    
    if is_valid:
        print("✅ 数据有效，可以正常使用")
    else:
        print("⚠️  数据已过期或无效，需要重新获取")
    
    # 关闭适配器
    await adapter.close()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    
    # 显示存储目录路径
    print(f"\n💾 数据存储位置：{storage.data_dir}")
    print(f"   如需清除数据，请删除该目录下的文件")


if __name__ == "__main__":
    asyncio.run(test_persistence())
