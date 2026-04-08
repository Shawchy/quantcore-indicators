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
from app.adapters.anti_wind import AntiWindFacade


class MarketTurnoverService:
    """市场成交额服务（使用 AntiWindFacade 统一管理反风控策略）"""
    
    def __init__(self):
        # 使用 AntiWindFacade 统一管理反风控策略
        self.anti_wind = AntiWindFacade({
            'enable_cookie_inject': True,
            'enable_tls_fingerprint': True,
            'enable_rate_limit': True,
            'enable_ua_rotation': True,
            'enable_smart_retry': True,
            'max_retries': 3,
            'rate_limit_config': {
                'base_delay_range': (3.0, 5.0),  # 基础延迟
                'adaptive_delay_enabled': True,
            },
            'retry_config': {
                'max_retries': 3,
                'base_wait_seconds': 5.0,
            },
        })
        
        # 熔断器设置（保留，因为 AntiWindFacade 没有熔断器）
        self._circuit_breaker_enabled = False
        self._circuit_breaker_time = 0
        self._circuit_breaker_duration = 300
        
        # 凭证注入器（懒加载，向后兼容）
        self._credential_injector = None
        
        # 智能路由器（懒加载，向后兼容）
        self._smart_router = None
    
    def _get_time_based_delay(self) -> tuple:
        """根据当前时间段获取合适的延迟范围（保留用于参考）"""
        current_hour = datetime.now().hour
        
        # 交易时段（9:30-11:30, 13:00-15:00）使用较长延迟
        if (9 <= current_hour <= 11) or (13 <= current_hour <= 14):
            return (4.0, 7.0)  # 增加延迟
        # 非交易时段使用较短延迟
        else:
            return (3.0, 5.0)  # 增加延迟
    
    # 以下方法已废弃，由 AntiWindFacade 的 RateLimitStrategy 和 UARotatorStrategy 处理
    # async def _rate_limit(self):  # 已删除
    # def _detect_rate_limit(self, error):  # 已删除
    # def _rotate_user_agent(self):  # 已删除
    # def reset_rate_limit_status(self):  # 已删除
    
    async def _ensure_credential_injector(self) -> bool:
        """确保凭证注入器可用"""
        if self._credential_injector is None:
            try:
                from app.adapters.credential_injector import CredentialInjector
                self._credential_injector = CredentialInjector()
                logger.info("凭证注入器初始化成功")
                return True
            except Exception as e:
                logger.error(f"凭证注入器初始化失败：{e}")
                return False
        return True
    
    async def _ensure_smart_router(self) -> bool:
        """确保智能路由器可用"""
        if self._smart_router is None:
            try:
                from app.adapters.smart_router import SmartDataRouter
                self._smart_router = SmartDataRouter()
                await self._smart_router.initialize()
                logger.info("智能路由器初始化成功")
                return True
            except Exception as e:
                logger.error(f"智能路由器初始化失败：{e}")
                return False
        return True
    
    def _is_circuit_breaker_open(self) -> bool:
        """检查熔断器是否打开"""
        if not self._circuit_breaker_enabled:
            return False
        
        current_time = time.time()
        if current_time - self._circuit_breaker_time < self._circuit_breaker_duration:
            return True
        
        # 熔断器超时，关闭熔断器
        self._circuit_breaker_enabled = False
        logger.info("熔断器已关闭，恢复正常请求")
        return False
    
    def _open_circuit_breaker(self):
        """打开熔断器"""
        self._circuit_breaker_enabled = True
        self._circuit_breaker_time = time.time()
        logger.warning(f"熔断器已打开！暂停成交额数据获取 {self._circuit_breaker_duration}秒")
    
    async def _fetch_with_anti_wind(self, fetch_func, *args, use_credential=False, use_smart_router=False, **kwargs):
        """带反风控的请求封装（使用 AntiWindFacade 统一管理）"""
        # 检查熔断器（保留熔断器逻辑）
        if self._is_circuit_breaker_open():
            logger.warning("熔断器打开中，跳过成交额数据获取")
            raise Exception("熔断器保护中，暂不获取成交额数据")
        
        # 使用 AntiWindFacade 执行请求（自动处理所有反风控策略）
        try:
            result = await self.anti_wind.execute_with_strategies(
                request_func=fetch_func,
                args=args,
                kwargs=kwargs,
                context="market_turnover"
            )
            
            # 成功后重置熔断器
            if self._circuit_breaker_enabled:
                self._circuit_breaker_enabled = False
                logger.info("请求成功，熔断器已关闭")
            
            return result
            
        except Exception as e:
            # 连续失败检测（用于熔断器）
            # AntiWindFacade 会自动处理重试，这里只需要处理熔断器
            logger.error(f"成交额数据获取失败（已使用 AntiWindFacade）：{e}")
            raise
    
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
                    'stock_count': record.stock_count,
                    'updated_at': record.updated_at  # 返回更新时间
                }
            return None
            
        except Exception as e:
            logger.error(f"获取最新成交额数据失败：{e}")
            return None
    
    @staticmethod
    async def is_data_stale(
        session: AsyncSession,
        trade_date: str,
        max_age_hours: int = 24
    ) -> bool:
        """
        检查数据是否过期
        
        Args:
            session: 数据库会话
            trade_date: 交易日期
            max_age_hours: 最大允许的数据年龄（小时）
            
        Returns:
            True 表示数据已过期，需要更新；False 表示数据有效
        """
        try:
            # 获取指定交易日的数据
            result = await session.execute(
                select(MarketTurnover).where(MarketTurnover.trade_date == trade_date)
            )
            record = result.scalar_one_or_none()
            
            if not record:
                return True  # 数据不存在，需要获取
            
            # 检查数据更新时间
            if record.updated_at:
                age_hours = (datetime.now() - record.updated_at).total_seconds() / 3600
                if age_hours > max_age_hours:
                    logger.info(f"数据已过期 {age_hours:.1f} 小时 > {max_age_hours} 小时")
                    return True
                else:
                    logger.info(f"数据有效，已更新 {age_hours:.1f} 小时")
                    return False
            else:
                # 没有更新时间，保守起见认为需要更新
                return True
                
        except Exception as e:
            logger.error(f"检查数据时效性失败：{e}")
            return True  # 出错时认为需要更新
    
    @staticmethod
    async def get_turnover_with_freshness_check(
        session: AsyncSession,
        max_age_hours: int = 24
    ) -> tuple[Optional[Dict[str, Any]], bool]:
        """
        获取成交额数据并检查时效性
        
        Args:
            session: 数据库会话
            max_age_hours: 最大允许的数据年龄（小时）
            
        Returns:
            (数据字典，是否需要更新)
        """
        try:
            # 获取最新数据
            result = await session.execute(
                select(MarketTurnover).order_by(MarketTurnover.trade_date.desc()).limit(1)
            )
            record = result.scalar_one_or_none()
            
            if not record:
                return None, True  # 无数据，需要获取
            
            data = {
                'trade_date': record.trade_date,
                'sh_turnover': record.sh_turnover,
                'sz_turnover': record.sz_turnover,
                'total_turnover': record.total_turnover,
                'stock_count': record.stock_count,
                'updated_at': record.updated_at
            }
            
            # 检查数据是否过期
            is_stale = True
            if record.updated_at:
                age_hours = (datetime.now() - record.updated_at).total_seconds() / 3600
                is_stale = age_hours > max_age_hours
                
                logger.info(
                    f"成交额数据：trade_date={record.trade_date}, "
                    f"age={age_hours:.1f}h, stale={is_stale}"
                )
            
            return data, is_stale
            
        except Exception as e:
            logger.error(f"检查数据时效性失败：{e}")
            return None, True  # 出错时需要获取
    
    async def fetch_and_save_latest(self, session: AsyncSession) -> Optional[Dict[str, Any]]:
        """获取并保存最新成交额数据（带反风控策略）"""
        try:
            from app.services.trading_calendar import trading_calendar
            import asyncio
            
            trade_date = await trading_calendar.get_latest_trading_day()
            
            existing = await MarketTurnoverService.get_turnover_data(session, trade_date)
            if existing:
                logger.info(f"数据库已有 {trade_date} 成交额数据")
                return existing
            
            logger.info(f"从 akshare 获取 {trade_date} 成交额数据（带反风控，超时 180 秒）...")
            
            # 使用 asyncio.wait_for 添加超时保护
            try:
                result = await asyncio.wait_for(
                    self._fetch_turnover_data(trade_date),
                    timeout=180.0  # 180 秒超时（3 分钟，数据获取较慢）
                )
                
                if result:
                    sh_turnover, sz_turnover, total_turnover, stock_count = result
                    
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
                
                logger.error(f"获取 {trade_date} 成交额数据失败")
                return None
                
            except asyncio.TimeoutError:
                logger.error(f"获取成交额数据超时（15 秒），返回默认值")
                # 超时返回默认值，避免阻塞 UI
                return {
                    'trade_date': trade_date,
                    'sh_turnover': 0.0,
                    'sz_turnover': 0.0,
                    'total_turnover': 0.0,
                    'stock_count': 0
                }
                
        except Exception as e:
            logger.error(f"获取并保存成交额数据失败：{e}")
            return None
    
    async def _fetch_turnover_data(self, trade_date: str):
        """获取成交额数据（内部方法）"""
        import akshare as ak
        
        # 检查熔断器
        if self._is_circuit_breaker_open():
            logger.warning("熔断器打开中，跳过成交额数据获取")
            return None
        
        # 串行获取沪市和深市数据，确保反风控策略生效
        # 使用凭证注入和智能路由
        try:
            logger.info(f"获取沪市成交额数据（使用凭证注入 + 智能路由）...")
            # 启用凭证注入和智能路由
            df_sh = await self._fetch_with_anti_wind(
                ak.stock_sh_a_spot_em,
                use_credential=True,
                use_smart_router=True
            )
            
            if df_sh is None:
                logger.error("获取沪市成交额数据失败")
                return None
            
            # 获取深市数据前再次限流
            logger.info(f"获取深市成交额数据（使用凭证注入 + 智能路由）...")
            await self._rate_limit()
            df_sz = await self._fetch_with_anti_wind(
                ak.stock_sz_a_spot_em,
                use_credential=True,
                use_smart_router=True
            )
            
            if df_sz is None:
                logger.error("获取深市成交额数据失败")
                return None
            
            sh_turnover = df_sh['成交额'].sum()
            sz_turnover = df_sz['成交额'].sum()
            total_turnover = sh_turnover + sz_turnover
            stock_count = len(df_sh) + len(df_sz)
            
            logger.info(f"沪市：{sh_turnover/100000000:.2f}亿，深市：{sz_turnover/100000000:.2f}亿，总计：{total_turnover/100000000:.2f}亿")
            
            return (sh_turnover, sz_turnover, total_turnover, stock_count)
            
        except Exception as e:
            logger.error(f"获取成交额数据失败：{e}")
            return None


market_turnover_service = MarketTurnoverService()
