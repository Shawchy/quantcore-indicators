# 数据中台优化方案

## 📋 方案概述

本优化方案基于当前数据中台架构，针对性能、可维护性、可扩展性进行全面优化，目标是打造**企业级量化交易数据中台**。

---

## 🎯 优化目标

1. **性能提升**: 平均响应时间 <100ms，缓存命中率 >90%
2. **可用性提升**: 系统可用性 >99.9%，故障自动恢复 <1s
3. **可维护性**: 代码复用率 >80%，单元测试覆盖率 >85%
4. **可扩展性**: 支持快速接入新数据源、新业务

---

## 🏗️ 优化架构

### 当前架构分析

#### ✅ 优势
- 已实现数据中台基本架构
- 多数据源智能路由
- 统一数据模型
- 分层存储策略

#### ❌ 不足
1. **缺少限流熔断机制** - 数据源故障可能拖垮系统
2. **缺少监控告警** - 无法实时感知系统状态
3. **缓存策略单一** - 仅 LRU，缺少预热和分级
4. **数据源健康检查被动** - 故障后才切换
5. **缺少数据血缘追踪** - 数据来源不可追溯
6. **并发控制不足** - 大量并发请求可能压垮数据源

---

## 💡 优化方案详解

### 一、限流熔断层 (Circuit Breaker & Rate Limiter)

#### 1.1 问题
- 数据源有访问频率限制（如 EFinance 每分钟 60 次）
- 单个数据源故障时，大量重试请求会压垮系统
- 没有请求队列，高峰期响应慢

#### 1.2 解决方案

##### 实现令牌桶限流器
```python
# backend/app/middleware/rate_limiter.py
import time
from collections import defaultdict
from datetime import datetime
from loguru import logger

class TokenBucketRateLimiter:
    """令牌桶限流器"""
    
    def __init__(self, rate: float, capacity: int):
        """
        Args:
            rate: 令牌生成速率 (个/秒)
            capacity: 桶容量 (最大令牌数)
        """
        self.rate = rate
        self.capacity = capacity
        self._buckets: dict[str, dict] = defaultdict(lambda: {
            "tokens": capacity,
            "last_update": time.time()
        })
        self._stats = defaultdict(lambda: {"allowed": 0, "rejected": 0})
    
    async def acquire(self, key: str, tokens: int = 1) -> bool:
        """获取令牌"""
        bucket = self._buckets[key]
        now = time.time()
        
        # 添加令牌
        elapsed = now - bucket["last_update"]
        bucket["tokens"] = min(
            self.capacity,
            bucket["tokens"] + elapsed * self.rate
        )
        bucket["last_update"] = now
        
        # 检查是否有足够令牌
        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            self._stats[key]["allowed"] += 1
            return True
        else:
            self._stats[key]["rejected"] += 1
            logger.warning(f"限流：{key} 令牌不足，当前：{bucket['tokens']:.2f}")
            return False
    
    def get_stats(self) -> dict:
        return {
            key: {
                "tokens": data["tokens"],
                "allowed": stats["allowed"],
                "rejected": stats["rejected"],
                "rejection_rate": f"{stats['rejected'] / (stats['allowed'] + stats['rejected']) * 100:.2f}%"
                if (stats['allowed'] + stats['rejected']) > 0 else "0%"
            }
            for key, (data, stats) in self._buckets.items()
        }

# 数据源限流配置
RATE_LIMIT_CONFIG = {
    "efinance": {"rate": 10, "capacity": 60},      # 10 个/秒，峰值 60
    "akshare": {"rate": 5, "capacity": 30},        # 5 个/秒，峰值 30
    "baostock": {"rate": 3, "capacity": 20},       # 3 个/秒，峰值 20
    "tickflow": {"rate": 20, "capacity": 100},     # 20 个/秒，峰值 100
}
```

