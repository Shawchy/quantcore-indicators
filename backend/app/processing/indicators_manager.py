"""
技术指标管理器

集成 quantcore-indicators (Rust)、pandas-ta 和 TA-Lib
提供统一的技术指标计算接口，优先使用 Rust 高性能版本
添加性能监控功能
"""
from typing import Optional, Dict, Any, List
import pandas as pd
import time
import warnings
from loguru import logger
from functools import wraps

# 过滤 pandas_ta 的弃用警告
import warnings
warnings.filterwarnings('ignore', category=FutureWarning, module='pandas_ta')
warnings.filterwarnings('ignore', category=UserWarning, message='.*copy_on_write.*')
warnings.filterwarnings('ignore', category=Warning, message='.*Pandas4Warning.*')

# 尝试导入 QuantCore Rust 指标库
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
    RUST_INDICATORS_AVAILABLE = True
    logger.info("✅ QuantCore Indicators (Rust) 已加载，将用于高性能指标计算")
except ImportError as e:
    RUST_INDICATORS_AVAILABLE = False
    logger.warning(f"⚠️ QuantCore Indicators (Rust) 未加载: {e}")

# 尝试导入 TA-Lib
try:
    import talib
    TALIB_AVAILABLE = True
    logger.info("TA-Lib 已安装，将用于高性能指标计算")
except ImportError:
    TALIB_AVAILABLE = False
    logger.info("TA-Lib 未安装，使用 pandas-ta 计算指标")

# 导入 pandas-ta
try:
    import pandas_ta as ta
    PANDAS_TA_AVAILABLE = True
    logger.info("pandas-ta 已安装")
except ImportError:
    PANDAS_TA_AVAILABLE = False
    logger.warning("pandas-ta 未安装，请运行：pip install pandas-ta")


