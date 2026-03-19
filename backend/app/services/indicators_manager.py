"""
技术指标管理器

集成 pandas-ta 和 TA-Lib，提供统一的技术指标计算接口
"""
from typing import Optional, Dict, Any, List
import pandas as pd
from loguru import logger

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


class IndicatorsManager:
    """技术指标管理器"""
    
    def __init__(self, prefer_talib: bool = True):
        """
        Args:
            prefer_talib: 是否优先使用 TA-Lib（如果可用）
        """
        self.prefer_talib = prefer_talib and TALIB_AVAILABLE
        self.use_pandas_ta = PANDAS_TA_AVAILABLE
        
        if not self.use_pandas_ta and not self.prefer_talib:
            logger.error("pandas-ta 和 TA-Lib 都不可用，指标计算功能将受限")
    
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
        df = df.copy()
        
        if self.prefer_talib:
            # 使用 TA-Lib
            for period in periods:
                df[f'ma{period}'] = talib.SMA(df[price_column].values, timeperiod=period)
        else:
            # 使用 pandas-ta
            for period in periods:
                df[f'ma{period}'] = ta.sma(df[price_column], length=period)
        
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
        
        if self.prefer_talib:
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
        
        if self.prefer_talib:
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
        """计算 KDJ 指标（只有 pandas-ta 支持）"""
        df = df.copy()
        
        if self.use_pandas_ta:
            kdj_df = ta.kdj(df['high'], df['low'], df['close'], length=n, signal=m1)
            if kdj_df is not None:
                df['kdj_k'] = kdj_df[f'K_{n}_{m1}']
                df['kdj_d'] = kdj_df[f'D_{n}_{m1}']
                df['kdj_j'] = kdj_df[f'J_{n}_{m1}']
            else:
                logger.warning("KDJ 计算失败")
        else:
            logger.warning("KDJ 指标需要 pandas-ta 支持")
        
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
        
        if self.prefer_talib:
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
        
        if self.prefer_talib:
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
        
        # KDJ (只有 pandas-ta 支持)
        if self.use_pandas_ta:
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

def get_indicators_manager(prefer_talib: bool = True) -> IndicatorsManager:
    """获取全局指标管理器实例"""
    global _indicators_manager
    if _indicators_manager is None:
        _indicators_manager = IndicatorsManager(prefer_talib=prefer_talib)
    return _indicators_manager
