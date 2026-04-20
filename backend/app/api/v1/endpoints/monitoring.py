"""
监控 API 端点

提供 Prometheus 指标暴露和监控数据查询接口
"""
from fastapi import APIRouter, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from loguru import logger

from app.middleware.metrics_collector import MetricsCollector
from app.middleware.rate_limiter import rate_limiters
from app.middleware.circuit_breaker import circuit_breakers
from app.storage.cache import cache_manager

from fastapi import Depends, HTTPException
from loguru import logger


# ==================== 依赖注入 ====================

def get_rate_limiters():
    """获取限流器实例（依赖注入）"""
    try:
        from app.middleware.rate_limiter import rate_limiters
        if rate_limiters is None:
            logger.error("限流器实例为 None")
            raise HTTPException(status_code=503, detail="服务未初始化")
        return rate_limiters
    except ImportError as e:
        logger.error(f"限流器导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")


def get_circuit_breakers():
    """获取断路器实例（依赖注入）"""
    try:
        from app.middleware.circuit_breaker import circuit_breakers
        if circuit_breakers is None:
            logger.error("断路器实例为 None")
            raise HTTPException(status_code=503, detail="服务未初始化")
        return circuit_breakers
    except ImportError as e:
        logger.error(f"断路器导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")


def get_cache_manager():
    """获取缓存管理器实例（依赖注入）"""
    try:
        from app.storage.cache import cache_manager
        if cache_manager is None:
            logger.error("缓存管理器实例为 None")
            raise HTTPException(status_code=503, detail="服务未初始化")
        return cache_manager
    except ImportError as e:
        logger.error(f"缓存管理器导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")


def get_trading_calendar():
    """获取交易日历服务实例（依赖注入）"""
    try:
        from app.services.trading_calendar import trading_calendar
        if trading_calendar is None:
            logger.error("交易日历服务实例为 None")
            raise HTTPException(status_code=503, detail="服务未初始化")
        return trading_calendar
    except ImportError as e:
        logger.error(f"交易日历服务导入失败：{e}")
        raise HTTPException(status_code=500, detail="服务初始化失败")



router = APIRouter(prefix="/metrics", tags=["监控"])


