"""
TickFlow 简单测试脚本（不依赖应用）

直接测试 TickFlow SDK 功能

运行方式：
    python test_tickflow_simple.py
"""
import asyncio


async def test_tickflow_sdk():
    """直接测试 TickFlow SDK"""
    print("=" * 60)
    print("TickFlow SDK 测试")
    print("=" * 60)
    
    # 检查是否安装
    try:
        from tickflow import TickFlow
        print("✅ tickflow 库已安装")
    except ImportError:
        print("❌ tickflow 库未安装，请先运行：pip install 'tickflow[all]' --upgrade")
        return
    
    # 测试免费服务
    print("\n" + "-" * 60)
    print("测试 1：使用免费服务")
    print("-" * 60)
    
    try:
        tf = TickFlow.free()
        print("✅ TickFlow 免费服务初始化成功")
        
        # 测试获取标的信息
        print("\n获取标的信息...")
        instruments = tf.instruments.get(symbols=["600000.SH", "000001.SZ"])
        for inst in instruments:
            print(f"  ✅ {inst.symbol}: {inst.name} ({inst.exchange})")
        
        # 测试获取日 K 线数据
        print("\n获取日 K 线数据（600000.SH）...")
        df = tf.klines.get("600000.SH", period="1d", count=10, as_dataframe=True)
        print(f"✅ 获取 {len(df)} 条数据")
        print(df.tail())
        
    except Exception as e:
        print(f"❌ 免费服务测试失败：{e}")
        import traceback
        traceback.print_exc()
    
    # 测试完整服务（如果有 API Key）
    print("\n" + "-" * 60)
    print("测试 2：使用完整服务（需要 API Key）")
    print("-" * 60)
    
    api_key = "tk_4d7e268030a5449abbcc59b28f6e76b8"
    
    try:
        tf = TickFlow(api_key=api_key)
        print(f"✅ TickFlow 完整服务初始化成功（API Key: {api_key[:10]}...）")
        
        # 测试获取实时行情
        print("\n获取实时行情...")
        quotes = tf.quotes.get(symbols=["600000.SH", "000001.SZ"])
        for q in quotes:
            print(f"  ✅ {q['symbol']}: {q.get('name', '')} - 最新价：{q.get('last_price', 0):.2f}")
        
    except Exception as e:
        print(f"❌ 完整服务测试失败：{e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tickflow_sdk())
