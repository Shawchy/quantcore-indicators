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
async def get_data_source_metrics():
    """获取数据源详细指标"""
    metrics = {
        "rate_limiters": {},
        "circuit_breakers": {},
        "requests": {}
    }
    
    # 限流器统计
    for source, limiter in rate_limiters.items():
        metrics["rate_limiters"][source] = limiter.get_stats()
    
    # 断路器统计
    for source, breaker in circuit_breakers.items():
        metrics["circuit_breakers"][source] = breaker.get_stats()
    
    return metrics


@router.get("/cache")
async def get_cache_metrics():
    """获取缓存详细指标"""
    cache_stats = cache_manager.get_all_stats()
    
    # 更新 Prometheus 指标
    for cache_type, stats in cache_stats.items():
        hit_rate = stats["hits"] / (stats["hits"] + stats["misses"]) if (stats["hits"] + stats["misses"]) > 0 else 0
        MetricsCollector.record_cache_hit_rate(cache_type, hit_rate)
    
    return cache_stats


@router.get("/storage")
async def get_storage_metrics():
    """获取存储详细指标"""
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
async def get_metrics_summary():
    """获取指标摘要"""
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