@router.get("")
async def get_metrics():
    """
    获取 Prometheus 指标
    
    Prometheus 会定期访问此端点收集指标数据
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )


@router.get("/data-sources")
async def get_data_source_metrics(
    rate_limiters=Depends(get_rate_limiters),
    circuit_breakers=Depends(get_circuit_breakers)
):
    """获取数据源详细指标"""
    try:
        metrics = {
            "rate_limiters": {},
            "circuit_breakers": {},
            "requests": {}
            }
    except Exception as e:
        logger.error(f"获取交易日历状态失败：{e}")
        raise HTTPException(status_code=500, detail="获取交易日历状态失败")
        
        # 限流器统计
        for source, limiter in rate_limiters.items():
        metrics["rate_limiters"][source] = limiter.get_stats()
    
    # 断路器统计
    for source, breaker in circuit_breakers.items():
        metrics["circuit_breakers"][source] = breaker.get_stats()
    
        return metrics
    except Exception as e:
        logger.error(f"获取数据源指标失败：{e}")
        raise HTTPException(status_code=500, detail="获取指标失败")


@router.get("/cache")
async def get_cache_metrics(
    cache_manager=Depends(get_cache_manager)
):
    """获取缓存详细指标"""
    try:
        cache_stats = cache_manager.get_all_stats()
    
    # 更新 Prometheus 指标
    for cache_type, stats in cache_stats.items():
        hit_rate = stats["hits"] / (stats["hits"] + stats["misses"]) if (stats["hits"] + stats["misses"]) > 0 else 0
        MetricsCollector.record_cache_hit_rate(cache_type, hit_rate)
    
        return cache_stats
    except Exception as e:
        logger.error(f"获取缓存指标失败：{e}")
        raise HTTPException(status_code=500, detail="获取缓存指标失败")


@router.get("/storage")
async def get_storage_metrics():
    """获取存储详细指标"""
    try:
        from pathlib import Path
        import os
    
    storage_info = {
        "sqlite": {},
        "parquet": {},
        "total_size_mb": 0
    }
    
    # SQLite 数据库信息
    sqlite_path = Path("./data/sqlite/quant.db")
    if sqlite_path.exists():
        storage_info["sqlite"] = {
            "path": str(sqlite_path),
            "size_mb": round(sqlite_path.stat().st_size / 1024 / 1024, 2),
            "exists": True
        }
        storage_info["total_size_mb"] += storage_info["sqlite"]["size_mb"]
    
    # Parquet 文件信息
    parquet_path = Path("./data/stock/market/kline/daily")
    if parquet_path.exists():
        parquet_files = list(parquet_path.rglob("*.parquet"))
        total_size = sum(f.stat().st_size for f in parquet_files)
        
        storage_info["parquet"] = {
            "path": str(parquet_path),
            "file_count": len(parquet_files),
            "total_size_mb": round(total_size / 1024 / 1024, 2)
        }
        storage_info["total_size_mb"] += storage_info["parquet"]["total_size_mb"]
    
        return storage_info
    except Exception as e:
        logger.error(f"获取存储指标失败：{e}")
        raise HTTPException(status_code=500, detail="获取存储指标失败")


@router.get("/health")
async def health_check():
    """健康检查端点"""
    health_status = {
        "status": "healthy",
        "timestamp": None,
        "components": {}
    }
    
    from datetime import datetime
    health_status["timestamp"] = datetime.now().isoformat()
    
    # 检查数据源状态
    for source, breaker in circuit_breakers.items():
        health_status["components"][f"data_source_{source}"] = {
            "status": "healthy" if breaker.get_state() == "closed" else "unhealthy",
            "circuit_breaker_state": breaker.get_state()
        }
    
    # 检查缓存状态
    cache_stats = cache_manager.get_all_stats()
    for cache_type, stats in cache_stats.items():
        hit_rate = stats["hits"] / (stats["hits"] + stats["misses"]) if (stats["hits"] + stats["misses"]) > 0 else 0
        health_status["components"][f"cache_{cache_type}"] = {
            "status": "healthy" if hit_rate > 0.5 else "degraded",
            "hit_rate": f"{hit_rate:.2%}"
        }
    
    # 检查数据库连接
    try:
        from app.storage.sqlite import get_session
        async with get_session() as session:
            await session.execute("SELECT 1")
        health_status["components"]["database"] = {"status": "healthy"}
    except Exception as e:
        health_status["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e)
        }
        health_status["status"] = "unhealthy"
    
    return health_status


@router.get("/summary")
async def get_metrics_summary(
    cache_manager=Depends(get_cache_manager)
):
    """获取指标摘要"""
    try:
        summary = {
            "data_sources": {},
            "cache": cache_manager.get_all_stats(),
            "storage": await get_storage_metrics()
        }
    
    # 数据源摘要
    for source in rate_limiters.keys():
        limiter_stats = rate_limiters[source].get_stats()
        breaker_stats = circuit_breakers[source].get_stats()
        
        summary["data_sources"][source] = {
            "rate_limiter": {
                "allowed": limiter_stats["allowed"],
                "rejected": limiter_stats["rejected"],
                "rejection_rate": limiter_stats["rejection_rate"]
            },
            "circuit_breaker": {
                "state": breaker_stats["state"],
                "failure_count": breaker_stats["failure_count"],
                "success_rate": breaker_stats["success_rate"]
            }
        }
    
        return summary
    except Exception as e:
        logger.error(f"获取指标摘要失败：{e}")
        raise HTTPException(status_code=500, detail="获取指标摘要失败")


@router.get("/trading-calendar")
async def get_trading_calendar_status(
    trading_calendar=Depends(get_trading_calendar)
):
    """获取交易日历状态"""
    try:
        status = trading_calendar.get_cache_status()
    
    latest_day = await trading_calendar.get_latest_trading_day()
    recent_days = await trading_calendar.get_recent_trading_days(5)
    
    return {
        "cache_status": status,
        "latest_trading_day": latest_day,
        "recent_trading_days": recent_days
    }


@router.post("/trading-calendar/refresh")
async def refresh_trading_calendar(
    trading_calendar=Depends(get_trading_calendar)
):
    """强制刷新交易日历数据"""
    try:
        success = await trading_calendar.force_refresh()
    
    return {
        "success": success,
        "message": "交易日历刷新成功" if success else "交易日历刷新失败",
        "status": trading_calendar.get_cache_status()
    }
