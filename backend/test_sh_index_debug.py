"""
测试上证指数 API 接口（带认证）- 调试版本
"""
import requests
import json

print("=" * 80)
print("测试上证指数 API 接口")
print("=" * 80)

# 先登录获取 token
try:
    login_response = requests.post("http://localhost:9329/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123"
    })
    
    print(f"\n登录响应状态码：{login_response.status_code}")
    print(f"登录响应内容：{login_response.text}")
    
    if login_response.status_code == 200:
        login_data = login_response.json()
        token = login_data.get('access_token')
        
        if not token:
            print(f"\n❌ 未获取到 token")
            print(f"响应数据结构：{login_data.keys()}")
        else:
            print(f"\n✅ 登录成功，获取到 token: {token[:20]}...")
            
            # 测试上证指数实时行情
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get("http://localhost:9329/api/v1/stock/000001/realtime", headers=headers)
            print(f"\n请求：GET /api/v1/stock/000001/realtime")
            print(f"状态码：{response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"\n✅ 获取到上证指数数据:")
                print(f"完整响应：{json.dumps(data, indent=2, ensure_ascii=False)}")
            else:
                print(f"\n❌ 请求失败：{response.text}")
    else:
        print(f"\n❌ 登录失败：{login_response.text}")
        
except Exception as e:
    print(f"\n❌ 测试失败：{e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
