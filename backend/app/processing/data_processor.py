import pandas as pd
import numpy as np
from typing import Optional, List, Dict, Any
from loguru import logger

_CN_PRICE_LIMIT = {
    'default': 0.10,
    'st': 0.05,
    'kc': 0.20,
    'cy': 0.20,
    'bj': 0.30,
}


def _get_trading_days(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    try:
        from chinese_calendar import is_workday
        all_days = pd.date_range(start=start, end=end, freq="B")
        trading_days = all_days[[is_workday(d) for d in all_days]]
        return trading_days
    except ImportError:
        pass

    try:
        import exchange_calendars as xcals
        xshg = xcals.get_calendar("XSHG")
        sessions = xshg.sessions_in_range(start, end)
        return sessions
    except ImportError:
        pass

    return pd.bdate_range(start=start, end=end)


class DataCleaner:
    @staticmethod
    def clean_kline_data(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        
        df = df.dropna(subset=["open", "high", "low", "close", "volume"])
        
        df = df[df["volume"] > 0]
        
        df = df[(df["high"] >= df["low"]) & 
                (df["high"] >= df["open"]) & 
                (df["high"] >= df["close"]) &
                (df["low"] <= df["open"]) & 
                (df["low"] <= df["close"])]
        
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        
        if "date" in df.columns:
            try:
                df["date"] = df["date"].astype(str).str.strip()
                df["date"] = pd.to_datetime(df["date"], format='mixed', errors='coerce')
            except Exception as e:
                logger.warning(f"日期转换失败，使用备用方案：{e}")
                def convert_date(date_str):
                    try:
                        date_str = str(date_str).strip()
                        if len(date_str) == 8 and date_str.isdigit():
                            return pd.to_datetime(date_str, format="%Y%m%d")
                        elif len(date_str) == 10 and '-' in date_str:
                            return pd.to_datetime(date_str, format="%Y-%m-%d")
                        else:
                            return pd.to_datetime(date_str)
                    except (ValueError, TypeError) as e:
                        logger.debug(f"日期解析失败: {date_str}, 错误: {e}")
                        return pd.NaT
                df["date"] = df["date"].apply(convert_date)
            
            df = df.sort_values("date").reset_index(drop=True)
        
        return df
    
    @staticmethod
    def remove_outliers(
        df: pd.DataFrame,
        columns: List[str] = None,
        n_std: float = 3.0,
        use_price_limit: bool = True,
        price_limit: float = 0.10
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        if columns is None:
            columns = ["open", "high", "low", "close"]
        
        df = df.copy()
        
        if use_price_limit and "close" in df.columns and "open" in df.columns:
            prev_close = df["close"].shift(1)
            valid_mask = pd.Series(True, index=df.index)
            
            for idx in df.index:
                if pd.isna(prev_close.iloc[idx if isinstance(idx, int) else 0]):
                    continue
                pc = prev_close.loc[idx]
                if pc <= 0:
                    continue
                
                upper = pc * (1 + price_limit)
                lower = pc * (1 - price_limit)
                
                for col in ["open", "high", "low", "close"]:
                    if col in df.columns:
                        val = df.loc[idx, col]
                        if val > upper * 1.01 or val < lower * 0.99:
                            valid_mask.loc[idx] = False
                            break
            
            df = df[valid_mask].reset_index(drop=True)
        else:
            for col in columns:
                if col in df.columns:
                    median = df[col].median()
                    mad = (df[col] - median).abs().median() * 1.4826
                    if mad > 0:
                        df = df[((df[col] - median) / mad).abs() <= n_std * 1.5]
            
            df = df.reset_index(drop=True)
        
        return df
    
    @staticmethod
    def fill_missing_dates(df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "date" not in df.columns:
            return df
        
        df = df.copy()
        try:
            df["date"] = df["date"].astype(str).str.strip()
            df["date"] = pd.to_datetime(df["date"], format='mixed', errors='coerce')
        except Exception:
            df["date"] = pd.to_datetime(df["date"], errors='coerce')
        
        df = df.dropna(subset=["date"])
        df = df.set_index("date")
        
        trading_days = _get_trading_days(df.index.min(), df.index.max())
        
        existing_dates = set(df.index.normalize())
        missing_dates = [d for d in trading_days if d.normalize() not in existing_dates]
        
        if missing_dates:
            missing_df = pd.DataFrame(index=missing_dates)
            df = pd.concat([df, missing_df]).sort_index()
        
        df = df.ffill()
        df = df.reset_index().rename(columns={"index": "date"})
        
        return df
    
    @staticmethod
    def validate_data(df: pd.DataFrame) -> Dict[str, Any]:
        result = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        if df.empty:
            result["is_valid"] = False
            result["errors"].append("数据为空")
            return result
        
        required_cols = ["open", "high", "low", "close", "volume"]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            result["is_valid"] = False
            result["errors"].append(f"缺少必要列: {missing_cols}")
        
        null_counts = df[required_cols].isnull().sum().to_dict()
        if any(null_counts.values()):
            result["warnings"].append(f"存在空值: {null_counts}")
        
        invalid_prices = df[(df["high"] < df["low"]) | 
                           (df["high"] < df["open"]) | 
                           (df["high"] < df["close"]) |
                           (df["low"] > df["open"]) | 
                           (df["low"] > df["close"])]
        if not invalid_prices.empty:
            result["warnings"].append(f"存在价格异常数据: {len(invalid_prices)}条")
        
        result["stats"] = {
            "total_rows": len(df),
            "date_range": f"{df['date'].min()} ~ {df['date'].max()}" if "date" in df.columns else "N/A",
            "null_counts": null_counts
        }
        
        return result


class PriceAdjuster:
    @staticmethod
    def adjust_price(
        df: pd.DataFrame,
        adj_factor: pd.Series,
        method: str = "qfq"
    ) -> pd.DataFrame:
        if df.empty or adj_factor.empty:
            return df
        
        df = df.copy()
        
        if method == "qfq":
            last_factor = adj_factor.iloc[-1]
            factor = adj_factor / last_factor
        elif method == "hfq":
            first_factor = adj_factor.iloc[0]
            factor = adj_factor / first_factor
        else:
            return df
        
        for col in ["open", "high", "low", "close"]:
            df[col] = df[col] * factor
        
        return df
    
    @staticmethod
    def calculate_adj_factor(
        df: pd.DataFrame,
        dividend_df: Optional[pd.DataFrame] = None,
        split_df: Optional[pd.DataFrame] = None
    ) -> pd.Series:
        if df.empty:
            return pd.Series()
        
        adj_factor = pd.Series(1.0, index=df.index)
        
        if dividend_df is not None and not dividend_df.empty:
            for _, row in dividend_df.iterrows():
                date = row["date"]
                dividend = row["dividend"]
                close = df.loc[df["date"] == date, "close"].values
                if len(close) > 0:
                    factor = 1 - dividend / close[0]
                    adj_factor.loc[df["date"] >= date] *= factor
        
        if split_df is not None and not split_df.empty:
            for _, row in split_df.iterrows():
                date = row["date"]
                split_ratio = row["split_ratio"]
                adj_factor.loc[df["date"] >= date] *= split_ratio
        
        return adj_factor


class DataProcessor:
    def __init__(self):
        self.cleaner = DataCleaner()
        self.adjuster = PriceAdjuster()
    
    def process_kline(
        self,
        df: pd.DataFrame,
        clean: bool = True,
        validate: bool = True,
        fill_missing: bool = False
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        if clean:
            df = self.cleaner.clean_kline_data(df)
        
        if fill_missing:
            df = self.cleaner.fill_missing_dates(df)
        
        if validate:
            validation = self.cleaner.validate_data(df)
            if not validation["is_valid"]:
                logger.warning(f"数据验证失败: {validation['errors']}")
            if validation["warnings"]:
                logger.warning(f"数据警告: {validation['warnings']}")
        
        return df
    
    def calculate_returns(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        df["return"] = df["close"].pct_change()
        df["log_return"] = np.log(df["close"] / df["close"].shift(1))
        
        return df
    
    def calculate_volatility(
        self,
        df: pd.DataFrame,
        window: int = 20
    ) -> pd.DataFrame:
        if df.empty:
            return df
        
        df = df.copy()
        df["volatility"] = df["return"].rolling(window=window).std() * np.sqrt(252)
        
        return df
