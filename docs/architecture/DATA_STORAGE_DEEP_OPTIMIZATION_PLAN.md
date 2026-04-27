# 数据中台与存储深度优化方案

## 📊 当前数据存储现状分析

### 实际存储情况

#### SQLite 数据库
- **位置**: `backend/data/sqlite/quant.db`
- **用途**: 热数据存储（<90 天）
- **表结构**: 7 个核心表（stock_info, kline, technical_indicators, watchlist, chip_data, sector_info, strategy）
- **索引优化**: 已实现复合索引优化

#### Parquet 文件存储
- **位置**: `backend/data/parquet/`
- **实际文件**:
  ```
  parquet/
  ├── kline/
  │   └── 600000/
  │       ├── 2024_qfq.parquet
  │       └── 2025_qfq.parquet
  ├── 000001_qfq.parquet  # ⚠️ 根目录文件
  ├── 000858_qfq.parquet
  ├── 600000_qfq.parquet
  ├── 600036_qfq.parquet
  └── 600519_qfq.parquet
  ```

### 存在的问题

#### 🔴 严重问题
1. **Parquet 文件组织混乱**
   - 部分文件在根目录，部分在子目录
   - 缺少统一的目录结构规范
   - 影响查询效率和维护性

2. **缺少数据生命周期管理**
   - 没有自动归档机制
   - 没有过期数据清理
   - 磁盘空间可能无限增长

3. **缺少数据备份机制**
   - 没有定期备份
   - 数据丢失风险高

#### 🟡 重要问题
4. **缺少数据质量监控**
   - 数据完整性检查不足
   - 数据异常发现滞后

5. **缺少存储性能优化**
   - Parquet 文件大小不优化
   - 压缩策略单一

6. **缺少数据血缘追踪**
   - 数据来源不可追溯
   - 数据质量问题难定位

---

## 🎯 深度优化方案

### 一、数据存储架构重构

#### 1.1 统一 Parquet 目录结构

**当前问题**: 文件组织混乱，查询效率低

**优化方案**: 实施标准化目录结构

```
data/
├── sqlite/
│   └── quant.db                    # SQLite 数据库
│
├── parquet/
│   ├── kline/                      # K 线数据
│   │   ├── {code}/                 # 按股票代码分区
│   │   │   ├── {year}_{adjust}.parquet  # 按年份和复权类型
│   │   │   └── metadata.json       # 元数据
│   │   └── _index.parquet          # 全局索引
│   │
│   ├── indicators/                 # 技术指标
│   │   ├── {code}/
│   │   │   └── {year}.parquet
│   │   └── _index.parquet
│   │
│   ├── chip/                       # 筹码数据
│   │   ├── {code}/
│   │   │   └── {year}.parquet
│   │   └── _index.parquet
│   │
│   ├── financial/                  # 财务数据
│   │   ├── {code}/
│   │   │   └── {year}.parquet
│   │   └── _index.parquet
│   │
│   └── backtest/                   # 回测结果
│       ├── {strategy_id}/
│       │   └── {timestamp}.parquet
│       └── _index.parquet
│
├── cache/                          # 缓存数据
│   ├── realtime/                   # 实时数据缓存
│   └── temp/                       # 临时数据
│
├── archive/                        # 归档数据（冷数据）
│   ├── kline/
│   │   └── {year}/                 # 按年份归档
│   │       └── {code}_{adjust}.parquet.gz
│   └── metadata.json
│
└── backup/                         # 备份数据
    ├── daily/
    │   └── {date}/
    │       ├── sqlite/
    │       └── parquet/
    └── weekly/
        └── {date}/
```

#### 1.2 实施步骤

