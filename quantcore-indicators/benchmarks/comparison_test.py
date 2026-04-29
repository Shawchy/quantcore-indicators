"""
quantcore-indicators (Rust) vs pandas-ta 性能与功能对比测试

对比维度：
1. 计算性能（不同数据量级）
2. 计算准确性（数值差异）
3. 内存使用
4. 功能完整性

运行方式：
  python benchmarks/comparison_test.py
"""
import sys
import os
import time
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple

# 添加 quantcore-indicators 路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

try:
    from quantcore_indicators import (
        ma, ema, macd, rsi, bollinger_bands, atr, cci,
        kdj, obv, williams_r, adx, wma, stochastic, vwap
    )
    RUST_AVAILABLE = True
    print("✅ quantcore-indicators (Rust) 已加载")
except ImportError:
    RUST_AVAILABLE = False
    print("⚠️ quantcore-indicators (Rust) 未加载，仅测试 pandas-ta")

try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
    print("✅ pandas-ta 已加载")
except ImportError:
    PANDAS_TA_AVAILABLE = False
    print("⚠️ pandas-ta 未安装")


# ============================================================
# 测试数据生成
# ============================================================
def generate_test_data(n: int = 10000) -> pd.DataFrame:
    """生成模拟 OHLCV 数据"""
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    open_ = close + np.random.randn(n) * 0.2
    volume = np.random.randint(1000, 5000, n).astype(float)
    
    return pd.DataFrame({
        'open': open_,
        'high': high,
        'low': low,
        'close': close,
        'volume': volume
    })


# ============================================================
# 性能测试框架
# ============================================================
def benchmark(func, *args, iterations=5, **kwargs):
    """基准测试函数执行时间"""
    times = []
    result = None
    for _ in range(iterations):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        times.append(elapsed * 1000)  # ms
    
    return {
        'avg_ms': np.mean(times),
        'min_ms': np.min(times),
        'max_ms': np.max(times),
        'result': result
    }


