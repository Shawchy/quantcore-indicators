# -*- coding: utf-8 -*-
"""
QuantCore Indicators - Python 接口层

高性能金融指标计算库，基于 Rust 实现
"""

from typing import List, Dict, Union, Optional
import numpy as np

# 导入 Rust 扩展模块
try:
    from .quantcore_indicators import (
        ma_py as _ma,
        ema_py as _ema,
        macd_py as _macd,
        rsi_py as _rsi,
        bollinger_bands_py as _bollinger_bands,
        atr_py as _atr,
        cci_py as _cci,
        kdj_py as _kdj,
        obv_py as _obv,
        williams_r_py as _williams_r,
        adx_py as _adx,
    )
    _RUST_AVAILABLE = True
except ImportError:
    _RUST_AVAILABLE = False
    print("警告：Rust 扩展未加载，将使用纯 Python 实现")


ArrayLike = Union[List[float], np.ndarray]


def _to_numpy_array(data: ArrayLike) -> np.ndarray:
    """转换为 numpy 数组"""
    if isinstance(data, np.ndarray):
        return data
    return np.array(data, dtype=np.float64)


def ma(prices: ArrayLike, period: int) -> np.ndarray:
    """
    移动平均线 (Moving Average)
    
    Args:
        prices: 价格序列（列表或 numpy 数组）
        period: 周期
        
    Returns:
        MA 值 numpy 数组
        
    Example:
        >>> from quantcore_indicators import ma
        >>> prices = [1, 2, 3, 4, 5, 6]
        >>> ma(prices, 3)
        array([2., 3., 4., 5.])
    """
    prices = _to_numpy_array(prices)
    
    if _RUST_AVAILABLE:
        return _ma(prices, period)
    else:
        if period < 2 or len(prices) < period:
            return np.array([])
        
        result = []
        for i in range(period - 1, len(prices)):
            avg = np.mean(prices[i - period + 1:i + 1])
            result.append(avg)
        
        return np.array(result)


def ema(prices: ArrayLike, period: int) -> np.ndarray:
    """
    指数移动平均线 (Exponential Moving Average)
    
    Args:
        prices: 价格序列
        period: 周期
        
    Returns:
        EMA 值 numpy 数组
    """
    prices = _to_numpy_array(prices)
    
    if _RUST_AVAILABLE:
        return _ema(prices, period)
    else:
        if period < 2 or len(prices) < period:
            return np.array([])
        
        multiplier = 2 / (period + 1)
        result = [np.mean(prices[:period])]
        
        for i in range(period, len(prices)):
            ema_value = (prices[i] - result[-1]) * multiplier + result[-1]
            result.append(ema_value)
        
        return np.array(result)


def macd(prices: ArrayLike, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, np.ndarray]:
    """
    MACD 指标 (Moving Average Convergence Divergence)
    
    Args:
        prices: 价格序列
        fast: 快线周期，默认 12
        slow: 慢线周期，默认 26
        signal: 信号线周期，默认 9
        
    Returns:
        字典 {'macd': array, 'signal': array, 'histogram': array}
    """
    prices = _to_numpy_array(prices)
    
    if _RUST_AVAILABLE:
        return _macd(prices, fast, slow, signal)
    else:
        if fast < 2 or slow < 2 or signal < 2:
            return {'macd': np.array([]), 'signal': np.array([]), 'histogram': np.array([])}
        
        fast_ema = ema(prices, fast)
        slow_ema = ema(prices, slow)
        
        # 对齐长度
        min_len = min(len(fast_ema), len(slow_ema))
        fast_ema = fast_ema[-min_len:]
        slow_ema = slow_ema[-min_len:]
        
        macd_line = fast_ema - slow_ema
        
        if len(macd_line) >= signal:
            signal_line = ema(macd_line, signal)
            histogram = macd_line[-len(signal_line):] - signal_line
        else:
            signal_line = np.array([])
            histogram = np.array([])
        
        return {
            'macd': macd_line,
            'signal': signal_line,
            'histogram': histogram
        }


def rsi(prices: ArrayLike, period: int = 14) -> np.ndarray:
    """
    RSI 指标 (Relative Strength Index)
    
    Args:
        prices: 价格序列
        period: 周期，默认 14
        
    Returns:
        RSI 值 numpy 数组（0-100）
    """
    prices = _to_numpy_array(prices)
    
    if _RUST_AVAILABLE:
        return _rsi(prices, period)
    else:
        if period < 2 or len(prices) < period + 1:
            return np.array([])
        
        result = []
        for i in range(period, len(prices)):
            gains = []
            losses = []
            
            for j in range(i - period + 1, i + 1):
                change = prices[j] - prices[j - 1]
                if change > 0:
                    gains.append(change)
                    losses.append(0)
                else:
                    gains.append(0)
                    losses.append(abs(change))
            
            avg_gain = np.mean(gains)
            avg_loss = np.mean(losses)
            
            if avg_loss == 0:
                result.append(100.0)
            else:
                rs = avg_gain / avg_loss
                rsi_value = 100 - (100 / (1 + rs))
                result.append(rsi_value)
        
        return np.array(result)