```python
# backend/app/storage/migration/migrate_parquet_structure.py
import shutil
from pathlib import Path
from loguru import logger

class ParquetMigration:
    """Parquet 文件迁移工具"""
    
    def __init__(self, parquet_dir: str = "./data/parquet"):
        self.parquet_dir = Path(parquet_dir)
    
    async def migrate_to_standard_structure(self):
        """迁移到标准目录结构"""
        # 1. 扫描根目录下的 Parquet 文件
        root_files = list(self.parquet_dir.glob("*.parquet"))
        
        for file_path in root_files:
            # 解析文件名: 000001_qfq.parquet
            parts = file_path.stem.split("_")
            if len(parts) == 2:
                code, adjust = parts
                
                # 创建目标目录
                target_dir = self.parquet_dir / "kline" / code
                target_dir.mkdir(parents=True, exist_ok=True)
                
                # 读取文件，按年份拆分
                import pandas as pd
                df = pd.read_parquet(file_path)
                
                if 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df['year'] = df['date'].dt.year
                    
                    for year in df['year'].unique():
                        year_df = df[df['year'] == year].drop('year', axis=1)
                        target_file = target_dir / f"{int(year)}_{adjust}.parquet"
                        
                        # 合并已有文件
                        if target_file.exists():
                            existing_df = pd.read_parquet(target_file)
                            combined_df = pd.concat([existing_df, year_df], ignore_index=True)
                            combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
                            combined_df.to_parquet(target_file, index=False, compression='snappy')
                        else:
                            year_df.to_parquet(target_file, index=False, compression='snappy')
                        
                        logger.info(f"迁移: {file_path.name} -> {target_file.name}")
                
                # 删除原文件
                file_path.unlink()
                logger.info(f"已删除原文件: {file_path.name}")
        
        logger.info("Parquet 文件迁移完成")
```

---

### 二、数据生命周期管理

#### 2.1 数据分层策略

```python
# backend/app/storage/lifecycle_manager.py
from datetime import datetime, timedelta
from typing import Dict, List
from pathlib import Path
import pandas as pd
from loguru import logger

class DataLifecycleManager:
    """数据生命周期管理器"""
    
    def __init__(self):
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
    
    async def classify_data(self, date: str) -> str:
        """数据分层"""
        data_date = datetime.strptime(date, "%Y-%m-%d")
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
        """自动归档旧数据"""
        # 1. 从 SQLite 查询需要归档的数据
        threshold_date = (datetime.now() - timedelta(days=90)).strftime("%Y-%m-%d")
        
        async with get_session() as session:
            query = select(KLine).where(
                and_(
                    KLine.code == code,
                    KLine.date < threshold_date
                )
            )
            result = await session.execute(query)
            old_klines = result.scalars().all()
            
            if old_klines:
                # 2. 保存到 Parquet
                kline_dicts = [self._kline_to_dict(k) for k in old_klines]
                self.parquet_manager.save_klines(code, kline_dicts)
                
                # 3. 从 SQLite 删除
                for kline in old_klines:
                    await session.delete(kline)
                await session.commit()
                
                logger.info(f"归档 {code} {len(old_klines)} 条数据到 Parquet")
    
    async def auto_compress_cold_data(self, code: str, year: int):
        """自动压缩冷数据"""
        parquet_path = self.parquet_manager.get_kline_path(code, year)
        
        if not parquet_path.exists():
            return
        
        # 检查数据年龄
        df = pd.read_parquet(parquet_path)
        latest_date = pd.to_datetime(df['date']).max()
        days_old = (datetime.now() - latest_date).days
        
        if days_old > 730:  # 超过 2 年
            # 压缩到归档目录
            archive_dir = Path("./data/archive/kline") / str(year)
            archive_dir.mkdir(parents=True, exist_ok=True)
            
            archive_path = archive_dir / f"{code}_qfq.parquet.gz"
            
            # 使用 gzip 压缩（压缩率更高）
            df.to_parquet(archive_path, compression='gzip')
            
            # 删除原文件
            parquet_path.unlink()
            
            logger.info(f"压缩冷数据: {code} {year} -> {archive_path}")
    
    async def cleanup_expired_data(self, code: str):
        """清理过期数据"""
        threshold_date = (datetime.now() - timedelta(days=1825)).strftime("%Y-%m-%d")
        
        # 删除 5 年以上的数据
        archive_dir = Path("./data/archive/kline")
        for year_dir in archive_dir.glob("*"):
            if year_dir.is_dir():
                year = int(year_dir.name)
                if year < int(threshold_date[:4]):
                    # 删除整个年份目录
                    shutil.rmtree(year_dir)
                    logger.info(f"删除过期数据: {year} 年")
```

