# -*- coding: utf-8 -*-
"""
数据重采样模块

支持 K 线数据的时间周期转换：
- 分钟线 → 小时线/日线
- 日线 → 周线/月线
- 自定义周期重采样
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
from ..core import Bar
from ..exceptions import DataException, InsufficientDataException


class Resampler:
    """数据重采样器"""
    
    def __init__(self, bars: List[Bar]):
        """
        初始化重采样器
        
        Args:
            bars: 原始 K 线数据列表
            
        Raises:
            InsufficientDataException: 数据为空时
        """
        if not bars:
            raise InsufficientDataException("K 线数据为空，无法重采样")
        
        self.bars = bars
        self.sorted_bars = sorted(bars, key=lambda x: self._parse_timestamp(x.timestamp))
    
    def resample(self, target_freq: str) -> List[Bar]:
        """
        重采样到目标频率
        
        Args:
            target_freq: 目标频率
                - '1min', '5min', '15min', '30min', '60min' (分钟线)
                - '1hour', '2hour', '4hour' (小时线)
                - '1day', '1week', '1month' (日/周/月线)
                
        Returns:
            重采样后的 K 线列表
            
        Raises:
            DataException: 不支持的频率格式
        """
        supported_freqs = {
            '1day': self.resample_to_daily,
            'daily': self.resample_to_daily,
            '1week': self.resample_to_weekly,
            'weekly': self.resample_to_weekly,
            '1month': self.resample_to_monthly,
            'monthly': self.resample_to_monthly,
        }
        
        # 检查预定义频率
        if target_freq in supported_freqs:
            return supported_freqs[target_freq]()
        
        # 检查分钟线
        if target_freq.endswith('min'):
            try:
                minutes = int(target_freq.replace('min', ''))
                if minutes <= 0:
                    raise ValueError()
                return self.resample_to_minutes(minutes)
            except ValueError:
                raise DataException(f"无效的分钟频率：{target_freq}", "INVALID_FREQUENCY")
        
        # 检查小时线
        if target_freq.endswith('hour'):
            try:
                hours = int(target_freq.replace('hour', ''))
                if hours <= 0:
                    raise ValueError()
                return self.resample_to_hours(hours)
            except ValueError:
                raise DataException(f"无效的小时频率：{target_freq}", "INVALID_FREQUENCY")
        
        # 不支持的频率
        raise DataException(f"不支持的频率：{target_freq}", "UNSUPPORTED_FREQUENCY")
    
    def resample_to_daily(self) -> List[Bar]:
        """
        重采样到日线
        
        Returns:
            日线 K 线列表
        """
        if not self.sorted_bars:
            return []
        
        daily_bars = []
        current_date = None
        current_bar = None
        
        for bar in self.sorted_bars:
            # 提取日期（假设 timestamp 格式为 YYYY-MM-DD 或 YYYY-MM-DD HH:MM:SS）
            bar_date = str(bar.timestamp)[:10]
            
            if current_date is None:
                current_date = bar_date
                current_bar = self._init_bar(bar)
            
            if bar_date == current_date:
                # 同一天，更新 OHLCV
                self._update_bar(current_bar, bar)
            else:
                # 新的一天，保存前一天的 K 线
                daily_bars.append(current_bar)
                current_date = bar_date
                current_bar = self._init_bar(bar)
        
        # 添加最后一根 K 线
        if current_bar:
            daily_bars.append(current_bar)
        
        return daily_bars
    
    def resample_to_weekly(self) -> List[Bar]:
        """
        重采样到周线（以周一为每周开始）
        
        Returns:
            周线 K 线列表
        """
        if not self.sorted_bars:
            return []
        
        daily_bars = self.resample_to_daily()
        weekly_bars = []
        current_week = None
        current_bar = None
        
        for bar in daily_bars:
            # 计算周数（ISO 周）
            bar_datetime = self._parse_timestamp(bar.timestamp)
            bar_week = bar_datetime.isocalendar()[1]
            bar_year = bar_datetime.year
            week_key = f"{bar_year}-W{bar_week:02d}"
            
            if current_week is None:
                current_week = week_key
                current_bar = self._init_bar(bar)
            
            if week_key == current_week:
                self._update_bar(current_bar, bar)
            else:
                weekly_bars.append(current_bar)
                current_week = week_key
                current_bar = self._init_bar(bar)
        
        if current_bar:
            weekly_bars.append(current_bar)
        
        return weekly_bars
    
    def resample_to_monthly(self) -> List[Bar]:
        """
        重采样到月线
        
        Returns:
            月线 K 线列表
        """
        if not self.sorted_bars:
            return []
        
        daily_bars = self.resample_to_daily()
        monthly_bars = []
        current_month = None
        current_bar = None
        
        for bar in daily_bars:
            # 提取年月
            bar_datetime = self._parse_timestamp(bar.timestamp)
            month_key = f"{bar_datetime.year}-{bar_datetime.month:02d}"
            
            if current_month is None:
                current_month = month_key
                current_bar = self._init_bar(bar)
            
            if month_key == current_month:
                self._update_bar(current_bar, bar)
            else:
                monthly_bars.append(current_bar)
                current_month = month_key
                current_bar = self._init_bar(bar)
        
        if current_bar:
            monthly_bars.append(current_bar)
        
        return monthly_bars
    
    def resample_to_minutes(self, minutes: int) -> List[Bar]:
        """
        重采样到分钟线
        
        Args:
            minutes: 目标分钟数（如 5 表示 5 分钟线）
            
        Returns:
            分钟线 K 线列表
        """
        if not self.sorted_bars:
            return []
        
        resampled_bars = []
        current_period = None
        current_bar = None
        
        for bar in self.sorted_bars:
            bar_datetime = self._parse_timestamp(bar.timestamp)
            
            # 计算时间周期
            period_start = self._get_period_start(bar_datetime, minutes, 'minutes')
            period_key = period_start.strftime('%Y-%m-%d %H:%M')
            
            if current_period is None:
                current_period = period_key
                current_bar = self._init_bar(bar)
            
            if period_key == current_period:
                self._update_bar(current_bar, bar)
            else:
                resampled_bars.append(current_bar)
                current_period = period_key
                current_bar = self._init_bar(bar)
        
        if current_bar:
            resampled_bars.append(current_bar)
        
        return resampled_bars
    
    def resample_to_hours(self, hours: int) -> List[Bar]:
        """
        重采样到小时线
        
        Args:
            hours: 目标小时数（如 4 表示 4 小时线）
            
        Returns:
            小时线 K 线列表
        """
        if not self.sorted_bars:
            return []
        
        resampled_bars = []
        current_period = None
        current_bar = None
        
        for bar in self.sorted_bars:
            bar_datetime = self._parse_timestamp(bar.timestamp)
            
            # 计算时间周期
            period_start = self._get_period_start(bar_datetime, hours, 'hours')
            period_key = period_start.strftime('%Y-%m-%d %H:00')
            
            if current_period is None:
                current_period = period_key
                current_bar = self._init_bar(bar)
            
            if period_key == current_period:
                self._update_bar(current_bar, bar)
            else:
                resampled_bars.append(current_bar)
                current_period = period_key
                current_bar = self._init_bar(bar)
        
        if current_bar:
            resampled_bars.append(current_bar)
        
        return resampled_bars
    
    def _init_bar(self, bar: Bar) -> Bar:
        """初始化新 K 线"""
        from ..core import Bar as BarClass
        return BarClass(
            timestamp=bar.timestamp,
            symbol=bar.symbol,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
            turnover=bar.turnover
        )
    
    def _update_bar(self, current_bar: Bar, new_bar: Bar):
        """更新 K 线数据"""
        # 更新最高价
        if new_bar.high > current_bar.high:
            current_bar.high = new_bar.high
        
        # 更新最低价
        if new_bar.low < current_bar.low:
            current_bar.low = new_bar.low
        
        # 更新收盘价（使用周期内最后一根）
        current_bar.close = new_bar.close
        
        # 累加成交量和成交额
        current_bar.volume += new_bar.volume
        current_bar.turnover += new_bar.turnover
    
    def _parse_timestamp(self, timestamp) -> datetime:
        """
        解析时间戳
        
        Args:
            timestamp: 时间戳（字符串或 datetime 对象）
            
        Returns:
            datetime 对象
            
        Raises:
            DataFormatException: 时间戳格式无法解析
        """
        if isinstance(timestamp, datetime):
            return timestamp
        
        timestamp_str = str(timestamp)
        
        # 尝试多种格式
        formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d %H:%M',
            '%Y-%m-%d',
            '%Y/%m/%d %H:%M:%S',
            '%Y/%m/%d',
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # 如果都失败，抛出异常
        raise DataFormatException(f"无法解析时间戳：{timestamp_str}")
    
    def _get_period_start(self, dt: datetime, period: int, unit: str) -> datetime:
        """
        获取周期起始时间
        
        Args:
            dt: 原始时间
            period: 周期长度
            unit: 单位 ('minutes' 或 'hours')
            
        Returns:
            周期起始时间
        """
        if unit == 'minutes':
            # 分钟线：向下取整到周期的整数倍
            minute = (dt.minute // period) * period
            return dt.replace(minute=minute, second=0, microsecond=0)
        
        elif unit == 'hours':
            # 小时线：向下取整到周期的整数倍
            hour = (dt.hour // period) * period
            return dt.replace(hour=hour, minute=0, second=0, microsecond=0)
        
        return dt


def resample_bars(bars: List[Bar], target_freq: str) -> List[Bar]:
    """
    便捷函数：重采样 K 线数据
    
    Args:
        bars: 原始 K 线列表
        target_freq: 目标频率
        
    Returns:
        重采样后的 K 线列表
        
    Example:
    ```python
    # 日线转周线
    weekly_bars = resample_bars(daily_bars, '1week')
    
    # 5 分钟线转小时线
    hourly_bars = resample_bars(minute_5_bars, '1hour')
    
    # 日线转月线
    monthly_bars = resample_bars(daily_bars, '1month')
    ```
    """
    resampler = Resampler(bars)
    return resampler.resample(target_freq)


# 导出
__all__ = ['Resampler', 'resample_bars']