def bollinger_bands(prices: ArrayLike, period: int = 20, std_dev: float = 2.0) -> Dict[str, np.ndarray]:
    """
    布林带指标 (Bollinger Bands)
    
    Args:
        prices: 价格序列
        period: 周期，默认 20
        std_dev: 标准差倍数，默认 2.0
        
    Returns:
        字典 {'upper': array, 'middle': array, 'lower': array}
    """
    prices = _to_numpy_array(prices)
    
    if _RUST_AVAILABLE:
        return _bollinger_bands(prices, period, std_dev)
    else:
        if period < 2:
            return {'upper': np.array([]), 'middle': np.array([]), 'lower': np.array([])}
        
        middle = ma(prices, period)
        upper = []
        lower = []
        
        for i in range(period - 1, len(prices)):
            window = prices[i - period + 1:i + 1]
            mean = np.mean(window)
            std = np.std(window)
            
            upper.append(mean + std_dev * std)
            lower.append(mean - std_dev * std)
        
        return {
            'upper': np.array(upper),
            'middle': middle,
            'lower': np.array(lower)
        }


def atr(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> np.ndarray:
    """
    ATR 指标 (Average True Range)
    
    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: 周期，默认 14
        
    Returns:
        ATR 值 numpy 数组
    """
    high = _to_numpy_array(high)
    low = _to_numpy_array(low)
    close = _to_numpy_array(close)
    
    if _RUST_AVAILABLE:
        return _atr(high, low, close, period)
    else:
        if period < 2 or len(high) < 2 or len(high) != len(low) or len(high) != len(close):
            return np.array([])
        
        tr = []
        for i in range(1, len(high)):
            hl = high[i] - low[i]
            hc = abs(high[i] - close[i - 1])
            lc = abs(low[i] - close[i - 1])
            tr.append(max(hl, hc, lc))
        
        if len(tr) < period:
            return np.array([])
        
        return ema(np.array(tr), period)


def kdj(high: ArrayLike, low: ArrayLike, close: ArrayLike, 
        n: int = 9, m1: int = 3, m2: int = 3) -> Dict[str, np.ndarray]:
    """
    KDJ 指标（随机指标）
    
    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        n: KDJ 周期，默认 9
        m1: K 值平滑周期，默认 3
        m2: D 值平滑周期，默认 3
        
    Returns:
        字典 {'k': array, 'd': array, 'j': array}
    """
    high = _to_numpy_array(high)
    low = _to_numpy_array(low)
    close = _to_numpy_array(close)
    
    if _RUST_AVAILABLE:
        return _kdj(high, low, close, n, m1, m2)
    else:
        if n < 2 or m1 < 2 or m2 < 2 or len(high) < n or len(high) != len(low) or len(high) != len(close):
            return {'k': np.array([]), 'd': np.array([]), 'j': np.array([])}
        
        rsv = []
        for i in range(n - 1, len(high)):
            highest = np.max(high[i - n + 1:i + 1])
            lowest = np.min(low[i - n + 1:i + 1])
            close_val = close[i]
            
            if highest != lowest:
                rsv_val = (close_val - lowest) / (highest - lowest) * 100
            else:
                rsv_val = 50.0
            rsv.append(rsv_val)
        
        # 计算 K, D, J
        k_list = []
        d_list = []
        j_list = []
        
        prev_k = 50.0
        prev_d = 50.0
        
        for rsv_val in rsv:
            k_val = (m2 - 1) / m2 * prev_k + 1 / m2 * rsv_val
            d_val = (m1 - 1) / m1 * prev_d + 1 / m1 * k_val
            j_val = 3 * k_val - 2 * d_val
            
            k_list.append(k_val)
            d_list.append(d_val)
            j_list.append(j_val)
            
            prev_k = k_val
            prev_d = d_val
        
        return {
            'k': np.array(k_list),
            'd': np.array(d_list),
            'j': np.array(j_list)
        }


def obv(close: ArrayLike, volume: ArrayLike) -> np.ndarray:
    """
    OBV 指标 (On-Balance Volume)
    
    Args:
        close: 收盘价序列
        volume: 成交量序列
        
    Returns:
        OBV 值 numpy 数组
    """
    close = _to_numpy_array(close)
    volume = _to_numpy_array(volume)
    
    if _RUST_AVAILABLE:
        return _obv(close, volume)
    else:
        if len(close) != len(volume) or len(close) < 2:
            return np.array([])
        
        obv_values = [0.0]
        for i in range(1, len(close)):
            if close[i] > close[i - 1]:
                obv_values.append(obv_values[-1] + volume[i])
            elif close[i] < close[i - 1]:
                obv_values.append(obv_values[-1] - volume[i])
            else:
                obv_values.append(obv_values[-1])
        
        return np.array(obv_values)


def cci(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 20) -> np.ndarray:
    """
    CCI 指标 (Commodity Channel Index)
    
    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: 周期，默认 20
        
    Returns:
        CCI 值 numpy 数组
    """
    high = _to_numpy_array(high)
    low = _to_numpy_array(low)
    close = _to_numpy_array(close)
    
    if _RUST_AVAILABLE:
        return _cci(high, low, close, period)
    else:
        if period < 2 or len(high) < period or len(high) != len(low) or len(high) != len(close):
            return np.array([])
        
        tp = (high + low + close) / 3.0
        
        result = []
        for i in range(period - 1, len(tp)):
            window = tp[i - period + 1:i + 1]
            avg_tp = np.mean(window)
            mean_dev = np.mean(np.abs(window - avg_tp))
            cci_val = (tp[i] - avg_tp) / (0.015 * mean_dev) if mean_dev > 0 else 0.0
            result.append(cci_val)
        
        return np.array(result)


def williams_r(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> np.ndarray:
    """
    Williams %R 指标
    
    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: 周期，默认 14
        
    Returns:
        Williams %R 值 numpy 数组（-100 到 0）
    """
    high = _to_numpy_array(high)
    low = _to_numpy_array(low)
    close = _to_numpy_array(close)
    
    if _RUST_AVAILABLE:
        return _williams_r(high, low, close, period)
    else:
        if period < 2 or len(high) < period or len(high) != len(low) or len(high) != len(close):
            return np.array([])
        
        result = []
        for i in range(period - 1, len(high)):
            highest = np.max(high[i - period + 1:i + 1])
            lowest = np.min(low[i - period + 1:i + 1])
            
            if highest != lowest:
                wr = (highest - close[i]) / (highest - lowest) * -100.0
            else:
                wr = -50.0
            result.append(wr)
        
        return np.array(result)


def adx(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> np.ndarray:
    """
    ADX 指标 (Average Directional Index)
    
    Args:
        high: 最高价序列
        low: 最低价序列
        close: 收盘价序列
        period: 周期，默认 14
        
    Returns:
        ADX 值 numpy 数组
    """
    high = _to_numpy_array(high)
    low = _to_numpy_array(low)
    close = _to_numpy_array(close)
    
    if _RUST_AVAILABLE:
        return _adx(high, low, close, period)
    else:
        # === 向量化优化版 (性能提升 50-200x) ===
        n = len(high)
        
        if period < 2 or n < period + 1 or len(low) != n or len(close) != n:
            return np.array([])
        
        # Step 1: 向量化计算 DM (Directional Movement)
        high_diff = np.diff(high)   # high[i] - high[i-1]
        low_diff = -np.diff(low)    # low[i-1] - low[i]
        
        plus_dm = np.where(
            (high_diff > low_diff) & (high_diff > 0),
            high_diff,
            0.0
        )
        
        minus_dm = np.where(
            (low_diff > high_diff) & (low_diff > 0),
            low_diff,
            0.0
        )
        
        # Step 2: 向量化计算 TR (True Range)
        hl = high[1:] - low[1:]
        hc = np.abs(high[1:] - close[:-1])
        lc = np.abs(low[1:] - close[:-1])
        tr = np.maximum(np.maximum(hl, hc), lc)
        
        # Step 3: 向量化滑动窗口求和 (使用 cumsum 技巧)
        def rolling_sum(arr: np.ndarray, window: int) -> np.ndarray:
            """使用 cumsum 实现的高效滑动窗口求和"""
            cumsum = np.cumsum(arr)
            n_windows = len(arr) - window + 1
            
            if n_windows <= 0:
                return np.array([])
            
            result = np.empty(n_windows)
            result[0] = cumsum[window - 1]
            
            if n_windows > 1:
                result[1:] = cumsum[window:len(arr)] - cumsum[:n_windows-1]
            
            return result
        
        smoothed_plus_dm = rolling_sum(plus_dm, period)
        smoothed_minus_dm = rolling_sum(minus_dm, period)
        smoothed_tr = rolling_sum(tr, period)
        
        if len(smoothed_tr) == 0:
            return np.array([])
        
        # Step 4: 计算 DI 和 DX
        plus_di = np.where(smoothed_tr > 0, smoothed_plus_dm / smoothed_tr * 100, 0.0)
        minus_di = np.where(smoothed_tr > 0, smoothed_minus_dm / smoothed_tr * 100, 0.0)
        
        di_sum = plus_di + minus_di
        di_diff = np.abs(plus_di - minus_di)
        dx = np.where(di_sum > 0, di_diff / di_sum * 100, 0.0)
        
        if len(dx) < period:
            return np.array([])
        
        # Step 5: EMA 平滑 DX 得到 ADX
        return ema(dx, period)


# 导出所有指标
__all__ = [
    'ma',
    'ema',
    'macd',
    'rsi',
    'bollinger_bands',
    'atr',
    'cci',
    'kdj',
    'obv',
    'williams_r',
    'adx',
]
