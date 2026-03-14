"""
数据加载进度 API
提供数据加载进度的查询和管理功能
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List, Dict, Any
from loguru import logger

from app.models.schemas import ResponseModel
from app.api.deps import OptionalCurrentUser
from app.utils.load_progress import get_progress_manager, LoadTaskStatus, DataType, DataSource

router = APIRouter()
progress_manager = get_progress_manager()


@router.get("/tasks", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_loading_tasks(
    status: Optional[str] = Query(None, description="任务状态筛选"),
    data_type: Optional[str] = Query(None, description="数据类型筛选"),
    current_user: OptionalCurrentUser = None
):
    """
    获取所有加载任务列表
    
    Args:
        status: 任务状态筛选（pending/running/completed/failed/partial）
        data_type: 数据类型筛选（kline/stock_info/sector/chip 等）
    """
    tasks = await progress_manager.get_all_progress()
    
    # 筛选
    if status:
        tasks = [t for t in tasks if t["status"] == status]
    if data_type:
        tasks = [t for t in tasks if t["data_type"] == data_type]
    
    return ResponseModel(data=tasks)


@router.get("/task/{task_id}", response_model=ResponseModel[Dict[str, Any]])
async def get_loading_task(
    task_id: str,
    current_user: OptionalCurrentUser = None
):
    """
    获取单个任务的加载进度
    """
    progress = await progress_manager.get_progress(task_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail=f"任务不存在：{task_id}")
    
    return ResponseModel(data=progress)


@router.delete("/task/{task_id}", response_model=ResponseModel[Dict[str, Any]])
async def remove_loading_task(
    task_id: str,
    current_user: OptionalCurrentUser = None
):
    """
    移除已完成的任务
    """
    progress = await progress_manager.get_progress(task_id)
    
    if not progress:
        raise HTTPException(status_code=404, detail=f"任务不存在：{task_id}")
    
    if progress["status"] not in ["completed", "failed", "partial"]:
        raise HTTPException(status_code=400, detail="只能移除已完成或失败的任务")
    
    await progress_manager.remove_task(task_id)
    
    return ResponseModel(data={"message": f"任务已移除：{task_id}"})


@router.post("/cleanup", response_model=ResponseModel[Dict[str, Any]])
async def cleanup_loading_tasks(
    max_age_hours: int = Query(24, description="保留小时数"),
    current_user: OptionalCurrentUser = None
):
    """
    清理旧的加载任务
    
    Args:
        max_age_hours: 保留最近多少小时的任务，默认 24 小时
    """
    await progress_manager.cleanup_old_tasks(max_age_hours)
    
    return ResponseModel(data={"message": f"已清理超过 {max_age_hours} 小时的旧任务"})
