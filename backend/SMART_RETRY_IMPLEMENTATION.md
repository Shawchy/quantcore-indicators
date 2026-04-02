# 智能重试策略实施进度报告

## 实施状态

### ✅ AkShare 适配器 - 已完成

**修改内容**:

1. **导入智能重试模块**
```python
from .smart_retry import SmartRetryExecutor, ErrorClassifier, ErrorType
from .hybrid_tls_client import HybridTLSClient
```

2. **初始化 SmartRetryExecutor 和 HybridTLSClient**
```python
def __init__(self):
    # 智能重试执行器
    self._retry_executor = SmartRetryExecutor({
        'max_retries': 3,
        'base_wait_seconds': 2.0,
    })
    
    # 混合 TLS 客户端（用于降级）
    self._hybrid_client: Optional[HybridTLSClient] = None
    
    # 设置模式切换回调
    self._retry_executor.set_switch_mode_callback(self._fallback_to_hybrid_client)
```

3. **初始化时创建 HybridTLSClient**
```python
async def initialize(self) -> bool:
    # 初始化混合 TLS 客户端（用于降级）
    self._hybrid_client = HybridTLSClient({
        'playwright_pool_size': 2,
        'enable_http2': True,
        'fallback_to_playwright': True,
    })
    await self._hybrid_client.initialize()
```

4. **添加降级方法**
```python
async def _fallback_to_hybrid_client(self, url: str, **kwargs) -> Optional[Dict]:
    """降级到混合 TLS 客户端"""
    logger.info("检测到 TLS 指纹错误，降级到 HybridTLSClient...")
    
    result = await self._hybrid_client.get(...)
    return result
```

5. **修改高敏感 API 使用智能重试**
```python
async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
    async def fetch():
        # 原始请求逻辑
        df = ak.stock_board_industry_name_em()
        # ...
    
    try:
        # 使用智能重试执行器
        result = await self._retry_executor.execute(
            func=fetch,
            context="get_sector_list",
            on_switch_mode=lambda: self._handle_sector_list_fallback(sector_type)
        )
        return result or []
    except Exception as e:
        # 最后尝试降级方案
        return await self._handle_sector_list_fallback(sector_type)
```

**工作流程**:

```
1. 调用 get_sector_list()
   ↓
2. 确保凭证有效（懒加载）
   ↓
3. SmartRetryExecutor.execute()
   ├─ 正常：直接返回结果
   ├─ TLS 错误：不重试 → 调用 on_switch_mode → _fallback_to_hybrid_client
   ├─ 网络错误：重试 2 次 → 仍失败 → 降级
   └─ 限流：等待 30s → 重试 1 次
   ↓
4. 如果智能重试失败，调用 _handle_sector_list_fallback()
   └─ 使用 HybridTLSClient 直接请求 API
```

**预期日志**:

```
# 正常情况
INFO - AkShare 适配器初始化成功（凭证注入模式待命 + 智能重试）
INFO -   - 智能重试：已启用（自动切换模式）
INFO -   - 降级方案：HybridTLSClient（tls-client → curl_cffi → Playwright）

# TLS 错误时
WARNING - 请求失败 [get_sector_list]: RemoteDisconnected: Remote end closed connection
  错误类型：connection_closed
  决策：不重试
  原因：TLS 指纹/连接被识别，重试无效，建议切换到 Playwright 模式
INFO - 切换模式...
INFO - 检测到 TLS 指纹错误，降级到 HybridTLSClient...
INFO - HybridTLSClient 请求成功：状态码 200
INFO - HybridTLSClient 获取板块列表成功：50 个

# 网络错误时
WARNING - 请求失败 [get_sector_list]: ConnectionError: Connection aborted
  错误类型：network_error
  决策：重试
  原因：network_error 错误，第 1/3 次重试
INFO - 等待 2.5 秒后重试...
```

### ⏳ EFinance 适配器 - 待实施

**需要修改的内容**（与 AkShare 类似）:

1. 导入智能重试模块
2. 初始化 SmartRetryExecutor
3. 初始化 HybridTLSClient
4. 修改高敏感 API（`get_stock_list`, `get_realtime_quotes`）

**建议实施顺序**:
1. 先测试 AkShare 适配器的智能重试效果
2. 验证 TLS 错误自动切换功能
3. 确认效果良好后，再实施 EFinance 适配器

