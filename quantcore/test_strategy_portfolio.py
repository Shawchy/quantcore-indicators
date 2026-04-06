"""
多策略组合测试

测试 StrategyPortfolio 的功能：
1. 策略权重配置
2. 资金分配
3. 组合回测
4. 绩效汇总
"""

from datetime import datetime
from quantcore.strategy.base import Strategy
from quantcore.strategy.portfolio import StrategyPortfolio
from quantcore.core import Bar
from quantcore.indicators import ma


class MACDStrategy(Strategy):
    """简单的 MACD 趋势策略"""
    
    def __init__(self, fast_period: int = 12, slow_period: int = 26, signal_period: int = 9):
        super().__init__()
        self.fast_period = fast_period
        self.slow_period = slow_period
        self.signal_period = signal_period
        self.position = 0
        self.prices = []
    
    def on_init(self, engine):
        super().on_init(engine)
        from quantcore.logger import get_logger
        self.logger = get_logger("QuantCore.MACDStrategy")
    
    def on_bar(self, bar, engine):
        # 累积价格数据
        self.prices.append(bar.close)
        
        if len(self.prices) < self.slow_period:
            return
        
        # 计算 MACD
        from quantcore.indicators import macd
        macd_result = macd(self.prices, self.fast_period, self.slow_period, self.signal_period)
        macd_value = macd_result['macd'][-1] if isinstance(macd_result['macd'], list) else macd_result['macd']
        
        # 交易信号
        if macd_value > 0 and self.position == 0:
            # 金叉买入
            portfolio = engine.get_portfolio()
            available_cash = portfolio.cash * 0.95
            volume = int(available_cash / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"MACD 金叉买入：{volume}股 @ {bar.close:.2f}")
        
        elif macd_value < 0 and self.position > 0:
            # 死叉卖出
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"MACD 死叉卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


class RSIStrategy(Strategy):
    """RSI 超买超卖策略"""
    
    def __init__(self, period: int = 14, oversold: float = 30, overbought: float = 70):
        super().__init__()
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
        self.position = 0
        self.prices = []
    
    def on_init(self, engine):
        super().on_init(engine)
        from quantcore.logger import get_logger
        self.logger = get_logger("QuantCore.RSIStrategy")
    
    def on_bar(self, bar, engine):
        # 简化 RSI 计算
        from quantcore.indicators import rsi
        self.prices.append(bar.close)
        
        if len(self.prices) < self.period + 1:  # RSI 需要 period+1 个数据点
            return
        
        rsi_result = rsi(self.prices, self.period)
        
        if not rsi_result:
            return
        
        rsi_value = rsi_result[-1]
        
        # 交易信号
        if rsi_value < self.oversold and self.position == 0:
            # 超卖买入
            portfolio = engine.get_portfolio()
            available_cash = portfolio.cash * 0.95
            volume = int(available_cash / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"RSI 超卖买入：{volume}股 @ {bar.close:.2f}")
        
        elif rsi_value > self.overbought and self.position > 0:
            # 超买卖出
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"RSI 超买卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


