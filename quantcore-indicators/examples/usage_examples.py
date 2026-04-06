# -*- coding: utf-8 -*-
"""
QuantCore Indicators 使用示例

展示如何使用高性能 Rust 指标库
"""

import numpy as np
import pandas as pd
from quantcore_indicators import ma, ema, macd, rsi, bollinger_bands, atr, kdj, obv
import time


def example_basic_usage():
    """基础使用示例"""
    print("="*60)
    print("基础使用示例")
    print("="*60)
    
    # 生成模拟数据
    prices = np.random.rand(100) * 100 + 50
    
    # 移动平均
    ma_values = ma(prices, 20)
    print(f"\nMA(20): 长度={len(ma_values)}, 最新值={ma_values[-1]:.2f}")
    
    # RSI
    rsi_values = rsi(prices, 14)
    print(f"RSI(14): 长度={len(rsi_values)}, 最新值={rsi_values[-1]:.2f}")
    
    # MACD
    macd_result = macd(prices)
    print(f"MACD: 长度={len(macd_result['macd'])}, 最新值={macd_result['macd'][-1]:.2f}")
    
    # 布林带
    boll = bollinger_bands(prices)
    print(f"布林带：上轨={boll['upper'][-1]:.2f}, 中轨={boll['middle'][-1]:.2f}, 下轨={boll['lower'][-1]:.2f}")


def example_performance_comparison():
    """性能对比示例"""
    print("\n" + "="*60)
    print("性能对比（Rust vs 纯 Python）")
    print("="*60)
    
    # 生成大数据集
    sizes = [1000, 5000, 10000]
    
    for size in sizes:
        prices = np.random.rand(size) * 100 + 50
        
        # Rust 实现
        start = time.time()
        ma_rust = ma(prices, 20)
        rust_time = time.time() - start
        
        # 纯 Python 实现（模拟）
        start = time.time()
        ma_python = [np.mean(prices[i-20+1:i+1]) for i in range(19, len(prices))]
        python_time = time.time() - start
        
        speedup = python_time / rust_time if rust_time > 0 else float('inf')
        
        print(f"\n数据量：{size}")
        print(f"  Rust 实现：{rust_time*1000:.2f}ms")
        print(f"  纯 Python: {python_time*1000:.2f}ms")
        print(f"  性能提升：{speedup:.1f}x")


def example_with_pandas():
    """Pandas 集成示例"""
    print("\n" + "="*60)
    print("Pandas 集成示例")
    print("="*60)
    
    # 创建 DataFrame
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    df = pd.DataFrame({
        'date': dates,
        'close': np.random.rand(100) * 100 + 50,
        'high': np.random.rand(100) * 100 + 55,
        'low': np.random.rand(100) * 100 + 45,
        'volume': np.random.randint(1000, 10000, 100)
    })
    
    # 计算指标
    df['ma20'] = ma(df['close'].values, 20)
    df['rsi14'] = rsi(df['close'].values, 14)
    
    # MACD
    macd_result = macd(df['close'].values)
    df['macd'] = macd_result['macd']
    df['signal'] = macd_result['signal']
    
    # 布林带
    boll = bollinger_bands(df['close'].values)
    df['boll_upper'] = boll['upper']
    df['boll_middle'] = boll['middle']
    df['boll_lower'] = boll['lower']
    
    # 显示结果
    print("\n最后 5 行数据:")
    print(df[['date', 'close', 'ma20', 'rsi14', 'macd']].tail())
    
    print("\n布林带宽度:")
    df['boll_width'] = (df['boll_upper'] - df['boll_lower']) / df['boll_middle']
    print(f"  平均宽度：{df['boll_width'].mean():.2%}")


def example_kdj():
    """KDJ 指标示例"""
    print("\n" + "="*60)
    print("KDJ 指标示例")
    print("="*60)
    
    # 生成 OHLC 数据
    high = np.random.rand(100) * 10 + 100
    low = high - np.random.rand(100) * 5
    close = low + np.random.rand(100) * 5
    
    # 计算 KDJ
    kdj_result = kdj(high, low, close)
    
    print(f"\nK 值：最新={kdj_result['k'][-1]:.2f}")
    print(f"D 值：最新={kdj_result['d'][-1]:.2f}")
    print(f"J 值：最新={kdj_result['j'][-1]:.2f}")
    
    # 金叉死叉判断
    k = kdj_result['k']
    d = kdj_result['d']
    
    for i in range(1, len(k)):
        if k[i] > d[i] and k[i-1] <= d[i-1]:
            print(f"  第{i}天：金叉信号！")
        elif k[i] < d[i] and k[i-1] >= d[i-1]:
            print(f"  第{i}天：死叉信号！")


def example_obv():
    """OBV 指标示例"""
    print("\n" + "="*60)
    print("OBV 指标示例")
    print("="*60)
    
    # 生成数据
    close = np.cumsum(np.random.randn(100)) + 100
    volume = np.random.randint(1000, 10000, 100)
    
    # 计算 OBV
    obv_values = obv(close, volume)
    
    print(f"\nOBV 趋势:")
    print(f"  初始值：{obv_values[0]:.0f}")
    print(f"  最终值：{obv_values[-1]:.0f}")
    print(f"  变化：{obv_values[-1] - obv_values[0]:.0f}")
    
    # OBV 与价格背离检测
    price_trend = close[-1] > close[0]
    obv_trend = obv_values[-1] > obv_values[0]
    
    if price_trend and not obv_trend:
        print("  ⚠️ 顶背离：价格上涨，OBV 下跌")
    elif not price_trend and obv_trend:
        print("  ⚠️ 底背离：价格下跌，OBV 上涨")
    else:
        print("  ✓ 量价配合正常")


def example_atr():
    """ATR 指标示例"""
    print("\n" + "="*60)
    print("ATR 指标示例（波动率）")
    print("="*60)
    
    # 生成数据
    high = np.random.rand(100) * 10 + 100
    low = high - np.random.rand(100) * 5
    close = low + np.random.rand(100) * 5
    
    # 计算 ATR
    atr_values = atr(high, low, close, 14)
    
    print(f"\nATR 统计:")
    print(f"  平均值：{np.mean(atr_values):.2f}")
    print(f"  最大值：{np.max(atr_values):.2f}")
    print(f"  最小值：{np.min(atr_values):.2f}")
    print(f"  当前值：{atr_values[-1]:.2f}")
    
    # 波动率评估
    avg_price = np.mean(close)
    atr_percent = atr_values[-1] / avg_price * 100
    
    print(f"\n波动率评估:")
    print(f"  ATR/价格：{atr_percent:.2f}%")
    
    if atr_percent > 5:
        print("  ⚠️ 高波动")
    elif atr_percent < 2:
        print("  ✓ 低波动")
    else:
        print("  正常波动")


def main():
    """运行所有示例"""
    print("\n" + "="*70)
    print("QuantCore Indicators 使用示例")
    print("="*70)
    
    example_basic_usage()
    example_performance_comparison()
    example_with_pandas()
    example_kdj()
    example_obv()
    example_atr()
    
    print("\n" + "="*70)
    print("示例运行完成！")
    print("="*70)


if __name__ == '__main__':
    main()
