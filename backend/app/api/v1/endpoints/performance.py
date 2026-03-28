"""
性能优化 API 端点

提供查询分析、缓存管理和性能监控接口
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from loguru import logger

from app.storage.query_optimizer import query_optimizer
from app.storage.cache_optimizer import cache_optimizer


router = APIRouter(prefix="/performance", tags=["性能优化"])


class QueryAnalyzeRequest(BaseModel):
    query: str


class CacheWarmupRequest(BaseModel):
    data_type: str
    items: List[str]


class CachePolicyRequest(BaseModel):
    cache_type: str
    policy: Dict[str, Any]


@router.get("/query/stats")
async def get_query_stats():
    """获取查询统计信息"""
    stats = query_optimizer.get_query_stats()
    
    return {
        "success": True,
        "data": stats
    }


@router.get("/query/slow")
async def get_slow_queries(threshold: Optional[float] = None):
    """获取慢查询列表"""
    slow_queries = query_optimizer.get_slow_queries(threshold)
    
    return {
        "success": True,
        "count": len(slow_queries),
        "slow_queries": slow_queries
    }


@router.post("/query/analyze")
async def analyze_query(request: QueryAnalyzeRequest):
    """分析查询"""
    analysis = await query_optimizer.analyze_query(request.query)
    
    return {
        "success": True,
        "analysis": analysis
    }


@router.get("/query/index-suggestions")
async def get_index_suggestions():
    """获取索引建议"""
    suggestions = query_optimizer.get_index_suggestions()
    
    return {
        "success": True,
        "suggestions": suggestions
    }


@router.post("/query/reset-stats")
async def reset_query_stats():
    """重置查询统计"""
    query_optimizer.reset_stats()
    
    return {
        "success": True,
        "message": "查询统计已重置"
    }


@router.get("/cache/stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    stats = cache_optimizer.get_cache_stats()
    
    return {
        "success": True,
        "data": stats
    }


@router.post("/cache/warmup")
async def warmup_cache(request: CacheWarmupRequest, background_tasks: BackgroundTasks):
    """缓存预热"""
    background_tasks.add_task(
        cache_optimizer.warmup_cache,
        request.data_type,
        request.items
    )
    
    return {
        "success": True,
        "message": f"已提交缓存预热任务: {request.data_type}, 数量: {len(request.items)}"
    }


@router.post("/cache/clear")
async def clear_cache(level: Optional[str] = None):
    """清空缓存"""
    cache_optimizer.clear_cache(level)
    
    return {
        "success": True,
        "message": f"缓存已清空: {level or 'all'}"
    }


@router.get("/cache/policies")
async def get_cache_policies():
    """获取缓存策略"""
    policies = cache_optimizer.get_cache_policies()
    
    return {
        "success": True,
        "policies": policies
    }


@router.post("/cache/policy")
async def set_cache_policy(request: CachePolicyRequest):
    """设置缓存策略"""
    cache_optimizer.set_cache_policy(request.cache_type, request.policy)
    
    return {
        "success": True,
        "message": f"缓存策略已更新: {request.cache_type}"
    }


@router.get("/overview")
async def get_performance_overview():
    """获取性能概览"""
    query_stats = query_optimizer.get_query_stats()
    cache_stats = cache_optimizer.get_cache_stats()
    
    return {
        "success": True,
        "data": {
            "query": {
                "total_queries": query_stats["total_queries"],
                "avg_duration": f"{query_stats['avg_duration']:.3f}s",
                "slow_query_threshold": f"{query_stats['slow_query_threshold']}s"
            },
            "cache": {
                "l1_hit_rate": cache_stats["l1_cache"]["hit_rate"],
                "l2_hit_rate": cache_stats["l2_cache"]["hit_rate"],
                "l3_hit_rate": cache_stats["l3_cache"]["hit_rate"],
                "overall_hit_rate": cache_stats["stats"]["overall_hit_rate"]
            }
        }
    }