class BOLLStrategy(Strategy):
    """布林带均值回归策略"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        super().__init__()
        self.period = period
        self.std_dev = std_dev
        self.position = 0
        self.prices = []
    
    def on_init(self, engine):
        super().on_init(engine)
        from quantcore.logger import get_logger
        self.logger = get_logger("QuantCore.BOLLStrategy")
    
    def on_bar(self, bar, engine):
        # 简化布林带计算
        from quantcore.indicators import bollinger_bands
        self.prices.append(bar.close)
        
        if len(self.prices) < self.period:
            return
        
        boll_result = bollinger_bands(self.prices, self.period, self.std_dev)
        upper = boll_result['upper'][-1] if isinstance(boll_result['upper'], list) else boll_result['upper']
        lower = boll_result['lower'][-1] if isinstance(boll_result['lower'], list) else boll_result['lower']
        middle = boll_result['middle'][-1] if isinstance(boll_result['middle'], list) else boll_result['middle']
        
        # 交易信号
        if bar.close < lower and self.position == 0:
            # 触及下轨买入
            portfolio = engine.get_portfolio()
            available_cash = portfolio.cash * 0.95
            volume = int(available_cash / bar.close / 100) * 100
            if volume >= 100:
                self.buy(bar.symbol, bar.close, volume, order_type="market")
                self.position = volume
                self.logger.info(f"布林带下轨买入：{volume}股 @ {bar.close:.2f}")
        
        elif bar.close > middle and self.position > 0:
            # 回归中轨卖出
            self.sell(bar.symbol, bar.close, self.position, order_type="market")
            self.logger.info(f"布林带中轨卖出：{self.position}股 @ {bar.close:.2f}")
            self.position = 0


def generate_test_data(days: int = 100) -> list:
    """生成测试用的 K 线数据"""
    import random
    bars = []
    base_price = 10.0
    
    for i in range(days):
        # 生成有趋势的价格
        trend = (i % 20 - 10) * 0.05  # 周期性趋势
        noise = random.uniform(-0.02, 0.02)
        price = base_price * (1 + trend + noise)
        
        bar = Bar(
            timestamp=datetime(2024, 1, 1 + i // 24, i % 24, 0),
            symbol="SH.600000",
            open=price,
            high=price * 1.03,
            low=price * 0.97,
            close=price,
            volume=1000000,
            turnover=price * 1000000
        )
        bars.append(bar)
    
    return bars


def test_basic_portfolio():
    """测试基本的多策略组合功能"""
    print("\n" + "="*60)
    print("测试 1: 基本的多策略组合")
    print("="*60)
    
    # 创建组合
    portfolio = StrategyPortfolio(initial_capital=1000000)
    
    # 添加策略
    portfolio.add_strategy("MACD", MACDStrategy(), weight=0.4)
    portfolio.add_strategy("RSI", RSIStrategy(), weight=0.3)
    portfolio.add_strategy("BOLL", BOLLStrategy(), weight=0.3)
    
    # 生成数据
    bars = generate_test_data(100)
    
    # 运行回测
    result = portfolio.run(bars, tplus1=True)
    
    # 打印结果
    portfolio.print_summary()
    
    # 验证结果
    assert 'total_return' in result
    assert 'sharpe_ratio' in result
    assert 'max_drawdown' in result
    assert result['num_strategies'] == 3
    
    print("\n[PASSED] 测试 1 通过：基本的多策略组合功能正常")
    return result


def test_strategy_weights():
    """测试策略权重配置"""
    print("\n" + "="*60)
    print("测试 2: 策略权重配置")
    print("="*60)
    
    portfolio = StrategyPortfolio(initial_capital=500000)
    
    # 添加不同权重的策略
    portfolio.add_strategy("Strategy_A", MACDStrategy(), weight=0.5)
    portfolio.add_strategy("Strategy_B", RSIStrategy(), weight=0.3)
    portfolio.add_strategy("Strategy_C", BOLLStrategy(), weight=0.2)
    
    # 验证权重
    total_weight = sum(s.weight for s in portfolio.strategies.values())
    print(f"总权重：{total_weight:.2%}")
    assert abs(total_weight - 1.0) < 0.001, "权重之和应等于 1"
    
    # 验证资金分配
    for name, config in portfolio.strategies.items():
        expected_capital = portfolio.initial_capital * config.weight
        print(f"{name}: 权重={config.weight:.2%}, 分配资金={config.capital_allocation:.2f}")
        assert abs(config.capital_allocation - expected_capital) < 0.01
    
    print("\n[PASSED] 测试 2 通过：策略权重配置正确")


def test_enable_disable_strategy():
    """测试启用/禁用策略"""
    print("\n" + "="*60)
    print("测试 3: 启用/禁用策略")
    print("="*60)
    
    portfolio = StrategyPortfolio(initial_capital=300000)
    portfolio.add_strategy("MACD", MACDStrategy(), weight=0.4)
    portfolio.add_strategy("RSI", RSIStrategy(), weight=0.3)
    portfolio.add_strategy("BOLL", BOLLStrategy(), weight=0.3)
    
    # 禁用一个策略
    portfolio.disable_strategy("RSI")
    assert portfolio.strategies["RSI"].enabled == False
    
    # 运行回测（只运行 2 个策略）
    bars = generate_test_data(50)
    result = portfolio.run(bars, tplus1=False)
    
    print(f"运行策略数：{result['num_strategies']}")
    assert result['num_strategies'] == 2, "应只运行 2 个启用的策略"
    
    # 重新启用
    portfolio.enable_strategy("RSI")
    assert portfolio.strategies["RSI"].enabled == True
    
    print("\n[PASSED] 测试 3 通过：启用/禁用策略功能正常")


def test_single_strategy():
    """测试单策略组合（权重=1）"""
    print("\n" + "="*60)
    print("测试 4: 单策略组合")
    print("="*60)
    
    portfolio = StrategyPortfolio(initial_capital=200000)
    portfolio.add_strategy("MACD_Only", MACDStrategy(), weight=1.0)
    
    bars = generate_test_data(60)
    result = portfolio.run(bars, tplus1=True)
    
    print(f"单策略收益：{result['total_return']:.2%}")
    assert result['num_strategies'] == 1
    
    print("\n[PASSED] 测试 4 通过：单策略组合功能正常")


def test_portfolio_daily_values():
    """测试组合每日资产值"""
    print("\n" + "="*60)
    print("测试 5: 组合每日资产值")
    print("="*60)
    
    portfolio = StrategyPortfolio(initial_capital=100000)
    portfolio.add_strategy("MACD", MACDStrategy(), weight=0.5)
    portfolio.add_strategy("RSI", RSIStrategy(), weight=0.5)
    
    bars = generate_test_data(30)
    result = portfolio.run(bars, tplus1=False)
    
    # 检查每日资产值
    daily_values = result['daily_values']
    print(f"初始资产：{daily_values[0]:.2f}")
    print(f"最终资产：{daily_values[-1]:.2f}")
    print(f"数据点数量：{len(daily_values)}")
    
    assert len(daily_values) > 0, "应有每日资产值数据"
    assert daily_values[0] == portfolio.initial_capital, "初始资产应等于初始资金"
    
    print("\n[PASSED] 测试 5 通过：组合每日资产值记录正常")


def test_weight_validation():
    """测试权重验证"""
    print("\n" + "="*60)
    print("测试 6: 权重验证")
    print("="*60)
    
    portfolio = StrategyPortfolio(initial_capital=100000)
    
    # 添加有效权重
    portfolio.add_strategy("S1", MACDStrategy(), weight=0.6)
    portfolio.add_strategy("S2", RSIStrategy(), weight=0.4)
    
    is_valid = portfolio.validate_weights()
    print(f"有效权重验证：{is_valid}")
    assert is_valid == True
    
    # 添加第三个策略（使总权重超过 1）
    portfolio.add_strategy("S3", BOLLStrategy(), weight=0.2)
    
    is_valid = portfolio.validate_weights()
    print(f"无效权重验证：{is_valid}")
    assert is_valid == False
    
    print("\n[PASSED] 测试 6 通过：权重验证功能正常")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("多策略组合功能测试")
    print("="*60)
    
    tests = [
        test_basic_portfolio,
        test_strategy_weights,
        test_enable_disable_strategy,
        test_single_strategy,
        test_portfolio_daily_values,
        test_weight_validation,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n[FAILED] 测试失败：{test.__name__}")
            print(f"  错误：{e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"测试完成：{passed} 通过，{failed} 失败")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    
    if success:
        print("\n[PASSED] 所有测试通过！多策略组合功能正常。")
    else:
        print("\n[FAILED] 部分测试失败，请检查错误信息。")
