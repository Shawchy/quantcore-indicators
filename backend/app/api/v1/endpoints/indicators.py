"""
技术指标健康检查端点
提供指标库状态、性能测试等功能
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, Any, List
import time
import pandas as pd
import numpy as np
from loguru import logger

from app.processing.indicators_manager import (
    TALIB_AVAILABLE, 
    PANDAS_TA_AVAILABLE,
    get_indicators_manager
)

router = APIRouter()


@router.get("/health")
async def check_indicators_health() -> Dict[str, Any]:
    """
    检查指标库健康状态
    
    返回:
    - TA-Lib 是否可用
    - pandas-ta 是否可用
    - 当前使用的指标库
    - 性能对比测试结果
    """
    # 获取指标管理器
    indicator_manager = get_indicators_manager()
    
    # 确定当前使用的库
    if indicator_manager.prefer_talib:
        active_library = "TA-Lib"
    elif indicator_manager.use_pandas_ta:
        active_library = "pandas-ta"
    else:
        active_library = "pure_python"
    
    return {
        "status": "healthy",
        "libraries": {
            "talib": {
                "available": TALIB_AVAILABLE,
                "version": get_talib_version() if TALIB_AVAILABLE else None
            },
            "pandas_ta": {
                "available": PANDAS_TA_AVAILABLE,
                "version": get_pandas_ta_version() if PANDAS_TA_AVAILABLE else None
            }
        },
        "configuration": {
            "prefer_talib": indicator_manager.prefer_talib,
            "active_library": active_library
        },
        "supported_indicators": get_supported_indicators()
    }


@router.get("/benchmark")
async def benchmark_indicators() -> Dict[str, Any]:
    """
    指标计算性能基准测试
    
    测试各指标库的性能表现
    """
    # 生成测试数据
    np.random.seed(42)
    n_samples = 1000
    
    df = pd.DataFrame({
        'open': np.random.uniform(10, 100, n_samples),
        'high': np.random.uniform(10, 100, n_samples),
        'low': np.random.uniform(10, 100, n_samples),
        'close': np.random.uniform(10, 100, n_samples),
        'volume': np.random.uniform(1000000, 10000000, n_samples)
    })
    
    # 确保 high > close > low
    df['high'] = df[['open', 'high', 'close', 'low']].max(axis=1)
    df['low'] = df[['open', 'high', 'close', 'low']].min(axis=1)
    
    indicator_manager = get_indicators_manager()
    results = {}
    
    # 测试 MA
    results['ma'] = benchmark_single_indicator(
        indicator_manager.calculate_ma, 
        df, 
        periods=[5, 10, 20, 60]
    )
    
    # 测试 MACD
    results['macd'] = benchmark_single_indicator(
        indicator_manager.calculate_macd, 
        df
    )
    
    # 测试 RSI
    results['rsi'] = benchmark_single_indicator(
        indicator_manager.calculate_rsi, 
        df, 
        periods=[6, 12, 24]
    )
    
    # 测试 BOLL
    results['boll'] = benchmark_single_indicator(
        indicator_manager.calculate_bollinger_bands, 
        df
    )
    
    # 测试 KDJ (只有 pandas-ta 支持)
    if PANDAS_TA_AVAILABLE:
        results['kdj'] = benchmark_single_indicator(
            indicator_manager.calculate_kdj, 
            df
        )
    
    # 测试 ATR
    results['atr'] = benchmark_single_indicator(
        indicator_manager.calculate_atr, 
        df
    )
    
    return {
        "status": "success",
        "data_samples": n_samples,
        "active_library": "TA-Lib" if indicator_manager.prefer_talib else "pandas-ta",
        "benchmark_results": results,
        "timestamp": pd.Timestamp.now().isoformat()
    }


def benchmark_single_indicator(func, df: pd.DataFrame, **kwargs) -> Dict[str, Any]:
    """
    测试单个指标的计算性能
    
    Args:
        func: 指标计算函数
        df: 测试数据
        kwargs: 函数参数
        
    Returns:
        性能测试结果
    """
    # 预热（第一次计算可能较慢）
    try:
        _ = func(df.copy(), **kwargs)
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
    
    # 正式测试（多次计算取平均）
    n_iterations = 10
    times = []
    
    for _ in range(n_iterations):
        start = time.time()
        try:
            _ = func(df.copy(), **kwargs)
            elapsed = time.time() - start
            times.append(elapsed * 1000)  # 转换为毫秒
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
    
    return {
        "status": "success",
        "avg_time_ms": np.mean(times),
        "min_time_ms": np.min(times),
        "max_time_ms": np.max(times),
        "std_dev_ms": np.std(times)
    }


def get_talib_version() -> str:
    """获取 TA-Lib 版本"""
    try:
        import talib
        return talib.__version__
    except ImportError:
        return "unknown"


def get_pandas_ta_version() -> str:
    """获取 pandas-ta 版本"""
    try:
        import pandas_ta as ta
        return ta.__version__
    except ImportError:
        return "unknown"


def get_supported_indicators() -> List[str]:
    """获取支持的指标列表"""
    indicator_manager = get_indicators_manager()
    
    indicators = [
        "MA (移动平均线)",
        "EMA (指数平均线)",
        "MACD (异同移动平均线)",
        "RSI (相对强弱指标)",
        "BOLL (布林带)",
        "ATR (平均真实波幅)"
    ]
    
    # KDJ 只有 pandas-ta 支持
    if indicator_manager.use_pandas_ta:
        indicators.append("KDJ (随机指标)")
    
    return indicators


@router.get("/compare")
async def compare_libraries() -> Dict[str, Any]:
    """
    对比 TA-Lib 和 pandas-ta 的性能
    
    返回两个库在不同指标上的性能差异
    """
    if not (TALIB_AVAILABLE and PANDAS_TA_AVAILABLE):
        raise HTTPException(
            status_code=400, 
            detail="需要同时安装 TA-Lib 和 pandas-ta 才能进行对比"
        )
    
    # 生成测试数据
    np.random.seed(42)
    n_samples = 1000
    
    df = pd.DataFrame({
        'open': np.random.uniform(10, 100, n_samples),
        'high': np.random.uniform(10, 100, n_samples),
        'low': np.random.uniform(10, 100, n_samples),
        'close': np.random.uniform(10, 100, n_samples),
        'volume': np.random.uniform(1000000, 10000000, n_samples)
    })
    
    df['high'] = df[['open', 'high', 'close', 'low']].max(axis=1)
    df['low'] = df[['open', 'high', 'close', 'low']].min(axis=1)
    
    # 使用 TA-Lib 测试
    talib_manager = get_indicators_manager(prefer_talib=True)
    talib_results = {}
    
    # 使用 pandas-ta 测试
    pandas_ta_manager = get_indicators_manager(prefer_talib=False)
    pandas_ta_results = {}
    
    # 测试各指标
    indicators = ['ma', 'macd', 'rsi', 'boll', 'atr']
    
    for indicator in indicators:
        func_name = f'calculate_{indicator}'
        
        if hasattr(talib_manager, func_name):
            func = getattr(talib_manager, func_name)
            talib_results[indicator] = benchmark_single_indicator(func, df)
        
        if hasattr(pandas_ta_manager, func_name):
            func = getattr(pandas_ta_manager, func_name)
            pandas_ta_results[indicator] = benchmark_single_indicator(func, df)
    
    # 计算性能提升
    comparison = {}
    for indicator in talib_results:
        if indicator in pandas_ta_results:
            talib_time = talib_results[indicator]['avg_time_ms']
            pandas_ta_time = pandas_ta_results[indicator]['avg_time_ms']
            
            if talib_time > 0 and pandas_ta_time > 0:
                speedup = pandas_ta_time / talib_time
                comparison[indicator] = {
                    "talib_avg_ms": talib_time,
                    "pandas_ta_avg_ms": pandas_ta_time,
                    "speedup_factor": round(speedup, 2),
                    "faster": "TA-Lib" if speedup > 1 else "pandas-ta"
                }
    
    return {
        "status": "success",
        "data_samples": n_samples,
        "talib_results": talib_results,
        "pandas_ta_results": pandas_ta_results,
        "comparison": comparison,
        "summary": {
            "talib_installed": TALIB_AVAILABLE,
            "pandas_ta_installed": PANDAS_TA_AVAILABLE,
            "recommended_library": "TA-Lib" if TALIB_AVAILABLE else "pandas-ta"
        }
    }
