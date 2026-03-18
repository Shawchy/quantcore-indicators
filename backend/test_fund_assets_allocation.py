"""
基金资产配置比例 API 测试脚本

测试 efinance.fund.get_types_percentage 接口
"""
import asyncio
import sys
sys.path.insert(0, 'd:/PROJ/Quant/backend')

from app.adapters.efinance_adapter import EFinanceAdapter


async def test_assets_allocation():
    """测试基金资产配置比例"""
    print("=" * 80)
    print("基金资产配置比例 API 测试")
    print("=" * 80)
    print()
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    try:
        # 测试获取最新资产配置
        print("测试：获取易方达蓝筹精选混合 (005827) 的资产配置比例")
        print("-" * 80)
        
        result = await adapter.get_fund_types_percentage('005827')
        
        if not result:
            print("X 获取失败：返回空数据")
            return
        
        print(f"V 获取成功，共{len(result)}个报告期的数据")
        print()
        
        # 打印表头
        print(f"{'报告期':<12} {'股票比重':>10} {'债券比重':>10} {'现金比重':>10} {'其他比重':>10} {'总规模 (亿)':>12}")
        print("-" * 80)
        
        # 打印数据
        for assets in result:
            report_date = assets['report_date'] or 'N/A'
            stock_ratio = f"{assets['stock_ratio']:.2f}%" if assets['stock_ratio'] is not None else '--'
            bond_ratio = f"{assets['bond_ratio']:.2f}%" if assets['bond_ratio'] is not None else '--'
            cash_ratio = f"{assets['cash_ratio']:.2f}%" if assets['cash_ratio'] is not None else '--'
            other_ratio = f"{assets['other_ratio']:.2f}%" if assets['other_ratio'] is not None else '--'
            total_scale = f"{assets['total_scale']:.2f}" if assets['total_scale'] is not None else 'N/A'
            
            print(f"{report_date:<12} {stock_ratio:>10} {bond_ratio:>10} {cash_ratio:>10} {other_ratio:>10} {total_scale:>12}")
        
        print()
        print("-" * 80)
        print("数据分析：")
        print("-" * 80)
        
        if len(result) >= 2:
            latest = result[0]
            previous = result[1]
            
            # 计算变化
            stock_change = None
            if latest['stock_ratio'] is not None and previous['stock_ratio'] is not None:
                stock_change = latest['stock_ratio'] - previous['stock_ratio']
            
            cash_change = None
            if latest['cash_ratio'] is not None and previous['cash_ratio'] is not None:
                cash_change = latest['cash_ratio'] - previous['cash_ratio']
            
            scale_change = None
            if latest['total_scale'] is not None and previous['total_scale'] is not None:
                scale_change = latest['total_scale'] - previous['total_scale']
            
            print(f"与上一报告期相比（{previous['report_date']} → {latest['report_date']}）：")
            
            if stock_change is not None:
                print(f"  股票仓位：{stock_change > 0 and '+' or ''}{stock_change:.2f}%")
            
            if cash_change is not None:
                print(f"  现金比重：{cash_change > 0 and '+' or ''}{cash_change:.2f}%")
            
            if scale_change is not None:
                print(f"  基金规模：{scale_change > 0 and '+' or ''}{scale_change:.2f}亿元")
            
            # 分析投资风格
            print()
            print("投资风格分析：")
            if latest['stock_ratio'] is not None:
                if latest['stock_ratio'] > 90:
                    print("  ✅ 高仓位运作（股票仓位>90%）")
                elif latest['stock_ratio'] > 70:
                    print("  ✅ 中高仓位运作（股票仓位 70-90%）")
                elif latest['stock_ratio'] > 50:
                    print("  ⚠️ 中等仓位运作（股票仓位 50-70%）")
                else:
                    print("  🔴 低仓位运作（股票仓位<50%）")
            
            # 分析风格稳定性
            if len(result) >= 3:
                stock_ratios = [
                    r['stock_ratio'] 
                    for r in result 
                    if r['stock_ratio'] is not None
                ]
                
                if len(stock_ratios) >= 3:
                    avg_stock = sum(stock_ratios) / len(stock_ratios)
                    max_stock = max(stock_ratios)
                    min_stock = min(stock_ratios)
                    volatility = max_stock - min_stock
                    
                    print(f"\n  历史平均仓位：{avg_stock:.2f}%")
                    print(f"  仓位波动范围：{min_stock:.2f}% - {max_stock:.2f}%")
                    print(f"  仓位波动幅度：{volatility:.2f}%")
                    
                    if volatility < 3:
                        print("  ✅ 风格非常稳定（波动<3%）")
                    elif volatility < 8:
                        print("  ✅ 风格较稳定（波动 3-8%）")
                    else:
                        print("  ⚠️ 风格波动较大（波动>8%）")
        
        print()
        print("=" * 80)
        print("测试完成")
        print("=" * 80)
    
    except Exception as e:
        print(f"X 测试失败：{e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await adapter.close()


async def test_with_dates():
    """测试指定日期的资产配置"""
    print("\n" + "=" * 80)
    print("测试：获取指定日期的资产配置")
    print("=" * 80)
    print()
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    try:
        # 测试获取指定日期的资产配置
        print("获取 2021-12-31 和 2021-06-30 两个日期的资产配置...")
        result = await adapter.get_fund_types_percentage(
            '005827', 
            dates=['2021-12-31', '2021-06-30']
        )
        
        if result:
            print(f"✅ 获取成功，共{len(result)}个日期的数据")
            for assets in result:
                print(f"{assets['report_date']}: "
                      f"股票{assets['stock_ratio']:.2f}%, "
                      f"现金{assets['cash_ratio']:.2f}%, "
                      f"规模{assets['total_scale']:.2f}亿")
        else:
            print("X 获取失败")
    
    except Exception as e:
        print(f"❌ 测试失败：{e}")
    
    finally:
        await adapter.close()


async def test_cache():
    """测试缓存机制"""
    print("\n" + "=" * 80)
    print("缓存机制测试")
    print("=" * 80)
    print()
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    try:
        # 第一次查询
        print("第一次查询（从 API 获取）...")
        result1 = await adapter.get_fund_types_percentage('005827')
        
        # 第二次查询
        print("第二次查询（应该从缓存获取）...")
        result2 = await adapter.get_fund_types_percentage('005827')
        
        if result1 and result2:
            print(f"V 缓存测试成功")
            print(f"   两次查询结果一致：{result1 == result2}")
            print(f"   数据量：{len(result1)}个报告期")
        else:
            print(f"X 缓存测试失败")
    
    except Exception as e:
        print(f"X 测试失败：{e}")
    
    finally:
        await adapter.close()


async def main():
    """主测试函数"""
    # 测试 1: 基金资产配置比例
    await test_assets_allocation()
    
    # 测试 2: 指定日期查询
    await test_with_dates()
    
    # 测试 3: 缓存机制
    await test_cache()


if __name__ == "__main__":
    asyncio.run(main())