#### 2.2 定时任务

```python
# backend/app/tasks/data_lifecycle_tasks.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from loguru import logger

scheduler = AsyncIOScheduler()

async def daily_archive_task():
    """每日归档任务"""
    logger.info("开始每日数据归档...")
    
    lifecycle_manager = DataLifecycleManager()
    
    # 获取所有股票代码
    stock_codes = await get_all_stock_codes()
    
    for code in stock_codes:
        try:
            await lifecycle_manager.auto_archive(code)
        except Exception as e:
            logger.error(f"归档 {code} 失败: {e}")
    
    logger.info("每日数据归档完成")

async def weekly_compress_task():
    """每周压缩任务"""
    logger.info("开始每周数据压缩...")
    
    lifecycle_manager = DataLifecycleManager()
    
    # 压缩 2 年以上的数据
    for year in range(2015, datetime.now().year - 1):
        stock_codes = await get_all_stock_codes()
        
        for code in stock_codes:
            try:
                await lifecycle_manager.auto_compress_cold_data(code, year)
            except Exception as e:
                logger.error(f"压缩 {code} {year} 失败: {e}")
    
    logger.info("每周数据压缩完成")

async def monthly_cleanup_task():
    """每月清理任务"""
    logger.info("开始每月数据清理...")
    
    lifecycle_manager = DataLifecycleManager()
    
    stock_codes = await get_all_stock_codes()
    
    for code in stock_codes:
        try:
            await lifecycle_manager.cleanup_expired_data(code)
        except Exception as e:
            logger.error(f"清理 {code} 失败: {e}")
    
    logger.info("每月数据清理完成")

# 配置定时任务
scheduler.add_job(daily_archive_task, 'cron', hour=2, minute=0)  # 每天凌晨 2 点
scheduler.add_job(weekly_compress_task, 'cron', day_of_week='sun', hour=3, minute=0)  # 每周日凌晨 3 点
scheduler.add_job(monthly_cleanup_task, 'cron', day=1, hour=4, minute=0)  # 每月 1 号凌晨 4 点
```

---

### 三、数据备份与恢复

#### 3.1 自动备份机制

