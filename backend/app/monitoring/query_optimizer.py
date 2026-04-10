"""
查询优化器

提供查询优化、索引管理和查询分析功能
"""
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime, timedelta
from loguru import logger
from functools import wraps
import pandas as pd


class QueryOptimizer:
    """查询优化器"""
    
    def __init__(self):
        self.query_stats: Dict[str, Dict[str, Any]] = {}
        self.slow_query_threshold = 1.0
        self.query_cache: Dict[str, Any] = {}
        self.cache_ttl = 300
        
        self.index_suggestions = {
            "kline": ["code", "date", "volume"],
            "stock_info": ["code", "industry", "sector"],
            "realtime_quote": ["code", "quote_time"]
        }
    
    def track_query(self, query_name: str):
        """
        查询追踪装饰器
        
        用法:
            @query_optimizer.track_query("get_kline")
            async def get_kline(code: str):
                ...
        """
        def decorator(func: Callable):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    
                    duration = time.time() - start_time
                    self._record_query(query_name, duration, True)
                    
                    if duration > self.slow_query_threshold:
                        logger.warning(
                            f"慢查询警告: {query_name}, "
                            f"耗时: {duration:.3f}s"
                        )
                    
                    return result
                
                except Exception as e:
                    duration = time.time() - start_time
                    self._record_query(query_name, duration, False)
                    raise e
            
            return wrapper
        return decorator
    
    def _record_query(self, query_name: str, duration: float, success: bool):
        """记录查询统计"""
        if query_name not in self.query_stats:
            self.query_stats[query_name] = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_duration": 0.0,
                "max_duration": 0.0,
                "min_duration": float("inf"),
                "avg_duration": 0.0,
                "last_call_time": None
            }
        
        stats = self.query_stats[query_name]
        stats["total_calls"] += 1
        stats["total_duration"] += duration
        stats["max_duration"] = max(stats["max_duration"], duration)
        stats["min_duration"] = min(stats["min_duration"], duration)
        stats["avg_duration"] = stats["total_duration"] / stats["total_calls"]
        stats["last_call_time"] = datetime.now().isoformat()
        
        if success:
            stats["successful_calls"] += 1
        else:
            stats["failed_calls"] += 1
    
    async def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        分析查询
        
        返回查询分析结果和建议
        """
        analysis = {
            "query": query[:100] + "..." if len(query) > 100 else query,
            "suggestions": [],
            "estimated_complexity": "medium"
        }
        
        if "SELECT *" in query.upper():
            analysis["suggestions"].append({
                "type": "performance",
                "message": "避免使用 SELECT *，只选择需要的列"
            })
        
        if "WHERE" not in query.upper() and "LIMIT" not in query.upper():
            analysis["suggestions"].append({
                "type": "performance",
                "message": "建议添加 WHERE 条件或 LIMIT 限制结果集"
            })
        
        if "ORDER BY" in query.upper() and "LIMIT" not in query.upper():
            analysis["suggestions"].append({
                "type": "performance",
                "message": "排序操作建议配合 LIMIT 使用"
            })
        
        if "JOIN" in query.upper():
            analysis["estimated_complexity"] = "high"
            analysis["suggestions"].append({
                "type": "performance",
                "message": "JOIN 操作较复杂，确保关联字段有索引"
            })
        
        return analysis
    
    def get_query_stats(self) -> Dict[str, Any]:
        """获取查询统计信息"""
        return {
            "queries": self.query_stats,
            "slow_query_threshold": self.slow_query_threshold,
            "total_queries": sum(s["total_calls"] for s in self.query_stats.values()),
            "avg_duration": sum(s["avg_duration"] for s in self.query_stats.values()) / len(self.query_stats) if self.query_stats else 0
        }
    
    def get_slow_queries(self, threshold: Optional[float] = None) -> List[Dict[str, Any]]:
        """获取慢查询列表"""
        threshold = threshold or self.slow_query_threshold
        slow_queries = []
        
        for query_name, stats in self.query_stats.items():
            if stats["avg_duration"] > threshold:
                slow_queries.append({
                    "query_name": query_name,
                    "avg_duration": stats["avg_duration"],
                    "max_duration": stats["max_duration"],
                    "total_calls": stats["total_calls"]
                })
        
        return sorted(slow_queries, key=lambda x: x["avg_duration"], reverse=True)
    
    def get_index_suggestions(self) -> Dict[str, List[str]]:
        """获取索引建议"""
        return self.index_suggestions
    
    def reset_stats(self):
        """重置统计信息"""
        self.query_stats = {}


query_optimizer = QueryOptimizer()
