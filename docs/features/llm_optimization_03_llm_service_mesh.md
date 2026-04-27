# 优化模块 3: LLM 服务治理层

## 📊 设计概述

### 问题背景

LLM 服务在生产环境面临:
- **不稳定性**: 模型可能崩溃、超时、OOM
- **高延迟**: 单条推理 100ms+，批量处理更慢
- **无降级**: 失败后直接报错，影响下游
- **无监控**: 不知道服务健康状态
- **难排查**: 出错后无法定位问题

### 解决方案

设计**生产级 LLM 服务治理层**，实现:
- ✅ 优雅降级 (LLM → BERT → 规则 → 默认值)
- ✅ 请求重试 (指数退避)
- ✅ 批量优化 (并发控制 + 分批处理)
- ✅ 结果缓存 (避免重复计算)
- ✅ 健康监控 (实时指标采集)
- ✅ 限流保护 (防止雪崩)

---

## 🏗️ 服务治理架构

```
┌─────────────────────────────────────────────────────────┐
│                    客户端请求                             │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              LLM 服务网关 (Gateway)                       │
│                                                         │
│  1. 请求验证                                             │
│  2. 限流控制 (Rate Limiter)                              │
│  3. 缓存检查 (Cache Lookup)                              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              服务治理层 (Service Mesh)                    │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │重试管理器│  │降级管理器│  │超时管理器│             │
│  │          │  │          │  │          │             │
│  │3 次重试   │  │4 级降级  │  │30 秒超时  │             │
│  │指数退避   │  │LLM→BERT  │  │可配置    │             │
│  │          │  │→规则→默认│  │          │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              LLM 服务实例 (Instances)                     │
│                                                         │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐       │
│  │FinSenti-9B │  │BERT 模型   │  │规则方法    │       │
│  │(主服务)    │  │(备用 1)    │  │(备用 2)    │       │
│  └────────────┘  └────────────┘  └────────────┘       │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              监控与指标 (Monitoring)                      │
│                                                         │
│  - 请求延迟 (P50/P95/P99)                               │
│  - 错误率 (4xx/5xx)                                     │
│  - 缓存命中率                                            │
│  - GPU 利用率                                            │
│  - 降级触发次数                                          │
└─────────────────────────────────────────────────────────┘
```

---

## 💻 核心代码设计

### 1. 服务健康检查器

```python
# backend/app/services/llm_service/health_checker.py

from typing import Optional, Dict
from datetime import datetime, timedelta
from loguru import logger
import asyncio

from .client import LLMClient


class ServiceHealthStatus:
    """服务健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    DOWN = "down"


class LLMHealthChecker:
    """LLM 服务健康检查器"""
    
    def __init__(
        self,
        client: LLMClient,
        check_interval: int = 30,  # 检查间隔 (秒)
        unhealthy_threshold: int = 3,  # 不健康阈值
        recovery_threshold: int = 2  # 恢复阈值
    ):
        self.client = client
        self.check_interval = check_interval
        
        # 状态跟踪
        self._status = ServiceHealthStatus.UNHEALTHY
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._unhealthy_threshold = unhealthy_threshold
        self._recovery_threshold = recovery_threshold
        
        # 统计
        self._stats = {
            "total_checks": 0,
            "successful_checks": 0,
            "failed_checks": 0,
            "last_check_time": None,
            "last_error": None,
        }
    
    async def start_monitoring(self):
        """启动健康监控 (后台任务)"""
        while True:
            try:
                await self.check()
                await asyncio.sleep(self.check_interval)
            except asyncio.CancelledError:
                logger.info("健康检查任务已取消")
                break
            except Exception as e:
                logger.error(f"健康检查异常: {e}")
                await asyncio.sleep(self.check_interval)
    
    async def check(self) -> str:
        """执行一次健康检查"""
        self._stats["total_checks"] += 1
        self._stats["last_check_time"] = datetime.now()
        
        try:
            # 发送测试请求
            start_time = datetime.now()
            response = await self.client.query(
                "你好",
                max_tokens=10
            )
            latency = (datetime.now() - start_time).total_seconds()
            
            # 检查成功
            self._consecutive_successes += 1
            self._consecutive_failures = 0
            
            # 判断是否恢复
            if (self._status != ServiceHealthStatus.HEALTHY and
                self._consecutive_successes >= self._recovery_threshold):
                old_status = self._status
                self._status = ServiceHealthStatus.HEALTHY
                logger.info(
                    f"服务状态恢复: {old_status} → {self._status}"
                )
            
            self._stats["successful_checks"] += 1
            
            return self._status
            
        except Exception as e:
            # 检查失败
            self._consecutive_failures += 1
            self._consecutive_successes = 0
            self._stats["failed_checks"] += 1
            self._stats["last_error"] = str(e)
            
            # 判断是否降级
            if self._consecutive_failures >= self._unhealthy_threshold:
                old_status = self._status
                if self._consecutive_failures < self._unhealthy_threshold * 2:
                    self._status = ServiceHealthStatus.DEGRADED
                elif self._consecutive_failures < self._unhealthy_threshold * 3:
                    self._status = ServiceHealthStatus.UNHEALTHY
                else:
                    self._status = ServiceHealthStatus.DOWN
                
                logger.warning(
                    f"服务状态降级: {old_status} → {self._status} "
                    f"(连续失败: {self._consecutive_failures})"
                )
            
            return self._status
    
    def get_status(self) -> str:
        """获取当前健康状态"""
        return self._status
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self._stats,
            "current_status": self._status,
            "consecutive_failures": self._consecutive_failures,
            "consecutive_successes": self._consecutive_successes,
        }
    
    def is_healthy(self) -> bool:
        """是否健康"""
        return self._status == ServiceHealthStatus.HEALTHY
    
    def should_degrade(self) -> bool:
        """是否应该降级"""
        return self._status in [
            ServiceHealthStatus.UNHEALTHY,
            ServiceHealthStatus.DOWN
        ]
```

