# -*- coding: utf-8 -*-
"""
技术指标库

提供常用技术指标：
- MA: 移动平均
- EMA: 指数平均
- MACD: 异同移动平均
- RSI: 相对强弱指标
- BOLL: 布林带

优先使用 quantcore-indicators（Rust 加速版本），不可用时降级到纯 Python 实现
"""

from typing import List, Union
import math

try:
    import numpy as np
    _HAS_NUMPY = True
except ImportError:
    _HAS_NUMPY = False

# 尝试导入 quantcore-indicators（Rust 加速版）
try:
    from quantcore_indicators import (
        ma as _rsi_ma,
        ema as _rsi_ema,
        macd as _rsi_macd,
        rsi as _rsi_rsi,
        bollinger_bands as _rsi_boll,
        atr as _rsi_atr,
        cci as _rsi_cci,
        kdj as _rsi_kdj,
        obv as _rsi_obv,
        williams_r as _rsi_williams,
        adx as _rsi_adx,
    )
    _USE_RUST = True
except ImportError:
    _USE_RUST = False


def _use_rust_if_available():
    """检查是否使用 Rust 版本"""
    return _USE_RUST


def _to_array(data) -> 'np.ndarray':
    if _HAS_NUMPY:
        if isinstance(data, np.ndarray):
            return data.astype(np.float64)
        return np.asarray(data, dtype=np.float64)
    return list(data)


def ma(prices: List[float], period: int) -> List[float]:
    if _USE_RUST:
        return _rsi_ma(prices, period).tolist()
    
    if len(prices) < period:
        return []
    
    if _HAS_NUMPY:
        arr = _to_array(prices)
        kernel = np.ones(period) / period
        result = np.convolve(arr, kernel, mode='valid')
        return result.tolist()
    
    result = []
    for i in range(period - 1, len(prices)):
        avg = sum(prices[i - period + 1:i + 1]) / period
        result.append(avg)
    
    return result


def ema(prices: List[float], period: int) -> List[float]:
    if _USE_RUST:
        return _rsi_ema(prices, period).tolist()
    
    if len(prices) < period:
        return []
    
    multiplier = 2 / (period + 1)
    
    if _HAS_NUMPY:
        arr = _to_array(prices)
        result = np.empty(len(arr) - period + 1)
        result[0] = np.mean(arr[:period])
        for i in range(1, len(result)):
            result[i] = (arr[period + i - 1] - result[i - 1]) * multiplier + result[i - 1]
        return result.tolist()
    
    result = [sum(prices[:period]) / period]
    
    for i in range(period, len(prices)):
        ema_value = (prices[i] - result[-1]) * multiplier + result[-1]
        result.append(ema_value)
    
    return result


def macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """
    MACD 指标
    
    Args:
        prices: 价格列表
        fast: 快线周期
        slow: 慢线周期
        signal: 信号线周期
        
    Returns:
        包含 MACD、Signal、Histogram 的字典
    """
    if _USE_RUST:
        result = _rsi_macd(prices, fast, slow, signal)
        return {
            'macd': result['macd'].tolist(),
            'signal': result['signal'].tolist(),
            'histogram': result['histogram'].tolist(),
        }
    
    if len(prices) < slow:
        return {'macd': [], 'signal': [], 'histogram': []}
    
    fast_ema = ema(prices, fast)
    slow_ema = ema(prices, slow)
    
    # 对齐长度
    min_len = min(len(fast_ema), len(slow_ema))
    fast_ema = fast_ema[-min_len:]
    slow_ema = slow_ema[-min_len:]
    
    macd_line = [f - s for f, s in zip(fast_ema, slow_ema)]
    signal_line = ema(macd_line, signal) if len(macd_line) >= signal else []
    
    histogram = []
    if signal_line:
        histogram = [m - s for m, s in zip(macd_line[-len(signal_line):], signal_line)]
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def rsi(prices: List[float], period: int = 14) -> List[float]:
    if _USE_RUST:
        return _rsi_rsi(prices, period).tolist()
    
    if len(prices) < period + 1:
        return []
    
    if _HAS_NUMPY:
        arr = _to_array(prices)
        deltas = np.diff(arr)
        
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        
        alpha = 1.0 / period
        
        try:
            from scipy.signal import lfilter
            b = [alpha]
            a = [1, -(1 - alpha)]
            avg_gain = lfilter(b, a, gains)
            avg_loss = lfilter(b, a, losses)
            
            avg_gain[:period-1] = 0.0
            avg_loss[:period-1] = 0.0
            seed_gain = np.mean(gains[:period])
            seed_loss = np.mean(losses[:period])
            avg_gain[period-1] = seed_gain
            avg_loss[period-1] = seed_loss
            
            for i in range(period, min(period + 1, len(deltas))):
                avg_gain[i] = avg_gain[i-1] * (1 - alpha) + gains[i] * alpha
                avg_loss[i] = avg_loss[i-1] * (1 - alpha) + losses[i] * alpha
        except ImportError:
            avg_gain = np.empty(len(deltas))
            avg_loss = np.empty(len(deltas))
            
            avg_gain[:period] = 0.0
            avg_loss[:period] = 0.0
            avg_gain[period - 1] = np.mean(gains[:period])
            avg_loss[period - 1] = np.mean(losses[:period])
            
            for i in range(period, len(deltas)):
                avg_gain[i] = avg_gain[i-1] * (1 - alpha) + gains[i] * alpha
                avg_loss[i] = avg_loss[i-1] * (1 - alpha) + losses[i] * alpha
        
        rs = np.where(avg_loss[period-1:] != 0, avg_gain[period-1:] / avg_loss[period-1:], 0.0)
        rsi_values = np.where(avg_loss[period-1:] != 0, 100.0 - (100.0 / (1.0 + rs)), 100.0)
        
        return rsi_values.tolist()
    
    deltas = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
    
    gains = [d if d > 0 else 0.0 for d in deltas]
    losses = [-d if d < 0 else 0.0 for d in deltas]
    
    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period
    
    result = []
    
    if avg_loss == 0:
        result.append(100.0)
    else:
        rs = avg_gain / avg_loss
        result.append(100.0 - (100.0 / (1.0 + rs)))
    
    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        
        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(100.0 - (100.0 / (1.0 + rs)))
    
    return result


def bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> dict:
    if _USE_RUST:
        result = _rsi_boll(prices, period, std_dev)
        return {
            'upper': result['upper'].tolist(),
            'middle': result['middle'].tolist(),
            'lower': result['lower'].tolist(),
        }
    
    if len(prices) < period:
        return {'upper': [], 'middle': [], 'lower': []}
    
    if _HAS_NUMPY:
        arr = _to_array(prices)
        cumsum = np.cumsum(arr)
        sums = cumsum[period - 1:] - np.concatenate([[0], cumsum[:-period]])
        middle = sums / period
        
        cumsum2 = np.cumsum(arr ** 2)
        sums2 = cumsum2[period - 1:] - np.concatenate([[0], cumsum2[:-period]])
        variance = sums2 / period - middle ** 2
        std = np.sqrt(np.maximum(variance, 0))
        
        upper = middle + std_dev * std
        lower = middle - std_dev * std
        
        return {
            'upper': upper.tolist(),
            'middle': middle.tolist(),
            'lower': lower.tolist()
        }
    
    middle = ma(prices, period)
    upper = []
    lower = []
    
    for i in range(period - 1, len(prices)):
        window = prices[i - period + 1:i + 1]
        mean = sum(window) / period
        variance = sum((x - mean) ** 2 for x in window) / period
        std = variance ** 0.5
        
        upper.append(mean + std_dev * std)
        lower.append(mean - std_dev * std)
    
    return {
        'upper': upper,
        'middle': middle,
        'lower': lower
    }


def kdj(high: List[float], low: List[float], close: List[float], 
        n: int = 9, m1: int = 3, m2: int = 3) -> dict:
    """
    KDJ 指标（随机指标）
    
    Args:
        high: 最高价列表
        low: 最低价列表
        close: 收盘价列表
        n: KDJ 周期，默认 9
        m1: K 值平滑周期，默认 3
        m2: D 值平滑周期，默认 3
        
    Returns:
        字典 {'k': List, 'd': List, 'j': List}
    """
    if _USE_RUST:
        result = _rsi_kdj(high, low, close, n, m1, m2)
        return {
            'k': result['k'].tolist(),
            'd': result['d'].tolist(),
            'j': result['j'].tolist(),
        }
    
    if len(high) < n or len(low) < n or len(close) < n:
        return {'k': [], 'd': [], 'j': []}
    
    k = 50.0  # 初始值
    d = 50.0  # 初始值
    
    k_list = []
    d_list = []
    j_list = []
    
    for i in range(n - 1, len(high)):
        highest = max(high[i - n + 1:i + 1])
        lowest = min(low[i - n + 1:i + 1])
        current_close = close[i]
        
        if highest == lowest:
            rsv = 50.0
        else:
            rsv = ((current_close - lowest) / (highest - lowest)) * 100
        
        k = (m2 - 1) / m2 * k + 1 / m2 * rsv
        d = (m1 - 1) / m1 * d + 1 / m1 * k
        j = 3 * k - 2 * d
        
        k_list.append(k)
        d_list.append(d)
        j_list.append(j)
    
    return {'k': k_list, 'd': d_list, 'j': j_list}


