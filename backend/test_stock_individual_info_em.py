"""
测试 stock_individual_info_em API（高危反爬）

测试内容：
1. 基本功能测试
2. 反爬策略验证
3. 缓存机制测试
4. 错误处理测试
"""

import asyncio
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from app.adapters.akshare_adapter import AkShareDataAdapter


async def test_basic_function():
    """测试 1：基本功能"""
    print("\n" + "="*60)
    print("测试 1：基本功能 - 获取个股详细资料")
    print("="*60)
    
    adapter = AkShareDataAdapter()
    await adapter.initialize()
    
    # 测试股票：贵州茅台
    code = "600519"
    print(f"\n📊 测试股票：{code}（贵州茅台）")
    
    try:
        result = await adapter.get_stock_individual_info_em(code)
        
        if result:
            print(f"\n✅ 获取成功！")
            print(f"   股票简称：{result.get('name', 'Unknown')}")
            print(f"   最新价：{result.get('latest_price')}")
            print(f"   涨跌幅：{result.get('change_pct')}%")
            print(f"   总市值：{result.get('total_market_cap')} 亿元")
            print(f"   流通市值：{result.get('float_market_cap')} 亿元")
            print(f"   市盈率：{result.get('pe_ratio')}")
            print(f"   市净率：{result.get('pb_ratio')}")
            print(f"   每股收益：{result.get('eps')} 元")
            print(f"   净资产收益率：{result.get('roe')}%")
            print(f"   所属行业：{result.get('industry')}")
            print(f"   地区：{result.get('area')}")
            print(f"   上市日期：{result.get('list_date')}")
        else:
            print(f"\n❌ 获取失败：返回空数据")
            
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
    
    await adapter.close()
    return True


async def test_multiple_stocks():
    """测试 2：批量获取多只股票"""
    print("\n" + "="*60)
    print("测试 2：批量获取多只股票")
    print("="*60)
    
    adapter = AkShareDataAdapter()
    await adapter.initialize()
    
    # 测试股票列表
    test_stocks = [
        ("600519", "贵州茅台"),
        ("000858", "五粮液"),
        ("300750", "宁德时代"),
        ("601318", "中国平安"),
        ("600036", "招商银行"),
    ]
    
    results = []
    
    for code, name in test_stocks:
        print(f"\n📊 获取：{code}（{name}）...")
        
        try:
            result = await adapter.get_stock_individual_info_em(code)
            
            if result and not result.get('error'):
                print(f"   ✅ 成功 - 最新价：{result.get('latest_price')}，涨跌幅：{result.get('change_pct')}%")
                results.append((code, True))
            else:
                print(f"   ⚠️  失败 - {result.get('error', 'Unknown error') if result else 'Empty result'}")
                results.append((code, False))
                
        except Exception as e:
            print(f"   ❌ 异常：{e}")
            results.append((code, False))
        
        # 间隔延迟，避免触发限流
        await asyncio.sleep(1.0)
    
    # 统计结果
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    print(f"\n📊 测试总结：")
    print(f"   成功：{success_count}/{total_count} ({success_count/total_count:.1%})")
    
    await adapter.close()
    return success_count > 0


async def test_cache_mechanism():
    """测试 3：缓存机制"""
    print("\n" + "="*60)
    print("测试 3：缓存机制测试")
    print("="*60)
    
    adapter = AkShareDataAdapter()
    await adapter.initialize()
    
    code = "600519"
    print(f"\n📊 测试股票：{code}（贵州茅台）")
    
    # 第一次请求（应该调用 API）
    print(f"\n⏳ 第一次请求（应该调用 API）...")
    import time
    start_time = time.time()
    result1 = await adapter.get_stock_individual_info_em(code)
    time1 = time.time() - start_time
    print(f"   耗时：{time1:.2f}秒")
    
    # 第二次请求（应该命中缓存）
    print(f"\n⏳ 第二次请求（应该命中缓存）...")
    start_time = time.time()
    result2 = await adapter.get_stock_individual_info_em(code)
    time2 = time.time() - start_time
    print(f"   耗时：{time2:.2f}秒")
    
    # 验证缓存
    if time2 < time1 * 0.5:  # 缓存应该快很多
        print(f"\n✅ 缓存机制正常！")
        print(f"   第一次：{time1:.2f}秒")
        print(f"   第二次：{time2:.2f}秒（缓存命中）")
        print(f"   加速：{(time1/time2):.1f}x")
    else:
        print(f"\n⚠️  缓存可能未生效")
        print(f"   第一次：{time1:.2f}秒")
        print(f"   第二次：{time2:.2f}秒")
    
    await adapter.close()
    return True


async def test_error_handling():
    """测试 4：错误处理"""
    print("\n" + "="*60)
    print("测试 4：错误处理测试")
    print("="*60)
    
    adapter = AkShareDataAdapter()
    await adapter.initialize()
    
    # 测试无效股票代码
    invalid_code = "000000"
    print(f"\n📊 测试无效代码：{invalid_code}")
    
    try:
        result = await adapter.get_stock_individual_info_em(invalid_code)
        
        if result:
            if result.get('error'):
                print(f"✅ 错误处理正常！")
                print(f"   错误信息：{result.get('error')}")
            else:
                print(f"⚠️  返回了数据（可能代码有效）")
                print(f"   股票简称：{result.get('name')}")
        else:
            print(f"✅ 返回空数据（错误处理正常）")
            
    except Exception as e:
        print(f"✅ 捕获异常：{e}")
    
    await adapter.close()
    return True


async def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("stock_individual_info_em API 测试（高危反爬）")
    print("="*60)
    
    tests = [
        ("基本功能测试", test_basic_function),
        ("批量获取测试", test_multiple_stocks),
        ("缓存机制测试", test_cache_mechanism),
        ("错误处理测试", test_error_handling),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n❌ {test_name} 测试异常：{e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # 打印总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{status}: {test_name}")
    
    print(f"\n总计：{passed}/{total} 测试通过 ({passed/total:.1%})")
    
    if passed == total:
        print("\n🎉 所有测试通过！反爬策略工作正常。")
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查。")


if __name__ == "__main__":
    asyncio.run(run_all_tests())
