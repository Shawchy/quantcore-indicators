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
        ma as _ma,
        ema as _ema,
        macd as _macd,
        rsi as _rsi,
        bollinger_bands as _bollinger_bands,
        atr as _atr,
        cci as _cci,
        kdj as _kdj,
        obv as _obv,
        williams_r as _williams_r,
        adx as _adx,
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
        # 纯 Python 实现（后备）
        if len(prices) < period:
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
        # 纯 Python 实现（后备）
        if len(prices) < period:
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
        # 纯 Python 实现（后备）
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
        # 纯 Python 实现（后备）
        if len(prices) < period + 1:
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
        # 纯 Python 实现（后备）
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
        # 纯 Python 实现（后备）
        if len(high) < 2 or len(high) != len(low) or len(high) != len(close):
            return np.array([])
        
        # 计算真实波幅
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
        # 纯 Python 实现（后备）
        if len(high) < n or len(high) != len(low) or len(high) != len(close):
            return {'k': np.array([]), 'd': np.array([]), 'j': np.array([])}
        
        # 计算 RSV
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
        # 纯 Python 实现（后备）
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


# 导出所有指标
__all__ = [
    'ma',
    'ema',
    'macd',
    'rsi',
    'bollinger_bands',
    'atr',
    'kdj',
    'obv',
]
