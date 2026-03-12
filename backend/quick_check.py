"""
快速验证脚本 - 检查数据库和 API
"""
import sqlite3
import requests
import os

print("=" * 70)
print("快速验证 - 数据库和 API")
print("=" * 70)

# 1. 检查数据库
db_path = os.path.join(os.path.dirname(__file__), 'data', 'sqlite', 'quant.db')
print(f"\n1️⃣ 数据库检查")
print(f"   路径：{db_path}")
print(f"   存在：{'✅' if os.path.exists(db_path) else '❌'}")

if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT COUNT(*) FROM stock_info')
    stock_count = cursor.fetchone()[0]
    print(f"   stock_info: {stock_count} 条 {'✅' if stock_count > 0 else '❌'}")
    
    cursor.execute('SELECT COUNT(*) FROM sector_info')
    sector_count = cursor.fetchone()[0]
    print(f"   sector_info: {sector_count} 条 {'✅' if sector_count > 0 else '❌'}")
    
    cursor.execute('SELECT COUNT(*) FROM kline')
    kline_count = cursor.fetchone()[0]
    print(f"   kline: {kline_count} 条 {'✅' if kline_count > 100 else '⚠️' if kline_count > 0 else '❌'}")
    
    conn.close()

# 2. 检查 API
print(f"\n2️⃣ API 检查")
BASE_URL = "http://localhost:8000/api/v1"

try:
    # 测试 K 线 API
    response = requests.get(f"{BASE_URL}/kline/000001", timeout=5)
    if response.status_code == 200:
        data = response.json()
        klines = data.get('data', {}).get('data', [])
        print(f"   GET /kline/000001: {len(klines)} 条 {'✅' if len(klines) > 0 else '❌'}")
    else:
        print(f"   GET /kline/000001: HTTP {response.status_code} ❌")
except Exception as e:
    print(f"   GET /kline/000001: 请求失败 - {e} ❌")

try:
    # 测试指数 API
    response = requests.get(f"{BASE_URL}/market/realtime?index_codes=000001", timeout=5)
    if response.status_code == 200:
        data = response.json()
        quotes = data.get('data', [])
        print(f"   GET /market/realtime: {len(quotes)} 个 {'✅' if len(quotes) > 0 else '⚠️ 空数据'}")
    else:
        print(f"   GET /market/realtime: HTTP {response.status_code} ❌")
except Exception as e:
    print(f"   GET /market/realtime: 请求失败 - {e} ❌")

print("\n" + "=" * 70)
print("验证完成")
print("=" * 70)

print("\n💡 建议:")
if stock_count == 0 or sector_count == 0:
    print("   1. 获取新的 Tushare Token: https://tushare.pro/")
    print("   2. 更新 backend/.env 中的 TUSHARE_TOKEN")
    print("   3. 重启后端：python -m uvicorn app.main:app --reload")
    print("   4. 初始化数据：python init_data.py")
else:
    print("   ✅ 数据库有数据，请检查前端是否正确调用 API")
