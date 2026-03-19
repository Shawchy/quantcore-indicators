"""
基金阶段涨跌幅 API 测试脚本

测试 efinance.fund.get_period_change 接口
"""
import asyncio
import sys
sys.path.insert(0, 'd:/PROJ/Quant/backend')

from app.adapters.efinance_adapter import EFinanceAdapter


async def test_period_change():
    """测试基金阶段涨跌幅"""
    print("=" * 80)
    print("基金阶段涨跌幅 API 测试")
    print("=" * 80)
    print()
    
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    try:
        # 测试单只基金
        print("测试：获取招商中证白酒指数 (LOF)A (161725) 的阶段涨跌幅")
        print("-" * 80)
        
        result = await adapter.get_fund_period_change('161725')
        
        if not result:
            print("❌ 获取失败：返回空数据")
            return
        
        print(f"✅ 获取成功，共{len(result)}个时间段的数据")
        print()
        
        # 打印表头
        print(f"{'时间段':<10} {'收益率':>10} {'同类平均':>10} {'同类排行':>12} {'排名百分比':>10}")
        print("-" * 80)
        
        # 打印数据
        for period in result:
            period_name = period['period']
            return_rate = f"{period['return_rate']:.2f}%" if period['return_rate'] is not None else "N/A"
            avg_return = f"{period['avg_return']:.2f}%" if period['avg_return'] is not None else "N/A"
            
            if period['rank'] is not None and period['total_count'] is not None:
                rank = f"{period['rank']}/{period['total_count']}"
                rank_rate = f"{(period['rank_rate'] or 0) * 100:.2f}%"
            else:
                rank = "N/A"
                rank_rate = "N/A"
            
            print(f"{period_name:<10} {return_rate:>10} {avg_return:>10} {rank:>12} {rank_rate:>10}")
        
        print()
        print("-" * 80)
        print("数据分析：")
        print("-" * 80)
        
        # 找出表现最好的时间段
        valid_periods = [p for p in result if p['rank_rate'] is not None]
        if valid_periods:
            best = min(valid_periods, key=lambda x: x['rank_rate'] or 1)
            print(f"🏆 表现最佳：{best['period']} (收益率{best['return_rate']}%, 排名前{best['rank_rate']*100:.2f}%)")
        
        # 找出收益率最高的时间段
        high_return_periods = [p for p in result if p['return_rate'] is not None]
        if high_return_periods:
            highest = max(high_return_periods, key=lambda x: x['return_rate'] or 0)
            print(f"📈 收益率最高：{highest['period']} ({highest['return_rate']}%)")
        
        # 分析长期表现
        long_term_periods = ['近一年', '近三年', '近五年']
        long_term_data = [p for p in result if p['period'] in long_term_periods and p['rank_rate'] is not None]
        if long_term_data:
            avg_rank_rate = sum(p['rank_rate'] or 0 for p in long_term_data) / len(long_term_data)
            print(f"📊 长期平均排名：前{avg_rank_rate*100:.2f}%")
            
            if avg_rank_rate < 0.1:
                print("   ✅ 长期表现极佳（前 10%）")
            elif avg_rank_rate < 0.3:
                print("   ✅ 长期表现良好（前 30%）")
            else:
                print("   ⚠️ 长期表现一般")
        
        print()
        print("=" * 80)
        print("测试完成")
        print("=" * 80)
    
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
    
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
        result1 = await adapter.get_fund_period_change('161725')
        
        # 第二次查询
        print("第二次查询（应该从缓存获取）...")
        result2 = await adapter.get_fund_period_change('161725')
        
        if result1 and result2:
            print(f"✅ 缓存测试成功")
            print(f"   两次查询结果一致：{result1 == result2}")
            print(f"   数据量：{len(result1)}个时间段")
        else:
            print("❌ 缓存测试失败")
    
    except Exception as e:
        print(f"❌ 测试失败：{e}")
    
    finally:
        await adapter.close()


async def main():
    """主测试函数"""
    # 测试 1: 基金阶段涨跌幅
    await test_period_change()
    
    # 测试 2: 缓存机制
    await test_cache()


if __name__ == "__main__":
    asyncio.run(main())