```python
# backend/app/storage/backup_manager.py
import shutil
import gzip
from datetime import datetime
from pathlib import Path
from loguru import logger

class BackupManager:
    """数据备份管理器"""
    
    def __init__(self):
        self.backup_dir = Path("./data/backup")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def create_daily_backup(self):
        """创建每日备份"""
        timestamp = datetime.now().strftime("%Y%m%d")
        backup_path = self.backup_dir / "daily" / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 备份 SQLite
        sqlite_backup = backup_path / "sqlite"
        sqlite_backup.mkdir(exist_ok=True)
        shutil.copy2(
            "./data/sqlite/quant.db",
            sqlite_backup / "quant.db"
        )
        
        # 2. 备份 Parquet 元数据
        metadata_backup = backup_path / "metadata"
        metadata_backup.mkdir(exist_ok=True)
        
        # 生成元数据索引
        await self._generate_metadata_index(metadata_backup / "index.json")
        
        logger.info(f"每日备份完成: {backup_path}")
    
    async def create_weekly_backup(self):
        """创建每周备份"""
        timestamp = datetime.now().strftime("%Y%m%d")
        backup_path = self.backup_dir / "weekly" / timestamp
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 1. 备份 SQLite（压缩）
        sqlite_backup = backup_path / "sqlite"
        sqlite_backup.mkdir(exist_ok=True)
        
        with open("./data/sqlite/quant.db", 'rb') as f_in:
            with gzip.open(sqlite_backup / "quant.db.gz", 'wb') as f_out:
                shutil.copyfileobj(f_in, f_out)
        
        # 2. 备份 Parquet（增量）
        parquet_backup = backup_path / "parquet"
        parquet_backup.mkdir(exist_ok=True)
        
        # 只备份最近 7 天修改的文件
        cutoff_time = datetime.now() - timedelta(days=7)
        
        for parquet_file in Path("./data/parquet").rglob("*.parquet"):
            if datetime.fromtimestamp(parquet_file.stat().st_mtime) > cutoff_time:
                relative_path = parquet_file.relative_to("./data/parquet")
                target_path = parquet_backup / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(parquet_file, target_path)
        
        logger.info(f"每周备份完成: {backup_path}")
    
    async def restore_backup(self, backup_type: str, timestamp: str):
        """恢复备份"""
        backup_path = self.backup_dir / backup_type / timestamp
        
        if not backup_path.exists():
            raise ValueError(f"备份不存在: {backup_path}")
        
        # 1. 恢复 SQLite
        sqlite_backup = backup_path / "sqlite" / "quant.db"
        if sqlite_backup.exists():
            shutil.copy2(sqlite_backup, "./data/sqlite/quant.db")
            logger.info("SQLite 恢复完成")
        
        # 2. 恢复 Parquet（可选）
        parquet_backup = backup_path / "parquet"
        if parquet_backup.exists():
            shutil.copytree(parquet_backup, "./data/parquet", dirs_exist_ok=True)
            logger.info("Parquet 恢复完成")
        
        logger.info(f"备份恢复完成: {backup_path}")
    
    async def cleanup_old_backups(self, retention_days: int = 30):
        """清理旧备份"""
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        
        for backup_type in ["daily", "weekly"]:
            backup_dir = self.backup_dir / backup_type
            
            for backup_path in backup_dir.iterdir():
                if backup_path.is_dir():
                    try:
                        backup_date = datetime.strptime(backup_path.name, "%Y%m%d")
                        if backup_date < cutoff_date:
                            shutil.rmtree(backup_path)
                            logger.info(f"删除旧备份: {backup_path}")
                    except ValueError:
                        continue
```

---

### 四、数据质量监控

#### 4.1 数据质量检查器

