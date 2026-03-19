"""
测试 TickFlow SDK 的标的元数据 API

直接测试 SDK，不依赖适配器

运行方式：
    python test_tickflow_metadata_api.py
"""
import asyncio
from tickflow import TickFlow


async def test_metadata_api():
    """测试标的元数据 API"""
    print("=" * 60)
    print("TickFlow SDK 标的元数据 API 测试")
    print("=" * 60)
    
    api_key = "tk_4d7e268030a5449abbcc59b28f6e76b8"
    
    try:
        # 初始化 TickFlow
        tf = TickFlow(api_key=api_key)
        print(f"✅ TickFlow 初始化成功")
        
        # 检查 instruments 模块
        if not hasattr(tf, 'instruments') or tf.instruments is None:
            print("❌ TickFlow 没有 instruments 模块")
            return
        
        print(f"✅ 发现 instruments 模块")
        print(f"   可用方法：{[m for m in dir(tf.instruments) if not m.startswith('_')]}")
        
        # 测试 1：查询单个标的
        print("\n[测试 1] 查询单个标的元数据")
        print("-" * 60)
        
        symbol = "600177.SH"
        print(f"查询标的：{symbol}")
        
        try:
            instruments = tf.instruments.get(symbols=[symbol])
            
            if instruments and len(instruments) > 0:
                inst = instruments[0]
                print(f"✅ 查询成功")
                
                # 显示信息
                if isinstance(inst, dict):
                    print(f"  代码：{inst.get('code', 'N/A')}")
                    print(f"  名称：{inst.get('name', 'N/A')}")
                    print(f"  交易所：{inst.get('exchange', 'N/A')}")
                    print(f"  类型：{inst.get('type', 'N/A')}")
                    
                    ext = inst.get('ext', {})
                    if ext:
                        print(f"  扩展信息:")
                        for key, value in ext.items():
                            print(f"    {key}: {value}")
                else:
                    print(f"  代码：{getattr(inst, 'code', 'N/A')}")
                    print(f"  名称：{getattr(inst, 'name', 'N/A')}")
                    print(f"  交易所：{getattr(inst, 'exchange', 'N/A')}")
                    print(f"  类型：{getattr(inst, 'type', 'N/A')}")
            else:
                print("⚠️  返回数据为空")
                
        except Exception as e:
            print(f"❌ 查询失败：{e}")
            import traceback
            traceback.print_exc()
        
        # 测试 2：批量查询标的
        print("\n[测试 2] 批量查询标的元数据")
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
        
        try:
            # 使用 batch 方法
            if hasattr(tf.instruments, 'batch'):
                instruments = tf.instruments.batch(symbols=symbols)
            else:
                # 使用 get 方法
                instruments = tf.instruments.get(symbols=symbols)
            
            if instruments:
                print(f"\n✅ 批量查询成功，获取到 {len(instruments)} 个标的信息")
                
                # 显示详细信息
                for inst in instruments:
                    if isinstance(inst, dict):
                        print(f"\n  {inst.get('symbol', 'N/A')}: {inst.get('name', 'N/A')} ({inst.get('type', 'N/A')})")
                        print(f"    交易所：{inst.get('exchange', 'N/A')}")
                        ext = inst.get('ext', {})
                        if ext and isinstance(ext, dict):
                            if 'listing_date' in ext:
                                print(f"    上市日期：{ext['listing_date']}")
                            if 'total_shares' in ext:
                                print(f"    总股本：{ext['total_shares']}")
                    else:
                        print(f"\n  {getattr(inst, 'symbol', 'N/A')}: {getattr(inst, 'name', 'N/A')}")
            else:
                print("⚠️  返回数据为空")
                
        except Exception as e:
            print(f"❌ 批量查询失败：{e}")
            import traceback
            traceback.print_exc()
        
        # 测试 3：查询不存在的标的
        print("\n[测试 3] 查询不存在的标的")
        print("-" * 60)
        
        invalid_symbol = "000000.SH"
        print(f"查询标的：{invalid_symbol}")
        
        try:
            instruments = tf.instruments.get(symbols=[invalid_symbol])
            if instruments and len(instruments) > 0:
                print(f"⚠️  获取到数据（可能是有效标的）")
            else:
                print("✅ 正确返回空数据（标的不存在）")
        except Exception as e:
            print(f"✅ 查询异常（标的不存在）：{e}")
        
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_metadata_api())
