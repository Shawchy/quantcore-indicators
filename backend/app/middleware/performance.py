"""
性能监控中间件
用于监控 API 请求性能和资源使用
"""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger
import time
from typing import Dict, Optional
from collections import defaultdict
import asyncio


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.request_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'max_time': 0.0,
            'min_time': float('inf'),
            'slow_count': 0  # 超过 1 秒的请求数
        })
        self.start_time = time.time()
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        stats = {
            'uptime': time.time() - self.start_time,
            'endpoints': {}
        }
        
        for endpoint, data in self.request_stats.items():
            if data['count'] > 0:
                stats['endpoints'][endpoint] = {
                    'count': data['count'],
                    'avg_time': data['total_time'] / data['count'],
                    'max_time': data['max_time'],
                    'min_time': data['min_time'] if data['min_time'] != float('inf') else 0,
                    'slow_count': data['slow_count'],
                    'slow_rate': (data['slow_count'] / data['count'] * 100) if data['count'] > 0 else 0
                }
        
        return stats
    
    def record_request(self, endpoint: str, duration: float):
        """记录请求"""
        stats = self.request_stats[endpoint]
        stats['count'] += 1
        stats['total_time'] += duration
        stats['max_time'] = max(stats['max_time'], duration)
        stats['min_time'] = min(stats['min_time'], duration)
        
        if duration > 1.0:  # 超过 1 秒视为慢请求
            stats['slow_count'] += 1


# 全局性能监控实例
performance_monitor = PerformanceMonitor()


class PerformanceMiddleware(BaseHTTPMiddleware):
    """性能监控中间件"""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        path = request.url.path
        if path.startswith('/docs') or path.startswith('/redoc') or path.startswith('/openapi.json') or path == '/health':
            return await call_next(request)
        
        start_time = time.time()
        
        client_ip = request.client.host if request.client else 'unknown'
        query_params = str(request.query_params) if request.query_params else ''
        
        endpoint = f"{request.method}:{path}"
        logger.info(f"API请求开始: {endpoint} | 客户端: {client_ip} | 参数: {query_params}")
        
        try:
            response = await call_next(request)
            
            duration = time.time() - start_time
            performance_monitor.record_request(endpoint, duration)
            
            status_code = response.status_code
            
            if duration > 1.0:
                logger.warning(
                    f"慢请求: {endpoint} | 状态: {status_code} | 耗时: {duration:.3f}s | 客户端: {client_ip}"
                )
            elif status_code >= 400:
                logger.warning(
                    f"请求异常: {endpoint} | 状态: {status_code} | 耗时: {duration:.3f}s | 客户端: {client_ip}"
                )
            else:
                logger.info(f"API请求完成: {endpoint} | 状态: {status_code} | 耗时: {duration:.3f}s")
            
            response.headers['X-Process-Time'] = str(duration)
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            logger.error(
                f"请求异常: {endpoint} | 耗时: {duration:.3f}s | 客户端: {client_ip} | 错误: {str(e)}"
            )
            raise


async def get_performance_stats() -> Dict:
    """获取性能统计"""
    return performance_monitor.get_stats()


# 定期报告任务（每 5 分钟）
async def periodic_performance_report():
    """定期性能报告"""
    while True:
        await asyncio.sleep(300)  # 5 分钟
        
        stats = await get_performance_stats()
        if stats['endpoints']:
            logger.info("=== 性能统计报告 ===")
            logger.info(f"运行时间：{stats['uptime']:.0f}秒")
            
            # 按平均耗时排序
            sorted_endpoints = sorted(
                stats['endpoints'].items(),
                key=lambda x: x[1]['avg_time'],
                reverse=True
            )[:10]  # TOP 10
            
            for endpoint, data in sorted_endpoints:
                logger.info(
                    f"{endpoint}: "
                    f"请求数={data['count']}, "
                    f"平均={data['avg_time']:.3f}s, "
                    f"最大={data['max_time']:.3f}s, "
                    f"慢请求={data['slow_count']}({data['slow_rate']:.1f}%)"
                )
