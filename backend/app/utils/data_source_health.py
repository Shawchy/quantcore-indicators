"""
数据源健康检查器

实时监控数据源状态，提供健康检查和故障转移
"""
from typing import Dict, Any, List, Optional
from loguru import logger
import asyncio
from datetime import datetime


class DataSourceHealthChecker:
    """数据源健康检查器"""
    
    def __init__(self, check_interval: int = 300):
        """
        Args:
            check_interval: 检查间隔（秒），默认 5 分钟
        """
        self.health_status: Dict[str, Dict[str, Any]] = {}
        self.check_interval = check_interval
        self._running = False
    
    async def check_all_sources(self) -> Dict[str, Dict[str, Any]]:
        """检查所有数据源的健康状态"""
        # 延迟导入以避免循环依赖
        from app.adapters.factory import DataSourceFactory
        
        factory = DataSourceFactory()
        sources = factory.get_available_sources()
        
        tasks = []
        for source in sources:
            tasks.append(self._check_single_source(source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for source, result in zip(sources, results):
            if isinstance(result, Exception):
                self.health_status[source] = {
                    "status": "error",
                    "error": str(result),
                    "last_check": datetime.now().isoformat()
                }
            else:
                self.health_status[source] = result
        
        logger.info(f"数据源健康检查完成：{self._get_summary()}")
        return self.health_status
    
    async def _check_single_source(self, source: str) -> Dict[str, Any]:
        """检查单个数据源的健康状态"""
        start_time = datetime.now()
        
        try:
            adapter = DataSourceFactory.get_adapter(source)
            
            # 测试查询（使用一个简单接口）
            test_code = "000001"
            
            # 尝试获取股票信息
            stock_info = await adapter.get_stock_info(test_code)
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if stock_info:
                # 检查数据是否有效
                if hasattr(stock_info, 'code') and stock_info.code:
                    return {
                        "status": "healthy",
                        "response_time": response_time,
                        "last_check": datetime.now().isoformat(),
                        "test_result": "success"
                    }
                else:
                    return {
                        "status": "degraded",
                        "response_time": response_time,
                        "last_check": datetime.now().isoformat(),
                        "test_result": "empty_data"
                    }
            else:
                return {
                    "status": "degraded",
                    "response_time": response_time,
                    "last_check": datetime.now().isoformat(),
                    "test_result": "no_data"
                }
                
        except Exception as e:
            response_time = (datetime.now() - start_time).total_seconds()
            logger.warning(f"数据源 {source} 健康检查失败：{e}")
            return {
                "status": "unhealthy",
                "response_time": response_time,
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }
    
    def _get_summary(self) -> str:
        """获取健康检查摘要"""
        healthy = sum(1 for s in self.health_status.values() if s.get("status") == "healthy")
        degraded = sum(1 for s in self.health_status.values() if s.get("status") == "degraded")
        unhealthy = sum(1 for s in self.health_status.values() if s.get("status") in ["unhealthy", "error"])
        
        return f"健康:{healthy}, 降级:{degraded}, 异常:{unhealthy}"
    
    def get_healthy_sources(self) -> List[str]:
        """获取健康的数据源列表"""
        return [
            source for source, status in self.health_status.items()
            if status.get("status") == "healthy"
        ]
    
    def get_best_source(self) -> str:
        """获取最佳数据源（响应时间最短的健康数据源）"""
        healthy = [
            (source, status) 
            for source, status in self.health_status.items()
            if status.get("status") == "healthy"
        ]
        
        if healthy:
            return min(healthy, key=lambda x: x[1].get("response_time", 999))[0]
        
        # 如果没有健康的，返回响应时间最短的非异常数据源
        available = [
            (source, status) 
            for source, status in self.health_status.items()
            if status.get("status") != "error"
        ]
        if available:
            return min(available, key=lambda x: x[1].get("response_time", 999))[0]
        
        # 默认返回 efinance
        return "efinance"
    
    def get_source_priority(
        self,
        preferred_sources: Optional[List[str]] = None
    ) -> List[str]:
        """
        获取排序后的数据源优先级列表
        
        Args:
            preferred_sources: 用户偏好的数据源列表
        
        Returns:
            排序后的数据源列表（优先使用健康的）
        """
        if preferred_sources:
            # 用户指定的优先级
            priority = preferred_sources
        else:
            # 使用默认优先级
            priority = ["efinance", "akshare", "baostock", "tickflow", "tushare"]
        
        # 按健康状态排序
        def sort_key(source: str) -> tuple:
            status = self.health_status.get(source, {}).get("status", "unknown")
            if status == "healthy":
                return (0, priority.index(source) if source in priority else 999)
            elif status == "degraded":
                return (1, priority.index(source) if source in priority else 999)
            else:
                return (2, priority.index(source) if source in priority else 999)
        
        return sorted(priority, key=sort_key)
    
    def is_source_available(self, source: str) -> bool:
        """检查数据源是否可用"""
        status = self.health_status.get(source, {}).get("status")
        return status in ["healthy", "degraded"]
    
    async def start_monitoring(self):
        """启动健康监控（后台任务）"""
        self._running = True
        logger.info("启动数据源健康监控")
        
        while self._running:
            try:
                await self.check_all_sources()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"健康监控异常：{e}")
                await asyncio.sleep(self.check_interval)
    
    def stop_monitoring(self):
        """停止健康监控"""
        self._running = False
        logger.info("停止数据源健康监控")


# 全局健康检查器实例
_health_checker: Optional[DataSourceHealthChecker] = None

def get_health_checker() -> DataSourceHealthChecker:
    """获取全局健康检查器实例"""
    global _health_checker
    if _health_checker is None:
        _health_checker = DataSourceHealthChecker()
    return _health_checker
