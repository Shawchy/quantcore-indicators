"""
缓存预热服务

应用启动时预加载热门数据到缓存，减少首次请求延迟
"""
import asyncio
from typing import List, Optional
from loguru import logger

from app.storage.cache import cache_manager


WARMUP_STOCKS: List[str] = [
    "600000", "600036", "000001", "601318", "600519",
    "000858", "601398", "600030", "000333", "601888",
    "600900", "601012", "000651", "600276", "601166",
    "600887", "000568", "601668", "600048", "002475",
]

WARMUP_SECTORS: List[str] = [
    "industry_银行",
    "industry_证券",
    "industry_保险",
    "industry_食品饮料",
    "industry_医药生物",
    "industry_电子",
    "industry_计算机",
    "industry_房地产",
]


class CacheWarmupService:

    def __init__(self, batch_size: int = 5, delay_between_batches: float = 0.5):
        self._batch_size = batch_size
        self._delay = delay_between_batches
        self._warmed_up = False
        self._stats = {
            "stocks_attempted": 0,
            "stocks_success": 0,
            "sectors_attempted": 0,
            "sectors_success": 0,
            "errors": 0,
        }

    async def warmup(self) -> dict:
        if self._warmed_up:
            logger.info("缓存已预热，跳过重复预热")
            return self._stats

        logger.info("开始缓存预热...")

        try:
            await self._warmup_kline()
            await self._warmup_sectors()
            self._warmed_up = True
            logger.info(
                f"缓存预热完成 - 股票: {self._stats['stocks_success']}/{self._stats['stocks_attempted']}, "
                f"板块: {self._stats['sectors_success']}/{self._stats['sectors_attempted']}"
            )
        except Exception as e:
            logger.error(f"缓存预热异常: {e}")
            self._stats["errors"] += 1

        return self._stats

    async def _warmup_kline(self):
        from app.adapters import data_source_manager

        for i in range(0, len(WARMUP_STOCKS), self._batch_size):
            batch = WARMUP_STOCKS[i:i + self._batch_size]
            tasks = []
            for code in batch:
                tasks.append(self._warmup_single_kline(data_source_manager, code))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for code, result in zip(batch, results):
                self._stats["stocks_attempted"] += 1
                if isinstance(result, Exception):
                    logger.debug(f"预热K线失败 {code}: {result}")
                    self._stats["errors"] += 1
                elif result:
                    self._stats["stocks_success"] += 1

            if i + self._batch_size < len(WARMUP_STOCKS):
                await asyncio.sleep(self._delay)

    async def _warmup_single_kline(self, dsm, code: str) -> bool:
        try:
            data = await dsm.get_kline(code)
            if data:
                await cache_manager.set("kline", code, data)
                return True
            return False
        except Exception as e:
            logger.debug(f"预热K线异常 {code}: {e}")
            raise

    async def _warmup_sectors(self):
        from app.adapters import data_source_manager

        try:
            sector_list = await data_source_manager.get_sector_list(sector_type="industry")
            if sector_list:
                for sector in sector_list[:8]:
                    self._stats["sectors_attempted"] += 1
                    try:
                        sector_key = f"industry_{sector.name if hasattr(sector, 'name') else sector}"
                        await cache_manager.set("sector", sector_key, sector)
                        self._stats["sectors_success"] += 1
                    except Exception as e:
                        logger.debug(f"预热板块失败: {e}")
                        self._stats["errors"] += 1
                    await asyncio.sleep(self._delay)
        except Exception as e:
            logger.debug(f"获取板块列表失败: {e}")
            self._stats["errors"] += 1

    @property
    def is_warmed_up(self) -> bool:
        return self._warmed_up

    def get_stats(self) -> dict:
        return {**self._stats, "warmed_up": self._warmed_up}


cache_warmup_service = CacheWarmupService()