def compare_performance(df: pd.DataFrame, iterations=5) -> List[Dict]:
    """对比所有指标的性能"""
    results = []
    n = len(df)
    
    if not (RUST_AVAILABLE and PANDAS_TA_AVAILABLE):
        print("需要同时加载 Rust 和 pandas-ta 才能进行性能对比")
        return results
    
    # 1. MA (简单移动平均)
    for period in [5, 10, 20, 50]:
        rust_res = benchmark(ma, df['close'].values, period, iterations=iterations)
        pandas_ta_res = benchmark(ta.sma, df['close'], length=period, iterations=iterations)
        
        results.append({
            'indicator': 'MA',
            'period': period,
            'data_size': n,
            'rust_avg_ms': rust_res['avg_ms'],
            'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
            'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
            'rust_output_len': len(rust_res['result']),
            'pandas_ta_output_len': len(pandas_ta_res['result']),
        })
    
    # 2. EMA
    for period in [12, 26, 50]:
        rust_res = benchmark(ema, df['close'].values, period, iterations=iterations)
        pandas_ta_res = benchmark(ta.ema, df['close'], length=period, iterations=iterations)
        
        results.append({
            'indicator': 'EMA',
            'period': period,
            'data_size': n,
            'rust_avg_ms': rust_res['avg_ms'],
            'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
            'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
            'rust_output_len': len(rust_res['result']),
            'pandas_ta_output_len': len(pandas_ta_res['result']),
        })
    
    # 3. WMA
    for period in [10, 20]:
        rust_res = benchmark(wma, df['close'].values, period, iterations=iterations)
        pandas_ta_res = benchmark(ta.wma, df['close'], length=period, iterations=iterations)
        
        results.append({
            'indicator': 'WMA',
            'period': period,
            'data_size': n,
            'rust_avg_ms': rust_res['avg_ms'],
            'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
            'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
            'rust_output_len': len(rust_res['result']),
            'pandas_ta_output_len': len(pandas_ta_res['result']),
        })
    
    # 4. MACD
    rust_res = benchmark(macd, df['close'].values, 12, 26, 9, iterations=iterations)
    pandas_ta_res = benchmark(ta.macd, df['close'], fast=12, slow=26, signal=9, iterations=iterations)
    
    results.append({
        'indicator': 'MACD',
        'period': '12,26,9',
        'data_size': n,
        'rust_avg_ms': rust_res['avg_ms'],
        'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
        'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
        'rust_output_len': len(rust_res['result']['macd']),
        'pandas_ta_output_len': len(pandas_ta_res['result'].iloc[:, 0]) if pandas_ta_res['result'] is not None else 0,
    })
    
    # 5. RSI
    for period in [6, 14, 24]:
        rust_res = benchmark(rsi, df['close'].values, period, iterations=iterations)
        pandas_ta_res = benchmark(ta.rsi, df['close'], length=period, iterations=iterations)
        
        results.append({
            'indicator': 'RSI',
            'period': period,
            'data_size': n,
            'rust_avg_ms': rust_res['avg_ms'],
            'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
            'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
            'rust_output_len': len(rust_res['result']),
            'pandas_ta_output_len': len(pandas_ta_res['result']),
        })
    
    # 6. Bollinger Bands
    rust_res = benchmark(bollinger_bands, df['close'].values, 20, 2.0, iterations=iterations)
    pandas_ta_res = benchmark(ta.bbands, df['close'], length=20, std=2.0, iterations=iterations)
    
    results.append({
        'indicator': 'Bollinger Bands',
        'period': '20,2.0',
        'data_size': n,
        'rust_avg_ms': rust_res['avg_ms'],
        'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
        'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
        'rust_output_len': len(rust_res['result']['upper']),
        'pandas_ta_output_len': len(pandas_ta_res['result'].iloc[:, 0]) if pandas_ta_res['result'] is not None else 0,
    })
    
    # 7. ATR
    rust_res = benchmark(atr, df['high'].values, df['low'].values, df['close'].values, 14, iterations=iterations)
    pandas_ta_res = benchmark(ta.atr, df['high'], df['low'], df['close'], length=14, iterations=iterations)
    
    results.append({
        'indicator': 'ATR',
        'period': 14,
        'data_size': n,
        'rust_avg_ms': rust_res['avg_ms'],
        'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
        'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
        'rust_output_len': len(rust_res['result']),
        'pandas_ta_output_len': len(pandas_ta_res['result']),
    })
    
    # 8. CCI
    rust_res = benchmark(cci, df['high'].values, df['low'].values, df['close'].values, 20, iterations=iterations)
    pandas_ta_res = benchmark(ta.cci, df['high'], df['low'], df['close'], length=20, iterations=iterations)
    
    results.append({
        'indicator': 'CCI',
        'period': 20,
        'data_size': n,
        'rust_avg_ms': rust_res['avg_ms'],
        'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
        'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
        'rust_output_len': len(rust_res['result']),
        'pandas_ta_output_len': len(pandas_ta_res['result']),
    })
    
    # 9. KDJ
    rust_res = benchmark(kdj, df['high'].values, df['low'].values, df['close'].values, 9, 3, iterations=iterations)
    pandas_ta_res = benchmark(ta.stoch, df['high'], df['low'], df['close'], k=9, d=3, smooth_k=3, iterations=iterations)
    
    results.append({
        'indicator': 'KDJ',
        'period': '9,3,3',
        'data_size': n,
        'rust_avg_ms': rust_res['avg_ms'],
        'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
        'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
        'rust_output_len': len(rust_res['result']['k']),
        'pandas_ta_output_len': len(pandas_ta_res['result'].iloc[:, 0]) if pandas_ta_res['result'] is not None else 0,
    })
    
    # 10. Williams %R
    rust_res = benchmark(williams_r, df['high'].values, df['low'].values, df['close'].values, 14, iterations=iterations)
    pandas_ta_res = benchmark(ta.willr, df['high'], df['low'], df['close'], length=14, iterations=iterations)
    
    results.append({
        'indicator': 'Williams %R',
        'period': 14,
        'data_size': n,
        'rust_avg_ms': rust_res['avg_ms'],
        'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
        'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
        'rust_output_len': len(rust_res['result']),
        'pandas_ta_output_len': len(pandas_ta_res['result']),
    })
    
    # 11. ADX
    rust_res = benchmark(adx, df['high'].values, df['low'].values, df['close'].values, 14, iterations=iterations)
    pandas_ta_res = benchmark(ta.adx, df['high'], df['low'], df['close'], length=14, iterations=iterations)
    
    results.append({
        'indicator': 'ADX',
        'period': 14,
        'data_size': n,
        'rust_avg_ms': rust_res['avg_ms'],
        'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
        'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
        'rust_output_len': len(rust_res['result']),
        'pandas_ta_output_len': len(pandas_ta_res['result'].iloc[:, 0]) if pandas_ta_res['result'] is not None else 0,
    })
    
    # 12. Stochastic
    rust_res = benchmark(stochastic, df['high'].values, df['low'].values, df['close'].values, 14, 3, iterations=iterations)
    pandas_ta_res = benchmark(ta.stoch, df['high'], df['low'], df['close'], k=14, d=3, smooth_k=3, iterations=iterations)
    
    results.append({
        'indicator': 'Stochastic',
        'period': '14,3',
        'data_size': n,
        'rust_avg_ms': rust_res['avg_ms'],
        'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
        'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
        'rust_output_len': len(rust_res['result']['k']),
        'pandas_ta_output_len': len(pandas_ta_res['result'].iloc[:, 0]) if pandas_ta_res['result'] is not None else 0,
    })
    
    # 13. VWAP
    rust_res = benchmark(vwap, df['high'].values, df['low'].values, df['close'].values, df['volume'].values, iterations=iterations)
    pandas_ta_res = benchmark(ta.vwap, df['high'], df['low'], df['close'], df['volume'], iterations=iterations)
    
    results.append({
        'indicator': 'VWAP',
        'period': '-',
        'data_size': n,
        'rust_avg_ms': rust_res['avg_ms'],
        'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
        'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
        'rust_output_len': len(rust_res['result']['vwap']),
        'pandas_ta_output_len': len(pandas_ta_res['result']),
    })
    
    # 14. OBV
    rust_res = benchmark(obv, df['close'].values, df['volume'].values.astype(int), iterations=iterations)
    pandas_ta_res = benchmark(ta.obv, df['close'], df['volume'], iterations=iterations)
    
    results.append({
        'indicator': 'OBV',
        'period': '-',
        'data_size': n,
        'rust_avg_ms': rust_res['avg_ms'],
        'pandas_ta_avg_ms': pandas_ta_res['avg_ms'],
        'speedup': pandas_ta_res['avg_ms'] / rust_res['avg_ms'] if rust_res['avg_ms'] > 0 else float('inf'),
        'rust_output_len': len(rust_res['result']),
        'pandas_ta_output_len': len(pandas_ta_res['result']),
    })
    
    return results


