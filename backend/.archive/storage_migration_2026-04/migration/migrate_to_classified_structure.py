"""
数据迁移脚本

将现有的 Parquet 文件迁移到新的分类目录结构
"""
from pathlib import Path
import pandas as pd
import shutil
from datetime import datetime
from loguru import logger
import asyncio
from typing import List, Dict


class DataMigration:
    """数据迁移工具"""
    
    def __init__(self, base_dir: str = "./data"):
        self.base_dir = Path(base_dir)
        self.old_parquet_dir = self.base_dir / "parquet"
        self.new_data_dir = self.base_dir
        
        # 统计信息
        self.stats = {
            "total_files": 0,
            "migrated_files": 0,
            "failed_files": 0,
            "total_records": 0
        }
    
    async def migrate_all(self):
        """迁移所有数据"""
        logger.info("开始数据迁移...")
        
        # 1. 迁移股票 K 线数据
        await self.migrate_stock_kline()
        
        # 2. 迁移基金数据
        await self.migrate_fund_data()
        
        # 3. 迁移市场数据
        await self.migrate_market_data()
        
        # 4. 生成索引文件
        await self.generate_index_files()
        
        # 5. 打印统计信息
        self._print_stats()
        
        logger.info("数据迁移完成！")
    
    async def migrate_stock_kline(self):
        """迁移股票 K 线数据"""
        logger.info("开始迁移股票 K 线数据...")
        
        old_kline_dir = self.old_parquet_dir / "kline"
        
        if not old_kline_dir.exists():
            logger.warning(f"K 线目录不存在: {old_kline_dir}")
            return
        
        # 遍历所有股票代码目录
        for code_dir in old_kline_dir.iterdir():
            if not code_dir.is_dir():
                continue
            
            code = code_dir.name
            
            # 遍历该股票的所有 Parquet 文件
            for parquet_file in code_dir.glob("*.parquet"):
                try:
                    await self._migrate_kline_file(code, parquet_file)
                    self.stats["migrated_files"] += 1
                except Exception as e:
                    logger.error(f"迁移失败: {parquet_file.name}, 错误: {e}")
                    self.stats["failed_files"] += 1
        
        logger.info(f"股票 K 线数据迁移完成，成功: {self.stats['migrated_files']}, 失败: {self.stats['failed_files']}")
    
    async def _migrate_kline_file(self, code: str, parquet_file: Path):
        """迁移单个 K 线文件"""
        # 解析文件名: 2024_qfq.parquet
        parts = parquet_file.stem.split("_")
        year = parts[0]
        adjust = parts[1] if len(parts) > 1 else "qfq"
        
        # 新路径: stock/market/kline/daily/{code}/{year}_{adjust}.parquet
        new_path = (
            self.new_data_dir / 
            "stock" / "market" / "kline" / "daily" / 
            code / f"{year}_{adjust}.parquet"
        )
        
        # 创建目标目录
        new_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 读取数据
        df = pd.read_parquet(parquet_file)
        
        # 统计记录数
        self.stats["total_records"] += len(df)
        
        # 写入新位置
        df.to_parquet(new_path, index=False, compression='snappy')
        
        logger.info(f"迁移: {parquet_file.name} -> {new_path.relative_to(self.new_data_dir)}")
        
        self.stats["total_files"] += 1
    
    async def migrate_fund_data(self):
        """迁移基金数据"""
        logger.info("开始迁移基金数据...")
        
        # 检查是否有基金数据
        fund_files = list(self.old_parquet_dir.glob("fund_*.parquet"))
        
        if not fund_files:
            logger.info("未发现基金数据文件")
            return
        
        for fund_file in fund_files:
            try:
                await self._migrate_fund_file(fund_file)
                self.stats["migrated_files"] += 1
            except Exception as e:
                logger.error(f"迁移失败: {fund_file.name}, 错误: {e}")
                self.stats["failed_files"] += 1
        
        logger.info(f"基金数据迁移完成")
    
    async def _migrate_fund_file(self, fund_file: Path):
        """迁移单个基金文件"""
        # 解析文件名: fund_nav_000001.parquet
        parts = fund_file.stem.split("_")
        
        if len(parts) >= 3:
            data_type = parts[1]  # nav, return, etc.
            fund_code = parts[2]
        else:
            logger.warning(f"无法解析基金文件名: {fund_file.name}")
            return
        
        # 根据数据类型确定目标目录
        type_mapping = {
            "nav": "fund/performance/nav",
            "return": "fund/performance/return",
            "ranking": "fund/performance/ranking",
            "risk": "fund/performance/risk",
            "position": "fund/portfolio/stock_position",
        }
        
        target_dir = type_mapping.get(data_type, "fund/basic/info")
        
        # 新路径
        new_path = (
            self.new_data_dir / 
            target_dir / 
            f"{fund_code}.parquet"
        )
        
        # 创建目标目录
        new_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制文件
        shutil.copy2(fund_file, new_path)
        
        logger.info(f"迁移: {fund_file.name} -> {new_path.relative_to(self.new_data_dir)}")
        
        self.stats["total_files"] += 1
    
    async def migrate_market_data(self):
        """迁移市场数据"""
        logger.info("开始迁移市场数据...")
        
        # 检查是否有指数数据
        index_files = list(self.old_parquet_dir.glob("index_*.parquet"))
        
        if not index_files:
            logger.info("未发现市场数据文件")
            return
        
        for index_file in index_files:
            try:
                await self._migrate_index_file(index_file)
                self.stats["migrated_files"] += 1
            except Exception as e:
                logger.error(f"迁移失败: {index_file.name}, 错误: {e}")
                self.stats["failed_files"] += 1
        
        logger.info(f"市场数据迁移完成")
    
    async def _migrate_index_file(self, index_file: Path):
        """迁移指数文件"""
        # 解析文件名: index_000001.parquet
        parts = index_file.stem.split("_")
        
        if len(parts) >= 2:
            index_code = parts[1]
        else:
            logger.warning(f"无法解析指数文件名: {index_file.name}")
            return
        
        # 新路径
        new_path = (
            self.new_data_dir / 
            "market" / "index" / "kline" / 
            f"{index_code}.parquet"
        )
        
        # 创建目标目录
        new_path.parent.mkdir(parents=True, exist_ok=True)
        
        # 复制文件
        shutil.copy2(index_file, new_path)
        
        logger.info(f"迁移: {index_file.name} -> {new_path.relative_to(self.new_data_dir)}")
        
        self.stats["total_files"] += 1
    
    async def generate_index_files(self):
        """生成索引文件"""
        logger.info("开始生成索引文件...")
        
        # 为每个二级分类目录生成索引
        index_dirs = [
            "stock/market/kline/daily",
            "stock/financial/balance_sheet",
            "stock/technical/indicators",
            "fund/performance/nav",
            "market/index/kline",
        ]
        
        for index_dir in index_dirs:
            index_path = self.new_data_dir / index_dir / "_index.parquet"
            
            if not index_path.parent.exists():
                continue
            
            # 收集该目录下所有 Parquet 文件的信息
            index_data = []
            
            for parquet_file in index_path.parent.rglob("*.parquet"):
                if parquet_file.name == "_index.parquet":
                    continue
                
                try:
                    # 读取文件获取基本信息
                    df = pd.read_parquet(parquet_file)
                    
                    index_data.append({
                        "file_path": str(parquet_file.relative_to(self.new_data_dir)),
                        "file_name": parquet_file.name,
                        "file_size_mb": round(parquet_file.stat().st_size / 1024 / 1024, 2),
                        "record_count": len(df),
                        "created_at": datetime.fromtimestamp(parquet_file.stat().st_ctime).isoformat(),
                        "updated_at": datetime.fromtimestamp(parquet_file.stat().st_mtime).isoformat(),
                    })
                except Exception as e:
                    logger.warning(f"无法读取文件: {parquet_file.name}, 错误: {e}")
            
            if index_data:
                index_df = pd.DataFrame(index_data)
                index_df.to_parquet(index_path, index=False)
                logger.info(f"生成索引: {index_path.relative_to(self.new_data_dir)}, 包含 {len(index_data)} 个文件")
        
        logger.info("索引文件生成完成")
    
    def _print_stats(self):
        """打印统计信息"""
        logger.info("=" * 60)
        logger.info("数据迁移统计:")
        logger.info(f"  总文件数: {self.stats['total_files']}")
        logger.info(f"  成功迁移: {self.stats['migrated_files']}")
        logger.info(f"  失败文件: {self.stats['failed_files']}")
        logger.info(f"  总记录数: {self.stats['total_records']}")
        logger.info("=" * 60)


async def main():
    """主函数"""
    migration = DataMigration(base_dir="./data")
    await migration.migrate_all()


if __name__ == "__main__":
    asyncio.run(main())
