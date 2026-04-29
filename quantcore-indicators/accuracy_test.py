# -*- coding: utf-8 -*-
"""
准确率基准测试：对比 Rust 实现与 pandas-ta 的指标计算结果
确保优化不改变计算精度
"""

import numpy as np
import pandas as pd
import time
import sys

try:
    import pandas_ta as ta
    HAS_PANDAS_TA = True
except Exception as e:
    HAS_PANDAS_TA = False
    print(f"⚠️  pandas-ta 未安装/加载失败，将使用 pandas 向量化实现作为基准")
    print(f"   错误信息: {e}")

try:
    from quantcore_indicators import (
        ma, ema, macd, rsi, bollinger_bands, atr, cci, kdj, 
        obv, williams_r, adx, wma, stochastic, vwap, 
        dema, tema, hma, roc, psar, natr
    )
    HAS_RUST = True
except ImportError:
    HAS_RUST = False
    print("❌ Rust 扩展未加载")
    sys.exit(1)

# 生成测试数据
np.random.seed(42)
N = 10000

# OHLCV 数据
high = np.random.uniform(100, 110, N)
low = np.random.uniform(90, 100, N)
close = np.random.uniform(95, 105, N)
volume = np.random.uniform(1000, 5000, N)

# 确保 OHLC 合理性
high = np.maximum(high, np.maximum(close, low) + 0.5)
low = np.minimum(low, np.minimum(close, high) - 0.5)

def compare(name, rust_result, pandas_result, tolerance=1e-6):
    """对比两个结果"""
    if isinstance(rust_result, dict):
        for key in rust_result:
            if key in pandas_result:
                rust_arr = np.asarray(rust_result[key], dtype=np.float64)
                pandas_arr = np.asarray(pandas_result[key], dtype=np.float64)
                
                if len(rust_arr) != len(pandas_arr):
                    print(f"  ⚠️ {name}.{key}: 长度不匹配 (Rust={len(rust_arr)}, Pandas={len(pandas_arr)})")
                    continue
                
                if np.allclose(rust_arr, pandas_arr, rtol=tolerance, atol=tolerance, equal_nan=True):
                    print(f"  ✅ {name}.{key}: 完全匹配 (len={len(rust_arr)})")
                else:
                    max_diff = np.max(np.abs(rust_arr - pandas_arr))
                    mean_diff = np.mean(np.abs(rust_arr - pandas_arr))
                    print(f"  ❌ {name}.{key}: 不匹配 (max_diff={max_diff:.2e}, mean_diff={mean_diff:.2e})")
    else:
        rust_arr = np.asarray(rust_result, dtype=np.float64)
        pandas_arr = np.asarray(pandas_result, dtype=np.float64)
        
        if len(rust_arr) != len(pandas_arr):
            print(f"  ⚠️ {name}: 长度不匹配 (Rust={len(rust_arr)}, Pandas={len(pandas_arr)})")
            return
        
        if np.allclose(rust_arr, pandas_arr, rtol=tolerance, atol=tolerance, equal_nan=True):
            print(f"  ✅ {name}: 完全匹配 (len={len(rust_arr)})")
        else:
            max_diff = np.max(np.abs(rust_arr - pandas_arr))
            mean_diff = np.mean(np.abs(rust_arr - pandas_arr))
            print(f"  ❌ {name}: 不匹配 (max_diff={max_diff:.2e}, mean_diff={mean_diff:.2e})")

print("=" * 80)
print("准确率基准测试")
print("=" * 80)

# 1. MA
print("\n1. MA (20)")
rust_ma = ma(close, 20)
pd_ma = close_df = pd.Series(close).rolling(20).mean().dropna().values
compare("MA", rust_ma, pd_ma)

# 2. EMA
print("\n2. EMA (12)")
rust_ema = ema(close, 12)
# Rust: 第一个值是 SMA(12)，然后从索引 12 开始递推
# pandas: ewm 从索引 0 开始，但前 11 个值不可靠（adjust=False）
# Rust 输出长度 = 10000 - 12 + 1 = 9989
pd_ema_full = pd.Series(close).ewm(span=12, adjust=False).mean().values
# 对齐：Rust 的第一个值对应 pandas SMA(12)，即 pd_ema_full[11]
# Rust 的第二个值对应 pd_ema_full[12]，依此类推
pd_ema = pd_ema_full[11:]  # 从 SMA 完成后开始
if len(rust_ema) != len(pd_ema):
    print(f"  ⚠️ EMA 长度不匹配: Rust={len(rust_ema)}, Pandas={len(pd_ema)}")
compare("EMA", rust_ema, pd_ema)

# 3. WMA
print("\n3. WMA (20)")
rust_wma = wma(close, 20)
# pandas 没有直接 WMA，用 rolling.apply 模拟
weights = np.arange(1, 21)
weight_sum = weights.sum()
pd_wma = []
for i in range(19, len(close)):
    wma_val = np.sum(close[i-19:i+1] * weights) / weight_sum
    pd_wma.append(wma_val)
