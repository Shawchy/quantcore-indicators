"""
QuantCore 示例策略库

包含多种经典量化策略示例：
1. MACD 策略
2. RSI 策略
3. BOLL 布林带策略
4. 多因子策略
5. 趋势跟踪策略
"""

from quantcore import Strategy, ma, macd, rsi, bollinger_bands


class MACDStrategy(Strategy):
    """
    MACD 策略
    
    交易逻辑：
    - DIF 上穿 DEA（金叉）：买入
    - DIF 下穿 DEA（死叉）：卖出
    """
    
    parameters = {
        'fast_period': 12,
        'slow_period': 26,
        'signal_period': 9,
    }
    
    def __init__(self):
        super().__init__()
        self.name = "MACD"
        self.prices = []
        self.position = 0
        self.fast_period = self.parameters['fast_period']
        self.slow_period = self.parameters['slow_period']
        self.signal_period = self.parameters['signal_period']
    
    def on_init(self, engine):
        """初始化"""
        super().on_init(engine)
    
    def on_bar(self, bar, engine):
        """K 线事件处理"""
        self.prices.append(bar.close)
        
        # 等待足够的数据
        if len(self.prices) < self.slow_period + self.signal_period:
            return
        
        # 计算 MACD
        macd_result = macd(
            self.prices,
            fast=self.fast_period,
            slow=self.slow_period,
            signal=self.signal_period
        )
        
        if not macd_result['macd'] or not macd_result['signal']:
            return
        
        # 获取当前和之前的 MACD 值
        dif = macd_result['macd']
        dea = macd_result['signal']
        
        # 判断金叉/死叉
        if len(dif) >= 2 and len(dea) >= 2:
            prev_dif, curr_dif = dif[-2], dif[-1]
            prev_dea, curr_dea = dea[-2], dea[-1]
            
            # 金叉：DIF 从下向上穿越 DEA
            if prev_dif <= prev_dea and curr_dif > curr_dea:
                if self.position == 0:
                    self.buy(bar.symbol, bar.close, 1000)
                    self.position = 1
                    print(f"{bar.timestamp} MACD 金叉买入：{bar.close:.2f}")
            
            # 死叉：DIF 从上向下穿越 DEA
            elif prev_dif >= prev_dea and curr_dif < curr_dea:
                if self.position == 1:
                    self.sell(bar.symbol, bar.close, 1000)
                    self.position = 0
                    print(f"{bar.timestamp} MACD 死叉卖出：{bar.close:.2f}")


class RSIStrategy(Strategy):
    """
    RSI 策略
    
    交易逻辑：
    - RSI < 20（超卖）：买入
    - RSI > 80（超买）：卖出
    """
    
    parameters = {
        'rsi_period': 14,
        'oversold': 20,
        'overbought': 80,
    }
    
    def __init__(self):
        super().__init__()
        self.name = "RSI"
        self.prices = []
        self.position = 0
        self.rsi_period = self.parameters['rsi_period']
        self.oversold = self.parameters['oversold']
        self.overbought = self.parameters['overbought']
    
    def on_init(self, engine):
        """初始化"""
        super().on_init(engine)
    
    def on_bar(self, bar, engine):
        """K 线事件处理"""
        self.prices.append(bar.close)
        
        # 等待足够的数据
        if len(self.prices) < self.rsi_period + 1:
            return
        
        # 计算 RSI
        rsi_values = rsi(self.prices, self.rsi_period)
        
        if not rsi_values or len(rsi_values) < 2:
            return
        
        prev_rsi = rsi_values[-2]
        curr_rsi = rsi_values[-1]
        
        # 超卖买入：RSI 从超卖区回升
        if prev_rsi < self.oversold and curr_rsi >= self.oversold:
            if self.position == 0:
                self.buy(bar.symbol, bar.close, 1000)
                self.position = 1
                print(f"{bar.timestamp} RSI 超卖买入：{curr_rsi:.2f} @ {bar.close:.2f}")
        
        # 超买卖出：RSI 从超买区回落
        elif prev_rsi > self.overbought and curr_rsi <= self.overbought:
            if self.position == 1:
                self.sell(bar.symbol, bar.close, 1000)
                self.position = 0
                print(f"{bar.timestamp} RSI 超买卖出：{curr_rsi:.2f} @ {bar.close:.2f}")


