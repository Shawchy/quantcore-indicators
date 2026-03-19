"""
数据源管理 API 路由

提供数据源健康检查、优先级配置、性能统计等功能
"""
from fastapi import APIRouter, Query, HTTPException
from typing import List, Dict
from datetime import datetime
from loguru import logger

from app.models.schemas import ResponseModel

router = APIRouter(prefix="/data-source", tags=["数据源管理"])


class DataSourceHealth:
    name: str
    status: str
    response_time_ms: float
    success_rate: float
    last_check: datetime
    error_message: str | None = None


@router.get("/health", response_model=ResponseModel[Dict])
async def get_data_source_health():
    """获取所有数据源健康状态"""
    from app.adapters.factory import data_source_manager
    import time
    
    health_status = {}
    available_sources = data_source_manager.get_available_sources()
    
    for source_name in available_sources:
        adapter = data_source_manager.get_adapter(source_name)
        
        # 获取统计数据
        if hasattr(adapter, 'get_stats'):
            stats = adapter.get_stats()
        else:
            stats = {}
        
        # 健康检查（简单 ping 测试）
        try:
            start_time = time.time()
            # 执行一个简单请求
            await adapter.get_stock_info("000001")
            response_time = (time.time() - start_time) * 1000
            
            health_status[source_name] = {
                "name": source_name,
                "status": "healthy" if response_time < 2000 else "degraded",
                "response_time_ms": round(response_time, 2),
                "success_rate": stats.get("success_rate", 100.0),
                "last_check": datetime.now().isoformat(),
                "error_message": None
            }
        except Exception as e:
            logger.warning(f"数据源 {source_name} 健康检查失败：{e}")
            health_status[source_name] = {
                "name": source_name,
                "status": "unavailable",
                "response_time_ms": 0,
                "success_rate": 0,
                "last_check": datetime.now().isoformat(),
                "error_message": str(e)
            }
    
    return ResponseModel(data=health_status)


@router.get("/stats/{source_name}", response_model=ResponseModel[Dict])
async def get_data_source_stats(source_name: str):
    """获取指定数据源统计信息"""
    from app.adapters.factory import data_source_manager
    
    available_sources = data_source_manager.get_available_sources()
    
    if source_name not in available_sources:
        raise HTTPException(
            status_code=404,
            detail=f"数据源 {source_name} 不存在，可用数据源：{available_sources}"
        )
    
    adapter = data_source_manager.get_adapter(source_name)
    
    if hasattr(adapter, 'get_stats'):
        stats = adapter.get_stats()
    else:
        stats = {}
    
    return ResponseModel(data={
        "source_name": source_name,
        "total_requests": stats.get("total_requests", 0),
        "failed_requests": stats.get("failed_requests", 0),
        "avg_response_time_ms": stats.get("avg_response_time", 0),
        "cache_hit_rate": stats.get("cache_hit_rate", 0),
        "success_rate": stats.get("success_rate", 100.0),
    })


@router.post("/switch", response_model=ResponseModel[Dict])
async def switch_data_source(
    source_name: str = Query(..., description="数据源名称"),
    set_as_default: bool = Query(True, description="是否设为默认"),
):
    """切换默认数据源"""
    from app.adapters.factory import data_source_manager
    from app.config import settings
    
    available_sources = data_source_manager.get_available_sources()
    
    if source_name not in available_sources:
        return ResponseModel(
            success=False,
            code="NOT_AVAILABLE",
            message=f"数据源 {source_name} 不可用，可用数据源：{available_sources}"
        )
    
    # 更新配置（临时）
    if set_as_default:
        settings.DEFAULT_DATA_SOURCE = source_name
        logger.info(f"已切换默认数据源为：{source_name}")
    
    return ResponseModel(
        success=True,
        message=f"已切换默认数据源为：{source_name}",
        data={
            "current_source": source_name,
            "available_sources": available_sources
        }
    )


@router.get("/sources", response_model=ResponseModel[List[str]])
async def get_available_sources():
    """获取所有可用数据源列表"""
    from app.adapters.factory import data_source_manager
    
    sources = data_source_manager.get_available_sources()
    return ResponseModel(data=sources)


@router.get("/performance-stats", response_model=ResponseModel[Dict])
async def get_performance_stats():
    """获取数据源性能统计（用于智能推荐）"""
    from app.adapters.factory import data_source_manager
    
    stats = {}
    available_sources = data_source_manager.get_available_sources()
    
    for source_name in available_sources:
        adapter = data_source_manager.get_adapter(source_name)
        
        if hasattr(adapter, 'get_stats'):
            adapter_stats = adapter.get_stats()
            stats[source_name] = {
                "total_requests": adapter_stats.get("total_requests", 0),
                "success_rate": adapter_stats.get("success_rate", 0),
                "avg_response_time": adapter_stats.get("avg_response_time", 0),
                "cache_hit_rate": adapter_stats.get("cache_hit_rate", 0),
            }
    
    # 计算推荐优先级（基于响应时间和成功率）
    recommended = []
    for source_name, source_stats in stats.items():
        # 综合得分 = 成功率 * 0.6 + (100 - 响应时间) * 0.4
        score = (
            source_stats.get("success_rate", 0) * 0.6 +
            max(0, 100 - source_stats.get("avg_response_time", 100)) * 0.4
        )
        recommended.append((source_name, score))
    
    # 按得分排序
    recommended.sort(key=lambda x: x[1], reverse=True)
    recommended_priority = [name for name, _ in recommended]
    
    return ResponseModel(
        data={
            "stats": stats,
            "recommended_priority": recommended_priority,
            "recommendation_reason": "基于响应时间和成功率的综合评分",
        }
    )