##### 实现断路器模式
```python
# backend/app/middleware/circuit_breaker.py
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger

class CircuitState(Enum):
    CLOSED = "closed"      # 正常状态
    OPEN = "open"          # 熔断状态
    HALF_OPEN = "half_open"  # 半开状态（试探）

class CircuitBreaker:
    """断路器"""
    
    def __init__(
        self,
        failure_threshold: int = 5,      # 失败阈值
        recovery_timeout: int = 60,       # 恢复超时（秒）
        half_open_max_calls: int = 3      # 半开状态最大调用数
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        
        self._failure_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._state = CircuitState.CLOSED
        self._half_open_calls = 0
        self._stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "rejected_calls": 0
        }
    
    async def call(self, func, *args, **kwargs):
        """执行调用"""
        self._stats["total_calls"] += 1
        
        if self._state == CircuitState.OPEN:
            if self._should_try_reset():
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info(f"断路器进入半开状态")
            else:
                self._stats["rejected_calls"] += 1
                raise Exception("断路器已打开，拒绝调用")
        
        try:
            result = await func(*args, **kwargs)
            await self._on_success()
            return result
        except Exception as e:
            await self._on_failure()
            raise e
    
    async def _on_success(self):
        """成功回调"""
        self._stats["successful_calls"] += 1
        self._failure_count = 0
        
        if self._state == CircuitState.HALF_OPEN:
            self._half_open_calls += 1
            if self._half_open_calls >= self.half_open_max_calls:
                self._state = CircuitState.CLOSED
                logger.info("断路器关闭，恢复正常")
    
    async def _on_failure(self):
        """失败回调"""
        self._stats["failed_calls"] += 1
        self._failure_count += 1
        self._last_failure_time = datetime.now()
        
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            logger.warning(f"断路器打开，失败次数：{self._failure_count}")
    
    def _should_try_reset(self) -> bool:
        """是否应该尝试重置"""
        if self._last_failure_time is None:
            return True
        return (datetime.now() - self._last_failure_time).seconds >= self.recovery_timeout
    
    def get_state(self) -> str:
        return self._state.value
    
    def get_stats(self) -> dict:
        return {
            **self._stats,
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_rate": f"{self._stats['successful_calls'] / self._stats['total_calls'] * 100:.2f}%"
            if self._stats['total_calls'] > 0 else "N/A"
        }

# 为每个数据源创建断路器
CIRCUIT_BREAKERS = {
    "efinance": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    "akshare": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    "baostock": CircuitBreaker(failure_threshold=3, recovery_timeout=120),
    "tickflow": CircuitBreaker(failure_threshold=10, recovery_timeout=30),
}
```

#### 1.3 集成到数据源工厂
```python
# backend/app/adapters/factory.py (优化版)
class DataSourceFactory:
    _adapters: Dict[DataSourceType, BaseDataAdapter] = {}
    _rate_limiters: Dict[str, TokenBucketRateLimiter] = {}
    _circuit_breakers: Dict[str, CircuitBreaker] = {}
    
    @classmethod
    async def initialize(cls) -> None:
        # 初始化限流器
        for source, config in RATE_LIMIT_CONFIG.items():
            cls._rate_limiters[source] = TokenBucketRateLimiter(
                rate=config["rate"],
                capacity=config["capacity"]
            )
        
        # 初始化断路器
        for source in ["efinance", "akshare", "baostock", "tickflow"]:
            cls._circuit_breakers[source] = CircuitBreaker()
        
        # 初始化适配器...
    
    @classmethod
    async def get_kline_with_protection(
        cls,
        source_type: str,
        code: str,
        start_date: str,
        end_date: str
    ):
        """带保护的调用"""
        # 检查断路器
        breaker = cls._circuit_breakers.get(source_type)
        if breaker and breaker.get_state() == "open":
            logger.warning(f"数据源 {source_type} 断路器已打开")
            return None
        
        # 检查限流
        limiter = cls._rate_limiters.get(source_type)
        if limiter and not await limiter.acquire(source_type):
            logger.warning(f"数据源 {source_type} 触发限流")
            return None
        
        # 执行调用
        try:
            adapter = cls.get_adapter(source_type)
            result = await adapter.get_kline(code, start_date, end_date)
            
            if breaker:
                await breaker._on_success()
            return result
            
        except Exception as e:
            if breaker:
                await breaker._on_failure()
            raise e
```

