"""
简化版数据迁移脚本

将现有的 Parquet 文件迁移到新的分类目录结构
"""
from pathlib import Path
import pandas as pd
from datetime import datetime
from loguru import logger


def migrate_parquet_files():
    """迁移 Parquet 文件"""
    base_dir = Path("./data")
    old_parquet_dir = base_dir / "parquet"
    
    if not old_parquet_dir.exists():
        logger.warning("未找到 Parquet 目录")
        return
    
    logger.info("=" * 60)
    logger.info("开始迁移 Parquet 文件")
    logger.info("=" * 60)
    
    stats = {
        "total_files": 0,
        "migrated_files": 0,
        "failed_files": 0,
        "total_records": 0
    }
    
    # 1. 迁移根目录下的 Parquet 文件
    root_parquet_files = list(old_parquet_dir.glob("*.parquet"))
    
    logger.info(f"发现 {len(root_parquet_files)} 个根目录文件")
    
    for parquet_file in root_parquet_files:
        try:
            stats["total_files"] += 1
            
            # 解析文件名: 000001_qfq.parquet
            parts = parquet_file.stem.split("_")
            code = parts[0]
            adjust = parts[1] if len(parts) > 1 else "qfq"
            
            # 读取数据
            df = pd.read_parquet(parquet_file)
            stats["total_records"] += len(df)
            
            # 提取年份
            if 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df['year'] = df['date'].dt.year
                
                # 按年份保存
                for year in df['year'].unique():
                    year_df = df[df['year'] == year].drop('year', axis=1)
                    
                    # 新路径
                    new_path = (
                        base_dir / 
                        "stock" / "market" / "kline" / "daily" / 
                        code / f"{int(year)}_{adjust}.parquet"
                    )
                    
                    # 创建目录
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 保存文件
                    year_df.to_parquet(new_path, index=False, compression='snappy')
                    
                    logger.info(
                        f"✅ 迁移: {parquet_file.name} -> "
                        f"stock/market/kline/daily/{code}/{int(year)}_{adjust}.parquet "
                        f"({len(year_df)} 条记录)"
                    )
            else:
                logger.warning(f"⚠️  文件缺少 date 列: {parquet_file.name}")
            
            stats["migrated_files"] += 1
            
        except Exception as e:
            logger.error(f"❌ 迁移失败: {parquet_file.name}, 错误: {e}")
            stats["failed_files"] += 1
    
    # 2. 迁移 kline 子目录下的文件
    kline_dir = old_parquet_dir / "kline"
    
    if kline_dir.exists():
        for code_dir in kline_dir.iterdir():
            if not code_dir.is_dir():
                continue
            
            code = code_dir.name
            
            for parquet_file in code_dir.glob("*.parquet"):
                try:
                    stats["total_files"] += 1
                    
                    # 解析文件名: 2024_qfq.parquet
                    parts = parquet_file.stem.split("_")
                    year = parts[0]
                    adjust = parts[1] if len(parts) > 1 else "qfq"
                    
                    # 新路径
                    new_path = (
                        base_dir / 
                        "stock" / "market" / "kline" / "daily" / 
                        code / f"{year}_{adjust}.parquet"
                    )
                    
                    # 创建目录
                    new_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    # 读取并保存
                    df = pd.read_parquet(parquet_file)
                    stats["total_records"] += len(df)
                    
                    df.to_parquet(new_path, index=False, compression='snappy')
                    
                    logger.info(
                        f"✅ 迁移: kline/{code}/{parquet_file.name} -> "
                        f"stock/market/kline/daily/{code}/{year}_{adjust}.parquet "
                        f"({len(df)} 条记录)"
                    )
                    
                    stats["migrated_files"] += 1
                    
                except Exception as e:
                    logger.error(f"❌ 迁移失败: {parquet_file.name}, 错误: {e}")
                    stats["failed_files"] += 1
    
    # 打印统计信息
    logger.info("=" * 60)
    logger.info("迁移统计:")
    logger.info(f"  总文件数: {stats['total_files']}")
    logger.info(f"  成功迁移: {stats['migrated_files']}")
    logger.info(f"  失败文件: {stats['failed_files']}")
    logger.info(f"  总记录数: {stats['total_records']}")
    logger.info("=" * 60)
    logger.info("迁移完成！")


if __name__ == "__main__":
    migrate_parquet_files()
