"""
市场成交额数据持久化服务

提供历史成交额的存储和查询功能
"""
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
from datetime import datetime
import asyncio
import random
import time
import akshare as ak
from loguru import logger

from app.storage.sqlite import MarketTurnover, get_session


class MarketTurnoverService:
    """市场成交额服务（带反风控策略）"""
    
    def __init__(self):
        # 反风控设置
        self._request_delay_range = (2.0, 4.0)  # 请求间隔（秒）
        self._retry_base_delay = 3.0  # 增加基础延迟到 3 秒
        self._max_retries = 2  # 减少重试次数到 2 次
        self._consecutive_failures = 0  # 连续失败次数
        self._adaptive_delay_enabled = True  # 启用自适应延迟
        
        # 限流检测
        self._rate_limit_detected = False
        self._rate_limit_count = 0
        self._last_rate_limit_time = 0
        
        # User-Agent 轮换池
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        ]
        self._current_user_agent = self._user_agents[0]
    
    def _get_time_based_delay(self) -> tuple:
        """根据当前时间段获取合适的延迟范围"""
        current_hour = datetime.now().hour
        
        # 交易时段（9:30-11:30, 13:00-15:00）使用较长延迟
        if (9 <= current_hour <= 11) or (13 <= current_hour <= 14):
            return (4.0, 7.0)  # 增加延迟
        # 非交易时段使用较短延迟
        else:
            return (3.0, 5.0)  # 增加延迟
    
    async def _rate_limit(self):
        """异步请求限流"""
        if self._adaptive_delay_enabled:
            min_delay, max_delay = self._get_time_based_delay()
            
            # 如果检测到限流，大幅增加延迟
            if self._rate_limit_detected:
                min_delay *= 3
                max_delay *= 3
                logger.warning(f"检测到限流，使用 3 倍延迟：{min_delay:.1f}-{max_delay:.1f}秒")
            
            # 根据连续失败次数增加额外延迟
            if self._consecutive_failures > 0:
                extra_delay = min(self._consecutive_failures * 2, 10)
                min_delay += extra_delay
                max_delay += extra_delay
            
            delay = random.uniform(min_delay, max_delay)
        else:
            delay = random.uniform(*self._request_delay_range)
        
        logger.debug(f"成交额服务请求限流：延迟 {delay:.2f}秒")
        await asyncio.sleep(delay)
    
    def _detect_rate_limit(self, error: Exception) -> bool:
        """检测是否被限流"""
        error_msg = str(error).lower()
        rate_limit_keywords = [
            'connection aborted',
            'remote end closed',
            'too many requests',
            'rate limit',
            'frequency limit',
            'access denied',
            'ip blocked',
            'request rejected'
        ]
        
        is_rate_limit = any(keyword in error_msg for keyword in rate_limit_keywords)
        
        if is_rate_limit:
            current_time = time.time()
            # 5 分钟内多次限流才确认
            if current_time - self._last_rate_limit_time < 300:
                self._rate_limit_count += 1
                if self._rate_limit_count >= 2:
                    self._rate_limit_detected = True
                    logger.warning(f"确认被限流！5 分钟内{self._rate_limit_count}次触发")
            else:
                self._rate_limit_count = 1
                self._last_rate_limit_time = current_time
        
        return is_rate_limit
    
    def _rotate_user_agent(self):
        """轮换 User-Agent"""
        old_ua = self._current_user_agent
        self._current_user_agent = random.choice(self._user_agents)
        logger.debug(f"User-Agent 已轮换：{old_ua[:50]}... -> {self._current_user_agent[:50]}...")
    
    def reset_rate_limit_status(self):
        """重置限流状态（在成功请求后调用）"""
        if self._rate_limit_detected:
            self._rate_limit_detected = False
            self._rate_limit_count = 0
            self._last_rate_limit_time = 0
            logger.info("成交额服务限流状态已重置")
    
    async def _fetch_with_anti_wind(self, fetch_func, *args, **kwargs):
        """带反风控的请求封装"""
        for attempt in range(self._max_retries):
            try:
                # 请求前限流
                await self._rate_limit()
                
                # 执行请求
                result = await asyncio.get_event_loop().run_in_executor(None, fetch_func, *args, **kwargs)
                
                # 成功后重置失败计数
                self._consecutive_failures = 0
                self.reset_rate_limit_status()
                
                return result
                
            except Exception as e:
                self._consecutive_failures += 1
                
                # 检测是否被限流
                if self._detect_rate_limit(e):
                    self._rotate_user_agent()
                
                if attempt < self._max_retries - 1:
                    # 指数退避 + 限流惩罚
                    base_delay = (2 ** attempt) * self._retry_base_delay
                    if self._rate_limit_detected:
                        base_delay *= 2  # 限流时延迟翻倍
                    
                    delay = base_delay + random.uniform(0, 1)
                    logger.warning(f"成交额数据获取失败，{delay:.1f}秒后重试（{attempt+1}/{self._max_retries}）: {e}")
                    await asyncio.sleep(delay)
                else:
                    logger.error(f"成交额数据获取失败，已达最大重试次数：{e}")
                    raise
        
        return None
    
    @staticmethod
    async def save_turnover_data(
        session: AsyncSession,
        trade_date: str,
        sh_turnover: float,
        sz_turnover: float,
        total_turnover: float,
        stock_count: int = 0
    ) -> bool:
        try:
            result = await session.execute(
                select(MarketTurnover).where(MarketTurnover.trade_date == trade_date)
            )
            existing = result.scalar_one_or_none()
            
            if existing:
                existing.sh_turnover = sh_turnover
                existing.sz_turnover = sz_turnover
                existing.total_turnover = total_turnover
                existing.stock_count = stock_count
                existing.updated_at = datetime.now()
                logger.info(f"更新成交额数据：{trade_date}")
            else:
                new_record = MarketTurnover(
                    trade_date=trade_date,
                    sh_turnover=sh_turnover,
                    sz_turnover=sz_turnover,
                    total_turnover=total_turnover,
                    stock_count=stock_count
                )
                session.add(new_record)
                logger.info(f"保存成交额数据：{trade_date}")
            
            await session.commit()
            return True
            
        except Exception as e:
            logger.error(f"保存成交额数据失败：{e}")
            await session.rollback()
            return False
    
    @staticmethod
    async def get_turnover_data(
        session: AsyncSession,
        trade_date: str
    ) -> Optional[Dict[str, Any]]:
        try:
            result = await session.execute(
                select(MarketTurnover).where(MarketTurnover.trade_date == trade_date)
            )
            record = result.scalar_one_or_none()
            
            if record:
                return {
                    'trade_date': record.trade_date,
                    'sh_turnover': record.sh_turnover,
                    'sz_turnover': record.sz_turnover,
                    'total_turnover': record.total_turnover,
                    'stock_count': record.stock_count
                }
            return None
            
        except Exception as e:
            logger.error(f"获取成交额数据失败：{e}")
            return None
    
    @staticmethod
    async def get_latest_turnover(session: AsyncSession) -> Optional[Dict[str, Any]]:
        try:
            result = await session.execute(
                select(MarketTurnover).order_by(MarketTurnover.trade_date.desc()).limit(1)
            )
            record = result.scalar_one_or_none()
            
            if record:
                return {
                    'trade_date': record.trade_date,
                    'sh_turnover': record.sh_turnover,
                    'sz_turnover': record.sz_turnover,
                    'total_turnover': record.total_turnover,
                    'stock_count': record.stock_count
                }
            return None
            
        except Exception as e:
            logger.error(f"获取最新成交额数据失败：{e}")
            return None
    
    async def fetch_and_save_latest(self, session: AsyncSession) -> Optional[Dict[str, Any]]:
        """获取并保存最新成交额数据（带反风控策略）"""
        try:
            from app.services.trading_calendar import trading_calendar
            from app.adapters.factory import DataSourceFactory
            
            trade_date = await trading_calendar.get_latest_trading_day()
            
            existing = await MarketTurnoverService.get_turnover_data(session, trade_date)
            if existing:
                logger.info(f"数据库已有 {trade_date} 成交额数据")
                return existing
            
            # 确保凭证注入和 TLS 指纹伪装已启用
            logger.info("正在确保 akshare 凭证注入和 TLS 指纹伪装...")
            akshare_adapter = DataSourceFactory.get_adapter('akshare')
            await akshare_adapter._ensure_credentials()
            
            logger.info(f"从 akshare 获取 {trade_date} 成交额数据（带反风控）...")
            
            # 使用反风控封装获取沪市数据
            df_sh = await self._fetch_with_anti_wind(ak.stock_sh_a_spot_em)
            if df_sh is None:
                logger.error("获取沪市成交额数据失败")
                return None
            
            # 再次限流后获取深市数据
            df_sz = await self._fetch_with_anti_wind(ak.stock_sz_a_spot_em)
            if df_sz is None:
                logger.error("获取深市成交额数据失败")
                return None
            
            sh_turnover = df_sh['成交额'].sum()
            sz_turnover = df_sz['成交额'].sum()
            total_turnover = sh_turnover + sz_turnover
            stock_count = len(df_sh) + len(df_sz)
            
            logger.info(f"沪市：{sh_turnover/100000000:.2f}亿，深市：{sz_turnover/100000000:.2f}亿")
            
            success = await MarketTurnoverService.save_turnover_data(
                session, trade_date, sh_turnover, sz_turnover, total_turnover, stock_count
            )
            
            if success:
                logger.info(f"✅ 保存 {trade_date} 成交额数据成功")
                return {
                    'trade_date': trade_date,
                    'sh_turnover': sh_turnover,
                    'sz_turnover': sz_turnover,
                    'total_turnover': total_turnover,
                    'stock_count': stock_count
                }
            else:
                logger.error(f"保存 {trade_date} 成交额数据失败")
                return None
                
        except Exception as e:
            logger.error(f"获取并保存成交额数据失败：{e}")
            return None


market_turnover_service = MarketTurnoverService()
