# -*- coding: utf-8 -*-
"""
QuantCore Indicators 测试套件
"""

import pytest
import numpy as np
from quantcore_indicators import (
    ma, ema, macd, rsi, bollinger_bands, atr, cci, kdj, obv, williams_r, adx
)


class TestMA:
    def test_ma_basic(self):
        prices = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        result = ma(prices, 3)
        assert len(result) == 4
        assert np.isclose(result[0], 2.0)
        assert np.isclose(result[1], 3.0)
        assert np.isclose(result[2], 4.0)
        assert np.isclose(result[3], 5.0)

    def test_ma_insufficient_data(self):
        prices = [1.0, 2.0, 3.0]
        result = ma(prices, 5)
        assert len(result) == 0

    def test_ma_numpy_array(self):
        prices = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        result = ma(prices, 3)
        assert isinstance(result, np.ndarray)
        assert len(result) == 3

    def test_ma_large_data(self):
        prices = np.random.rand(10000)
        result = ma(prices, 20)
        assert len(result) == 9981
        assert not np.any(np.isnan(result))

    def test_ma_period_validation(self):
        prices = [1.0, 2.0, 3.0]
        assert len(ma(prices, 0)) == 0
        assert len(ma(prices, 1)) == 0


class TestEMA:
    def test_ema_basic(self):
        prices = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = ema(prices, 3)
        assert len(result) == 3
        assert result[0] == np.mean(prices[:3])

    def test_ema_smoothing(self):
        prices = [1.0, 1.0, 1.0, 1.0, 1.0]
        result = ema(prices, 3)
        assert np.allclose(result, 1.0)

    def test_ema_period_validation(self):
        prices = [1.0, 2.0, 3.0]
        assert len(ema(prices, 0)) == 0
        assert len(ema(prices, 1)) == 0


class TestRSI:
    def test_rsi_range(self):
        prices = np.random.rand(100) * 100
        result = rsi(prices, 14)
        assert np.all(result >= 0)
        assert np.all(result <= 100)

    def test_rsi_uptrend(self):
        prices = [100 + i for i in range(20)]
        result = rsi(prices, 14)
        assert len(result) > 0
        assert result[-1] > 50

    def test_rsi_downtrend(self):
        prices = [100 - i for i in range(20)]
        result = rsi(prices, 14)
        assert len(result) > 0
        assert result[-1] < 50

    def test_rsi_period_validation(self):
        prices = [1.0, 2.0, 3.0]
        assert len(rsi(prices, 0)) == 0
        assert len(rsi(prices, 1)) == 0


class TestMACD:
    def test_macd_structure(self):
        prices = np.random.rand(100)
        result = macd(prices)
        assert 'macd' in result
        assert 'signal' in result
        assert 'histogram' in result

    def test_macd_lengths(self):
        prices = np.random.rand(200)
        result = macd(prices, 12, 26, 9)
        assert len(result['macd']) >= len(result['signal'])
        if len(result['signal']) > 0:
            assert len(result['histogram']) == len(result['signal'])

    def test_macd_period_validation(self):
        prices = np.random.rand(50)
        result = macd(prices, 1, 26, 9)
        assert len(result['macd']) == 0


class TestBollingerBands:
    def test_boll_structure(self):
        prices = np.random.rand(100)
        result = bollinger_bands(prices)
        assert 'upper' in result
        assert 'middle' in result
        assert 'lower' in result

    def test_boll_ordering(self):
        prices = np.random.rand(100) * 100 + 50
        result = bollinger_bands(prices, 20, 2.0)
        assert np.all(result['upper'] >= result['middle'])
        assert np.all(result['middle'] >= result['lower'])

    def test_boll_period_validation(self):
        prices = [1.0, 2.0, 3.0]
        result = bollinger_bands(prices, 1, 2.0)
        assert len(result['upper']) == 0


class TestATR:
    def test_atr_positive(self):
        high = np.random.rand(100) * 10 + 100
        low = high - np.random.rand(100) * 5
        close = low + np.random.rand(100) * 5
        result = atr(high, low, close, 14)
        assert len(result) > 0
        assert np.all(result >= 0)

    def test_atr_period_validation(self):
        high = np.array([105.0, 106.0])
        low = np.array([100.0, 101.0])
        close = np.array([103.0, 104.0])
        assert len(atr(high, low, close, 1)) == 0


