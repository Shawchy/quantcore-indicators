"""
统一存储抽象层

整合缓存、持久化存储和本地数据库，提供统一的数据访问接口
采用三级存储架构：
- L1: 内存缓存（LRU Cache）- 最快，容量小
- L2: 本地数据库（SQLite）- 较快，容量中
- L3: 文件存储（Parquet）- 较慢，容量大
"""
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from loguru import logger

from app.storage.cache import AsyncLRUCache
from app.services.local_database import local_db_service
from app.storage.parquet_store import ParquetStore

T = TypeVar('T')


class StorageTier(Enum):
    """存储层级"""
    L1_CACHE = "l1_cache"  # 内存缓存
    L2_DATABASE = "l2_database"  # SQLite 数据库
    L3_PARQUET = "l3_parquet"  # Parquet 文件


class DataCategory(Enum):
    """数据分类"""
    QUOTE = "quote"  # 实时行情
    KLINE_DAILY = "kline_daily"  # 日线 K 线
    KLINE_WEEKLY = "kline_weekly"  # 周线 K 线
    KLINE_MONTHLY = "kline_monthly"  # 月线 K 线
    FUND = "fund"  # 基金数据
    SECTOR = "sector"  # 板块数据
    BILLBOARD = "billboard"  # 龙虎榜
    MONEYFLOW = "moneyflow"  # 资金流向
    FINANCIAL = "financial"  # 财务数据
    SHAREHOLDER = "shareholder"  # 股东信息
    EXCHANGE = "exchange"  # 交易所数据