def atr(high_prices: List[float], low_prices: List[float], 
       close_prices: List[float], period: int = 14) -> List[float]:
    if _USE_RUST:
        return _rsi_atr(high_prices, low_prices, close_prices, period).tolist()
    
    if len(high_prices) < period or len(low_prices) < period or len(close_prices) < period:
        return []
    
    if _HAS_NUMPY:
        high = _to_array(high_prices)
        low = _to_array(low_prices)
        close = _to_array(close_prices)
        
        tr = np.maximum(high - low, np.maximum(
            np.abs(high - np.concatenate([[close[0]], close[:-1]])),
            np.abs(low - np.concatenate([[close[0]], close[:-1]]))
        ))
        tr[0] = high[0] - low[0]
        
        atr_result = np.empty(len(tr) - period + 1)
        atr_result[0] = np.mean(tr[:period])
        for i in range(1, len(atr_result)):
            atr_result[i] = (atr_result[i - 1] * (period - 1) + tr[period + i - 1]) / period
        
        return atr_result.tolist()
    
    tr_list = []
    
    for i in range(len(high_prices)):
        if i == 0:
            tr = high_prices[i] - low_prices[i]
        else:
            tr1 = high_prices[i] - low_prices[i]
            tr2 = abs(high_prices[i] - close_prices[i-1])
            tr3 = abs(low_prices[i] - close_prices[i-1])
            tr = max(tr1, tr2, tr3)
        tr_list.append(tr)
    
    atr_list = []
    
    first_atr = sum(tr_list[:period]) / period
    atr_list.append(first_atr)
    
    for i in range(period, len(tr_list)):
        atr_val = (atr_list[-1] * (period - 1) + tr_list[i]) / period
        atr_list.append(atr_val)
    
    return atr_list


def cci(high_prices: List[float], low_prices: List[float], 
      close_prices: List[float], period: int = 14) -> List[float]:
    if _USE_RUST:
        return _rsi_cci(high_prices, low_prices, close_prices, period).tolist()
    
    if len(high_prices) < period or len(low_prices) < period or len(close_prices) < period:
        return []
    
    if _HAS_NUMPY:
        high = _to_array(high_prices)
        low = _to_array(low_prices)
        close = _to_array(close_prices)
        
        tp = (high + low + close) / 3.0
        
        kernel = np.ones(period) / period
        ma_tp = np.convolve(tp, kernel, mode='valid')
        
        tp_windows = np.lib.stride_tricks.sliding_window_view(tp, period)
        mean_dev = np.mean(np.abs(tp_windows - ma_tp[:, np.newaxis]), axis=1)
        
        cci_values = np.where(mean_dev > 0, (tp[period-1:] - ma_tp) / (0.015 * mean_dev), 0.0)
        return cci_values.tolist()
    
    cci_list = []
    
    for i in range(period - 1, len(close_prices)):
        tp_list = []
        for j in range(i - period + 1, i + 1):
            tp = (high_prices[j] + low_prices[j] + close_prices[j]) / 3
            tp_list.append(tp)
        
        ma_tp = sum(tp_list) / period
        
        deviations = [abs(tp - ma_tp) for tp in tp_list]
        mean_deviation = sum(deviations) / period
        
        if mean_deviation == 0:
            cci = 0.0
        else:
            tp_current = (high_prices[i] + low_prices[i] + close_prices[i]) / 3
            cci = (tp_current - ma_tp) / (0.015 * mean_deviation)
        
        cci_list.append(cci)
    
    return cci_list


