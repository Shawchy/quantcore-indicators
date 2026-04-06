# -*- coding: utf-8 -*-
"""
可视化功能测试

测试 plotting 模块的各项功能
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-api'))

from datetime import datetime
import random
from quantcore.strategy.base import Strategy
from quantcore.strategy.portfolio import StrategyPortfolio
from quantcore.core import Bar
from quantcore.plotting import (
    plot_equity_curve,
    plot_drawdown_curve,
    plot_return_distribution,
    plot_monthly_returns,
    plot_all_charts
)


class SimpleTestStrategy(Strategy):
    """简单测试策略"""
    
    def __init__(self):
        super().__init__()
        self.position = 0
        self.prices = []
    
    def on_init(self, engine):
        super().on_init(engine)
        from quantcore.logger import get_logger
        self.logger = get_logger("QuantCore.SimpleTestStrategy")
    
    def on_bar(self, bar, engine):
        self.prices.append(bar.close)
        
        if len(self.prices) < 20:
            return
        
        # 简单均线策略
        from quantcore.indicators import ma
        ma_values = ma(self.prices, 20)
        
        if not ma_values:
            return
        
        ma20 = ma_values[-1]
        
        if bar.close > ma20 * 1.02 and self.position == 0:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"买入：{volume}股 @ {bar.close:.2f}")
        
        elif bar.close < ma20 * 0.98 and self.position > 0:
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


def generate_test_data(days: int = 252) -> list:
    """生成测试数据"""
    from datetime import timedelta
    
    bars = []
    base_price = 100.0
    
    # 生成有趋势和波动的价格
    trend = 0.0003  # 每日平均涨幅
    volatility = 0.02  # 日波动率
    
    price = base_price
    start_date = datetime(2024, 1, 1)
    
    for i in range(days):
        # 随机游走 + 趋势
        daily_return = random.gauss(trend, volatility)
        price = price * (1 + daily_return)
        
        # 生成 OHLC
        open_price = price
        close_price = price * (1 + random.gauss(0, 0.01))
        high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, 0.01)))
        low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, 0.01)))
        
        current_date = start_date + timedelta(days=i)
        
        bar = Bar(
            timestamp=current_date,
            symbol="SH.000001",
            open=open_price,
            high=high_price,
            low=low_price,
            close=close_price,
            volume=int(1000000 * (1 + random.gauss(0, 0.2))),
            turnover=close_price * 1000000
        )
        bars.append(bar)
    
    return bars


def test_single_plot():
    """测试单个图表绘制"""
    print("\n" + "="*70)
    print("测试 1: 单个图表绘制")
    print("="*70)
    
    # 运行策略获取结果
    portfolio = StrategyPortfolio(initial_capital=1000000)
    portfolio.add_strategy("Simple", SimpleTestStrategy(), weight=1.0)
    
    bars = generate_test_data(252)
    result = portfolio.run(bars, tplus1=True)
    
    daily_values = result['daily_values']
    initial_capital = result['total_initial_capital']
    
    print(f"\n数据点数：{len(daily_values)}")
    print(f"初始资金：{initial_capital:,.2f}")
    print(f"最终资金：{result['total_final_capital']:,.2f}")
    print(f"总收益：{result['total_return']:.2%}")
    
    # 1. 资金曲线图
    print("\n绘制资金曲线图...")
    try:
        plot_equity_curve(
            daily_values=daily_values,
            initial_capital=initial_capital,
            title="测试策略 - 资金曲线",
            show=False  # 不显示，只保存
        )
        print("✓ 资金曲线图绘制成功")
    except Exception as e:
        print(f"✗ 资金曲线图绘制失败：{e}")
    
    # 2. 回撤曲线图
    print("\n绘制回撤曲线图...")
    try:
        plot_drawdown_curve(
            daily_values=daily_values,
            title="测试策略 - 回撤分析",
            show=False
        )
        print("✓ 回撤曲线图绘制成功")
    except Exception as e:
        print(f"✗ 回撤曲线图绘制失败：{e}")
    
    # 3. 收益分布图
    print("\n绘制收益分布图...")
    try:
        plot_return_distribution(
            daily_values=daily_values,
            title="测试策略 - 收益分布",
            show=False
        )
        print("✓ 收益分布图绘制成功")
    except Exception as e:
        print(f"✗ 收益分布图绘制失败：{e}")
    
    # 4. 月度收益图
    print("\n绘制月度收益图...")
    try:
        plot_monthly_returns(
            daily_values=daily_values,
            initial_capital=initial_capital,
            title="测试策略 - 月度收益",
            show=False
        )
        print("✓ 月度收益图绘制成功")
    except Exception as e:
        print(f"✗ 月度收益图绘制失败：{e}")
    
    print("\n[PASSED] 单个图表绘制测试完成")
    return result


def test_save_to_file():
    """测试保存到文件"""
    print("\n" + "="*70)
    print("测试 2: 保存到文件")
    print("="*70)
    
    # 创建测试输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 运行策略
    portfolio = StrategyPortfolio(initial_capital=500000)
    portfolio.add_strategy("Simple", SimpleTestStrategy(), weight=1.0)
    
    bars = generate_test_data(252)
    result = portfolio.run(bars, tplus1=True)
    
    daily_values = result['daily_values']
    initial_capital = result['total_initial_capital']
    
    # 保存图表到文件
    print(f"\n保存图表到：{output_dir}")
    
    try:
        plot_equity_curve(
            daily_values=daily_values,
            initial_capital=initial_capital,
            title="保存测试 - 资金曲线",
            save_path=os.path.join(output_dir, "equity_curve.png"),
            show=False
        )
        print("✓ 资金曲线图已保存")
    except Exception as e:
        print(f"✗ 保存失败：{e}")
    
    try:
        plot_drawdown_curve(
            daily_values=daily_values,
            title="保存测试 - 回撤分析",
            save_path=os.path.join(output_dir, "drawdown_curve.png"),
            show=False
        )
        print("✓ 回撤曲线图已保存")
    except Exception as e:
        print(f"✗ 保存失败：{e}")
    
    try:
        plot_return_distribution(
            daily_values=daily_values,
            title="保存测试 - 收益分布",
            save_path=os.path.join(output_dir, "return_distribution.png"),
            show=False
        )
        print("✓ 收益分布图已保存")
    except Exception as e:
        print(f"✗ 保存失败：{e}")
    
    # 检查文件是否存在
    print("\n检查保存的文件:")
    files = ["equity_curve.png", "drawdown_curve.png", "return_distribution.png"]
    for file in files:
        file_path = os.path.join(output_dir, file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {file} ({size:,} bytes)")
        else:
            print(f"  ✗ {file} (不存在)")
    
    print("\n[PASSED] 保存到文件测试完成")


def test_all_charts():
    """测试综合图表生成"""
    print("\n" + "="*70)
    print("测试 3: 综合图表生成")
    print("="*70)
    
    # 创建输出目录
    output_dir = os.path.join(os.path.dirname(__file__), "test_output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 运行策略
    portfolio = StrategyPortfolio(initial_capital=1000000)
    portfolio.add_strategy("Simple", SimpleTestStrategy(), weight=1.0)
    
    bars = generate_test_data(252)
    result = portfolio.run(bars, tplus1=True)
    
    print("\n生成所有图表...")
    try:
        plot_all_charts(
            result=result,
            title="综合测试",
            save_dir=output_dir,
            show=False
        )
        print("✓ 所有图表生成成功")
    except Exception as e:
        print(f"✗ 图表生成失败：{e}")
        import traceback
        traceback.print_exc()
    
    # 检查生成的文件
    print("\n检查生成的文件:")
    files = [
        "equity_curve.png",
        "drawdown_curve.png",
        "return_distribution.png",
        "monthly_returns.png"
    ]
    
    all_exist = True
    for file in files:
        file_path = os.path.join(output_dir, file)
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"  ✓ {file} ({size:,} bytes)")
        else:
            print(f"  ✗ {file} (不存在)")
            all_exist = False
    
    if all_exist:
        print(f"\n[PASSED] 综合图表生成测试完成")
        print(f"所有图表已保存到：{output_dir}")
    else:
        print("\n[FAILED] 部分文件未生成")


def test_with_benchmark():
    """测试带基准对比的图表"""
    print("\n" + "="*70)
    print("测试 4: 带基准对比")
    print("="*70)
    
    # 运行策略
    portfolio = StrategyPortfolio(initial_capital=1000000)
    portfolio.add_strategy("Simple", SimpleTestStrategy(), weight=1.0)
    
    bars = generate_test_data(252)
    result = portfolio.run(bars, tplus1=True)
    
    daily_values = result['daily_values']
    initial_capital = result['total_initial_capital']
    
    # 生成基准数据（简单买入持有）
    benchmark_values = []
    base_price = bars[0].close
    for bar in bars:
        # 假设初始全仓买入
        shares = initial_capital / base_price
        benchmark_value = shares * bar.close
        benchmark_values.append(benchmark_value)
    
    print(f"\n策略最终资金：{daily_values[-1]:,.2f}")
    print(f"基准最终资金：{benchmark_values[-1]:,.2f}")
    
    strategy_return = (daily_values[-1] - initial_capital) / initial_capital * 100
    benchmark_return = (benchmark_values[-1] - initial_capital) / initial_capital * 100
    
    print(f"策略收益：{strategy_return:.2f}%")
    print(f"基准收益：{benchmark_return:.2f}%")
    print(f"超额收益：{strategy_return - benchmark_return:.2f}%")
    
    # 绘制带基准的资金曲线
    try:
        plot_equity_curve(
            daily_values=daily_values,
            initial_capital=initial_capital,
            title="策略 vs 基准",
            benchmark_values=benchmark_values,
            show=False
        )
        print("\n✓ 基准对比图绘制成功")
        print("[PASSED] 基准对比测试完成")
    except Exception as e:
        print(f"\n✗ 基准对比图绘制失败：{e}")
        print("[FAILED] 基准对比测试失败")


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("可视化功能测试")
    print("="*70)
    
    try:
        # 测试 1: 单个图表绘制
        test_single_plot()
        
        # 测试 2: 保存到文件
        test_save_to_file()
        
        # 测试 3: 综合图表生成
        test_all_charts()
        
        # 测试 4: 带基准对比
        test_with_benchmark()
        
        print("\n" + "="*70)
        print("所有测试完成！")
        print("="*70)
        
    except Exception as e:
        print(f"\n[ERROR] 测试过程中发生错误：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