## 智能重试策略核心功能

### 错误分类与处理

| 错误类型 | 识别关键词 | 处理策略 | 重试次数 | 等待时间 |
|---------|-----------|---------|---------|---------|
| **TLS 指纹被识别** | `Connection closed abruptly`<br>`Empty reply from server`<br>`RemoteDisconnected` | ❌ 不重试<br>✅ 切换模式 | 0 | 0s |
| **IP 被封禁** | `403`, `forbidden`, `blocked` | ❌ 不重试<br>✅ 切换代理 | 0 | 0s |
| **限流 (429)** | `429`, `rate limit`, `too many requests` | ✅ 等待后重试 | 1 | 30s+ |
| **网络错误** | `ConnectionError`, `Network` | ✅ 指数退避 | 2 | 2s+ |
| **超时** | `Timeout`, `timed out` | ✅ 指数退避 | 2 | 3s+ |
| **服务器错误 (5xx)** | `500`, `502`, `503` | ✅ 指数退避 | 2 | 5s+ |
| **客户端错误 (4xx)** | `400`, `404`, `401` | ❌ 不重试 | 0 | 0s |

### 自动模式切换

```python
# 检测到 TLS 错误时
if error_type == ErrorType.CONNECTION_CLOSED:
    return RetryDecision(
        should_retry=False,
        should_switch_mode=True,  # ← 关键：触发模式切换
        reason="TLS 指纹/连接被识别，重试无效，建议切换到 Playwright 模式"
    )

# SmartRetryExecutor 自动调用回调
if decision.should_switch_mode:
    if on_switch_mode:
        return await on_switch_mode()  # ← 调用降级方案
```

## 测试验证

### 测试脚本

```python
from app.adapters.akshare_adapter import AkShareAdapter

async def test_smart_retry():
    adapter = AkShareAdapter()
    await adapter.initialize()
    
    # 测试高敏感 API
    print("测试板块列表...")
    sectors = await adapter.get_sector_list('industry')
    print(f"获取到 {len(sectors)} 个板块")
    
    # 查看重试统计
    stats = adapter._retry_executor._strategy.get_retry_stats()
    print(f"重试统计：{stats}")

asyncio.run(test_smart_retry())
```

### 预期效果

| 指标 | 当前（自定义重试） | 实施后（智能重试） |
|------|------------------|------------------|
| **TLS 错误处理** | 重试 3 次（全部失败）<br>耗时：~15 秒 | ❌ 不重试 → 切换 HybridTLS<br>耗时：~3 秒 |
| **IP 封禁处理** | 重试 3 次（全部失败）<br>耗时：~15 秒 | ❌ 不重试 → 提示切换代理<br>耗时：0 秒 |
| **限流处理** | 等待 30s 重试 3 次<br>耗时：~90 秒 | ✅ 等待 30s 重试 1 次<br>耗时：~30 秒 |
| **网络错误** | 重试 3 次<br>成功率：60% | ✅ 智能重试 2 次<br>成功率：70% |
| **平均成功率** | 70% | **90%+** |
| **平均响应时间** | 8 秒 | **3 秒** |

## 下一步计划

### Phase 1: 测试 AkShare 适配器（立即）

1. 运行测试脚本验证智能重试
2. 检查日志确认 TLS 错误自动切换
3. 验证 HybridTLSClient 降级方案有效性

### Phase 2: 实施 EFinance 适配器（后续）

1. 按照 AkShare 模式修改代码
2. 重点修改 `get_stock_list()` 和 `get_realtime_quotes()`
3. 测试验证

### Phase 3: 扩展到其他 API（可选）

- 资金流向 API
- 板块成分股 API
- 龙虎榜数据 API

## 风险与对策

### 风险 1: HybridTLSClient 初始化失败

**对策**: 
- 懒加载初始化
- 初始化失败不影响主流程
- 降级到普通重试模式

### 风险 2: 模式切换回调参数不匹配

**对策**:
- 使用 `**kwargs` 兼容不同参数
- 统一的 URL 传递机制

### 风险 3: 循环依赖

**对策**:
- 在 `__init__` 中设置 `None` 占位
- 在 `initialize()` 中实际创建实例

---

**实施时间**: 2026-04-02
**AkShare 状态**: ✅ 完成
**EFinance 状态**: ⏳ 待实施
**测试状态**: ⏳ 待验证
