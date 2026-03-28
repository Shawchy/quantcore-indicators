"""
备份和恢复 API 端点

提供手动触发备份、恢复、查看备份列表的接口
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger

from app.storage.backup_manager import backup_manager


router = APIRouter(prefix="/backup", tags=["备份和恢复"])


class BackupRequest(BaseModel):
    description: Optional[str] = ""
    backup_type: str = "full"


class RestoreRequest(BaseModel):
    backup_name: str
    target_dir: Optional[str] = None


@router.post("/create")
async def create_backup(request: BackupRequest, background_tasks: BackgroundTasks):
    """
    手动创建备份
    
    - full: 完整备份
    - incremental: 增量备份
    """
    if request.backup_type == "full":
        background_tasks.add_task(
            backup_manager.create_full_backup,
            request.description
        )
        return {
            "success": True,
            "message": "已提交完整备份任务",
            "backup_type": "full"
        }
    elif request.backup_type == "incremental":
        background_tasks.add_task(
            backup_manager.create_incremental_backup,
            request.description
        )
        return {
            "success": True,
            "message": "已提交增量备份任务",
            "backup_type": "incremental"
        }
    else:
        raise HTTPException(status_code=400, detail="无效的备份类型")


@router.post("/restore")
async def restore_backup(request: RestoreRequest, background_tasks: BackgroundTasks):
    """
    从备份恢复数据
    
    警告：恢复操作会覆盖现有数据
    """
    result = await backup_manager.restore_backup(
        request.backup_name,
        request.target_dir
    )
    
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result.get("error", "恢复失败"))
    
    return result


@router.get("/list")
async def list_backups():
    """获取所有备份列表"""
    backups = await backup_manager.list_backups()
    
    return {
        "success": True,
        "count": len(backups),
        "backups": backups
    }


@router.post("/cleanup")
async def cleanup_old_backups(background_tasks: BackgroundTasks):
    """清理过期备份"""
    background_tasks.add_task(backup_manager.cleanup_old_backups)
    
    return {
        "success": True,
        "message": "已提交清理任务"
    }


@router.get("/stats")
async def get_backup_stats():
    """获取备份统计信息"""
    stats = backup_manager.get_stats()
    
    return {
        "success": True,
        "data": stats
    }


@router.get("/config")
async def get_backup_config():
    """获取备份配置"""
    return {
        "success": True,
        "data": backup_manager.backup_config
    }


@router.delete("/{backup_name}")
async def delete_backup(backup_name: str):
    """删除指定备份"""
    import shutil
    from pathlib import Path
    
    backup_path = Path(backup_manager.backup_dir) / backup_name
    
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="备份不存在")
    
    shutil.rmtree(backup_path)
    logger.info(f"已删除备份: {backup_name}")
    
    return {
        "success": True,
        "message": f"已删除备份: {backup_name}"
    }