---

### 2. 降级管理器

```python
# backend/app/services/llm_service/degradation_manager.py

from typing import Optional, Dict, Any, Callable
from loguru import logger

from .client import LLMClient
from .bert_fallback import BERTSentimentAnalyzer
from .rule_fallback import RuleBasedSentimentAnalyzer


class DegradationLevel:
    """降级级别"""
    LEVEL_0 = "llm_primary"  # LLM 主模型
    LEVEL_1 = "llm_fallback"  # LLM 备用模型
    LEVEL_2 = "bert_fallback"  # BERT 模型
    LEVEL_3 = "rule_fallback"  # 规则方法
    LEVEL_4 = "default_value"  # 默认值


class DegradationManager:
    """降级管理器"""
    
    def __init__(
        self,
        primary_client: LLMClient,
        fallback_client: Optional[LLMClient] = None,
        bert_analyzer: Optional[BERTSentimentAnalyzer] = None,
        rule_analyzer: Optional[RuleBasedSentimentAnalyzer] = None
    ):
        # 各级服务
        self.primary_client = primary_client
        self.fallback_client = fallback_client
        self.bert_analyzer = bert_analyzer
        self.rule_analyzer = rule_analyzer
        
        # 降级策略
        self._degradation_chain = [
            DegradationLevel.LEVEL_0,
            DegradationLevel.LEVEL_1,
            DegradationLevel.LEVEL_2,
            DegradationLevel.LEVEL_3,
            DegradationLevel.LEVEL_4,
        ]
        
        # 统计
        self._stats = {
            "total_requests": 0,
            "degraded_requests": 0,
            "degradation_by_level": {
                level: 0 for level in self._degradation_chain
            },
        }
    
    async def execute_with_degradation(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        执行带降级的请求
        
        Args:
            func: 要执行的函数
            *args, **kwargs: 函数参数
        
        Returns:
            执行结果
        """
        self._stats["total_requests"] += 1
        
        # 逐级尝试
        for level in self._degradation_chain:
            try:
                result = await self._execute_at_level(
                    level, func, *args, **kwargs
                )
                
                # 记录使用的级别
                self._stats["degradation_by_level"][level] += 1
                
                if level != DegradationLevel.LEVEL_0:
                    self._stats["degraded_requests"] += 1
                    logger.warning(f"降级到 {level} 执行成功")
                
                return result
                
            except Exception as e:
                logger.error(f"{level} 执行失败: {e}")
                continue
        
        # 所有级别都失败
        raise RuntimeError("所有降级级别都执行失败")
    
    async def _execute_at_level(
        self,
        level: str,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """在指定级别执行"""
        if level == DegradationLevel.LEVEL_0:
            # LLM 主模型
            if self.primary_client is None:
                raise ValueError("主模型未配置")
            return await func(*args, **kwargs)
        
        elif level == DegradationLevel.LEVEL_1:
            # LLM 备用模型
            if self.fallback_client is None:
                raise ValueError("备用模型未配置")
            return await self.fallback_client.query(*args, **kwargs)
        
        elif level == DegradationLevel.LEVEL_2:
            # BERT 模型
            if self.bert_analyzer is None:
                raise ValueError("BERT 模型未配置")
            return await self.bert_analyzer.analyze(*args, **kwargs)
        
        elif level == DegradationLevel.LEVEL_3:
            # 规则方法
            if self.rule_analyzer is None:
                raise ValueError("规则方法未配置")
            return self.rule_analyzer.analyze(*args, **kwargs)
        
        elif level == DegradationLevel.LEVEL_4:
            # 默认值
            return self._get_default_value()
        
        else:
            raise ValueError(f"未知的降级级别: {level}")
    
    def _get_default_value(self) -> Dict[str, Any]:
        """返回默认值"""
        return {
            "sentiment_score": 0.0,  # 中性
            "event_type": "unknown",
            "impact_scope": "unknown",
            "confidence": 0.0,
            "degraded": True,
            "degradation_level": DegradationLevel.LEVEL_4,
        }
    
    def get_stats(self) -> Dict:
        """获取降级统计"""
        total = self._stats["total_requests"]
        degraded = self._stats["degraded_requests"]
        
        return {
            **self._stats,
            "degradation_rate": degraded / max(1, total),
        }
```