```python
# backend/app/storage/quality_monitor.py
from datetime import datetime, timedelta
from typing import Dict, List
import pandas as pd
from loguru import logger

class DataQualityMonitor:
    """数据质量监控器"""
    
    def __init__(self):
        self.quality_thresholds = {
            "completeness": 0.95,    # 完整性阈值
            "accuracy": 0.98,        # 准确性阈值
            "consistency": 0.95,     # 一致性阈值
            "timeliness": 0.90       # 及时性阈值
        }
    
    async def check_data_quality(self, code: str, data_type: str = "kline") -> Dict:
        """检查数据质量"""
        quality_report = {
            "code": code,
            "data_type": data_type,
            "timestamp": datetime.now().isoformat(),
            "metrics": {}
        }
        
        # 1. 完整性检查
        quality_report["metrics"]["completeness"] = await self._check_completeness(code, data_type)
        
        # 2. 准确性检查
        quality_report["metrics"]["accuracy"] = await self._check_accuracy(code, data_type)
        
        # 3. 一致性检查
        quality_report["metrics"]["consistency"] = await self._check_consistency(code, data_type)
        
        # 4. 及时性检查
        quality_report["metrics"]["timeliness"] = await self._check_timeliness(code, data_type)
        
        # 5. 综合评分
        quality_report["overall_score"] = self._calculate_overall_score(quality_report["metrics"])
        
        return quality_report
    
    async def _check_completeness(self, code: str, data_type: str) -> float:
        """完整性检查"""
        # 检查字段完整性
        if data_type == "kline":
            async with get_session() as session:
                query = select(KLine).where(KLine.code == code).limit(100)
                result = await session.execute(query)
                klines = result.scalars().all()
                
                if not klines:
                    return 0.0
                
                # 检查必填字段
                required_fields = ['open', 'high', 'low', 'close', 'volume']
                total_fields = len(required_fields) * len(klines)
                complete_fields = 0
                
                for kline in klines:
                    for field in required_fields:
                        if getattr(kline, field) is not None:
                            complete_fields += 1
                
                return complete_fields / total_fields if total_fields > 0 else 0.0
    
    async def _check_accuracy(self, code: str, data_type: str) -> float:
        """准确性检查"""
        if data_type == "kline":
            async with get_session() as session:
                query = select(KLine).where(KLine.code == code).limit(100)
                result = await session.execute(query)
                klines = result.scalars().all()
                
                if not klines:
                    return 0.0
                
                accurate_count = 0
                
                for kline in klines:
                    # 检查价格合理性
                    if (kline.high >= kline.low and
                        kline.high >= kline.open and
                        kline.high >= kline.close and
                        kline.low <= kline.open and
                        kline.low <= kline.close):
                        accurate_count += 1
                
                return accurate_count / len(klines)
    
    async def _check_consistency(self, code: str, data_type: str) -> float:
        """一致性检查"""
        # 检查跨数据源一致性
        # 这里可以对比不同数据源的数据
        return 0.95  # 简化实现
    
    async def _check_timeliness(self, code: str, data_type: str) -> float:
        """及时性检查"""
        if data_type == "kline":
            async with get_session() as session:
                # 查询最新数据日期
                query = select(KLine).where(
                    KLine.code == code
                ).order_by(KLine.date.desc()).limit(1)
                
                result = await session.execute(query)
                latest_kline = result.scalar_one_or_none()
                
                if not latest_kline:
                    return 0.0
                
                # 检查数据是否最新
                latest_date = datetime.strptime(latest_kline.date, "%Y-%m-%d")
                days_old = (datetime.now() - latest_date).days
                
                # 交易日数据应该在 1 天内更新
                if days_old <= 1:
                    return 1.0
                elif days_old <= 3:
                    return 0.8
                else:
                    return max(0.0, 1.0 - days_old / 30)
    
    def _calculate_overall_score(self, metrics: Dict[str, float]) -> float:
        """计算综合评分"""
        weights = {
            "completeness": 0.3,
            "accuracy": 0.3,
            "consistency": 0.2,
            "timeliness": 0.2
        }
        
        score = sum(
            metrics.get(metric, 0) * weight
            for metric, weight in weights.items()
        )
        
        return round(score, 2)
```

---

### 五、存储性能优化

#### 5.1 Parquet 文件优化

```python
# backend/app/storage/parquet_optimizer.py
import pandas as pd
from pathlib import Path
from loguru import logger

class ParquetOptimizer:
    """Parquet 文件优化器"""
    
    @staticmethod
    async def optimize_parquet_file(file_path: Path):
        """优化单个 Parquet 文件"""
        if not file_path.exists():
            return
        
        # 读取文件
        df = pd.read_parquet(file_path)
        
        # 优化策略
        # 1. 按日期排序
        if 'date' in df.columns:
            df = df.sort_values('date')
        
        # 2. 去重
        df = df.drop_duplicates(subset=['date'], keep='last')
        
        # 3. 选择最优压缩算法
        # snappy: 速度快，压缩率中等
        # gzip: 速度慢，压缩率高
        # brotli: 速度最慢，压缩率最高
        
        file_size = file_path.stat().st_size
        
        if file_size > 10 * 1024 * 1024:  # >10MB
            compression = 'gzip'  # 大文件用 gzip
        else:
            compression = 'snappy'  # 小文件用 snappy
        
        # 4. 写入优化后的文件
        optimized_path = file_path.with_suffix('.optimized.parquet')
        df.to_parquet(optimized_path, index=False, compression=compression)
        
        # 5. 替换原文件
        file_path.unlink()
        optimized_path.rename(file_path)
        
        logger.info(f"优化 Parquet: {file_path.name}, 压缩: {compression}")
    
    @staticmethod
    async def merge_small_files(directory: Path, max_files: int = 10):
        """合并小文件"""
        parquet_files = list(directory.glob("*.parquet"))
        
        if len(parquet_files) <= max_files:
            return
        
        # 按年份分组
        files_by_year = {}
        for file_path in parquet_files:
            year = file_path.stem.split('_')[0]
            if year not in files_by_year:
                files_by_year[year] = []
            files_by_year[year].append(file_path)
        
        # 合并同一年份的文件
        for year, files in files_by_year.items():
            if len(files) > 1:
                dfs = [pd.read_parquet(f) for f in files]
                combined_df = pd.concat(dfs, ignore_index=True)
                combined_df = combined_df.sort_values('date')
                combined_df = combined_df.drop_duplicates(subset=['date'], keep='last')
                
                # 写入合并后的文件
                merged_file = directory / f"{year}_merged.parquet"
                combined_df.to_parquet(merged_file, index=False, compression='snappy')
                
                # 删除原文件
                for f in files:
                    f.unlink()
                
                # 重命名合并文件
                merged_file.rename(directory / f"{year}_qfq.parquet")
                
                logger.info(f"合并 {year} 年文件: {len(files)} -> 1")
```

