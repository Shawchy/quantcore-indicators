"""
quantcore-indicators (Rust) 纯性能测试

测试不同数据量级下的计算性能，无需 pandas-ta 对比

运行：python benchmarks/rust_only_benchmark.py
"""
import sys
import os
import time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from quantcore_indicators import (
    ma, ema, wma, macd, rsi, bollinger_bands, atr, cci,
    kdj, obv, williams_r, adx, stochastic, vwap
)


def generate_test_data(n):
    np.random.seed(42)
    close = 100 + np.cumsum(np.random.randn(n) * 0.5)
    high = close + np.abs(np.random.randn(n) * 0.3)
    low = close - np.abs(np.random.randn(n) * 0.3)
    volume = np.random.randint(1000, 5000, n).astype(float)
    return {
        'close': close.tolist(),
        'high': high.tolist(),
        'low': low.tolist(),
        'volume': volume.tolist(),
    }


def benchmark(func, *args, iterations=10, **kwargs):
    times = []
    result = None
    for _ in range(iterations):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = (time.perf_counter() - start) * 1000
        times.append(elapsed)
    return {
        'avg_ms': np.mean(times),
        'min_ms': np.min(times),
        'max_ms': np.max(times),
        'result': result
    }


def test_indicators(data, n, iterations=10):
    results = []
    
    tests = [
        ('MA(20)', lambda: ma(data['close'], 20)),
        ('EMA(12)', lambda: ema(data['close'], 12)),
        ('WMA(20)', lambda: wma(data['close'], 20)),
        ('MACD(12,26,9)', lambda: macd(data['close'], 12, 26, 9)),
        ('RSI(14)', lambda: rsi(data['close'], 14)),
        ('Bollinger(20,2)', lambda: bollinger_bands(data['close'], 20, 2.0)),
        ('ATR(14)', lambda: atr(data['high'], data['low'], data['close'], 14)),
        ('CCI(20)', lambda: cci(data['high'], data['low'], data['close'], 20)),
        ('KDJ(9,3,3)', lambda: kdj(data['high'], data['low'], data['close'], 9, 3, 3)),
        ('OBV', lambda: obv(data['close'], [int(v) for v in data['volume']])),
        ('Williams %R(14)', lambda: williams_r(data['high'], data['low'], data['close'], 14)),
        ('ADX(14)', lambda: adx(data['high'], data['low'], data['close'], 14)),
        ('Stochastic(14,3)', lambda: stochastic(data['high'], data['low'], data['close'], 14, 3)),
        ('VWAP', lambda: vwap(data['high'], data['low'], data['close'], data['volume'])),
    ]
    
    for name, func in tests:
        try:
            res = benchmark(func, iterations=iterations)
            result = res['result']
            # Handle different return types
            if isinstance(result, list):
                output_len = len(result)
            elif isinstance(result, dict):
                output_len = len(result.get('k', result.get('macd', result.get('vwap', []))))
            else:
                # numpy array
                output_len = len(result)
            results.append({
                'indicator': name,
                'avg_ms': res['avg_ms'],
                'min_ms': res['min_ms'],
                'max_ms': res['max_ms'],
                'output_len': output_len,
            })
        except Exception as e:
            results.append({
                'indicator': name,
                'avg_ms': float('inf'),
                'min_ms': float('inf'),
                'max_ms': float('inf'),
                'output_len': 0,
                'error': str(e),
            })
    
    return results


def print_report(results, n):
    print(f"\n{'='*80}")
    print(f"数据量: {n:,} 条")
    print(f"{'='*80}")
    print(f"{'指标':<20} {'平均(ms)':<12} {'最小(ms)':<12} {'最大(ms)':<12} {'输出长度':<12}")
    print("-"*80)
    
    total_avg = 0
    count = 0
    
    for r in results:
        avg = r['avg_ms']
        if avg == float('inf'):
            status = f"❌ {r.get('error', '未知错误')}"
            print(f"{r['indicator']:<20} {'N/A':<12} {'N/A':<12} {'N/A':<12} {'N/A':<12} {status}")
        else:
            avg_str = f"{avg:.3f}"
            min_str = f"{r['min_ms']:.3f}"
            max_str = f"{r['max_ms']:.3f}"
            total_avg += avg
            count += 1
            
            # 性能标记
            if avg < 1:
                marker = "⚡"
            elif avg < 10:
                marker = "🚀"
            elif avg < 50:
                marker = "✅"
            else:
                marker = "⚠️"
            
            print(f"{r['indicator']:<20} {avg_str:<12} {min_str:<12} {max_str:<12} {r['output_len']:<12} {marker}")
    
    if count > 0:
        print("-"*80)
        avg_total = total_avg / count
        print(f"\n📊 14 个指标平均计算时间: {avg_total:.3f} ms")
        print(f"⚡ 预计全量计算 (14 指标) 总耗时: {total_avg:.3f} ms")


def main():
    print("="*80)
    print("quantcore-indicators (Rust) 性能基准测试")
    print("="*80)
    
    data_sizes = [1000, 10000, 100000, 500000]
    
    for size in data_sizes:
        data = generate_test_data(size)
        iterations = 10 if size <= 10000 else 5
        
        results = test_indicators(data, size, iterations=iterations)
        print_report(results, size)
    
    print(f"\n{'='*80}")
    print("✅ 测试完成!")
    print("="*80)


if __name__ == "__main__":
    main()
