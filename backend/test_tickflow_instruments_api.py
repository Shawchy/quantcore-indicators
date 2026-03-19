"""
测试 TickFlow SDK 的交易所标的列表 API

直接测试 SDK，不依赖适配器

运行方式：
    python test_tickflow_instruments_api.py
"""
import asyncio
from tickflow import TickFlow


async def test_instruments_api():
    """测试获取交易所标的列表"""
    print("=" * 60)
    print("TickFlow SDK 交易所标的列表 API 测试")
    print("=" * 60)
    
    api_key = "tk_4d7e268030a5449abbcc59b28f6e76b8"
    
    try:
        # 初始化 TickFlow
        tf = TickFlow(api_key=api_key)
        print(f"✅ TickFlow 初始化成功")
        
        # 检查 exchanges 模块
        if not hasattr(tf, 'exchanges') or tf.exchanges is None:
            print("❌ TickFlow 没有 exchanges 模块")
            return
        
        print(f"✅ 发现 exchanges 模块")
        
        # 检查是否有 get_instruments 方法
        if not hasattr(tf.exchanges, 'get_instruments'):
            print("❌ exchanges 对象没有 get_instruments() 方法")
            print(f"   可用的方法：{[m for m in dir(tf.exchanges) if not m.startswith('_')]}")
            return
        
        print(f"✅ 发现 get_instruments() 方法")
        
        # 测试获取上海证券交易所标的
        print("\n[测试 1] 获取上海证券交易所 (SH) 标的列表")
        print("-" * 60)
        
        try:
            instruments_sh = tf.exchanges.get_instruments("SH")
            
            if instruments_sh:
                print(f"✅ 获取到 {len(instruments_sh)} 个标的")
                
                # 显示前 5 个
                print(f"\n前 5 个标的:")
                for i, inst in enumerate(instruments_sh[:5], 1):
                    if isinstance(inst, dict):
                        print(f"  {i}. {inst.get('symbol', 'N/A')}: {inst.get('name', 'N/A')} ({inst.get('type', 'N/A')})")
                    else:
                        print(f"  {i}. {getattr(inst, 'symbol', 'N/A')}: {getattr(inst, 'name', 'N/A')} ({getattr(inst, 'type', 'N/A')})")
                
                # 显示第一个标的的详细信息
                if instruments_sh:
                    first = instruments_sh[0]
                    print(f"\n第一个标的的详细信息:")
                    if isinstance(first, dict):
                        for key, value in first.items():
                            print(f"  {key}: {value}")
                    else:
                        print(f"  类型：{type(first)}")
                        if hasattr(first, '__dict__'):
                            for key, value in vars(first).items():
                                print(f"  {key}: {value}")
            else:
                print("⚠️  返回数据为空")
                
        except Exception as e:
            print(f"❌ 获取 SH 标的失败：{e}")
            import traceback
            traceback.print_exc()
        
        # 测试获取深圳证券交易所标的
        print("\n[测试 2] 获取深圳证券交易所 (SZ) 标的列表")
        print("-" * 60)
        
        try:
            instruments_sz = tf.exchanges.get_instruments("SZ")
            
            if instruments_sz:
                print(f"✅ 获取到 {len(instruments_sz)} 个标的")
                
                # 显示前 3 个
                print(f"\n前 3 个标的:")
                for inst in instruments_sz[:3]:
                    if isinstance(inst, dict):
                        print(f"  {inst.get('symbol', 'N/A')}: {inst.get('name', 'N/A')}")
                    else:
                        print(f"  {getattr(inst, 'symbol', 'N/A')}: {getattr(inst, 'name', 'N/A')}")
            else:
                print("⚠️  返回数据为空")
                
        except Exception as e:
            print(f"❌ 获取 SZ 标的失败：{e}")
        
        # 测试获取期货交易所标的
        print("\n[测试 3] 获取上海期货交易所 (SHFE) 标的列表")
        print("-" * 60)
        
        try:
            instruments_shfe = tf.exchanges.get_instruments("SHFE")
            
            if instruments_shfe:
                print(f"✅ 获取到 {len(instruments_shfe)} 个期货标的")
                
                # 显示所有（期货标的一般较少）
                print(f"\n标的列表:")
                for inst in instruments_shfe[:10]:
                    if isinstance(inst, dict):
                        print(f"  {inst.get('symbol', 'N/A')}: {inst.get('name', 'N/A')}")
                    else:
                        print(f"  {getattr(inst, 'symbol', 'N/A')}: {getattr(inst, 'name', 'N/A')}")
                
                if len(instruments_shfe) > 10:
                    print(f"  ... 还有 {len(instruments_shfe) - 10} 个")
            else:
                print("⚠️  返回数据为空")
                
        except Exception as e:
            print(f"❌ 获取 SHFE 标的失败：{e}")
        
        # 统计
        print("\n[测试 4] 统计")
        print("-" * 60)
        
        total = 0
        if 'instruments_sh' in locals() and instruments_sh:
            total += len(instruments_sh)
        if 'instruments_sz' in locals() and instruments_sz:
            total += len(instruments_sz)
        if 'instruments_shfe' in locals() and instruments_shfe:
            total += len(instruments_shfe)
        
        print(f"本次测试获取的总标的数：{total}")
        
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_instruments_api())
