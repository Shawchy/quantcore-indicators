"""
QuantCore Indicators Bridge - Rust 指标库桥接模块

优先使用 Rust 高性能版本，回退到 Python 实现
"""
from typing import Dict, Optional
import pandas as pd
import numpy as np
from loguru import logger

# 尝试导入 Rust 版本
try:
    import sys
    from app.config import get_quantcore_indicators_path
    
    indicators_path = get_quantcore_indicators_path()
    if indicators_path not in sys.path:
        sys.path.insert(0, indicators_path)
    
    from quantcore_indicators import (
        ma as rust_ma,
        ema as rust_ema,
        macd as rust_macd,
        rsi as rust_rsi,
        bollinger_bands as rust_bollinger_bands,
        atr as rust_atr,
        cci as rust_cci,
        kdj as rust_kdj,
        obv as rust_obv,
        williams_r as rust_williams_r,
        adx as rust_adx,
    )
    RUST_AVAILABLE = True
    logger.info("✅ QuantCore Indicators (Rust) 已加载")
except ImportError as e:
    RUST_AVAILABLE = False
    logger.warning(f"⚠️ QuantCore Indicators (Rust) 未加载: {e}")


class QuantCoreIndicatorsBridge:
    """
    QuantCore Rust 指标库桥接
    
    优先使用 Rust 高性能版本，如果不可用则回退到 Python 实现
    """
    
    def __init__(self):
        self.rust_available = RUST_AVAILABLE
    
    def calculate_ma(self, df: pd.DataFrame, period: int = 20, price_column: str = "close") -> pd.Series:
        """计算移动平均线"""
        prices = df[price_column].values
        
        if self.rust_available:
            result = rust_ma(prices, period)
        else:
            result = df[price_column].rolling(window=period).mean()
            if hasattr(result, 'values'):
                result = result.values
        
        return pd.Series(result, index=df.index[-len(result):])
    
    def calculate_macd(self, df: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9, 
                      price_column: str = "close") -> Dict[str, pd.Series]:
        """计算 MACD 指标"""
        prices = df[price_column].values
        
        if self.rust_available:
            result = rust_macd(prices, fast=fast, slow=slow, signal=signal)
        else:
            # 回退到 pandas-ta 或纯 Python
            ema_fast = df[price_column].ewm(span=fast, adjust=False).mean()
            ema_slow = df[price_column].ewm(span=slow, adjust=False).mean()
            macd_line = ema_fast - ema_slow
            signal_line = macd_line.ewm(span=signal, adjust=False).mean()
            histogram = macd_line - signal_line
            return {
                'macd': macd_line,
                'signal': signal_line,
                'histogram': histogram
            }
        
        idx = df.index[-len(result['macd']):]
        return {
            'macd': pd.Series(result['macd'], index=idx),
            'signal': pd.Series(result['signal'], index=idx),
            'histogram': pd.Series(result['histogram'], index=idx)
        }
    
    def calculate_rsi(self, df: pd.DataFrame, period: int = 14, price_column: str = "close") -> pd.Series:
        """计算 RSI 指标"""
        prices = df[price_column].values
        
        if self.rust_available:
            result = rust_rsi(prices, period)
        else:
            delta = df[price_column].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            rs = gain / loss
            result = 100 - (100 / (1 + rs))
            if hasattr(result, 'values'):
                result = result.values
        
        return pd.Series(result, index=df.index[-len(result):])
    
    def calculate_bollinger_bands(self, df: pd.DataFrame, period: int = 20, std_dev: float = 2.0,
                                  price_column: str = "close") -> Dict[str, pd.Series]:
        """计算布林带"""
        prices = df[price_column].values
        
        if self.rust_available:
            result = rust_bollinger_bands(prices, period=period, std_dev=std_dev)
        else:
            sma = df[price_column].rolling(window=period).mean()
            std = df[price_column].rolling(window=period).std()
            return {
                'upper': sma + std_dev * std,
                'middle': sma,
                'lower': sma - std_dev * std
            }
        
        idx = df.index[-len(result['middle']):]
        return {
            'upper': pd.Series(result['upper'], index=idx),
            'middle': pd.Series(result['middle'], index=idx),
            'lower': pd.Series(result['lower'], index=idx)
        }
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算 ATR 指标"""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        if self.rust_available:
            result = rust_atr(high, low, close, period)
        else:
            high_low = df['high'] - df['low']
            high_close = np.abs(df['high'] - df['close'].shift())
            low_close = np.abs(df['low'] - df['close'].shift())
            tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
            result = tr.rolling(window=period).mean()
            if hasattr(result, 'values'):
                result = result.values
        
        return pd.Series(result, index=df.index[-len(result):])
    
    def calculate_kdj(self, df: pd.DataFrame, n: int = 9, m1: int = 3, m2: int = 3) -> Dict[str, pd.Series]:
        """计算 KDJ 指标"""
        high = df['high'].values
        low = df['low'].values
        close = df['close'].values
        
        if self.rust_available:
            result = rust_kdj(high, low, close, n=n, m1=m1, m2=m2)
        else:
            # 回退实现
            lowest_low = df['low'].rolling(window=n).min()
            highest_high = df['high'].rolling(window=n).max()
            rsv = (df['close'] - lowest_low) / (highest_high - lowest_low) * 100
            k = rsv.ewm(com=m2-1, adjust=False).mean()
            d = k.ewm(com=m1-1, adjust=False).mean()
            j = 3 * k - 2 * d
            return {
                'k': k,
                'd': d,
                'j': j
            }
        
        idx = df.index[-len(result['k']):]
        return {
            'k': pd.Series(result['k'], index=idx),
            'd': pd.Series(result['d'], index=idx),
            'j': pd.Series(result['j'], index=idx)
        }


# 全局单例
_indicators_bridge: Optional[QuantCoreIndicatorsBridge] = None

def get_indicators_bridge() -> QuantCoreIndicatorsBridge:
    """获取全局指标桥接实例"""
    global _indicators_bridge
    if _indicators_bridge is None:
        _indicators_bridge = QuantCoreIndicatorsBridge()
    return _indicators_bridge
