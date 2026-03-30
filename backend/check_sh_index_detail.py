"""
检查上证指数数据 - 详细版本
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
        # 尝试不同的代码格式
        test_codes = ["000001", "000001.SH", "sh000001", "000001.XSHG"]
        
        for code in test_codes:
            print(f"\n尝试代码：{code}", flush=True)
            index_data = await data_source_manager.get_realtime_quote(code)
            
            if index_data:
                print(f"✅ 获取到数据:")
                if isinstance(index_data, dict):
                    print(f"   类型：字典")
                    print(f"   完整数据：{index_data}")
                else:
                    print(f"   类型：{type(index_data)}")
                    print(f"   code: {getattr(index_data, 'code', 'N/A')}")
                    print(f"   name: {getattr(index_data, 'name', 'N/A')}")
                    print(f"   price: {getattr(index_data, 'price', 'N/A')}")
                    print(f"   change: {getattr(index_data, 'change', 'N/A')}")
                    print(f"   change_pct: {getattr(index_data, 'change_pct', 'N/A')}")
            else:
                print(f"❌ 获取数据失败", flush=True)
    except Exception as e:
        print(f"\n❌ 获取数据失败：{e}", flush=True)
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 80, flush=True)

if __name__ == '__main__':
    asyncio.run(check_sh_index())
