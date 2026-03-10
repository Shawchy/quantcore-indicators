from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import asyncio
from loguru import logger


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
    """分层数据加载器"""
    
    def __init__(self):
        self.task_queue: asyncio.Queue[LoadTask] = asyncio.Queue()
        self.active_tasks: Dict[str, LoadTask] = {}
        self.completed_tasks: Dict[str, LoadTask] = {}
        self._running = False
        self._worker_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """启动后台加载器"""
        self._running = True
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("数据加载器已启动")
    
    async def stop(self):
        """停止后台加载器"""
        self._running = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
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
            # 从数据源拉取数据
            klines = await data_source_manager.get_kline(
                code=code,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            task.loaded_count = len(klines)
            
            # 保存到数据库
            if klines:
                await data_persistence.save_klines(code, klines, "qfq")
            
            # 检查是否还有更多历史数据
            has_more = len(klines) >= 2000  # 假设单次最多返回 2000 条
            
            task.status = LoadStatus.PARTIAL if has_more else LoadStatus.COMPLETED
            task.progress = 100
            
            # 如果有更多数据，加入后台加载队列
            if has_more and priority in [LoadPriority.CURRENT_MONTH, LoadPriority.CURRENT_YEAR]:
                await self.queue_historical_loading(code, data_source_manager, data_persistence)
            
            # 返回加载进度
            return LoadProgress(
                code=code,
                status="partial" if has_more else "complete",
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
                background_loading=has_more,
                total_expected=self._estimate_total_bars(code, start_date, end_date),
                loaded=len(klines)
            )
            
        except Exception as e:
            task.status = LoadStatus.FAILED
            task.error = str(e)
            logger.error(f"加载 K 线数据失败 {code}: {e}")
            raise
        
        finally:
            self.completed_tasks[f"{code}_{priority.value}"] = task
            self.active_tasks.pop(f"{code}_{priority.value}", None)
            task.updated_at = datetime.now()
    
    async def queue_historical_loading(
        self,
        code: str,
        data_source_manager,
        data_persistence
    ):
        """将历史数据加载加入后台队列"""
        # 按优先级加入队列
        for priority in [LoadPriority.LAST_3_YEARS, LoadPriority.LAST_5_YEARS, LoadPriority.ALL_HISTORY]:
            await self.task_queue.put(LoadTask(
                code=code,
                priority=priority,
                start_date="",  # 将在 worker 中计算
                end_date=""
            ))
    
    async def _worker(self):
        """后台加载工作协程"""
        while self._running:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                await self._process_task(task)
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"后台加载任务处理失败：{e}")
    
    async def _process_task(self, task: LoadTask):
        """处理单个加载任务"""
        try:
            task.status = LoadStatus.LOADING
            logger.info(f"后台加载 {task.code} 优先级 {task.priority.name}")
            
            # 计算日期范围
            end_date = datetime.now().strftime("%Y%m%d")
            if task.priority == LoadPriority.LAST_3_YEARS:
                start_date = (datetime.now() - timedelta(days=365*3)).strftime("%Y%m%d")
            elif task.priority == LoadPriority.LAST_5_YEARS:
                start_date = (datetime.now() - timedelta(days=365*5)).strftime("%Y%m%d")
            else:
                start_date = "19900101"
            
            # 从数据源拉取数据
            from app.adapters import data_source_manager
            from app.services.data_persistence import data_persistence
            
            klines = await data_source_manager.get_kline(
                code=task.code,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )
            
            # 保存到数据库
            if klines:
                await data_persistence.save_klines(task.code, klines, "qfq")
                task.loaded_count = len(klines)
                logger.info(f"后台加载完成 {task.code} {task.priority.name} - {len(klines)}条数据")
            else:
                logger.warning(f"后台加载无数据 {task.code} {task.priority.name}")
            
            task.status = LoadStatus.COMPLETED
            task.progress = 100
            
        except Exception as e:
            task.status = LoadStatus.FAILED
            task.error = str(e)
            logger.error(f"后台加载失败 {task.code}: {e}")
        
        finally:
            task.updated_at = datetime.now()
            self.completed_tasks[f"{task.code}_{task.priority.value}"] = task
    
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
