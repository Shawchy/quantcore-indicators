"""
测试后端 API 数据返回
"""
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

print("=" * 60)
print("后端 API 数据测试")
print("=" * 60)

# 测试 1: 获取股票列表
print("\n1️⃣ 测试：获取股票列表")
try:
    response = requests.get(f"{BASE_URL}/stock/list", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 200:
            stocks = data.get('data', [])
            print(f"✅ 成功获取股票列表：{len(stocks)} 只股票")
            if stocks:
                print(f"   示例：{stocks[0]}")
        else:
            print(f"❌ API 返回错误：{data}")
    else:
        print(f"❌ HTTP 错误：{response.status_code}")
except Exception as e:
    print(f"❌ 请求失败：{e}")

# 测试 2: 获取上证指数 K 线
print("\n2️⃣ 测试：获取上证指数 K 线 (000001)")
try:
    response = requests.get(f"{BASE_URL}/kline/000001", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 200:
            klines = data.get('data', {}).get('klines', [])
            print(f"✅ 成功获取 K 线数据：{len(klines)} 条")
            if klines:
                print(f"   最新：{klines[-1]}")
        else:
            print(f"❌ API 返回错误：{data}")
    else:
        print(f"❌ HTTP 错误：{response.status_code}")
except Exception as e:
    print(f"❌ 请求失败：{e}")

# 测试 3: 获取板块列表
print("\n3️⃣ 测试：获取行业板块列表")
try:
    response = requests.get(f"{BASE_URL}/sector/list?sector_type=industry", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 200:
            sectors = data.get('data', [])
            print(f"✅ 成功获取板块列表：{len(sectors)} 个板块")
            if sectors:
                print(f"   示例：{sectors[0]}")
        else:
            print(f"❌ API 返回错误：{data}")
    else:
        print(f"❌ HTTP 错误：{response.status_code}")
except Exception as e:
    print(f"❌ 请求失败：{e}")

# 测试 4: 获取实时行情
print("\n4️⃣ 测试：获取大盘实时行情")
try:
    response = requests.get(f"{BASE_URL}/market/realtime?index_codes=000001,399001,399006", timeout=10)
    if response.status_code == 200:
        data = response.json()
        if data.get('code') == 200:
            quotes = data.get('data', [])
            print(f"✅ 成功获取实时行情：{len(quotes)} 个指数")
            if quotes:
                print(f"   示例：{quotes[0]}")
        else:
            print(f"❌ API 返回错误：{data}")
    else:
        print(f"❌ HTTP 错误：{response.status_code}")
except Exception as e:
    print(f"❌ 请求失败：{e}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
