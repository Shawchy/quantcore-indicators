"""
quantcore-indicators (Rust) vs pandas 向量化实现 真实性能对比

使用 pandas 原生方法（不依赖 pandas-ta）作为对比基准

运行：python benchmarks/final_comparison.py
"""
import sys
import os
import time
import numpy as np
import pandas as pd

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from quantcore_indicators import ma, ema, macd, rsi, bollinger_bands, atr, cci, kdj, williams_r, adx, wma, stochastic, vwap, obv

def gen(n):
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    volume = np.random.randint(1000, 5000, n).astype(float)
    return pd.DataFrame({'open': close, 'high': high, 'low': low, 'close': close, 'volume': volume})


def bench(func, iters=5):
    ts = []
    r = None
    for _ in range(iters):
        t0 = time.perf_counter()
        r = func()
        ts.append((time.perf_counter() - t0) * 1000)
    return np.mean(ts), r


def pd_sma(s, length):
    return s.rolling(length).mean()

def pd_ema(s, length):
    return s.ewm(span=length, adjust=False).mean()

def pd_wma(s, length):
    weights = np.arange(1, length + 1)
    return s.rolling(length).apply(lambda x: np.dot(x, weights) / weights.sum(), raw=True)

def pd_rsi(s, length):
    delta = s.diff()
    gain = delta.where(delta > 0, 0.0)
    loss = (-delta).where(delta < 0, 0.0)
    avg_gain = gain.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1/length, min_periods=length, adjust=False).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def pd_macd(s, fast=12, slow=26, signal=9):
    ema_fast = s.ewm(span=fast, adjust=False).mean()
    ema_slow = s.ewm(span=slow, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    hist = macd_line - signal_line
    return macd_line, signal_line, hist

def pd_bbands(s, length=20, std=2.0):
    sma = s.rolling(length).mean()
    std_dev = s.rolling(length).std()
    upper = sma + std * std_dev
    lower = sma - std * std_dev
    return upper, sma, lower

def pd_atr(high, low, close, length=14):
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(length).mean()

def pd_cci(high, low, close, length=20):
    tp = (high + low + close) / 3
    sma = tp.rolling(length).mean()
    md = tp.rolling(length).apply(lambda x: np.mean(np.abs(x - np.mean(x))), raw=True)
    return (tp - sma) / (0.015 * md)

def pd_kdj(high, low, close, k=9, d=3, smooth_k=3):
    lowest_low = low.rolling(k).min()
    highest_high = high.rolling(k).max()
    rsv = (close - lowest_low) / (highest_high - lowest_low) * 100
    k_line = rsv.rolling(smooth_k).mean()
    d_line = k_line.rolling(d).mean()
    j_line = 3 * k_line - 2 * d_line
    return k_line, d_line, j_line

def pd_willr(high, low, close, length=14):
    highest_high = high.rolling(length).max()
    lowest_low = low.rolling(length).min()
    return (highest_high - close) / (highest_high - lowest_low) * -100

def pd_adx(high, low, close, length=14):
    plus_dm = high.diff()
    minus_dm = -low.diff()
    plus_dm = plus_dm.where((plus_dm > minus_dm) & (plus_dm > 0), 0)
    minus_dm = minus_dm.where((minus_dm > plus_dm) & (minus_dm > 0), 0)
    tr1 = high - low
    tr2 = (high - close.shift()).abs()
    tr3 = (low - close.shift()).abs()
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(length).mean()
    plus_di = 100 * (plus_dm.rolling(length).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(length).mean() / atr)
    dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di)
    return dx.rolling(length).mean()

def pd_stoch(high, low, close, k=14, d=3, smooth_k=3):
    return pd_kdj(high, low, close, k, d, smooth_k)

def pd_vwap(high, low, close, volume):
    tp = (high + low + close) / 3
    return (tp * volume).cumsum() / volume.cumsum()

def pd_obv(close, volume):
    sign = close.diff().apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    return (sign * volume).cumsum()


