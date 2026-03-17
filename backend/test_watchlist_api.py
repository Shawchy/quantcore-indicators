"""
测试自选股 API
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"
TOKEN = None

def login():
    """登录获取 token"""
    global TOKEN  # 使用全局变量
    
    url = f"{BASE_URL}/auth/login"
    data = {
        "username": "admin",
        "password": "admin123"  # 默认密码，可以在 .env 中修改
    }
    
    print(f"\n🔐 登录获取 Token")
    print(f"URL: {url}")
    print(f"用户：{data['username']}")
    
    try:
        response = requests.post(url, json=data)
        if response.status_code == 200:
            result = response.json()
            token = result.get("access_token")
            TOKEN = token
            print(f"✅ 登录成功！Token: {token[:20]}...")
            return token
        else:
            print(f"❌ 登录失败：{response.status_code}")
            print(f"响应：{response.json()}")
            return None
    except Exception as e:
        print(f"❌ 错误：{e}")
        return None

def get_headers():
    """获取请求头（包含认证）"""
    if TOKEN:
        return {
            "Authorization": f"Bearer {TOKEN}",
            "Content-Type": "application/json"
        }
    return {}

def test_add_stock():
    """测试添加股票到自选股"""
    url = f"{BASE_URL}/watchlist/add"
    data = {
        "code": "000001",
        "note": "测试股票 - 平安银行"
    }
    
    print(f"\n1️⃣ 添加股票到自选股：{data['code']}")
    print(f"URL: {url}")
    print(f"数据：{json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.post(url, json=data, headers=get_headers())
        print(f"状态码：{response.status_code}")
        print(f"响应：{response.json()}")
    except Exception as e:
        print(f"❌ 错误：{e}")

def test_get_watchlist():
    """测试获取自选股列表"""
    url = f"{BASE_URL}/watchlist/list"
    
    print(f"\n2️⃣ 获取自选股列表")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"状态码：{response.status_code}")
        result = response.json()
        print(f"响应：{json.dumps(result, ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ 错误：{e}")

def test_remove_stock():
    """测试删除自选股"""
    code = "000001"
    url = f"{BASE_URL}/watchlist/remove/{code}"
    
    print(f"\n3️⃣ 删除自选股：{code}")
    print(f"URL: {url}")
    
    try:
        response = requests.delete(url, headers=get_headers())
        print(f"状态码：{response.status_code}")
        print(f"响应：{response.json()}")
    except Exception as e:
        print(f"❌ 错误：{e}")

def test_update_note():
    """测试更新备注"""
    code = "000001"
    url = f"{BASE_URL}/watchlist/update/{code}"
    data = {
        "note": "更新后的备注 - 平安银行"
    }
    
    print(f"\n4️⃣ 更新自选股备注：{code}")
    print(f"URL: {url}")
    print(f"数据：{json.dumps(data, ensure_ascii=False)}")
    
    try:
        response = requests.put(url, json=data, headers=get_headers())
        print(f"状态码：{response.status_code}")
        print(f"响应：{response.json()}")
    except Exception as e:
        print(f"❌ 错误：{e}")

def test_get_quotes():
    """测试获取自选股行情"""
    url = f"{BASE_URL}/watchlist/quotes"
    
    print(f"\n5️⃣ 获取自选股行情")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=get_headers())
        print(f"状态码：{response.status_code}")
        print(f"响应：{json.dumps(response.json(), ensure_ascii=False, indent=2)}")
    except Exception as e:
        print(f"❌ 错误：{e}")

if __name__ == "__main__":
    print("=" * 70)
    print("自选股 API 测试")
    print("=" * 70)
    
    # 先登录
    token = login()
    
    if not token:
        print("\n❌ 登录失败，无法继续测试")
        print("\n请确保：")
        print("1. 后端服务已启动：python main.py")
        print("2. 用户名密码正确（默认：admin/admin123）")
        exit(1)
    
    # 测试添加
    test_add_stock()
    
    # 测试获取列表
    test_get_watchlist()
    
    # 测试更新备注
    test_update_note()
    
    # 测试获取行情
    test_get_quotes()
    
    # 测试删除（可选）
    # test_remove_stock()
    
    print("\n" + "=" * 70)
    print("测试完成")
    print("=" * 70)
