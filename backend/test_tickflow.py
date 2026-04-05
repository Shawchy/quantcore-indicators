"""
TickFlow API 连接测试脚本
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.adapters.tickflow_adapter import TickFlowAdapter


async def test_tickflow():
    """测试 TickFlow 连接"""
    print("=" * 60)
    print("TickFlow API 连接测试")
    print("=" * 60)
    
    # 1. 检查配置
    print("\n1. 配置检查:")
    print(f"   TICKFLOW_API_KEY: {'已配置' if settings.TICKFLOW_API_KEY else '未配置'}")
    if settings.TICKFLOW_API_KEY:
        # 显示部分 API Key（安全考虑）
        key = settings.TICKFLOW_API_KEY
        print(f"   API Key: {key[:10]}...{key[-8:]}")
    
    # 2. 初始化适配器
    print("\n2. 初始化 TickFlow 适配器:")
    adapter = TickFlowAdapter()
    
    try:
        success = await adapter.initialize()
        if success:
            print("   ✓ TickFlow 初始化成功")
            print(f"   使用服务类型: {'完整服务' if not adapter.is_free_service else '免费服务'}")
        else:
            print("   ✗ TickFlow 初始化失败")
            return
    except Exception as e:
        print(f"   ✗ 初始化异常: {e}")
        return
    
    # 3. 测试获取股票信息
    print("\n3. 测试获取股票信息 (600000 浦发银行):")
    try:
        stock_info = await adapter.get_stock_info("600000")
        if stock_info:
            print(f"   ✓ 成功获取股票信息")
            print(f"   代码: {stock_info.code}")
            print(f"   名称: {stock_info.name}")
            print(f"   市场: {stock_info.market}")
        else:
            print("   ✗ 未获取到股票信息")
    except Exception as e:
        print(f"   ✗ 获取股票信息失败: {e}")
    
    # 4. 测试获取 K 线数据
    print("\n4. 测试获取 K 线数据 (600000 近5日):")
    try:
        kline_data = await adapter.get_kline(
            code="600000",
            start_date="2025-03-01",
            end_date="2025-03-05",
            period="daily"
        )
        if kline_data:
            print(f"   ✓ 成功获取 K 线数据")
            print(f"   数据条数: {len(kline_data)}")
            if len(kline_data) > 0:
                first = kline_data[0]
                print(f"   最新数据: {first.date} 收盘: {first.close}")
        else:
            print("   ✗ 未获取到 K 线数据")
    except Exception as e:
        print(f"   ✗ 获取 K 线数据失败: {e}")
    
    # 5. 关闭连接
    print("\n5. 关闭连接:")
    await adapter.close()
    print("   ✓ TickFlow 连接已关闭")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(test_tickflow())
