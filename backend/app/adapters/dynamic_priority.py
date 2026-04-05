"""
动态优先级管理器

根据数据源的实时性能动态调整优先级
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import deque
import asyncio
from loguru import logger

from .strategy_config import DataSourceType, get_priority_sources


@dataclass
class DataSourcePerformance:
    """数据源性能统计"""
    source: DataSourceType
    total_requests: int = 0
    success_count: int = 0
    failure_count: int = 0
    total_response_time: float = 0.0
    avg_response_time: float = 0.0
    last_request_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    last_failure_time: Optional[datetime] = None
    consecutive_failures: int = 0
    consecutive_successes: int = 0
    
    # 滑动窗口统计（最近10次请求）
    recent_response_times: deque = field(default_factory=lambda: deque(maxlen=10))
    recent_successes: deque = field(default_factory=lambda: deque(maxlen=10))
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 1.0
        return self.success_count / self.total_requests
    
    @property
    def recent_success_rate(self) -> float:
        """最近成功率"""
        if not self.recent_successes:
            return 1.0
        return sum(self.recent_successes) / len(self.recent_successes)
    
    @property
    def recent_avg_response_time(self) -> float:
        """最近平均响应时间"""
        if not self.recent_response_times:
            return 0.0
        return sum(self.recent_response_times) / len(self.recent_response_times)
    
    def record_request(self, success: bool, response_time: float):
        """记录请求结果"""
        self.total_requests += 1
        self.last_request_time = datetime.now()
        
        if success:
            self.success_count += 1
            self.consecutive_successes += 1
            self.consecutive_failures = 0
            self.last_success_time = datetime.now()
        else:
            self.failure_count += 1
            self.consecutive_failures += 1
            self.consecutive_successes = 0
            self.last_failure_time = datetime.now()
        
        # 更新响应时间统计
        self.total_response_time += response_time
        self.avg_response_time = self.total_response_time / self.total_requests
        self.recent_response_times.append(response_time)
        self.recent_successes.append(1 if success else 0)
    
    def calculate_score(self) -> float:
        """
        计算数据源得分
        
        得分公式：
        - 成功率权重：60%
        - 响应时间权重：40%（响应时间越短得分越高）
        - 连续失败惩罚：连续失败会降低得分
        """
        if self.total_requests == 0:
            return 0.5  # 默认中等分数
        
        # 成功率得分（使用最近成功率，更快反映当前状态）
        success_score = self.recent_success_rate * 0.6
        
        # 响应时间得分（归一化到 0-1，假设 5 秒为最差）
        avg_time = self.recent_avg_response_time
        if avg_time == 0:
            time_score = 0.5
        else:
            time_score = max(0, 1 - (avg_time / 5.0)) * 0.4
        
        # 连续失败惩罚
        failure_penalty = min(self.consecutive_failures * 0.1, 0.3)
        
        score = success_score + time_score - failure_penalty
        return max(0.0, min(1.0, score))


class DynamicPriorityManager:
    """动态优先级管理器"""
    
    def __init__(self, update_interval: int = 60):
        """
        初始化动态优先级管理器
        
        Args:
            update_interval: 优先级更新间隔（秒）
        """
        self._performance_stats: Dict[str, DataSourcePerformance] = {}
        self._update_interval = update_interval
        self._last_update = datetime.now()
        self._update_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
        # 缓存的动态优先级
        self._dynamic_priorities: Dict[str, List[DataSourceType]] = {}
    
    async def start(self):
        """启动优先级更新任务"""
        if self._update_task is None:
            self._update_task = asyncio.create_task(self._update_loop())
            logger.info("动态优先级管理器已启动")
    
    async def stop(self):
        """停止优先级更新任务"""
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
            logger.info("动态优先级管理器已停止")
    
    async def _update_loop(self):
        """优先级更新循环"""
        while True:
            try:
                await asyncio.sleep(self._update_interval)
                await self._update_all_priorities()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"优先级更新失败: {e}")
    
    async def _update_all_priorities(self):
        """更新所有数据类型的优先级"""
        from .strategy_config import get_all_data_types
        
        async with self._lock:
            for data_type in get_all_data_types():
                self._dynamic_priorities[data_type] = self._calculate_priority(data_type)
            
            self._last_update = datetime.now()
            logger.debug(f"已更新 {len(self._dynamic_priorities)} 种数据类型的优先级")
    
    def _calculate_priority(self, data_type: str) -> List[DataSourceType]:
        """计算指定数据类型的动态优先级"""
        base_priority = get_priority_sources(data_type)
        
        # 为每个数据源计算得分
        scored_sources = []
        for source in base_priority:
            perf_key = f"{source.value}:{data_type}"
            perf = self._performance_stats.get(perf_key)
            
            if perf:
                score = perf.calculate_score()
            else:
                score = 0.5  # 默认分数
            
            scored_sources.append((source, score))
        
        # 按得分排序
        scored_sources.sort(key=lambda x: x[1], reverse=True)
        
        return [s[0] for s in scored_sources]
    
    def record_request(
        self,
        source: DataSourceType,
        data_type: str,
        success: bool,
        response_time: float
    ):
        """
        记录请求结果
        
        Args:
            source: 数据源类型
            data_type: 数据类型
            success: 是否成功
            response_time: 响应时间（秒）
        """
        perf_key = f"{source.value}:{data_type}"
        
        if perf_key not in self._performance_stats:
            self._performance_stats[perf_key] = DataSourcePerformance(source)
        
        self._performance_stats[perf_key].record_request(success, response_time)
        
        # 如果距离上次更新时间超过 10 秒，立即更新
        if (datetime.now() - self._last_update).total_seconds() > 10:
            # 异步更新优先级
            asyncio.create_task(self._update_all_priorities())
    
    def get_priority(self, data_type: str) -> List[DataSourceType]:
        """
        获取指定数据类型的动态优先级
        
        Args:
            data_type: 数据类型
        
        Returns:
            数据源优先级列表
        """
        # 如果有动态优先级，使用动态优先级
        if data_type in self._dynamic_priorities:
            return self._dynamic_priorities[data_type]
        
        # 否则返回基础优先级
        return get_priority_sources(data_type)
    
    def get_performance_stats(self, source: DataSourceType, data_type: str) -> Optional[DataSourcePerformance]:
        """获取性能统计"""
        perf_key = f"{source.value}:{data_type}"
        return self._performance_stats.get(perf_key)
    
    def get_all_performance_stats(self) -> Dict[str, DataSourcePerformance]:
        """获取所有性能统计"""
        return self._performance_stats.copy()
    
    def reset_stats(self, source: Optional[DataSourceType] = None, data_type: Optional[str] = None):
        """重置统计信息"""
        if source and data_type:
            perf_key = f"{source.value}:{data_type}"
            if perf_key in self._performance_stats:
                del self._performance_stats[perf_key]
        elif source:
            keys_to_remove = [k for k in self._performance_stats.keys() if k.startswith(f"{source.value}:")]
            for key in keys_to_remove:
                del self._performance_stats[key]
        else:
            self._performance_stats.clear()
    
    def get_priority_report(self) -> Dict[str, Any]:
        """获取优先级报告"""
        from .strategy_config import get_all_data_types
        
        report = {
            "last_update": self._last_update.isoformat(),
            "update_interval": self._update_interval,
            "data_types": {}
        }
        
        for data_type in get_all_data_types():
            base_priority = get_priority_sources(data_type)
            dynamic_priority = self._dynamic_priorities.get(data_type, base_priority)
            
            # 计算每个数据源的得分
            source_scores = []
            for source in dynamic_priority:
                perf_key = f"{source.value}:{data_type}"
                perf = self._performance_stats.get(perf_key)
                score = perf.calculate_score() if perf else 0.5
                
                source_scores.append({
                    "source": source.value,
                    "score": round(score, 3),
                    "success_rate": round(perf.recent_success_rate, 3) if perf else None,
                    "avg_response_time": round(perf.recent_avg_response_time, 3) if perf else None,
                    "total_requests": perf.total_requests if perf else 0,
                })
            
            report["data_types"][data_type] = {
                "base_priority": [s.value for s in base_priority],
                "dynamic_priority": [s.value for s in dynamic_priority],
                "source_scores": source_scores
            }
        
        return report


# 全局动态优先级管理器实例
dynamic_priority_manager = DynamicPriorityManager()
