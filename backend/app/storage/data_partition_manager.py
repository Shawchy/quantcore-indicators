"""
数据分区管理器

核心功能：
- 自动管理数据的生命周期和存储位置
- 按时间热度自动分区（热/温/冷/归档）
- 定期执行分区维护任务
- 提供存储空间统计和优化建议

使用统一分类系统: app.storage.classification.DataTier

设计原理：
┌─────────────────────────────────────────────────────────┐
│                    数据生命周期                          │
├──────────┬──────────┬──────────┬──────────┬─────────────┤
│  实时区   │  热数据区  │  温数据区  │  冷数据区   │   归档区    │
│ (Memory) │ (SQLite) │ (Parquet)│ (Parquet) │ (压缩归档)  │
├──────────┼──────────┼──────────┼──────────┼─────────────┤
│  0-1天   │  1-90天  │ 90天-2年  │  2-5年   │  >5年       │
│  行情数据 │  日K线   │  历史K线  │  回测数据 │  历史研究   │
│          │  指标    │  财务数据 │          │             │
├──────────┼──────────┼──────────┼──────────┼─────────────┤
│  RAM     │  SSD     │  HDD/SSD  │  HDD     │  对象存储   │
│  ms级    │  ms级    │  10ms级   │  50ms级  │  秒级       │
└──────────┴──────────┴──────────┴──────────┴─────────────┘

存储成本优化：
- 自动压缩冷数据（节省40%空间）
- 删除过期缓存（释放内存）
- 归档历史数据（降低主库压力）
"""

import os
import shutil
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from loguru import logger
from dataclasses import dataclass
import asyncio

from app.storage.classification import DataTier


@dataclass
class PartitionRule:
    """分区规则"""
    tier: DataTier
    max_age_days: int
    storage_type: str        # 'memory', 'sqlite', 'parquet', 'compressed_parquet'
    compression: Optional[str]  # None, 'zstd', 'gzip'
    description: str


@dataclass 
class PartitionStats:
    """分区统计"""
    tier: DataTier
    file_count: int
    total_size_mb: float
    record_count: int
    last_access: Optional[datetime]


# 默认分区规则（使用统一 DataTier）
DEFAULT_PARTITION_RULES: List[PartitionRule] = [
    PartitionRule(
        tier=DataTier.REALTIME,
        max_age_days=1,
        storage_type='memory',
        compression=None,
        description='实时行情数据（内存缓存，<1天）'
    ),
    PartitionRule(
        tier=DataTier.HOT,
        max_age_days=90,
        storage_type='sqlite',
        compression=None,
        description='热数据（SQLite，1-90天）'
    ),
    PartitionRule(
        tier=DataTier.WARM,
        max_age_days=730,  # 2年
        storage_type='parquet',
        compression=None,
        description='温数据（Parquet标准格式，90天-2年）'
    ),
    PartitionRule(
        tier=DataTier.COLD,
        max_age_days=1825,  # 5年
        storage_type='parquet',
        compression='zstd',
        description='冷数据（ZSTD压缩，2-5年）'
    ),
    PartitionRule(
        tier=DataTier.ARCHIVED,
        max_age_days=float('inf'),
        storage_type='compressed_parquet',
        compression='zstd',
        description='归档数据（高压缩比，>5年）'
    ),
]


