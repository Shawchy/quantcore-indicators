"""
数据加载进度追踪模块
提供数据加载进度的实时追踪和查询功能
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field
import asyncio
from loguru import logger


class LoadTaskStatus(str, Enum):
    """加载任务状态"""
    PENDING = "pending"  # 等待中
    RUNNING = "running"  # 运行中
    COMPLETED = "completed"  # 已完成
    FAILED = "failed"  # 失败
    PARTIAL = "partial"  # 部分完成


class DataType(str, Enum):
    """数据类型"""
    KLINE = "kline"  # K 线数据
    STOCK_INFO = "stock_info"  # 股票信息
    SECTOR = "sector"  # 板块数据
    CHIP = "chip"  # 筹码数据
    MONEYFLOW = "moneyflow"  # 资金流向
    INDEX = "index"  # 指数数据
    REALTIME = "realtime"  # 实时数据


class DataSource(str, Enum):
    """数据源"""
    TUSHARE = "tushare"
    AKSHARE = "akshare"
    BAOSTOCK = "baostock"
    YFINANCE = "yfinance"
    MIXED = "mixed"  # 混合数据源


@dataclass
class LoadProgress:
    """加载进度信息"""
    task_id: str
    task_name: str
    status: LoadTaskStatus
    data_type: DataType
    data_source: DataSource
    code: Optional[str] = None  # 股票代码（如果是单个股票）
    start_date: Optional[str] = None  # 开始日期
    end_date: Optional[str] = None  # 结束日期
    
    # 进度信息
    total: int = 0  # 总任务数
    current: int = 0  # 当前完成数
    progress_percent: float = 0.0  # 进度百分比
    
    # 详细信息
    message: str = ""  # 当前状态消息
    error_message: Optional[str] = None  # 错误信息
    
    # 时间信息
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    updated_at: datetime = field(default_factory=datetime.now)
    
    # 统计数据
    loaded_count: int = 0  # 已加载数据条数
    failed_count: int = 0  # 失败次数
    retry_count: int = 0  # 重试次数
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "task_name": self.task_name,
            "status": self.status.value,
            "data_type": self.data_type.value,
            "data_source": self.data_source.value,
            "code": self.code,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "progress_percent": self.progress_percent,
            "total": self.total,
            "current": self.current,
            "loaded_count": self.loaded_count,
            "failed_count": self.failed_count,
            "message": self.message,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "updated_at": self.updated_at.isoformat(),
        }


class ProgressManager:
    """进度管理器"""
    _instance: Optional['ProgressManager'] = None
    _tasks: Dict[str, LoadProgress] = {}
    _lock: asyncio.Lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def create_task(
        self,
        task_name: str,
        data_type: DataType,
        data_source: DataSource,
        code: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        total: int = 0
    ) -> str:
        """创建新的加载任务"""
        async with self._lock:
            import uuid
            task_id = str(uuid.uuid4())
            
            progress = LoadProgress(
                task_id=task_id,
                task_name=task_name,
                status=LoadTaskStatus.PENDING,
                data_type=data_type,
                data_source=data_source,
                code=code,
                start_date=start_date,
                end_date=end_date,
                total=total
            )
            
            self._tasks[task_id] = progress
            logger.info(f"创建加载任务：{task_id} - {task_name}")
            return task_id
    
    async def update_progress(
        self,
        task_id: str,
        current: Optional[int] = None,
        status: Optional[LoadTaskStatus] = None,
        message: Optional[str] = None,
        loaded_count: Optional[int] = None,
        error_message: Optional[str] = None
    ):
        """更新任务进度"""
        async with self._lock:
            if task_id not in self._tasks:
                logger.error(f"任务不存在：{task_id}")
                return
            
            progress = self._tasks[task_id]
            progress.updated_at = datetime.now()
            
            if current is not None:
                progress.current = current
                if progress.total > 0:
                    progress.progress_percent = (current / progress.total) * 100
            
            if status is not None:
                progress.status = status
                if status == LoadTaskStatus.RUNNING and not progress.started_at:
                    progress.started_at = datetime.now()
                elif status in [LoadTaskStatus.COMPLETED, LoadTaskStatus.FAILED, LoadTaskStatus.PARTIAL]:
                    progress.completed_at = datetime.now()
            
            if message is not None:
                progress.message = message
            
            if loaded_count is not None:
                progress.loaded_count = loaded_count
            
            if error_message is not None:
                progress.error_message = error_message
                progress.failed_count += 1
            
            logger.debug(f"更新任务进度：{task_id} - {progress.current}/{progress.total} ({progress.progress_percent:.1f}%)")
    
    async def get_progress(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取任务进度"""
        async with self._lock:
            if task_id not in self._tasks:
                return None
            return self._tasks[task_id].to_dict()
    
    async def get_all_progress(self) -> List[Dict[str, Any]]:
        """获取所有任务进度"""
        async with self._lock:
            return [task.to_dict() for task in self._tasks.values()]
    
    async def remove_task(self, task_id: str):
        """移除已完成的任务"""
        async with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
                logger.info(f"移除任务：{task_id}")
    
    async def cleanup_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        async with self._lock:
            now = datetime.now()
            to_remove = []
            
            for task_id, progress in self._tasks.items():
                if progress.completed_at:
                    age = (now - progress.completed_at).total_seconds() / 3600
                    if age > max_age_hours:
                        to_remove.append(task_id)
            
            for task_id in to_remove:
                del self._tasks[task_id]
            
            if to_remove:
                logger.info(f"清理了 {len(to_remove)} 个旧任务")


# 全局进度管理器实例
progress_manager = ProgressManager()


def get_progress_manager() -> ProgressManager:
    """获取进度管理器实例"""
    return progress_manager
