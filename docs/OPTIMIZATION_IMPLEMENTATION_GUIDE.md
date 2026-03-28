# 数据中台优化实施指南

## 🎯 快速开始

本指南帮助你快速实施数据中台优化方案，按优先级排序。

---

## 📋 实施优先级

### 🔴 **P0 - 紧急（立即实施）**

#### 1. 限流熔断机制
**为什么紧急**: 
- 防止数据源故障拖垮整个系统
- 避免触发数据源频率限制
- 保护系统稳定性

**实施步骤**:
```bash
# 1. 创建中间件目录
mkdir backend/app/middleware

# 2. 创建限流器
touch backend/app/middleware/rate_limiter.py
touch backend/app/middleware/circuit_breaker.py

# 3. 复制方案代码
# 从 DATA_MIDDLE_PLATFORM_OPTIMIZATION_PLAN.md 复制相应代码
```

**核心文件**:
- [`backend/app/middleware/rate_limiter.py`](file:///d:/PROJ/Quant/backend/app/middleware/rate_limiter.py) - 令牌桶限流器
- [`backend/app/middleware/circuit_breaker.py`](file:///d:/PROJ/Quant/backend/app/middleware/circuit_breaker.py) - 断路器
- [`backend/app/adapters/factory.py`](file:///d:/PROJ/Quant/backend/app/adapters/factory.py) - 集成保护机制

**预期效果**:
- ✅ 系统过载保护
- ✅ 故障自动隔离
- ✅ 避免频率限制

---

### 🟡 **P1 - 重要（本周实施）**

#### 2. 监控告警系统
**为什么重要**:
- 实时了解系统状态
- 快速发现和处理故障
- 性能瓶颈定位

**实施步骤**:
```bash
# 1. 安装 Prometheus 客户端
pip install prometheus-client

# 2. 创建指标收集器
touch backend/app/middleware/metrics_collector.py

# 3. 创建告警管理器
touch backend/app/middleware/alerter.py

# 4. 配置 Grafana 仪表盘（可选）
```

**核心文件**:
- [`backend/app/middleware/metrics_collector.py`](file:///d:/PROJ/Quant/backend/app/middleware/metrics_collector.py) - 指标收集
- [`backend/app/middleware/alerter.py`](file:///d:/PROJ/Quant/backend/app/middleware/alerter.py) - 告警管理
- [`backend/app/api/v1/endpoints/monitoring.py`](file:///d:/PROJ/Quant/backend/app/api/v1/endpoints/monitoring.py) - 监控 API

**预期效果**:
- ✅ 实时性能监控
- ✅ 故障自动告警
- ✅ 数据质量追踪

---

### 🟢 **P2 - 重要（下周实施）**

#### 3. 智能缓存优化
**为什么重要**:
- 显著提升性能（85%+）
- 减少数据源压力
- 提升用户体验

**实施步骤**:
```bash
# 1. 创建多级缓存
touch backend/app/storage/multi_level_cache.py

# 2. 实现缓存穿透保护
touch backend/app/storage/cache_protection.py

# 3. 实现缓存预热
# 在 services 目录添加 warm_up_cache.py
```

**核心文件**:
- [`backend/app/storage/multi_level_cache.py`](file:///d:/PROJ/Quant/backend/app/storage/multi_level_cache.py) - 多级缓存
- [`backend/app/storage/cache_protection.py`](file:///d:/PROJ/Quant/backend/app/storage/cache_protection.py) - 缓存保护
- [`backend/app/services/cache_warm_up.py`](file:///d:/PROJ/Quant/backend/app/services/cache_warm_up.py) - 缓存预热

**预期效果**:
- ✅ 响应时间 <100ms
- ✅ 缓存命中率 >95%
- ✅ 数据源请求减少 70%

---

### 🔵 **P3 - 优化（后续实施）**

#### 4. 数据血缘追踪
**实施价值**:
- 数据质量可追溯
- 问题定位更快速
- 满足审计要求

**核心文件**:
- [`backend/app/utils/data_lineage.py`](file:///d:/PROJ/Quant/backend/app/utils/data_lineage.py) - 血缘追踪

#### 5. 性能优化
**实施价值**:
- 批量查询性能提升
- 连接资源优化
- 系统吞吐量提升

**核心文件**:
- [`backend/app/services/batch_query.py`](file:///d:/PROJ/Quant/backend/app/services/batch_query.py) - 批量查询
- [`backend/app/storage/connection_pool.py`](file:///d:/PROJ/Quant/backend/app/storage/connection_pool.py) - 连接池

---

## 🛠️ 代码示例

### 快速集成限流熔断

#### 步骤 1: 创建限流器
```python
# backend/app/middleware/rate_limiter.py
import time
from collections import defaultdict
from loguru import logger

class TokenBucketRateLimiter:
    def __init__(self, rate: float, capacity: int):
        self.rate = rate
        self.capacity = capacity
        self._buckets = defaultdict(lambda: {
            "tokens": capacity,
            "last_update": time.time()
        })
    
    async def acquire(self, key: str, tokens: int = 1) -> bool:
        bucket = self._buckets[key]
        now = time.time()
        
        # 添加令牌
        elapsed = now - bucket["last_update"]
        bucket["tokens"] = min(
            self.capacity,
            bucket["tokens"] + elapsed * self.rate
        )
        bucket["last_update"] = now
        
        # 检查令牌
        if bucket["tokens"] >= tokens:
            bucket["tokens"] -= tokens
            return True
        else:
            logger.warning(f"限流：{key} 令牌不足")
            return False

# 全局限流器实例
rate_limiters = {
    "efinance": TokenBucketRateLimiter(rate=10, capacity=60),
    "akshare": TokenBucketRateLimiter(rate=5, capacity=30),
    "baostock": TokenBucketRateLimiter(rate=3, capacity=20),
}
```

#### 步骤 2: 创建断路器
```python
# backend/app/middleware/circuit_breaker.py
from enum import Enum
from datetime import datetime
from loguru import logger

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failure_count = 0
        self._last_failure_time = None
        self._state = CircuitState.CLOSED
    
    async def call(self, func, *args, **kwargs):
        if self._state == CircuitState.OPEN:
            if self._should_try_reset():
                self._state = CircuitState.HALF_OPEN
                logger.info("断路器进入半开状态")
            else:
                raise Exception("断路器已打开")
        
        try:
            result = await func(*args, **kwargs)
            self._failure_count = 0
            if self._state == CircuitState.HALF_OPEN:
                self._state = CircuitState.CLOSED
                logger.info("断路器关闭")
            return result
        except Exception as e:
            self._failure_count += 1
            self._last_failure_time = datetime.now()
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitState.OPEN
                logger.warning(f"断路器打开：{self._failure_count} 次失败")
            raise e
    
    def _should_try_reset(self) -> bool:
        if self._last_failure_time is None:
            return True
        return (datetime.now() - self._last_failure_time).seconds >= self.recovery_timeout

# 全局断路器实例
circuit_breakers = {
    "efinance": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    "akshare": CircuitBreaker(failure_threshold=5, recovery_timeout=60),
    "baostock": CircuitBreaker(failure_threshold=3, recovery_timeout=120),
}
```

#### 步骤 3: 集成到数据源工厂
```python
# backend/app/adapters/factory.py (修改版)
from .middleware.rate_limiter import rate_limiters
from .middleware.circuit_breaker import circuit_breakers

class DataSourceFactory:
    @classmethod
    async def get_kline_with_protection(
        cls,
        source_type: str,
        code: str,
        start_date: str,
        end_date: str
    ):
        # 检查断路器
        breaker = circuit_breakers.get(source_type)
        if breaker and breaker._state == CircuitState.OPEN:
            logger.warning(f"数据源 {source_type} 断路器已打开")
            return None
        
        # 检查限流
        limiter = rate_limiters.get(source_type)
        if limiter and not await limiter.acquire(source_type):
            logger.warning(f"数据源 {source_type} 触发限流")
            return None
        
        # 执行调用
        try:
            adapter = cls.get_adapter(source_type)
            result = await adapter.get_kline(code, start_date, end_date)
            
            if breaker:
                breaker._failure_count = 0
            return result
            
        except Exception as e:
            if breaker:
                await breaker._on_failure() if hasattr(breaker, '_on_failure') else None
            raise e
```

---

## 📊 性能测试

### 测试脚本
```python
# tests/test_optimization.py
import asyncio
import time

async def test_rate_limiter():
    """测试限流器"""
    limiter = rate_limiters["efinance"]
    
    start = time.time()
    success_count = 0
    
    for i in range(100):
        if await limiter.acquire("efinance"):
            success_count += 1
    
    elapsed = time.time() - start
    print(f"限流测试：{success_count}/100 成功，耗时：{elapsed:.2f}s")

async def test_circuit_breaker():
    """测试断路器"""
    breaker = circuit_breakers["efinance"]
    
    async def mock_func():
        raise Exception("模拟失败")
    
    try:
        for i in range(10):
            await breaker.call(mock_func)
    except Exception as e:
        print(f"断路器状态：{breaker._state.value}")

async def main():
    await test_rate_limiter()
    await test_circuit_breaker()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎯 验收标准

### 限流熔断
- [ ] 限流器正常工作，超过阈值拒绝请求
- [ ] 断路器在连续失败后打开
- [ ] 断路器在半开状态能自动恢复
- [ ] 有完整的日志记录

### 监控告警
- [ ] 指标收集正常（请求数、响应时间、成功率）
- [ ] 告警规则触发正常
- [ ] Grafana 仪表盘显示数据
- [ ] 告警通知发送正常

### 缓存优化
- [ ] 多级缓存工作正常
- [ ] 缓存穿透保护生效
- [ ] 缓存预热完成
- [ ] 缓存命中率 >95%

---

## 📚 相关文档

- [优化方案全文](file:///d:/PROJ/Quant/docs/DATA_MIDDLE_PLATFORM_OPTIMIZATION_PLAN.md)
- [架构决策记录](file:///d:/PROJ/Quant/docs/adr/README.md)
- [API 文档](http://localhost:8000/docs)

---

## 🆘 常见问题

### Q1: 限流阈值如何设置？
**A**: 根据数据源的实际承受能力设置：
- EFinance: 10 个/秒（峰值 60）
- AkShare: 5 个/秒（峰值 30）
- Baostock: 3 个/秒（峰值 20）

### Q2: 断路器阈值设置多少合适？
**A**: 建议 5 次连续失败，恢复超时 60 秒。可根据实际情况调整。

### Q3: 缓存预热会不会影响正常请求？
**A**: 不会。预热在后台异步执行，优先级较低。

### Q4: 如何验证优化效果？
**A**: 使用压力测试工具（如 wrk、ab）测试性能指标。

---

**最后更新**: 2026-03-28  
**维护者**: 架构团队
