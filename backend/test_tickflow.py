"""
TickFlow 数据源测试脚本

测试 TickFlow 数据源的各项功能

运行方式：
    python test_tickflow.py
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from app.adapters.tickflow_adapter import TickFlowAdapter, TICKFLOW_AVAILABLE
from app.adapters.factory import DataSourceFactory, DataSourceManager
from app.config import settings


async def test_tickflow_adapter():
    """测试 TickFlow 适配器"""
    print("=" * 60)
    print("TickFlow 数据源测试")
    print("=" * 60)
    
    # 检查是否安装
    if not TICKFLOW_AVAILABLE:
        print("❌ tickflow 库未安装，请先运行：pip install 'tickflow[all]' --upgrade")
        return
    
    print("✅ tickflow 库已安装")
    
    # 创建适配器
    config = {}
    if hasattr(settings, 'TICKFLOW_API_KEY') and settings.TICKFLOW_API_KEY:
        config['api_key'] = settings.TICKFLOW_API_KEY
        print(f"✅ 使用 API Key: {settings.TICKFLOW_API_KEY[:10]}...")
    else:
        print("⚠️  未配置 API Key，将使用免费服务")
    
    adapter = TickFlowAdapter(config)
    
    # 初始化
    print("\n初始化 TickFlow...")
    success = await adapter.initialize()
    if not success:
        print("❌ TickFlow 初始化失败")
        return
    
    print(f"✅ TickFlow 初始化成功（免费服务：{adapter.is_free_service}）")
    
    # 测试 1：获取股票信息
    print("\n" + "-" * 60)
    print("测试 1：获取股票信息")
    print("-" * 60)
    
    test_codes = ["600000", "000001", "300750"]
    for code in test_codes:
        try:
            info = await adapter.get_stock_info(code)
            if info:
                print(f"✅ {code}: {info.name} ({info.market})")
            else:
                print(f"❌ {code}: 未找到信息")
        except Exception as e:
            print(f"❌ {code}: 获取失败 - {e}")
    
    # 测试 2：获取日 K 线数据
    print("\n" + "-" * 60)
    print("测试 2：获取日 K 线数据")
    print("-" * 60)
    
    for code in ["600000"]:
        try:
            klines = await adapter.get_kline(code, period='daily')
            if klines:
                print(f"✅ {code}: 获取 {len(klines)} 条日 K 线数据")
                # 显示最近 5 条
                for kline in klines[-5:]:
                    print(f"   {kline.date}: 开={kline.open:.2f} 收={kline.close:.2f} 高={kline.high:.2f} 低={kline.low:.2f}")
            else:
                print(f"❌ {code}: K 线数据为空")
        except Exception as e:
            print(f"❌ {code}: 获取 K 线失败 - {e}")
    
    # 测试 3：获取周 K 线数据
    print("\n" + "-" * 60)
    print("测试 3：获取周 K 线数据")
    print("-" * 60)
    
    for code in ["600000"]:
        try:
            klines = await adapter.get_weekly_kline(code)
            if klines:
                print(f"✅ {code}: 获取 {len(klines)} 条周 K 线数据")
                # 显示最近 3 条
                for kline in klines[-3:]:
                    print(f"   {kline.date}: 开={kline.open:.2f} 收={kline.close:.2f}")
            else:
                print(f"❌ {code}: 周 K 线数据为空")
        except Exception as e:
            print(f"❌ {code}: 获取周 K 线失败 - {e}")
    
    # 测试 4：获取实时行情（仅完整服务）
    print("\n" + "-" * 60)
    print("测试 4：获取实时行情")
    print("-" * 60)
    
    if adapter.is_free_service:
        print("⚠️  免费服务不支持实时行情，跳过此测试")
    else:
        for code in ["600000", "000001"]:
            try:
                quote = await adapter.get_realtime_quote(code)
                if quote:
                    print(f"✅ {code}: {quote.get('name', '')} - 最新价：{quote.get('price', 0):.2f}")
                else:
                    print(f"❌ {code}: 实时行情为空")
            except Exception as e:
                print(f"❌ {code}: 获取实时行情失败 - {e}")
    
    # 测试 5：分钟级 K 线（仅完整服务）
    print("\n" + "-" * 60)
    print("测试 5：获取分钟级 K 线（5 分钟）")
    print("-" * 60)
    
    if adapter.is_free_service:
        print("⚠️  免费服务不支持分钟级 K 线，跳过此测试")
    else:
        for code in ["600000"]:
            try:
                klines = await adapter.get_kline(code, period='5m')
                if klines:
                    print(f"✅ {code}: 获取 {len(klines)} 条 5 分钟 K 线数据")
                else:
                    print(f"❌ {code}: 分钟 K 线数据为空")
            except Exception as e:
                print(f"❌ {code}: 获取分钟 K 线失败 - {e}")
    
    # 关闭
    await adapter.close()
    
    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)


async def test_data_source_manager():
    """测试通过 DataSourceManager 调用 TickFlow"""
    print("\n" + "=" * 60)
    print("通过 DataSourceManager 测试 TickFlow")
    print("=" * 60)
    
    # 初始化数据源管理器
    manager = DataSourceManager()
    await manager.initialize()
    
    # 获取 TickFlow 适配器
    try:
        adapter = manager.get_adapter("tickflow")
        print(f"✅ 成功获取 TickFlow 适配器")
        
        # 测试获取股票信息
        info = await adapter.get_stock_info("600000")
        if info:
            print(f"✅ 通过 manager 获取股票信息：{info.name}")
        else:
            print("❌ 通过 manager 获取股票信息失败")
        
        # 测试获取 K 线
        klines = await adapter.get_kline("600000", period='daily')
        if klines:
            print(f"✅ 通过 manager 获取 K 线：{len(klines)}条")
        else:
            print("❌ 通过 manager 获取 K 线失败")
        
    except Exception as e:
        print(f"❌ 获取 TickFlow 适配器失败：{e}")
    
    await manager.close()


async def main():
    """主函数"""
    # 测试 1：直接测试适配器
    await test_tickflow_adapter()
    
    # 测试 2：通过 DataSourceManager 测试
    await test_data_source_manager()


if __name__ == "__main__":
    asyncio.run(main())
