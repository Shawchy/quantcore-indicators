"""
因子数据库模块

提供因子数据的存储、查询和管理功能。
"""

from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, date
import os
import json

import pandas as pd
import numpy as np
from loguru import logger


@dataclass
class FactorRecord:
    """因子数据记录"""
    symbol: str
    trade_date: date
    factor_name: str
    factor_value: float
    factor_group: str = "custom"
    raw_value: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FactorMetadata:
    """因子元数据"""
    factor_name: str
    factor_group: str  # market/fundamental/alternative/structured
    description: str = ""
    calculation_formula: str = ""
    frequency: str = "daily"
    version: str = "1.0"
    status: str = "active"  # active/deprecated/testing
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    total_records: int = 0
    valid_ratio: float = 0.0


class FactorDatabase:
    """
    因子数据库管理类
    
    功能：
    - 因子数据存储和查询
    - 批量导入导出
    - 版本管理
    - 元数据管理
    
    使用示例：
        db = FactorDatabase(data_dir="./factor_data")
        
        # 保存因子
        db.save_factor("MOMENTUM_20", factor_data, group="market")
        
        # 查询因子
        data = db.get_factor("MOMENTUM_20", start_date="2024-01-01")
        
        # 列出可用因子
        factors = db.list_factors()
    """
    
    def __init__(self, data_dir: str = "./factor_data"):
        """
        初始化因子数据库
        
        Args:
            data_dir: 数据存储目录
        """
        self.data_dir = data_dir
        self.parquet_dir = os.path.join(data_dir, "parquet")
        self.meta_file = os.path.join(data_dir, "metadata.json")
        
        # 创建目录
        os.makedirs(self.parquet_dir, exist_ok=True)
        
        # 元数据缓存
        self._metadata_cache: Dict[str, FactorMetadata] = {}
        self._load_metadata()
        
        logger.info(f"FactorDatabase 初始化完成，数据目录: {data_dir}")
    
    def _load_metadata(self):
        """加载元数据"""
        if os.path.exists(self.meta_file):
            try:
                with open(self.meta_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, meta in data.items():
                        self._metadata_cache[name] = FactorMetadata(**meta)
                logger.debug(f"加载 {len(self._metadata_cache)} 条元数据")
            except Exception as e:
                logger.warning(f"加载元数据失败: {e}")
    
    def _save_metadata(self):
        """保存元数据"""
        try:
            data = {}
            for name, meta in self._metadata_cache.items():
                data[name] = {
                    "factor_name": meta.factor_name,
                    "factor_group": meta.factor_group,
                    "description": meta.description,
                    "calculation_formula": meta.calculation_formula,
                    "frequency": meta.frequency,
                    "version": meta.version,
                    "status": meta.status,
                    "created_at": meta.created_at.isoformat(),
                    "updated_at": meta.updated_at.isoformat(),
                    "total_records": meta.total_records,
                    "valid_ratio": meta.valid_ratio
                }
            
            with open(self.meta_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存元数据失败: {e}")
    
    def save_factor(
        self,
        factor_name: str,
        data: pd.DataFrame,
        factor_group: str = "custom",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        保存因子数据到 Parquet 文件
        
        Args:
            factor_name: 因子名称
            data: DataFrame (index=symbol, columns=[date, value])
            factor_group: 因子分组
            metadata: 额外元数据
        """
        if data.empty:
            logger.warning(f"因子 {factor_name} 数据为空，跳过保存")
            return
        
        # 确保数据格式正确
        if not isinstance(data.index, pd.DatetimeIndex):
            if 'date' in data.columns or 'trade_date' in data.columns:
                date_col = 'date' if 'date' in data.columns else 'trade_date'
                data = data.set_index(date_col)
        
        # 保存为 Parquet
        file_path = os.path.join(self.parquet_dir, f"{factor_name}.parquet")
        
        try:
            data.to_parquet(file_path, index=True)
            
            # 更新元数据
            self._update_factor_metadata(factor_name, factor_group, data, metadata)
            
            logger.info(f"保存因子 {factor_name}: {len(data)} 条记录")
            
        except Exception as e:
            logger.error(f"保存因子 {factor_name} 失败: {e}")
            raise
    
    def _update_factor_metadata(
        self,
        factor_name: str,
        factor_group: str,
        data: pd.DataFrame,
        extra_meta: Optional[Dict] = None
    ):
        """更新因子元数据"""
        now = datetime.now()
        
        if factor_name in self._metadata_cache:
            meta = self._metadata_cache[factor_name]
            meta.updated_at = now
            meta.total_records = len(data)
            meta.valid_ratio = data.notna().sum().sum() / (len(data) * len(data.columns))
        else:
            meta = FactorMetadata(
                factor_name=factor_name,
                factor_group=factor_group,
                description=extra_meta.get("description", "") if extra_meta else "",
                frequency=extra_meta.get("frequency", "daily") if extra_meta else "daily",
                created_at=now,
                updated_at=now,
                total_records=len(data),
                valid_ratio=data.notna().sum().sum() / (len(data) * len(data.columns)) if len(data) > 0 else 0
            )
        
        self._metadata_cache[factor_name] = meta
        self._save_metadata()
    
    def get_factor(
        self,
        factor_name: str,
        start_date: Optional[Union[str, date]] = None,
        end_date: Optional[Union[str, date]] = None,
        symbols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        查询因子数据
        
        Args:
            factor_name: 因子名称
            start_date: 开始日期
            end_date: 结束日期
            symbols: 股票代码列表
            
        Returns:
            DataFrame: 因子数据
        """
        file_path = os.path.join(self.parquet_dir, f"{factor_name}.parquet")
        
        if not os.path.exists(file_path):
            logger.warning(f"因子数据不存在: {factor_name}")
            return pd.DataFrame()
        
        try:
            df = pd.read_parquet(file_path)
            
            # 日期过滤
            if start_date is not None:
                if isinstance(start_date, str):
                    start_date = pd.to_datetime(start_date)
                df = df[df.index >= start_date]
            
            if end_date is not None:
                if isinstance(end_date, str):
                    end_date = pd.to_datetime(end_date)
                df = df[df.index <= end_date]
            
            # 股票代码过滤
            if symbols is not None and len(symbols) > 0:
                if isinstance(df.columns, pd.MultiIndex):
                    df = df.loc[:, df.columns.get_level_values(0).isin(symbols)]
                elif hasattr(df.columns, 'levels'):
                    pass  # MultiIndex 处理
                else:
                    df = df[symbols] if all(s in df.columns for s in symbols) else df
            
            return df
            
        except Exception as e:
            logger.error(f"读取因子 {factor_name} 失败: {e}")
            return pd.DataFrame()
    
    def get_latest_snapshot(
        self,
        factor_names: List[str],
        symbols: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        获取最新快照（所有因子的最新值）
        
        Args:
            factor_names: 因子名称列表
            symbols: 股票代码列表
            
        Returns:
            DataFrame: 最新快照 (index=symbol, columns=factor_name)
        """
        snapshots = []
        
        for name in factor_names:
            data = self.get_factor(name)
            if data.empty:
                continue
            
            latest = data.iloc[-1]  # 取最后一行（最新）
            latest.name = name
            snapshots.append(latest)
        
        if not snapshots:
            return pd.DataFrame()
        
        result = pd.DataFrame(snapshots).T
        
        # 过滤股票代码
        if symbols is not None:
            result = result[result.index.isin(symbols)]
        
        return result
    
    def list_factors(
        self,
        group: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        列出可用因子
        
        Args:
            group: 按分组过滤
            status: 按状态过滤
            
        Returns:
            因子信息列表
        """
        results = []
        
        for name, meta in self._metadata_cache.items():
            if group and meta.factor_group != group:
                continue
            if status and meta.status != status:
                continue
            
            results.append({
                "name": name,
                "group": meta.factor_group,
                "description": meta.description,
                "frequency": meta.frequency,
                "version": meta.version,
                "status": meta.status,
                "total_records": meta.total_records,
                "valid_ratio": round(meta.valid_ratio, 4),
                "updated_at": meta.updated_at.strftime("%Y-%m-%d %H:%M:%S") if meta.updated_at else None
            })
        
        return sorted(results, key=lambda x: x["name"])
    
    def delete_factor(self, factor_name: str) -> bool:
        """
        删除因子数据
        
        Args:
            factor_name: 因子名称
            
        Returns:
            是否成功删除
        """
        file_path = os.path.join(self.parquet_dir, f"{factor_name}.parquet")
        
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
            
            if factor_name in self._metadata_cache:
                del self._metadata_cache[factor_name]
                self._save_metadata()
            
            logger.info(f"删除因子: {factor_name}")
            return True
            
        except Exception as e:
            logger.error(f"删除因子 {factor_name} 失败: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取数据库统计"""
        return {
            "total_factors": len(self._metadata_cache),
            "by_group": {
                group: len([m for m in self._metadata_cache.values() if m.factor_group == group])
                for group in ["market", "fundamental", "alternative", "structured"]
            },
            "by_status": {
                status: len([m for m in self._metadata_cache.values() if m.status == status])
                for status in ["active", "deprecated", "testing"]
            },
            "storage_size_mb": sum(
                os.path.getsize(os.path.join(self.parquet_dir, f"{name}.parquet"))
                for name in self._metadata_cache.keys()
                if os.path.exists(os.path.join(self.parquet_dir, f"{name}.parquet"))
            ) / (1024 * 1024),
            "data_dir": self.data_dir
        }