---

### 3. 重试管理器

```python
# backend/app/services/llm_service/retry_manager.py

from typing import Callable, Any, Optional
import asyncio
from loguru import logger


class RetryManager:
    """重试管理器"""
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,  # 基础延迟 (秒)
        max_delay: float = 30.0,  # 最大延迟 (秒)
        exponential_base: float = 2.0,  # 指数底数
        retryable_exceptions: tuple = (
            TimeoutError,
            ConnectionError,
            OSError,
        )
    ):
        """
        Args:
            max_retries: 最大重试次数
            base_delay: 基础延迟
            max_delay: 最大延迟
            exponential_base: 指数底数
            retryable_exceptions: 可重试的异常类型
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.retryable_exceptions = retryable_exceptions
        
        # 统计
        self._stats = {
            "total_attempts": 0,
            "successful_attempts": 0,
            "retried_attempts": 0,
        }
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        带重试的执行
        
        Args:
            func: 要执行的函数 (异步)
            *args, **kwargs: 函数参数
        
        Returns:
            执行结果
        """
        last_exception = None
        
        for attempt in range(self.max_retries + 1):
            self._stats["total_attempts"] += 1
            
            try:
                # 执行函数
                result = await func(*args, **kwargs)
                
                # 成功
                self._stats["successful_attempts"] += 1
                if attempt > 0:
                    self._stats["retried_attempts"] += 1
                
                return result
                
            except self.retryable_exceptions as e:
                last_exception = e
                
                if attempt < self.max_retries:
                    # 计算延迟
                    delay = self._calculate_delay(attempt)
                    
                    logger.warning(
                        f"第 {attempt + 1} 次尝试失败: {e}\n"
                        f"等待 {delay:.1f} 秒后重试..."
                    )
                    
                    # 等待后重试
                    await asyncio.sleep(delay)
                else:
                    logger.error(
                        f"重试 {self.max_retries} 次后仍然失败: {e}"
                    )
            
            except Exception as e:
                # 不可重试的异常，直接抛出
                logger.error(f"不可重试的异常: {e}")
                raise
        
        # 所有重试都失败
        raise last_exception
    
    def _calculate_delay(self, attempt: int) -> float:
        """计算重试延迟 (指数退避 + 抖动)"""
        import random
        
        # 指数退避
        delay = self.base_delay * (self.exponential_base ** attempt)
        
        # 限制最大延迟
        delay = min(delay, self.max_delay)
        
        # 添加随机抖动 (避免惊群效应)
        jitter = random.uniform(0, delay * 0.1)
        delay += jitter
        
        return delay
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        total = self._stats["total_attempts"]
        return {
            **self._stats,
            "retry_rate": (
                self._stats["retried_attempts"] / max(1, total)
            ),
            "success_rate": (
                self._stats["successful_attempts"] / max(1, total)
            ),
        }
```

---

### 4. 结果缓存

