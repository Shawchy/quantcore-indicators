"""
统一的 Parquet 文件管理器

提供标准化的 Parquet 文件存储和加载功能
"""
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger


class ParquetManager:
    """统一的 Parquet 文件管理器"""
    
    def __init__(self, base_dir: str = "./data/parquet"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # 统一的目录结构
        self.kline_dir = self.base_dir / "kline"
        self.indicators_dir = self.base_dir / "indicators"
        self.chip_dir = self.base_dir / "chip"
        self.backtest_dir = self.base_dir / "backtest"
        
        # 创建目录
        for dir_path in [self.kline_dir, self.indicators_dir, 
                         self.chip_dir, self.backtest_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)
    
    def get_kline_path(
        self,
        code: str,
        year: int,
        adjust_type: str = "qfq"
    ) -> Path:
        """
        获取 K 线文件路径
        
        目录结构:
        data/parquet/kline/{code}/{year}_{adjust_type}.parquet
        
        Args:
            code: 股票代码（6 位）
            year: 年份
            adjust_type: 复权类型（qfq/hfq/none）
        
        Returns:
            Parquet 文件路径
        """
        code_dir = self.kline_dir / code
        code_dir.mkdir(parents=True, exist_ok=True)
        return code_dir / f"{year}_{adjust_type}.parquet"
    
    def save_klines(
        self,
        code: str,
        klines: List[Dict[str, Any]],
        adjust_type: str = "qfq"
    ) -> int:
        """
        保存 K 线数据到 Parquet
        
        特性:
        - 按年份自动分区
        - 自动合并和去重
        - 保留元数据
        
        Args:
            code: 股票代码
            klines: K 线数据列表
            adjust_type: 复权类型
        
        Returns:
            保存的记录数
        """
        if not klines:
            return 0
        
        df = pd.DataFrame(klines)
        
        # 提取年份
        df['date'] = pd.to_datetime(df['date'])
        df['year'] = df['date'].dt.year
        
        saved_count = 0
        for year in df['year'].unique():
            year_df = df[df['year'] == year].drop('year', axis=1)
            parquet_path = self.get_kline_path(code, int(year), adjust_type)
            
            if parquet_path.exists():
                # 读取已有数据
                existing_df = pd.read_parquet(parquet_path)
                
                # 合并数据
                combined_df = pd.concat([existing_df, year_df], ignore_index=True)
                
                # 去重（保留最新）
                combined_df = combined_df.drop_duplicates(
                    subset=['date'],
                    keep='last'
                )
                
                # 排序
                combined_df = combined_df.sort_values('date')
            else:
                combined_df = year_df
            
            # 添加元数据
            combined_df['updated_at'] = datetime.now().isoformat()
            combined_df['source'] = 'multi_source'
            
            # 保存
            combined_df.to_parquet(parquet_path, index=False)
            saved_count += len(year_df)
            
            logger.debug(f"保存 {code} {year}年 K 线到 {parquet_path}, 共{len(year_df)}条")
        
        return saved_count
    
    def load_klines(
        self,
        code: str,
        start_date: str,
        end_date: str,
        adjust_type: str = "qfq"
    ) -> pd.DataFrame:
        """
        加载 K 线数据
        
        自动从多个年份文件中加载并合并
        
        Args:
            code: 股票代码
            start_date: 开始日期（YYYY-MM-DD）
            end_date: 结束日期（YYYY-MM-DD）
            adjust_type: 复权类型
        
        Returns:
            包含 K 线数据的 DataFrame
        """
        start_year = int(start_date[:4])
        end_year = int(end_date[:4])
        
        dfs = []
        for year in range(start_year, end_year + 1):
            parquet_path = self.get_kline_path(code, year, adjust_type)
            if parquet_path.exists():
                df = pd.read_parquet(parquet_path)
                dfs.append(df)
        
        if not dfs:
            return pd.DataFrame()
        
        # 合并
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # 筛选日期范围
        combined_df['date'] = pd.to_datetime(combined_df['date'])
        mask = (combined_df['date'] >= start_date) & (combined_df['date'] <= end_date)
        result = combined_df[mask]
        
        return result.sort_values('date')
    
    def get_indicators_path(self, code: str) -> Path:
        """获取技术指标文件路径"""
        self.indicators_dir.mkdir(parents=True, exist_ok=True)
        return self.indicators_dir / f"{code}.parquet"
    
    def save_indicators(
        self,
        code: str,
        indicators: List[Dict[str, Any]]
    ) -> int:
        """
        保存技术指标数据
        
        Args:
            code: 股票代码
            indicators: 技术指标数据列表
        
        Returns:
            保存的记录数
        """
        if not indicators:
            return 0
        
        df = pd.DataFrame(indicators)
        parquet_path = self.get_indicators_path(code)
        
        if parquet_path.exists():
            # 读取已有数据
            existing_df = pd.read_parquet(parquet_path)
            
            # 合并数据
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            
            # 去重（保留最新）
            combined_df = combined_df.drop_duplicates(
                subset=['date'],
                keep='last'
            )
            
            # 排序
            combined_df = combined_df.sort_values('date')
        else:
            combined_df = df
        
        # 添加元数据
        combined_df['updated_at'] = datetime.now().isoformat()
        
        # 保存
        combined_df.to_parquet(parquet_path, index=False)
        logger.debug(f"保存 {code} 技术指标到 {parquet_path}, 共{len(df)}条")
        
        return len(df)
    
    def load_indicators(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        加载技术指标数据
        
        Args:
            code: 股票代码
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        
        Returns:
            包含技术指标的 DataFrame
        """
        parquet_path = self.get_indicators_path(code)
        if not parquet_path.exists():
            return pd.DataFrame()
        
        df = pd.read_parquet(parquet_path)
        
        # 筛选日期范围
        if start_date or end_date:
            df['date'] = pd.to_datetime(df['date'])
            mask = True
            if start_date:
                mask = mask & (df['date'] >= start_date)
            if end_date:
                mask = mask & (df['date'] <= end_date)
            df = df[mask]
        
        return df.sort_values('date')
    
    def get_chip_path(self, code: str) -> Path:
        """获取筹码数据文件路径"""
        self.chip_dir.mkdir(parents=True, exist_ok=True)
        return self.chip_dir / f"{code}.parquet"
    
    def save_chip_data(
        self,
        code: str,
        chip_data: List[Dict[str, Any]]
    ) -> int:
        """
        保存筹码数据
        
        Args:
            code: 股票代码
            chip_data: 筹码数据列表
        
        Returns:
            保存的记录数
        """
        if not chip_data:
            return 0
        
        df = pd.DataFrame(chip_data)
        parquet_path = self.get_chip_path(code)
        
        if parquet_path.exists():
            existing_df = pd.read_parquet(parquet_path)
            combined_df = pd.concat([existing_df, df], ignore_index=True)
            combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
            combined_df = combined_df.sort_values('date')
        else:
            combined_df = df
        
        combined_df['updated_at'] = datetime.now().isoformat()
        combined_df.to_parquet(parquet_path, index=False)
        logger.debug(f"保存 {code} 筹码数据到 {parquet_path}, 共{len(df)}条")
        
        return len(df)
    
    def load_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        加载筹码数据
        
        Args:
            code: 股票代码
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
        
        Returns:
            包含筹码数据的 DataFrame
        """
        parquet_path = self.get_chip_path(code)
        if not parquet_path.exists():
            return pd.DataFrame()
        
        df = pd.read_parquet(parquet_path)
        
        if start_date or end_date:
            df['date'] = pd.to_datetime(df['date'])
            mask = True
            if start_date:
                mask = mask & (df['date'] >= start_date)
            if end_date:
                mask = mask & (df['date'] <= end_date)
            df = df[mask]
        
        return df.sort_values('date')
    
    def get_backtest_path(self, backtest_id: str) -> Path:
        """获取回测结果文件路径"""
        self.backtest_dir.mkdir(parents=True, exist_ok=True)
        return self.backtest_dir / f"{backtest_id}.parquet"
    
    def save_backtest_result(
        self,
        backtest_id: str,
        result: Dict[str, Any]
    ):
        """
        保存回测结果
        
        Args:
            backtest_id: 回测 ID
            result: 回测结果字典
        """
        # 将嵌套字典展平
        df_data = []
        for key, value in result.items():
            if isinstance(value, list):
                if value and isinstance(value[0], dict):
                    df_data.extend(value)
            elif not isinstance(value, (dict, list)):
                df_data.append({key: value})
        
        if df_data:
            df = pd.DataFrame(df_data)
            parquet_path = self.get_backtest_path(backtest_id)
            df.to_parquet(parquet_path, index=False)
            logger.info(f"保存回测结果 {backtest_id} 到 {parquet_path}")
    
    def load_backtest_result(
        self,
        backtest_id: str
    ) -> pd.DataFrame:
        """
        加载回测结果
        
        Args:
            backtest_id: 回测 ID
        
        Returns:
            包含回测结果的 DataFrame
        """
        parquet_path = self.get_backtest_path(backtest_id)
        if not parquet_path.exists():
            return pd.DataFrame()
        
        return pd.read_parquet(parquet_path)
    
    def add_metadata(
        self,
        parquet_path: Path,
        metadata: Dict[str, Any]
    ):
        """
        添加元数据到 Parquet 文件
        
        元数据包括:
        - 数据来源
        - 更新时间
        - 数据质量评分
        - 版本号
        
        Args:
            parquet_path: Parquet 文件路径
            metadata: 元数据字典
        """
        if not parquet_path.exists():
            return
        
        # 读取
        df = pd.read_parquet(parquet_path)
        
        # 添加元数据列（如果不存在）
        for key, value in metadata.items():
            if key not in df.columns:
                df[key] = value
        
        # 保存
        df.to_parquet(parquet_path, index=False)
        logger.debug(f"添加元数据到 {parquet_path}")
    
    def cleanup_old_files(
        self,
        days_threshold: int = 365
    ):
        """
        清理旧文件
        
        Args:
            days_threshold: 保留天数阈值
        """
        cutoff_date = datetime.now().timestamp() - (days_threshold * 24 * 60 * 60)
        
        for parquet_file in self.base_dir.rglob("*.parquet"):
            if parquet_file.stat().st_mtime < cutoff_date:
                logger.info(f"删除旧文件：{parquet_file}")
                parquet_file.unlink()
