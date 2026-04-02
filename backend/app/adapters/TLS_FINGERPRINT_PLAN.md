# TLS 指纹解决方案改进计划

## 一、当前问题分析

### 1. 代码层面问题
- **Bug**: `hybrid_tls_client.py` 中 `TLSClientPool` 缺少 `get_available_fingerprints` 方法
- **重复代码**: `tls_fingerprint.py` 和 `hybrid_tls_client.py` 功能重叠
- **架构分散**: TLS 指纹管理分散在多个文件中

### 2. 技术层面问题
- **高敏感 API 仍被拦截**: A股列表、板块列表等 API 即使使用 TLS 指纹伪装也会失败
- **指纹库更新滞后**: curl_cffi 和 tls-client 的指纹版本可能落后于最新浏览器
- **缺乏自适应机制**: 无法根据服务器响应自动调整指纹策略

### 3. 资源层面问题
- **Playwright 资源消耗大**: 每次请求启动浏览器开销大
- **缺乏连接池**: 没有复用 TLS 连接

## 二、改进方案

### Phase 1: 修复与整合 (优先级: 高)

#### 1.1 修复现有 Bug
```python
# 在 TLSClientPool 中添加方法
def get_available_fingerprints(self) -> List[str]:
    return self._fingerprint_pool.get_available_fingerprints()
```

#### 1.2 统一 TLS 指纹管理架构
```
tls_fingerprint.py (核心)
├── TLSFingerprintPool      # 指纹池管理
├── TLSClientFactory        # 客户端工厂
└── TLSFingerprintInjector  # 注入器

hybrid_tls_client.py (整合)
├── HybridTLSClient         # 统一入口
└── 移除重复代码

smart_router.py (路由)
└── 保持 API 敏感度路由逻辑
```

### Phase 2: 增强指纹伪装 (优先级: 高)

#### 2.1 多层 TLS 指纹策略
```
Layer 1: tls-client (最新指纹)
    └── chrome120, chrome119, firefox120, safari17
    
Layer 2: curl_cffi (稳定指纹)
    └── chrome110-120, firefox110-120, edge101
    
Layer 3: Playwright 池 (兜底)
    └── 预热浏览器实例池
```

#### 2.2 指纹动态轮换
- 每次请求随机选择指纹
- 失败时自动切换指纹
- 记录指纹成功率，优先使用高成功率指纹

#### 2.3 HTTP/2 + TLS 组合
```python
# 使用 httpx 的 HTTP/2 支持
import httpx
client = httpx.Client(http2=True)
```

### Phase 3: 智能自适应 (优先级: 中)

#### 3.1 指纹学习机制
```python
class FingerprintLearner:
    """学习最优指纹"""
    
    def record_result(self, fingerprint: str, api: str, success: bool):
        # 记录指纹对特定 API 的成功率
        
    def get_best_fingerprint(self, api: str) -> str:
        # 返回该 API 最优指纹
```

#### 3.2 服务器响应分析
```python
class ResponseAnalyzer:
    """分析服务器响应，判断是否被识别"""
    
    def analyze(self, response) -> dict:
        return {
            'is_blocked': bool,
            'block_type': 'tls' | 'ip' | 'behavior' | 'none',
            'suggested_action': 'switch_fingerprint' | 'use_playwright' | 'retry'
        }
```

### Phase 4: Playwright 池优化 (优先级: 中)

#### 4.1 浏览器实例池
```python
class PlaywrightPool:
    """浏览器实例池"""
    
    def __init__(self, pool_size: int = 3):
        self._pool = []
        self._available = asyncio.Queue()
        
    async def acquire(self) -> Page:
        # 获取可用页面
        
    async def release(self, page: Page):
        # 释放页面回池
```

#### 4.2 预热机制
- 启动时预创建浏览器实例
- 定期刷新实例防止过期
- 空闲时保持最小实例数

### Phase 5: 高级伪装技术 (优先级: 低)

#### 5.1 JA3 指纹完全模拟
```python
# 使用 tls-client 的自定义 JA3
session = tls_client.Session(
    ja3_string="771,4865-4866-4867-196-192-191,..."
)
```

#### 5.2 请求链模拟
- 模拟真实用户请求顺序
- 先访问首页，再访问 API
- 保持 Cookie 和 Referer 一致性

#### 5.3 行为伪装
- 随机请求间隔
- 模拟鼠标移动
- 模拟页面滚动

## 三、实施步骤

### Step 1: 修复 Bug (立即)
1. 修复 `TLSClientPool.get_available_fingerprints` 方法
2. 测试验证修复

### Step 2: 架构整合 (1-2天)
1. 重构 `tls_fingerprint.py` 为核心模块
2. 简化 `hybrid_tls_client.py`
3. 统一接口

### Step 3: 增强指纹 (2-3天)
1. 实现指纹动态轮换
2. 添加 HTTP/2 支持
3. 实现指纹学习机制

### Step 4: Playwright 池 (1-2天)
1. 实现浏览器实例池
2. 添加预热机制
3. 测试资源消耗

### Step 5: 测试验证 (1天)
1. 测试所有敏感 API
2. 压力测试
3. 资源消耗评估

## 四、预期效果

| 指标 | 当前 | 改进后 |
|------|------|--------|
| 低敏感 API 成功率 | 90% | 95%+ |
| 中敏感 API 成功率 | 60% | 85%+ |
| 高敏感 API 成功率 | 30% | 70%+ |
| 平均响应时间 | 2s | 1.5s |
| Playwright 资源消耗 | 100% | 50% |

## 五、风险与对策

### 风险 1: 指纹库更新滞后
- 对策: 定期更新 curl_cffi 和 tls-client 版本
- 对策: 实现自定义 JA3 字符串支持

### 风险 2: 服务器升级检测机制
- 对策: 多层方案互为备份
- 对策: 监控成功率变化，及时调整

### 风险 3: Playwright 资源消耗
- 对策: 实例池复用
- 对策: 仅在高敏感 API 使用

## 六、决策点

需要确认以下问题：

1. **优先级确认**: 是否先修复 Bug，还是直接重构？
2. **Playwright 池大小**: 建议默认 3 个实例，是否合适？
3. **指纹学习**: 是否需要持久化指纹成功率数据？
4. **HTTP/2 支持**: 是否需要强制启用 HTTP/2？

---

请确认此计划，或提出修改意见。
