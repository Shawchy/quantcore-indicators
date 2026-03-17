from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from loguru import logger

from app.utils.load_progress import (
    get_progress_manager, 
    LoadTaskStatus, 
    DataType, 
    DataSource
)


class LoadPriority(Enum):
    """加载优先级"""
    CURRENT_MONTH = 1  # 本月
    CURRENT_YEAR = 2   # 本年
    LAST_3_YEARS = 3   # 最近 3 年
    LAST_5_YEARS = 4   # 最近 5 年
    ALL_HISTORY = 5    # 全部历史


class LoadStatus(Enum):
    """加载状态"""
    PENDING = "pending"
    LOADING = "loading"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial"


@dataclass
class LoadTask:
    """加载任务"""
    code: str
    priority: LoadPriority
    start_date: str
    end_date: str
    status: LoadStatus = LoadStatus.PENDING
    progress: int = 0
    loaded_count: int = 0
    error: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class LoadProgress:
    """加载进度"""
    code: str
    status: str  # partial | complete | loading
    data: List[Dict[str, Any]]
    coverage: Dict[str, Any]
    background_loading: bool = True
    total_expected: int = 0
    loaded: int = 0


class DataLoader:
    """按需数据加载器（Lazy Loading）"""
    
    def __init__(self):
        self.completed_tasks: Dict[str, LoadTask] = {}
        self._progress_manager = get_progress_manager()
    
    async def start(self):
        """启动加载器（按需模式无需后台任务）"""
        logger.info("数据加载器已启动（按需加载模式）")
    
    async def stop(self):
        """停止加载器"""
        logger.info("数据加载器已停止")
    
    async def load_kline_priority(
        self,
        code: str,
        data_source_manager,
        data_persistence,
        priority: LoadPriority = LoadPriority.CURRENT_YEAR
    ) -> LoadProgress:
        """
        优先加载指定范围的 K 线数据
        
        Args:
            code: 股票代码
            data_source_manager: 数据源管理器
            data_persistence: 数据持久化服务
            priority: 加载优先级
        """
        # 计算日期范围
        end_date = datetime.now().strftime("%Y%m%d")
        
        if priority == LoadPriority.CURRENT_MONTH:
            start_date = datetime.now().replace(day=1).strftime("%Y%m%d")
        elif priority == LoadPriority.CURRENT_YEAR:
            start_date = datetime.now().replace(month=1, day=1).strftime("%Y%m%d")
        elif priority == LoadPriority.LAST_3_YEARS:
            start_date = (datetime.now() - timedelta(days=365*3)).strftime("%Y%m%d")
        elif priority == LoadPriority.LAST_5_YEARS:
            start_date = (datetime.now() - timedelta(days=365*5)).strftime("%Y%m%d")
        else:
            start_date = "19900101"  # A 股起始日期
        
        # 创建进度追踪任务
        task_id = await self._progress_manager.create_task(
            task_name=f"加载 K 线数据 - {code}",
            data_type=DataType.KLINE,
            data_source=DataSource.MIXED,
            code=code,
            start_date=start_date,
            end_date=end_date,
            total=100  # 假设总进度为 100%
        )
        
        # 更新进度：开始
        await self._progress_manager.update_progress(
            task_id=task_id,
            status=LoadTaskStatus.RUNNING,
            message=f"开始加载 {code} 的 K 线数据",
            current=10
        )
        
        # 创建加载任务
        task = LoadTask(
            code=code,
            priority=priority,
            start_date=start_date,
            end_date=end_date
        )
        
        # 同步加载优先数据
        task.status = LoadStatus.LOADING
        self.active_tasks[f"{code}_{priority.value}"] = task
        
        try:
            # 更新进度：获取数据中
            await self._progress_manager.update_progress(
                task_id=task_id,
                message="正在从数据源获取数据...",
                current=30
            )
            
            # 从数据源拉取数据
            klines = await data_source_manager.get_kline(
                code=code,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            task.loaded_count = len(klines)
            
            # 更新进度：保存数据中
            await self._progress_manager.update_progress(
                task_id=task_id,
                message=f"已获取 {len(klines)} 条数据，正在保存到数据库...",
                current=70,
                loaded_count=len(klines)
            )
            
            # 保存到数据库
            if klines:
                await data_persistence.save_klines(code, klines, "qfq")
            
            # 更新进度：完成
            await self._progress_manager.update_progress(
                task_id=task_id,
                status=LoadTaskStatus.COMPLETED,
                message=f"成功加载 {len(klines)} 条 K 线数据",
                current=100
            )
            
            task.status = LoadStatus.COMPLETED
            task.progress = 100
            
            # 返回加载进度（按需模式，不后台加载历史数据）
            return LoadProgress(
                code=code,
                status="complete",
                data=[{
                    "date": k.date,
                    "open": k.open,
                    "high": k.high,
                    "low": k.low,
                    "close": k.close,
                    "volume": k.volume,
                    "amount": k.amount,
                    "turnover_rate": k.turnover_rate
                } for k in klines],
                coverage={
                    "start_date": start_date,
                    "end_date": end_date,
                    "loaded": len(klines),
                    "total_expected": self._estimate_total_bars(code, start_date, end_date)
                },
                background_loading=False,
                total_expected=self._estimate_total_bars(code, start_date, end_date),
                loaded=len(klines)
            )
            
        except Exception as e:
            task.status = LoadStatus.FAILED
            task.error = str(e)
            
            # 更新进度：失败
            await self._progress_manager.update_progress(
                task_id=task_id,
                status=LoadTaskStatus.FAILED,
                message=f"加载失败：{str(e)}",
                error_message=str(e)
            )
            
            logger.error(f"加载 K 线数据失败 {code}: {e}")
            raise
        
        finally:
            self.completed_tasks[f"{code}_{priority.value}"] = task
            task.updated_at = datetime.now()
    
    def _estimate_total_bars(self, code: str, start_date: str, end_date: str) -> int:
        """估算总数据量"""
        try:
            start = datetime.strptime(start_date, "%Y%m%d")
            end = datetime.strptime(end_date, "%Y%m%d")
            trading_days = (end - start).days * 0.41  # 一年约 250 个交易日
            return int(trading_days)
        except:
            return 0
    
    def get_load_progress(self, code: str) -> Optional[LoadProgress]:
        """获取加载进度"""
        # 查找最新的任务
        for key, task in self.completed_tasks.items():
            if key.startswith(code):
                return LoadProgress(
                    code=code,
                    status=task.status.value,
                    data=[],
                    coverage={
                        "start_date": task.start_date,
                        "end_date": task.end_date,
                        "loaded": task.loaded_count,
                        "total_expected": self._estimate_total_bars(
                            code, task.start_date, task.end_date
                        )
                    },
                    background_loading=task.status == LoadStatus.PARTIAL,
                    total_expected=self._estimate_total_bars(
                        code, task.start_date, task.end_date
                    ),
                    loaded=task.loaded_count
                )
        return None


# 全局数据加载器实例
data_loader = DataLoader()