class BOLLStrategy(Strategy):
    """
    布林带策略
    
    交易逻辑：
    - 价格跌破下轨：买入（超卖反弹）
    - 价格突破上轨：卖出（超买回调）
    """
    
    parameters = {
        'period': 20,
        'std_dev': 2.0,
    }
    
    def __init__(self):
        super().__init__()
        self.name = "BOLL"
        self.prices = []
        self.position = 0
        self.period = self.parameters['period']
        self.std_dev = self.parameters['std_dev']
    
    def on_init(self, engine):
        """初始化"""
        super().on_init(engine)
    
    def on_bar(self, bar, engine):
        """K 线事件处理"""
        self.prices.append(bar.close)
        
        # 等待足够的数据
        if len(self.prices) < self.period:
            return
        
        # 计算布林带
        boll = bollinger_bands(self.prices, self.period, self.std_dev)
        
        if not boll['upper'] or not boll['lower']:
            return
        
        upper = boll['upper'][-1]
        lower = boll['lower'][-1]
        middle = boll['middle'][-1]
        
        # 价格跌破下轨：买入信号
        if bar.close < lower and self.position == 0:
            self.buy(bar.symbol, bar.close, 1000)
            self.position = 1
            print(f"{bar.timestamp} BOLL 下轨买入：{bar.close:.2f} < {lower:.2f}")
        
        # 价格突破上轨：卖出信号
        elif bar.close > upper and self.position == 1:
            self.sell(bar.symbol, bar.close, 1000)
            self.position = 0
            print(f"{bar.timestamp} BOLL 上轨卖出：{bar.close:.2f} > {upper:.2f}")
        
        # 价格回归中轨：平仓
        elif self.position == 1:
            # 如果价格从下轨下方回到中轨上方，平仓
            if len(self.prices) >= 2 and self.prices[-2] < lower and bar.close > middle:
                self.sell(bar.symbol, bar.close, 1000)
                self.position = 0
                print(f"{bar.timestamp} BOLL 中轨平仓：{bar.close:.2f} > {middle:.2f}")


class MultiFactorStrategy(Strategy):
    """
    多因子策略
    
    结合多个技术指标：
    - MA 趋势
    - MACD 动量
    - RSI 超买超卖
    
    只有当多个因子同时发出信号时才交易
    """
    
    parameters = {
        'ma_period': 20,
        'macd_fast': 12,
        'macd_slow': 26,
        'macd_signal': 9,
        'rsi_period': 14,
    }
    
    def __init__(self):
        super().__init__()
        self.name = "MultiFactor"
        self.prices = []
        self.position = 0
        self.ma_period = self.parameters['ma_period']
        self.macd_fast = self.parameters['macd_fast']
        self.macd_slow = self.parameters['macd_slow']
        self.macd_signal = self.parameters['macd_signal']
        self.rsi_period = self.parameters['rsi_period']
    
    def on_init(self, engine):
        """初始化"""
        super().on_init(engine)
    
    def on_bar(self, bar, engine):
        """K 线事件处理"""
        self.prices.append(bar.close)
        
        # 等待足够的数据
        required_len = self.macd_slow + self.macd_signal + 5
        if len(self.prices) < required_len:
            return
        
        # 1. MA 趋势判断
        ma_value = sum(self.prices[-self.ma_period:]) / self.ma_period
        trend_bullish = bar.close > ma_value
        
        # 2. MACD 动量判断
        macd_result = macd(
            self.prices,
            fast=self.macd_fast,
            slow=self.macd_slow,
            signal=self.macd_signal
        )
        
        if not macd_result['macd'] or len(macd_result['macd']) < 2:
            return
        
        momentum_bullish = macd_result['macd'][-1] > macd_result['signal'][-1]
        
        # 3. RSI 超买超卖判断
        rsi_values = rsi(self.prices, self.rsi_period)
        if not rsi_values or len(rsi_values) < 1:
            return
        
        not_overbought = rsi_values[-1] < 70
        not_oversold = rsi_values[-1] > 30
        
        # 综合判断：多个因子共振
        buy_signal = trend_bullish and momentum_bullish and not_overbought
        sell_signal = (not trend_bullish) or (rsi_values[-1] > 80)
        
        # 执行交易
        if buy_signal and self.position == 0:
            self.buy(bar.symbol, bar.close, 1000)
            self.position = 1
            print(f"{bar.timestamp} 多因子买入：MA={ma_value:.2f}, RSI={rsi_values[-1]:.2f}")
        
        elif sell_signal and self.position == 1:
            self.sell(bar.symbol, bar.close, 1000)
            self.position = 0
            print(f"{bar.timestamp} 多因子卖出：MA={ma_value:.2f}, RSI={rsi_values[-1]:.2f}")