def performance_monitor(func):
    """性能监控装饰器"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_ms = (time.time() - start_time) * 1000
        
        # 记录性能日志（仅当超过阈值时）
        if elapsed_ms > 100:  # 超过 100ms 才记录
            logger.warning(
                f"指标计算耗时较长：{func.__name__} - {elapsed_ms:.2f}ms"
            )
        else:
            logger.debug(
                f"指标计算完成：{func.__name__} - {elapsed_ms:.2f}ms"
            )
        
        return result
    return wrapper


class IndicatorsManager:
    """技术指标管理器（优先使用 Rust 版本）"""
    
    def __init__(
        self, 
        prefer_rust: bool = True,
        prefer_talib: bool = True, 
        enable_performance_monitoring: bool = True
    ):
        """
        Args:
            prefer_rust: 是否优先使用 Rust 指标库（如果可用）
            prefer_talib: 是否优先使用 TA-Lib（如果可用）
            enable_performance_monitoring: 是否启用性能监控
        """
        self.prefer_rust = prefer_rust and RUST_INDICATORS_AVAILABLE
        self.prefer_talib = prefer_talib and TALIB_AVAILABLE and not self.prefer_rust
        self.use_pandas_ta = PANDAS_TA_AVAILABLE
        self.enable_performance_monitoring = enable_performance_monitoring
        
        # 性能统计
        self.performance_stats = {}
        
        if self.prefer_rust:
            logger.info("🚀 指标计算优先级: Rust (QuantCore) > TA-Lib > pandas-ta")
        elif self.prefer_talib:
            logger.info("📊 指标计算优先级: TA-Lib > pandas-ta")
        else:
            logger.info("🐍 使用 pandas-ta 计算指标")
        
        if not self.use_pandas_ta and not self.prefer_talib and not self.prefer_rust:
            logger.error("pandas-ta、TA-Lib 和 Rust 指标库都不可用，指标计算功能将受限")
    
    def _update_stats(self, indicator_name: str, elapsed_ms: float):
        """更新性能统计"""
        if indicator_name not in self.performance_stats:
            self.performance_stats[indicator_name] = {
                'count': 0,
                'total_ms': 0,
                'min_ms': float('inf'),
                'max_ms': 0,
                'avg_ms': 0
            }
        
        stats = self.performance_stats[indicator_name]
        stats['count'] += 1
        stats['total_ms'] += elapsed_ms
        stats['min_ms'] = min(stats['min_ms'], elapsed_ms)
        stats['max_ms'] = max(stats['max_ms'], elapsed_ms)
        stats['avg_ms'] = stats['total_ms'] / stats['count']
    
    def get_performance_stats(self) -> Dict[str, Dict[str, Any]]:
        """获取性能统计信息"""
        return self.performance_stats.copy()
    
    def reset_performance_stats(self):
        """重置性能统计"""
        self.performance_stats = {}
    
    @performance_monitor
    def calculate_ma(
        self,
        df: pd.DataFrame,
        periods: List[int] = [5, 10, 20, 60],
        price_column: str = "close"
    ) -> pd.DataFrame:
        """
        计算移动平均线 (MA)
        
        Args:
            df: 包含价格数据的 DataFrame
            periods: 周期列表
            price_column: 价格列名
        
        Returns:
            添加了 MA 列的 DataFrame
        """
        start_time = time.time()
        df = df.copy()
        
        if self.prefer_rust:
            # 使用 Rust 高性能版本
            prices = df[price_column].values
            for period in periods:
                result = rust_ma(prices, period)
                df[f'ma{period}'] = pd.Series(result, index=df.index[-len(result):])
        elif self.prefer_talib:
            # 使用 TA-Lib
            for period in periods:
                df[f'ma{period}'] = talib.SMA(df[price_column].values, timeperiod=period)
        else:
            # 使用 pandas-ta
            for period in periods:
                df[f'ma{period}'] = ta.sma(df[price_column], length=period)
        
        # 记录性能统计
        if self.enable_performance_monitoring:
            elapsed_ms = (time.time() - start_time) * 1000
            self._update_stats('ma', elapsed_ms)
        
        return df
    
    def calculate_macd(
        self,
        df: pd.DataFrame,
        fast: int = 12,
        slow: int = 26,
        signal: int = 9,
        price_column: str = "close"
    ) -> pd.DataFrame:
        """计算 MACD 指标"""
        df = df.copy()
        
        if self.prefer_rust:
            # 使用 Rust 高性能版本
            prices = df[price_column].values
            result = rust_macd(prices, fast=fast, slow=slow, signal=signal)
            idx = df.index[-len(result['macd']):]
            df['macd'] = pd.Series(result['macd'], index=idx)
            df['macd_signal'] = pd.Series(result['signal'], index=idx)
            df['macd_hist'] = pd.Series(result['histogram'], index=idx)
        elif self.prefer_talib:
            df['macd'], df['macd_signal'], df['macd_hist'] = talib.MACD(
                df[price_column].values,
                fastperiod=fast,
                slowperiod=slow,
                signalperiod=signal
            )
        else:
            macd_df = ta.macd(
                df[price_column],
                fast=fast,
                slow=slow,
                signal=signal
            )
            if macd_df is not None:
                df['macd'] = macd_df[f'MACD_{fast}_{slow}_{signal}']
                df['macd_signal'] = macd_df[f'MACDs_{fast}_{slow}_{signal}']
                df['macd_hist'] = macd_df[f'MACDh_{fast}_{slow}_{signal}']
            else:
                logger.warning("MACD 计算失败")
        
        return df
    
    def calculate_rsi(
        self,
        df: pd.DataFrame,
        periods: List[int] = [6, 12, 24],
        price_column: str = "close"
    ) -> pd.DataFrame:
        """计算 RSI 指标"""
        df = df.copy()
        
        if self.prefer_rust:
            # 使用 Rust 高性能版本
            prices = df[price_column].values
            for period in periods:
                result = rust_rsi(prices, period)
                df[f'rsi{period}'] = pd.Series(result, index=df.index[-len(result):])
        elif self.prefer_talib:
            for period in periods:
                df[f'rsi{period}'] = talib.RSI(df[price_column].values, timeperiod=period)
        else:
            for period in periods:
                df[f'rsi{period}'] = ta.rsi(df[price_column], length=period)
        
        return df
    
    def calculate_kdj(
        self,
        df: pd.DataFrame,
        n: int = 9,
        m1: int = 3,
        m2: int = 3
    ) -> pd.DataFrame:
        """计算 KDJ 指标"""
        df = df.copy()
        
        if self.prefer_rust:
            # 使用 Rust 高性能版本
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            result = rust_kdj(high, low, close, n=n, m1=m1, m2=m2)
            idx = df.index[-len(result['k']):]
            df['kdj_k'] = pd.Series(result['k'], index=idx)
            df['kdj_d'] = pd.Series(result['d'], index=idx)
            df['kdj_j'] = pd.Series(result['j'], index=idx)
        elif self.use_pandas_ta:
            kdj_df = ta.kdj(df['high'], df['low'], df['close'], length=n, signal=m1)
            if kdj_df is not None:
                df['kdj_k'] = kdj_df[f'K_{n}_{m1}']
                df['kdj_d'] = kdj_df[f'D_{n}_{m1}']
                df['kdj_j'] = kdj_df[f'J_{n}_{m1}']
            else:
                logger.warning("KDJ 计算失败")
        else:
            logger.warning("KDJ 指标需要 Rust 或 pandas-ta 支持")
        
        return df
    
    def calculate_bollinger_bands(
        self,
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        price_column: str = "close"
    ) -> pd.DataFrame:
        """计算布林带"""
        df = df.copy()
        
        if self.prefer_rust:
            # 使用 Rust 高性能版本
            prices = df[price_column].values
            result = rust_bollinger_bands(prices, period=period, std_dev=std_dev)
            idx = df.index[-len(result['middle']):]
            df['bb_upper'] = pd.Series(result['upper'], index=idx)
            df['bb_middle'] = pd.Series(result['middle'], index=idx)
            df['bb_lower'] = pd.Series(result['lower'], index=idx)
        elif self.prefer_talib:
            df['bb_upper'], df['bb_middle'], df['bb_lower'] = talib.BBANDS(
                df[price_column].values,
                timeperiod=period,
                nbdevup=std_dev,
                nbdevdn=std_dev
            )
        else:
            bb_df = ta.bbands(df[price_column], length=period, std=std_dev)
            if bb_df is not None:
                df['bb_upper'] = bb_df[f'BBU_{period}_{std_dev}_{std_dev}']
                df['bb_middle'] = bb_df[f'BBM_{period}_{std_dev}_{std_dev}']
                df['bb_lower'] = bb_df[f'BBL_{period}_{std_dev}_{std_dev}']
            else:
                logger.warning("布林带计算失败")
        
        return df
    
    def calculate_atr(
        self,
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.DataFrame:
        """计算 ATR 指标"""
        df = df.copy()
        
        if self.prefer_rust:
            # 使用 Rust 高性能版本
            high = df['high'].values
            low = df['low'].values
            close = df['close'].values
            result = rust_atr(high, low, close, period)
            df['atr'] = pd.Series(result, index=df.index[-len(result):])
        elif self.prefer_talib:
            df['atr'] = talib.ATR(
                df['high'].values,
                df['low'].values,
                df['close'].values,
                timeperiod=period
            )
        else:
            df['atr'] = ta.atr(df['high'], df['low'], df['close'], length=period)
        
        return df
    
    def calculate_all_indicators(
        self,
        df: pd.DataFrame,
        price_column: str = "close"
    ) -> pd.DataFrame:
        """
        一次性计算所有常用指标
        
        Args:
            df: 包含 OHLC 数据的 DataFrame
            price_column: 价格列名
        
        Returns:
            包含所有指标的 DataFrame
        """
        # 移动平均线
        df = self.calculate_ma(df, periods=[5, 10, 20, 60], price_column=price_column)
        
        # MACD
        df = self.calculate_macd(df, price_column=price_column)
        
        # RSI
        df = self.calculate_rsi(df, periods=[6, 12, 24], price_column=price_column)
        
        # 布林带
        df = self.calculate_bollinger_bands(df, price_column=price_column)
        
        # KDJ (Rust 或 pandas-ta 支持)
        df = self.calculate_kdj(df)
        
        # ATR
        df = self.calculate_atr(df)
        
        return df
    
    def calculate_custom_indicators(
        self,
        df: pd.DataFrame,
        indicators: List[str]
    ) -> pd.DataFrame:
        """
        计算自定义指标列表
        
        Args:
            df: 包含 OHLC 数据的 DataFrame
            indicators: 指标名称列表（pandas-ta 格式）
        
        Returns:
            包含自定义指标的 DataFrame
        """
        if not self.use_pandas_ta:
            logger.error("自定义指标需要 pandas-ta 支持")
            return df
        
        df = df.copy()
        
        # 使用 pandas-ta 的 strategy 功能
        strategy = ta.Strategy(name="custom", ta=indicators)
        df.ta(strategy=strategy, append=True)
        
        return df


# 全局指标管理器实例
_indicators_manager: Optional[IndicatorsManager] = None

def get_indicators_manager(prefer_rust: bool = True, prefer_talib: bool = True) -> IndicatorsManager:
    """获取全局指标管理器实例"""
    global _indicators_manager
    if _indicators_manager is None:
        _indicators_manager = IndicatorsManager(
            prefer_rust=prefer_rust, 
            prefer_talib=prefer_talib
        )
    return _indicators_manager
