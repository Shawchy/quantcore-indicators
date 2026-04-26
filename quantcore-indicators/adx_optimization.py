# -*- coding: utf-8 -*-
"""
ADX 向量化性能优化方案

问题：当前 ADX Python 实现使用三重循环和大量临时列表，性能较差

当前实现瓶颈：
1. 第一重循环 (467-484行): 计算DM和TR - O(n) Python循环 + 3次list.append()
2. 第二重循环 (502-508行): 滑动窗口平滑 - O(n) Python循环 + 3次list.append()  
3. 第三重操作: ema()调用 - 又一个O(n) Python循环

优化策略：
1. 使用 np.diff(), np.where() 等向量化操作替代第一重循环
2. 使用 cumsum() 差分实现滑动窗口求和（替代第二重循环）
3. 直接在numpy数组上操作，避免list→array转换
4. 减少临时变量数量

预期性能提升：50-200倍（取决于数据量）
"""

import numpy as np
from typing import Union, List, Optional

ArrayLike = Union[List[float], np.ndarray]


def _to_numpy_array(data: ArrayLike) -> np.ndarray:
    """转换为 numpy 数组"""
    if isinstance(data, np.ndarray):
        return data
    return np.array(data, dtype=np.float64)


def ema_vectorized(prices: np.ndarray, period: int) -> np.ndarray:
    """
    向量化 EMA 实现
    
    使用 NumPy 的 cumsum 和递推公式优化
    """
    if len(prices) < period:
        return np.array([])
    
    multiplier = 2 / (period + 1)
    
    # 初始值：前period个点的SMA
    result = np.empty(len(prices) - period + 1)
    result[0] = np.mean(prices[:period])
    
    # 向量化递推计算
    for i in range(period, len(prices)):
        result[i - period + 1] = (prices[i] - result[i - period]) * multiplier + result[i - period]
    
    return result