class DataPartitionManager:
    """
    数据分区管理器
    
    功能：
    1. 根据数据年龄自动分类到不同分区
    2. 执行定期维护任务（迁移、压缩、清理）
    3. 监控各分区的存储使用情况
    4. 提供优化建议
    
    使用示例：
        >>> manager = DataPartitionManager()
        >>> await manager.run_maintenance()
        >>> stats = manager.get_partition_stats()
    """
    
    def __init__(
        self,
        parquet_base_dir: str = None,
        archive_dir: str = None,
        rules: List[PartitionRule] = None
    ):
        from app.config import settings
        
        self._base_dir = parquet_base_dir or settings.PARQUET_DIR
        self._archive_dir = archive_dir or os.path.join(settings.DATA_DIR, 'archive')
        
        self._rules = rules or DEFAULT_PARTITION_RULES
        
        self._stats_cache: Optional[Dict[DataTier, PartitionStats]] = None
        self._stats_cache_time: Optional[datetime] = None
        
        # 创建目录
        os.makedirs(self._base_dir, exist_ok=True)
        os.makedirs(self._archive_dir, exist_ok=True)
    
    def get_partition_for_data(self, date_str: str) -> DataTier:
        """
        根据数据日期判断应该属于哪个分区（使用统一 DataTier）

        Args:
            date_str: 数据日期 (YYYY-MM-DD)

        Returns:
            DataTier 数据层级
        """
        try:
            data_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return DataTier.HOT
        
        now = datetime.now().date()
        age_days = (now - data_date).days
        
        # 使用 DataTier.from_age_days() 统一判断
        return DataTier.from_age_days(age_days)
    
    async def run_maintenance(self, dry_run: bool = False) -> Dict[str, Any]:
        """
        执行分区维护任务（建议在凌晨运行）
        
        任务内容：
        1. 迁移超龄数据到下一级分区
        2. 压缩冷数据
        3. 清理过期的实时缓存
        4. 更新分区统计
        
        Args:
            dry_run: 是否只模拟不实际执行
        
        Returns:
            维护报告字典
        """
        start_time = datetime.now()
        
        report = {
            'start_time': start_time.isoformat(),
            'actions': [],
            'migrated_files': 0,
            'freed_space_mb': 0.0,
            'errors': []
        }
        
        logger.info("🔧 开始执行数据分区维护任务...")
        
        try:
            # 1. 迁移热数据 → 温数据 (>90天)
            hot_to_warm = await self._migrate_hot_to_warm(dry_run)
            report['actions'].append(hot_to_warm)
            
            # 2. 迁移温数据 → 冷数据 (>2年)
            warm_to_cold = await self._migrate_warm_to_cold(dry_run)
            report['actions'].append(warm_to_cold)
            
            # 3. 清理过期缓存
            cache_cleanup = await self._cleanup_expired_cache(dry_run)
            report['actions'].append(cache_cleanup)
            
            # 统计迁移数量
            for action in report['actions']:
                if isinstance(action, dict):
                    report['migrated_files'] += action.get('migrated_count', 0)
                    report['freed_space_mb'] += action.get('freed_space_mb', 0.0)
            
        except Exception as e:
            error_msg = f"维护任务异常: {e}"
            logger.error(error_msg)
            report['errors'].append(error_msg)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        report['elapsed_seconds'] = elapsed
        report['status'] = 'success' if not report['errors'] else 'partial_success'
        
        logger.info(
            f"✅ 分区维护完成: "
            f"迁移 {report['migrated_files']} 个文件, "
            f"释放 {report['freed_space_mb']:.1f}MB, "
            f"耗时 {elapsed:.1f}s"
        )
        
        return report
    
    async def _migrate_hot_to_warm(self, dry_run: bool = False) -> Dict[str, Any]:
        """迁移热数据到温数据区"""
        result = {
            'action': 'hot_to_warm_migration',
            'migrated_count': 0,
            'freed_space_mb': 0.0
        }
        
        cutoff_date = datetime.now() - timedelta(days=90)
        
        # 扫描 SQLite 中的旧数据
        try:
            from app.storage.sqlite import get_session
            from sqlalchemy import text
            
            async with get_session() as session:
                # 查询超过90天的K线数据量
                query = text("""
                    SELECT code, COUNT(*) as cnt, MIN(date) as min_date, MAX(date) as max_date
                    FROM klines_daily
                    WHERE date < :cutoff
                    GROUP BY code
                    HAVING cnt > 0
                    ORDER BY cnt DESC
                    LIMIT 100
                """)
                
                rows = await session.execute(query, {'cutoff': cutoff_date.strftime('%Y-%m-%d')})
                old_data = rows.fetchall()
                
                if dry_run or not old_data:
                    result['migrated_count'] = len(old_data)
                    return result
                
                # 实际迁移：导出到 Parquet 并从 SQLite 删除
                for row in old_data[:10]:  # 限制每次处理数量
                    code = row.code
                    count = row.cnt
                    
                    # 导出为 Parquet
                    export_query = text("""
                        SELECT * FROM klines_daily
                        WHERE code = :code AND date < :cutoff
                        ORDER BY date ASC
                    """)
                    
                    export_result = await session.execute(
                        export_query,
                        {'code': code, 'cutoff': cutoff_date.strftime('%Y-%m-%d')}
                    )
                    
                    df = pd.DataFrame([dict(r._mapping) for r in export_result.fetchall()])
                    
                    if not df.empty:
                        # 保存到温数据区
                        warm_path = os.path.join(
                            self._base_dir, 
                            'warm', 
                            f"{code}_warm.parquet"
                        )
                        
                        os.makedirs(os.path.dirname(warm_path), exist_ok=True)
                        df.to_parquet(warm_path, index=False, engine='pyarrow')
                        
                        # 从 SQLite 删除已迁移的数据
                        delete_query = text("""
                            DELETE FROM klines_daily
                            WHERE code = :code AND date < :cutoff
                        """)
                        await session.execute(delete_query, {'code': code, 'cutoff': cutoff_date.strftime('%Y-%m-%d')})
                        await session.commit()
                        
                        result['migrated_count'] += 1
                        
                        file_size = os.path.getsize(warm_path) / (1024 * 1024)
                        result['freed_space_mb'] += file_size * 0.3  # 预估节省30%（SQLite开销）
                
        except Exception as e:
            logger.warning(f"热→温迁移失败: {e}")
            result['error'] = str(e)
        
        return result
    
    async def _migrate_warm_to_cold(self, dry_run: bool = False) -> Dict[str, Any]:
        """迁移温数据到冷数据区（压缩）"""
        result = {
            'action': 'warm_to_cold_compression',
            'compressed_count': 0,
            'saved_space_mb': 0.0
        }
        
        warm_dir = os.path.join(self._base_dir, 'warm')
        cold_dir = os.path.join(self._base_dir, 'cold')
        
        if not os.path.exists(warm_dir):
            return result
        
        cutoff_date = datetime.now() - timedelta(days=730)  # 2年
        
        for filename in os.listdir(warm_dir):
            if not filename.endswith('.parquet'):
                continue
            
            filepath = os.path.join(warm_dir, filename)
            
            # 检查文件年龄
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if (datetime.now() - mtime).days < 730:
                continue
            
            if dry_run:
                result['compressed_count'] += 1
                continue
            
            try:
                # 读取并重新压缩写入冷数据区
                df = pd.read_parquet(filepath)
                
                cold_filepath = os.path.join(cold_dir, filename.replace('.parquet', '_cold.parquet'))
                os.makedirs(cold_dir, exist_ok=True)
                
                df.to_parquet(cold_filepath, compression='zstd', index=False)
                
                original_size = os.path.getsize(filepath) / (1024 * 1024)
                compressed_size = os.path.getsize(cold_filepath) / (1024 * 1024)
                
                # 删除原始文件
                os.remove(filepath)
                
                result['compressed_count'] += 1
                result['saved_space_mb'] += (original_size - compressed_size)
                
            except Exception as e:
                logger.warning(f"压缩失败 [{filename}]: {e}")
                result.setdefault('errors', []).append(str(e))
        
        return result
    
    async def _cleanup_expired_cache(self, dry_run: bool = False) -> Dict[str, Any]:
        """清理过期的实时缓存"""
        result = {
            'action': 'cache_cleanup',
            'cleaned_entries': 0,
            'freed_memory_mb': 0.0
        }
        
        try:
            from app.services.cache_service import cache_service
            
            if dry_run:
                stats = cache_service.cache_manager.get_all_stats()
                total_cached = sum(s.get('size', 0) for s in stats.values())
                result['cleaned_entries'] = total_cached // 3  # 估算清理1/3
                return result
            
            # 实际清理
            cleaned = await cache_service.cleanup_expired()
            result['cleaned_entries'] = cleaned
            
        except Exception as e:
            logger.warning(f"缓存清理失败: {e}")
            result['error'] = str(e)
        
        return result
    
    def get_partition_stats(self, force_refresh: bool = False) -> Dict[DataTier, PartitionStats]:
        """
        获取各分区的统计信息

        Args:
            force_refresh: 是否强制刷新缓存

        Returns:
            {DataTier: PartitionStats} 字典
        """
        if (not force_refresh and
            self._stats_cache is not None and
            self._stats_cache_time is not None and
            (datetime.now() - self._stats_cache_time).total_seconds() < 300):  # 5分钟缓存
            return self._stats_cache

        stats = {}

        # 统计各分区（使用统一 DataTier）
        partitions = [
            (DataTier.REALTIME, 'memory', None),
            (DataTier.HOT, 'sqlite', None),
            (DataTier.WARM, 'parquet', os.path.join(self._base_dir, 'warm')),
            (DataTier.COLD, 'parquet', os.path.join(self._base_dir, 'cold')),
            (DataTier.ARCHIVED, 'compressed_parquet', self._archive_dir),
        ]

        for tier, storage_type, directory in partitions:
            if directory is None:
                stats[tier] = PartitionStats(
                    tier=tier,
                    file_count=0,
                    total_size_mb=0.0,
                    record_count=0,
                    last_access=None
                )
                continue

            if not os.path.exists(directory):
                stats[tier] = PartitionStats(
                    tier=tier,
                    file_count=0,
                    total_size_mb=0.0,
                    record_count=0,
                    last_access=None
                )
                continue
            
            files = []
            total_size = 0
            
            for root, dirs, filenames in os.walk(directory):
                for filename in filenames:
                    if filename.endswith(('.parquet', '.db', '.sqlite')):
                        filepath = os.path.join(root, filename)
                        files.append(filepath)
                        total_size += os.path.getsize(filepath)
            
            latest_mtime = 0
            for filepath in files[-10:] if files else []:
                mtime = os.path.getmtime(filepath)
                if mtime > latest_mtime:
                    latest_mtime = mtime
            
            stats[partition] = PartitionStats(
                partition=partition,
                file_count=len(files),
                total_size_mb=total_size / (1024 * 1024),
                record_count=0,  # 需要数据库查询才能精确统计
                last_access=datetime.fromtimestamp(latest_mtime) if latest_mtime > 0 else None
            )
        
        self._stats_cache = stats
        self._stats_cache_time = datetime.now()
        
        return stats
    
    def get_storage_summary(self) -> Dict[str, Any]:
        """获取存储使用摘要"""
        stats = self.get_partition_stats()
        
        total_size = sum(s.total_size_mb for s in stats.values())
        total_files = sum(s.file_count for s in stats.values())
        
        summary = {
            'total_size_gb': round(total_size / 1024, 2),
            'total_files': total_files,
            'partitions': {},
            'recommendations': []
        }
        
        for partition, stat in stats.items():
            pct = (stat.total_size_mb / total_size * 100) if total_size > 0 else 0
            summary['partitions'][partition.value] = {
                'files': stat.file_count,
                'size_mb': round(stat.total_size_mb, 2),
                'percentage': round(pct, 1)
            }
        
        # 生成优化建议
        if stats.get(DataTier.COLD, PartitionStats(tier=DataTier.COLD, file_count=0, total_size_mb=0, record_count=0, last_access=None)).total_size_mb > 1000:
            summary['recommendations'].append({
                'type': 'archive_old_data',
                'message': f'冷数据超过1GB，考虑归档到长期存储以节省空间',
                'priority': 'medium'
            })

        if stats.get(DataTier.REALTIME, PartitionStats(tier=DataTier.REALTIME, file_count=0, total_size_mb=0, record_count=0, last_access=None)).file_count > 500:
            summary['recommendations'].append({
                'type': 'reduce_realtime_cache',
                'message': '实时缓存文件过多，建议增加淘汰策略',
                'priority': 'low'
            })
        
        return summary
    
    def schedule_periodic_maintenance(self, interval_hours: int = 24):
        """
        调度定期维护任务
        
        Args:
            interval_hours: 执行间隔（小时）
        """
        async def maintenance_loop():
            while True:
                try:
                    await asyncio.sleep(interval_hours * 3600)
                    await self.run_maintenance()
                except Exception as e:
                    logger.error(f"定期维护任务异常: {e}")
                    await asyncio.sleep(300)  # 出错后等5分钟重试
        
        task = asyncio.create_task(maintenance_loop())
        task.set_name("data_partition_maintenance")
        
        logger.info(f"✅ 已调度定期维护任务，间隔 {interval_hours} 小时")


# 全局单例
data_partition_manager = DataPartitionManager()
