"""
测试 TickFlow 交易所 API

运行方式：
    python test_tickflow_exchanges.py
"""
import asyncio
from tickflow import TickFlow


async def test_exchanges_api():
    """测试交易所 API"""
    print("=" * 60)
    print("TickFlow 交易所 API 测试")
    print("=" * 60)
    
    api_key = "tk_4d7e268030a5449abbcc59b28f6e76b8"
    
    try:
        # 初始化 TickFlow
        tf = TickFlow(api_key=api_key)
        print(f"✅ TickFlow 初始化成功")
        
        # 检查是否有 exchanges 属性
        if hasattr(tf, 'exchanges') and tf.exchanges is not None:
            print("✅ 发现 exchanges 模块")
            
            try:
                # 获取交易所列表（使用 list() 方法）
                if hasattr(tf.exchanges, 'list'):
                    exchanges = tf.exchanges.list()
                else:
                    exchanges = tf.exchanges.get()
                
                if exchanges:
                    print(f"\n✅ 获取到 {len(exchanges)} 个交易所：\n")
                    
                    for exc in exchanges:
                        # 支持字典和对象两种格式
                        if isinstance(exc, dict):
                            exchange_code = exc.get('exchange', 'N/A')
                            region = exc.get('region', 'N/A')
                            count = exc.get('count', 0)
                        else:
                            exchange_code = getattr(exc, 'exchange', getattr(exc, 'code', 'N/A'))
                            region = getattr(exc, 'region', getattr(exc, 'country', 'N/A'))
                            count = getattr(exc, 'count', 0)
                        
                        print(f"  交易所：{exchange_code}")
                        print(f"  地区：{region}")
                        print(f"  标的数量：{count}")
                        print("-" * 40)
                else:
                    print("⚠️  返回数据为空")
                    
            except Exception as e:
                print(f"❌ 获取交易所列表失败：{e}")
                import traceback
                traceback.print_exc()
        else:
            print("⚠️  TickFlow SDK 没有 exchanges 模块")
            print("   可用的模块：")
            for attr in dir(tf):
                if not attr.startswith('_'):
                    print(f"     - {attr}")
            
            # 尝试从 instruments 推断
            print("\n尝试从 instruments 推断交易所信息...")
            try:
                instruments = tf.instruments.get()
                if instruments:
                    exchange_stats = {}
                    for inst in instruments:
                        exc = getattr(inst, 'exchange', '')
                        if exc:
                            if exc not in exchange_stats:
                                exchange_stats[exc] = 0
                            exchange_stats[exc] += 1
                    
                    print(f"\n✅ 推断出 {len(exchange_stats)} 个交易所：\n")
                    for exc, count in exchange_stats.items():
                        region = 'CN' if exc in ['SH', 'SZ'] else 'UNKNOWN'
                        print(f"  交易所：{exc}")
                        print(f"  地区：{region}")
                        print(f"  样本数量：{count}")
                        print("-" * 40)
                else:
                    print("⚠️  instruments 返回数据为空")
            except Exception as e:
                print(f"❌ 获取 instruments 失败：{e}")
        
    except Exception as e:
        print(f"❌ 初始化失败：{e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_exchanges_api())
