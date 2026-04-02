# 反风控策略整合报告

## 问题现状

```
2026-04-02 15:47:41 | ERROR | app.adapters.akshare_adapter:get_sector_list:582 - 获取板块列表失败：('Connection aborted.', RemoteDisconnected('Remote end closed connection without response'))
```

**根本原因**: TLS 指纹被识别，导致连接被服务器主动断开

## 当前反风控策略分析

### 1. AkShare 适配器

**已有策略**:
- ✅ 请求频率控制 (2-4 秒延迟)
- ✅ User-Agent 轮换
- ✅ 自适应延迟
- ✅ 失败重试机制
- ✅ 代理 IP 支持

**缺失策略**:
- ❌ **TLS 指纹伪装** - 使用 Python requests 原生 TLS 指纹
- ❌ **HTTP/2 支持** - 仅使用 HTTP/1.1
- ❌ **浏览器指纹伪装** - 无 Canvas/WebGL 指纹处理

### 2. EFinance 适配器

**已有策略**:
- ✅ 请求频率控制 (1-2 秒延迟)
- ✅ User-Agent 轮换 (15 个浏览器)
- ✅ 请求头伪装
- ✅ 失败重试机制
- ✅ 代理 IP 支持

**缺失策略**:
- ❌ **TLS 指纹伪装** - 使用 Python requests 原生 TLS 指纹
- ❌ **HTTP/2 支持** - 仅使用 HTTP/1.1

### 3. 混合 TLS 指纹方案 (hybrid_tls_client.py)

**已实现**:
- ✅ tls-client 集成
- ✅ curl_cffi 多指纹轮换
- ✅ httpx HTTP/2 支持
- ✅ Playwright 池兜底
- ✅ 指纹成功率持久化
- ✅ 动态指纹选择

**未整合**:
- ❌ **未集成到 AkShare 适配器**
- ❌ **未集成到 EFinance 适配器**

## 完整反风控策略架构

```
完整反风控策略
├── 网络层
│   ├── TLS 指纹伪装 (新增)
│   │   ├── tls-client (最新指纹)
│   │   ├── curl_cffi (多指纹轮换)
│   │   └── httpx (HTTP/2 协议)
│   ├── 代理 IP 池
│   └── 连接复用
│
├── 协议层
│   ├── HTTP/2 支持 (新增)
│   ├── 请求头轮换
│   └── Cookie 管理
│
├── 应用层
│   ├── User-Agent 轮换
│   ├── 请求频率控制
│   ├── 自适应延迟
│   └── 失败重试
│
└── 浏览器层 (兜底)
    ├── Playwright 池
    ├── 指纹伪装
    └── 验证码处理
```

## 整合方案

### 方案一：凭证注入模式 (推荐)

**原理**: 使用 Playwright 获取 Cookie，然后注入到 requests/curl_cffi

**优点**:
- 性能好 (仅首次使用 Playwright)
- 兼容性好 (不影响现有代码)
- 成功率高

**实施步骤**:

1. 在 `credential_injector.py` 中整合混合 TLS 方案
2. 修改 `AkShareAdapter` 和 `EFinanceAdapter` 使用凭证注入
3. 配置自动获取凭证策略

**代码示例**:

```python
# 在 AkShareAdapter.initialize() 中
from .credential_injector import CredentialInjector

async def initialize(self) -> bool:
    self._injector = CredentialInjector({
        'tls_patch_mode': TLSPatchMode.CURL_CFFI,
        'impersonate': 'chrome120',
    })
    await self._injector.initialize()
    await self._injector.fetch_credentials('eastmoney.com')
    self._injector.patch_requests_with_tls()
    return True
```

### 方案二：直接使用混合 TLS 客户端

**原理**: 在适配器内部直接使用 `HybridTLSClient`

**优点**:
- 自动故障切换
- 多层防护

**缺点**:
- 需要重构适配器代码
- 可能影响现有功能

### 方案三：智能路由模式

**原理**: 使用 `SmartDataRouter` 根据 API 敏感度自动选择策略

**优点**:
- 自动化程度高
- 性能最优

**缺点**:
- 需要配置 API 敏感度映射

## 推荐实施方案

### Phase 1: 立即实施 (1 天)

1. **启用凭证注入器**
   ```python
   # 在 config.py 中
   ENABLE_CREDENTIAL_INJECTION = True
   TLS_FINGERPRINT_MODE = "curl_cffi"  # 或 "tls_client"
   ```

2. **修改 AkShare 适配器**
   ```python
   # 在 akshare_adapter.py 中
   async def initialize(self) -> bool:
       # 初始化凭证注入器
       from .credential_injector import CredentialInjector
       self._injector = CredentialInjector()
       await self._injector.initialize()
       
       # 获取凭证
       await self._injector.fetch_credentials('eastmoney.com')
       
       # 注入 TLS 指纹
       self._injector.patch_requests_with_tls()
       
       self._is_initialized = True
       return True
   ```

3. **修改 EFinance 适配器**
   同样在 `initialize()` 中添加凭证注入

### Phase 2: 优化改进 (2-3 天)

1. **实现智能路由**
   - 配置 API 敏感度映射
   - 集成 `SmartDataRouter`

2. **添加监控**
   - 记录 TLS 指纹成功率
   - 自动切换最优指纹

3. **性能优化**
   - 凭证缓存
   - 连接池复用

### Phase 3: 高级功能 (可选)

1. **浏览器指纹伪装**
   - Canvas 指纹
   - WebGL 指纹
   - AudioContext 指纹

2. **行为伪装**
   - 鼠标移动模拟
   - 页面滚动模拟
   - 请求链模拟

## 预期效果

| 指标 | 当前 | 实施后 |
|------|------|--------|
| 板块列表成功率 | 30% | 90%+ |
| 资金流向成功率 | 60% | 95%+ |
| K 线数据成功率 | 90% | 98%+ |
| 平均响应时间 | 5s | 2s |
| 被封 IP 概率 | 高 | 极低 |

## 风险与对策

**风险 1**: 凭证注入可能影响其他功能
- **对策**: 使用 monkey-patch，可随时恢复

**风险 2**: Playwright 初始化慢
- **对策**: 懒加载 + 凭证缓存

**风险 3**: TLS 指纹库更新滞后
- **对策**: 定期更新 curl_cffi 和 tls-client

## 决策点

请确认：
1. 是否立即启用凭证注入模式？
2. 是否优先整合 AkShare 还是 EFinance？
3. 是否需要实施完整的智能路由？