```python
# backend/app/services/llm_service/result_cache.py

from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from collections import OrderedDict
import hashlib
from loguru import logger


class LLMResultCache:
    """LLM 结果缓存 (LRU)"""
    
    def __init__(
        self,
        max_size: int = 10000,
        ttl_hours: int = 24
    ):
        """
        Args:
            max_size: 最大缓存条目数
            ttl_hours: 缓存过期时间 (小时)
        """
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        
        # 缓存: {cache_key: (result, expire_time)}
        self._cache: OrderedDict[str, tuple] = OrderedDict()
        
        # 统计
        self._stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
        }
    
    def get(self, text: str, params: Optional[Dict] = None) -> Optional[Any]:
        """获取缓存结果"""
        cache_key = self._generate_key(text, params)
        
        if cache_key in self._cache:
            result, expire_time = self._cache[cache_key]
            
            # 检查是否过期
            if datetime.now() < expire_time:
                # 缓存命中
                self._stats["hits"] += 1
                
                # 移到末尾 (LRU)
                self._cache.move_to_end(cache_key)
                
                return result
            else:
                # 过期，删除
                del self._cache[cache_key]
        
        # 缓存未命中
        self._stats["misses"] += 1
        return None
    
    def put(
        self,
        text: str,
        result: Any,
        params: Optional[Dict] = None
    ):
        """存入缓存结果"""
        cache_key = self._generate_key(text, params)
        expire_time = datetime.now() + self.ttl
        
        # 如果缓存已满，删除最老的
        if len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
            self._stats["evictions"] += 1
        
        self._cache[cache_key] = (result, expire_time)
    
    def _generate_key(
        self,
        text: str,
        params: Optional[Dict] = None
    ) -> str:
        """生成缓存键"""
        key = text
        
        if params:
            # 加入参数
            key += str(sorted(params.items()))
        
        # MD5 哈希
        return hashlib.md5(key.encode()).hexdigest()
    
    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total = self._stats["hits"] + self._stats["misses"]
        
        return {
            **self._stats,
            "hit_rate": (
                self._stats["hits"] / max(1, total)
            ),
            "cache_size": len(self._cache),
        }
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
        logger.info("LLM 结果缓存已清空")
```

---

### 5. 限流保护器

```python
# backend/app/services/llm_service/rate_limiter.py

from typing import Optional
from datetime import datetime, timedelta
from loguru import logger
import asyncio


class TokenBucketRateLimiter:
    """令牌桶限流器"""
    
    def __init__(
        self,
        rate: float = 10.0,  # 每秒请求数
        burst: int = 20  # 突发容量
    ):
        """
        Args:
            rate: 持续速率 (请求/秒)
            burst: 突发容量
        """
        self.rate = rate
        self.burst = burst
        
        # 令牌桶
        self._tokens = float(burst)
        self._last_refill = datetime.now()
        
        # 统计
        self._stats = {
            "total_requests": 0,
            "allowed_requests": 0,
            "rejected_requests": 0,
        }
    
    async def acquire(self, timeout: float = 10.0) -> bool:
        """
        获取令牌
        
        Args:
            timeout: 超时时间 (秒)
        
        Returns:
            bool: 是否成功获取
        """
        self._stats["total_requests"] += 1
        
        start_time = datetime.now()
        
        while True:
            # 补充令牌
            self._refill()
            
            # 检查是否有令牌
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                self._stats["allowed_requests"] += 1
                return True
            
            # 检查超时
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed >= timeout:
                self._stats["rejected_requests"] += 1
                logger.warning("获取令牌超时")
                return False
            
            # 等待后重试
            await asyncio.sleep(0.1)
    
    def _refill(self):
        """补充令牌"""
        now = datetime.now()
        elapsed = (now - self._last_refill).total_seconds()
        
        # 计算新增令牌
        new_tokens = elapsed * self.rate
        
        if new_tokens > 0:
            self._tokens = min(
                self.burst,  # 不超过突发容量
                self._tokens + new_tokens
            )
            self._last_refill = now
    
    def get_stats(self) -> dict:
        """获取统计信息"""
        total = self._stats["total_requests"]
        return {
            **self._stats,
            "rejection_rate": (
                self._stats["rejected_requests"] / max(1, total)
            ),
        }
```

---

### 6. 服务治理主类 (组合所有组件)

