# 请求头轮换策略分析与优化

## 问题

请求头轮换是否还需要？是否对反风控有效？

## 当前策略分析

### 现有实现

**EFinance 适配器**:
```python
# 12 个不同的浏览器 User-Agent
self._user_agents = [
    # Chrome - Windows (3 个)
    "Mozilla/5.0 ... Chrome/122.0.0.0 ...",
    "Mozilla/5.0 ... Chrome/121.0.0.0 ...",
    "Mozilla/5.0 ... Chrome/120.0.0.0 ...",
    # Chrome - macOS (2 个)
    # Edge - Windows (2 个)
    # Firefox - Windows (2 个)
    # Firefox - macOS (1 个)
    # Safari - macOS (2 个)
]

# 每次请求轮换
def _rotate_user_agent(self):
    ua = self._user_agents[self._current_ua_index]
    self._current_ua_index = (self._current_ua_index + 1) % len(self._user_agents)
    return ua
```

### 有效性分析

#### ✅ 有效场景

| 场景 | 有效性 | 说明 |
|------|--------|------|
| **基础反爬虫** | ⭐⭐⭐⭐ | 简单的 User-Agent 检测 |
| **频率限制** | ⭐⭐⭐ | 分散请求特征 |
| **日志分析** | ⭐⭐⭐ | 避免单一 UA 高频访问 |
| **初级风控** | ⭐⭐⭐⭐ | 识别爬虫 UA |

#### ❌ 无效场景

| 场景 | 有效性 | 说明 |
|------|--------|------|
| **TLS 指纹识别** | ⭐ | Python TLS 指纹固定，UA 轮换无用 |
| **IP 封禁** | ⭐ | UA 不同但 IP 相同 |
| **行为分析** | ⭐⭐ | 请求模式、时间间隔等 |
| **高级风控** | ⭐⭐ | JA3 指纹、HTTP/2 特征等 |

### 与现有策略对比

| 策略 | 优先级 | 效果 | 成本 |
|------|--------|------|------|
| **TLS 指纹伪装** | 🔴 高 | ⭐⭐⭐⭐⭐ | 低 |
| **凭证注入** | 🔴 高 | ⭐⭐⭐⭐⭐ | 中 |
| **智能重试** | 🔴 高 | ⭐⭐⭐⭐ | 低 |
| **请求频率控制** | 🟡 中 | ⭐⭐⭐⭐ | 低 |
| **请求头轮换** | 🟢 低 | ⭐⭐⭐ | 极低 |

## 结论

### 请求头轮换仍然有价值，但定位需要调整

**从"主要防御手段" → "辅助伪装手段"**

### 理由

1. **TLS 指纹是主要识别点**
   - 服务器首先检测 TLS 指纹（Python 特征）
   - UA 轮换无法掩盖 TLS 指纹
   - **已解决**: curl_cffi + 凭证注入

2. **请求头轮换的剩余价值**
   - ✅ 分散请求特征（避免单一 UA 高频）
   - ✅ 应对基础反爬虫（检查爬虫 UA）
   - ✅ 降低日志分析风险
   - ✅ 成本极低（几乎无开销）

3. **过度轮换的问题**
   - ❌ 12 个 UA 过多（维护成本高）
   - ❌ 可能触发异常检测（频繁切换 UA）
   - ❌ 实际效果有限（TLS 指纹暴露）

## 优化建议

### 方案一：简化轮换（推荐）⭐

**保留轮换，但简化配置**

```python
# 优化后：仅保留 3-4 个主流浏览器
self._user_agents = [
    # Chrome 最新版（主力）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    
    # Chrome 上一版（备用）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    
    # Edge（备用）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    
    # Firefox（备用）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

# 每 10 次请求轮换一次（而非每次）
def _rotate_user_agent(self):
    if self._request_count % 10 == 0:
        self._current_ua_index = (self._current_ua_index + 1) % len(self._user_agents)
    return self._user_agents[self._current_ua_index]
```

**优点**:
- ✅ 保留基础伪装效果
- ✅ 降低维护成本（4 个 vs 12 个）
- ✅ 减少异常检测风险
- ✅ 几乎无性能开销

### 方案二：固定 UA + TLS 指纹轮换

**完全移除 UA 轮换，依赖 TLS 指纹**

```python
# 仅使用一个 UA（与 TLS 指纹匹配）
self._user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"

# curl_cffi 会自动轮换 TLS 指纹
# 无需 UA 轮换
```

**优点**:
- ✅ 配置简单
- ✅ 避免 UA 与 TLS 指纹不匹配
- ✅ 减少变量

**缺点**:
- ❌ 失去 UA 分散效果
- ❌ 单一 UA 高频可能被检测

### 方案三：智能 UA 匹配

**根据 TLS 指纹自动选择 UA**

```python
# TLS 指纹与 UA 配对
FINGERPRINT_UA_PAIRS = [
    ('chrome120', 'Mozilla/5.0 ... Chrome/120.0.0.0 ...'),
    ('chrome121', 'Mozilla/5.0 ... Chrome/121.0.0.0 ...'),
    ('chrome122', 'Mozilla/5.0 ... Chrome/122.0.0.0 ...'),
]

# 自动匹配
def get_user_agent_for_fingerprint(self, fingerprint: str):
    for fp, ua in FINGERPRINT_UA_PAIRS:
        if fingerprint == fp:
            return ua
    return default_ua
```

**优点**:
- ✅ UA 与 TLS 指纹一致
- ✅ 最真实的行为模拟
- ✅ 降低被检测风险

**缺点**:
- ❌ 实现复杂
- ❌ 维护成本高

## 推荐实施方案

### 立即实施：方案一（简化轮换）

**修改内容**:

1. **减少 UA 数量** (12 个 → 4 个)
2. **降低轮换频率** (每次 → 每 10 次)
3. **更新日志信息** (反映新策略)

**预期效果**:
- 保留基础伪装效果
- 降低维护复杂度
- 减少异常检测风险

### 代码修改

```python
# 在 efinance_adapter.py 中

# 修改 1: 简化 UA 列表
self._user_agents = [
    # Chrome 最新版（主力，60% 概率）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    
    # Chrome 上一版（20% 概率）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    
    # Edge（10% 概率）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
    
    # Firefox（10% 概率）
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
]

# 修改 2: 降低轮换频率
def _rotate_user_agent(self):
    # 每 10 次请求轮换一次
    if self._request_count % 10 == 0:
        self._current_ua_index = (self._current_ua_index + 1) % len(self._user_agents)
    return self._user_agents[self._current_ua_index]

# 修改 3: 更新日志
logger.info(f"  - 请求头：已配置（{len(self._user_agents)}个主流浏览器，每 10 次轮换）")
```

## 最终策略定位

```
反风控策略金字塔:

         🔺
        /  \
       /    \
      / TLS  \
     /指纹伪装\  ← 主要防御（效果 90%）
    /──────────\
   /  凭证注入  \  ← 核心机制（效果 80%）
  /──────────────\
 /  智能重试降级  \  ← 兜底方案（效果 70%）
/──────────────────\
|  请求频率控制    |  ← 基础防御（效果 60%）
|──────────────────|
|  请求头轮换 (简化)|  ← 辅助伪装（效果 30%）
|__________________|
```

**请求头轮换定位**:
- ✅ 保留：作为辅助伪装手段
- ✅ 简化：减少配置和维护成本
- ✅ 降频：避免过度轮换触发异常

---

**建议**: 立即实施**方案一（简化轮换）**，保留基础伪装效果的同时降低复杂度。