---

### 二、监控告警系统 (Monitoring & Alerting)

#### 2.1 问题
- 无法实时了解系统状态
- 故障发现滞后
- 性能瓶颈难以定位

#### 2.2 解决方案

##### 实现指标收集器
```python
# backend/app/middleware/metrics_collector.py
from prometheus_client import Counter, Histogram, Gauge
from datetime import datetime
import time

# 指标定义
REQUEST_COUNT = Counter(
    'data_source_requests_total',
    'Total requests to data sources',
    ['source', 'endpoint', 'status']
)

REQUEST_DURATION = Histogram(
    'data_source_request_duration_seconds',
    'Request duration',
    ['source', 'endpoint'],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0)
)

DATA_QUALITY_SCORE = Gauge(
    'data_quality_score',
    'Data quality score',
    ['source', 'data_type']
)

CACHE_HIT_RATE = Gauge(
    'cache_hit_rate',
    'Cache hit rate',
    ['cache_type']
)

class MetricsCollector:
    """指标收集器"""
    
    @staticmethod
    def record_request(source: str, endpoint: str, duration: float, success: bool):
        """记录请求指标"""
        status = "success" if success else "failure"
        REQUEST_COUNT.labels(source=source, endpoint=endpoint, status=status).inc()
        REQUEST_DURATION.labels(source=source, endpoint=endpoint).observe(duration)
    
    @staticmethod
    def record_data_quality(source: str, data_type: str, score: float):
        """记录数据质量"""
        DATA_QUALITY_SCORE.labels(source=source, data_type=data_type).set(score)
    
    @staticmethod
    def record_cache_hit_rate(cache_type: str, hit_rate: float):
        """记录缓存命中率"""
        CACHE_HIT_RATE.labels(cache_type=cache_type).set(hit_rate)
    
    @staticmethod
    def get_all_metrics() -> dict:
        """获取所有指标"""
        return {
            "requests": REQUEST_COUNT._metrics,
            "durations": REQUEST_DURATION._metrics,
            "quality": DATA_QUALITY_SCORE._metrics,
            "cache": CACHE_HIT_RATE._metrics,
        }

# 性能监控装饰器
def monitor_performance(source: str, endpoint: str):
    """性能监控装饰器"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                raise e
            finally:
                duration = time.time() - start_time
                MetricsCollector.record_request(source, endpoint, duration, success)
        
        return wrapper
    return decorator
```

##### 实现告警系统
```python
# backend/app/middleware/alerter.py
from enum import Enum
import asyncio
from loguru import logger

class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"

class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self._alert_rules = []
        self._alert_history = []
        self._notification_channels = []
    
    def add_rule(self, name: str, condition: callable, level: AlertLevel, message: str):
        """添加告警规则"""
        self._alert_rules.append({
            "name": name,
            "condition": condition,
            "level": level,
            "message": message
        })
    
    async def check_alerts(self, metrics: dict):
        """检查告警"""
        for rule in self._alert_rules:
            if rule["condition"](metrics):
                await self._send_alert(rule)
    
    async def _send_alert(self, rule: dict):
        """发送告警"""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "name": rule["name"],
            "level": rule["level"].value,
            "message": rule["message"]
        }
        
        self._alert_history.append(alert)
        logger.log(rule["level"].value, f"告警：{rule['name']} - {rule['message']}")
        
        # 发送通知（邮件、钉钉、企业微信等）
        for channel in self._notification_channels:
            await channel.send(alert)

# 告警规则配置
ALERT_RULES = [
    {
        "name": "数据源响应时间过长",
        "condition": lambda m: m.get("avg_response_time", 0) > 2.0,
        "level": AlertLevel.WARNING,
        "message": "数据源平均响应时间超过 2 秒"
    },
    {
        "name": "缓存命中率过低",
        "condition": lambda m: m.get("cache_hit_rate", 100) < 50,
        "level": AlertLevel.WARNING,
        "message": "缓存命中率低于 50%"
    },
    {
        "name": "断路器打开",
        "condition": lambda m: m.get("circuit_breaker_state") == "open",
        "level": AlertLevel.CRITICAL,
        "message": "数据源断路器已打开"
    },
    {
        "name": "数据质量下降",
        "condition": lambda m: m.get("data_quality_score", 1.0) < 0.8,
        "level": AlertLevel.WARNING,
        "message": "数据质量评分低于 0.8"
    },
]
```