def williams_r(high_prices: List[float], low_prices: List[float], 
               close_prices: List[float], period: int = 14) -> List[float]:
    if _USE_RUST:
        return _rsi_williams(high_prices, low_prices, close_prices, period).tolist()
    
    if len(high_prices) < period or len(low_prices) < period or len(close_prices) < period:
        return []
    
    if _HAS_NUMPY:
        high = _to_array(high_prices)
        low = _to_array(low_prices)
        close = _to_array(close_prices)
        
        high_windows = np.lib.stride_tricks.sliding_window_view(high, period)
        low_windows = np.lib.stride_tricks.sliding_window_view(low, period)
        
        highest = np.max(high_windows, axis=1)
        lowest = np.min(low_windows, axis=1)
        
        current_close = close[period - 1:]
        
        wr = np.where(highest == lowest, -50.0, ((highest - current_close) / (highest - lowest)) * -100)
        return wr.tolist()
    
    wr_list = []
    
    for i in range(period - 1, len(close_prices)):
        highest = max(high_prices[i - period + 1:i + 1])
        lowest = min(low_prices[i - period + 1:i + 1])
        current_close = close_prices[i]
        
        if highest == lowest:
            wr = -50.0
        else:
            wr = ((highest - current_close) / (highest - lowest)) * -100
        
        wr_list.append(wr)
    
    return wr_list


def obv(close_prices: List[float], volumes: List[int]) -> List[float]:
    if _USE_RUST:
        return _rsi_obv(close_prices, volumes).tolist()
    
    if len(close_prices) != len(volumes) or len(close_prices) < 2:
        return []
    
    if _HAS_NUMPY:
        close = _to_array(close_prices)
        vol = _to_array(volumes).astype(np.float64)
        
        direction = np.sign(np.diff(close))
        direction = np.concatenate([[0], direction])
        
        signed_vol = vol * direction
        result = np.cumsum(signed_vol)
        return result.tolist()
    
    obv_list = [0.0]
    
    for i in range(1, len(close_prices)):
        if close_prices[i] > close_prices[i-1]:
            obv = obv_list[-1] + volumes[i]
        elif close_prices[i] < close_prices[i-1]:
            obv = obv_list[-1] - volumes[i]
        else:
            obv = obv_list[-1]
        
        obv_list.append(obv)
    
    return obv_list


# 11. ADX - 平均趋向指标

def _calc_true_range(high_prices, low_prices, close_prices):
    if _HAS_NUMPY:
        high = _to_array(high_prices)
        low = _to_array(low_prices)
        close = _to_array(close_prices)
        tr = np.maximum(high - low, np.maximum(
            np.abs(high - np.concatenate([[close[0]], close[:-1]])),
            np.abs(low - np.concatenate([[close[0]], close[:-1]]))
        ))
        tr[0] = high[0] - low[0]
        return tr
    
    tr_list = []
    for i in range(len(high_prices)):
        if i == 0:
            tr = high_prices[i] - low_prices[i]
        else:
            tr1 = high_prices[i] - low_prices[i]
            tr2 = abs(high_prices[i] - close_prices[i-1])
            tr3 = abs(low_prices[i] - close_prices[i-1])
            tr = max(tr1, tr2, tr3)
        tr_list.append(tr)
    return tr_list


def _calc_directional_movement(high_prices, low_prices):
    plus_dm = []
    minus_dm = []
    for i in range(1, len(high_prices)):
        up_move = high_prices[i] - high_prices[i-1]
        down_move = low_prices[i-1] - low_prices[i]
        
        if up_move > down_move and up_move > 0:
            plus_dm.append(up_move)
        else:
            plus_dm.append(0.0)
        
        if down_move > up_move and down_move > 0:
            minus_dm.append(down_move)
        else:
            minus_dm.append(0.0)
    return plus_dm, minus_dm


def adx(high_prices: List[float], low_prices: List[float], 
        close_prices: List[float], period: int = 14) -> List[float]:
    if _USE_RUST:
        return _rsi_adx(high_prices, low_prices, close_prices, period).tolist()
    
    if len(high_prices) < period + 1:
        return []
    
    plus_dm, minus_dm = _calc_directional_movement(high_prices, low_prices)
    tr_list = _calc_true_range(high_prices, low_prices, close_prices)
    
    # 计算 +DI 和 -DI
    plus_di = []
    minus_di = []
    
    for i in range(len(plus_dm)):
        if i < period:
            plus_di.append(0.0)
            minus_di.append(0.0)
        else:
            sum_plus_dm = sum(plus_dm[i-period+1:i+1])
            sum_minus_dm = sum(minus_dm[i-period+1:i+1])
            sum_tr = sum(tr_list[i-period+1:i+1])
            
            plus_di.append((sum_plus_dm / sum_tr) * 100 if sum_tr > 0 else 0)
            minus_di.append((sum_minus_dm / sum_tr) * 100 if sum_tr > 0 else 0)
    
    # 计算 DX
    dx_list = []
    for i in range(len(plus_di)):
        if plus_di[i] + minus_di[i] > 0:
            dx = abs(plus_di[i] - minus_di[i]) / (plus_di[i] + minus_di[i]) * 100
        else:
            dx = 0.0
        dx_list.append(dx)
    
    # 计算 ADX（DX 的 MA）
    adx_list = []
    for i in range(len(dx_list)):
        if i < period:
            adx_list.append(0.0)
        else:
            adx = sum(dx_list[i-period+1:i+1]) / period
            adx_list.append(adx)
    
    return adx_list


