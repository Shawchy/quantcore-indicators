from fastapi import APIRouter, Query, Body, BackgroundTasks, Depends
from app.models.schemas import ResponseModel
from app.api.deps import CurrentUser
from app.core.security import User
from typing import Optional, Dict, Any, List
import uuid
import json
from datetime import datetime
from loguru import logger
from sqlalchemy import select
import asyncio

from app.storage import Strategy, get_session
from app.core.backtest import strategy_optimizer

router = APIRouter()

class OptimizationTaskManager:
    """优化任务管理器（线程安全）"""
    def __init__(self):
        self._tasks: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def create_task(self, task_id: str, task_data: Dict[str, Any]):
        async with self._lock:
            self._tasks[task_id] = task_data
    
    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        async with self._lock:
            return self._tasks.get(task_id)
    
    async def update_task(self, task_id: str, updates: Dict[str, Any]):
        async with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].update(updates)
    
    async def delete_task(self, task_id: str):
        async with self._lock:
            self._tasks.pop(task_id, None)

task_manager = OptimizationTaskManager()


async def run_optimization_task(
    task_id: str,
    strategy_id: str,
    code: str,
    start_date: str,
    end_date: str,
    strategy_type: str,
    param_ranges: Dict[str, List],
    method: str,
    initial_capital: float
):
    try:
        await task_manager.update_task(task_id, {
            "status": "running",
            "progress": 0
        })
        
        result = await strategy_optimizer.optimize_strategy(
            code=code,
            start_date=start_date,
            end_date=end_date,
            strategy_type=strategy_type,
            param_ranges=param_ranges,
            initial_capital=initial_capital,
            n_iterations=20 if method == "bayesian" else 50,
            method=method
        )
        
        await task_manager.update_task(task_id, {
            "status": "completed",
            "result": {
                "best_params": result.best_params,
                "best_score": float(result.best_score),
                "total_iterations": result.n_iterations,
                "all_results": result.all_results[-10:] if len(result.all_results) > 10 else result.all_results
            }
        })
        
        logger.info(f"优化任务 {task_id} 完成，最佳得分: {result.best_score:.4f}")
        
    except Exception as e:
        logger.error(f"优化任务 {task_id} 失败: {e}")
        await task_manager.update_task(task_id, {
            "status": "failed",
            "error": str(e)
        })


@router.get("/list", response_model=ResponseModel[list])
async def get_strategy_list(current_user: CurrentUser):
    async with get_session() as session:
        result = await session.execute(select(Strategy))
        strategies = result.scalars().all()
        
        return ResponseModel(data=[{
            "strategy_id": s.strategy_id,
            "name": s.name,
            "strategy_type": s.strategy_type,
            "is_active": s.is_active,
            "created_at": s.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for s in strategies])


@router.get("/{strategy_id}", response_model=ResponseModel[dict])
async def get_strategy(strategy_id: str, current_user: CurrentUser):
    async with get_session() as session:
        result = await session.execute(
            select(Strategy).where(Strategy.strategy_id == strategy_id)
        )
        strategy = result.scalar_one_or_none()
        
        if not strategy:
            return ResponseModel(success=False, code="NOT_FOUND", message="策略不存在")
        
        return ResponseModel(data={
            "strategy_id": strategy.strategy_id,
            "name": strategy.name,
            "strategy_type": strategy.strategy_type,
            "config": json.loads(strategy.config) if strategy.config else {},
            "is_active": strategy.is_active,
            "created_at": strategy.created_at.strftime("%Y-%m-%d %H:%M:%S")
        })


@router.post("/create", response_model=ResponseModel[dict])
async def create_strategy(current_user: CurrentUser, strategy_config: dict = Body(...)):
    strategy_id = f"strategy_{uuid.uuid4().hex[:8]}"
    
    async with get_session() as session:
        strategy = Strategy(
            strategy_id=strategy_id,
            name=strategy_config.get("name", "未命名策略"),
            strategy_type=strategy_config.get("type", "custom"),
            config=json.dumps(strategy_config.get("config", {})),
            is_active=True
        )
        session.add(strategy)
        await session.commit()
        
        return ResponseModel(data={
            "strategy_id": strategy_id,
            "message": "策略创建成功"
        })


@router.put("/{strategy_id}", response_model=ResponseModel[dict])
async def update_strategy(strategy_id: str, current_user: CurrentUser, strategy_config: dict = Body(...)):
    async with get_session() as session:
        result = await session.execute(
            select(Strategy).where(Strategy.strategy_id == strategy_id)
        )
        strategy = result.scalar_one_or_none()
        
        if not strategy:
            return ResponseModel(success=False, code="NOT_FOUND", message="策略不存在")
        
        if "name" in strategy_config:
            strategy.name = strategy_config["name"]
        if "config" in strategy_config:
            strategy.config = json.dumps(strategy_config["config"])
        if "is_active" in strategy_config:
            strategy.is_active = strategy_config["is_active"]
        
        await session.commit()
        
        return ResponseModel(data={
            "strategy_id": strategy_id,
            "message": "策略更新成功"
        })


@router.delete("/{strategy_id}", response_model=ResponseModel[dict])
async def delete_strategy(strategy_id: str, current_user: CurrentUser):
    async with get_session() as session:
        result = await session.execute(
            select(Strategy).where(Strategy.strategy_id == strategy_id)
        )
        strategy = result.scalar_one_or_none()
        
        if not strategy:
            return ResponseModel(success=False, code="NOT_FOUND", message="策略不存在")
        
        await session.delete(strategy)
        await session.commit()
        
        return ResponseModel(data={
            "strategy_id": strategy_id,
            "message": "策略删除成功"
        })


@router.post("/{strategy_id}/optimize", response_model=ResponseModel[dict])
async def optimize_strategy_params(
    strategy_id: str,
    background_tasks: BackgroundTasks,
    current_user: CurrentUser,
    optimization_config: dict = Body(...),
):
    task_id = f"opt_{uuid.uuid4().hex[:8]}"
    
    await task_manager.create_task(task_id, {
        "strategy_id": strategy_id,
        "status": "pending",
        "progress": 0,
        "method": optimization_config.get("method", "bayesian"),
        "created_at": datetime.now().isoformat()
    })
    
    background_tasks.add_task(
        run_optimization_task,
        task_id,
        strategy_id,
        optimization_config.get("code", "000001"),
        optimization_config.get("start_date", ""),
        optimization_config.get("end_date", ""),
        optimization_config.get("strategy_type", "ma_cross"),
        optimization_config.get("param_ranges", {}),
        optimization_config.get("method", "bayesian"),
        optimization_config.get("initial_capital", 1000000)
    )
    
    return ResponseModel(data={
        "task_id": task_id,
        "strategy_id": strategy_id,
        "status": "pending",
        "message": "参数优化任务已提交，请通过task_id查询进度"
    })


@router.get("/optimize/status/{task_id}", response_model=ResponseModel[dict])
async def get_optimization_status(task_id: str, current_user: CurrentUser):
    task = await task_manager.get_task(task_id)
    
    if not task:
        return ResponseModel(success=False, code="NOT_FOUND", message="优化任务不存在")
    
    return ResponseModel(data={
        "task_id": task_id,
        "strategy_id": task.get("strategy_id"),
        "status": task.get("status"),
        "progress": task.get("progress", 0),
        "result": task.get("result"),
        "error": task.get("error"),
        "created_at": task.get("created_at")
    })
