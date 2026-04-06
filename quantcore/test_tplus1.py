"""
T+1 交易规则测试

测试 T+1 规则下的交易行为
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-api'))

from quantcore import Strategy, BacktestEngine, BacktestConfig, StrategyRunner, Bar
from datetime import datetime, timedelta


class TPlus1TestStrategy(Strategy):
    """T+1 测试策略：当日买入，尝试当日卖出"""
    
    def __init__(self):
        super().__init__()
        self.name = "TPlus1Test"
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = self.engine.logger
        self.logger.info("T+1 测试策略初始化")
    
    def on_bar(self, bar, engine):
        """测试 T+1 规则"""
        # 第一天：买入
        if len(engine.trades) == 0:
            self.logger.info(f"第 1 天：买入 1000 股 @ {bar.close:.2f}")
            self.buy(bar.symbol, bar.close, 1000, order_type="market")
        
        # 第二天：尝试卖出（应该失败，因为是 T+1）
        elif len(engine.trades) == 1:
            position = self.get_position(bar.symbol)
            self.logger.info(f"第 2 天：持仓={position.quantity}, 可用={position.available_quantity}")
            self.logger.info(f"尝试卖出 1000 股（T+1 应该失败）")
            
            # 尝试卖出，但应该因为 T+1 规则而失败或只能卖出 0 股
            self.sell(bar.symbol, bar.close, 1000, order_type="market")
        
        # 第三天：应该可以卖出
        elif len(engine.trades) == 2:
            position = self.get_position(bar.symbol)
            self.logger.info(f"第 3 天：持仓={position.quantity}, 可用={position.available_quantity}")
            
            if position.available_quantity > 0:
                self.logger.info(f"卖出 {position.available_quantity} 股（T+1 允许）")
                self.sell(bar.symbol, bar.close, position.available_quantity, order_type="market")


class TPlus1NormalStrategy(Strategy):
    """正常的 T+1 策略：今日买入，明日卖出"""
    
    def __init__(self):
        super().__init__()
        self.name = "TPlus1Normal"
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = self.engine.logger
        self.logger.info("正常 T+1 策略初始化")
    
    def on_bar(self, bar, engine):
        """正常的 T+1 交易"""
        # 奇数天买入
        if len(engine.trades) % 2 == 0:
            position = self.get_position(bar.symbol) if self.has_position(bar.symbol) else None
            available = position.available_quantity if position else 0
            
            if available == 0:
                self.logger.info(f"买入 1000 股 @ {bar.close:.2f}")
                self.buy(bar.symbol, bar.close, 1000, order_type="market")
        
        # 偶数天卖出（有可用持仓时）
        else:
            position = self.get_position(bar.symbol)
            if position and position.available_quantity > 0:
                self.logger.info(f"卖出 {position.available_quantity} 股 @ {bar.close:.2f}")
                self.sell(bar.symbol, bar.close, position.available_quantity, order_type="market")


def generate_daily_data(days: int = 10):
    """生成日线数据"""
    bars = []
    base_price = 10.0
    
    for i in range(days):
        # 创建有波动的价格
        price = base_price + (i % 5) * 0.2
        
        bar = Bar(
            timestamp=datetime(2024, 1, 1 + i),  # 每天
            symbol="SH.600000",
            open=price,
            high=price * 1.02,
            low=price * 0.98,
            close=price,
            volume=1000000,
            turnover=price * 1000000
        )
        bars.append(bar)
    
    return bars


def test_tplus1_rule():
    """测试 T+1 规则"""
    print("\n" + "="*60)
    print("测试 T+1 交易规则")
    print("="*60)
    
    # 生成数据
    bars = generate_daily_data(10)
    
    # 创建策略
    strategy = TPlus1TestStrategy()
    
    # 配置回测
    config = BacktestConfig(
        initial_capital=1000000.0,
        commission_rate=0.0003,
        slippage=0.001,
    )
    
    # 创建引擎
    engine = BacktestEngine(config)
    
    # 运行回测
    runner = StrategyRunner(strategy)
    result = runner.run(engine, bars)
    
    # 输出结果
    print(f"\n回测结果:")
    print(f"  初始资金：{result.initial_capital:,.2f}")
    print(f"  最终资金：{result.final_capital:,.2f}")
    print(f"  总收益：{result.total_return*100:.2f}%")
    print(f"  交易次数：{result.total_trades}")
    
    # 打印持仓详情
    if result.positions:
        print(f"\n最终持仓:")
        for symbol, pos in result.positions.items():
            print(f"  {symbol}: {pos.quantity}股 (可用：{pos.available_quantity})")
    
    return result


def test_normal_tplus1():
    """测试正常的 T+1 交易"""
    print("\n" + "="*60)
    print("测试正常 T+1 策略")
    print("="*60)
    
    # 生成数据
    bars = generate_daily_data(10)
    
    # 创建策略
    strategy = TPlus1NormalStrategy()
    
    # 配置回测
    config = BacktestConfig(
        initial_capital=1000000.0,
        commission_rate=0.0003,
        slippage=0.001,
    )
    
    # 创建引擎
    engine = BacktestEngine(config)
    
    # 运行回测
    runner = StrategyRunner(strategy)
    result = runner.run(engine, bars)
    
    # 输出结果
    print(f"\n回测结果:")
    print(f"  初始资金：{result.initial_capital:,.2f}")
    print(f"  最终资金：{result.final_capital:,.2f}")
    print(f"  总收益：{result.total_return*100:.2f}%")
    print(f"  交易次数：{result.total_trades}")
    
    return result


if __name__ == "__main__":
    print("\n" + "="*60)
    print("QuantCore T+1 交易规则测试")
    print("="*60)
    
    # 测试 T+1 规则
    tplus1_result = test_tplus1_rule()
    
    # 测试正常 T+1 策略
    normal_result = test_normal_tplus1()
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)
