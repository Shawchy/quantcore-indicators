"""
测试完整响应
"""
import requests
import json

response = requests.get('http://localhost:8000/api/v1/screener/market-stats', timeout=20)

print("完整响应:")
print(json.dumps(response.json(), indent=2, ensure_ascii=False))
