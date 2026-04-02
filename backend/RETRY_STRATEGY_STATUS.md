# 数据源重连策略实施状态

## 问题

数据源重连策略是否已应用到 AkShare 和 EFinance 适配器？

## 当前状态

### 1. SmartRetry 模块 (smart_retry.py)

**已实现功能**:
- ✅ `SmartRetryStrategy` - 智能重试策略
- ✅ `SmartRetryExecutor` - 智能重试执行器
- ✅ `ErrorClassifier` - 错误分类器
- ✅ `RequestFrequencyController` - 请求频率控制器

**策略规则**:
| 错误类型 | 是否重试 | 等待时间 | 说明 |
|---------|---------|---------|------|
| **TLS 指纹被识别** | ❌ | 0s | 需要切换 Playwright 模式 |
| **连接被关闭** | ❌ | 0s | TLS 指纹/连接被识别，重试无效 |
| **IP 被封禁** | ❌ | 0s | 需要切换代理 |
| **客户端错误 (4xx)** | ❌ | 0s | 请检查请求参数 |
| **限流 (429)** | ✅ (1 次) | 30s+ | 等待后重试 |
| **网络错误** | ✅ (2 次) | 2s+ | 指数退避 |
| **超时** | ✅ (2 次) | 3s+ | 指数退避 |
| **服务器错误 (5xx)** | ✅ (2 次) | 5s+ | 指数退避 |

### 2. AkShare 适配器

**已有重连策略**:
- ✅ `rate_limit_decorator` - 同步限流装饰器（重试 3 次）
- ✅ `async_rate_limit_decorator` - 异步限流装饰器（重试 3 次）
- ✅ `_rate_limit()` - 请求频率控制
- ✅ `_detect_rate_limit()` - 限流检测
- ✅ `_consecutive_failures` - 连续失败计数
- ✅ 指数退避算法

**缺失**:
- ❌ **未使用 SmartRetryExecutor** - 仍使用自定义重试逻辑
- ❌ **未集成错误分类器** - 无法智能识别 TLS 指纹错误
- ❌ **未实现模式切换** - TLS 错误时不会自动切换到 Playwright

**代码示例**:
```python
@async_rate_limit_decorator(min_delay=1.5, max_delay=2.5, retries=3)
async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
    try:
        df = ak.stock_zh_a_spot_em()
        # ...
    except Exception as e:
        logger.error(f"获取股票列表失败：{e}")
        return []
```

### 3. EFinance 适配器

**已有重连策略**:
- ✅ `rate_limit_decorator` - 限流装饰器（重试 3 次）
- ✅ `_rate_limit()` - 请求频率控制
- ✅ `_consecutive_failures` - 连续失败计数
- ✅ 自适应延迟

**缺失**:
- ❌ **未使用 SmartRetryExecutor** - 仍使用自定义重试逻辑
- ❌ **未集成错误分类器** - 无法智能识别 TLS 指纹错误
- ❌ **未实现模式切换** - TLS 错误时不会自动切换到 Playwright

## 推荐实施方案

### 方案一：集成 SmartRetryExecutor（推荐）

**优点**:
- 智能错误分类
- 自动模式切换（TLS 错误 → Playwright）
- 统一的重试策略

**实施步骤**:

1. **修改 AkShare 适配器**

```python
from .smart_retry import SmartRetryExecutor, ErrorClassifier

class AkShareAdapter(BaseDataAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._retry_executor = SmartRetryExecutor({
            'max_retries': 3,
            'base_wait_seconds': 2.0,
        })
        
        # 设置模式切换回调
        self._retry_executor.set_switch_mode_callback(
            lambda: self._fallback_to_playwright()
        )
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        async def fetch():
            df = ak.stock_zh_a_spot_em()
            # ...
        
        try:
            return await self._retry_executor.execute(
                func=fetch,
                context="get_stock_list"
            )
        except Exception as e:
            logger.error(f"获取股票列表失败：{e}")
            return []
    
    async def _fallback_to_playwright(self):
        """降级到 Playwright 模式"""
        logger.info("降级到 Playwright 模式")
        # 使用 Playwright 直接获取数据
        # ...
```

