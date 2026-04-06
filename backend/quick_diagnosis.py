"""
快速诊断 API 响应
"""
import requests
import time

print("=" * 70)
print("API 快速诊断")
print("=" * 70)

# 测试 1: 健康检查
print("\n1. 健康检查...")
try:
    response = requests.get('http://localhost:8000/health', timeout=5)
    print(f"   ✅ 健康检查通过：{response.json()}")
except Exception as e:
    print(f"   ❌ 健康检查失败：{e}")

# 测试 2: 市场统计
print("\n2. 市场统计数据...")
start = time.time()
try:
    response = requests.get('http://localhost:8000/api/v1/screener/market-stats', timeout=10)
    elapsed = time.time() - start
    print(f"   ✅ 响应时间：{elapsed:.2f}秒")
    print(f"   状态码：{response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"   ✅ JSON 解析成功")
        
        # 检查数据结构
        if isinstance(data, dict):
            if 'data' in data:
                # 有 data 字段（未使用拦截器）
                data_content = data['data']
                print(f"   ⚠️  响应包含 'data' 字段（后端原始格式）")
            else:
                # 无 data 字段（可能已处理）
                data_content = data
                print(f"   ✅ 响应无 'data' 字段（已处理）")
            
            print(f"\n   数据内容:")
            print(f"     - total_stocks: {data_content.get('total_stocks', '缺失')}")
            print(f"     - industry_distribution: {len(data_content.get('industry_distribution', {}))} 个行业")
            print(f"     - turnover: {data_content.get('turnover', '缺失')}")
        else:
            print(f"   ❌ 响应不是字典：{type(data)}")
    else:
        print(f"   ❌ 状态码异常：{response.status_code}")
        print(f"   响应内容：{response.text[:200]}")
        
except requests.Timeout:
    print(f"   ❌ 请求超时（>10 秒）")
except Exception as e:
    print(f"   ❌ 请求失败：{e}")

# 测试 3: 实时行情
print("\n3. 实时行情...")
start = time.time()
try:
    response = requests.get('http://localhost:8000/api/v1/stock/market/realtime?index_codes=000001', timeout=10)
    elapsed = time.time() - start
    print(f"   ✅ 响应时间：{elapsed:.2f}秒")
    print(f"   状态码：{response.status_code}")
except Exception as e:
    print(f"   ❌ 请求失败：{e}")

print("\n" + "=" * 70)
print("诊断完成")
print("=" * 70)
