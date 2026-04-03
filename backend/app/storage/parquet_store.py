from pathlib import Path
from typing import Optional
import pandas as pd
import pyarrow.parquet as pq
import pyarrow as pa
from datetime import datetime
from loguru import logger

from app.config import settings


class ParquetStore:
    def __init__(self, base_dir: Optional[str] = None):
        self.base_dir = Path(base_dir or settings.PARQUET_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        self.kline_dir = self.base_dir / "kline"
        self.indicators_dir = self.base_dir / "indicators"
        self.chip_dir = self.base_dir / "chip"
        self.backtest_dir = self.base_dir / "backtest"
        
        for dir_path in [self.kline_dir, self.indicators_dir, self.chip_dir, self.backtest_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def save_kline(
        self,
        df: pd.DataFrame,
        code: str,
        partition_by_year: bool = True
    ) -> str:
        if partition_by_year and "date" in df.columns:
            # 统一日期格式处理，支持多种格式
            try:
                df["date"] = df["date"].astype(str).str.strip()
                df["date"] = pd.to_datetime(df["date"], format='mixed', errors='coerce')
            except Exception:
                df["date"] = pd.to_datetime(df["date"], errors='coerce')
            
            df["year"] = df["date"].dt.year
            for year, group in df.groupby("year"):
                file_path = self.kline_dir / code / f"{year}.parquet"
                file_path.parent.mkdir(parents=True, exist_ok=True)
                group.drop(columns=["year"]).to_parquet(file_path, index=False)
            return str(self.kline_dir / code)
        else:
            file_path = self.kline_dir / f"{code}.parquet"
            df.to_parquet(file_path, index=False)
            return str(file_path)
    
    def load_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        code_dir = self.kline_dir / code
        if code_dir.exists():
            dfs = []
            for file_path in sorted(code_dir.glob("*.parquet")):
                df = pd.read_parquet(file_path)
                dfs.append(df)
            if dfs:
                result = pd.concat(dfs, ignore_index=True)
                if start_date:
                    result = result[result["date"] >= start_date]
                if end_date:
                    result = result[result["date"] <= end_date]
                return result
        else:
            file_path = self.kline_dir / f"{code}.parquet"
            if file_path.exists():
                df = pd.read_parquet(file_path)
                if start_date:
                    df = df[df["date"] >= start_date]
                if end_date:
                    df = df[df["date"] <= end_date]
                return df
        return None
    
    def save_indicators(self, df: pd.DataFrame, code: str) -> str:
        file_path = self.indicators_dir / f"{code}.parquet"
        df.to_parquet(file_path, index=False)
        return str(file_path)
    
    def load_indicators(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        file_path = self.indicators_dir / f"{code}.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            if start_date:
                df = df[df["date"] >= start_date]
            if end_date:
                df = df[df["date"] <= end_date]
            return df
        return None
    
    def save_chip_data(self, df: pd.DataFrame, code: str) -> str:
        file_path = self.chip_dir / f"{code}.parquet"
        df.to_parquet(file_path, index=False)
        return str(file_path)
    
    def load_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Optional[pd.DataFrame]:
        file_path = self.chip_dir / f"{code}.parquet"
        if file_path.exists():
            df = pd.read_parquet(file_path)
            if start_date:
                df = df[df["date"] >= start_date]
            if end_date:
                df = df[df["date"] <= end_date]
            return df
        return None
    
    def save_backtest_result(
        self,
        result: dict,
        backtest_id: str
    ) -> str:
        file_path = self.backtest_dir / f"{backtest_id}.parquet"
        
        if "trades" in result:
            trades_df = pd.DataFrame(result["trades"])
            trades_df.to_parquet(file_path.with_suffix(".trades.parquet"), index=False)
        
        if "equity_curve" in result:
            equity_df = pd.DataFrame(result["equity_curve"])
            equity_df.to_parquet(file_path.with_suffix(".equity.parquet"), index=False)
        
        return str(file_path)
    
    def load_backtest_result(self, backtest_id: str) -> Optional[dict]:
        result = {}
        
        trades_path = self.backtest_dir / f"{backtest_id}.trades.parquet"
        if trades_path.exists():
            result["trades"] = pd.read_parquet(trades_path).to_dict("records")
        
        equity_path = self.backtest_dir / f"{backtest_id}.equity.parquet"
        if equity_path.exists():
            result["equity_curve"] = pd.read_parquet(equity_path).to_dict("records")
        
        return result if result else None
    
    def get_storage_stats(self) -> dict:
        stats = {}
        for name, dir_path in [
            ("kline", self.kline_dir),
            ("indicators", self.indicators_dir),
            ("chip", self.chip_dir),
            ("backtest", self.backtest_dir)
        ]:
            if dir_path.exists():
                files = list(dir_path.glob("**/*.parquet"))
                total_size = sum(f.stat().st_size for f in files)
                stats[name] = {
                    "file_count": len(files),
                    "total_size_mb": round(total_size / (1024 * 1024), 2)
                }
        return stats
    
    def cleanup_old_data(self, years_to_keep: int = 3) -> dict:
        cutoff_year = datetime.now().year - years_to_keep
        cleaned = {}
        
        for name, dir_path in [
            ("kline", self.kline_dir),
            ("indicators", self.indicators_dir)
        ]:
            if dir_path.exists():
                count = 0
                for file_path in dir_path.glob("**/*.parquet"):
                    try:
                        year = int(file_path.stem)
                        if year < cutoff_year:
                            file_path.unlink()
                            count += 1
                    except ValueError:
                        continue
                cleaned[name] = count
        
        logger.info(f"清理完成: {cleaned}")
        return cleaned


parquet_store = ParquetStore()
