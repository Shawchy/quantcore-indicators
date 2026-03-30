"""
测试板块 API 接口
"""
import requests
import json

# 测试 SW 类型
print("=" * 80)
print("测试板块 API 接口")
print("=" * 80)

try:
    # 测试 SW 类型
    response = requests.get("http://localhost:9329/api/v1/sector/list?sector_type=sw")
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ SW 类型板块数：{len(data.get('data', []))}")
        if data.get('data'):
            print("\n前 10 个 SW 板块:")
            for i, sector in enumerate(data['data'][:10]):
                print(f"  {i+1}. {sector['code']} | {sector['name']:15} | {sector.get('sector_type', 'N/A')}")
    else:
        print(f"\n❌ SW 类型请求失败：{response.status_code}")
        print(response.text)
    
    # 测试 industry 类型
    response = requests.get("http://localhost:9329/api/v1/sector/list?sector_type=industry")
    if response.status_code == 200:
        data = response.json()
        print(f"\n✅ Industry 类型板块数：{len(data.get('data', []))}")
        if data.get('data'):
            print("\n前 10 个 Industry 板块:")
            for i, sector in enumerate(data['data'][:10]):
                print(f"  {i+1}. {sector['code']} | {sector['name']:15} | {sector.get('sector_type', 'N/A')}")
    else:
        print(f"\n❌ Industry 类型请求失败：{response.status_code}")
        print(response.text)
    
except Exception as e:
    print(f"\n❌ 测试失败：{e}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
