"""
测试标的元数据查询功能

运行方式：
    python test_instrument_metadata.py
"""
import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

# 设置环境变量避免导入整个 app
import os
os.environ['QUANT_SKIP_APP_INIT'] = '1'

from app.adapters.tickflow_adapter import TickFlowAdapter


async def test_instrument_metadata():
    """测试标的元数据查询功能"""
    print("=" * 60)
    print("标的元数据查询功能测试")
    print("=" * 60)
    
    # 1. 初始化 TickFlow 适配器
    print("\n[测试 1] 初始化 TickFlow 适配器")
    print("-" * 60)
    
    config = {}
    adapter = TickFlowAdapter(config)
    success = await adapter.initialize()
    
    if success:
        print(f"✅ TickFlow 初始化成功")
        print(f"   使用免费服务：{adapter.is_free_service}")
    else:
        print("❌ TickFlow 初始化失败")
        return
    
    # 2. 查询单个标的元数据
    print("\n[测试 2] 查询单个标的元数据")
    print("-" * 60)
    
    symbol = "600177.SH"
    print(f"查询标的：{symbol}")
    
    info = await adapter.get_instrument_info(symbol)
    if info:
        print(f"✅ 查询成功")
        print(f"  代码：{info['code']}")
        print(f"  名称：{info['name']}")
        print(f"  交易所：{info['exchange']}")
        print(f"  类型：{info['type']}")
        print(f"  扩展信息:")
        ext = info.get('ext', {})
        if ext:
            if isinstance(ext, dict):
                for key, value in ext.items():
                    print(f"    {key}: {value}")
            else:
                print(f"    {ext}")
    else:
        print("❌ 查询失败")
    
    # 3. 批量查询标的元数据
    print("\n[测试 3] 批量查询标的元数据")
    print("-" * 60)
    
    symbols = [
        "600177.SH",  # 雅戈尔
        "000001.SZ",  # 平安银行
        "300750.SZ",  # 宁德时代
        "600519.SH",  # 贵州茅台
    ]
    
    print(f"批量查询 {len(symbols)} 个标的:")
    for s in symbols:
        print(f"  - {s}")
    
    batch_info = await adapter.get_instruments_batch(symbols)
    if batch_info:
        print(f"\n✅ 批量查询成功，获取到 {len(batch_info)} 个标的信息")
        
        # 显示详细信息
        for inst in batch_info:
            print(f"\n  {inst['symbol']}: {inst['name']} ({inst['type']})")
            print(f"    交易所：{inst['exchange']}")
            if inst.get('ext'):
                ext = inst['ext']
                if isinstance(ext, dict):
                    if 'listing_date' in ext:
                        print(f"    上市日期：{ext['listing_date']}")
                    if 'total_shares' in ext:
                        print(f"    总股本：{ext['total_shares']}")
    else:
        print("❌ 批量查询失败")
    
    # 4. 测试缓存功能
    print("\n[测试 4] 测试缓存功能")
    print("-" * 60)
    
    print("再次查询单个标的（应从缓存加载）:")
    info_cached = await adapter.get_instrument_info(symbol)
    if info_cached:
        print(f"✅ 从缓存获取成功")
        
        # 验证数据一致性
        if info == info_cached:
            print("✅ 数据一致性验证通过")
        else:
            print("⚠️  数据有变化")
    else:
        print("❌ 缓存加载失败")
    
    print("\n批量查询（测试缓存）:")
    batch_cached = await adapter.get_instruments_batch(symbols)
    if batch_cached:
        print(f"✅ 从缓存获取 {len(batch_cached)} 个标的信息")
    else:
        print("❌ 缓存加载失败")
    
    # 5. 测试强制刷新
    print("\n[测试 5] 测试强制刷新")
    print("-" * 60)
    
    print("强制刷新单个标的:")
    info_refresh = await adapter.get_instrument_info(symbol, force_refresh=True)
    if info_refresh:
        print(f"✅ 刷新成功")
    else:
        print("❌ 刷新失败")
    
    # 6. 查询不存在的标的
    print("\n[测试 6] 查询不存在的标的")
    print("-" * 60)
    
    invalid_symbol = "000000.SH"
    print(f"查询标的：{invalid_symbol}")
    
    invalid_info = await adapter.get_instrument_info(invalid_symbol)
    if invalid_info:
        print(f"⚠️  获取到数据（可能是有效标的）")
    else:
        print("✅ 正确返回 None（标的不存在）")
    
    # 7. 统计数据
    print("\n[测试 7] 统计数据")
    print("-" * 60)
    
    total = 0
    if info:
        total += 1
    if batch_info:
        total += len(batch_info)
    
    print(f"本次测试获取的总标的数：{total}")
    
    # 关闭适配器
    await adapter.close()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_instrument_metadata())