# ============================================================
# 准确性对比
# ============================================================
def compare_accuracy(df: pd.DataFrame) -> List[Dict]:
    """对比计算结果的数值差异"""
    results = []
    
    if not (RUST_AVAILABLE and PANDAS_TA_AVAILABLE):
        return results
    
    # 1. MA 准确性
    rust_ma = ma(df['close'].values, 20)
    pandas_ta_ma = ta.sma(df['close'], length=20).values
    # 对齐长度
    min_len = min(len(rust_ma), len(pandas_ta_ma))
    rust_ma_aligned = rust_ma[-min_len:]
    pandas_ta_aligned = pandas_ta_ma[-min_len:]
    diff = np.abs(rust_ma_aligned - pandas_ta_aligned)
    max_diff = np.max(diff) if len(diff) > 0 else float('inf')
    mean_diff = np.mean(diff) if len(diff) > 0 else float('inf')
    
    results.append({
        'indicator': 'MA',
        'rust_len': len(rust_ma),
        'pandas_ta_len': len(pandas_ta_ma),
        'max_diff': max_diff,
        'mean_diff': mean_diff,
        'match': max_diff < 1e-10,
    })
    
    # 2. EMA 准确性
    rust_ema_res = ema(df['close'].values, 12)
    pandas_ta_ema = ta.ema(df['close'], length=12).values
    min_len = min(len(rust_ema_res), len(pandas_ta_ema))
    diff = np.abs(rust_ema_res[-min_len:] - pandas_ta_ema[-min_len:])
    max_diff = np.max(diff) if len(diff) > 0 else float('inf')
    
    results.append({
        'indicator': 'EMA',
        'rust_len': len(rust_ema_res),
        'pandas_ta_len': len(pandas_ta_ema),
        'max_diff': max_diff,
        'mean_diff': np.mean(diff) if len(diff) > 0 else float('inf'),
        'match': max_diff < 1e-10,
    })
    
    # 3. MACD 准确性
    rust_macd_res = macd(df['close'].values, 12, 26, 9)
    pandas_ta_macd = ta.macd(df['close'], fast=12, slow=26, signal=9)
    if pandas_ta_macd is not None:
        rust_macd_line = rust_macd_res['macd']
        pandas_ta_macd_line = pandas_ta_macd.iloc[:, 0].dropna().values
        min_len = min(len(rust_macd_line), len(pandas_ta_macd_line))
        diff = np.abs(rust_macd_line[-min_len:] - pandas_ta_macd_line[-min_len:])
        max_diff = np.max(diff) if len(diff) > 0 else float('inf')
        
        results.append({
            'indicator': 'MACD',
            'rust_len': len(rust_macd_line),
            'pandas_ta_len': len(pandas_ta_macd_line),
            'max_diff': max_diff,
            'mean_diff': np.mean(diff) if len(diff) > 0 else float('inf'),
            'match': max_diff < 1e-10,
        })
    
    # 4. RSI 准确性
    rust_rsi_res = rsi(df['close'].values, 14)
    pandas_ta_rsi = ta.rsi(df['close'], length=14).values
    min_len = min(len(rust_rsi_res), len(pandas_ta_rsi))
    diff = np.abs(rust_rsi_res[-min_len:] - pandas_ta_rsi[-min_len:])
    max_diff = np.max(diff) if len(diff) > 0 else float('inf')
    
    results.append({
        'indicator': 'RSI',
        'rust_len': len(rust_rsi_res),
        'pandas_ta_len': len(pandas_ta_rsi),
        'max_diff': max_diff,
        'mean_diff': np.mean(diff) if len(diff) > 0 else float('inf'),
        'match': max_diff < 1e-10,
    })
    
    # 5. ATR 准确性
    rust_atr_res = atr(df['high'].values, df['low'].values, df['close'].values, 14)
    pandas_ta_atr = ta.atr(df['high'], df['low'], df['close'], length=14).values
    min_len = min(len(rust_atr_res), len(pandas_ta_atr))
    diff = np.abs(rust_atr_res[-min_len:] - pandas_ta_atr[-min_len:])
    max_diff = np.max(diff) if len(diff) > 0 else float('inf')
    
    results.append({
        'indicator': 'ATR',
        'rust_len': len(rust_atr_res),
        'pandas_ta_len': len(pandas_ta_atr),
        'max_diff': max_diff,
        'mean_diff': np.mean(diff) if len(diff) > 0 else float('inf'),
        'match': max_diff < 1e-10,
    })
    
    return results


