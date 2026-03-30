"""
检查上证指数数据
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.adapters import data_source_manager

async def check_sh_index():
    """检查上证指数数据"""
    print("=" * 80, flush=True)
    print("检查上证指数数据")
    print("=" * 80, flush=True)
    
    # 初始化数据源管理器
    await data_source_manager.initialize()
    print(f"\n✅ 数据源管理器初始化完成，当前使用：{data_source_manager._default_source}\n", flush=True)
    
    # 获取上证指数实时行情
    print("📈 获取上证指数实时行情...", flush=True)
    try:
        index_data = await data_source_manager.get_realtime_quote("000001")
        
        if index_data:
            print(f"\n✅ 获取到上证指数数据:")
            print(f"   代码：{index_data.code}")
            print(f"   名称：{index_data.name}")
            print(f"   当前价：{index_data.price}")
            print(f"   涨跌：{index_data.change}")
            print(f"   涨跌幅：{index_data.change_pct}%")
            print(f"   今开：{index_data.open}")
            print(f"   昨收：{index_data.pre_close}")
            print(f"   最高：{index_data.high}")
            print(f"   最低：{index_data.low}")
            print(f"   成交量：{index_data.volume}")
            print(f"   成交额：{index_data.amount}")
        else:
            print("❌ 获取数据失败", flush=True)
    except Exception as e:
        print(f"\n❌ 获取数据失败：{e}", flush=True)
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80, flush=True)

if __name__ == '__main__':
    asyncio.run(check_sh_index())
