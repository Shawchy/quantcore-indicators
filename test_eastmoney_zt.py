"""东方财富涨停板行情 API 测试脚本

测试新增的 3 个接口：
1. 昨日涨停股池
2. 强势股池
3. 次新股池

使用方法：
python test_eastmoney_zt.py
"""
import asyncio
import aiohttp
import json
from datetime import datetime


BASE_URL = "http://localhost:8000/api/v1/eastmoney"


async def test_api(session: aiohttp.ClientSession, endpoint: str, params: dict = None):
    """测试单个 API 接口"""
    url = f"{BASE_URL}/{endpoint}"
    try:
        async with session.get(url, params=params) as resp:
            if resp.status == 200:
                data = await resp.json()
                return {
                    "success": True,
                    "endpoint": endpoint,
                    "count": len(data.get("data", [])),
                    "message": data.get("message", ""),
                }
            else:
                return {
                    "success": False,
                    "endpoint": endpoint,
                    "error": f"HTTP {resp.status}",
                }
    except Exception as e:
        return {
            "success": False,
            "endpoint": endpoint,
            "error": str(e),
        }


async def main():
    """主测试函数"""
    print("=" * 60)
    print("东方财富涨停板行情 API 测试")
    print("=" * 60)
    print()
    
    # 获取今日日期
    today = datetime.now().strftime("%Y%m%d")
    print(f"测试日期：{today}")
    print()
    
    async with aiohttp.ClientSession() as session:
        # 测试接口列表
        tests = [
            ("zt-pool", {"date": today}, "涨停股池"),
            ("zt-pool-previous", {"date": today}, "昨日涨停"),
            ("zt-pool-strong", {"date": today}, "强势股"),
            ("zt-pool-sub-new", {"date": today}, "次新股"),
            ("market-changes-summary", None, "市场异动汇总"),
        ]
        
        print("开始测试接口...")
        print("-" * 60)
        
        results = []
        for endpoint, params, name in tests:
            print(f"\n测试：{name} ({endpoint})")
            result = await test_api(session, endpoint, params)
            results.append(result)
            
            if result["success"]:
                print(f"  ✅ 成功 - {result['message']}")
            else:
                print(f"  ❌ 失败 - {result.get('error', '未知错误')}")
        
        print()
        print("=" * 60)
        print("测试汇总")
        print("=" * 60)
        
        success_count = sum(1 for r in results if r["success"])
        total_count = len(results)
        
        print(f"成功：{success_count}/{total_count}")
        
        if success_count == total_count:
            print("\n🎉 所有测试通过！")
        else:
            print(f"\n⚠️  有 {total_count - success_count} 个测试失败")
        
        print()
        print("详细结果：")
        for result in results:
            status = "✅" if result["success"] else "❌"
            print(f"  {status} {result['endpoint']}: {result.get('count', 'N/A')} 条数据")


if __name__ == "__main__":
    asyncio.run(main())