# ============================================================
# 打印报告
# ============================================================
def print_performance_report(results: List[Dict]):
    """打印性能对比报告"""
    print("\n" + "="*100)
    print("quantcore-indicators (Rust) vs pandas-ta 性能对比报告")
    print("="*100)
    
    if not results:
        print("无数据")
        return
    
    # 表头
    print(f"{'指标':<20} {'周期':<12} {'Rust(ms)':<12} {'pandas-ta(ms)':<15} {'加速比':<10} {'输出长度对齐'}")
    print("-"*100)
    
    total_speedup = 0
    count = 0
    
    for r in results:
        indicator = r['indicator']
        period = str(r['period'])
        rust_ms = f"{r['rust_avg_ms']:.3f}"
        pandas_ms = f"{r['pandas_ta_avg_ms']:.3f}"
        speedup = r['speedup']
        total_speedup += speedup
        count += 1
        
        # 检查输出长度是否一致
        len_match = "✅" if r['rust_output_len'] == r['pandas_ta_output_len'] else "❌"
        
        # 高亮显示
        if speedup > 2:
            speedup_str = f"🚀 {speedup:.1f}x"
        elif speedup > 1:
            speedup_str = f"⬆️ {speedup:.1f}x"
        else:
            speedup_str = f"{speedup:.2f}x"
        
        print(f"{indicator:<20} {period:<12} {rust_ms:<12} {pandas_ms:<15} {speedup_str:<10} {len_match}")
    
    print("-"*100)
    avg_speedup = total_speedup / count if count > 0 else 0
    print(f"\n📊 平均加速比: {avg_speedup:.1f}x")


