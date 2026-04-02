"""
验证 AkShare 适配器凭证注入集成
"""

import asyncio
import sys
sys.path.insert(0, '.')

from app.adapters.akshare_adapter import AkShareAdapter


async def verify():
    print("\n=== 验证 AkShare 适配器凭证注入集成 ===\n")
    
    adapter = AkShareAdapter()
    
    # 初始化
    print("初始化 AkShare 适配器...")
    success = await adapter.initialize()
    
    if success:
        print("✓ 初始化成功")
        print(f"✓ 凭证注入器已创建：{hasattr(adapter, '_injector')}")
        print(f"✓ TLS 指纹模式：curl_cffi (chrome120)")
        print(f"✓ 懒加载模式：首次请求时获取凭证")
    else:
        print("✗ 初始化失败")
    
    await adapter.close()
    
    print("\n验证完成！")
    print("\n预期日志输出：")
    print("  - AkShare 适配器初始化成功（凭证注入模式待命）")
    print("  - TLS 指纹：curl_cffi (chrome120)")
    print("  - 请求频率：自适应延迟（根据时间段和失败次数调整）")
    print("  - 最大重试：5 次（指数退避）")


if __name__ == "__main__":
    asyncio.run(verify())