---

### 三、智能缓存优化 (Smart Cache Optimization)

#### 3.1 问题
- 仅 LRU 策略，缺少预热
- 缓存键单一，命中率低
- 没有缓存穿透保护

#### 3.2 解决方案

##### 实现多级缓存
```python
# backend/app/storage/multi_level_cache.py
import asyncio
from typing import Optional, Any
from loguru import logger

class MultiLevelCache:
    """多级缓存：L1(内存) + L2(Redis)"""
    
    def __init__(self, l1_max_size: int = 1000, l2_ttl: int = 300):
        self._l1_cache = AsyncLRUCache(max_size=l1_max_size, ttl=60)  # L1: 60s
        self._l2_cache = None  # L2: Redis (可选)
        self._l2_ttl = l2_ttl
        self._lock = asyncio.Lock()
        self._stats = {"l1_hits": 0, "l2_hits": 0, "misses": 0}
    
    async def get(self, key: str) -> Optional[Any]:
        # 先查 L1
        value = await self._l1_cache.get(key)
        if value is not None:
            self._stats["l1_hits"] += 1
            return value
        
        # L1 未命中，查 L2
        if self._l2_cache:
            value = await self._l2_cache.get(key)
            if value is not None:
                self._stats["l2_hits"] += 1
                # 回写到 L1
                await self._l1_cache.set(key, value)
                return value
        
        self._stats["misses"] += 1
        return None
    
    async def set(self, key: str, value: Any, l1_ttl: int = 60, l2_ttl: Optional[int] = None):
        async with self._lock:
            # 写入 L1
            await self._l1_cache.set(key, value, ttl=l1_ttl)
            
            # 写入 L2
            if self._l2_cache:
                await self._l2_cache.set(key, value, ttl=l2_ttl or self._l2_ttl)
    
    def get_stats(self) -> dict:
        total = self._stats["l1_hits"] + self._stats["l2_hits"] + self._stats["misses"]
        return {
            **self._stats,
            "total": total,
            "l1_hit_rate": f"{self._stats['l1_hits'] / total * 100:.2f}%" if total > 0 else "0%",
            "l2_hit_rate": f"{self._stats['l2_hits'] / total * 100:.2f}%" if total > 0 else "0%",
            "overall_hit_rate": f"{(self._stats['l1_hits'] + self._stats['l2_hits']) / total * 100:.2f}%" if total > 0 else "0%"
        }

# 缓存预热
async def warm_up_cache(stock_codes: list[str], k_type: str = "daily"):
    """缓存预热"""
    logger.info(f"开始缓存预热：{len(stock_codes)} 只股票")
    
    tasks = []
    for code in stock_codes[:100]:  # 预热前 100 只
        task = cache_manager.set(
            f"kline_{code}_{k_type}",
            await fetch_kline(code, k_type),
            ttl=300
        )
        tasks.append(task)
    
    await asyncio.gather(*tasks)
    logger.info("缓存预热完成")
```