# 12. SAR - 抛物线转向指标
def sar(high_prices: List[float], low_prices: List[float], 
        af: float = 0.02, max_af: float = 0.2) -> List[float]:
    """
    SAR 指标（Parabolic SAR，抛物线转向指标）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        af: 加速因子，默认 0.02
        max_af: 最大加速因子，默认 0.2
        
    Returns:
        SAR 值列表
    """
    if len(high_prices) < 3:
        return []
    
    sar_list = [low_prices[0]]  # 初始 SAR
    
    long_pos = True  # 多头仓位
    ep = high_prices[0]  # 极值点
    current_af = af
    
    for i in range(1, len(high_prices)):
        # 计算 SAR
        prev_sar = sar_list[-1]
        sar = prev_sar + current_af * (ep - prev_sar)
        
        # 更新极值点和加速因子
        if long_pos:
            if high_prices[i] > ep:
                ep = high_prices[i]
                current_af = min(current_af + af, max_af)
            
            # 检查是否转向
            if low_prices[i] < sar:
                long_pos = False
                sar = ep
                ep = low_prices[i]
                current_af = af
        else:
            if low_prices[i] < ep:
                ep = low_prices[i]
                current_af = min(current_af + af, max_af)
            
            # 检查是否转向
            if high_prices[i] > sar:
                long_pos = True
                sar = ep
                ep = high_prices[i]
                current_af = af
        
        sar_list.append(sar)
    
    return sar_list


# 13. STOCH - 随机指标
def stoch(high_prices: List[float], low_prices: List[float], 
          close_prices: List[float], k_period: int = 14, 
          d_period: int = 3) -> dict:
    if len(high_prices) < k_period:
        return {'k': [], 'd': []}
    
    if _HAS_NUMPY:
        high = _to_array(high_prices)
        low = _to_array(low_prices)
        close = _to_array(close_prices)
        
        high_windows = np.lib.stride_tricks.sliding_window_view(high, k_period)
        low_windows = np.lib.stride_tricks.sliding_window_view(low, k_period)
        
        highest = np.max(high_windows, axis=1)
        lowest = np.min(low_windows, axis=1)
        
        current_close = close[k_period - 1:]
        
        k_values = np.where(highest == lowest, 50.0, ((current_close - lowest) / (highest - lowest)) * 100)
        
        k_full = np.concatenate([np.full(k_period - 1, 50.0), k_values])
        
        d_values = np.convolve(k_full, np.ones(d_period) / d_period, mode='valid')
        
        return {'k': k_full.tolist(), 'd': d_values.tolist()}
    
    k_list = []
    d_list = []
    
    for i in range(len(close_prices)):
        if i < k_period - 1:
            k_list.append(50.0)
            d_list.append(50.0)
        else:
            highest = max(high_prices[i-k_period+1:i+1])
            lowest = min(low_prices[i-k_period+1:i+1])
            
            if highest == lowest:
                k = 50.0
            else:
                k = ((close_prices[i] - lowest) / (highest - lowest)) * 100
            
            k_list.append(k)
            
            if len(k_list) >= d_period:
                d = sum(k_list[-d_period:]) / d_period
            else:
                d = 50.0
            d_list.append(d)
    
    return {'k': k_list, 'd': d_list}