class TrendFollowingStrategy(Strategy):
    """
    趋势跟踪策略
    
    使用双均线 + 通道突破：
    - 快速均线上穿慢速均线，且价格突破 N 日高点：买入
    - 快速均线下穿慢速均线，或价格跌破 N 日低点：卖出
    """
    
    parameters = {
        'fast_period': 10,
        'slow_period': 30,
        'breakout_period': 20,
    }
    
    def __init__(self):
        super().__init__()
        self.name = "TrendFollowing"
        self.prices = []
        self.position = 0
        self.fast_period = self.parameters['fast_period']
        self.slow_period = self.parameters['slow_period']
        self.breakout_period = self.parameters['breakout_period']
    
    def on_init(self, engine):
        """初始化"""
        super().on_init(engine)
    
    def on_bar(self, bar, engine):
        """K 线事件处理"""
        self.prices.append(bar.close)
        
        # 等待足够的数据
        if len(self.prices) < self.slow_period + self.breakout_period:
            return
        
        # 计算双均线
        fast_ma = sum(self.prices[-self.fast_period:]) / self.fast_period
        slow_ma = sum(self.prices[-self.slow_period:]) / self.slow_period
        
        # 计算之前的均线
        prev_fast_ma = sum(self.prices[-self.fast_period-1:-1]) / self.fast_period
        prev_slow_ma = sum(self.prices[-self.slow_period-1:-1]) / self.slow_period
        
        # 计算 N 日高低点
        high_prices = [bar.high] if hasattr(bar, 'high') else self.prices[-self.breakout_period:]
        low_prices = [bar.low] if hasattr(bar, 'low') else self.prices[-self.breakout_period:]
        
        # 如果没有 high/low 数据，使用 close 代替
        if len(self.prices) >= self.breakout_period:
            period_prices = self.prices[-self.breakout_period:]
            highest = max(period_prices)
            lowest = min(period_prices)
        else:
            highest = max(self.prices)
            lowest = min(self.prices)
        
        # 买入信号：金叉 + 突破
        if prev_fast_ma <= prev_slow_ma and fast_ma > slow_ma:
            if bar.close >= highest and self.position == 0:
                self.buy(bar.symbol, bar.close, 1000)
                self.position = 1
                print(f"{bar.timestamp} 趋势突破买入：{bar.close:.2f} >= {highest:.2f}")
        
        # 卖出信号：死叉 或 跌破低点
        sell_signal = False
        
        if prev_fast_ma >= prev_slow_ma and fast_ma < slow_ma:
            sell_signal = True
            print(f"{bar.timestamp} 均线死叉卖出")
        
        if self.position == 1 and bar.close < lowest:
            sell_signal = True
            print(f"{bar.timestamp} 跌破低点卖出：{bar.close:.2f} < {lowest:.2f}")
        
        if sell_signal:
            self.sell(bar.symbol, bar.close, 1000)
            self.position = 0


# 策略工厂函数
def create_strategy(name: str, **kwargs) -> Strategy:
    """
    策略工厂函数
    
    Args:
        name: 策略名称
        **kwargs: 策略参数
        
    Returns:
        Strategy 实例
    """
    strategies = {
        'macd': MACDStrategy,
        'rsi': RSIStrategy,
        'boll': BOLLStrategy,
        'multi_factor': MultiFactorStrategy,
        'trend_following': TrendFollowingStrategy,
    }
    
    if name.lower() not in strategies:
        raise ValueError(f"Unknown strategy: {name}")
    
    strategy = strategies[name.lower()]()
    
    # 更新参数
    if kwargs:
        strategy.parameters.update(kwargs)
    
    return strategy


# 便捷函数
def get_all_strategies() -> dict:
    """获取所有可用策略"""
    return {
        'macd': MACDStrategy,
        'rsi': RSIStrategy,
        'boll': BOLLStrategy,
        'multi_factor': MultiFactorStrategy,
        'trend_following': TrendFollowingStrategy,
    }