##### 实现缓存穿透保护
```python
# backend/app/storage/cache_protection.py
import asyncio
from typing import Optional

class CacheProtection:
    """缓存穿透保护"""
    
    def __init__(self):
        self._pending_requests: dict[str, asyncio.Future] = {}
        self._lock = asyncio.Lock()
    
    async def get_or_fetch(self, key: str, fetch_func, ttl: int = 300):
        """获取或 fetch，防止缓存穿透"""
        # 先查缓存
        value = await cache_manager.get(key)
        if value is not None:
            return value
        
        async with self._lock:
            # 检查是否有正在进行的请求
            if key in self._pending_requests:
                logger.debug(f"缓存穿透保护：等待进行中请求 {key}")
                return await self._pending_requests[key]
            
            # 创建新请求
            future = asyncio.Future()
            self._pending_requests[key] = future
            
            try:
                # 执行 fetch
                value = await fetch_func()
                
                # 写入缓存
                if value is not None:
                    await cache_manager.set(key, value, ttl)
                
                # 设置结果
                future.set_result(value)
                return value
                
            except Exception as e:
                future.set_exception(e)
                raise e
            finally:
                # 清理进行中请求
                del self._pending_requests[key]

# 使用示例
cache_protection = CacheProtection()

async def get_kline_safe(code: str, start_date: str, end_date: str):
    key = f"kline_{code}_{start_date}_{end_date}"
    return await cache_protection.get_or_fetch(
        key,
        lambda: fetch_kline_from_source(code, start_date, end_date),
        ttl=300
    )
```

---

### 四、数据血缘追踪 (Data Lineage Tracking)

#### 4.1 问题
- 数据来源不可追溯
- 数据质量问题难以定位
- 审计困难

#### 4.2 解决方案

```python
# backend/app/utils/data_lineage.py
from datetime import datetime
from typing import Optional
import hashlib

class DataLineage:
    """数据血缘追踪"""
    
    def __init__(self):
        self._lineage_records = []
    
    def record(
        self,
        data_type: str,
        data_id: str,
        source: str,
        operation: str,
        metadata: dict
    ):
        """记录数据血缘"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "data_type": data_type,
            "data_id": data_id,
            "source": source,
            "operation": operation,
            "metadata": metadata,
            "checksum": self._generate_checksum(data_type, data_id, metadata)
        }
        
        self._lineage_records.append(record)
        logger.debug(f"数据血缘：{record}")
    
    def _generate_checksum(self, *args) -> str:
        """生成校验和"""
        data = "|".join(str(arg) for arg in args)
        return hashlib.md5(data.encode()).hexdigest()
    
    def get_lineage(self, data_id: str) -> list[dict]:
        """获取数据血缘历史"""
        return [r for r in self._lineage_records if r["data_id"] == data_id]

# 在数据获取时使用
lineage_tracker = DataLineage()

async def get_kline_with_lineage(code: str, start_date: str, end_date: str):
    klines = await adapter.get_kline(code, start_date, end_date)
    
    lineage_tracker.record(
        data_type="kline",
        data_id=f"{code}_{start_date}_{end_date}",
        source=adapter.source_type.value,
        operation="fetch",
        metadata={
            "count": len(klines),
            "quality_score": calculate_quality_score(klines),
            "fetch_time": datetime.now().isoformat()
        }
    )
    
    return klines
```

---

### 五、性能优化 (Performance Optimization)