# 14. ROC - 变动率指标
def roc(prices: List[float], period: int = 12) -> List[float]:
    if len(prices) < period + 1:
        return []
    
    if _HAS_NUMPY:
        arr = _to_array(prices)
        result = np.where(arr[:-period] != 0, ((arr[period:] - arr[:-period]) / arr[:-period]) * 100, 0.0)
        return result.tolist()
    
    roc_list = []
    
    for i in range(period, len(prices)):
        if prices[i - period] != 0:
            roc = ((prices[i] - prices[i - period]) / prices[i - period]) * 100
        else:
            roc = 0.0
        roc_list.append(roc)
    
    return roc_list


# 15. MFI - 资金流量指标
def mfi(high_prices: List[float], low_prices: List[float], 
        close_prices: List[float], volumes: List[int], 
        period: int = 14) -> List[float]:
    if len(high_prices) < period + 1:
        return []
    
    if _HAS_NUMPY:
        high = _to_array(high_prices)
        low = _to_array(low_prices)
        close = _to_array(close_prices)
        vol = _to_array(volumes).astype(np.float64)
        
        tp = (high + low + close) / 3.0
        mf = tp * vol
        
        tp_diff = np.diff(tp)
        tp_diff = np.concatenate([[0], tp_diff])
        
        positive_mf = np.where(tp_diff > 0, mf, 0.0)
        negative_mf = np.where(tp_diff < 0, mf, 0.0)
        
        kernel = np.ones(period)
        sum_pos = np.convolve(positive_mf[1:], kernel, mode='valid')
        sum_neg = np.convolve(negative_mf[1:], kernel, mode='valid')
        
        mfi_values = np.where(sum_neg == 0, 100.0, 100.0 - (100.0 / (1.0 + sum_pos / sum_neg)))
        
        padding = np.full(len(high) - len(mfi_values), 50.0)
        result = np.concatenate([padding, mfi_values])
        return result.tolist()
    
    typical_prices = [(high_prices[i] + low_prices[i] + close_prices[i]) / 3 
                      for i in range(len(high_prices))]
    
    money_flow = []
    for i in range(len(typical_prices)):
        mf = typical_prices[i] * volumes[i]
        money_flow.append(mf)
    
    positive_flow = []
    negative_flow = []
    
    for i in range(1, len(typical_prices)):
        if typical_prices[i] > typical_prices[i-1]:
            positive_flow.append(money_flow[i])
            negative_flow.append(0.0)
        elif typical_prices[i] < typical_prices[i-1]:
            positive_flow.append(0.0)
            negative_flow.append(money_flow[i])
        else:
            positive_flow.append(0.0)
            negative_flow.append(0.0)
    
    mfi_list = []
    for i in range(len(positive_flow)):
        if i < period - 1:
            mfi_list.append(50.0)
        else:
            sum_positive = sum(positive_flow[i-period+1:i+1])
            sum_negative = sum(negative_flow[i-period+1:i+1])
            
            if sum_negative == 0:
                mfi = 100.0
            else:
                money_ratio = sum_positive / sum_negative
                mfi = 100 - (100 / (1 + money_ratio))
            
            mfi_list.append(mfi)
    
    return mfi_list


# 16. AROON - 阿隆指标
def aroon(high_prices: List[float], low_prices: List[float], 
          period: int = 25) -> dict:
    """
    AROON 指标（Aroon Indicator，阿隆指标）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        period: 周期，默认 25
        
    Returns:
        包含 Aroon Up 和 Aroon Down 的字典
    """
    if len(high_prices) < period + 1:
        return {'up': [], 'down': []}
    
    aroon_up = []
    aroon_down = []
    
    for i in range(period, len(high_prices)):
        # 寻找周期内最高价和最低价的位置
        highest_high = max(high_prices[i-period+1:i+1])
        lowest_low = min(low_prices[i-period+1:i+1])
        
        # 计算距离周期结束的天数
        days_since_high = high_prices[i-period+1:i+1][::-1].index(highest_high)
        days_since_low = low_prices[i-period+1:i+1][::-1].index(lowest_low)
        
        # 计算 Aroon Up 和 Down
        up = ((period - days_since_high) / period) * 100
        down = ((period - days_since_low) / period) * 100
        
        aroon_up.append(up)
        aroon_down.append(down)
    
    # 填充前面的值
    for i in range(period):
        aroon_up.insert(0, 50.0)
        aroon_down.insert(0, 50.0)
    
    return {'up': aroon_up, 'down': aroon_down}


