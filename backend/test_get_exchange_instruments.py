"""
测试获取交易所标的列表功能

运行方式：
    python test_get_exchange_instruments_simple.py
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
from app.storage.unified_storage import storage_manager


async def test_get_instruments():
    """测试获取交易所标的列表"""
    print("=" * 60)
    print("获取交易所标的列表功能测试")
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
    
    # 2. 获取上海证券交易所标的列表
    print("\n[测试 2] 获取上海证券交易所 (SH) 标的列表")
    print("-" * 60)
    
    instruments_sh = await adapter.get_exchange_instruments("SH")
    if instruments_sh:
        print(f"✅ 获取到 {len(instruments_sh)} 个标的")
        
        # 显示前 5 个标的
        print(f"\n前 5 个标的:")
        for inst in instruments_sh[:5]:
            print(f"  {inst['symbol']}: {inst['name']} ({inst['type']})")
        
        # 显示扩展信息
        if instruments_sh[0].get('ext'):
            ext = instruments_sh[0]['ext']
            print(f"\n第一个标的的扩展信息:")
            if isinstance(ext, dict):
                for key, value in ext.items():
                    print(f"  {key}: {value}")
            else:
                print(f"  {ext}")
    else:
        print("❌ 获取失败或无数据")
    
    # 3. 获取深圳证券交易所标的列表
    print("\n[测试 3] 获取深圳证券交易所 (SZ) 标的列表")
    print("-" * 60)
    
    instruments_sz = await adapter.get_exchange_instruments("SZ")
    if instruments_sz:
        print(f"✅ 获取到 {len(instruments_sz)} 个标的")
        
        # 显示前 5 个标的
        print(f"\n前 5 个标的:")
        for inst in instruments_sz[:5]:
            print(f"  {inst['symbol']}: {inst['name']} ({inst['type']})")
    else:
        print("❌ 获取失败或无数据")
    
    # 4. 测试从缓存加载
    print("\n[测试 4] 测试从缓存加载")
    print("-" * 60)
    
    print("再次获取 SH 交易所标的列表（应从缓存加载）:")
    instruments_sh_cached = await adapter.get_exchange_instruments("SH")
    if instruments_sh_cached:
        print(f"✅ 从缓存加载到 {len(instruments_sh_cached)} 个标的")
        
        # 验证数据一致性
        if instruments_sh == instruments_sh_cached:
            print("✅ 数据一致性验证通过")
        else:
            print("⚠️  数据有变化")
    else:
        print("❌ 缓存加载失败")
    
    # 5. 测试强制刷新
    print("\n[测试 5] 测试强制刷新")
    print("-" * 60)
    
    print("强制刷新 SH 交易所标的列表:")
    instruments_sh_refresh = await adapter.get_exchange_instruments("SH", force_refresh=True)
    if instruments_sh_refresh:
        print(f"✅ 刷新后获取到 {len(instruments_sh_refresh)} 个标的")
    else:
        print("❌ 刷新失败")
    
    # 6. 获取期货交易所标的
    print("\n[测试 6] 获取上海期货交易所 (SHFE) 标的列表")
    print("-" * 60)
    
    instruments_shfe = await adapter.get_exchange_instruments("SHFE")
    if instruments_shfe:
        print(f"✅ 获取到 {len(instruments_shfe)} 个期货标的")
        
        # 显示所有标的
        print(f"\n标的列表:")
        for inst in instruments_shfe[:10]:  # 只显示前 10 个
            print(f"  {inst['symbol']}: {inst['name']}")
        
        if len(instruments_shfe) > 10:
            print(f"  ... 还有 {len(instruments_shfe) - 10} 个")
    else:
        print("❌ 获取失败或无数据")
    
    # 7. 统计数据
    print("\n[测试 7] 统计数据")
    print("-" * 60)
    
    total = 0
    if instruments_sh:
        total += len(instruments_sh)
    if instruments_sz:
        total += len(instruments_sz)
    if instruments_shfe:
        total += len(instruments_shfe)
    
    print(f"本次获取的总标的数：{total}")
    print(f"  - SH: {len(instruments_sh) if instruments_sh else 0}")
    print(f"  - SZ: {len(instruments_sz) if instruments_sz else 0}")
    print(f"  - SHFE: {len(instruments_shfe) if instruments_shfe else 0}")
    
    # 8. 检查存储文件
    print("\n[测试 8] 检查存储文件（新架构）")
    print("-" * 60)
    
    from pathlib import Path
    from app.config import settings
    import json
    
    data_dir = Path(settings.PARQUET_DIR)
    exchanges_file = data_dir / "exchanges.json"
    
    print(f"存储目录：{data_dir}")
    print(f"交易所数据文件：{exchanges_file}")
    
    if exchanges_file.exists():
        with open(exchanges_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"✅ 文件存在，包含 {len(data) if isinstance(data, list) else 'unknown'} 项")
        size = exchanges_file.stat().st_size
        print(f"   📄 exchanges.json ({size} 字节)")
    else:
        print("⚠️ 文件不存在（数据可能在缓存中）")
    
    # 关闭适配器
    await adapter.close()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_get_instruments())