def main():
    print("="*100)
    print("quantcore-indicators (Rust) vs pandas 向量化实现 真实性能对比")
    print("="*100)
    print()

    sizes = [1000, 10000, 100000]
    iters = [10, 5, 3]

    for sz, it in zip(sizes, iters):
        df = gen(sz)
        c = df['close'].values
        h = df['high'].values
        l = df['low'].values
        v = df['volume'].values

        cp = c.tolist()
        hp = h.tolist()
        lp = l.tolist()
        vp = v.tolist()

        print(f"{'='*100}")
        print(f"数据量: {sz:,} 条  (迭代 {it} 次取平均)")
        print(f"{'='*100}")
        print(f"{'指标':<20} {'Rust(ms)':<12} {'pandas(ms)':<12} {'加速比':<10} {'算法差异'}")
        print("-"*100)

        tests = [
            ('MA(20)',
             lambda: bench(lambda: ma(cp, 20), it),
             lambda: bench(lambda: pd_sma(df['close'].copy(), 20).sum(), it)),
            ('EMA(12)',
             lambda: bench(lambda: ema(cp, 12), it),
             lambda: bench(lambda: pd_ema(df['close'].copy(), 12).sum(), it)),
            ('WMA(20)',
             lambda: bench(lambda: wma(cp, 20), it),
             lambda: bench(lambda: pd_wma(df['close'].copy(), 20).sum(), it)),
            ('RSI(14)',
             lambda: bench(lambda: rsi(cp, 14), it),
             lambda: bench(lambda: pd_rsi(df['close'].copy(), 14).sum(), it)),
            ('MACD(12,26,9)',
             lambda: bench(lambda: macd(cp, 12, 26, 9), it),
             lambda: bench(lambda: pd_macd(df['close'].copy(), 12, 26, 9)[0].sum(), it)),
            ('Bollinger(20,2)',
             lambda: bench(lambda: bollinger_bands(cp, 20, 2.0), it),
             lambda: bench(lambda: pd_bbands(df['close'].copy(), 20, 2.0)[0].sum(), it)),
            ('ATR(14)',
             lambda: bench(lambda: atr(hp, lp, cp, 14), it),
             lambda: bench(lambda: pd_atr(df['high'].copy(), df['low'].copy(), df['close'].copy(), 14).sum(), it)),
            ('CCI(20)',
             lambda: bench(lambda: cci(hp, lp, cp, 20), it),
             lambda: bench(lambda: pd_cci(df['high'].copy(), df['low'].copy(), df['close'].copy(), 20).sum(), it)),
            ('KDJ(9,3,3)',
             lambda: bench(lambda: kdj(hp, lp, cp, 9, 3, 3), it),
             lambda: bench(lambda: pd_kdj(df['high'].copy(), df['low'].copy(), df['close'].copy(), 9, 3, 3)[0].sum(), it)),
            ('Williams %R(14)',
             lambda: bench(lambda: williams_r(hp, lp, cp, 14), it),
             lambda: bench(lambda: pd_willr(df['high'].copy(), df['low'].copy(), df['close'].copy(), 14).sum(), it)),
            ('ADX(14)',
             lambda: bench(lambda: adx(hp, lp, cp, 14), it),
             lambda: bench(lambda: pd_adx(df['high'].copy(), df['low'].copy(), df['close'].copy(), 14).sum(), it)),
            ('Stochastic(14,3)',
             lambda: bench(lambda: stochastic(hp, lp, cp, 14, 3), it),
             lambda: bench(lambda: pd_stoch(df['high'].copy(), df['low'].copy(), df['close'].copy(), 14, 3, 3)[0].sum(), it)),
            ('VWAP',
             lambda: bench(lambda: vwap(hp, lp, cp, vp), it),
             lambda: bench(lambda: pd_vwap(df['high'].copy(), df['low'].copy(), df['close'].copy(), df['volume'].copy()).sum(), it)),
            ('OBV',
             lambda: bench(lambda: obv(cp, [int(x) for x in vp]), it),
             lambda: bench(lambda: pd_obv(df['close'].copy(), df['volume'].copy()).sum(), it)),
        ]

        speedups = []
        for name, rust_f, pd_f in tests:
            try:
                rust_ms, rust_r = rust_f()
                pd_ms, pd_r = pd_f()

                if hasattr(pd_r, '__len__') and len(pd_r) == 3:
                    pd_ms = np.mean([bench(lambda: pr, it)[0] for pr in pd_r])
                    pd_r = pd_r[0]

                speedup = pd_ms / rust_ms if rust_ms > 0 else 0
                speedups.append(speedup)

                if speedup > 50:
                    s = f"🚀🚀 {speedup:.0f}x"
                elif speedup > 10:
                    s = f"🚀 {speedup:.1f}x"
                elif speedup > 2:
                    s = f"⬆️ {speedup:.1f}x"
                elif speedup > 1:
                    s = f"  {speedup:.1f}x"
                else:
                    s = f"  {speedup:.2f}x"

                algo_note = ""
                if 'KDJ' in name or 'Stochastic' in name:
                    algo_note = "Rust O(n) vs pandas O(n*k)"
                elif 'WMA' in name:
                    algo_note = "Rust 直接循环 vs pandas rolling.apply"

                print(f"{name:<20} {rust_ms:<12.3f} {pd_ms:<12.3f} {s:<12} {algo_note}")
            except Exception as e:
                print(f"{name:<20} {'ERR':<12} {'ERR':<12} {'N/A':<12} ❌ {e}")

        if speedups:
            avg = np.mean(speedups)
            print("-"*100)
            print(f"📊 14 个指标平均加速比: {avg:.1f}x")
            fastest = min(speedups)
            slowest = max(speedups)
            print(f"⚡ 最低加速: {fastest:.1f}x  |  最高加速: {slowest:.1f}x")
        print()

    print("="*100)
    print("✅ 测试完成!")
    print("="*100)


if __name__ == "__main__":
    main()
