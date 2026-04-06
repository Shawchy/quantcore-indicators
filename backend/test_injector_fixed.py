"""
测试修复后的凭证注入器
"""
import asyncio
from app.adapters.credential_injector import CredentialInjector

async def test():
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    print(f"创建凭证注入器 (Edge: {edge_path})...")
    injector = CredentialInjector({
        'browser_path': edge_path,
        'headless': True,
    })
    
    print("初始化凭证注入器...")
    await injector.initialize()
    
    print("\n获取凭证...")
    success = await injector.fetch_credentials('eastmoney.com')
    print(f"✅ 凭证获取结果：{success}")
    
    status = injector.get_status()
    print(f"\n凭证注入器状态:")
    print(f"  初始化：{status.get('initialized')}")
    print(f"  已注入：{status.get('patched')}")
    
    credentials = status.get('credentials', {})
    if 'eastmoney.com' in credentials:
        cred = credentials['eastmoney.com']
        print(f"  eastmoney.com:")
        print(f"    有效：{cred.get('valid')}")
        print(f"    Cookie 数量：{cred.get('count', 'N/A')}")
    
    # 测试 patch_requests
    print("\n测试 patch_requests_with_tls...")
    patch_result = injector.patch_requests_with_tls()
    print(f"✅ Patch 结果：{patch_result}")
    
    print("\n✅ 所有测试完成！")

if __name__ == '__main__':
    asyncio.run(test())
