"""
交易日历服务
提供交易日查询、最新交易日判断、开盘状态检测等功能
"""
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from loguru import logger
import akshare as ak
import time
import json
import os


class TradingCalendarService:
    """交易日历服务"""
    
    def __init__(self):
        self._cache: Dict[str, Any] = {}
        self._cache_timeout = 3600  # 缓存 1 小时
        self._all_trading_days_cache: Optional[List[str]] = None
        self._all_trading_days_cache_time: float = 0
        self._all_trading_days_cache_ttl = 86400  # 24 小时缓存
        self._local_cache_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "trading_days_cache.json")
    
    def _load_from_local_cache(self) -> Optional[List[str]]:
        """从本地文件加载交易日历"""
        try:
            if os.path.exists(self._local_cache_file):
                with open(self._local_cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'trading_days' in data and 'timestamp' in data:
                        # 检查是否过期（24 小时）
                        if datetime.now().timestamp() - data['timestamp'] < 86400:
                            return data['trading_days']
        except Exception as e:
            logger.warning(f"读取本地缓存失败：{e}")
        return None
    
    def _save_to_local_cache(self, trading_days: List[str]):
        """保存到本地文件"""
        try:
            os.makedirs(os.path.dirname(self._local_cache_file), exist_ok=True)
            with open(self._local_cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'trading_days': trading_days,
                    'timestamp': datetime.now().timestamp()
                }, f, ensure_ascii=False)
            logger.debug(f"交易日历已保存到本地：{self._local_cache_file}")
        except Exception as e:
            logger.warning(f"保存本地缓存失败：{e}")
    
    async def _get_all_trading_days(self) -> List[str]:
        """
        获取所有交易日（缓存）
        
        Returns:
            所有交易日列表
        """
        # 检查内存缓存
        if (self._all_trading_days_cache and 
            datetime.now().timestamp() - self._all_trading_days_cache_time < self._all_trading_days_cache_ttl):
            return self._all_trading_days_cache
        
        # 检查本地文件缓存
        local_cache = self._load_from_local_cache()
        if local_cache:
            logger.debug("从本地文件缓存加载交易日历")
            self._all_trading_days_cache = local_cache
            self._all_trading_days_cache_time = datetime.now().timestamp()
            return local_cache
        
        try:
            start_time = time.time()
            
            # 优先使用 Baostock（更快）
            try:
                import baostock as bs
                bs.login()
                df = bs.query_trade_dates()
                bs.logout()
                
                trading_days = []
                for _, row in df.iterrows():
                    if row['is_trading_day'] == '1':
                        date = row['calendar_date'].replace('-', '')
                        trading_days.append(date)
                
                if trading_days:
                    # 缓存
                    self._all_trading_days_cache = trading_days
                    self._all_trading_days_cache_time = time.time()
                    self._save_to_local_cache(trading_days)
                    logger.debug(f"从 Baostock 获取交易日数据耗时：{time.time() - start_time:.2f}秒，共{len(trading_days)}天")
                    return trading_days
            except Exception as bs_error:
                logger.warning(f"Baostock 获取失败，切换到 AkShare: {bs_error}")
            
            # 使用 AkShare
            df = ak.tool_trade_date_hist_sina()
            
            # 转换为列表
            trading_days = []
            for _, row in df.iterrows():
                date = str(row['trade_date']).replace('-', '')
                trading_days.append(date)
            
            # 缓存
            self._all_trading_days_cache = trading_days
            self._all_trading_days_cache_time = time.time()
            self._save_to_local_cache(trading_days)
            
            logger.debug(f"从 AkShare 获取交易日数据耗时：{time.time() - start_time:.2f}秒，共{len(trading_days)}天")
            
            return trading_days
            
        except Exception as e:
            logger.error(f"获取交易日失败：{e}")
            # 返回空列表，使用估算
            return []
    
    async def get_trading_days(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 60
    ) -> List[str]:
        """
        获取交易日列表
        
        Args:
            start_date: 开始日期，格式 YYYYMMDD，默认 60 天前
            end_date: 结束日期，格式 YYYYMMDD，默认今天
            limit: 最多返回的交易日数量
        
        Returns:
            交易日列表，格式 ['20260311', '20260310', ...]（降序）
        """
        # 优先使用缓存的完整数据
        try:
            all_days = await self._get_all_trading_days()
            
            if not all_days:
                # 如果获取失败，使用估算
                return self._estimate_trading_days(limit)
            
            # 计算日期范围
            if not end_date:
                end_date = datetime.now().strftime("%Y%m%d")
            
            if not start_date:
                start_date = (datetime.now() - timedelta(days=limit*2)).strftime("%Y%m%d")
            
            # 筛选日期范围（从新到旧）
            trading_days = []
            # 倒序遍历，获取最新的交易日
            for date in reversed(all_days):
                if start_date <= date <= end_date:
                    trading_days.append(date)
                if len(trading_days) >= limit:
                    break
            
            # 倒序已经是降序的（从新到旧）
            return trading_days
            
        except Exception as e:
            logger.error(f"获取交易日失败：{e}")
            return self._estimate_trading_days(limit)
    
    def _estimate_trading_days(self, limit: int = 60) -> List[str]:
        """估算交易日（当无法获取真实数据时使用）"""
        trading_days = []
        current = datetime.now()
        
        while len(trading_days) < limit:
            # 排除周末
            if current.weekday() < 5:
                trading_days.append(current.strftime("%Y%m%d"))
            current -= timedelta(days=1)
        
        return trading_days
    
    async def get_latest_trading_day(self) -> str:
        """
        获取最新交易日
        
        Returns:
            最新交易日，格式 YYYYMMDD
        """
        trading_days = await self.get_trading_days(limit=1)
        return trading_days[0] if trading_days else datetime.now().strftime("%Y%m%d")
    
    async def get_previous_trading_day(self, date: str) -> str:
        """
        获取前一个交易日
        
        Args:
            date: 日期，格式 YYYYMMDD
        
        Returns:
            前一个交易日
        """
        trading_days = await self.get_trading_days(end_date=date, limit=2)
        return trading_days[1] if len(trading_days) > 1 else trading_days[0] if trading_days else date
    
    async def is_market_open(self) -> bool:
        """
        判断当前是否已开盘
        
        判断逻辑：
        1. 必须是交易日
        2. 当前时间在开盘时间之后（9:30）
        
        Returns:
            True 表示已开盘，False 表示未开盘
        """
        now = datetime.now()
        
        # 检查是否是周末
        if now.weekday() >= 5:
            return False
        
        # 检查是否是交易日
        today = now.strftime("%Y%m%d")
        trading_days = await self.get_trading_days(limit=1)
        if not trading_days or trading_days[0] != today:
            return False
        
        # 检查时间（A 股开盘时间 9:30）
        market_open_time = now.replace(hour=9, minute=30, second=0, microsecond=0)
        if now < market_open_time:
            return False
        
        return True
    
    async def get_effective_date(self) -> Dict[str, Any]:
        """
        获取有效日期（智能判断应该显示哪天的数据）
        
        逻辑：
        - 如果已开盘：显示今天
        - 如果未开盘：显示前一个交易日
        
        Returns:
            {
                "effective_date": "20260311",  # 应该显示的日期
                "is_today": True,              # 是否是今天
                "is_market_open": False,       # 是否已开盘
                "latest_trading_day": "20260311",  # 最新交易日
                "previous_trading_day": "20260310"  # 前一个交易日
            }
        """
        now = datetime.now()
        today = now.strftime("%Y%m%d")
        
        # 获取最新交易日
        latest_trading_day = await self.get_latest_trading_day()
        
        # 判断是否已开盘
        is_open = await self.is_market_open()
        
        # 获取前一个交易日
        previous_trading_day = await self.get_previous_trading_day(latest_trading_day)
        
        # 确定有效日期
        if is_open:
            effective_date = latest_trading_day
        else:
            effective_date = previous_trading_day
        
        return {
            "effective_date": effective_date,
            "is_today": effective_date == today,
            "is_market_open": is_open,
            "latest_trading_day": latest_trading_day,
            "previous_trading_day": previous_trading_day,
            "current_time": now.strftime("%H:%M:%S")
        }
    
    async def get_recent_trading_days(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取最近 N 个交易日的详细信息
        
        Returns:
            [
                {
                    "date": "20260311",
                    "display": "3 月 11 日",
                    "is_today": True,
                    "is_latest": True
                },
                ...
            ]
        """
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
    
    def _format_date_display(self, date: str) -> str:
        """格式化日期显示"""
        try:
            dt = datetime.strptime(date, "%Y%m%d")
            return f"{dt.month}月{dt.day}日"
        except:
            return date


# 全局实例
trading_calendar = TradingCalendarService()