def print_accuracy_report(results: List[Dict]):
    """打印准确性对比报告"""
    print("\n" + "="*100)
    print("quantcore-indicators (Rust) vs pandas-ta 准确性对比报告")
    print("="*100)
    
    if not results:
        print("无数据")
        return
    
    print(f"{'指标':<20} {'Rust输出长度':<15} {'pandas-ta长度':<15} {'最大差异':<15} {'平均差异':<15} {'完全匹配'}")
    print("-"*100)
    
    for r in results:
        indicator = r['indicator']
        rust_len = r['rust_len']
        pandas_len = r['pandas_ta_len']
        max_diff = f"{r['max_diff']:.2e}" if r['max_diff'] != float('inf') else "N/A"
        mean_diff = f"{r['mean_diff']:.2e}" if r['mean_diff'] != float('inf') else "N/A"
        match = "✅ 是" if r['match'] else "❌ 否"
        
        print(f"{indicator:<20} {rust_len:<15} {pandas_len:<15} {max_diff:<15} {mean_diff:<15} {match}")


def print_feature_comparison():
    """打印功能对比表"""
    print("\n" + "="*100)
    print("quantcore-indicators (Rust) vs pandas-ta 功能对比")
    print("="*100)
    
    features = [
        ("语言实现", "Rust", "Python"),
        ("并发安全", "✅ 零数据竞争", "❌ GIL 限制"),
        ("内存安全", "✅ 编译期保证", "⚠️ 运行时检查"),
        ("零拷贝优化", "✅ Arrow 后端", "❌ 无"),
        ("GPU 加速", "❌ 规划中", "❌ 无"),
        ("Python 绑定", "✅ PyO3", "原生"),
        ("NumPy 兼容", "✅ 完全", "原生"),
        ("Arrow 兼容", "✅ 规划中", "❌ 无"),
        ("fallback 机制", "✅ Rust失败自动降级", "❌ 无"),
        ("错误处理", "✅ Rust Result<T, E>", "⚠️ 异常"),
        ("单元测试覆盖", "✅ 59+ 用例", "✅ 官方测试"),
        ("滑动窗口优化", "✅ 单调队列 O(n)", "⚠️ O(n*k)"),
        ("大数数值稳定性", "✅ Kahan 求和", "⚠️ 标准求和"),
        ("文档完整性", "✅ Rustdoc + 中文", "✅ 英文"),
    ]
    
    print(f"{'特性':<25} {'quantcore-indicators':<30} {'pandas-ta':<20}")
    print("-"*100)
    
    for feature, rust_val, pandas_val in features:
        print(f"{feature:<25} {rust_val:<30} {pandas_val:<20}")


# ============================================================
# 主程序
# ============================================================
def main():
    print("="*100)
    print("quantcore-indicators (Rust) vs pandas-ta 全面对比测试")
    print("="*100)
    
    # 测试数据量
    data_sizes = [1000, 10000, 100000]
    
    for size in data_sizes:
        print(f"\n{'='*100}")
        print(f"测试数据量: {size} 条")
        print("="*100)
        
        df = generate_test_data(size)
        
        # 性能对比
        perf_results = compare_performance(df, iterations=3)
        if perf_results:
            print_performance_report(perf_results)
        
        # 准确性对比（仅最大数据集）
        if size == data_sizes[-1]:
            accuracy_results = compare_accuracy(df)
            if accuracy_results:
                print_accuracy_report(accuracy_results)
    
    # 功能对比
    print_feature_comparison()
    
    print("\n" + "="*100)
    print("测试完成!")
    print("="*100)


if __name__ == "__main__":
    main()