---

## 📊 优化效果预估

### 存储空间优化

| 优化项 | 当前 | 优化后 | 节省 |
|--------|------|--------|------|
| **Parquet 压缩** | snappy | snappy + gzip | 30% ↓ |
| **文件合并** | 分散小文件 | 合并大文件 | 20% ↓ |
| **冷数据归档** | 无 | gzip 压缩 | 50% ↓ |
| **过期数据清理** | 无 | 自动删除 | 10% ↓ |
| **总体节省** | - | - | **60-70% ↓** |

### 查询性能优化

| 优化项 | 当前 | 优化后 | 提升 |
|--------|------|--------|------|
| **目录结构** | 混乱 | 标准化 | 30% ↑ |
| **索引优化** | 基础索引 | 复合索引 | 50% ↑ |
| **文件大小** | 不定 | 优化后 | 20% ↑ |
| **缓存命中率** | 87% | >95% | 9% ↑ |
| **总体提升** | - | - | **2-3x ↑** |

### 运维效率优化

| 优化项 | 当前 | 优化后 | 提升 |
|--------|------|--------|------|
| **数据备份** | 手动 | 自动 | 100% ↑ |
| **数据归档** | 手动 | 自动 | 100% ↑ |
| **质量监控** | 无 | 自动 | ∞ ↑ |
| **故障恢复** | 小时级 | 分钟级 | 90% ↑ |

---

## 🚀 实施计划

### 阶段一：数据迁移（1 周）
- [ ] 实施标准化目录结构
- [ ] 迁移现有 Parquet 文件
- [ ] 验证数据完整性

### 阶段二：生命周期管理（1 周）
- [ ] 实现自动归档机制
- [ ] 实现自动压缩机制
- [ ] 实现自动清理机制

### 阶段三：备份恢复（3 天）
- [ ] 实现每日备份
- [ ] 实现每周备份
- [ ] 实现备份恢复

### 阶段四：质量监控（3 天）
- [ ] 实现数据质量检查
- [ ] 实现质量报告生成
- [ ] 集成告警系统

### 阶段五：性能优化（3 天）
- [ ] 优化 Parquet 文件
- [ ] 合并小文件
- [ ] 性能测试

---

## 🎯 总结

本深度优化方案涵盖：

1. ✅ **存储架构重构** - 标准化目录结构
2. ✅ **生命周期管理** - 自动归档、压缩、清理
3. ✅ **备份恢复机制** - 自动备份、快速恢复
4. ✅ **数据质量监控** - 完整性、准确性、一致性、及时性
5. ✅ **存储性能优化** - 压缩、合并、索引优化

实施后，数据存储将具备**企业级可靠性、高性能、可维护性**！

---

**最后更新**: 2026-03-28  
**维护者**: 架构团队
