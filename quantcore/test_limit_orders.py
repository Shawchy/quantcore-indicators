"""
限价单测试

测试限价单的撮合功能
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-api'))

from quantcore import Strategy, BacktestEngine, BacktestConfig, StrategyRunner, Bar
from datetime import datetime, timedelta


class LimitOrderStrategy(Strategy):
    """限价单测试策略"""
    
    def __init__(self):
        super().__init__()
        self.name = "LimitOrder"
        self.buy_price = None
        self.sell_price = None
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = self.engine.logger
        self.logger.info("限价单策略初始化")
    
    def on_bar(self, bar, engine):
        """使用限价单进行交易"""
        # 第一天：设置买入限价单（低于当前价）
        if len(engine.trades) == 0:
            self.buy_price = bar.close * 0.98  # 低于市价 2%
            self.logger.info(f"提交买入限价单：价格={self.buy_price:.2f}, 当前价={bar.close:.2f}")
            self.buy(bar.symbol, self.buy_price, 1000, order_type="limit")
        
        # 如果有持仓，设置卖出限价单（高于成本价）
        if self.has_position(bar.symbol):
            position = self.get_position(bar.symbol)
            self.sell_price = position.cost_price * 1.05  # 高于成本 5%
            self.logger.info(f"提交卖出限价单：价格={self.sell_price:.2f}, 成本={position.cost_price:.2f}")
            self.sell(bar.symbol, self.sell_price, 1000, order_type="limit")


class MixedOrderStrategy(Strategy):
    """混合订单策略（市价 + 限价）"""
    
    def __init__(self):
        super().__init__()
        self.name = "MixedOrder"
    
    def on_init(self, engine):
        super().on_init(engine)
        self.logger = self.engine.logger
        self.logger.info("混合订单策略初始化")
    
    def on_bar(self, bar, engine):
        """混合使用市价单和限价单"""
        if len(engine.trades) == 0:
            # 使用市价单快速买入
            self.logger.info(f"提交买入市价单：当前价={bar.close:.2f}")
            self.buy(bar.symbol, bar.close, 1000, order_type="market")
        
        # 如果有持仓，使用限价单卖出
        if self.has_position(bar.symbol) and len(engine.trades) == 1:
            position = self.get_position(bar.symbol)
            limit_price = position.cost_price * 1.03  # 高于成本 3%
            self.logger.info(f"提交卖出限价单：价格={limit_price:.2f}")
            self.sell(bar.symbol, limit_price, 1000, order_type="limit")


def generate_test_data(days: int = 30):
    """生成测试数据（带有波动）"""
    bars = []
    base_price = 10.0
    
    for i in range(days):
        # 创建有波动的价格
        if i < 10:
            # 上涨趋势
            price = base_price + i * 0.1
        elif i < 20:
            # 下跌趋势
            price = base_price + 1.0 - (i - 10) * 0.15
        else:
            # 震荡
            price = base_price - 0.5 + ((i - 20) % 5) * 0.1
        
        bar = Bar(
            timestamp=datetime(2024, 1, 1) + timedelta(days=i),
            symbol="SH.600000",
            open=price,
            high=price * 1.02,  # 2% 振幅
            low=price * 0.98,   # 2% 振幅
            close=price * (1 + ((i % 3) - 1) * 0.01),
            volume=1000000,
            turnover=price * 1000000
        )
        bars.append(bar)
    
    return bars


def test_limit_orders():
    """测试限价单"""
    print("\n" + "="*60)
    print("测试限价单策略")
    print("="*60)
    
    # 生成数据
    bars = generate_test_data(30)
    
    # 打印价格范围
    print(f"\n数据范围：{bars[0].timestamp.date()} - {bars[-1].timestamp.date()}")
    print(f"最高价：{max(b.high for b in bars):.2f}")
    print(f"最低价：{min(b.low for b in bars):.2f}")
    
    # 创建策略
    strategy = LimitOrderStrategy()
    
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
    print(f"  持仓：{result.positions}")
    
    # 打印订单详情
    if engine.orders:
        print(f"\n订单详情:")
        for order in engine.orders:
            print(f"  {order.order_id}: {order.side.value} {order.order_type.value} "
                  f"{order.quantity} @ {order.price:.2f} - {order.status.value}")
    
    return result


def test_mixed_orders():
    """测试混合订单"""
    print("\n" + "="*60)
    print("测试混合订单策略")
    print("="*60)
    
    # 生成数据
    bars = generate_test_data(30)
    
    # 创建策略
    strategy = MixedOrderStrategy()
    
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
    print("QuantCore 限价单测试")
    print("="*60)
    
    # 测试限价单
    limit_result = test_limit_orders()
    
    # 测试混合订单
    mixed_result = test_mixed_orders()
    
    print("\n" + "="*60)
    print("所有测试完成！")
    print("="*60)
