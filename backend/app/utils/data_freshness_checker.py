"""
数据时效性检查工具

提供统一的数据时效性检查机制，根据不同数据类型的更新频率要求，
智能判断是否需要从数据源重新获取数据。

支持交易时段/非交易时段的智能判断。
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
import json


class MarketSession:
    """交易时段常量"""
    # 早盘：9:30-11:30
    MORNING_START = (9, 30)
    MORNING_END = (11, 30)
    
    # 午盘：13:00-15:00
    AFTERNOON_START = (13, 0)
    AFTERNOON_END = (15, 0)
    
    @classmethod
    def is_trading_time(cls, dt: Optional[datetime] = None) -> bool:
        """判断当前是否在交易时段内"""
        if dt is None:
            dt = datetime.now()
        
        hour, minute = dt.hour, dt.minute
        current_time = hour * 60 + minute
        
        morning_start = cls.MORNING_START[0] * 60 + cls.MORNING_START[1]
        morning_end = cls.MORNING_END[0] * 60 + cls.MORNING_END[1]
        afternoon_start = cls.AFTERNOON_START[0] * 60 + cls.AFTERNOON_START[1]
        afternoon_end = cls.AFTERNOON_END[0] * 60 + cls.AFTERNOON_END[1]
        
        return (morning_start <= current_time <= morning_end or 
                afternoon_start <= current_time <= afternoon_end)
    
    @classmethod
    def is_market_closed(cls, dt: Optional[datetime] = None) -> bool:
        """判断当前是否已收盘"""
        if dt is None:
            dt = datetime.now()
        
        hour, minute = dt.hour, dt.minute
        current_time = hour * 60 + minute
        
        afternoon_end = cls.AFTERNOON_END[0] * 60 + cls.AFTERNOON_END[1]
        
        return current_time > afternoon_end


class DataFreshnessPolicy:
    """数据时效性策略配置"""
    
    # 不同数据类型的最大允许年龄（小时）
    # 说明：A 股交易日数据在收盘后（15:00）开始计算时效性
    # 日频数据应该在下一个交易日收盘前有效
    POLICIES = {
        # 高频数据（交易时段内实时变化）
        # 交易时段：15 分钟有效期（数据变化快）
        # 非交易时段：使用最新数据
        'realtime_quote': 0.25,     # 实时行情 - 15 分钟（交易时段）
        'tick_data': 0.25,          # 分时数据 - 15 分钟（交易时段）
        
        # 日频数据（每个交易日更新）
        # 交易时段：30 分钟有效期
        # 非交易时段/已收盘：使用最新数据
        'kline_daily': 0.5,         # 日 K 线 - 30 分钟（交易时段）
        'market_turnover': 0.25,    # 市场成交额 - 15 分钟（交易时段）
        'moneyflow': 0.25,          # 资金流向 - 15 分钟（交易时段）
        'billboard': 0.5,           # 龙虎榜 - 30 分钟（交易时段，盘后公布）
        
        # 周频数据（每周更新）
        'kline_weekly': 168,        # 周 K 线 - 7 天
        
        # 月频数据（每月更新）
        'kline_monthly': 720,       # 月 K 线 - 30 天
        
        # 低频数据（季度/年度更新）
        'financial_report': 2160,   # 财报 - 90 天
        'stock_info': 720,          # 股票基本信息 - 30 天
        
        # 静态数据（很少变化）
        'stock_list': 2160,         # 股票列表 - 90 天
        'sector_info': 2160,        # 板块信息 - 90 天
    }
    
    # 数据类型分类
    # 用于智能判断时区分不同特性的数据
    DATA_CATEGORIES = {
        # 实时数据：交易时段内频繁变化
        'REALTIME': ['realtime_quote', 'tick_data'],
        
        # 日频数据：每个交易日更新一次
        'DAILY': ['kline_daily', 'market_turnover', 'moneyflow', 'billboard'],
        
        # 周频数据：每周更新一次
        'WEEKLY': ['kline_weekly'],
        
        # 月频数据：每月更新一次
        'MONTHLY': ['kline_monthly'],
        
        # 低频数据：季度/年度更新
        'LOW_FREQ': ['financial_report', 'stock_info'],
        
        # 静态数据：很少变化
        'STATIC': ['stock_list', 'sector_info'],
    }
    
    # 默认策略（未知数据类型）
    DEFAULT_MAX_AGE_HOURS = 24
    
    @classmethod
    def get_max_age(cls, data_type: str) -> float:
        """获取指定数据类型的最大允许年龄（小时）"""
        return cls.POLICIES.get(data_type, cls.DEFAULT_MAX_AGE_HOURS)
    
    @classmethod
    def get_category(cls, data_type: str) -> str:
        """获取数据类型所属分类"""
        for category, types in cls.DATA_CATEGORIES.items():
            if data_type in types:
                return category
        return 'UNKNOWN'
    
    @classmethod
    def get_all_policies(cls) -> Dict[str, Any]:
        """获取所有策略配置"""
        return {
            'policies': cls.POLICIES,
            'categories': cls.DATA_CATEGORIES,
            'default': cls.DEFAULT_MAX_AGE_HOURS,
        }


class DataFreshnessChecker:
    """数据时效性检查器"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self._trading_calendar = None
    
    async def _get_trading_calendar(self):
        """懒加载交易日历服务"""
        if self._trading_calendar is None:
            try:
                from app.services.trading_calendar import trading_calendar
                await trading_calendar.ensure_initialized()
                self._trading_calendar = trading_calendar
            except Exception as e:
                logger.warning(f"加载交易日历服务失败：{e}")
                self._trading_calendar = None
        return self._trading_calendar
    
    def _is_trading_session(self, dt: Optional[datetime] = None) -> Tuple[bool, str]:
        """
        判断当前是否在交易时段
        
        Returns:
            (是否在交易时段，时段描述)
        """
        if dt is None:
            dt = datetime.now()
        
        # 判断是否是周末
        if dt.weekday() >= 5:
            return False, "非交易日（周末）"
        
        # 判断时间
        if MarketSession.is_trading_time(dt):
            return True, "交易时段"
        elif MarketSession.is_market_closed(dt):
            return False, "已收盘"
        else:
            return False, "未开盘"
    
    async def _is_today_trading_day(self) -> bool:
        """判断今天是否是交易日"""
        trading_calendar = await self._get_trading_calendar()
        if trading_calendar:
            try:
                return await trading_calendar.is_trading_day()
            except Exception:
                pass
        
        # 降级处理：简单判断（排除周末）
        return datetime.now().weekday() < 5
    
    async def check_freshness(
        self,
        table_class: Any,
        data_type: str,
        filter_conditions: Optional[Dict[str, Any]] = None,
        custom_max_age_hours: Optional[float] = None,
        enable_session_check: bool = True
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        检查数据时效性（支持交易时段判断）
        
        Args:
            table_class: SQLAlchemy 模型类
            data_type: 数据类型（用于查找策略）
            filter_conditions: 过滤条件（字典格式）
            custom_max_age_hours: 自定义最大年龄（小时），优先于策略配置
            enable_session_check: 是否启用交易时段检查
            
        Returns:
            (数据字典，是否需要更新)
            - 数据字典：最新的记录数据
            - 是否需要更新：True 表示需要获取新数据，False 表示可以使用缓存
        """
        try:
            # 获取最大允许年龄
            max_age_hours = custom_max_age_hours or DataFreshnessPolicy.get_max_age(data_type)
            
            # 构建查询
            query = select(table_class)
            
            # 应用过滤条件
            if filter_conditions:
                for key, value in filter_conditions.items():
                    if hasattr(table_class, key):
                        query = query.where(getattr(table_class, key) == value)
            
            # 按创建时间倒序，获取最新记录
            if hasattr(table_class, 'created_at'):
                query = query.order_by(table_class.created_at.desc())
            elif hasattr(table_class, 'updated_at'):
                query = query.order_by(table_class.updated_at.desc())
            else:
                # 如果没有时间字段，使用主键倒序
                primary_key = table_class.__table__.primary_key.columns.values()[0]
                query = query.order_by(primary_key.desc())
            
            query = query.limit(1)
            
            result = await self.session.execute(query)
            record = result.scalar_one_or_none()
            
            if not record:
                logger.info(f"数据不存在，需要获取：{data_type}")
                return None, True
            
            # 转换为字典
            data_dict = self._record_to_dict(record)
            
            # 检查时效性
            is_stale = True
            update_time = None
            
            # 优先使用 updated_at，其次使用 created_at
            if hasattr(record, 'updated_at') and record.updated_at:
                update_time = record.updated_at
            elif hasattr(record, 'created_at') and record.created_at:
                update_time = record.created_at
            
            if update_time:
                now = datetime.now()
                age_seconds = (now - update_time).total_seconds()
                age_hours = age_seconds / 3600
                
                # 智能判断：根据交易时段调整策略
                if enable_session_check and data_type in ['realtime_quote', 'tick_data', 'kline_daily', 'market_turnover', 'moneyflow', 'billboard']:
                    is_stale = await self._check_with_session_aware(
                        data_type, update_time, age_hours, max_age_hours
                    )
                else:
                    # 使用固定有效期判断
                    is_stale = age_hours > max_age_hours
                
                session_status, session_desc = self._is_trading_session()
                
                if is_stale:
                    logger.info(
                        f"数据已过期：{data_type}, "
                        f"age={age_hours:.2f}h > max={max_age_hours}h, "
                        f"session={session_desc}"
                    )
                else:
                    logger.debug(
                        f"数据有效：{data_type}, "
                        f"age={age_hours:.2f}h < max={max_age_hours}h, "
                        f"session={session_desc}"
                    )
            else:
                # 没有时间字段，保守起见认为需要更新
                logger.warning(f"数据无时间字段，认为已过期：{data_type}")
            
            # 添加时效性信息到返回数据
            data_dict['_freshness'] = {
                'is_stale': is_stale,
                'age_hours': age_hours if update_time else None,
                'max_age_hours': max_age_hours,
                'update_time': update_time.isoformat() if update_time else None,
                'session_status': self._is_trading_session()[0] if update_time else None,
            }
            
            return data_dict, is_stale
            
        except Exception as e:
            logger.error(f"检查数据时效性失败：{data_type}, error={e}")
            return None, True  # 出错时认为需要更新
    
    async def _check_with_session_aware(
        self,
        data_type: str,
        update_time: datetime,
        age_hours: float,
        base_max_age_hours: float
    ) -> bool:
        """
        根据交易时段和数据类型智能判断数据是否过期
        
        策略：
        1. 实时数据（REALTIME）：
           - 交易时段：严格检查，2 小时有效期
           - 非交易时段：使用最新数据
        
        2. 日频数据（DAILY）：
           - 交易时段：使用标准有效期
           - 已收盘：如果是今天数据，有效
           - 非交易日：使用最新交易日数据
        
        3. 周频数据（WEEKLY）：
           - 使用标准有效期（7 天）
           - 非交易日不强制更新
        
        4. 月频/低频数据（MONTHLY/LOW_FREQ）：
           - 使用标准有效期
           - 不启用智能判断
        
        5. 静态数据（STATIC）：
           - 不检查时效性
        """
        now = datetime.now()
        
        # 获取数据类型分类
        category = DataFreshnessPolicy.get_category(data_type)
        
        # 判断当前是否在交易时段
        is_trading_session, _ = self._is_trading_session()
        is_today_trading = await self._is_today_trading_day()
        
        # 判断数据是否是今天更新的
        update_date = update_time.strftime("%Y%m%d")
        today = now.strftime("%Y%m%d")
        is_today_update = update_date == today
        
        # 判断是否已收盘
        is_market_closed = MarketSession.is_market_closed(now)
        
        # 根据数据类型采用不同策略
        if category == 'REALTIME':
            # 实时数据：交易时段内频繁变化
            return self._check_realtime_data(
                is_trading_session, is_market_closed, is_today_update,
                age_hours, base_max_age_hours
            )
        
        elif category == 'DAILY':
            # 日频数据：每个交易日更新
            return self._check_daily_data(
                is_trading_session, is_market_closed, is_today_update,
                is_today_trading, age_hours, base_max_age_hours
            )
        
        elif category == 'WEEKLY':
            # 周频数据：每周更新
            return self._check_weekly_data(
                is_trading_session, is_today_trading,
                age_hours, base_max_age_hours
            )
        
        elif category in ['MONTHLY', 'LOW_FREQ', 'STATIC']:
            # 月频/低频/静态数据：使用标准判断
            logger.debug(f"{category} 数据：使用标准判断 age={age_hours:.2f}h")
            return age_hours > base_max_age_hours
        
        else:
            # 未知类型：使用标准判断
            return age_hours > base_max_age_hours
    
    def _check_realtime_data(
        self,
        is_trading_session: bool,
        is_market_closed: bool,
        is_today_update: bool,
        age_hours: float,
        base_max_age_hours: float
    ) -> bool:
        """
        实时数据判断策略
        
        - 交易时段：严格检查，2 小时有效期
        - 已收盘：如果是今天数据，有效
        - 非交易时段：使用最新数据
        """
        # 交易时段：严格检查
        if is_trading_session:
            logger.debug(f"实时数据 - 交易时段：age={age_hours:.2f}h, max={base_max_age_hours}h")
            return age_hours > base_max_age_hours
        
        # 已收盘：如果是今天数据，有效
        if is_market_closed and is_today_update:
            logger.debug(f"实时数据 - 已收盘 + 今天数据：有效")
            return False
        
        # 非交易时段：使用标准判断
        logger.debug(f"实时数据 - 非交易时段：age={age_hours:.2f}h")
        return age_hours > base_max_age_hours
    
    def _check_daily_data(
        self,
        is_trading_session: bool,
        is_market_closed: bool,
        is_today_update: bool,
        is_today_trading: bool,
        age_hours: float,
        base_max_age_hours: float
    ) -> bool:
        """
        日频数据判断策略
        
        - 交易时段：使用标准有效期
        - 已收盘：如果是今天数据，有效
        - 非交易日：使用最新交易日数据
        """
        # 交易时段：使用标准有效期
        if is_trading_session:
            logger.debug(f"日频数据 - 交易时段：age={age_hours:.2f}h, max={base_max_age_hours}h")
            return age_hours > base_max_age_hours
        
        # 已收盘：如果是今天数据，有效
        if is_market_closed and is_today_update:
            logger.debug(f"日频数据 - 已收盘 + 今天数据：有效")
            return False
        
        # 非交易日：使用标准判断（考虑周末）
        if not is_today_trading:
            # 如果是周五数据，在周末有效
            update_weekday = update_time.weekday()
            current_weekday = datetime.now().weekday()
            
            if current_weekday >= 5 and update_weekday == 4:
                # 周末 + 周五数据
                logger.debug(f"日频数据 - 周末 + 周五数据：有效")
                return False
            
            # 其他非交易日情况，使用标准判断
            logger.debug(f"日频数据 - 非交易日：age={age_hours:.2f}h")
            return age_hours > base_max_age_hours
        
        # 交易日但非交易时段（未开盘或已收盘）
        logger.debug(f"日频数据 - 交易日非交易时段：age={age_hours:.2f}h")
        return age_hours > base_max_age_hours
    
    def _check_weekly_data(
        self,
        is_trading_session: bool,
        is_today_trading: bool,
        age_hours: float,
        base_max_age_hours: float
    ) -> bool:
        """
        周频数据判断策略
        
        - 使用标准有效期（7 天）
        - 非交易日不强制更新
        """
        # 周频数据：使用标准判断
        logger.debug(f"周频数据：age={age_hours:.2f}h, max={base_max_age_hours}h")
        return age_hours > base_max_age_hours
    
    async def check_freshness_by_date(
        self,
        table_class: Any,
        data_type: str,
        date_field: str,
        target_date: str,
        custom_max_age_hours: Optional[float] = None
    ) -> Tuple[Optional[Dict[str, Any]], bool]:
        """
        按日期检查数据时效性（适用于按日期分区的数据）
        
        Args:
            table_class: SQLAlchemy 模型类
            data_type: 数据类型
            date_field: 日期字段名
            target_date: 目标日期（YYYYMMDD 格式）
            custom_max_age_hours: 自定义最大年龄（小时）
            
        Returns:
            (数据字典，是否需要更新)
        """
        try:
            # 获取最大允许年龄
            max_age_hours = custom_max_age_hours or DataFreshnessPolicy.get_max_age(data_type)
            
            # 查询指定日期的数据
            if not hasattr(table_class, date_field):
                logger.error(f"表 {table_class.__tablename__} 没有字段 {date_field}")
                return None, True
            
            query = select(table_class).where(
                getattr(table_class, date_field) == target_date
            )
            
            # 按更新时间倒序
            if hasattr(table_class, 'updated_at'):
                query = query.order_by(table_class.updated_at.desc())
            
            query = query.limit(1)
            
            result = await self.session.execute(query)
            record = result.scalar_one_or_none()
            
            if not record:
                logger.info(f"指定日期数据不存在：{data_type}, date={target_date}")
                return None, True
            
            # 转换为字典
            data_dict = self._record_to_dict(record)
            
            # 检查时效性
            is_stale = True
            update_time = None
            
            if hasattr(record, 'updated_at') and record.updated_at:
                update_time = record.updated_at
                age_seconds = (datetime.now() - update_time).total_seconds()
                age_hours = age_seconds / 3600
                is_stale = age_hours > max_age_hours
                
                logger.info(
                    f"数据检查：{data_type}, date={target_date}, "
                    f"age={age_hours:.2f}h, max={max_age_hours}h, stale={is_stale}"
                )
            else:
                age_hours = None
                logger.warning(f"数据无更新时间：{data_type}, date={target_date}")
            
            # 添加时效性信息
            data_dict['_freshness'] = {
                'is_stale': is_stale,
                'age_hours': age_hours,
                'max_age_hours': max_age_hours,
                'update_time': update_time.isoformat() if update_time else None,
                'target_date': target_date,
            }
            
            return data_dict, is_stale
            
        except Exception as e:
            logger.error(f"按日期检查数据时效性失败：{data_type}, date={target_date}, error={e}")
            return None, True
    
    def _record_to_dict(self, record: Any) -> Dict[str, Any]:
        """将 SQLAlchemy 记录转换为字典"""
        data = {}
        for column in record.__table__.columns:
            value = getattr(record, column.name)
            if isinstance(value, datetime):
                data[column.name] = value.isoformat()
            else:
                data[column.name] = value
        return data
    
    @staticmethod
    def get_policy_info() -> Dict[str, Any]:
        """获取策略配置信息"""
        return {
            'policies': DataFreshnessPolicy.POLICIES,
            'default': DataFreshnessPolicy.DEFAULT_MAX_AGE_HOURS,
            'descriptions': {
                'realtime_quote': '实时行情（30 分钟）',
                'tick_data': '分时数据（1 小时）',
                'kline_daily': '日 K 线（24 小时）',
                'market_turnover': '市场成交额（24 小时）',
                'moneyflow': '资金流向（24 小时）',
                'billboard': '龙虎榜（24 小时）',
                'kline_weekly': '周 K 线（7 天）',
                'kline_monthly': '月 K 线（30 天）',
                'financial_report': '财报（30 天）',
                'stock_info': '股票基本信息（30 天）',
                'stock_list': '股票列表（90 天）',
                'sector_info': '板块信息（90 天）',
            }
        }


# 便捷函数
async def check_data_freshness(
    session: AsyncSession,
    table_class: Any,
    data_type: str,
    filter_conditions: Optional[Dict[str, Any]] = None,
    max_age_hours: Optional[float] = None
) -> Tuple[Optional[Dict[str, Any]], bool]:
    """
    便捷函数：检查数据时效性
    
    Usage:
        data, is_stale = await check_data_freshness(
            session, StockInfo, 'stock_info', {'code': '000001'}
        )
        if is_stale:
            # 从数据源获取新数据
            pass
        else:
            # 使用缓存数据
            pass
    """
    checker = DataFreshnessChecker(session)
    return await checker.check_freshness(
        table_class, data_type, filter_conditions, max_age_hours
    )


# 装饰器：自动检查数据时效性
def auto_refresh_data(
    table_class: Any,
    data_type: str,
    max_age_hours: Optional[float] = None,
    refresh_func: Optional[str] = None
):
    """
    装饰器：自动检查数据时效性并在需要时刷新
    
    Args:
        table_class: SQLAlchemy 模型类
        data_type: 数据类型
        max_age_hours: 最大年龄（小时）
        refresh_func: 刷新函数名（默认是 get_{data_type}）
        
    Usage:
        @auto_refresh_data(StockInfo, 'stock_info')
        async def get_stock_info(code: str):
            # 自动检查时效性，过期时自动调用刷新函数
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # 获取 session（从参数或上下文）
            session = kwargs.get('session')
            if not session:
                # 尝试从 args 中获取
                for arg in args:
                    if isinstance(arg, AsyncSession):
                        session = arg
                        break
            
            if not session:
                logger.warning("无法获取 session，跳过时效性检查")
                return await func(*args, **kwargs)
            
            # 检查时效性
            checker = DataFreshnessChecker(session)
            filter_conditions = kwargs.get('filter_conditions', {})
            
            data, is_stale = await checker.check_freshness(
                table_class, data_type, filter_conditions, max_age_hours
            )
            
            if not is_stale and data:
                logger.debug(f"使用缓存数据：{data_type}")
                return data
            
            # 需要刷新，调用刷新函数
            refresh_name = refresh_func or f"get_{data_type}"
            logger.info(f"数据过期，调用刷新函数：{refresh_name}")
            
            # 尝试从当前模块或类中获取刷新函数
            refresh_func_obj = None
            if hasattr(func, '__self__'):
                # 是类方法
                instance = func.__self__
                if hasattr(instance, refresh_name):
                    refresh_func_obj = getattr(instance, refresh_name)
            
            if refresh_func_obj:
                new_data = await refresh_func_obj(*args, **kwargs)
                return new_data
            else:
                logger.warning(f"未找到刷新函数：{refresh_name}")
                return await func(*args, **kwargs)
        
        return wrapper
    return decorator
