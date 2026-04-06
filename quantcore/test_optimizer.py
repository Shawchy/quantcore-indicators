"""
参数优化测试

测试网格搜索和随机搜索功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-api'))

from quantcore import Strategy, BacktestEngine, BacktestConfig, StrategyRunner
from quantcore.optimizer import GridSearch, RandomSearch, optimize_strategy
from datetime import datetime, timedelta


class TestStrategy(Strategy):
    """测试策略 - 双均线"""
    
    parameters = {
        'fast_period': 5,
        'slow_period': 20,
    }
    
    def __init__(self):
        super().__init__()
        self.name = "TestMA"
        self.fast_period = self.parameters['fast_period']
        self.slow_period = self.parameters['slow_period']
        self.prices = []
        self.position = 0
    
    def on_init(self, engine):
        super().on_init(engine)
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < self.slow_period:
            return
        
        fast_ma = sum(self.prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(self.prices[-self.slow_period:]) / self.slow_period
        
        if fast_ma > slow_ma and self.position == 0:
            self.buy(bar.symbol, bar.close, 1000)
            self.position = 1
        elif fast_ma < slow_ma and self.position == 1:
            self.sell(bar.symbol, bar.close, 1000)
            self.position = 0


def generate_test_data(days: int = 200):
    """生成测试数据"""
    from quantcore import Bar
    
    bars = []
    base_price = 10.0
    
    for i in range(days):
        trend = 0.02 * (i // 30)
        noise = ((i % 7) - 3) * 0.05
        
        price = base_price + trend + noise
        
        bar = Bar(
            timestamp=datetime(2024, 1, 1) + timedelta(days=i),
            symbol="SH.600000",
            open=price,
            high=price * 1.02,
            low=price * 0.98,
            close=price * (1 + ((i % 3) - 1) * 0.02),
            volume=1000000 + (i % 10) * 100000,
            turnover=price * (1000000 + (i % 10) * 100000)
        )
        bars.append(bar)
    
    return bars


def test_grid_search():
    """测试网格搜索"""
    print("\n" + "="*80)
    print("测试网格搜索")
    print("="*80)
    
    # 生成数据
    bars = generate_test_data(200)
    
    # 参数网格
    param_grid = {
        'fast_period': [5, 10, 15],
        'slow_period': [20, 40, 60],
    }
    
    # 创建优化器
    optimizer = GridSearch(parallel=False, max_workers=4)
    
    # 执行优化
    results = optimizer.optimize(
        strategy_class=TestStrategy,
        param_grid=param_grid,
        bars=bars,
        initial_capital=1000000.0,
        objective='sharpe',
        verbose=True
    )
    
    # 打印结果
    optimizer.print_top_results(top_n=5)
    
    return results


def test_random_search():
    """测试随机搜索"""
    print("\n" + "="*80)
    print("测试随机搜索")
    print("="*80)
    
    # 生成数据
    bars = generate_test_data(200)
    
    # 参数分布
    param_distributions = {
        'fast_period': (5, 20),
        'slow_period': (20, 100),
    }
    
    # 创建优化器
    optimizer = RandomSearch(parallel=False, max_workers=4, random_state=42)
    
    # 执行优化
    results = optimizer.optimize(
        strategy_class=TestStrategy,
        param_distributions=param_distributions,
        bars=bars,
        n_iterations=20,
        initial_capital=1000000.0,
        objective='return',
        verbose=True
    )
    
    # 打印结果
    optimizer.print_top_results(top_n=5)
    
    return results


def test_convenience_function():
    """测试便捷函数"""
    print("\n" + "="*80)
    print("测试便捷函数")
    print("="*80)
    
    # 生成数据
    bars = generate_test_data(200)
    
    # 参数网格
    param_grid = {
        'fast_period': [5, 10],
        'slow_period': [20, 40],
    }
    
    # 使用便捷函数
    results = optimize_strategy(
        strategy_class=TestStrategy,
        param_grid=param_grid,
        bars=bars,
        method='grid',
        objective='return',
        parallel=False,
        verbose=True
    )
    
    print(f"\n找到 {len(results)} 个优化结果")
    if results:
        best = results[0]
        print(f"最佳参数：{best.parameters}")
        print(f"收益率：{best.return_value*100:.2f}%")
        print(f"夏普比率：{best.sharpe_ratio:.2f}")


if __name__ == "__main__":
    print("\n" + "="*80)
    print("QuantCore 参数优化工具测试")
    print("="*80)
    
    # 测试网格搜索
    grid_results = test_grid_search()
    
    # 测试随机搜索
    random_results = test_random_search()
    
    # 测试便捷函数
    convenience_results = test_convenience_function()
    
    print("\n" + "="*80)
    print("所有测试完成！")
    print("="*80)
