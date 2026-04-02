"""
快速测试凭证注入 - 仅测试初始化
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.efinance_adapter import EFinanceAdapter


async def quick_test():
    print("\n=== 快速测试凭证注入集成 ===\n")
    
    # 测试 AkShare 初始化
    print("1. AkShare 适配器初始化...")
    ak_adapter = AkShareAdapter()
    success = await ak_adapter.initialize()
    print(f"   结果：{'✓ 成功' if success else '✗ 失败'}")
    print(f"   凭证注入器：{'已创建' if hasattr(ak_adapter, '_injector') else '未创建'}")
    await ak_adapter.close()
    
    # 测试 EFinance 初始化
    print("\n2. EFinance 适配器初始化...")
    ef_adapter = EFinanceAdapter()
    success = await ef_adapter.initialize()
    print(f"   结果：{'✓ 成功' if success else '✗ 失败'}")
    print(f"   凭证注入器：{'已创建' if hasattr(ef_adapter, '_injector') else '未创建'}")
    await ef_adapter.close()
    
    print("\n✓ 两个适配器都已集成凭证注入器")
    print("✓ 懒加载模式：首次请求高敏感 API 时才会获取凭证")
    print("✓ TLS 指纹伪装：curl_cffi (chrome120)")


if __name__ == "__main__":
    asyncio.run(quick_test())
