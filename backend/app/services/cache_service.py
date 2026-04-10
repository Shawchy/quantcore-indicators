"""
统一的缓存服务

提供标准化的缓存管理功能，消除各 Service 的重复缓存逻辑
使用统一分类系统: app.storage.classification.UNIFIED_DATA_CONFIGS
"""
from typing import Any, Optional, Callable, Dict, List
from loguru import logger
import asyncio

from app.storage.cache import CacheManager
from app.storage.classification import UNIFIED_DATA_CONFIGS, get_config


class CacheService:
    """
    统一的三级缓存服务

    使用模式:
        cache.get_or_fetch(key, fetch_func, data_type)

    缓存层级:
        L1: 内存缓存 (AsyncLRUCache)
        L2: 数据库缓存 (可选)
        L3: 外部数据源
    """

    def __init__(self):
        self.cache_manager = CacheManager()

        # 从统一配置生成 cache_config（单一数据源）
        self.cache_config = {
            data_type: {
                "ttl": config.ttl,
                "l2_enabled": config.l2_enabled
            }
            for data_type, config in UNIFIED_DATA_CONFIGS.items()
        }

        logger.info(f"CacheService 初始化完成（从 UNIFIED_DATA_CONFIGS 加载 {len(self.cache_config)} 个配置）")
    
    async def get_or_fetch(
        self,
        key: str,
        fetch_func: Callable,
        data_type: str = "default",
        use_l2: bool = True
    ) -> Any:
        """
        统一的缓存获取模式
        
        流程:
        1. L1: 检查内存缓存
        2. L2: 检查数据库缓存（可选）
        3. L3: 调用获取函数
        
        Args:
            key: 缓存键
            fetch_func: 数据获取函数（异步）
            data_type: 数据类型（用于选择缓存策略）
            use_l2: 是否使用 L2 数据库缓存
        
        Returns:
            数据
        """
        config = self.cache_config.get(data_type, {"ttl": 300, "l2_enabled": False})
        
        # L1: 检查内存缓存
        cached = await self.cache_manager.get(data_type, key)
        if cached is not None:
            logger.debug(f"L1 缓存命中：{key}")
            return cached
        
        # L2: 检查数据库缓存（如果启用）
        if use_l2 and config.get("l2_enabled", False):
            db_data = await self._get_from_db(key, data_type)
            if db_data is not None:
                logger.debug(f"L2 数据库缓存命中：{key}")
                # 回填 L1 缓存
                await self.cache_manager.set(data_type, key, db_data, ttl=config["ttl"])
                return db_data
        
        # L3: 调用获取函数
        logger.debug(f"缓存未命中，获取数据：{key}")
        data = await fetch_func()
        
        if data is not None:
            # 保存到缓存
            await self.set(key, data, data_type)
        
        return data
    
    async def get(
        self,
        key: str,
        data_type: str = "default"
    ) -> Optional[Any]:
        """
        从缓存获取数据
        
        Args:
            key: 缓存键
            data_type: 数据类型
        
        Returns:
            缓存数据，如果不存在则返回 None
        """
        return await self.cache_manager.get(data_type, key)
    
    async def set(
        self,
        key: str,
        data: Any,
        data_type: str = "default",
        ttl: Optional[int] = None
    ):
        """
        保存数据到缓存
        
        Args:
            key: 缓存键
            data: 数据
            data_type: 数据类型
            ttl: 过期时间（秒），如果为 None 则使用默认配置
        """
        config = self.cache_config.get(data_type, {"ttl": 300})
        effective_ttl = ttl if ttl is not None else config["ttl"]
        
        # 保存到内存缓存
        await self.cache_manager.set(data_type, key, data, ttl=effective_ttl)
        logger.debug(f"缓存保存：{key}, data_type={data_type}, ttl={effective_ttl}")
    
    async def delete(self, key: str, data_type: str = "default"):
        """
        删除缓存
        
        Args:
            key: 缓存键
            data_type: 数据类型
        """
        await self.cache_manager.delete(data_type, key)
        logger.debug(f"删除缓存：{key}")
    
    async def clear(self, data_type: Optional[str] = None):
        """
        清除缓存
        
        Args:
            data_type: 数据类型，如果为 None 则清除所有
        """
        if data_type:
            await self.cache_manager.clear_cache(data_type)
            logger.info(f"清除 {data_type} 缓存")
        else:
            await self.cache_manager.clear_all()
            logger.info("清除所有缓存")
    
    async def _get_from_db(self, key: str, data_type: str) -> Optional[Any]:
        """
        从数据库获取缓存数据（子类可以实现）
        
        Args:
            key: 缓存键
            data_type: 数据类型
        
        Returns:
            数据库中的数据
        """
        # 默认实现：返回 None
        return None
    
    async def _save_to_db(self, key: str, data: Any, data_type: str):
        """
        保存到数据库（子类可以实现）
        
        Args:
            key: 缓存键
            data: 数据
            data_type: 数据类型
        """
        # 默认实现：空操作
        pass
    
    def get_config(self, data_type: str) -> Dict[str, Any]:
        """
        获取缓存配置
        
        Args:
            data_type: 数据类型
        
        Returns:
            缓存配置字典
        """
        return self.cache_config.get(data_type, {"ttl": 300, "l2_enabled": False})
    
    def set_config(self, data_type: str, config: Dict[str, Any]):
        """
        设置缓存配置
        
        Args:
            data_type: 数据类型
            config: 配置字典
        """
        self.cache_config[data_type] = config
        logger.info(f"更新缓存配置：{data_type} = {config}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            包含各缓存类型统计的字典
        """
        return self.cache_manager.get_all_stats()
    
    async def warmup_cache(
        self,
        keys: List[str],
        fetch_func: Callable,
        data_type: str = "default",
        batch_size: int = 10
    ):
        """
        批量预热缓存

        Args:
            keys: 缓存键列表
            fetch_func: 数据获取函数
            data_type: 数据类型
            batch_size: 批次大小
        """
        logger.info(f"开始预热缓存：{len(keys)} 个键，data_type={data_type}")

        # 分批处理
        for i in range(0, len(keys), batch_size):
            batch_keys = keys[i:i + batch_size]
            tasks = [
                self.get_or_fetch(key=key, fetch_func=fetch_func, data_type=data_type)
                for key in batch_keys
            ]

            try:
                await asyncio.gather(*tasks, return_exceptions=True)
                logger.debug(f"完成批次 {i // batch_size + 1}/{(len(keys) + batch_size - 1) // batch_size}")
            except Exception as e:
                logger.error(f"预热缓存批次失败：{e}")

        logger.info("缓存预热完成")

    def get_cache_stats_for_api(self) -> Dict[str, Any]:
        """
        获取缓存统计信息（API 兼容格式）

        Returns:
            与 cache_optimizer 兼容的统计格式
        """
        all_stats = self.cache_manager.get_all_stats()

        # 计算总体统计
        total_hits = sum(s.get("hits", 0) for s in all_stats.values())
        total_misses = sum(s.get("misses", 0) for s in all_stats.values())
        total_requests = total_hits + total_misses
        overall_hit_rate = f"{(total_hits / total_requests * 100):.2f}%" if total_requests > 0 else "0%"

        # 模拟多级缓存结构（为了API兼容）
        # 将高频访问的缓存映射为 L1，其他为 L2
        l1_caches = ["realtime", "kline"]
        l2_caches = ["indicators", "sector"]

        l1_hits = sum(all_stats.get(name, {}).get("hits", 0) for name in l1_caches)
        l1_misses = sum(all_stats.get(name, {}).get("misses", 0) for name in l1_caches)
        l1_total = l1_hits + l1_misses
        l1_hit_rate = f"{(l1_hits / l1_total * 100):.2f}%" if l1_total > 0 else "0%"

        l2_hits = sum(all_stats.get(name, {}).get("hits", 0) for name in l2_caches)
        l2_misses = sum(all_stats.get(name, {}).get("misses", 0) for name in l2_caches)
        l2_total = l2_hits + l2_misses
        l2_hit_rate = f"{(l2_hits / l2_total * 100):.2f}%" if l2_total > 0 else "0%"

        l3_hits = total_hits - l1_hits - l2_hits
        l3_misses = total_misses - l1_misses - l2_misses
        l3_total = l3_hits + l3_misses
        l3_hit_rate = f"{(l3_hits / l3_total * 100):.2f}%" if l3_total > 0 else "0%"

        return {
            "l1_cache": {
                **all_stats.get(l1_caches[0], {}),
                "hit_rate": l1_hit_rate
            },
            "l2_cache": {
                **all_stats.get(l2_caches[0], {}),
                "hit_rate": l2_hit_rate
            },
            "l3_cache": {
                "size": 0,
                "max_size": 10000,
                "ttl": 3600,
                "hits": l3_hits,
                "misses": l3_misses,
                "evictions": 0,
                "hit_rate": l3_hit_rate
            },
            "stats": {
                "l1_hits": l1_hits,
                "l2_hits": l2_hits,
                "l3_hits": l3_hits,
                "total_misses": total_misses,
                "total_requests": total_requests,
                "overall_hit_rate": overall_hit_rate
            }
        }

    async def warmup_cache_simple(
        self,
        data_type: str,
        items: List[str]
    ) -> Dict[str, Any]:
        """
        简化版缓存预热（API 兼容接口）

        Args:
            data_type: 数据类型（如 'kline', 'sector'）
            items: 数据项列表（如股票代码列表）

        Returns:
            预热结果统计
        """
        logger.info(f"开始缓存预热: {data_type}, 数量: {len(items)}")

        warmed = 0

        if data_type == "kline":
            from app.services.stock_service import stock_service

            for code in items:
                try:
                    await stock_service.get_kline(code)
                    warmed += 1

                    if warmed % 10 == 0:
                        logger.info(f"预热进度: {warmed}/{len(items)}")

                except Exception as e:
                    logger.warning(f"预热失败: {code}, {e}")
        elif data_type == "sector":
            from app.services.sector_service import sector_service

            for sector_name in items:
                try:
                    await sector_service.get_sector_stocks(sector_name)
                    warmed += 1
                except Exception as e:
                    logger.warning(f"预热失败: {sector_name}, {e}")
        else:
            logger.warning(f"不支持的预热数据类型: {data_type}")

        logger.info(f"缓存预热完成: {data_type}, 成功: {warmed}")

        return {
            "data_type": data_type,
            "total": len(items),
            "warmed": warmed
        }

    async def clear_by_level(self, level: Optional[str] = None):
        """
        按级别清空缓存（API 兼容接口）

        Args:
            level: 缓存级别 ('l1', 'l2', 'l3', None表示全部)
        """
        if level == "l1":
            # 清除高频访问缓存 (realtime, kline)
            for cache_type in ["realtime", "kline"]:
                await self.cache_manager.clear_cache(cache_type)
            logger.info(f"已清空 L1 缓存")
        elif level == "l2":
            # 清除中频访问缓存 (indicators, sector)
            for cache_type in ["indicators", "sector"]:
                await self.cache_manager.clear_cache(cache_type)
            logger.info(f"已清空 L2 缓存")
        elif level == "l3":
            # 清除低频访问缓存 (chip, screener, backtest)
            for cache_type in ["chip", "screener", "backtest"]:
                await self.cache_manager.clear_cache(cache_type)
            logger.info(f"已清空 L3 缓存")
        else:
            # 清除所有缓存
            await self.cache_manager.clear_all()
            logger.info(f"已清空所有缓存")

    def get_policies(self) -> Dict[str, Dict[str, Any]]:
        """
        获取缓存策略配置（API 兼容接口）

        Returns:
            缓存策略字典
        """
        policies = {}
        for data_type, config in self.cache_config.items():
            policies[data_type] = {
                "ttl": config.get("ttl", 300),
                "level": "l1" if data_type in ["realtime", "kline"] else "l2",
                "preload": config.get("l2_enabled", False)
            }
        return policies

    def set_policy(self, cache_type: str, policy: Dict[str, Any]):
        """
        设置缓存策略（API 兼容接口）

        Args:
            cache_type: 缓存类型
            policy: 策略配置
        """
        ttl = policy.get("ttl", 300)
        level = policy.get("level", "l2")
        preload = policy.get("preload", False)

        self.cache_config[cache_type] = {
            "ttl": ttl,
            "l2_enabled": preload
        }

        logger.info(f"缓存策略已更新: {cache_type}")


# 全局实例
cache_service = CacheService()
