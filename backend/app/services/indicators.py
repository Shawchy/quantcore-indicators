import pandas as pd
import numpy as np
from typing import Optional, Dict, Any, List
from loguru import logger


class TechnicalIndicators:
    @staticmethod
    def calculate_ma(
        df: pd.DataFrame,
        periods: List[int] = [5, 10, 20, 60],
        column: str = "close"
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        for period in periods:
            df[f"ma{period}"] = df[column].rolling(window=period).mean()
        
        return df
    
    @staticmethod
    def calculate_ema(
        df: pd.DataFrame,
        periods: List[int] = [12, 26],
        column: str = "close"
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        for period in periods:
            df[f"ema{period}"] = df[column].ewm(span=period, adjust=False).mean()
        
        return df
    
    @staticmethod
    def calculate_rsi(
        df: pd.DataFrame,
        periods: List[int] = [6, 12, 24],
        column: str = "close"
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        delta = df[column].diff()
        
        for period in periods:
            gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
            
            rs = gain / loss
            df[f"rsi{period}"] = 100 - (100 / (1 + rs))
        
        return df
    
    @staticmethod
    def calculate_macd(
        df: pd.DataFrame,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9,
        column: str = "close"
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        
        ema_fast = df[column].ewm(span=fast_period, adjust=False).mean()
        ema_slow = df[column].ewm(span=slow_period, adjust=False).mean()
        
        df["macd"] = ema_fast - ema_slow
        df["macd_signal"] = df["macd"].ewm(span=signal_period, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]
        
        return df
    
    @staticmethod
    def calculate_bollinger_bands(
        df: pd.DataFrame,
        period: int = 20,
        std_dev: float = 2.0,
        column: str = "close"
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        
        df["boll_mid"] = df[column].rolling(window=period).mean()
        std = df[column].rolling(window=period).std()
        
        df["boll_upper"] = df["boll_mid"] + std_dev * std
        df["boll_lower"] = df["boll_mid"] - std_dev * std
        df["boll_width"] = (df["boll_upper"] - df["boll_lower"]) / df["boll_mid"]
        
        return df
    
    @staticmethod
    def calculate_kdj(
        df: pd.DataFrame,
        n: int = 9,
        m1: int = 3,
        m2: int = 3
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        
        low_n = df["low"].rolling(window=n).min()
        high_n = df["high"].rolling(window=n).max()
        
        rsv = (df["close"] - low_n) / (high_n - low_n) * 100
        
        df["k"] = rsv.ewm(alpha=1/m1, adjust=False).mean()
        df["d"] = df["k"].ewm(alpha=1/m2, adjust=False).mean()
        df["j"] = 3 * df["k"] - 2 * df["d"]
        
        return df
    
    @staticmethod
    def calculate_atr(
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        
        high = df["high"]
        low = df["low"]
        close = df["close"].shift(1)
        
        tr1 = high - low
        tr2 = abs(high - close)
        tr3 = abs(low - close)
        
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        df["atr"] = tr.rolling(window=period).mean()
        
        return df
    
    @staticmethod
    def calculate_obv(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        
        direction = np.where(df["close"] > df["close"].shift(1), 1,
                            np.where(df["close"] < df["close"].shift(1), -1, 0))
        df["obv"] = (df["volume"] * direction).cumsum()
        
        return df
    
    @staticmethod
    def calculate_vwap(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        
        typical_price = (df["high"] + df["low"] + df["close"]) / 3
        df["vwap"] = (typical_price * df["volume"]).cumsum() / df["volume"].cumsum()
        
        return df
    
    @staticmethod
    def calculate_williams_r(
        df: pd.DataFrame,
        period: int = 14
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        
        high_n = df["high"].rolling(window=period).max()
        low_n = df["low"].rolling(window=period).min()
        
        df["williams_r"] = (high_n - df["close"]) / (high_n - low_n) * -100
        
        return df
    
    @staticmethod
    def calculate_cci(
        df: pd.DataFrame,
        period: int = 20
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        
        tp = (df["high"] + df["low"] + df["close"]) / 3
        sma = tp.rolling(window=period).mean()
        mad = tp.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean())
        
        df["cci"] = (tp - sma) / (0.015 * mad)
        
        return df


class IndicatorCalculator:
    def __init__(self):
        self.tech = TechnicalIndicators()
    
    def calculate_all(
        self,
        df: pd.DataFrame,
        include: Optional[List[str]] = None
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        
        all_indicators = {
            "ma": lambda: self.tech.calculate_ma(df),
            "ema": lambda: self.tech.calculate_ema(df),
            "rsi": lambda: self.tech.calculate_rsi(df),
            "macd": lambda: self.tech.calculate_macd(df),
            "boll": lambda: self.tech.calculate_bollinger_bands(df),
            "kdj": lambda: self.tech.calculate_kdj(df),
            "atr": lambda: self.tech.calculate_atr(df),
            "obv": lambda: self.tech.calculate_obv(df),
            "vwap": lambda: self.tech.calculate_vwap(df),
            "wr": lambda: self.tech.calculate_williams_r(df),
            "cci": lambda: self.tech.calculate_cci(df)
        }
        
        if include:
            for indicator in include:
                if indicator in all_indicators:
                    result = all_indicators[indicator]()
                    if result is not None:
                        df = result
        else:
            df = self.tech.calculate_ma(df)
            df = self.tech.calculate_rsi(df)
            df = self.tech.calculate_macd(df)
            df = self.tech.calculate_bollinger_bands(df)
            df = self.tech.calculate_kdj(df)
            df = self.tech.calculate_atr(df)
        
        return df
    
    def get_indicator_summary(self, df: pd.DataFrame) -> Dict[str, Any]:
        if df.empty:
            return {}
        
        summary = {}
        
        if "close" in df.columns:
            latest = df.iloc[-1]
            
            if "ma5" in df.columns:
                summary["ma_signal"] = "bullish" if latest["close"] > latest["ma5"] else "bearish"
            
            if "macd" in df.columns and "macd_signal" in df.columns:
                summary["macd_signal"] = "bullish" if latest["macd"] > latest["macd_signal"] else "bearish"
            
            if "rsi6" in df.columns:
                rsi = latest["rsi6"]
                if rsi > 70:
                    summary["rsi_signal"] = "overbought"
                elif rsi < 30:
                    summary["rsi_signal"] = "oversold"
                else:
                    summary["rsi_signal"] = "neutral"
            
            if "k" in df.columns and "d" in df.columns:
                k, d = latest["k"], latest["d"]
                if k > d and k < 20:
                    summary["kdj_signal"] = "buy"
                elif k < d and k > 80:
                    summary["kdj_signal"] = "sell"
                else:
                    summary["kdj_signal"] = "hold"
        
        return summary
