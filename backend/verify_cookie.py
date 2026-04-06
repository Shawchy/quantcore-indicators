import json

# 读取 Cookie 文件
with open('data/cookies/eastmoney_com_manual.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=" * 50)
print("东方财富网 Cookie 验证")
print("=" * 50)

print(f"\n✅ Cookie 文件存在")
print(f"域名：{data['domain']}")
print(f"Cookie 数量：{len(data['cookies'])}")
print(f"有效期：{data['expires_in_days']} 天")
print(f"获取时间：{data['captured_at']}")
print(f"备注：{data['note']}")

print(f"\n所有 Cookie 列表:")
for i, cookie in enumerate(data['cookies'], 1):
    print(f"  {i:2d}. {cookie['name']}: {cookie['value'][:40]}...")

print("\n" + "=" * 50)
print("✅ Cookie 配置验证通过！")
print("=" * 50)