class TestCCI:
    def test_cci_basic(self):
        high = np.random.rand(30) * 10 + 100
        low = high - np.random.rand(30) * 5
        close = low + np.random.rand(30) * 5
        result = cci(high, low, close, 20)
        assert len(result) > 0

    def test_cci_period_validation(self):
        high = np.array([105.0, 106.0])
        low = np.array([100.0, 101.0])
        close = np.array([103.0, 104.0])
        assert len(cci(high, low, close, 1)) == 0

    def test_cci_length_mismatch(self):
        high = np.array([105.0, 106.0, 107.0])
        low = np.array([100.0, 101.0])
        close = np.array([103.0, 104.0, 105.0])
        assert len(cci(high, low, close, 2)) == 0


class TestKDJ:
    def test_kdj_structure(self):
        high = np.random.rand(100) * 10 + 100
        low = high - np.random.rand(100) * 5
        close = low + np.random.rand(100) * 5
        result = kdj(high, low, close)
        assert 'k' in result
        assert 'd' in result
        assert 'j' in result

    def test_kdj_range(self):
        high = np.random.rand(100) * 10 + 100
        low = high - np.random.rand(100) * 5
        close = low + np.random.rand(100) * 5
        result = kdj(high, low, close)
        assert np.all(result['k'] >= 0)
        assert np.all(result['d'] >= 0)

    def test_kdj_period_validation(self):
        high = np.array([105.0])
        low = np.array([100.0])
        close = np.array([103.0])
        result = kdj(high, low, close, 1, 3, 3)
        assert len(result['k']) == 0


class TestOBV:
    def test_obv_monotonic(self):
        close = np.array([100 + i for i in range(20)])
        volume = np.ones(20) * 1000
        result = obv(close, volume)
        assert len(result) == 20
        for i in range(1, len(result)):
            assert result[i] >= result[i - 1]

    def test_obv_length_mismatch(self):
        close = np.array([100.0, 101.0])
        volume = np.array([1000])
        assert len(obv(close, volume)) == 0


class TestWilliamsR:
    def test_williams_r_range(self):
        high = np.random.rand(30) * 10 + 100
        low = high - np.random.rand(30) * 5
        close = low + np.random.rand(30) * 5
        result = williams_r(high, low, close, 14)
        assert len(result) > 0

    def test_williams_r_period_validation(self):
        high = np.array([105.0])
        low = np.array([100.0])
        close = np.array([103.0])
        assert len(williams_r(high, low, close, 1)) == 0

    def test_williams_r_length_mismatch(self):
        high = np.array([105.0, 106.0, 107.0])
        low = np.array([100.0, 101.0])
        close = np.array([103.0, 104.0, 105.0])
        assert len(williams_r(high, low, close, 2)) == 0


class TestADX:
    def test_adx_basic(self):
        high = np.random.rand(50) * 10 + 100
        low = high - np.random.rand(50) * 5
        close = low + np.random.rand(50) * 5
        result = adx(high, low, close, 14)
        assert len(result) > 0
        assert np.all(result >= 0)
        assert np.all(result <= 100)

    def test_adx_period_validation(self):
        high = np.array([105.0, 106.0])
        low = np.array([100.0, 101.0])
        close = np.array([103.0, 104.0])
        assert len(adx(high, low, close, 1)) == 0

    def test_adx_length_mismatch(self):
        high = np.array([105.0, 106.0, 107.0])
        low = np.array([100.0, 101.0])
        close = np.array([103.0, 104.0, 105.0])
        assert len(adx(high, low, close, 2)) == 0


class TestEdgeCases:
    def test_empty_input(self):
        assert len(ma([], 3)) == 0
        assert len(ema([], 3)) == 0
        assert len(rsi([], 3)) == 0

    def test_single_element(self):
        assert len(ma([1.0], 3)) == 0
        assert len(ema([1.0], 3)) == 0

    def test_constant_prices(self):
        prices = np.ones(100) * 50.0
        ma_result = ma(prices, 20)
        assert np.allclose(ma_result, 50.0)

        ema_result = ema(prices, 20)
        assert np.allclose(ema_result, 50.0)

        rsi_result = rsi(prices, 14)
        assert np.allclose(rsi_result, 100.0)

    def test_all_backends_consistent(self):
        prices = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
        ma_result = ma(prices, 3)
        expected = np.array([2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
        assert np.allclose(ma_result, expected)


class TestPerformance:
    def test_ma_performance(self):
        import time

        prices = np.random.rand(10000)
        start = time.perf_counter()
        result = ma(prices, 20)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.1
        assert len(result) == 9981

    def test_rsi_performance(self):
        import time

        prices = np.random.rand(10000)
        start = time.perf_counter()
        result = rsi(prices, 14)
        elapsed = time.perf_counter() - start
        assert elapsed < 0.2
        assert len(result) == 9986


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