```python
# backend/app/services/llm_service/service_mesh.py

from typing import Optional, Dict, Any, List
from loguru import logger
import asyncio

from .client import LLMClient
from .health_checker import LLMHealthChecker
from .degradation_manager import DegradationManager
from .retry_manager import RetryManager
from .result_cache import LLMResultCache
from .rate_limiter import TokenBucketRateLimiter


class LLMServiceMesh:
    """LLM 服务治理 (组合所有组件)"""
    
    def __init__(
        self,
        client: LLMClient,
        enable_cache: bool = True,
        enable_rate_limit: bool = True,
        enable_retry: bool = True,
        enable_degradation: bool = True,
        enable_health_check: bool = True,
    ):
        # 核心客户端
        self.client = client
        
        # 初始化各组件
        self.retry_manager = RetryManager() if enable_retry else None
        self.result_cache = LLMResultCache() if enable_cache else None
        self.rate_limiter = (
            TokenBucketRateLimiter() if enable_rate_limit else None
        )
        
        self.degradation_manager = (
            DegradationManager(client) if enable_degradation else None
        )
        
        self.health_checker = (
            LLMHealthChecker(client) if enable_health_check else None
        )
        
        # 统计
        self._stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "retries": 0,
            "degradations": 0,
            "errors": 0,
        }
    
    async def query(
        self,
        text: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        带治理的查询
        
        Args:
            text: 查询文本
            **kwargs: 其他参数
        
        Returns:
            Dict: 查询结果
        """
        self._stats["total_requests"] += 1
        
        # Step 1: 检查缓存
        if self.result_cache:
            cached = self.result_cache.get(text, kwargs)
            if cached is not None:
                self._stats["cache_hits"] += 1
                return cached
        
        # Step 2: 限流
        if self.rate_limiter:
            acquired = await self.rate_limiter.acquire()
            if not acquired:
                raise RuntimeError("请求被限流")
        
        # Step 3: 执行查询 (带重试和降级)
        try:
            async def _query():
                return await self.client.query(text, **kwargs)
            
            if self.degradation_manager:
                result = await self.degradation_manager.execute_with_degradation(
                    _query
                )
            elif self.retry_manager:
                result = await self.retry_manager.execute_with_retry(
                    _query
                )
            else:
                result = await _query()
            
            # Step 4: 存入缓存
            if self.result_cache:
                self.result_cache.put(text, result, kwargs)
            
            return result
            
        except Exception as e:
            self._stats["errors"] += 1
            logger.error(f"LLM 查询失败: {e}")
            raise
    
    async def batch_query(
        self,
        texts: List[str],
        batch_size: int = 32,
        max_concurrent: int = 4,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        批量查询
        
        Args:
            texts: 文本列表
            batch_size: 每批大小
            max_concurrent: 最大并发数
            **kwargs: 其他参数
        
        Returns:
            List[Dict]: 查询结果列表
        """
        results = []
        
        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            
            # 并发处理批次
            tasks = [
                self.query(text, **kwargs)
                for text in batch
            ]
            
            # 限制并发数
            semaphore = asyncio.Semaphore(max_concurrent)
            
            async def _limited_query(task):
                async with semaphore:
                    return await task
            
            batch_results = await asyncio.gather(
                *[_limited_query(t) for t in tasks],
                return_exceptions=True
            )
            
            # 收集结果
            for result in batch_results:
                if isinstance(result, Exception):
                    results.append({"error": str(result)})
                else:
                    results.append(result)
            
            # 批次间延迟 (避免过载)
            if i + batch_size < len(texts):
                await asyncio.sleep(0.1)
        
        return results
    
    def get_stats(self) -> Dict:
        """获取服务治理统计"""
        total = self._stats["total_requests"]
        
        stats = {
            **self._stats,
            "error_rate": self._stats["errors"] / max(1, total),
        }
        
        # 加入子组件统计
        if self.result_cache:
            stats["cache"] = self.result_cache.get_stats()
        
        if self.retry_manager:
            stats["retry"] = self.retry_manager.get_stats()
        
        if self.rate_limiter:
            stats["rate_limiter"] = self.rate_limiter.get_stats()
        
        if self.health_checker:
            stats["health"] = self.health_checker.get_stats()
        
        return stats
```

---

## 📊 预期效果

### 可靠性提升

| 指标 | 无治理 | 有治理 | 改善 |
|-----|--------|--------|------|
| 可用性 | 95% | 99.9% | +4.9% |
| 错误率 | 5% | < 0.1% | -98% |
| 超时率 | 10% | < 1% | -90% |
| 缓存命中率 | 0% | 30-50% | +50% |

### 降级效果

```
降级统计 (示例):
- LLM 主模型: 8500 次 (85%)
- BERT 降级: 1200 次 (12%)
- 规则降级: 250 次 (2.5%)
- 默认值: 50 次 (0.5%)

平均降级延迟:
- LLM: 100ms
- BERT: 20ms
- 规则: 1ms
- 默认: 0ms
```

---

**文档版本**: v1.0  
**创建时间**: 2026-04-24  
**模块位置**: backend/app/services/llm_service/