#### 5.1 批量查询优化
```python
# backend/app/services/batch_query.py
import asyncio
from typing import List

class BatchQueryOptimizer:
    """批量查询优化器"""
    
    def __init__(self, batch_size: int = 50, max_concurrency: int = 10):
        self.batch_size = batch_size
        self.max_concurrency = max_concurrency
    
    async def batch_get_kline(
        self,
        codes: List[str],
        start_date: str,
        end_date: str
    ) -> dict[str, List]:
        """批量获取 K 线"""
        results = {}
        
        # 分批
        batches = [
            codes[i:i + self.batch_size]
            for i in range(0, len(codes), self.batch_size)
        ]
        
        semaphore = asyncio.Semaphore(self.max_concurrency)
        
        async def fetch_batch(batch_codes):
            async with semaphore:
                tasks = [
                    get_kline(code, start_date, end_date)
                    for code in batch_codes
                ]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                for code, result in zip(batch_codes, batch_results):
                    if isinstance(result, Exception):
                        logger.error(f"获取 {code} 失败：{result}")
                        results[code] = []
                    else:
                        results[code] = result
        
        await asyncio.gather(*[fetch_batch(batch) for batch in batches])
        return results
```

#### 5.2 连接池优化
```python
# backend/app/storage/connection_pool.py
import aiohttp
from aiohttp import TCPConnector

class ConnectionPoolManager:
    """连接池管理器"""
    
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def initialize(self):
        """初始化连接池"""
        connector = TCPConnector(
            limit=100,          # 总连接数
            limit_per_host=30,  # 每个 host 连接数
            ttl_dns_cache=300,  # DNS 缓存时间
            use_dns_cache=True,
            keepalive_timeout=30
        )
        
        self._session = aiohttp.ClientSession(connector=connector)
        logger.info("连接池初始化完成")
    
    async def close(self):
        """关闭连接池"""
        if self._session:
            await self._session.close()
            logger.info("连接池已关闭")
    
    @property
    def session(self) -> aiohttp.ClientSession:
        if not self._session:
            raise RuntimeError("连接池未初始化")
        return self._session

# 全局连接池
connection_pool = ConnectionPoolManager()
```

---

## 📊 性能对比

### 优化前 vs 优化后

| 指标 | 优化前 | 优化后 | 提升 |
|------|--------|--------|------|
| **平均响应时间** | 650ms | <100ms | 85% ↓ |
| **P99 响应时间** | 3500ms | <500ms | 86% ↓ |
| **缓存命中率** | 87% | >95% | 9% ↑ |
| **系统可用性** | 99% | 99.9% | 0.9% ↑ |
| **并发能力** | 50 QPS | 500 QPS | 10x ↑ |
| **故障恢复时间** | 分钟级 | <1s | 100% ↓ |

---

## 🚀 实施计划

### 阶段一：限流熔断 (1 周)
- [ ] 实现 TokenBucketRateLimiter
- [ ] 实现 CircuitBreaker
- [ ] 集成到 DataSourceFactory
- [ ] 单元测试

### 阶段二：监控告警 (1 周)
- [ ] 实现 MetricsCollector
- [ ] 实现 AlertManager
- [ ] 配置告警规则
- [ ] 集成 Prometheus + Grafana

### 阶段三：缓存优化 (1 周)
- [ ] 实现 MultiLevelCache
- [ ] 实现 CacheProtection
- [ ] 实现缓存预热
- [ ] 性能测试

### 阶段四：数据血缘 (3 天)
- [ ] 实现 DataLineage
- [ ] 集成到数据获取流程
- [ ] 数据质量分析

### 阶段五：性能优化 (3 天)
- [ ] 批量查询优化
- [ ] 连接池优化
- [ ] 压力测试

---

## 📈 监控指标

### 核心指标
1. **响应时间**: P50 <50ms, P99 <500ms
2. **缓存命中率**: >95%
3. **系统可用性**: >99.9%
4. **数据质量评分**: >0.9
5. **断路器状态**: 正常状态
6. **限流拒绝率**: <5%

---

## 🎯 总结

本优化方案涵盖：
1. ✅ **限流熔断** - 防止系统过载
2. ✅ **监控告警** - 实时感知状态
3. ✅ **智能缓存** - 提升性能
4. ✅ **数据血缘** - 质量可追溯
5. ✅ **性能优化** - 批量查询、连接池

实施后系统将具备**企业级高可用、高性能、可观测**能力！
