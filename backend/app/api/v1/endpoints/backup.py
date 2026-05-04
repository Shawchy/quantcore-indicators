"""
备份和恢复 API 端点

提供手动触发备份、恢复、查看备份列表的接口
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from loguru import logger

from app.storage.backup_manager import backup_manager
from app.api.deps import CurrentAdminUser
from app.core.security import get_password_hash


router = APIRouter(prefix="/backup", tags=["备份和恢复"])


class BackupRequest(BaseModel):
    description: Optional[str] = ""
    backup_type: str = "full"


class RestoreRequest(BaseModel):
    backup_name: str
    target_dir: Optional[str] = None


@router.post("/create")
async def create_backup(request: BackupRequest, background_tasks: BackgroundTasks, _=CurrentAdminUser):
    """
    手动创建备份 (需要认证)
    
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
async def restore_backup(request: RestoreRequest, background_tasks: BackgroundTasks, _=CurrentAdminUser):
    """
    从备份恢复数据 (需要认证)
    
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
async def list_backups(_=CurrentAdminUser):
    """获取所有备份列表 (需要认证)"""
    backups = await backup_manager.list_backups()
    
    return {
        "success": True,
        "count": len(backups),
        "backups": backups
    }


@router.post("/cleanup")
async def cleanup_old_backups(background_tasks: BackgroundTasks, _=CurrentAdminUser):
    """清理过期备份 (需要认证)"""
    background_tasks.add_task(backup_manager.cleanup_old_backups)
    
    return {
        "success": True,
        "message": "已提交清理任务"
    }


@router.get("/stats")
async def get_backup_stats(_=CurrentAdminUser):
    """获取备份统计信息 (需要认证)"""
    stats = backup_manager.get_stats()
    
    return {
        "success": True,
        "data": stats
    }


@router.get("/config")
async def get_backup_config(_=CurrentAdminUser):
    """获取备份配置 (需要认证)"""
    return {
        "success": True,
        "data": backup_manager.backup_config
    }


@router.delete("/{backup_name}")
async def delete_backup(backup_name: str, _=CurrentAdminUser):
    """
    删除指定备份 (需要认证)
    
    安全验证：防止路径遍历攻击
    """
    import shutil
    from pathlib import Path
    
    # 路径遍历防护：拒绝任何包含路径分隔符的输入
    if "/" in backup_name or "\\" in backup_name:
        raise HTTPException(status_code=400, detail="无效的备份名称")
    
    # 获取绝对路径并验证是否在备份目录内
    backup_dir = Path(backup_manager.backup_dir).resolve()
    backup_path = (backup_dir / backup_name).resolve()
    
    # 确保解析后的路径仍在备份目录内
    if not str(backup_path).startswith(str(backup_dir)):
        raise HTTPException(status_code=403, detail="拒绝访问：非法路径")
    
    if not backup_path.exists():
        raise HTTPException(status_code=404, detail="备份不存在")
    
    # 验证是目录而不是符号链接
    if backup_path.is_symlink():
        raise HTTPException(status_code=403, detail="拒绝访问：不允许删除符号链接")
    
    shutil.rmtree(backup_path)
    logger.info(f"已删除备份: {backup_name}")
    
    return {
        "success": True,
        "message": f"已删除备份: {backup_name}"
    }
