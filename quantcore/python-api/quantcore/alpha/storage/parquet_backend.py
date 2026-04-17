"""
Parquet 存储引擎

提供高效的列式存储支持。
"""

import os
from typing import Dict, List, Optional, Any
from datetime import date

import pandas as pd
import numpy as np
import pyarrow.parquet as pq
from loguru import logger


class ParquetBackend:
    """
    Parquet 存储引擎
    
    特点：
    - 列式压缩，节省空间 5-10x
    - 支持分区存储（按日期、行业等）
    - 快速查询特定列
    - 支持 Schema 演进
    
    使用示例：
        backend = ParquetBackend("./data/factors")
        
        # 写入数据
        backend.write("MOMENTUM_20", factor_df)
        
        # 读取数据
        data = backend.read("MOMENTUM_20", columns=["factor_value"])
    """
    
    def __init__(self, base_dir: str = "./data/factors"):
        self.base_dir = base_dir
        self.daily_dir = os.path.join(base_dir, "daily")
        self.snapshot_dir = os.path.join(base_dir, "snapshot")
        
        os.makedirs(self.daily_dir, exist_ok=True)
        os.makedirs(self.snapshot_dir, exist_ok=True)
    
    def write(
        self,
        factor_name: str,
        data: pd.DataFrame,
        partition_by: Optional[str] = None,
        compression: str = "snappy"
    ):
        """
        写入因子数据
        
        Args:
            factor_name: 因子名称
            data: 因子数据 DataFrame
            partition_by: 分区列名（如 trade_date）
            compression: 压缩算法 (snappy/gzip/brotli/lz4)
        """
        file_path = self._get_file_path(factor_name, is_snapshot=False)
        
        try:
            if partition_by and partition_by in data.columns:
                # 分区存储
                data.to_parquet(
                    file_path,
                    partition_cols=[partition_by],
                    compression=compression,
                    index=True
                )
            else:
                data.to_parquet(file_path, compression=compression, index=True)
            
            logger.debug(f"写入 {len(data)} 条记录到 {file_path}")
            
        except Exception as e:
            logger.error(f"Parquet 写入失败: {e}")
            raise
    
    def read(
        self,
        factor_name: str,
        columns: Optional[List[str]] = None,
        filters: Optional[List[tuple]] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        读取因子数据
        
        Args:
            factor_name: 因子名称
            columns: 要读取的列
            filters: 过滤条件 [(col, op, value)]
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame
        """
        file_path = self._get_file_path(factor_name, is_snapshot=False)
        
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        try:
            if filters or start_date or end_date:
                dataset = pq.ParquetDataset(file_path)
                
                if start_date or end_date:
                    from pyarrow import compute as pc
                    partitions = dataset.partitions
                    
                    if start_date:
                        partitions = partitions.filter(
                            pc.field("trade_date") >= pd.Timestamp(start_date)
                        )
                    if end_date:
                        partitions = partitions.filter(
                            pc.field("trade_date") <= pd.Timestamp(end_date)
                        )
                    
                    table = partitions.read(columns=columns)
                    return table.to_pandas()
                else:
                    return dataset.to_pandas(columns=columns)
            
            else:
                return pd.read_parquet(file_path, columns=columns)
            
        except Exception as e:
            logger.error(f"Parquet 读取失败: {e}")
            return pd.DataFrame()
    
    def write_snapshot(self, factor_name: str, snapshot_data: Dict[str, float]):
        """
        写入快照数据（最新因子值）
        
        Args:
            factor_name: 因子名称
            snapshot_data: {symbol: value}
        """
        df = pd.DataFrame([
            {"symbol": symbol, "value": value}
            for symbol, value in snapshot_data.items()
        ])
        
        file_path = self._get_file_path(factor_name, is_snapshot=True)
        df.to_parquet(file_path, compression="snappy", index=False)
    
    def read_snapshot(self, factor_name: str) -> pd.DataFrame:
        """读取快照数据"""
        file_path = self._get_file_path(factor_name, is_snapshot=True)
        
        if not os.path.exists(file_path):
            return pd.DataFrame()
        
        return pd.read_parquet(file_path)
    
    def _get_file_path(self, factor_name: str, is_snapshot: bool = False) -> str:
        """获取文件路径"""
        safe_name = factor_name.replace("/", "_").replace("\\", "_")
        
        if is_snapshot:
            return os.path.join(self.snapshot_dir, f"{safe_name}_snapshot.parquet")
        else:
            return os.path.join(self.daily_dir, f"{safe_name}.parquet")
    
    def list_files(self) -> List[Dict[str, Any]]:
        """列出所有文件及其大小"""
        files = []
        
        for directory in [self.daily_dir, self.snapshot_dir]:
            for filename in os.listdir(directory):
                if filename.endswith(".parquet"):
                    filepath = os.path.join(directory, filename)
                    stat = os.stat(filepath)
                    files.append({
                        "name": filename.replace(".parquet", ""),
                        "path": filepath,
                        "size_bytes": stat.st_size,
                        "size_mb": round(stat.st_size / (1024 * 1024), 2),
                        "modified": stat.st_mtime
                    })
        
        return sorted(files, key=lambda x: x["modified"], reverse=True)
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """获取存储统计"""
        files = self.list_files()
        
        total_size = sum(f["size_bytes"] for f in files)
        total_files = len(files)
        
        daily_files = [f for f in files if "snapshot" not in f["name"]]
        snapshot_files = [f for f in files if "snapshot" in f["name"]]
        
        return {
            "total_files": total_files,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "daily_files": len(daily_files),
            "daily_size_mb": round(sum(f["size_bytes"] for f in daily_files) / (1024 * 1024), 2),
            "snapshot_files": len(snapshot_files),
            "snapshot_size_mb": round(sum(f["size_bytes"] for f in snapshot_files) / (1024 * 1024), 2),
            "base_dir": self.base_dir
        }