# 17. VWAP - 成交量加权平均价
def vwap(high_prices: List[float], low_prices: List[float], 
         close_prices: List[float], volumes: List[int]) -> List[float]:
    """
    VWAP 指标（Volume Weighted Average Price，成交量加权平均价）
    
    Args:
        high_prices: 最高价列表
        low_prices: 最低价列表
        close_prices: 收盘价列表
        volumes: 成交量列表
        
    Returns:
        VWAP 值列表
    """
    if len(high_prices) < 2:
        return []
    
    vwap_list = []
    cumulative_pv = 0.0
    cumulative_volume = 0
    
    for i in range(len(high_prices)):
        typical_price = (high_prices[i] + low_prices[i] + close_prices[i]) / 3
        pv = typical_price * volumes[i]
        
        cumulative_pv += pv
        cumulative_volume += volumes[i]
        
        if cumulative_volume > 0:
            vwap = cumulative_pv / cumulative_volume
        else:
            vwap = typical_price
        
        vwap_list.append(vwap)
    
    return vwap_list


# 18. PPO - 价格震荡百分比指标
def ppo(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> dict:
    """
    PPO 指标（Percentage Price Oscillator，价格震荡百分比指标）
    
    Args:
        prices: 价格列表
        fast: 快速周期，默认 12
        slow: 慢速周期，默认 26
        signal: 信号线周期，默认 9
        
    Returns:
        包含 PPO、Signal 和 Histogram 的字典
    """
    if len(prices) < slow:
        return {'ppo': [], 'signal': [], 'histogram': []}
    
    # 计算 EMA
    fast_ema = ema(prices, fast)
    slow_ema = ema(prices, slow)
    
    # 计算 PPO
    ppo_list = []
    for i in range(len(prices)):
        if slow_ema[i] != 0:
            ppo = ((fast_ema[i] - slow_ema[i]) / slow_ema[i]) * 100
        else:
            ppo = 0.0
        ppo_list.append(ppo)
    
    # 计算信号线
    signal_list = ema(ppo_list, signal)
    
    # 计算柱状图
    histogram_list = [ppo_list[i] - signal_list[i] for i in range(len(ppo_list))]
    
    return {'ppo': ppo_list, 'signal': signal_list, 'histogram': histogram_list}


# 19. TRIX - 三重指数平滑移动平均
def trix(prices: List[float], period: int = 14) -> List[float]:
    """
    TRIX 指标（Triple Exponential Average，三重指数平滑移动平均）
    
    Args:
        prices: 价格列表
        period: 周期，默认 14
        
    Returns:
        TRIX 值列表
    """
    if len(prices) < period * 3:
        return []
    
    # 三次 EMA 平滑
    ema1 = ema(prices, period)
    ema2 = ema(ema1, period)
    ema3 = ema(ema2, period)
    
    # 计算 TRIX
    trix_list = []
    for i in range(len(ema3)):
        if i == 0 or ema3[i-1] == 0:
            trix_list.append(0.0)
        else:
            trix = ((ema3[i] - ema3[i-1]) / ema3[i-1]) * 100
            trix_list.append(trix)
    
    return trix_list


# 20. DMI - 动向指标
def dmi(high_prices: List[float], low_prices: List[float], 
        close_prices: List[float], period: int = 14) -> dict:
    adx_values = adx(high_prices, low_prices, close_prices, period)
    
    plus_dm, minus_dm = _calc_directional_movement(high_prices, low_prices)
    tr_list = _calc_true_range(high_prices, low_prices, close_prices)
    
    plus_di = [0.0]
    minus_di = [0.0]
    
    for i in range(len(plus_dm)):
        if i < period:
            plus_di.append(0.0)
            minus_di.append(0.0)
        else:
            sum_plus_dm = sum(plus_dm[i-period+1:i+1])
            sum_minus_dm = sum(minus_dm[i-period+1:i+1])
            sum_tr = sum(tr_list[i-period+1:i+1])
            
            plus_di.append((sum_plus_dm / sum_tr) * 100 if sum_tr > 0 else 0)
            minus_di.append((sum_minus_dm / sum_tr) * 100 if sum_tr > 0 else 0)
    
    return {'plus_di': plus_di, 'minus_di': minus_di, 'adx': adx_values}


# 导出所有指标
__all__ = [
    'ma',
    'ema', 
    'macd',
    'rsi',
    'bollinger_bands',
    'kdj',
    'atr',
    'cci',
    'williams_r',
    'obv',
    'adx',
    'sar',
    'stoch',
    'roc',
    'mfi',
    'aroon',
    'vwap',
    'ppo',
    'trix',
    'dmi',
]
