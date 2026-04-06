"""
QuantCore 快速入门示例

这个示例展示如何使用 QuantCore 框架进行策略回测
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-api'))

from quantcore import (
    Bar, BacktestEngine, BacktestConfig, Strategy, StrategyRunner,
    create_data_loader, RiskManager, PositionLimit,
    PerformanceReport, ma, ema, macd, rsi, bollinger_bands,
)
from datetime import datetime, timedelta


class SimpleMAStrategy(Strategy):
    """简单均线策略示例"""
    
    parameters = {
        'fast_period': 5,
        'slow_period': 20,
    }
    
    def __init__(self):
        """初始化策略"""
        super().__init__()
        self.name = "SimpleMA"
        self.fast_period = self.parameters.get('fast_period', 5)
        self.slow_period = self.parameters.get('slow_period', 20)
    
    def on_init(self, engine):
        """策略初始化"""
        super().on_init(engine)
        self.prices = []
        self.position = 0
    
    def on_bar(self, bar, engine):
        """K 线事件处理"""
        self.prices.append(bar.close)
        
        # 等待足够的数据
        if len(self.prices) < self.slow_period:
            return
        
        # 计算均线
        fast_ma = sum(self.prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(self.prices[-self.slow_period:]) / self.slow_period
        
        # 金叉买入
        if fast_ma > slow_ma and self.position == 0:
            self.buy(bar.symbol, bar.close, 1000)
            self.position = 1
            print(f"{bar.timestamp} - 金叉买入：{bar.close:.2f}")
        
        # 死叉卖出
        elif fast_ma < slow_ma and self.position == 1:
            self.sell(bar.symbol, bar.close, 1000)
            self.position = 0
            print(f"{bar.timestamp} - 死叉卖出：{bar.close:.2f}")


def generate_sample_data():
    """生成示例数据"""
    print("生成示例数据...")
    
    bars = []
    base_price = 10.0
    
    for i in range(100):
        # 生成带有趋势的随机数据
        trend = 0.05 * (i // 20)  # 每 20 天一个趋势
        noise = ((i % 7) - 3) * 0.1  # 周期性噪音
        
        price = base_price + trend + noise
        
        bar = Bar(
            timestamp=datetime(2024, 1, 1) + timedelta(days=i),
            symbol="SH.600000",
            open=price,
            high=price * 1.02,
            low=price * 0.98,
            close=price * (1 + ((i % 3) - 1) * 0.01),
            volume=1000000 + (i % 10) * 100000,
            turnover=price * (1000000 + (i % 10) * 100000)
        )
        bars.append(bar)
    
    print(f"[OK] 生成了 {len(bars)} 条数据")
    return bars


def run_backtest():
    """运行回测"""
    print("\n" + "=" * 60)
    print("QuantCore 快速入门示例")
    print("=" * 60)
    
    # 1. 生成或加载数据
    bars = generate_sample_data()
    
    # 2. 配置回测
    config = BacktestConfig(
        initial_capital=1000000.0,
        commission_rate=0.0003,
        slippage=0.001,
    )
    print(f"\n回测配置:")
    print(f"  初始资金：{config.initial_capital:,.2f}")
    print(f"  手续费率：{config.commission_rate*100:.2f}%")
    print(f"  滑点：{config.slippage*100:.2f}%")
    
    # 3. 创建引擎
    engine = BacktestEngine(config)
    
    # 4. 创建策略
    strategy = SimpleMAStrategy()
    print(f"\n策略配置:")
    print(f"  策略名称：{strategy.name}")
    print(f"  快速均线：{strategy.fast_period}日")
    print(f"  慢速均线：{strategy.slow_period}日")
    
    # 5. 运行回测
    print("\n开始回测...")
    print("-" * 60)
    runner = StrategyRunner(strategy)
    result = runner.run(engine, bars)
    print("-" * 60)
    
    # 6. 输出结果
    print("\n" + "=" * 60)
    print("回测结果")
    print("=" * 60)
    print(f"初始资金：{result.initial_capital:,.2f}")
    print(f"最终资金：{result.final_capital:,.2f}")
    print(f"总收益：{result.total_return*100:.2f}%")
    print(f"交易次数：{result.total_trades}")
    print(f"持仓：{len(result.positions)}")
    
    # 7. 绩效分析
    print("\n" + "=" * 60)
    print("绩效分析")
    print("=" * 60)
    
    analyzer = PerformanceReport(result)
    analyzer.print_report()
    
    print("\n" + "=" * 60)
    print("✓ 回测完成！")
    print("=" * 60)
    
    return result


def test_indicators():
    """测试技术指标"""
    print("\n" + "=" * 60)
    print("技术指标测试")
    print("=" * 60)
    
    # 生成测试数据
    prices = [10.0 + i * 0.1 for i in range(30)]
    
    # 测试 MA
    ma_5 = ma(prices, 5)
    print(f"\nMA(5): 最后 5 个值 = {[f'{x:.2f}' for x in ma_5[-5:]]}")
    
    # 测试 EMA
    ema_12 = ema(prices, 12)
    print(f"EMA(12): 最后 5 个值 = {[f'{x:.2f}' for x in ema_12[-5:]]}")
    
    # 测试 MACD
    macd_result = macd(prices, fast=12, slow=26, signal=9)
    if macd_result['signal']:
        print(f"\nMACD:")
        print(f"  DIF 最后值：{macd_result['macd'][-1]:.2f}")
        print(f"  DEA 最后值：{macd_result['signal'][-1]:.2f}")
        print(f"  柱状图最后值：{macd_result['histogram'][-1]:.2f}")
    else:
        print(f"\nMACD: 数据点不足，无法计算")
    
    # 测试 RSI
    rsi_14 = rsi(prices, 14)
    print(f"\nRSI(14): {rsi_14[-1]:.2f}")
    
    # 测试 BOLL
    boll = bollinger_bands(prices, period=20)
    print(f"\nBOLL(20):")
    print(f"  上轨：{boll['upper'][-1]:.2f}")
    print(f"  中轨：{boll['middle'][-1]:.2f}")
    print(f"  下轨：{boll['lower'][-1]:.2f}")
    
    print("\n[OK] 技术指标测试完成！")


if __name__ == "__main__":
    # 运行回测示例
    result = run_backtest()
    
    # 测试技术指标
    test_indicators()
    
    print("\n" + "=" * 60)
    print("[OK] 所有示例运行完成！")
    print("=" * 60)