pd_wma = np.array(pd_wma)
compare("WMA", rust_wma, pd_wma)

# 4. RSI
print("\n4. RSI (14)")
rust_rsi = rsi(close, 14)
if HAS_PANDAS_TA:
    pd_rsi = ta.rsi(pd.Series(close), length=14).dropna().values
else:
    # Wilder 平滑法实现 RSI
    delta = np.diff(close)
    gain = np.where(delta > 0, delta, 0)
    loss = np.where(delta < 0, -delta, 0)
    
    avg_gain = np.zeros(len(gain))
    avg_loss = np.zeros(len(loss))
    avg_gain[13] = np.mean(gain[:14])
    avg_loss[13] = np.mean(loss[:14])
    
    for i in range(14, len(gain)):
        avg_gain[i] = (avg_gain[i-1] * 13 + gain[i]) / 14
        avg_loss[i] = (avg_loss[i-1] * 13 + loss[i]) / 14
    
    rs = avg_gain / np.where(avg_loss == 0, 1e-10, avg_loss)
    pd_rsi = 100 - 100 / (1 + rs)
    pd_rsi = pd_rsi[13:]  # 对齐起始位置

compare("RSI", rust_rsi, pd_rsi)

# 5. MACD
print("\n5. MACD (12,26,9)")
rust_macd = macd(close, 12, 26, 9)
if HAS_PANDAS_TA:
    macd_result = ta.macd(pd.Series(close), fast=12, slow=26, signal=9)
    pd_macd = {
        'macd': macd_result['MACD_12_26_9'].dropna().values,
        'signal': macd_result['MACDs_12_26_9'].dropna().values,
        'histogram': macd_result['MACDh_12_26_9'].dropna().values
    }
else:
    fast_ema = pd.Series(close).ewm(span=12, adjust=False).mean()
    slow_ema = pd.Series(close).ewm(span=26, adjust=False).mean()
    macd_line = (fast_ema - slow_ema).values[25:]
    signal_line = pd.Series(macd_line).ewm(span=9, adjust=False).mean().values[8:]
    histogram = macd_line[-len(signal_line):] - signal_line
    pd_macd = {'macd': macd_line, 'signal': signal_line, 'histogram': histogram}

compare("MACD", rust_macd, pd_macd)

# 6. Bollinger Bands
print("\n6. Bollinger Bands (20, 2)")
rust_boll = bollinger_bands(close, 20, 2.0)
pd_series = pd.Series(close)
pd_rolling_mean = pd_series.rolling(20).mean().values[19:]
pd_rolling_std = pd_series.rolling(20).std(ddof=0).values[19:]  # ddof=0 总体标准差
pd_boll = {
    'upper': pd_rolling_mean + 2 * pd_rolling_std,
    'middle': pd_rolling_mean,
    'lower': pd_rolling_mean - 2 * pd_rolling_std
}
compare("Bollinger", rust_boll, pd_boll)

# 7. ATR
print("\n7. ATR (14)")
rust_atr = atr(high, low, close, 14)
if HAS_PANDAS_TA:
    pd_atr = ta.atr(pd.Series(high), pd.Series(low), pd.Series(close), length=14).dropna().values
else:
    tr = np.maximum(high[1:] - low[1:], 
                    np.maximum(np.abs(high[1:] - close[:-1]), 
                              np.abs(low[1:] - close[:-1])))
    # EMA 平滑
    multiplier = 2 / (14 + 1)
    atr_vals = np.zeros(len(tr))
    atr_vals[13] = np.mean(tr[:14])
    for i in range(14, len(tr)):
        atr_vals[i] = (tr[i] - atr_vals[i-1]) * multiplier + atr_vals[i-1]
    pd_atr = atr_vals[13:]

compare("ATR", rust_atr, pd_atr)

# 8. CCI
print("\n8. CCI (20)")
rust_cci = cci(high, low, close, 20)
if HAS_PANDAS_TA:
    pd_cci = ta.cci(pd.Series(high), pd.Series(low), pd.Series(close), length=20).dropna().values
else:
    tp = (high + low + close) / 3
    pd_cci = []
    for i in range(19, len(tp)):
        window = tp[i-19:i+1]
        mean_tp = np.mean(window)
        mean_dev = np.mean(np.abs(window - mean_tp))
        cci_val = (tp[i] - mean_tp) / (0.015 * mean_dev) if mean_dev > 0 else 0.0
        pd_cci.append(cci_val)
    pd_cci = np.array(pd_cci)

compare("CCI", rust_cci, pd_cci)

# 9. VWAP
print("\n9. VWAP")
rust_vwap = vwap(high, low, close, volume)
typical_price = (high + low + close) / 3
cum_vp = np.cumsum(typical_price * volume)
cum_volume = np.cumsum(volume)
pd_vwap = {'vwap': cum_vp / cum_volume}
compare("VWAP", rust_vwap, pd_vwap)

print("\n" + "=" * 80)
print("准确率测试完成")
print("=" * 80)
