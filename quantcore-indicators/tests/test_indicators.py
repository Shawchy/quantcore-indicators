# -*- coding: utf-8 -*-
"""
QuantCore Indicators 测试套件
"""

import pytest
import numpy as np
from quantcore_indicators import ma, ema, macd, rsi, bollinger_bands, atr, kdj, obv


class TestMA:
    """MA 指标测试"""
    
    def test_ma_basic(self):
        """测试基本 MA 计算"""
        prices = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        result = ma(prices, 3)
        
        assert len(result) == 4
        assert np.isclose(result[0], 2.0)
        assert np.isclose(result[1], 3.0)
        assert np.isclose(result[2], 4.0)
        assert np.isclose(result[3], 5.0)
    
    def test_ma_insufficient_data(self):
        """测试数据不足情况"""
        prices = [1.0, 2.0, 3.0]
        result = ma(prices, 5)
        
        assert len(result) == 0
    
    def test_ma_numpy_array(self):
        """测试 numpy 数组输入"""
        prices = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = ma(prices, 3)
        
        assert isinstance(result, np.ndarray)
        assert len(result) == 3
    
    def test_ma_large_data(self):
        """测试大数据集"""
        prices = np.random.rand(10000)
        result = ma(prices, 20)
        
        assert len(result) == 9981
        assert not np.any(np.isnan(result))


class TestEMA:
    """EMA 指标测试"""
    
    def test_ema_basic(self):
        """测试基本 EMA 计算"""
        prices = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = ema(prices, 3)
        
        assert len(result) == 3
        assert result[0] == np.mean(prices[:3])
    
    def test_ema_smoothing(self):
        """测试 EMA 平滑效果"""
        prices = [1.0, 1.0, 1.0, 1.0, 1.0]
        result = ema(prices, 3)
        
        # 所有值应该相同
        assert np.allclose(result, 1.0)


class TestRSI:
    """RSI 指标测试"""
    
    def test_rsi_range(self):
        """测试 RSI 范围（0-100）"""
        prices = np.random.rand(100) * 100
        result = rsi(prices, 14)
        
        assert np.all(result >= 0)
        assert np.all(result <= 100)
    
    def test_rsi_uptrend(self):
        """测试上涨趋势 RSI"""
        prices = [100 + i for i in range(20)]  # 持续上涨
        result = rsi(prices, 14)
        
        # 上涨趋势 RSI 应该较高
        assert len(result) > 0
        assert result[-1] > 50
    
    def test_rsi_downtrend(self):
        """测试下跌趋势 RSI"""
        prices = [100 - i for i in range(20)]  # 持续下跌
        result = rsi(prices, 14)
        
        # 下跌趋势 RSI 应该较低
        assert len(result) > 0
        assert result[-1] < 50


class TestMACD:
    """MACD 指标测试"""
    
    def test_macd_structure(self):
        """测试 MACD 返回结构"""
        prices = np.random.rand(100)
        result = macd(prices)
        
        assert 'macd' in result
        assert 'signal' in result
        assert 'histogram' in result
    
    def test_macd_lengths(self):
        """测试 MACD 各线长度关系"""
        prices = np.random.rand(200)
        result = macd(prices, 12, 26, 9)
        
        # MACD 线应该最长
        assert len(result['macd']) >= len(result['signal'])
        # 柱状图应该和信号线等长
        if len(result['signal']) > 0:
            assert len(result['histogram']) == len(result['signal'])


class TestBollingerBands:
    """布林带指标测试"""
    
    def test_boll_structure(self):
        """测试布林带返回结构"""
        prices = np.random.rand(100)
        result = bollinger_bands(prices)
        
        assert 'upper' in result
        assert 'middle' in result
        assert 'lower' in result
    
    def test_boll_ordering(self):
        """测试布林带上下轨关系"""
        prices = np.random.rand(100) * 100 + 50
        result = bollinger_bands(prices, 20, 2.0)
        
        # 上轨 > 中轨 > 下轨
        assert np.all(result['upper'] >= result['middle'])
        assert np.all(result['middle'] >= result['lower'])


class TestATR:
    """ATR 指标测试"""
    
    def test_atr_positive(self):
        """测试 ATR 值为正"""
        high = np.random.rand(100) * 10 + 100
        low = high - np.random.rand(100) * 5
        close = low + np.random.rand(100) * 5
        
        result = atr(high, low, close, 14)
        
        assert len(result) > 0
        assert np.all(result >= 0)  # ATR 应该非负


class TestKDJ:
    """KDJ 指标测试"""
    
    def test_kdj_structure(self):
        """测试 KDJ 返回结构"""
        high = np.random.rand(100) * 10 + 100
        low = high - np.random.rand(100) * 5
        close = low + np.random.rand(100) * 5
        
        result = kdj(high, low, close)
        
        assert 'k' in result
        assert 'd' in result
        assert 'j' in result
    
    def test_kdj_range(self):
        """测试 KDJ 范围"""
        high = np.random.rand(100) * 10 + 100
        low = high - np.random.rand(100) * 5
        close = low + np.random.rand(100) * 5
        
        result = kdj(high, low, close)
        
        # K 和 D 应该在 0-100 之间
        assert np.all(result['k'] >= 0)
        assert np.all(result['k'] <= 100)
        assert np.all(result['d'] >= 0)
        assert np.all(result['d'] <= 100)


class TestOBV:
    """OBV 指标测试"""
    
    def test_obv_monotonic(self):
        """测试 OBV 单调性（在特定条件下）"""
        # 如果价格持续上涨，OBV 应该递增
        close = np.array([100 + i for i in range(20)])
        volume = np.ones(20) * 1000
        
        result = obv(close, volume)
        
        assert len(result) == 20
        # 检查 OBV 是否递增
        for i in range(1, len(result)):
            assert result[i] >= result[i-1]


class TestPerformance:
    """性能测试"""
    
    def test_ma_performance(self):
        """测试 MA 性能"""
        import time
        
        prices = np.random.rand(10000)
        
        start = time.time()
        result = ma(prices, 20)
        elapsed = time.time() - start
        
        # 应该在 100ms 内完成
        assert elapsed < 0.1
        assert len(result) == 9981
    
    def test_rsi_performance(self):
        """测试 RSI 性能"""
        import time
        
        prices = np.random.rand(10000)
        
        start = time.time()
        result = rsi(prices, 14)
        elapsed = time.time() - start
        
        # 应该在 200ms 内完成
        assert elapsed < 0.2
        assert len(result) == 9986


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