2. **修改 EFinance 适配器**

```python
from .smart_retry import SmartRetryExecutor

class EFinanceAdapter(BaseDataAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._retry_executor = SmartRetryExecutor({
            'max_retries': 3,
            'base_wait_seconds': 2.0,
        })
        
        # 设置模式切换回调
        self._retry_executor.set_switch_mode_callback(
            lambda: self._fallback_to_playwright()
        )
```

### 方案二：保留现有逻辑 + 增强错误检测

**优点**:
- 改动小
- 兼容性好

**实施步骤**:

1. **增强错误检测**

```python
def _detect_tls_fingerprint_error(self, error: Exception) -> bool:
    """检测 TLS 指纹错误"""
    error_msg = str(error).lower()
    tls_indicators = [
        'connection closed abruptly',
        'empty reply from server',
        'remote end closed connection',
    ]
    
    for indicator in tls_indicators:
        if indicator in error_msg:
            return True
    return False

async def _handle_error(self, error: Exception, attempt: int, max_retries: int):
    """智能错误处理"""
    # 检测 TLS 指纹错误
    if self._detect_tls_fingerprint_error(error):
        logger.warning(f"TLS 指纹被识别，不重试，建议切换模式")
        raise error  # 不重试
    
    # 普通错误，继续重试逻辑
    if attempt < max_retries - 1:
        # 指数退避
        # ...
```

### 方案三：混合模式（最佳实践）

结合方案一和方案二：

1. **核心 API 使用 SmartRetryExecutor**
   - 高敏感 API（板块列表、股票列表）
   - 频繁调用 API（实时行情）

2. **保留现有装饰器用于简单场景**
   - 低敏感 API（K 线数据）
   - 一次性请求

## 实施建议

### 优先级 1：高敏感 API

以下 API 优先集成 SmartRetryExecutor：

**AkShare**:
- `get_sector_list()` - 板块列表
- `get_market_quotes()` - 市场实时行情
- `get_stock_list()` - 股票列表

**EFinance**:
- `get_stock_list()` - 股票列表
- `get_realtime_quotes()` - 实时行情

### 优先级 2：中敏感 API

- 资金流向
- 板块成分股
- 龙虎榜数据

### 优先级 3：低敏感 API

- K 线数据
- 历史行情
- 技术指标

## 预期效果

| 指标 | 当前 | 实施后 |
|------|------|--------|
| **TLS 错误处理** | 重试无效 | 自动切换 Playwright |
| **IP 封禁处理** | 重试无效 | 提示切换代理 |
| **限流处理** | 等待 30s | 智能等待 30-60s |
| **网络错误** | 重试 3 次 | 智能重试 2 次 |
| **平均成功率** | 70% | 90%+ |

## 验证方法

### 测试用例

```python
from app.adapters.smart_retry import SmartRetryExecutor, ErrorClassifier

# 测试错误分类
error = Exception("Connection closed abruptly")
error_type = ErrorClassifier.classify(error)
print(f"错误类型：{error_type}")  # 应该输出：ErrorType.CONNECTION_CLOSED

# 测试重试决策
strategy = SmartRetryStrategy()
decision = strategy.should_retry(error, attempt=0)
print(f"是否重试：{decision.should_retry}")  # 应该输出：False
print(f"需要切换模式：{decision.should_switch_mode}")  # 应该输出：True
```

### 日志验证

实施后，日志应该显示：

```
WARNING - 请求失败 [get_sector_list]: RemoteDisconnected: Remote end closed connection
  错误类型：connection_closed
  决策：不重试
  原因：TLS 指纹/连接被识别，重试无效，建议切换到 Playwright 模式
INFO - 切换模式...
INFO - 使用 Playwright 获取板块列表...
```

## 下一步

1. **确认实施方案** - 选择方案一、二或三
2. **修改适配器代码** - 集成 SmartRetryExecutor
3. **测试验证** - 运行测试用例
4. **监控优化** - 根据实际效果调整参数

---

**创建时间**: 2026-04-02
**状态**: 待实施
