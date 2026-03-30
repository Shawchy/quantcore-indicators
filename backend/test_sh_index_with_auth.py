"""
测试上证指数 API 接口（带认证）
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
    
    if login_response.status_code == 200:
        token = login_response.json()['data']['token']
        print(f"\n✅ 登录成功，获取到 token")
        
        # 测试上证指数实时行情
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get("http://localhost:9329/api/v1/stock/000001/realtime", headers=headers)
        print(f"\n请求：GET /api/v1/stock/000001/realtime")
        print(f"状态码：{response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 获取到上证指数数据:")
            
            if 'data' in data:
                quote = data['data']
                print(f"   代码：{quote.get('code', 'N/A')}")
                print(f"   名称：{quote.get('name', 'N/A')}")
                print(f"   当前价：{quote.get('price', 'N/A')}")
                print(f"   涨跌：{quote.get('change', 'N/A')}")
                print(f"   涨跌幅：{quote.get('change_pct', 'N/A')}%")
                print(f"   今开：{quote.get('open', 'N/A')}")
                print(f"   昨收：{quote.get('prev_close', 'N/A')}")
                print(f"   最高：{quote.get('high', 'N/A')}")
                print(f"   最低：{quote.get('low', 'N/A')}")
                print(f"   成交量：{quote.get('volume', 'N/A')}")
                
                # 检查价格是否合理（上证指数应该在 3000 点左右）
                price = quote.get('price', 0)
                if 2000 <= price <= 5000:
                    print(f"\n✅ 价格 {price} 在合理范围内 (2000-5000)")
                else:
                    print(f"\n❌ 价格 {price} 不在合理范围内 (2000-5000)")
            else:
                print(f"\n❌ 返回数据格式错误：{data}")
        else:
            print(f"\n❌ 请求失败：{response.text}")
    else:
        print(f"\n❌ 登录失败：{login_response.text}")
        
except Exception as e:
    print(f"\n❌ 测试失败：{e}")

print("\n" + "=" * 80)
print("测试完成")
print("=" * 80)
