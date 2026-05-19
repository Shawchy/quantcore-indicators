"""
数据生命周期管理器

实现数据的自动归档、压缩和清理机制
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import pandas as pd
import shutil
import gzip
from loguru import logger
from sqlalchemy import select, and_


class DataLifecycleManager:
    """数据生命周期管理器"""
    
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir)
        
        # 生命周期配置
        self.lifecycle_config = {
            "hot": {
                "storage": "sqlite",
                "threshold_days": 90,
                "description": "热数据 - 频繁访问"
            },
            "warm": {
                "storage": "parquet",
                "threshold_days": 365,
                "description": "温数据 - 偶尔访问"
            },
            "cold": {
                "storage": "archive",
                "threshold_days": 730,
                "description": "冷数据 - 很少访问"
            },
            "expired": {
                "storage": "delete",
                "threshold_days": 1825,  # 5 年
                "description": "过期数据 - 删除或归档"
            }
        }
        
        # 统计信息
        self.stats = {
            "archived_files": 0,
            "compressed_files": 0,
            "deleted_files": 0,
            "archived_records": 0,
            "compressed_records": 0,
            "deleted_records": 0,
            "space_saved_mb": 0.0
        }
    
    def classify_data(self, date: str) -> str:
        """
        数据分层
        
        Args:
            date: 数据日期 (支持 YYYY-MM-DD 或 YYYYMMDD 格式)
        
        Returns:
            数据层级 (hot/warm/cold/expired)
        """
        # 统一日期格式
        from app.utils.date_utils import to_compact_date
        
        try:
            # 尝试转换为紧凑格式
            normalized = to_compact_date(date) or date.replace('-', '')
            data_date = datetime.strptime(normalized, "%Y%m%d")
        except Exception as e:
            logger.warning(f"日期解析失败：{date}, 错误：{e}")
            data_date = datetime.now()
        
        days_old = (datetime.now() - data_date).days
        
        if days_old <= 90:
            return "hot"
        elif days_old <= 365:
            return "warm"
        elif days_old <= 730:
            return "cold"
        else:
            return "expired"
    
    async def auto_archive(self, code: str):
        """
        自动归档旧数据
        
        将 SQLite 中的旧数据迁移到 Parquet
        """
        from app.storage.sqlite import get_session, KLine
        from app.storage.parquet_manager import ParquetManager
        
        threshold_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        logger.info(f"开始归档 {code} 的旧数据 (早于 {threshold_date})")
        
        try:
            async with get_session() as session:
                # 查询需要归档的数据
                query = select(KLine).where(
                    and_(
                        KLine.code == code,
                        KLine.date < threshold_date
                    )
                )
                result = await session.execute(query)
                old_klines = result.scalars().all()
                
                if not old_klines:
                    logger.info(f"{code} 无需归档的数据")
                    return
                
                # 转换为字典
                kline_dicts = []
                for kline in old_klines:
                    kline_dicts.append({
                        "code": kline.code,
                        "date": kline.date,
                        "open": kline.open,
                        "high": kline.high,
                        "low": kline.low,
                        "close": kline.close,
                        "volume": kline.volume,
                        "amount": kline.amount,
                        "turnover_rate": kline.turnover_rate,
                        "adjust_type": kline.adjust_type,
                    })
                
                # 保存到 Parquet
                parquet_manager = ParquetManager()
                saved_count = parquet_manager.save_klines(code, kline_dicts)
                
                # 从 SQLite 删除
                for kline in old_klines:
                    await session.delete(kline)
                await session.commit()
                
                # 更新统计
                self.stats["archived_files"] += 1
                self.stats["archived_records"] += len(old_klines)
                
                logger.info(
                    f"归档完成: {code}, "
                    f"记录数: {len(old_klines)}, "
                    f"保存到 Parquet: {saved_count}"
                )
        
        except Exception as e:
            logger.error(f"归档失败: {code}, 错误: {e}")
            raise e
    
    async def auto_compress_cold_data(self, code: str, year: int):
        """
        自动压缩冷数据
        
        将超过 2 年的 Parquet 文件压缩到归档目录
        """
        parquet_path = (
            self.base_dir / 
            "stock" / "market" / "kline" / "daily" / 
            code / f"{year}_qfq.parquet"
        )
        
        if not parquet_path.exists():
            logger.debug(f"文件不存在: {parquet_path}")
            return
        
        try:
            # 读取数据
            df = pd.read_parquet(parquet_path)
            
            # 检查数据年龄
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                latest_date = df['date'].max()
                days_old = (datetime.now() - latest_date).days
                
                if days_old > 730:  # 超过 2 年
                    # 压缩到归档目录
                    archive_dir = self.base_dir / "archive" / "kline" / str(year)
                    archive_dir.mkdir(parents=True, exist_ok=True)
                    
                    archive_path = archive_dir / f"{code}_qfq.parquet.gz"
                    
                    # 使用 gzip 压缩（压缩率更高）
                    df.to_parquet(archive_path, compression='gzip')
                    
                    # 计算节省的空间
                    original_size = parquet_path.stat().st_size
                    compressed_size = archive_path.stat().st_size
                    space_saved = (original_size - compressed_size) / 1024 / 1024
                    
                    # 删除原文件
                    parquet_path.unlink()
                    
                    # 更新统计
                    self.stats["compressed_files"] += 1
                    self.stats["compressed_records"] += len(df)
                    self.stats["space_saved_mb"] += space_saved
                    
                    logger.info(
                        f"压缩完成: {code} {year}, "
                        f"记录数: {len(df)}, "
                        f"节省空间: {space_saved:.2f} MB"
                    )
        
        except Exception as e:
            logger.error(f"压缩失败: {code} {year}, 错误: {e}")
            raise e
    
    async def cleanup_expired_data(self, code: str):
        """
        清理过期数据
        
        删除超过 5 年的数据
        """
        threshold_date = (datetime.now() - timedelta(days=1825)).strftime("%Y-%m-%d")
        threshold_year = int(threshold_date[:4])
        
        logger.info(f"开始清理 {code} 的过期数据 (早于 {threshold_year} 年)")
        
        # 删除归档目录中的过期数据
        archive_dir = self.base_dir / "archive" / "kline"
        
        if not archive_dir.exists():
            return
        
        deleted_count = 0
        
        for year_dir in archive_dir.iterdir():
            if not year_dir.is_dir():
                continue
            
            try:
                year = int(year_dir.name)
                if year < threshold_year:
                    # 统计记录数
                    for parquet_file in year_dir.glob("*.parquet.gz"):
                        try:
                            df = pd.read_parquet(parquet_file)
                            deleted_count += len(df)
                        except Exception:
                            pass
                    
                    # 删除整个年份目录
                    shutil.rmtree(year_dir)
                    
                    logger.info(f"删除过期数据: {year} 年")
            
            except ValueError:
                continue
        
        # 更新统计
        self.stats["deleted_files"] += 1
        self.stats["deleted_records"] += deleted_count
        
        logger.info(f"清理完成: {code}, 删除记录数: {deleted_count}")
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self.stats,
            "space_saved_mb": round(self.stats["space_saved_mb"], 2)
        }
    
    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            "archived_files": 0,
            "compressed_files": 0,
            "deleted_files": 0,
            "archived_records": 0,
            "compressed_records": 0,
            "deleted_records": 0,
            "space_saved_mb": 0.0
        }


# 全局生命周期管理器实例
lifecycle_manager = DataLifecycleManager()