class UnifiedStorage(Generic[T]):
    """
    统一存储器
    
    提供三级存储的透明访问，自动选择最优存储层级
    """
    
    def __init__(
        self,
        category: DataCategory,
        cache_ttl: int = 300,
        cache_size: int = 1000,
        auto_sync: bool = True
    ):
        """
        Args:
            category: 数据分类
            cache_ttl: L1 缓存 TTL（秒）
            cache_size: L1 缓存大小
            auto_sync: 是否自动同步到下级存储
        """
        self.category = category
        self.cache_ttl = cache_ttl
        self.auto_sync = auto_sync
        
        # L1: 内存缓存
        self._cache = AsyncLRUCache(max_size=cache_size, ttl=cache_ttl)
        
        # L2: 本地数据库（延迟初始化）
        self._db_initialized = False
        self._db_init_lock = asyncio.Lock()  # 防止并发初始化
        
        # L3: Parquet 存储
        self._parquet = ParquetStore()
        
        # 统计信息（使用锁保护）
        self._stats = {
            "l1_hits": 0,
            "l2_hits": 0,
            "l3_hits": 0,
            "misses": 0,
            "writes": 0
        }
        self._stats_lock = asyncio.Lock()
    
    async def _ensure_db_initialized(self):
        """确保数据库已初始化（线程安全）"""
        if not self._db_initialized:
            async with self._db_init_lock:
                # 双重检查锁定模式
                if not self._db_initialized:
                    if local_db_service._initialized:
                        self._db_initialized = True
                    else:
                        await local_db_service.initialize()
                        self._db_initialized = True
    
    def _generate_key(self, identifier: str, **kwargs) -> str:
        """生成统一的键"""
        parts = [self.category.value, identifier]
        for k, v in sorted(kwargs.items()):
            parts.append(f"{k}={v}")
        return "_".join(parts)
    
    async def get(self, identifier: str, **kwargs) -> Optional[T]:
        """
        获取数据（自动从最优层级）
        
        Args:
            identifier: 数据标识（如股票代码）
            **kwargs: 额外参数（如 start_date, end_date）
            
        Returns:
            数据，如果不存在则返回 None
        """
        key = self._generate_key(identifier, **kwargs)
        
        # L1: 尝试从缓存获取
        cached = await self._cache.get(key)
        if cached is not None:
            async with self._stats_lock:
                self._stats["l1_hits"] += 1
            logger.debug(f"L1 缓存命中：{key}")
            return cached
        
        await self._ensure_db_initialized()
        
        # L2: 从数据库获取
        data = await self._get_from_db(identifier, **kwargs)
        if data:
            async with self._stats_lock:
                self._stats["l2_hits"] += 1
            logger.debug(f"L2 数据库命中：{key}")
            # 回填到 L1 缓存
            await self._cache.set(key, data, ttl=self.cache_ttl)
            return data
        
        # L3: 从 Parquet 获取（历史数据）
        l3_data = await self._get_from_parquet(identifier, **kwargs)
        if l3_data:
            async with self._stats_lock:
                self._stats["l3_hits"] += 1
            logger.debug(f"L3 Parquet 命中：{key}")
            # 回填到 L1 和 L2
            await self._cache.set(key, l3_data, ttl=self.cache_ttl)
            await self._set_to_db(identifier, l3_data, **kwargs)
            return l3_data
        
        async with self._stats_lock:
            self._stats["misses"] += 1
        logger.debug(f"未命中：{key}")
        return None
    
    async def set(
        self,
        identifier: str,
        data: T,
        sync_to_lower: bool = True,
        **kwargs
    ) -> bool:
        """
        保存数据
        
        Args:
            identifier: 数据标识
            data: 数据
            sync_to_lower: 是否同步到下级存储
            **kwargs: 额外参数
            
        Returns:
            是否成功
        """
        key = self._generate_key(identifier, **kwargs)
        
        # L1: 写入缓存
        await self._cache.set(key, data, ttl=self.cache_ttl)
        async with self._stats_lock:
            self._stats["writes"] += 1
        
        # 同步到 L2
        if sync_to_lower and self.auto_sync:
            await self._ensure_db_initialized()
            await self._set_to_db(identifier, data, **kwargs)
        
        logger.debug(f"数据已保存：{key}")
        return True
    
    async def _get_from_db(self, identifier: str, **kwargs) -> Optional[T]:
        """从数据库获取数据的内部方法"""
        try:
            category = self.category.value
            
            # 根据数据分类调用不同的数据库方法
            if category in ["kline_daily", "kline_weekly", "kline_monthly"]:
                code = identifier
                start_date = kwargs.get("start_date")
                end_date = kwargs.get("end_date")
                
                if category == "kline_daily":
                    result = await local_db_service.get_kline_from_db(code, start_date, end_date)
                    return result
                elif category == "kline_weekly":
                    result = await local_db_service.get_kline_weekly_from_db(code, start_date, end_date)
                    return result
                elif category == "kline_monthly":
                    result = await local_db_service.get_kline_monthly_from_db(code, start_date, end_date)
                    return result
            
            elif category == "quote":
                code = identifier
                result = await local_db_service.get_quote_from_db(code)
                return result
            
            elif category == "fund":
                code = identifier
                result = await local_db_service.get_fund_nav_from_db(code)
                return result
            
            elif category == "billboard":
                trade_date = kwargs.get("trade_date")
                code = kwargs.get("code")
                result = await local_db_service.get_billboard_from_db(trade_date, code)
                return result
            
            elif category == "moneyflow":
                code = identifier
                start_date = kwargs.get("start_date")
                end_date = kwargs.get("end_date")
                result = await local_db_service.get_moneyflow_from_db(code, start_date, end_date)
                return result
            
            elif category == "financial":
                code = identifier
                report_date = kwargs.get("report_date")
                result = await local_db_service.get_financial_from_db(code, report_date)
                return result
            
            elif category == "shareholder":
                code = identifier
                report_date = kwargs.get("report_date")
                result = await local_db_service.get_shareholder_from_db(code, report_date)
                return result
            
            elif category == "sector":
                sector_code = identifier
                result = await local_db_service.get_sector_components_from_db(sector_code)
                return result
            
            elif category == "exchange":
                # 交易所数据使用 JSON 文件存储（特殊类型，不常变化）
                result = await self._load_from_json_file("exchanges")
                return result
            
        except Exception as e:
            logger.error(f"从数据库获取数据失败：{identifier}, 错误：{e}")
        
        return None
    
    async def _set_to_db(self, identifier: str, data: T, **kwargs):
        """同步到数据库的内部方法"""
        try:
            category = self.category.value
            
            if category in ["kline_daily", "kline_weekly", "kline_monthly"]:
                code = identifier
                if category == "kline_daily":
                    await local_db_service.sync_kline_data(code, data)
                elif category == "kline_weekly":
                    await local_db_service.sync_kline_weekly(code, data)
                elif category == "kline_monthly":
                    await local_db_service.sync_kline_monthly(code, data)
            
            elif category == "quote":
                # quotes 是列表
                if isinstance(data, list):
                    await local_db_service.sync_quote_data(data)
            
            elif category == "fund":
                code = identifier
                await local_db_service.sync_fund_nav(code, data)
            
            elif category == "billboard":
                if isinstance(data, list):
                    await local_db_service.sync_billboard(data)
            
            elif category == "moneyflow":
                if isinstance(data, list):
                    await local_db_service.sync_moneyflow(data)
            
            elif category == "financial":
                if isinstance(data, list):
                    code = identifier
                    report_date = kwargs.get("report_date")
                    await local_db_service.sync_financial(code, data)
            
            elif category == "shareholder":
                if isinstance(data, list):
                    code = identifier
                    report_date = kwargs.get("report_date")
                    await local_db_service.sync_shareholder(code, report_date, data)
            
            elif category == "sector":
                if isinstance(data, list):
                    sector_name = kwargs.get("sector_name", "")
                    await local_db_service.sync_sector_components(identifier, sector_name, data)
            
            elif category == "exchange":
                # 交易所数据使用 JSON 文件存储
                await self._save_to_json_file("exchanges", data)
            
            logger.debug(f"数据已同步到数据库：{identifier}")
            
        except Exception as e:
            logger.error(f"同步到数据库失败：{identifier}, 错误：{e}")
            logger.error(f"同步数据到数据库失败：{e}")
    
    async def _load_from_json_file(self, data_type: str) -> Optional[Any]:
        """从 JSON 文件加载数据（用于交易所等特殊类型）"""
        try:
            from pathlib import Path
            import json
            from app.config import settings
            
            file_path = Path(settings.PARQUET_DIR) / f"{data_type}.json"
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.debug(f"从 JSON 文件加载 {data_type} 数据成功")
                return data
            return None
        except Exception as e:
            logger.error(f"从 JSON 文件加载失败：{e}")
            return None
    
    async def _save_to_json_file(self, data_type: str, data: Any) -> bool:
        """保存数据到 JSON 文件"""
        try:
            from pathlib import Path
            import json
            from app.config import settings
            
            file_path = Path(settings.PARQUET_DIR) / f"{data_type}.json"
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.debug(f"数据已保存到 JSON 文件：{file_path}")
            return True
        except Exception as e:
            logger.error(f"保存到 JSON 文件失败：{e}")
            return False
    
    async def _get_from_parquet(self, identifier: str, **kwargs) -> Optional[T]:
        """从 Parquet 文件获取数据（L3 存储）"""
        try:
            category = self.category.value
            
            # K 线数据从 Parquet 读取
            if category in ["kline_daily", "kline_weekly", "kline_monthly"]:
                code = identifier
                start_date = kwargs.get("start_date")
                end_date = kwargs.get("end_date")
                
                # 从 Parquet 读取 K 线数据
                df = await self._parquet.read_kline(
                    code=code,
                    period=category.replace("kline_", ""),
                    start_date=start_date,
                    end_date=end_date
                )
                
                if df is not None and not df.empty:
                    # 转换为 KLineData 列表
                    from app.models.unified_models import UnifiedKLine
                    klines = []
                    for _, row in df.iterrows():
                        kline = UnifiedKLine(
                            code=code,
                            date=row.get('date', ''),
                            open=float(row.get('open', 0)),
                            high=float(row.get('high', 0)),
                            low=float(row.get('low', 0)),
                            close=float(row.get('close', 0)),
                            volume=float(row.get('volume', 0)),
                            amount=float(row.get('amount', 0)) if 'amount' in row else None
                        )
                        klines.append(kline)
                    
                    logger.debug(f"从 Parquet 读取 K 线数据成功：{code} {len(klines)}条")
                    return klines
            
            # 基金数据从 Parquet 读取
            elif category == "fund":
                code = identifier
                start_date = kwargs.get("start_date")
                end_date = kwargs.get("end_date")
                
                df = await self._parquet.read_fund_nav(
                    code=code,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if df is not None and not df.empty:
                    logger.debug(f"从 Parquet 读取基金数据成功：{code}")
                    return df.to_dict('records')
            
            return None
            
        except Exception as e:
            logger.error(f"从 Parquet 读取失败：{e}")
            return None
    
    async def delete(self, identifier: str, **kwargs) -> bool:
        """删除数据"""
        key = self._generate_key(identifier, **kwargs)
        deleted = await self._cache.delete(key)
        
        # 从数据库删除
        await self._delete_from_db(identifier, **kwargs)
        
        return deleted
    
    async def _delete_from_db(self, identifier: str, **kwargs):
        """从数据库删除数据的内部方法"""
        try:
            await self._ensure_db_initialized()
            category = self.category.value
            
            # 根据数据分类调用不同的数据库删除方法
            if category in ["kline_daily", "kline_weekly", "kline_monthly"]:
                code = identifier
                start_date = kwargs.get("start_date")
                end_date = kwargs.get("end_date")
                
                if category == "kline_daily":
                    await local_db_service.delete_kline_data(code, start_date, end_date)
                elif category == "kline_weekly":
                    await local_db_service.delete_kline_weekly(code, start_date, end_date)
                elif category == "kline_monthly":
                    await local_db_service.delete_kline_monthly(code, start_date, end_date)
            
            elif category == "quote":
                code = identifier
                await local_db_service.delete_quote_data(code)
            
            elif category == "fund":
                code = identifier
                await local_db_service.delete_fund_nav(code)
            
            elif category == "billboard":
                trade_date = kwargs.get("trade_date")
                code = kwargs.get("code")
                await local_db_service.delete_billboard(trade_date, code)
            
            elif category == "moneyflow":
                code = identifier
                start_date = kwargs.get("start_date")
                end_date = kwargs.get("end_date")
                await local_db_service.delete_moneyflow(code, start_date, end_date)
            
            logger.debug(f"数据已从数据库删除：{identifier}")
            
        except Exception as e:
            logger.error(f"从数据库删除失败：{e}")
    
    async def clear(self):
        """清空缓存"""
        await self._cache.clear()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        cache_stats = self._cache.get_stats()
        return {
            "category": self.category.value,
            "l1_cache": cache_stats,
            "l2_database": "initialized" if self._db_initialized else "not_initialized",
            "hits": {
                "l1": self._stats["l1_hits"],
                "l2": self._stats["l2_hits"],
                "l3": self._stats["l3_hits"],
                "total": self._stats["l1_hits"] + self._stats["l2_hits"] + self._stats["l3_hits"]
            },
            "misses": self._stats["misses"],
            "writes": self._stats["writes"],
            "hit_rate": f"{(self._stats['l1_hits'] + self._stats['l2_hits']) / max(1, sum(self._stats.values())) * 100:.2f}%"
        }


# ========== 便捷访问接口 ==========

class StorageManager:
    """
    存储管理器
    
    提供预配置的存储器实例，简化使用
    """
    
    def __init__(self):
        self._storages: Dict[DataCategory, UnifiedStorage] = {}
    
    def get_storage(
        self,
        category: DataCategory,
        cache_ttl: int = 300,
        cache_size: int = 1000
    ) -> UnifiedStorage:
        """获取或创建存储器"""
        if category not in self._storages:
            self._storages[category] = UnifiedStorage(
                category=category,
                cache_ttl=cache_ttl,
                cache_size=cache_size
            )
        return self._storages[category]
    
    def get_kline_storage(self, period: str = "daily") -> UnifiedStorage:
        """获取 K 线存储器"""
        category_map = {
            "daily": DataCategory.KLINE_DAILY,
            "weekly": DataCategory.KLINE_WEEKLY,
            "monthly": DataCategory.KLINE_MONTHLY
        }
        return self.get_storage(category_map.get(period, DataCategory.KLINE_DAILY))
    
    def get_quote_storage(self) -> UnifiedStorage:
        """获取行情存储器"""
        return self.get_storage(DataCategory.QUOTE)
    
    def get_fund_storage(self) -> UnifiedStorage:
        """获取基金存储器"""
        return self.get_storage(DataCategory.FUND)
    
    def get_exchange_storage(self) -> UnifiedStorage:
        """获取交易所数据存储器"""
        return self.get_storage(DataCategory.EXCHANGE, cache_ttl=86400 * 7)  # 7 天缓存
    
    def get_all_stats(self) -> Dict[str, Any]:
        """获取所有存储器的统计信息"""
        return {
            category.value: storage.get_stats()
            for category, storage in self._storages.items()
        }


# 全局实例
storage_manager = StorageManager()
