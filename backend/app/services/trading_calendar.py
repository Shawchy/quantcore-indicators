"""
交易日历服务 - 优化版

优化策略：
1. SQLite 持久化 - 替代 JSON 文件，支持高效查询
2. 多级缓存 - 内存缓存 -> SQLite -> 远程 API
3. 启动时预加载 - 应用启动时异步预加载交易日数据
4. 快速响应 - 优先返回缓存数据，后台异步更新
5. 健康检查 - 定期检查数据是否需要更新
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Set
from loguru import logger
import asyncio
import time
from pathlib import Path

from sqlalchemy import String, Integer, DateTime, Boolean, Index, select, delete
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.sqlite import Base, get_session
from app.storage import sqlite as sqlite_module
from app.utils.date_utils import to_compact_date


class TradingDay(Base):
    __tablename__ = "trading_days"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String(8), unique=True, nullable=False, index=True)
    is_trading_day: Mapped[bool] = mapped_column(Boolean, default=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    __table_args__ = (
        Index("idx_trading_day_date", "date"),
    )


class TradingCalendarService:
    """交易日历服务 - 优化版"""
    
    CACHE_TTL = 86400
    REFRESH_INTERVAL = 3600
    API_TIMEOUT = 5.0
    
    def __init__(self):
        self._memory_cache: Optional[Set[str]] = None
        self._sorted_list_cache: Optional[List[str]] = None
        self._cache_time: float = 0
        self._last_refresh_time: float = 0
        self._is_initialized: bool = False
        self._init_lock: asyncio.Lock = asyncio.Lock()
        self._refresh_task: Optional[asyncio.Task] = None
    
    async def initialize(self) -> bool:
        """初始化交易日历服务"""
        async with self._init_lock:
            if self._is_initialized:
                return True
            
            try:
                start_time = time.time()
                
                await self._ensure_table_exists()
                
                loaded = await self._load_from_db()
                
                if loaded:
                    logger.info(f"交易日历从数据库加载完成，共 {len(self._memory_cache)} 个交易日，耗时 {time.time() - start_time:.3f}s")
                else:
                    logger.info("数据库无交易日数据，开始从远程获取...")
                    await self._fetch_and_save_from_remote()
                
                self._is_initialized = True
                
                self._start_background_refresh()
                
                return True
                
            except Exception as e:
                logger.error(f"交易日历初始化失败: {e}")
                self._memory_cache = self._generate_estimate_cache()
                self._sorted_list_cache = sorted(self._memory_cache)
                self._is_initialized = True
                return False
    
    async def _ensure_table_exists(self):
        """确保数据库表存在"""
        from app.storage.sqlite import init_database
        try:
            if sqlite_module.engine is None:
                await init_database()
            if sqlite_module.engine is None:
                logger.warning("数据库引擎初始化失败，跳过表创建")
                return
            async with sqlite_module.engine.begin() as conn:
                await conn.run_sync(TradingDay.__table__.create, checkfirst=True)
        except Exception as e:
            logger.warning(f"确保数据库表存在失败: {e}")
    
    async def _load_from_db(self) -> bool:
        """从数据库加载交易日数据"""
        try:
            async with get_session() as session:
                result = await session.execute(
                    select(TradingDay.date).where(TradingDay.is_trading_day == True)
                )
                dates = [row[0] for row in result.fetchall()]
                
                if dates:
                    # 统一转换为 YYYYMMDD 格式
                    normalized_dates = []
                    for date in dates:
                        try:
                            normalized = self._normalize_date_format(date)
                            normalized_dates.append(normalized)
                        except Exception as e:
                            logger.warning(f"日期格式转换失败：{date}, 错误：{e}")
                            # 如果转换失败，尝试直接替换短横线
                            normalized_dates.append(date.replace('-', ''))
                    
                    self._memory_cache = set(normalized_dates)
                    self._sorted_list_cache = sorted(normalized_dates)
                    self._cache_time = time.time()
                    logger.info(f"交易日历从数据库加载完成，共 {len(self._memory_cache)} 个交易日（已统一格式）")
                    return True
                return False
                
        except Exception as e:
            logger.warning(f"从数据库加载交易日失败: {e}")
            return False
    
    async def _save_to_db(self, trading_days: List[str]) -> bool:
        """保存交易日数据到数据库"""
        try:
            async with get_session() as session:
                await session.execute(delete(TradingDay))
                
                now = datetime.now()
                # 统一转换为 YYYYMMDD 格式
                records = []
                for date in trading_days:
                    try:
                        normalized = self._normalize_date_format(date)
                        records.append(TradingDay(date=normalized, is_trading_day=True, updated_at=now))
                    except Exception as e:
                        logger.warning(f"日期格式转换失败：{date}, 错误：{e}")
                        # 如果转换失败，尝试直接替换短横线
                        records.append(TradingDay(date=date.replace('-', ''), is_trading_day=True, updated_at=now))
                
                session.add_all(records)
                await session.commit()
                
                logger.info(f"交易日数据已保存到数据库，共 {len(records)} 条（已统一格式）")
                return True
                
        except Exception as e:
            logger.error(f"保存交易日到数据库失败: {e}")
            return False
    
    async def _fetch_and_save_from_remote(self) -> bool:
        """从远程 API 获取交易日数据并保存"""
        try:
            trading_days = await self._fetch_from_baostock()
            
            if not trading_days:
                trading_days = await self._fetch_from_akshare()
            
            if trading_days:
                await self._save_to_db(trading_days)
                self._memory_cache = set(trading_days)
                self._sorted_list_cache = sorted(trading_days)
                self._cache_time = time.time()
                self._last_refresh_time = time.time()
                logger.info(f"从远程获取交易日数据成功，共 {len(trading_days)} 天")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"从远程获取交易日失败: {e}")
            return False
    
    async def _fetch_from_baostock(self) -> Optional[List[str]]:
        """从 Baostock 获取交易日数据"""
        try:
            import baostock as bs
            
            def fetch_sync():
                try:
                    bs.login()
                    rs = bs.query_trade_dates()
                    bs.logout()
                    return rs
                except Exception as e:
                    logger.warning(f"Baostock 同步获取失败: {e}")
                    return None
            
            rs = await asyncio.wait_for(
                asyncio.to_thread(fetch_sync),
                timeout=self.API_TIMEOUT
            )
            
            if rs:
                import pandas as pd
                df = pd.DataFrame(rs.get_data())
                
                trading_days = []
                for row in df.itertuples(index=False):
                    if hasattr(row, 'is_trading_day') and row.is_trading_day == '1':
                        date = str(getattr(row, 'calendar_date', '')).replace('-', '')
                        if date and len(date) == 8:
                            trading_days.append(date)
                
                if trading_days:
                    logger.debug(f"Baostock 获取交易日成功: {len(trading_days)} 天")
                    return trading_days
                    
        except asyncio.TimeoutError:
            logger.warning("Baostock 获取超时")
        except Exception as e:
            logger.warning(f"Baostock 获取失败: {e}")
        
        return None
    
    async def _fetch_from_akshare(self) -> Optional[List[str]]:
        """从 AkShare 获取交易日数据"""
        try:
            import akshare as ak
            
            def fetch_sync():
                try:
                    df = ak.tool_trade_date_hist_sina()
                    return df['trade_date'].tolist()
                except Exception as e:
                    logger.warning(f"AkShare 同步获取失败: {e}")
                    return None
            
            dates = await asyncio.wait_for(
                asyncio.to_thread(fetch_sync),
                timeout=self.API_TIMEOUT
            )
            
            if dates:
                trading_days = [str(d).replace('-', '') for d in dates if d]
                logger.debug(f"AkShare 获取交易日成功: {len(trading_days)} 天")
                return trading_days
                
        except asyncio.TimeoutError:
            logger.warning("AkShare 获取超时")
        except Exception as e:
            logger.warning(f"AkShare 获取失败: {e}")
        
        return None
    
    def _generate_estimate_cache(self) -> Set[str]:
        """生成估算的交易日缓存（降级方案）"""
        trading_days = set()
        current = datetime(2020, 1, 1)
        end = datetime.now() + timedelta(days=365)
        
        while current <= end:
            if current.weekday() < 5:
                trading_days.add(current.strftime("%Y%m%d"))
            current += timedelta(days=1)
        
        logger.info(f"生成估算交易日数据: {len(trading_days)} 天")
        return trading_days
    
    def _start_background_refresh(self):
        """启动后台刷新任务"""
        if self._refresh_task is None or self._refresh_task.done():
            self._refresh_task = asyncio.create_task(self._background_refresh_loop())
            logger.debug("交易日历后台刷新任务已启动")
    
    async def _background_refresh_loop(self):
        """后台刷新循环"""
        while True:
            try:
                await asyncio.sleep(self.REFRESH_INTERVAL)
                
                if self._should_refresh():
                    logger.debug("开始后台刷新交易日数据...")
                    await self._fetch_and_save_from_remote()
                    
            except asyncio.CancelledError:
                logger.debug("交易日历后台刷新任务已取消")
                break
            except Exception as e:
                logger.error(f"后台刷新交易日失败: {e}")
    
    def _should_refresh(self) -> bool:
        """判断是否需要刷新数据"""
        if not self._memory_cache:
            return True
        
        if time.time() - self._last_refresh_time > self.CACHE_TTL:
            return True
        
        today = datetime.now().strftime("%Y%m%d")
        if today not in self._memory_cache:
            today_weekday = datetime.now().weekday()
            if today_weekday < 5:
                return True
        
        return False
    
    async def ensure_initialized(self):
        """确保服务已初始化"""
        if not self._is_initialized:
            await self.initialize()
    
    async def get_trading_days(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 60
    ) -> List[str]:
        """
        获取交易日列表
        
        Args:
            start_date: 开始日期，格式 YYYYMMDD 或 YYYY-MM-DD
            end_date: 结束日期，格式 YYYYMMDD 或 YYYY-MM-DD
            limit: 最多返回的交易日数量
        
        Returns:
            交易日列表（降序，从新到旧）
        """
        await self.ensure_initialized()
        
        if not self._sorted_list_cache:
            return self._estimate_trading_days(limit)
        
        if not end_date:
            end_date = datetime.now().strftime("%Y%m%d")
        else:
            end_date = self._normalize_date_format(end_date)
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=limit * 3)).strftime("%Y%m%d")
        else:
            start_date = self._normalize_date_format(start_date)
        
        result = []
        for date in reversed(self._sorted_list_cache):
            if start_date <= date <= end_date:
                result.append(date)
                if len(result) >= limit:
                    break
        
        return result
    
    async def get_latest_trading_day(self) -> str:
        """获取最新交易日"""
        await self.ensure_initialized()
        
        if self._sorted_list_cache:
            today = datetime.now().strftime("%Y%m%d")
            for date in reversed(self._sorted_list_cache):
                if date <= today:
                    return date
        
        return datetime.now().strftime("%Y%m%d")
    
    def _normalize_date_format(self, date: str) -> str:
        """统一日期格式为 YYYYMMDD"""
        if not date:
            return datetime.now().strftime("%Y%m%d")
        
        # 如果已经是 8 位数字，直接返回
        if len(date) == 8 and date.isdigit():
            return date
        
        # 如果是 ISO 格式（YYYY-MM-DD），转换为 YYYYMMDD
        try:
            return to_compact_date(date) or datetime.now().strftime("%Y%m%d")
        except Exception:
            # 如果转换失败，尝试直接替换短横线
            return date.replace('-', '')
    
    def _parse_date(self, date: str) -> datetime:
        """解析日期字符串为 datetime 对象（支持多种格式）"""
        normalized = self._normalize_date_format(date)
        try:
            return datetime.strptime(normalized, "%Y%m%d")
        except ValueError as e:
            logger.warning(f"日期解析失败：{date}, 错误：{e}")
            return datetime.now()
    
    async def get_previous_trading_day(self, date: str) -> str:
        """获取前一个交易日"""
        await self.ensure_initialized()
        
        # 统一日期格式
        normalized_date = self._normalize_date_format(date)
        
        if self._sorted_list_cache:
            try:
                idx = self._sorted_list_cache.index(normalized_date)
                if idx > 0:
                    return self._sorted_list_cache[idx - 1]
            except ValueError:
                pass
        
        dt = self._parse_date(normalized_date)
        while True:
            dt -= timedelta(days=1)
            if dt.weekday() < 5:
                return dt.strftime("%Y%m%d")
    
    async def is_trading_day(self, date: Optional[str] = None) -> bool:
        """判断是否是交易日"""
        await self.ensure_initialized()
        
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        # 统一日期格式
        normalized_date = self._normalize_date_format(date)
        
        if self._memory_cache:
            return normalized_date in self._memory_cache
        
        dt = self._parse_date(normalized_date)
        return dt.weekday() < 5
    
    async def is_market_open(self) -> bool:
        """判断当前是否已开盘"""
        now = datetime.now()
        
        if now.weekday() >= 5:
            return False
        
        today = now.strftime("%Y%m%d")
        if not await self.is_trading_day(today):
            return False
        
        market_open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
        if now < market_open_time:
            return False
        
        return True
    
    async def get_effective_date(self) -> Dict[str, Any]:
        """获取有效日期"""
        await self.ensure_initialized()
        
        now = datetime.now()
        today = now.strftime("%Y%m%d")
        
        try:
            latest_trading_day = await self.get_latest_trading_day()
            previous_trading_day = await self.get_previous_trading_day(latest_trading_day)
            is_open = self._is_market_open_simple(now, today, latest_trading_day)
            
            return {
                "effective_date": latest_trading_day,
                "is_today": latest_trading_day == today,
                "is_market_open": is_open,
                "latest_trading_day": latest_trading_day,
                "previous_trading_day": previous_trading_day,
                "current_time": now.strftime("%H:%M:%S")
            }
        except Exception as e:
            logger.error(f"获取有效日期失败: {e}")
            return {
                "effective_date": today,
                "is_today": True,
                "is_market_open": False,
                "latest_trading_day": today,
                "previous_trading_day": self._estimate_previous_day(today),
                "current_time": now.strftime("%H:%M:%S")
            }
    
    async def get_recent_trading_days(self, limit: int = 10) -> List[Dict[str, Any]]:
        """获取最近 N 个交易日的详细信息"""
        await self.ensure_initialized()
        
        trading_days = await self.get_trading_days(limit=limit)
        today = datetime.now().strftime("%Y%m%d")
        latest = trading_days[0] if trading_days else today
        
        result = []
        for i, date in enumerate(trading_days):
            result.append({
                "date": date,
                "display": self._format_date_display(date),
                "is_today": date == today,
                "is_latest": date == latest,
                "is_selected": i == 0
            })
        
        return result
    
    def _is_market_open_simple(self, now: datetime, today: str, latest_trading_day: str) -> bool:
        """简化版开盘判断"""
        if now.weekday() >= 5:
            return False
        
        if today != latest_trading_day:
            return False
        
        market_open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
        return now >= market_open_time
    
    def _estimate_trading_days(self, limit: int = 60) -> List[str]:
        """估算交易日"""
        trading_days = []
        current = datetime.now()
        
        while len(trading_days) < limit:
            if current.weekday() < 5:
                trading_days.append(current.strftime("%Y%m%d"))
            current -= timedelta(days=1)
        
        return trading_days
    
    def _estimate_previous_day(self, date: str) -> str:
        """估算前一个交易日"""
        # 统一日期格式
        normalized_date = self._normalize_date_format(date)
        dt = self._parse_date(normalized_date)
        while True:
            dt -= timedelta(days=1)
            if dt.weekday() < 5:
                return dt.strftime("%Y%m%d")
    
    def _format_date_display(self, date: str) -> str:
        """格式化日期显示"""
        try:
            # 统一日期格式
            normalized_date = self._normalize_date_format(date)
            dt = self._parse_date(normalized_date)
            return f"{dt.month}月{dt.day}日"
        except Exception:
            return date
    
    async def force_refresh(self) -> bool:
        """强制刷新交易日数据"""
        logger.info("强制刷新交易日数据...")
        return await self._fetch_and_save_from_remote()
    
    def get_cache_status(self) -> Dict[str, Any]:
        """获取缓存状态"""
        return {
            "is_initialized": self._is_initialized,
            "cache_count": len(self._memory_cache) if self._memory_cache else 0,
            "cache_time": datetime.fromtimestamp(self._cache_time).isoformat() if self._cache_time else None,
            "last_refresh_time": datetime.fromtimestamp(self._last_refresh_time).isoformat() if self._last_refresh_time else None,
            "should_refresh": self._should_refresh(),
        }


trading_calendar = TradingCalendarService()
