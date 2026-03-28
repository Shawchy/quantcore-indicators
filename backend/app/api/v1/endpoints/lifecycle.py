"""
生命周期管理 API 端点

提供手动触发归档、压缩、清理的接口
"""
from fastapi import APIRouter, BackgroundTasks
from loguru import logger
from typing import List

from app.storage.lifecycle_manager import lifecycle_manager


router = APIRouter(prefix="/lifecycle", tags=["生命周期管理"])


@router.post("/archive/{code}")
async def archive_stock_data(code: str, background_tasks: BackgroundTasks):
    """
    手动归档指定股票的数据
    
    将 90 天前的数据从 SQLite 迁移到 Parquet
    """
    background_tasks.add_task(lifecycle_manager.auto_archive, code)
    
    return {
        "success": True,
        "message": f"已提交 {code} 的归档任务",
        "code": code
    }


@router.post("/archive/batch")
async def batch_archive_data(codes: List[str], background_tasks: BackgroundTasks):
    """
    批量归档多只股票的数据
    """
    for code in codes:
        background_tasks.add_task(lifecycle_manager.auto_archive, code)
    
    return {
        "success": True,
        "message": f"已提交 {len(codes)} 只股票的归档任务",
        "codes": codes
    }


@router.post("/compress/{code}/{year}")
async def compress_stock_data(code: str, year: int, background_tasks: BackgroundTasks):
    """
    手动压缩指定股票的冷数据
    
    将指定年份的 Parquet 文件压缩到归档目录
    """
    background_tasks.add_task(
        lifecycle_manager.auto_compress_cold_data,
        code,
        year
    )
    
    return {
        "success": True,
        "message": f"已提交 {code} {year} 年数据的压缩任务",
        "code": code,
        "year": year
    }


@router.post("/cleanup/{code}")
async def cleanup_stock_data(code: str, background_tasks: BackgroundTasks):
    """
    手动清理指定股票的过期数据
    
    删除超过 5 年的数据
    """
    background_tasks.add_task(lifecycle_manager.cleanup_expired_data, code)
    
    return {
        "success": True,
        "message": f"已提交 {code} 的清理任务",
        "code": code
    }


@router.get("/stats")
async def get_lifecycle_stats():
    """获取生命周期管理统计信息"""
    stats = lifecycle_manager.get_stats()
    
    return {
        "success": True,
        "data": stats
    }


@router.post("/stats/reset")
async def reset_lifecycle_stats():
    """重置生命周期管理统计信息"""
    lifecycle_manager.reset_stats()
    
    return {
        "success": True,
        "message": "统计信息已重置"
    }


@router.get("/classify/{date}")
async def classify_data_by_date(date: str):
    """
    根据日期对数据进行分层
    
    返回数据所属的层级 (hot/warm/cold/expired)
    """
    layer = lifecycle_manager.classify_data(date)
    
    return {
        "success": True,
        "data": {
            "date": date,
            "layer": layer,
            "description": lifecycle_manager.lifecycle_config[layer]["description"]
        }
    }


@router.get("/config")
async def get_lifecycle_config():
    """获取生命周期配置"""
    return {
        "success": True,
        "data": lifecycle_manager.lifecycle_config
    }