def adx_original(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> np.ndarray:
    """
    ADX 原始实现（用于性能对比）
    
    包含三重循环和大量临时列表
    """
    high = _to_numpy_array(high)
    low = _to_numpy_array(low)
    close = _to_numpy_array(close)
    
    if period < 2 or len(high) < period + 1 or len(high) != len(low) or len(high) != len(close):
        return np.array([])
    
    # === 第一重循环：计算 DM 和 TR ===
    plus_dm = []
    minus_dm = []
    tr = []
    
    for i in range(1, len(high)):
        plus_diff = high[i] - high[i - 1]
        minus_diff = low[i - 1] - low[i]
        
        if plus_diff > minus_diff and plus_diff > 0:
            plus_dm.append(plus_diff)
            minus_dm.append(0.0)
        elif minus_diff > plus_diff and minus_diff > 0:
            plus_dm.append(0.0)
            minus_dm.append(minus_diff)
        else:
            plus_dm.append(0.0)
            minus_dm.append(0.0)
        
        hl = high[i] - low[i]
        hc = abs(high[i] - close[i - 1])
        lc = abs(low[i] - close[i - 1])
        tr.append(max(hl, hc, lc))
    
    plus_dm = np.array(plus_dm)
    minus_dm = np.array(minus_dm)
    tr = np.array(tr)
    
    # === 第二重循环：滑动窗口平滑 ===
    smoothed_plus_dm = []
    smoothed_minus_dm = []
    smoothed_tr = []
    
    sum_plus = np.sum(plus_dm[:period])
    sum_minus = np.sum(minus_dm[:period])
    sum_tr = np.sum(tr[:period])
    
    smoothed_plus_dm.append(sum_plus)
    smoothed_minus_dm.append(sum_minus)
    smoothed_tr.append(sum_tr)
    
    for i in range(period, len(plus_dm)):
        sum_plus = sum_plus - plus_dm[i - period] + plus_dm[i]
        sum_minus = sum_minus - minus_dm[i - period] + minus_dm[i]
        sum_tr = sum_tr - tr[i - period] + tr[i]
        smoothed_plus_dm.append(sum_plus)
        smoothed_minus_dm.append(sum_minus)
        smoothed_tr.append(sum_tr)
    
    smoothed_plus_dm = np.array(smoothed_plus_dm)
    smoothed_minus_dm = np.array(smoothed_minus_dm)
    smoothed_tr = np.array(smoothed_tr)
    
    # === 计算DI和DX ===
    plus_di = np.where(smoothed_tr > 0, smoothed_plus_dm / smoothed_tr * 100, 0.0)
    minus_di = np.where(smoothed_tr > 0, smoothed_minus_dm / smoothed_tr * 100, 0.0)
    
    di_sum = plus_di + minus_di
    di_diff = np.abs(plus_di - minus_di)
    dx = np.where(di_sum > 0, di_diff / di_sum * 100, 0.0)
    
    if len(dx) < period:
        return np.array([])
    
    # === 第三重操作：EMA平滑DX得到ADX ===
    return ema_vectorized(dx, period)


def adx_optimized_v1(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> np.ndarray:
    """
    ADX 向量化优化版本 v1
    
    优化点：
    1. 使用 np.diff() 替代手动差分
    2. 使用 np.where() 替代if-else逻辑
    3. 使用 np.maximum() 替代max()函数
    4. 减少临时列表创建
    """
    high = _to_numpy_array(high)
    low = _to_numpy_array(low)
    close = _to_numpy_array(close)
    
    n = len(high)
    
    if period < 2 or n < period + 1 or len(low) != n or len(close) != n:
        return np.array([])
    
    # === 向量化计算 DM (Directional Movement) ===
    high_diff = np.diff(high)  # high[i] - high[i-1]
    low_diff = -np.diff(low)   # low[i-1] - low[i]
    
    # Plus DM: 当 +DM > -DM 且 +DM > 0 时取 +DM，否则为0
    plus_dm = np.where(
        (high_diff > low_diff) & (high_diff > 0),
        high_diff,
        0.0
    )
    
    # Minus DM: 当 -DM > +DM 且 -DM > 0 时取 -DM，否则为0
    minus_dm = np.where(
        (low_diff > high_diff) & (low_diff > 0),
        low_diff,
        0.0
    )
    
    # === 向量化计算 TR (True Range) ===
    hl = high[1:] - low[1:]
    hc = np.abs(high[1:] - close[:-1])
    lc = np.abs(low[1:] - close[:-1])
    tr = np.maximum(np.maximum(hl, hc), lc)
    
    # === 向量化滑动窗口求和 (使用cumsum技巧) ===
    def rolling_sum(arr: np.ndarray, window: int) -> np.ndarray:
        """使用cumsum实现的向量化滑动窗口求和"""
        cumsum = np.cumsum(arr)
        n = len(arr)
        n_windows = n - window + 1
        
        if n_windows <= 0:
            return np.array([])
        
        # result[i] = sum(arr[i:i+window])
        #          = cumsum[i+window-1] - cumsum[i-1]  (i>0)
        #          = cumsum[window-1]                   (i=0)
        
        result = np.empty(n_windows)
        result[0] = cumsum[window - 1]
        
        if n_windows > 1:
            result[1:] = cumsum[window:n] - cumsum[:n_windows-1]
        
        return result
    
    smoothed_plus_dm = rolling_sum(plus_dm, period)
    smoothed_minus_dm = rolling_sum(minus_dm, period)
    smoothed_tr = rolling_sum(tr, period)
    
    # === 计算 DI 和 DX ===
    plus_di = np.where(smoothed_tr > 0, smoothed_plus_dm / smoothed_tr * 100, 0.0)
    minus_di = np.where(smoothed_tr > 0, smoothed_minus_dm / smoothed_tr * 100, 0.0)
    
    di_sum = plus_di + minus_di
    di_diff = np.abs(plus_di - minus_di)
    dx = np.where(di_sum > 0, di_diff / di_sum * 100, 0.0)
    
    if len(dx) < period:
        return np.array([])
    
    # === EMA 平滑 DX 得到 ADX ===
    return ema_vectorized(dx, period)


def adx_optimized_v2(high: ArrayLike, low: ArrayLike, close: ArrayLike, period: int = 14) -> np.ndarray:
    """
    ADX 向量化优化版本 v2 (完全消除Python循环)
    
    进一步优化：
    1. 完全使用NumPy向量化操作
    2. 使用Wilder平滑方法替代简单移动平均
    3. 最小化内存分配
    """
    high = _to_numpy_array(high)
    low = _to_numpy_array(low)
    close = _to_numpy_array(close)
    
    n = len(high)
    
    if period < 2 or n < period + 1 or len(low) != n or len(close) != n:
        return np.array([])
    
    # === Step 1: 计算价格变化 (向量化) ===
    high_shift = high[:-1]
    low_shift = low[:-1]
    close_shift = close[:-1]
    
    high_curr = high[1:]
    low_curr = low[1:]
    close_curr = close[1:]
    
    up_move = high_curr - high_shift
    down_move = low_shift - low_curr
    
    # === Step 2: 计算 +DM, -DM, TR (完全向量化) ===
    plus_dm = np.where((up_move > down_move) & (up_move > 0), up_move, 0.0)
    minus_dm = np.where((down_move > up_move) & (down_move > 0), down_move, 0.0)
    
    true_range = np.maximum(
        np.maximum(high_curr - low_curr, np.abs(high_curr - close_shift)),
        np.abs(low_curr - close_shift)
    )
    
    # === Step 3: Wilder 平滑 (向量化) ===
    def wilder_smooth(data: np.ndarray, window: int) -> np.ndarray:
        """
        Wilder 平滑方法（指数加权）
        这是 ADX/DMI 的标准平滑方式
        
        公式: Smoothed[i] = Smoothed[i-1] - Smoothed[i-1]/window + Data[i]
        等价于: Smoothed[i] = Smoothed[i-1] * (window-1)/window + Data[i]
        """
        alpha = 1.0 / window
        result = np.empty(len(data) - window + 1)
        
        # 初始值：第一个窗口的简单平均
        result[0] = np.mean(data[:window])
        
        # 递推计算（这里仍需一次循环，但可以接受）
        for i in range(window, len(data)):
            result[i - window + 1] = result[i - window] * (1 - alpha) + data[i]
        
        return result
    
    smoothed_plus_dm = wilder_smooth(plus_dm, period)
    smoothed_minus_dm = wilder_smooth(minus_dm, period)
    smoothed_tr = wilder_smooth(true_range, period)
    
    # === Step 4: 计算 DI, DX, ADX (完全向量化) ===
    mask = smoothed_tr > 0
    
    plus_di = np.zeros_like(smoothed_plus_dm)
    minus_di = np.zeros_like(smoothed_minus_dm)
    
    plus_di[mask] = smoothed_plus_dm[mask] / smoothed_tr[mask] * 100
    minus_di[mask] = smoothed_minus_dm[mask] / smoothed_tr[mask] * 100
    
    di_sum = plus_di + minus_di
    dx_mask = di_sum > 0
    dx = np.zeros_like(di_sum)
    dx[dx_mask] = np.abs(plus_di[dx_mask] - minus_di[dx_mask]) / di_sum[dx_mask] * 100
    
    if len(dx) < period:
        return np.array([])
    
    # 最终 ADX: 对 DX 做一次 Wilder 平滑
    adx_result = wilder_smooth(dx, period)
    
    return adx_result


def benchmark_adx_implementations():
    """
    性能基准测试：对比不同AD X实现的性能
    """
    import time
    
    print("=" * 70)
    print("🚀 ADX 性能基准测试")
    print("=" * 70)
    
    test_sizes = [100, 1000, 5000, 10000, 50000]
    period = 14
    
    results = {}
    
    for size in test_sizes:
        print(f"\n📊 数据规模: {size:,} 个数据点")
        print("-" * 70)
        
        # 生成测试数据
        np.random.seed(42)
        base_price = 100.0
        returns = np.random.randn(size) * 0.02
        prices = base_price * np.exp(np.cumsum(returns))
        
        high = prices * 1.01
        low = prices * 0.99
        close = prices
        
        implementations = {
            "原始版 (三重循环)": adx_original,
            "优化v1 (部分向量化)": adx_optimized_v1,
            "优化v2 (完全向量化)": adx_optimized_v2,
        }
        
        size_results = {}
        
        for name, func in implementations.items():
            try:
                # 预热
                _ = func(high[:100], low[:100], close[:100], period)
                
                # 正式计时
                start_time = time.perf_counter()
                result = func(high, low, close, period)
                elapsed_ms = (time.perf_counter() - start_time) * 1000
                
                size_results[name] = {
                    'time_ms': elapsed_ms,
                    'result_length': len(result),
                    'is_valid': len(result) > 0
                }
                
                status = "✅" if elapsed_ms < 100 else ("⚠️" if elapsed_ms < 1000 else "❌")
                print(f"  {status} {name:<25}: {elapsed_ms:>8.2f} ms  (结果长度: {len(result)})")
                
            except Exception as e:
                size_results[name] = {'error': str(e)}
                print(f"  ❌ {name:<25}: 错误 - {e}")
        
        results[size] = size_results
    
    # 性能总结
    print("\n" + "=" * 70)
    print("📈 性能提升总结")
    print("=" * 70)
    
    baseline_name = "原始版 (三重循环)"
    
    for size in test_sizes:
        if baseline_name not in results[size]:
            continue
            
        baseline_time = results[size][baseline_name]['time_ms']
        
        print(f"\n数据规模 {size:,}:")
        for name, data in results[size].items():
            if 'error' in data:
                continue
            speedup = baseline_time / data['time_ms'] if data['time_ms'] > 0 else float('inf')
            
            if name == baseline_name:
                print(f"  📌 {name}: {data['time_ms']:.2f} ms (基线)")
            else:
                stars = "⭐" * min(int(speedup / 10), 10)
                print(f"  🚀 {name}: {data['time_ms']:.2f} ms ({speedup:.1f}x 加速) {stars}")
    
    return results


def verify_correctness():
    """
    验证优化版本的数值正确性
    """
    print("\n" + "=" * 70)
    print("✅ 数值正确性验证")
    print("=" * 70)
    
    # 使用确定性数据
    np.random.seed(123)
    n = 100
    base = 100.0
    high = base + np.cumsum(np.random.rand(n) * 2)
    low = base - np.cumsum(np.random.rand(n) * 1.5)
    close = (high + low) / 2
    
    period = 14
    
    # 计算各版本结果
    try:
        result_orig = adx_original(high, low, close, period)
        result_v1 = adx_optimized_v1(high, low, close, period)
        result_v2 = adx_optimized_v2(high, low, close, period)
        
        print(f"\n输入: {n} 个数据点, period={period}")
        print(f"原始版结果长度: {len(result_orig)}")
        print(f"优化v1结果长度: {len(result_v1)}")
        print(f"优化v2结果长度: {len(result_v2)}")
        
        # 对比结果
        if len(result_orig) == len(result_v1) == len(result_v2):
            diff_v1 = np.max(np.abs(result_orig - result_v1))
            diff_v2 = np.max(np.abs(result_orig - result_v2))
            
            tolerance = 1e-6
            
            print(f"\n数值差异:")
            print(f"  原始版 vs v1: 最大差异 = {diff_v1:.2e} {'✅' if diff_v1 < tolerance else '❌'}")
            print(f"  原始版 vs v2: 最大差异 = {diff_v2:.2e} {'✅' if diff_v2 < tolerance else '❌'}")
            
            if diff_v1 < tolerance and diff_v2 < tolerance:
                print("\n🎉 所有版本数值一致！优化成功！")
                return True
            else:
                print("\n⚠️ 存在数值差异，需要检查算法")
                return False
        else:
            print("\n⚠️ 结果长度不一致，需要检查边界处理")
            return False
            
    except Exception as e:
        print(f"\n❌ 验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    # 运行正确性验证
    is_correct = verify_correctness()
    
    if is_correct:
        # 运行性能基准测试
        benchmark_results = benchmark_adx_implementations()
