# QuantCore LLM 数据获取完整优化方案

## 📊 文档概览

本文档是 **QuantCore 模块 LLM 数据获取** 的完整优化方案，整合以下内容：

- ✅ **模块 1**: 文本数据源管理管线
- ✅ **模块 2**: 智能文本过滤器
- ✅ **模块 3**: LLM 服务治理层
- ✅ **模块 4**: 文本因子回测验证框架
- ✅ **模块 5**: GPU 显存智能调度器
- ✅ **模块 6**: 因子生命周期管理
- 🆕 **模块 7**: 反风控措施 (新增)

---

## 🎯 问题定义

### 当前 QuantCore 数据获取现状

| 组件 | 现有状态 | 主要问题 |
|------|---------|---------|
| 数据采集 | 依赖 BackendAdapter，失败时生成模拟数据 | 真实数据源覆盖率 < 10% |
| 新闻数据 | 未实现 | 无财经新闻抓取能力 |
| 公告数据 | 未实现 | 无交易所公告爬取能力 |
| 社交媒体 | 仅支持雪球/东财框架，无实际实现 | 舆情数据缺失 |
| 情感分析 | 基于 BERT + 规则方法 | 未集成 LLM，复杂语义理解不足 |
| 反风控 | 无 | 爬虫极易被封禁 |

### 优化目标

```
数据覆盖率: 10% → 85%+
分析精度: 60% → 85%+
因子 IC 值: 0.03 → 0.06-0.08
服务可用性: 95% → 99.9%
年化超额收益: +3-5%
```

---

## 🏗️ 完整架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        数据采集层 (模块 1)                          │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │ 新闻采集  │ │ 公告采集  │ │ 舆情采集  │ │ 研报采集  │          │
│  │(新浪财经) │ │(巨潮资讯) │ │(雪球/东财)│ │(慧博)    │          │
│  │(东方财富) │ │(上交所)   │ │(微博)    │ │(萝卜投研)│          │
│  │(财联社)   │ │(深交所)   │ │(淘股吧)  │ │          │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
│         ↓            ↓            ↓            ↓                │
│  ┌──────────────────────────────────────────────────────┐      │
│  │              反风控层 (模块 7)                         │      │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐             │      │
│  │  │请求伪装   │ │代理池    │ │频率控制   │             │      │
│  │  │浏览器指纹 │ │Cookie池  │ │验证码识别 │             │      │
│  │  └──────────┘ └──────────┘ └──────────┘             │      │
│  └──────────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    智能过滤层 (模块 2)                             │
│                                                                  │
│  原始文本 (58300 条/天) → 去重 → 相关性 → 质量 → 重要性排序       │
│  最终输出: 5000 条/天 (减少 91%)                                 │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    存储层                                         │
│                                                                  │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐          │
│  │实时缓存   │ │日级存储   │ │索引构建   │ │版本管理   │          │
│  │(Redis)   │ │(SQLite)  │ │          │ │          │          │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘          │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LLM 服务层 (模块 3)                            │
│                                                                  │
│  五级降级: LLM → BERT → 规则 → 默认值                            │
│  服务治理: 重试 + 缓存 + 限流 + 健康监控                          │
│  可用性: 99.9%                                                  │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    显存调度层 (模块 5)                            │
│                                                                  │
│  时段调度: 交易/研究/离线                                         │
│  显存峰值: 16GB → 6.5GB                                          │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    因子生产层                                     │
│                                                                  │
│  FinSenti-Qwen3.5-9B (文本因子专用模型)                          │
│  输出: 标准化因子值 (-1 到 +1)                                    │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    验证管理层 (模块 4 + 6)                        │
│                                                                  │
│  回测验证: IC 分析 + 分层回测 + 独立性检验                        │
│  生命周期: 健康监控 + 版本控制 + 失效预警                         │
└─────────────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│                    应用层                                         │
│                                                                  │
│  Alpha 工厂 → 多因子模型 → 组合优化 → 策略回测                    │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 模块详细设计

### 模块 1: 文本数据源管理管线

**详细文档**: [llm_optimization_01_text_data_pipeline.md](file:///d:/PROJ/Quant/docs/llm_optimization_01_text_data_pipeline.md)

#### 核心组件

- **统一数据模型**: `TextItem` (新闻/公告/社交/研报/监管)
- **数据源接口**: `TextDataSource` (可插拔架构)
- **数据源管理器**: `TextDataSourceManager` (健康监控 + 并发查询)
- **数据存储**: `TextDataStorage` (SQLite + 索引)

#### 数据源规划

| 类型 | 数据源 | 更新频率 | 日处理量 | 反风控难度 |
|------|--------|---------|---------|-----------|
| 新闻 | 新浪财经 API | 5 分钟 | 5000 条 | ⭐ |
| 新闻 | 东方财富 | 5 分钟 | 3000 条 | ⭐⭐ |
| 新闻 | 财联社电报 | 1 分钟 | 2000 条 | ⭐⭐ |
| 公告 | 巨潮资讯 | 1 小时 | 200 条 | ⭐⭐⭐ |
| 公告 | 上交所 | 1 小时 | 50 条 | ⭐⭐ |
| 公告 | 深交所 | 1 小时 | 50 条 | ⭐⭐ |
| 社交 | 雪球 | 1 分钟 | 20000 条 | ⭐⭐⭐⭐ |
| 社交 | 东方财富股吧 | 1 分钟 | 15000 条 | ⭐⭐⭐⭐ |
| 社交 | 淘股吧 | 5 分钟 | 10000 条 | ⭐⭐⭐⭐⭐ |
| 研报 | 慧博投研 | 日更 | 50 条 | ⭐⭐⭐ |

#### 关键代码示例

```python
class TextDataSourceManager:
    """文本数据源管理器"""
    
    async def fetch_daily_texts(
        self,
        symbols: List[str],
        date: date,
        sources: Optional[List[str]] = None
    ) -> Dict[TextSourceType, List[TextItem]]:
        """获取指定股票当日的文本数据"""
        # 并发查询所有健康数据源
        tasks = []
        for name in source_names:
            if not self._source_status.get(name, False):
                continue
            source = self._sources[name]
            tasks.append(
                self._fetch_and_deduplicate(source, symbols, date)
            )
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        # 合并 + 去重
        return merged_results
```

---

### 模块 2: 智能文本过滤器

**详细文档**: [llm_optimization_02_smart_text_filter.md](file:///d:/PROJ/Quant/docs/llm_optimization_02_smart_text_filter.md)

#### 四级过滤管线

```
原始文本 (58300)
  ↓ [去重过滤 40%] → MD5 Hash + SimHash + 24h 时间窗口
35000 条
  ↓ [相关性过滤 57%] → 股票代码 + 名称 + 行业板块 + 关注列表
15000 条
  ↓ [质量过滤 33%] → 广告检测 + 垃圾内容 + 文本长度 + 语言检测
10000 条
  ↓ [重要性排序 50%] → 关键词评分 + 来源权重 + 时效性 + 情绪强度
5000 条 (最终输出)
```

#### 核心组件

- `DedupFilter`: 去重 (MD5 + SimHash)
- `RelevanceFilter`: 相关性 (股票代码/名称/行业)
- `QualityFilter`: 质量评估 (广告/垃圾/长度)
- `ImportanceRanker`: 重要性排序 (关键词/来源/时效)

#### 成本节约

| 指标 | 过滤前 | 过滤后 | 改善 |
|------|--------|--------|------|
| 处理量 | 58300 条/天 | 5000 条/天 | -91% |
| API 费用 | 17490 元/月 | 1590 元/月 | -91% |
| 年度节约 | - | 19 万元/年 | - |

---

### 模块 3: LLM 服务治理层

**详细文档**: [llm_optimization_03_llm_service_mesh.md](file:///d:/PROJ/Quant/docs/llm_optimization_03_llm_service_mesh.md)

#### 五级降级策略

```
Level 0: LLM 主模型 (FinSenti-Qwen3.5-9B) ← 100ms
  ↓ 失败
Level 1: LLM 备用模型 (Qwen3.5-9B) ← 100ms
  ↓ 失败
Level 2: BERT 模型 ← 20ms
  ↓ 失败
Level 3: 规则方法 ← 1ms
  ↓ 失败
Level 4: 默认值 (中性因子 = 0.0) ← 0ms
```

#### 核心组件

- `LLMHealthChecker`: 健康监控
- `DegradationManager`: 降级管理
- `RetryManager`: 重试 (指数退避 + 随机抖动)
- `LLMResultCache`: 结果缓存 (LRU + TTL)
- `TokenBucketRateLimiter`: 令牌桶限流
- `LLMServiceMesh`: 服务治理主类

#### 可靠性提升

| 指标 | 无治理 | 有治理 | 改善 |
|------|--------|--------|------|
| 可用性 | 95% | 99.9% | +4.9% |
| 错误率 | 5% | < 0.1% | -98% |
| 缓存命中率 | 0% | 30-50% | +50% |

---

### 模块 4: 文本因子回测验证框架

**详细文档**: [llm_optimization_04_text_factor_backtester.md](file:///d:/PROJ/Quant/docs/llm_optimization_04_text_factor_backtester.md)

#### 五步验证流程

```
Step 1: IC 分析
  - IC 均值 > 0.03 | ICIR > 0.5 | T 值 > 2.0

Step 2: 分层回测
  - 十分组 (Q1-Q10) | 多空收益 > 10%/年 | 单调性检验

Step 3: 风险调整收益
  - 夏普 > 1.0 | 最大回撤 < 20% | Calmar > 1.0

Step 4: 因子独立性
  - 与传统因子相关性 < 0.7 | 增量 R² > 5%

Step 5: 消融实验
  - 逐个移除因子 | 计算贡献度
```

#### 通过标准

| 测试项目 | 优秀 | 良好 | 合格 | 未通过 |
|---------|------|------|------|--------|
| IC 均值 | > 0.05 | 0.03-0.05 | 0.02-0.03 | < 0.02 |
| ICIR | > 1.0 | 0.5-1.0 | 0.3-0.5 | < 0.3 |
| 多空年化 | > 15% | 10-15% | 5-10% | < 5% |
| 夏普比率 | > 2.0 | 1.0-2.0 | 0.5-1.0 | < 0.5 |
| 增量 R² | > 10% | 5-10% | 3-5% | < 3% |

---

### 模块 5: GPU 显存智能调度器

**详细文档**: [llm_optimization_05_gpu_scheduler.md](file:///d:/PROJ/Quant/docs/llm_optimization_05_gpu_scheduler.md)

#### 三时段调度策略

```
交易时段 (9:00-15:00):
  常驻: FinSenti (6.5GB)
  按需: Qwen3.5
  优先级: 低延迟

研究时段 (非交易时间):
  常驻: Qwen3.5 (6.5GB)
  按需: FinSenti
  优先级: 吞吐量

离线时段 (0:00-6:00):
  顺序: FinSenti → Qwen3.5
  优先级: 成本控制
```

#### 效果对比

| 指标 | 无调度 | 有调度 | 改善 |
|------|--------|--------|------|
| OOM 次数 | 频繁 | 0 | -100% |
| 显存峰值 | 16GB | 6.5GB | -60% |
| 模型切换延迟 | N/A | < 5 秒 | 可控 |
| GPU 利用率 | 波动大 | 稳定 | +30% |

---

### 模块 6: 因子生命周期管理

**详细文档**: [llm_optimization_06_factor_lifecycle.md](file:///d:/PROJ/Quant/docs/llm_optimization_06_factor_lifecycle.md)

#### 生命周期阶段

```
创建 → 验证 → 上线 → 监控 → 衰减? → 更新/下线
```

#### 核心组件

- `FactorHealthMonitor`: 健康监控 (IC 衰减检测)
- `FactorVersionControl`: 版本控制
- `FactorUpdateManager`: 更新管理

#### 效果对比

| 场景 | 无监控 | 有监控 | 改善 |
|------|--------|--------|------|
| 因子失效发现时间 | 1-3 个月 | 1-3 天 | 提前 30 倍 |
| 策略损失 | 5-10% | < 1% | 减少 90% |
| 人工检查频率 | 每周 | 自动 | 效率 100 倍 |

---

## 🛡️ 模块 7: 反风控措施 (新增)

### 7.1 风险等级评估

#### 目标网站反风控强度

| 网站 | 反风控等级 | 主要手段 | 应对难度 |
|------|-----------|---------|---------|
| 新浪财经 API | ⭐ 低 | 基础频率限制 | 简单 |
| 东方财富 | ⭐⭐ 中 | Cookie 验证 + 频率限制 | 中等 |
| 财联社 | ⭐⭐ 中 | IP 限制 + Token 验证 | 中等 |
| 巨潮资讯 | ⭐⭐⭐ 中高 | 动态 Token + 参数加密 | 较高 |
| 上交所 | ⭐⭐ 中 | 基础频率限制 | 中等 |
| 深交所 | ⭐⭐ 中 | Cookie + 频率限制 | 中等 |
| 雪球 | ⭐⭐⭐⭐ 高 | 登录验证 + 行为分析 + IP 封禁 | 困难 |
| 东方财富股吧 | ⭐⭐⭐⭐ 高 | JS 加密 + 验证码 + IP 封禁 | 困难 |
| 淘股吧 | ⭐⭐⭐⭐⭐ 极高 | 多重加密 + 行为分析 + 设备指纹 | 极高 |

### 7.2 反风控架构

```
┌─────────────────────────────────────────────────────────┐
│                    反风控防护层                            │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ 请求伪装  │  │ 代理管理  │  │ 频率控制  │             │
│  │          │  │          │  │          │             │
│  │ - UA池   │  │ - 住宅IP │  │ - 高斯   │             │
│  │ - 头信息 │  │ - 数据中 │  │   延迟   │             │
│  │ - Cookie │  │   心IP   │  │ - 随机   │             │
│  │ - 浏览器 │  │ - IP健康 │  │   间隔   │             │
│  │   指纹   │  │   监控   │  │ - 速率   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
│                                                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐             │
│  │ 验证码   │  │ 行为模拟  │  │ 应急处理  │             │
│  │          │  │          │  │          │             │
│  │ - 识别   │  │ - 鼠标   │  │ - 自动   │             │
│  │   服务   │  │   轨迹   │  │   切换   │             │
│  │ - 打码   │  │ - 滚动   │  │   代理   │             │
│  │   平台   │  │ - 点击   │  │ - 降级   │             │
│  │          │  │   模拟   │  │   采集   │             │
│  └──────────┘  └──────────┘  └──────────┘             │
└─────────────────────────────────────────────────────────┘
```

### 7.3 核心反风控组件设计 (基于 QuantCore 实现)

#### 数据模型定义

```python
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict, List

# 代理相关模型
@dataclass
class ProxyInfo:
    ip: str
    port: int
    proxy_type: str  # residential/datacenter/mobile
    username: Optional[str] = None
    password: Optional[str] = None
    status: str = "active"  # active/banned/timeout
    use_count: int = 0
    last_check: Optional[datetime] = None
    
    def is_available(self) -> bool:
        return self.status == "active" and (
            self.last_check is None or 
            (datetime.now() - self.last_check).total_seconds() < 600
        )

@dataclass
class ProxyStats:
    success_rate: float = 100.0
    quality_score: float = 50.0
    avg_latency: float = 0.0  # 秒
    consecutive_fail: int = 0
    success_count: int = 0
    failure_count: int = 0
    anonymity_level: str = "anonymous"
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None

# Cookie 相关模型
@dataclass
class CookieInfo:
    value: Dict[str, str]
    created_at: datetime
    account: str
    use_count: int = 0
    expires_at: Optional[datetime] = None
    
    def is_valid(self) -> bool:
        if self.expires_at:
            return datetime.now() < self.expires_at
        return (datetime.now() - self.created_at).total_seconds() < 3600

@dataclass
class AccountInfo:
    username: str
    password: str
    user_agent: str

# 会话相关模型
@dataclass
class SessionContext:
    site_name: str = ""
    proxy: Optional[ProxyInfo] = None
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Optional[Dict[str, str]] = None
    browser_config: Optional[Dict] = None
    created_at: Optional[datetime] = None

# 统计模型
@dataclass
class SiteAntiDetectionStats:
    success_count: int = 0
    failure_count: int = 0
    ban_count: int = 0
    last_ban_time: Optional[datetime] = None
    
    def to_dict(self) -> Dict:
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "ban_count": self.ban_count,
            "success_rate": self.success_count / max(1, self.success_count + self.failure_count),
        }

# 风险相关模型
class RiskLevel(Enum):
    LOW = "low"           # 0-40 分
    MEDIUM = "medium"     # 40-60 分
    HIGH = "high"         # 60-80 分
    CRITICAL = "critical" # 80-100 分

@dataclass
class RiskAssessment:
    score: float
    level: RiskLevel
    factors: List[str]
    timestamp: datetime
    data_source: str
    recommendation: str = ""

@dataclass
class Adjustment:
    reason: str
    change_interval: bool = False
    new_min_interval: float = 0.0
    new_max_interval: float = 0.0
    enable_extra_check: bool = False
    extra_checks: List[str] = field(default_factory=list)

# 浏览器会话模型
@dataclass
class Credentials:
    domain: str
    cookies: Dict[str, str]
    tokens: Dict[str, str]
    user_agent: str
    obtained_at: datetime
    expires_at: datetime
    
    def is_valid(self) -> bool:
        return datetime.now() < self.expires_at

@dataclass
class TokenExtractorConfig:
    name: str
    type: str  # cookie/js_var/meta
    selector: str

@dataclass
class DomainConfig:
    init_url: str
    refresh_interval: int  # 秒
    required_tokens: List[TokenExtractorConfig] = field(default_factory=list)

@dataclass
class BrowserSession:
    browser: object  # playwright browser
    context: object  # playwright context
    page: object     # playwright page
    domain: str
    created_at: float
    last_used: float

@dataclass
class BrowserStats:
    total_launches: int = 0
    total_closures: int = 0
    active_sessions: int = 0
    credentials_issued: int = 0
```

---

#### 组件 1: 请求头伪装管理器

```python
class RequestHeaderManager:
    """请求头伪装管理器"""
    
    USER_AGENTS = [
        # Chrome Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        
        # Chrome macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        
        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        
        # Edge
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]
    
    PLATFORM_HEADERS = {
        "Windows": {
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-CH-UA-Platform-Version": '"15.0.0"',
        },
        "macOS": {
            "Sec-CH-UA-Platform": '"macOS"',
            "Sec-CH-UA-Platform-Version": '"14.1.1"',
        },
        "Linux": {
            "Sec-CH-UA-Platform": '"Linux"',
            "Sec-CH-UA-Platform-Version": '"5.15.0"',
        },
    }
    
    COMMON_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }
    
    def generate_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """生成完整请求头"""
        ua = random.choice(self.USER_AGENTS)
        
        # 从 UA 推断平台
        platform = self._detect_platform(ua)
        
        headers = {
            "User-Agent": ua,
            **self.COMMON_HEADERS,
            **self.PLATFORM_HEADERS.get(platform, {}),
        }
        
        if referer:
            headers["Referer"] = referer
        
        # 添加 Sec-CH-UA 信息
        headers["Sec-CH-UA"] = self._extract_sec_ch_ua(ua)
        headers["Sec-CH-UA-Mobile"] = "?0"
        
        return headers
    
    def _detect_platform(self, ua: str) -> str:
        """从 User-Agent 检测平台"""
        if "Windows" in ua:
            return "Windows"
        elif "Macintosh" in ua or "Mac OS X" in ua:
            return "macOS"
        elif "Linux" in ua:
            return "Linux"
        return "Windows"
    
    def _extract_sec_ch_ua(self, ua: str) -> str:
        """提取 Sec-CH-UA 信息"""
        if "Chrome" in ua:
            version = re.search(r"Chrome/(\d+)", ua)
            if version:
                major = version.group(1)
                return f'"Not_A Brand";v="8", "Chromium";v="{major}", "Google Chrome";v="{major}"'
        return '"Not_A Brand";v="99", "Chromium";v="120"'
```

#### 组件 2: 代理池管理器

```python
class ProxyPoolManager:
    """代理池管理器"""
    
    PROXY_TYPES = {
        "residential": {
            "priority": "high",
            "sites": ["xueqiu", "eastmoney_guba", "taoguba"],
            "cost": "high",
            "success_rate": 0.95,
        },
        "datacenter": {
            "priority": "medium",
            "sites": ["sina", "eastmoney_news", "cls"],
            "cost": "low",
            "success_rate": 0.85,
        },
        "mobile": {
            "priority": "critical",
            "sites": ["juchao", "sse", "szse"],
            "cost": "very_high",
            "success_rate": 0.98,
        },
    }
    
    def __init__(
        self,
        max_pool_size: int = 100,
        health_check_interval: int = 300,
        ban_threshold: int = 3
    ):
        self.max_pool_size = max_pool_size
        self.health_check_interval = health_check_interval
        self.ban_threshold = ban_threshold
        
        self._pool: List[ProxyInfo] = []
        self._failed_proxies: Dict[str, int] = {}
        self._healthy_proxies: Set[str] = set()
    
    async def get_proxy(self, site_name: str) -> Optional[ProxyInfo]:
        """获取适合指定网站的代理"""
        proxy_type = self._get_proxy_type_for_site(site_name)
        
        # 优先选择健康代理
        healthy = [
            p for p in self._pool
            if p.proxy_type == proxy_type 
            and p.ip in self._healthy_proxies
            and p.is_available()
        ]
        
        if healthy:
            proxy = random.choice(healthy)
            proxy.use_count += 1
            return proxy
        
        # 没有健康代理，从池中随机选择
        available = [
            p for p in self._pool
            if p.proxy_type == proxy_type and p.is_available()
        ]
        
        if available:
            proxy = random.choice(available)
            proxy.use_count += 1
            return proxy
        
        return None
    
    def record_success(self, proxy_ip: str):
        """记录代理成功请求"""
        if proxy_ip in self._failed_proxies:
            self._failed_proxies[proxy_ip] = max(
                0, self._failed_proxies[proxy_ip] - 1
            )
            if self._failed_proxies[proxy_ip] == 0:
                self._healthy_proxies.add(proxy_ip)
    
    def record_failure(self, proxy_ip: str, error_type: str):
        """记录代理失败请求"""
        self._failed_proxies[proxy_ip] = (
            self._failed_proxies.get(proxy_ip, 0) + 1
        )
        
        if self._failed_proxies[proxy_ip] >= self.ban_threshold:
            self._healthy_proxies.discard(proxy_ip)
            
            if "ban" in error_type.lower() or "403" in error_type:
                self._mark_proxy_banned(proxy_ip)
    
    def _get_proxy_type_for_site(self, site_name: str) -> str:
        """根据网站获取代理类型"""
        for proxy_type, config in self.PROXY_TYPES.items():
            if site_name in config["sites"]:
                return proxy_type
        return "datacenter"
    
    def _mark_proxy_banned(self, proxy_ip: str):
        """标记代理被封禁"""
        for proxy in self._pool:
            if proxy.ip == proxy_ip:
                proxy.status = "banned"
                break
    
    async def health_check(self):
        """代理健康检查"""
        for proxy in self._pool:
            if proxy.status == "banned":
                continue
            
            try:
                await self._test_proxy(proxy)
                proxy.last_check = datetime.now()
                self._healthy_proxies.add(proxy.ip)
            except Exception:
                self._healthy_proxies.discard(proxy.ip)
    
    async def _test_proxy(self, proxy: ProxyInfo) -> bool:
        """测试单个代理"""
        test_url = "https://httpbin.org/ip"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(
                test_url,
                proxy=f"http://{proxy.ip}:{proxy.port}",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
```

#### 组件 3: 智能频率控制器

```python
class IntelligentRateLimiter:
    """智能频率控制器"""
    
    SITE_RATE_LIMITS = {
        "sina_news": {
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "delay_distribution": "gaussian",
            "mean_delay": 2.0,
            "std_delay": 0.5,
        },
        "eastmoney_news": {
            "requests_per_minute": 20,
            "requests_per_hour": 300,
            "delay_distribution": "gaussian",
            "mean_delay": 3.0,
            "std_delay": 1.0,
        },
        "juchao": {
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "delay_distribution": "uniform",
            "min_delay": 5.0,
            "max_delay": 15.0,
        },
        "xueqiu": {
            "requests_per_minute": 5,
            "requests_per_hour": 50,
            "delay_distribution": "gaussian",
            "mean_delay": 12.0,
            "std_delay": 3.0,
        },
        "eastmoney_guba": {
            "requests_per_minute": 8,
            "requests_per_hour": 80,
            "delay_distribution": "gaussian",
            "mean_delay": 8.0,
            "std_delay": 2.0,
        },
        "taoguba": {
            "requests_per_minute": 3,
            "requests_per_hour": 30,
            "delay_distribution": "uniform",
            "min_delay": 15.0,
            "max_delay": 30.0,
        },
    }
    
    def __init__(self):
        self._request_history: Dict[str, List[datetime]] = {}
        self._daily_stats: Dict[str, Dict] = {}
    
    async def wait_if_needed(self, site_name: str):
        """根据网站策略等待"""
        config = self.SITE_RATE_LIMITS.get(site_name)
        if not config:
            return
        
        now = datetime.now()
        
        # 检查分钟级限制
        minute_ago = now - timedelta(minutes=1)
        recent_requests = [
            t for t in self._request_history.get(site_name, [])
            if t > minute_ago
        ]
        
        if len(recent_requests) >= config["requests_per_minute"]:
            wait_seconds = 60 - (now - recent_requests[0]).total_seconds()
            logger.warning(
                f"触发 {site_name} 分钟限制，等待 {wait_seconds:.1f} 秒"
            )
            await asyncio.sleep(wait_seconds)
        
        # 检查小时级限制
        hour_ago = now - timedelta(hours=1)
        hour_requests = [
            t for t in self._request_history.get(site_name, [])
            if t > hour_ago
        ]
        
        if len(hour_requests) >= config["requests_per_hour"]:
            wait_seconds = 3600 - (now - hour_requests[0]).total_seconds()
            logger.warning(
                f"触发 {site_name} 小时限制，等待 {wait_seconds:.1f} 秒"
            )
            await asyncio.sleep(wait_seconds)
        
        # 应用延迟 (模拟人类行为)
        delay = self._generate_delay(config)
        if delay > 0:
            await asyncio.sleep(delay)
        
        # 记录请求
        self._request_history.setdefault(site_name, []).append(now)
    
    def _generate_delay(self, config: Dict) -> float:
        """生成延迟 (高斯分布或均匀分布)"""
        dist = config.get("delay_distribution", "gaussian")
        
        if dist == "gaussian":
            delay = random.gauss(
                config["mean_delay"],
                config["std_delay"]
            )
            return max(0.5, delay)
        elif dist == "uniform":
            return random.uniform(
                config["min_delay"],
                config["max_delay"]
            )
        
        return 0
    
    def get_site_stats(self, site_name: str) -> Dict:
        """获取网站请求统计"""
        now = datetime.now()
        history = self._request_history.get(site_name, [])
        
        minute_count = len([t for t in history if t > now - timedelta(minutes=1)])
        hour_count = len([t for t in history if t > now - timedelta(hours=1)])
        
        config = self.SITE_RATE_LIMITS.get(site_name, {})
        
        return {
            "requests_per_minute": minute_count,
            "requests_per_hour": hour_count,
            "limit_per_minute": config.get("requests_per_minute", 0),
            "limit_per_hour": config.get("requests_per_hour", 0),
            "minute_usage": minute_count / max(1, config.get("requests_per_minute", 1)),
            "hour_usage": hour_count / max(1, config.get("requests_per_hour", 1)),
        }
```

#### 组件 4: Cookie 池管理器

```python
class CookiePoolManager:
    """Cookie 池管理器 (针对需要登录的网站)"""
    
    def __init__(
        self,
        refresh_interval: int = 3600,
        max_cookies_per_site: int = 10
    ):
        self.refresh_interval = refresh_interval
        self.max_cookies = max_cookies_per_site
        
        self._cookies: Dict[str, List[CookieInfo]] = {}
        self._account_pool: Dict[str, List[AccountInfo]] = {}
    
    async def get_cookie(self, site_name: str) -> Optional[Dict]:
        """获取有效 Cookie"""
        if site_name not in self._cookies:
            await self._refresh_cookies(site_name)
        
        available = [
            c for c in self._cookies[site_name]
            if c.is_valid()
        ]
        
        if available:
            cookie = random.choice(available)
            cookie.use_count += 1
            return cookie.value
        
        # 没有可用 Cookie，刷新
        await self._refresh_cookies(site_name)
        available = self._cookies.get(site_name, [])
        
        if available:
            return available[0].value
        
        return None
    
    async def _refresh_cookies(self, site_name: str):
        """刷新指定网站的 Cookie"""
        accounts = self._account_pool.get(site_name, [])
        
        if not accounts:
            logger.warning(f"网站 {site_name} 没有可用账号")
            return
        
        new_cookies = []
        for account in accounts[:self.max_cookies]:
            try:
                cookie_value = await self._login_and_get_cookie(
                    site_name, account
                )
                if cookie_value:
                    new_cookies.append(CookieInfo(
                        value=cookie_value,
                        created_at=datetime.now(),
                        account=account.username,
                    ))
            except Exception as e:
                logger.error(f"登录失败: {account.username}, 错误: {e}")
        
        self._cookies[site_name] = new_cookies
        logger.info(f"网站 {site_name} 刷新了 {len(new_cookies)} 个 Cookie")
    
    async def _login_and_get_cookie(
        self, site_name: str, account: AccountInfo
    ) -> Optional[Dict]:
        """模拟登录获取 Cookie"""
        login_config = self._get_login_config(site_name)
        
        # 使用 Playwright 模拟浏览器登录
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            
            context = await browser.new_context(
                user_agent=account.user_agent,
                viewport={"width": 1920, "height": 1080},
            )
            
            # 反检测脚本注入
            await context.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            page = await context.new_page()
            
            try:
                # 导航到登录页
                await page.goto(login_config["login_url"], wait_until="networkidle")
                
                # 填写登录表单
                await page.fill(login_config["username_selector"], account.username)
                await page.fill(login_config["password_selector"], account.password)
                
                # 模拟人类行为延迟
                await asyncio.sleep(random.uniform(1, 3))
                
                # 点击登录
                await page.click(login_config["submit_selector"])
                await page.wait_for_load_state("networkidle")
                
                # 提取 Cookie
                cookies = await context.cookies()
                cookie_dict = {c["name"]: c["value"] for c in cookies}
                
                return cookie_dict
                
            except Exception as e:
                logger.error(f"登录过程出错: {e}")
                return None
            finally:
                await browser.close()
```

#### 组件 5: 浏览器指纹伪装

```python
class BrowserFingerprintManager:
    """浏览器指纹伪装器"""
    
    CANVAS_FINGERPRINTS = [
        # 预定义的 Canvas 指纹哈希
        "a1b2c3d4e5f6...",
        "b2c3d4e5f6a1...",
        # ... 更多指纹
    ]
    
    WEBGL_FINGERPRINTS = [
        "Intel Inc. | Intel Iris OpenGL Engine",
        "Google Inc. (Intel) | ANGLE (Intel, Intel(R) Iris(TM) Graphics, OpenGL 4.1)",
        "NVIDIA Corporation | NVIDIA GeForce GTX 1080 Ti OpenGL Engine",
    ]
    
    SCREEN_RESOLUTIONS = [
        {"width": 1920, "height": 1080, "depth": 24},
        {"width": 2560, "height": 1440, "depth": 24},
        {"width": 1366, "height": 768, "depth": 24},
        {"width": 1440, "height": 900, "depth": 24},
    ]
    
    TIMEZONES = [
        "Asia/Shanghai",
    ]
    
    LANGUAGES = [
        ["zh-CN", "zh", "en"],
        ["zh-CN", "zh"],
    ]
    
    async def apply_stealth(self, page) -> None:
        """应用反检测脚本到 Playwright 页面"""
        # 隐藏 webdriver 属性
        await page.add_init_script("""
            // 隐藏 webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            
            // 修改 Chrome 对象
            window.navigator.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // 修改 permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // 修改 plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ]
            });
            
            // 修改 languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en']
            });
        """)
    
    def generate_fingerprint(self) -> Dict:
        """生成浏览器指纹配置"""
        screen = random.choice(self.SCREEN_RESOLUTIONS)
        
        return {
            "user_agent": random.choice(RequestHeaderManager.USER_AGENTS),
            "viewport": {"width": screen["width"], "height": screen["height"]},
            "screen": screen,
            "timezone": random.choice(self.TIMEZONES),
            "languages": random.choice(self.LANGUAGES),
            "webgl": random.choice(self.WEBGL_FINGERPRINTS),
        }
```

#### 组件 6: 反风控主协调器

```python
class AntiDetectionCoordinator:
    """反风控主协调器"""
    
    def __init__(
        self,
        config_path: str = "config/anti_detection.yaml"
    ):
        self.config = self._load_config(config_path)
        
        # 初始化各组件
        self.header_manager = RequestHeaderManager()
        self.proxy_pool = ProxyPoolManager(
            max_pool_size=self.config.get("proxy_pool_size", 100)
        )
        self.rate_limiter = IntelligentRateLimiter()
        self.cookie_pool = CookiePoolManager()
        self.fingerprint_manager = BrowserFingerprintManager()
        
        # 监控统计
        self._stats: Dict[str, SiteAntiDetectionStats] = {}
    
    async def create_session(
        self,
        site_name: str,
        use_browser: bool = False
    ) -> SessionContext:
        """创建反检测会话"""
        context = SessionContext()
        
        # 1. 获取代理
        proxy = await self.proxy_pool.get_proxy(site_name)
        if proxy:
            context.proxy = proxy
        else:
            logger.warning(f"网站 {site_name} 无可用代理")
        
        # 2. 生成请求头
        context.headers = self.header_manager.generate_headers(
            referer=self.config.get("sites", {}).get(site_name, {}).get("referer")
        )
        
        # 3. 获取 Cookie (如果需要)
        if self._needs_cookie(site_name):
            cookie = await self.cookie_pool.get_cookie(site_name)
            if cookie:
                context.cookies = cookie
            else:
                logger.warning(f"网站 {site_name} 无可用 Cookie")
        
        # 4. 配置浏览器 (如果需要)
        if use_browser:
            context.browser_config = self.fingerprint_manager.generate_fingerprint()
        
        # 5. 记录会话
        context.site_name = site_name
        context.created_at = datetime.now()
        
        return context
    
    async def before_request(
        self,
        site_name: str,
        session: SessionContext
    ) -> None:
        """请求前准备"""
        # 1. 应用频率限制
        await self.rate_limiter.wait_if_needed(site_name)
        
        # 2. 检查代理健康
        if session.proxy:
            if not session.proxy.is_available():
                session.proxy = await self.proxy_pool.get_proxy(site_name)
        
        # 3. 检查 Cookie 有效性
        if session.cookies:
            if self._is_cookie_expired(session.cookies):
                session.cookies = await self.cookie_pool.get_cookie(site_name)
    
    async def after_request(
        self,
        site_name: str,
        session: SessionContext,
        response_status: int,
        error: Optional[str] = None
    ) -> None:
        """请求后处理"""
        if response_status == 200:
            # 成功
            if session.proxy:
                self.proxy_pool.record_success(session.proxy.ip)
            
            self._record_success(site_name)
            
        elif response_status == 403 or response_status == 429:
            # 被封禁或限制
            logger.warning(
                f"网站 {site_name} 触发反风控: HTTP {response_status}"
            )
            
            if session.proxy:
                self.proxy_pool.record_failure(
                    session.proxy.ip,
                    f"HTTP_{response_status}"
                )
            
            self._record_failure(site_name, f"HTTP_{response_status}")
            
            # 可能需要切换策略
            await self._handle_ban(site_name, session)
            
        elif error:
            # 其他错误
            if session.proxy:
                self.proxy_pool.record_failure(session.proxy.ip, error)
            
            self._record_failure(site_name, error)
    
    async def _handle_ban(
        self,
        site_name: str,
        session: SessionContext
    ) -> None:
        """处理被封禁的情况"""
        # 1. 立即切换代理
        new_proxy = await self.proxy_pool.get_proxy(site_name)
        if new_proxy:
            session.proxy = new_proxy
            logger.info(f"网站 {site_name} 已切换代理")
        
        # 2. 刷新 Cookie
        if self._needs_cookie(site_name):
            await self.cookie_pool._refresh_cookies(site_name)
        
        # 3. 增加等待时间
        await asyncio.sleep(random.uniform(10, 30))
        
        # 4. 更新该网站的限制参数 (临时降低频率)
        self._temporarily_reduce_rate(site_name)
    
    def _temporarily_reduce_rate(self, site_name: str) -> None:
        """临时降低请求频率"""
        if site_name in self.rate_limiter.SITE_RATE_LIMITS:
            config = self.rate_limiter.SITE_RATE_LIMITS[site_name]
            config["requests_per_minute"] = max(
                1, config["requests_per_minute"] // 2
            )
            config["mean_delay"] = config.get("mean_delay", 2) * 2
            
            logger.warning(
                f"网站 {site_name} 临时降低频率: "
                f"{config['requests_per_minute']} 请求/分钟"
            )
    
    def get_overall_stats(self) -> Dict:
        """获取整体反风控统计"""
        return {
            site: stats.to_dict()
            for site, stats in self._stats.items()
        }
```

---

### 7.3.1 高级反风控组件 (借鉴 Seadex 反风控模块)

> 以下内容从 `D:\PROJ\Seadex\pkg\antifraud` 提取并转换为 Python 实现,为 QuantCore 提供更强大的反风控能力。

#### 组件关系与演进路径

11 个反风控组件分为 **基础版** (组件 1-6) 和 **高级版** (组件 7-11) 两代:

```
┌─────────────────────────────────────────────────────────────┐
│  第一代: 基础组件 (模块 7.3) - Phase 1 实施                  │
│                                                             │
│  组件 1: RequestHeaderManager       (请求头伪装)             │
│  组件 2: ProxyPoolManager           (基础代理池)             │
│  组件 3: IntelligentRateLimiter     (静态频率控制)           │
│  组件 4: CookiePoolManager          (Cookie 池)             │
│  组件 5: BrowserFingerprintManager  (浏览器指纹)             │
│  组件 6: AntiDetectionCoordinator   (基础协调器)             │
│                                                             │
│  特点: 简单实用，覆盖 80% 场景                              │
└─────────────────────────────────────────────────────────────┘
                           ↓ 升级
┌─────────────────────────────────────────────────────────────┐
│  第二代: 高级组件 (模块 7.3.1) - Phase 2 实施                │
│                                                             │
│  组件 7: TLSFingerprintManager      ← 全新 (TLS 指纹混淆)    │
│  组件 8: AdaptiveRateLimiter        ← 替代组件 3 (自适应)    │
│  组件 9: ProxyQualityScorer         ← 增强组件 2 (质量评分)  │
│  组件 10: RiskDecisionEngine        ← 全新 (风险决策)        │
│  组件 11: BrowserSessionManager     ← 增强组件 4/5 (会话管理) │
│                                                             │
│  特点: 智能化，覆盖 98% 场景，自动恢复                       │
└─────────────────────────────────────────────────────────────┘
```

**组件替代关系**:

| 基础组件 | 高级组件 | 关系 | 说明 |
|----------|----------|------|------|
| 组件 3: IntelligentRateLimiter | 组件 8: AdaptiveRateLimiter | **替代** | 高级版增加成功率动态调整、被封惩罚、防突发保护 |
| 组件 2: ProxyPoolManager | 组件 9: ProxyQualityScorer | **增强** | 高级版增加质量评分算法、加权选择、延迟评分 |
| 组件 4: CookiePoolManager | 组件 11: BrowserSessionManager | **整合** | 高级版统一管理会话生命周期、凭证获取、Token 提取 |
| - | 组件 7: TLSFingerprintManager | **全新** | 基础版无 TLS 指纹能力 |
| - | 组件 10: RiskDecisionEngine | **全新** | 基础版无全局风险决策能力 |

**推荐实施策略**:
1. **Phase 1** (Week 1-2): 先部署组件 1-6，快速覆盖基本需求
2. **Phase 2** (Week 3-5): 用组件 7-11 逐步替代/增强基础组件
3. **最终架构**: 组件 1 (保留) + 组件 7 + 组件 8 (替代 3) + 组件 9 (增强 2) + 组件 10 + 组件 11 (整合 4/5) + 组件 6 (升级为统一协调器)

---

#### 组件集成架构

```
┌─────────────────────────────────────────────────────────────────┐
│                    反风控统一协调器 (升级版组件 6)                 │
│                                                                 │
│  AntiDetectionCoordinator (协调器)                               │
│    │                                                            │
│    ├── 请求头伪装 (组件 1: RequestHeaderManager)                │
│    │                                                            │
│    ├── TLS 指纹管理 (组件 7: TLSFingerprintManager) ──┐         │
│    │                                                   │         │
│    ├── 代理池 (组件 2 + 组件 9 质量评分) ←───────┘         │
│    │                                                   │         │
│    ├── 频率控制 (组件 8: AdaptiveRateLimiter) ←─────┘         │
│    │                                                   │         │
│    ├── 风险决策 (组件 10: RiskDecisionEngine) ←──────┘         │
│    │                                                   │         │
│    ├── Cookie/会话 (组件 11: BrowserSessionManager)            │
│    │                                                            │
│    └── 浏览器指纹 (组件 5: BrowserFingerprintManager)           │
└─────────────────────────────────────────────────────────────────┘
```

---

#### 组件 7: TLS 指纹混淆器 (来自 tls_fingerprinter.go)

**原理**: 网站通过 JA3 指纹识别爬虫。不同浏览器的 TLS 握手特征不同,通过动态切换 TLS 配置模拟真实浏览器。

```python
class TLSFingerprintManager:
    """TLS 指纹混淆管理器"""
    
    TLS_PROFILES = {
        "chrome_120_windows": {
            "name": "Chrome 120 on Windows",
            "cipher_suites": [
                "TLS_AES_128_GCM_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
                "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
                "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
            ],
            "curve_preferences": ["X25519", "P256", "P384"],
            "signature_algorithms": [
                "ecdsa_secp256r1_sha256",
                "rsa_pkcs1_sha256",
                "ecdsa_secp384r1_sha384",
                "rsa_pkcs1_sha384",
                "rsa_pkcs1_sha512",
                "ed25519",
            ],
            "ja3_hash": "771,4865-4866-4867-49195-49199-49196-49200,0-23-65281-10-11-35-16-5-51-43-13-45,29-23-24,0",
        },
        "firefox_121_linux": {
            "name": "Firefox 121 on Linux",
            "cipher_suites": [
                "TLS_AES_128_GCM_SHA256",
                "TLS_CHACHA20_POLY1305_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_ECDSA_WITH_CHACHA20_POLY1305_SHA256",
                "TLS_ECDHE_RSA_WITH_CHACHA20_POLY1305_SHA256",
            ],
            "curve_preferences": ["X25519", "P256", "P384", "P521"],
            "signature_algorithms": [
                "ecdsa_secp256r1_sha256",
                "ecdsa_secp384r1_sha384",
                "ecdsa_secp521r1_sha512",
                "rsa_pkcs1_sha256",
                "rsa_pkcs1_sha384",
                "rsa_pkcs1_sha512",
                "ed25519",
            ],
            "ja3_hash": "771,4865-4867-4866-49195-49199-49196-49200-52393-52392,0-23-65281-10-11-35-16-5-51-43-13-45,29-23-24,0",
        },
        "safari_17_macos": {
            "name": "Safari 17 on macOS",
            "cipher_suites": [
                "TLS_AES_128_GCM_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
            ],
            "curve_preferences": ["X25519", "P256", "P384"],
            "signature_algorithms": [
                "ecdsa_secp256r1_sha256",
                "ecdsa_secp384r1_sha384",
                "rsa_pkcs1_sha256",
                "rsa_pkcs1_sha384",
            ],
            "ja3_hash": "771,4865-4866-4867,0-23-65281-10-11-35-16-5-51-43-13-45,29-23-24,0",
        },
        "edge_120_windows": {
            "name": "Edge 120 on Windows (Chromium-based)",
            "cipher_suites": [
                "TLS_AES_128_GCM_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
                "TLS_ECDHE_ECDSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_RSA_WITH_AES_128_GCM_SHA256",
                "TLS_ECDHE_ECDSA_WITH_AES_256_GCM_SHA384",
                "TLS_ECDHE_RSA_WITH_AES_256_GCM_SHA384",
            ],
            "curve_preferences": ["X25519", "P256", "P384"],
            "signature_algorithms": [
                "ecdsa_secp256r1_sha256",
                "rsa_pkcs1_sha256",
                "ecdsa_secp384r1_sha384",
                "rsa_pkcs1_sha384",
                "rsa_pkcs1_sha512",
                "ed25519",
            ],
            "ja3_hash": "771,4865-4866-4867-49195-49199-49196-49200,0-23-65281-10-11-35-16-5-51-43-13-45,29-23-24,0",
        },
        "mobile_chrome_android": {
            "name": "Chrome Mobile on Android",
            "cipher_suites": [
                "TLS_AES_128_GCM_SHA256",
                "TLS_AES_256_GCM_SHA384",
                "TLS_CHACHA20_POLY1305_SHA256",
            ],
            "curve_preferences": ["X25519", "P256"],
            "signature_algorithms": [
                "ecdsa_secp256r1_sha256",
                "rsa_pkcs1_sha256",
            ],
            "ja3_hash": "771,4865-4866-4867,0-23-65281-10-11-35-16-5-51-43-13-45,29-23-24,0",
        },
    }
    
    def __init__(self):
        self.current_profile = random.choice(list(self.TLS_PROFILES.keys()))
        self.profile_history = []
        self.rotation_count = 0
    
    def rotate_profile(self) -> str:
        """轮换 TLS 配置文件"""
        available = [p for p in self.TLS_PROFILES.keys() if p != self.current_profile]
        new_profile = random.choice(available)
        
        self.profile_history.append(self.current_profile)
        if len(self.profile_history) > 10:
            self.profile_history.pop(0)
        
        self.current_profile = new_profile
        self.rotation_count += 1
        
        return new_profile
    
    def get_current_profile(self) -> Dict:
        """获取当前 TLS 配置"""
        return self.TLS_PROFILES[self.current_profile]
    
    def get_ja3_hash(self) -> str:
        """获取当前 JA3 指纹哈希"""
        return self.get_current_profile().get("ja3_hash", "")
    
    def apply_to_session(self, session) -> None:
        """将 TLS 配置应用到 HTTP 会话 (使用 curl_cffi 或 httpx)"""
        profile = self.get_current_profile()
        
        # 使用 curl_cffi 模拟真实浏览器 TLS 握手
        session.impersonate = self._map_profile_to_browser(self.current_profile)
    
    def _map_profile_to_browser(self, profile_name: str) -> str:
        """映射到 curl_cffi 浏览器类型"""
        mapping = {
            "chrome_120_windows": "chrome120",
            "firefox_121_linux": "firefox121",
            "safari_17_macos": "safari17",
            "edge_120_windows": "edge120",
            "mobile_chrome_android": "chrome100",
        }
        return mapping.get(profile_name, "chrome120")
```

**集成示例**:
```python
from curl_cffi import requests

tls_manager = TLSFingerprintManager()

# 创建浏览器指纹模拟的 Session
session = requests.Session(impersonate=tls_manager._map_profile_to_browser(tls_manager.current_profile))

# 每 50 次请求轮换一次 TLS 配置
if tls_manager.rotation_count % 50 == 0:
    tls_manager.rotate_profile()
    session = requests.Session(impersonate=tls_manager._map_profile_to_browser(tls_manager.current_profile))

response = session.get("https://xueqiu.com/", headers=headers)
```

**适用场景**:
- 雪球 (反风控 ⭐⭐⭐⭐): 必须使用 TLS 指纹模拟
- 东方财富股吧 (反风控 ⭐⭐⭐⭐): 必须使用 TLS 指纹模拟
- 巨潮资讯 (反风控 ⭐⭐⭐): 建议使用
- 新浪新闻 (反风控 ⭐): 不需要

---

#### 组件 8: 自适应频率限制器 (来自 rate_limiter.go)

**原理**: 根据请求成功率动态调整请求间隔,成功率低时自动降速,成功率高时适当提速,避免固定频率被识别为机器人。

```python
class AdaptiveRateLimiter:
    """自适应频率限制器 (基于 Seadex AdaptiveRateLimiter)"""
    
    def __init__(
        self,
        min_interval: float = 1.0,  # 最小间隔 (秒)
        max_interval: float = 10.0,  # 最大间隔 (秒)
        burst_protection: bool = True,
        max_burst: int = 5,
    ):
        self.base_min_interval = min_interval
        self.base_max_interval = max_interval
        self.current_interval = min_interval
        self.last_request = time.time()
        
        self.success_count = 0
        self.failure_count = 0
        self.block_count = 0
        
        self.jitter_enabled = True
        self.burst_protection = burst_protection
        self.max_burst = max_burst
        self.burst_counter = 0
    
    def calculate_interval(self) -> float:
        """根据成功率动态计算请求间隔"""
        base = self.base_min_interval
        range_val = self.base_max_interval - self.base_min_interval
        
        # 根据成功率调整间隔
        total = self.success_count + self.failure_count
        if total > 10:
            success_rate = self.success_count / total
            
            if success_rate < 0.5:
                # 成功率 < 50%,间隔 ×3
                base *= 3
            elif success_rate < 0.7:
                # 成功率 50-70%,间隔 ×1.5
                base *= 1.5
            elif success_rate > 0.95 and total > 50:
                # 成功率 > 95% 且样本充足,间隔 ÷1.5
                base /= 1.5
                base = max(base, self.base_min_interval)
        
        # 根据被封次数调整
        if self.block_count > 5:
            # 被封 > 5 次,间隔 ×4
            base *= 4
        elif self.block_count > 2:
            # 被封 3-5 次,间隔 ×2
            base *= 2
        
        # 确保在合理范围内
        base = max(self.base_min_interval, base)
        base = min(self.base_max_interval * 5, base)
        
        self.current_interval = base
        
        # 添加随机抖动 (避免被识别为机器行为)
        if self.jitter_enabled:
            jitter = random.uniform(0, range_val * 0.5)
            base += jitter
        
        return base
    
    def wait(self) -> None:
        """等待直到可以发送请求"""
        interval = self.calculate_interval()
        elapsed = time.time() - self.last_request
        
        if elapsed < interval:
            sleep_time = interval - elapsed
            time.sleep(sleep_time)
        
        self.last_request = time.time()
        
        # 防突发保护
        if self.burst_protection:
            self.burst_counter += 1
            if self.burst_counter >= self.max_burst:
                extra_delay = self.current_interval * 2
                time.sleep(extra_delay)
                self.burst_counter = 0
    
    def report_success(self) -> None:
        """报告请求成功"""
        self.success_count += 1
    
    def report_failure(self) -> None:
        """报告请求失败"""
        self.failure_count += 1
    
    def report_block(self) -> None:
        """报告请求被封禁"""
        self.block_count += 1
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        total = self.success_count + self.failure_count
        success_rate = self.success_count / total if total > 0 else 0
        
        return {
            "current_interval": self.current_interval,
            "success_rate": success_rate,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "block_count": self.block_count,
            "burst_counter": self.burst_counter,
        }
    
    def reset_stats(self) -> None:
        """重置统计信息"""
        self.success_count = 0
        self.failure_count = 0
        self.block_count = 0
        self.burst_counter = 0
        self.current_interval = self.base_min_interval
```

**自适应策略示例**:
| 场景 | 成功率 | 被封次数 | 间隔调整 |
|------|--------|----------|----------|
| 正常运行 | > 95% | 0 | 基础间隔 ÷1.5 |
| 轻微异常 | 70-95% | 0 | 基础间隔 |
| 中度异常 | 50-70% | 0 | 基础间隔 ×1.5 |
| 严重异常 | < 50% | 0 | 基础间隔 ×3 |
| 被封禁 | 任意 | 3-5 次 | 基础间隔 ×2 |
| 频繁封禁 | 任意 | > 5 次 | 基础间隔 ×4 |

**适用场景**: 所有数据采集模块,特别是雪球、东方财富股吧等高反风控网站。

---

#### 组件 9: 智能代理池质量评分 (来自 proxy_pool.go)

**原理**: 多维度评估代理质量 (成功率 40% + 延迟 30% + 稳定性 20% + 匿名级别 10%),基于加权评分智能选择代理,而非简单轮询。

```python
class ProxyQualityScorer:
    """代理质量评分器 (基于 Seadex ProxyPool)"""
    
    ANONYMITY_BONUS = {
        "elite": 10.0,      # 高匿代理
        "anonymous": 7.0,   # 普通匿名
        "transparent": 3.0, # 透明代理
    }
    
    def __init__(self):
        self.proxy_stats: Dict[str, ProxyStats] = {}
    
    def calculate_quality_score(self, stats: ProxyStats) -> float:
        """计算代理质量评分 (0-100)"""
        score = 0.0
        
        # 成功率权重 40%
        score += stats.success_rate * 0.4
        
        # 延迟评分权重 30% (延迟越低分越高)
        latency_score = 100.0
        if stats.avg_latency > 0:
            # 100ms 以内 100 分,每增加 100ms 扣 10 分,最低 0 分
            latency_ms = stats.avg_latency * 1000  # 转换为毫秒
            latency_score = max(0, 100.0 - (latency_ms / 100) * 10)
        score += latency_score * 0.3
        
        # 稳定性权重 20% (连续失败越少分越高)
        stability_score = max(0, 100.0 - stats.consecutive_fail * 10)
        score += stability_score * 0.2
        
        # 匿名级别权重 10%
        score += self.ANONYMITY_BONUS.get(stats.anonymity_level, 5.0)
        
        # 确保在 0-100 范围内
        return max(0.0, min(100.0, score))
    
    def get_weighted_proxy(self, available_proxies: List[ProxyInfo]) -> ProxyInfo:
        """基于加权评分选择代理"""
        if not available_proxies:
            raise ValueError("没有可用代理")
        
        total_weight = 0.0
        for proxy in available_proxies:
            stats = self.proxy_stats.get(proxy.ip)
            if stats:
                stats.quality_score = self.calculate_quality_score(stats)
                total_weight += stats.quality_score
            else:
                total_weight += 50.0  # 默认评分
        
        # 加权随机选择
        r = random.uniform(0, total_weight)
        cumulative = 0.0
        
        for proxy in available_proxies:
            stats = self.proxy_stats.get(proxy.ip)
            weight = stats.quality_score if stats else 50.0
            cumulative += weight
            if r < cumulative:
                return proxy
        
        return available_proxies[0]
    
    def get_top_proxies(self, proxies: List[ProxyInfo], n: int) -> List[ProxyInfo]:
        """获取评分最高的 N 个代理"""
        scored = []
        for proxy in proxies:
            stats = self.proxy_stats.get(proxy.ip)
            score = stats.quality_score if stats else 50.0
            scored.append((proxy, score))
        
        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, s in scored[:n]]
    
    def report_result(self, proxy_ip: str, success: bool, latency: float) -> None:
        """报告代理使用结果"""
        if proxy_ip not in self.proxy_stats:
            self.proxy_stats[proxy_ip] = ProxyStats(
                success_rate=100.0,
                quality_score=50.0,
            )
        
        stats = self.proxy_stats[proxy_ip]
        
        if success:
            stats.success_count += 1
            stats.last_success = datetime.now()
            stats.consecutive_fail = 0
            
            # 更新平均延迟
            if latency > 0:
                total_latency = stats.avg_latency * (stats.success_count - 1) + latency
                stats.avg_latency = total_latency / stats.success_count
        else:
            stats.failure_count += 1
            stats.last_failure = datetime.now()
            stats.consecutive_fail += 1
        
        # 更新成功率
        total = stats.success_count + stats.failure_count
        if total > 0:
            stats.success_rate = (stats.success_count / total) * 100
        
        # 更新质量评分
        stats.quality_score = self.calculate_quality_score(stats)
```

**代理评分示例**:
| 代理 | 成功率 | 延迟 | 连续失败 | 匿名级别 | 质量评分 |
|------|--------|------|----------|----------|----------|
| A | 95% | 200ms | 0 | elite | 89.5 |
| B | 80% | 500ms | 2 | anonymous | 63.0 |
| C | 50% | 1000ms | 5 | transparent | 28.0 |

**适用场景**: 分布式数据采集,需要大量代理池的场景。

---

#### 组件 10: 实时决策引擎 (来自 decision_engine.go)

**原理**: 多维度风险评估 (失败率 + 延迟 + 连续失败 + 请求频率 + 异常响应码),根据风险等级自动调整采集策略。

```python
class RiskDecisionEngine:
    """实时风险决策引擎 (基于 Seadex DecisionEngine)"""
    
    def __init__(self):
        self.indicators = {
            "failure_rate": {
                "threshold": 0.3,  # 30% 失败率阈值
                "weight": 0.25,
                "description": "请求失败率",
            },
            "avg_latency": {
                "threshold": 5000,  # 5000ms 延迟阈值
                "weight": 0.20,
                "description": "平均响应延迟",
            },
            "consecutive_failures": {
                "threshold": 5,  # 连续 5 次失败
                "weight": 0.20,
                "description": "连续失败次数",
            },
            "request_rate": {
                "threshold": 100,  # 每分钟 100 次
                "weight": 0.15,
                "description": "请求频率 (次/分钟)",
            },
            "error_response_rate": {
                "threshold": 0.2,  # 20% 错误响应
                "weight": 0.20,
                "description": "异常响应码比例",
            },
        }
        
        self.history: List[RiskAssessment] = []
        self.alert_callbacks: List[callable] = []
        self.auto_adjust_enabled = True
    
    def assess_risk(
        self,
        data_source: str,
        metrics: Dict[str, float]
    ) -> RiskAssessment:
        """评估风险"""
        assessment = RiskAssessment(
            score=0.0,
            level=RiskLevel.LOW,
            factors=[],
            timestamp=datetime.now(),
            data_source=data_source,
        )
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for name, indicator in self.indicators.items():
            value = metrics.get(name)
            if value is None:
                continue
            
            risk_score = self._calculate_indicator_risk(value, indicator)
            
            if risk_score > 0:
                assessment.factors.append(
                    f"{name}={value} (threshold={indicator['threshold']})"
                )
            
            weighted_score += risk_score * indicator["weight"]
            total_weight += indicator["weight"]
        
        # 归一化风险评分
        if total_weight > 0:
            assessment.score = min(100, weighted_score / total_weight * 100)
        
        # 确定风险等级
        assessment.level = self._determine_risk_level(assessment.score)
        
        # 生成建议
        assessment.recommendation = self._generate_recommendation(assessment)
        
        # 记录历史
        self.history.append(assessment)
        if len(self.history) > 1000:
            self.history.pop(0)
        
        # 触发告警
        if assessment.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self._trigger_alert(assessment)
        
        # 自动调整策略
        if self.auto_adjust_enabled:
            adjustment = self._generate_adjustment(assessment)
            self._apply_adjustment(data_source, adjustment)
        
        return assessment
    
    def _calculate_indicator_risk(
        self, value: float, indicator: Dict
    ) -> float:
        """计算单个指标的风险评分"""
        if value <= indicator["threshold"]:
            return 0.0
        
        # 超过阈值越多,风险越高
        ratio = value / indicator["threshold"]
        risk_score = min(100, (ratio - 1) * 50)
        
        return risk_score
    
    def _determine_risk_level(self, score: float) -> RiskLevel:
        """确定风险等级"""
        if score >= 80:
            return RiskLevel.CRITICAL
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW
    
    def _generate_recommendation(self, assessment: RiskAssessment) -> str:
        """生成建议"""
        if assessment.level == RiskLevel.CRITICAL:
            return "立即停止请求,检查反风控策略,切换代理池,刷新所有 Cookie"
        elif assessment.level == RiskLevel.HIGH:
            return "降低请求频率,升级反风控策略,考虑使用浏览器获取 Cookie"
        elif assessment.level == RiskLevel.MEDIUM:
            return "适当降低请求频率,监控成功率,准备降级方案"
        else:
            return "保持当前策略,持续监控"
    
    def _generate_adjustment(self, assessment: RiskAssessment) -> Adjustment:
        """生成策略调整"""
        adjustment = Adjustment(reason=assessment.recommendation)
        
        if assessment.level == RiskLevel.CRITICAL:
            adjustment.change_interval = True
            adjustment.new_min_interval = 5.0  # 5 秒
            adjustment.new_max_interval = 15.0  # 15 秒
            adjustment.enable_extra_check = True
            adjustment.extra_checks = [
                "cookie_validation",
                "proxy_check",
                "fingerprint_check",
            ]
        
        elif assessment.level == RiskLevel.HIGH:
            adjustment.change_interval = True
            adjustment.new_min_interval = 3.0  # 3 秒
            adjustment.new_max_interval = 10.0  # 10 秒
            adjustment.enable_extra_check = True
            adjustment.extra_checks = ["cookie_validation", "proxy_check"]
        
        elif assessment.level == RiskLevel.MEDIUM:
            adjustment.change_interval = True
            adjustment.new_min_interval = 2.0  # 2 秒
            adjustment.new_max_interval = 5.0  # 5 秒
        
        return adjustment
    
    def get_risk_trend(self, window_size: int = 100) -> str:
        """获取风险趋势"""
        if len(self.history) < 2:
            return "stable"
        
        recent = self.history[-1].score
        previous = self.history[-2].score
        
        if recent > previous + 5:
            return "increasing"
        elif recent < previous - 5:
            return "decreasing"
        else:
            return "stable"
    
    def get_recent_average_risk(self, window_size: int = 100) -> float:
        """获取最近平均风险"""
        if not self.history:
            return 0.0
        
        window = self.history[-window_size:]
        return sum(a.score for a in window) / len(window)
```

**风险等级定义**:
```python
class RiskLevel(Enum):
    LOW = "low"           # 0-40 分: 保持当前策略
    MEDIUM = "medium"     # 40-60 分: 适当降低频率
    HIGH = "high"         # 60-80 分: 大幅降低频率,升级反风控
    CRITICAL = "critical" # 80-100 分: 立即停止,检查策略
```

**适用场景**: 所有数据采集模块,作为全局反风控决策中心。

---

#### 组件 11: 浏览器会话管理器 (来自 browser_manager.go)

**原理**: 管理浏览器会话的生命周期,自动获取和刷新 Cookie/Token,支持多数据源配置。

```python
class BrowserSessionManager:
    """浏览器会话管理器 (基于 Seadex BrowserManager)"""
    
    def __init__(
        self,
        headless: bool = True,
        anti_detection: bool = True,
        idle_timeout: int = 300,  # 5 分钟空闲超时
    ):
        self.headless = headless
        self.anti_detection = anti_detection
        self.idle_timeout = idle_timeout
        
        self.sessions: Dict[str, BrowserSession] = {}
        self.credentials: Dict[str, Credentials] = {}
        self.stats = BrowserStats()
    
    async def get_session(self, domain: str) -> BrowserSession:
        """获取指定域名的浏览器会话"""
        # 检查是否有可用会话
        if domain in self.sessions:
            session = self.sessions[domain]
            if time.time() - session.last_used < self.idle_timeout:
                session.last_used = time.time()
                return session
        
        # 创建新会话
        session = await self._launch_session(domain)
        self.sessions[domain] = session
        self.stats.total_launches += 1
        self.stats.active_sessions += 1
        
        return session
    
    async def get_credentials(self, domain: str) -> Credentials:
        """获取指定域名的凭证 (Cookie + Token)"""
        # 检查缓存
        if domain in self.credentials:
            cred = self.credentials[domain]
            if cred.is_valid():
                return cred
        
        # 刷新凭证
        return await self._refresh_credentials(domain)
    
    async def _refresh_credentials(self, domain: str) -> Credentials:
        """刷新凭证"""
        session = await self.get_session(domain)
        
        try:
            # 导航到目标页面
            config = self._get_domain_config(domain)
            await session.goto(config.init_url)
            
            # 等待页面加载
            await asyncio.sleep(2)
            
            # 提取 Cookie
            cookies = await session.get_cookies()
            
            # 提取 Token (如果需要)
            tokens = {}
            for token_config in config.required_tokens:
                if token_config.type == "cookie":
                    tokens[token_config.name] = await session.get_cookie_value(token_config.selector)
                elif token_config.type == "js_var":
                    tokens[token_config.name] = await session.evaluate_js(token_config.selector)
                elif token_config.type == "meta":
                    tokens[token_config.name] = await session.get_meta_content(token_config.selector)
            
            # 构建凭证
            credentials = Credentials(
                domain=domain,
                cookies=cookies,
                tokens=tokens,
                user_agent=await session.get_user_agent(),
                obtained_at=datetime.now(),
                expires_at=datetime.now() + timedelta(seconds=config.refresh_interval),
            )
            
            self.credentials[domain] = credentials
            self.stats.credentials_issued += 1
            
            return credentials
            
        finally:
            await self.close_session(domain)
    
    async def _launch_session(self, domain: str) -> BrowserSession:
        """启动浏览器会话"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                ],
            )
            
            context = await browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent=self._get_random_ua(),
            )
            
            # 注入反检测脚本
            if self.anti_detection:
                await context.add_init_script(
                    """
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => undefined
                    });
                    window.navigator.chrome = {
                        runtime: {},
                        loadTimes: function() {},
                        csi: function() {},
                        app: {}
                    };
                    """
                )
            
            page = await context.new_page()
            
            return BrowserSession(
                browser=browser,
                context=context,
                page=page,
                domain=domain,
                created_at=time.time(),
                last_used=time.time(),
            )
    
    async def close_session(self, domain: str) -> None:
        """关闭指定域名的会话"""
        if domain in self.sessions:
            session = self.sessions[domain]
            await session.browser.close()
            del self.sessions[domain]
            self.stats.active_sessions -= 1
            self.stats.total_closures += 1
    
    def _get_domain_config(self, domain: str) -> DomainConfig:
        """获取域名配置"""
        configs = {
            "xueqiu.com": DomainConfig(
                init_url="https://xueqiu.com",
                refresh_interval=3600,
                required_tokens=[
                    TokenExtractorConfig(name="xq_a_token", type="cookie", selector="xq_a_token"),
                ],
            ),
            "cninfo.com.cn": DomainConfig(
                init_url="http://www.cninfo.com.cn",
                refresh_interval=7200,
                required_tokens=[],
            ),
        }
        return configs.get(domain)
```

**适用场景**:
- 雪球: 需要 xq_a_token Cookie
- 巨潮资讯: 需要浏览器渲染公告列表
- 东方财富股吧: 需要 Cookie 验证

---


### 7.4 各网站专用采集器

#### 雪球专用采集器

```python
class XueqiuCrawler:
    """雪球舆情采集器"""
    
    BASE_URL = "https://xueqiu.com"
    
    def __init__(self, anti_detection: AntiDetectionCoordinator):
        self.anti_detection = anti_detection
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def fetch_stock_discussions(
        self,
        symbol: str,
        max_items: int = 50
    ) -> List[TextItem]:
        """获取股票讨论"""
        # 创建反检测会话
        session_ctx = await self.anti_detection.create_session(
            site_name="xueqiu"
        )
        
        url = f"{self.BASE_URL}/query/v1/symbol/search/status"
        params = {
            "q": symbol,
            "count": max_items,
            "comment": 0,
            "symbol": True,
            "type": 0,
            "sort": "time",
        }
        
        try:
            await self.anti_detection.before_request("xueqiu", session_ctx)
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    headers=session_ctx.headers,
                    cookies=session_ctx.cookies,
                    proxy=f"http://{session_ctx.proxy.ip}:{session_ctx.proxy.port}" if session_ctx.proxy else None,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    await self.anti_detection.after_request(
                        "xueqiu", session_ctx, response.status
                    )
                    
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_response(data, symbol)
                    else:
                        return []
                        
        except Exception as e:
            logger.error(f"雪球采集失败: {e}")
            return []
    
    def _parse_response(self, data: Dict, symbol: str) -> List[TextItem]:
        """解析雪球响应"""
        items = []
        
        for status in data.get("data", {}).get("list", []):
            text_id = hashlib.md5(
                f"xueqiu_{status.get('id')}_{status.get('created_at')}".encode()
            ).hexdigest()
            
            item = TextItem(
                text_id=text_id,
                source=TextSourceType.SOCIAL,
                provider="xueqiu",
                title=status.get("title", ""),
                content=status.get("text", ""),
                url=f"{self.BASE_URL}{status.get('target')}",
                related_symbols=[symbol],
                publish_time=datetime.fromtimestamp(
                    status.get("created_at", 0) / 1000
                ),
                metadata={
                    "user": status.get("user", {}).get("screen_name"),
                    "likes": status.get("like_count", 0),
                    "comments": status.get("reply_count", 0),
                },
            )
            items.append(item)
        
        return items
```

#### 巨潮资讯公告采集器

```python
class JuchaoAnnouncementCrawler:
    """巨潮资讯公告采集器"""
    
    BASE_URL = "http://www.cninfo.com.cn"
    
    def __init__(self, anti_detection: AntiDetectionCoordinator):
        self.anti_detection = anti_detection
    
    async def fetch_announcements(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        max_items: int = 50
    ) -> List[TextItem]:
        """获取公告"""
        session_ctx = await self.anti_detection.create_session(
            site_name="juchao",
            use_browser=True
        )
        
        url = f"{self.BASE_URL}/new/hisAnnouncement/query"
        
        payload = {
            "stock": symbol,
            "tabName": "fulltext",
            "pageSize": max_items,
            "pageNum": 1,
            "column": "szse",
            "category": "",
            "seDate": f"{start_date.isoformat()}~{end_date.isoformat()}",
        }
        
        try:
            await self.anti_detection.before_request("juchao", session_ctx)
            
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    user_agent=session_ctx.headers.get("User-Agent"),
                    viewport=session_ctx.browser_config.get("viewport"),
                    proxy={
                        "server": f"http://{session_ctx.proxy.ip}:{session_ctx.proxy.port}"
                    } if session_ctx.proxy else None,
                )
                
                await session_ctx.fingerprint_manager.apply_stealth(context)
                
                page = await context.new_page()
                
                # 获取公告列表
                response = await page.request.post(
                    url,
                    data=payload,
                    headers=session_ctx.headers,
                )
                
                await self.anti_detection.after_request(
                    "juchao", session_ctx, response.status
                )
                
                if response.status == 200:
                    data = await response.json()
                    items = await self._parse_announcements(
                        page, data, symbol
                    )
                    await browser.close()
                    return items
                
                await browser.close()
                return []
                
        except Exception as e:
            logger.error(f"巨潮采集失败: {e}")
            return []
    
    async def _parse_announcements(
        self, page, data: Dict, symbol: str
    ) -> List[TextItem]:
        """解析公告列表"""
        items = []
        
        for ann in data.get("announcements", []):
            adjunct_url = ann.get("adjunctUrl")
            
            # 提取 PDF 内容
            pdf_content = await self._extract_pdf_content(
                page, adjunct_url
            )
            
            text_id = hashlib.md5(
                f"juchao_{ann.get('announcementId')}".encode()
            ).hexdigest()
            
            item = TextItem(
                text_id=text_id,
                source=TextSourceType.ANNOUNCEMENT,
                provider="juchao",
                title=ann.get("announcementTitle", ""),
                content=pdf_content,
                url=f"{self.BASE_URL}{adjunct_url}",
                related_symbols=[symbol],
                publish_time=datetime.fromtimestamp(
                    ann.get("announcementTime", 0) / 1000
                ),
                metadata={
                    "announcement_id": ann.get("announcementId"),
                    "type": ann.get("announcementTypeName"),
                },
            )
            items.append(item)
        
        return items
    
    async def _extract_pdf_content(
        self, page, pdf_url: str
    ) -> str:
        """提取 PDF 文本内容"""
        # 使用 PyPDF2 或 pdfplumber 解析 PDF
        full_url = f"{self.BASE_URL}{pdf_url}"
        
        response = await page.request.get(full_url)
        pdf_bytes = await response.body()
        
        import io
        import pdfplumber
        
        with io.BytesIO(pdf_bytes) as pdf_file:
            with pdfplumber.open(pdf_file) as pdf:
                text = ""
                for page_num in range(min(len(pdf.pages), 10)):
                    page_text = pdf.pages[page_num].extract_text()
                    if page_text:
                        text += page_text + "\n"
        
        return text[:50000]
```

### 7.5 反风控配置

```yaml
# config/anti_detection.yaml

# 全局设置
global:
  max_concurrent_requests: 5
  user_agent_rotation: true
  proxy_rotation: true
  cookie_refresh_interval: 3600
  ban_recovery_time: 1800

# 代理池配置
proxy_pool:
  providers:
    - name: "luminati"
      type: "residential"
      api_url: "http://provider.luminati.io"
      cost_per_gb: 10.0
    - name: "proxyscrape"
      type: "datacenter"
      api_url: "https://api.proxyscrape.com"
      cost_per_gb: 2.0
    - name: "mobile_proxy"
      type: "mobile"
      api_url: "http://provider.mobile.com"
      cost_per_gb: 25.0
  
  health_check:
    enabled: true
    interval: 300
    test_url: "https://httpbin.org/ip"
    timeout: 5

# 网站专用配置
sites:
  sina_news:
    enabled: true
    rate_limit:
      requests_per_minute: 30
      requests_per_hour: 500
    proxy_type: "datacenter"
    needs_cookie: false
    anti_detection_level: "low"
    
  eastmoney_news:
    enabled: true
    rate_limit:
      requests_per_minute: 20
      requests_per_hour: 300
    proxy_type: "datacenter"
    needs_cookie: false
    anti_detection_level: "medium"
    
  cls:
    enabled: true
    rate_limit:
      requests_per_minute: 15
      requests_per_hour: 200
    proxy_type: "datacenter"
    needs_cookie: false
    anti_detection_level: "medium"
    
  juchao:
    enabled: true
    rate_limit:
      requests_per_minute: 10
      requests_per_hour: 100
    proxy_type: "mobile"
    needs_cookie: false
    anti_detection_level: "high"
    requires_browser: true
    
  sse:
    enabled: true
    rate_limit:
      requests_per_minute: 10
      requests_per_hour: 100
    proxy_type: "datacenter"
    needs_cookie: false
    anti_detection_level: "medium"
    
  szse:
    enabled: true
    rate_limit:
      requests_per_minute: 10
      requests_per_hour: 100
    proxy_type: "datacenter"
    needs_cookie: false
    anti_detection_level: "medium"
    
  xueqiu:
    enabled: true
    rate_limit:
      requests_per_minute: 5
      requests_per_hour: 50
    proxy_type: "residential"
    needs_cookie: true
    anti_detection_level: "very_high"
    requires_browser: true
    accounts:
      - username: "user1"
        password: "${XUEQIU_USER1_PASS}"
      - username: "user2"
        password: "${XUEQIU_USER2_PASS}"
    
  eastmoney_guba:
    enabled: true
    rate_limit:
      requests_per_minute: 8
      requests_per_hour: 80
    proxy_type: "residential"
    needs_cookie: false
    anti_detection_level: "high"
    requires_browser: true
    
  taoguba:
    enabled: false
    rate_limit:
      requests_per_minute: 3
      requests_per_hour: 30
    proxy_type: "residential"
    needs_cookie: false
    anti_detection_level: "extreme"
    requires_browser: true
    note: "反风控极强，建议手动采集或使用付费数据源"

# 验证码识别配置
captcha:
  enabled: true
  provider: "2captcha"
  api_key: "${TWOCAPTCHA_API_KEY}"
  max_wait_time: 120
  retry_on_fail: true

# 监控告警配置
monitoring:
  enabled: true
  alert_channels:
    - type: "log"
    - type: "email"
      recipients: ["admin@example.com"]
  
  thresholds:
    ban_rate: 0.1
    failure_rate: 0.2
    proxy_unhealthy_ratio: 0.3
```

### 7.6 反风控效果预期

| 指标 | 无反风控 | 有反风控 | 改善 |
|------|---------|---------|------|
| 封禁率 | 30-50% | < 2% | -95% |
| 成功率 | 50-70% | 95%+ | +35% |
| 平均请求延迟 | 1 秒 | 2-12 秒 (可控) | 正常 |
| 代理成本 | 0 元 | 500-800 元/月 | 必要投入 |
| 数据采集连续性 | 频繁中断 | 99%+ 连续 | 显著提升 |

### 7.7 反风控成本分析

| 项目 | 月成本 | 说明 |
|------|--------|------|
| 住宅代理 | 300-500 元 | 雪球/股吧等高反风控网站 |
| 数据中心代理 | 100-200 元 | 新闻/公告等低反风控网站 |
| 移动代理 | 200-300 元 | 巨潮等重要公告源 |
| 验证码识别 | 50-100 元 | 按需使用 |
| 账号维护 | 100-200 元 | 雪球账号池 |
| **合计** | **750-1300 元/月** | - |

**投入产出比**: 每月 ~1000 元投入，换取 85%+ 数据覆盖率，支撑年化 +3-5% 超额收益

### 7.8 Seadex 反风控模块对比与整合

#### 对比分析

| 组件 | Seadex 实现 (Go) | QuantCore 实现 (Python) | 差异点 | 整合方案 |
|------|------------------|------------------------|--------|----------|
| TLS 指纹混淆 | `tls_fingerprinter.go` | `TLSFingerprintManager` | Go 直接操作 `crypto/tls`,Python 使用 `curl_cffi` | 完全借鉴配置文件,集成方式不同 |
| 自适应频率限制 | `rate_limiter.go` | `AdaptiveRateLimiter` | Go 使用 CAS 无锁,Python 用 threading.Lock | 算法完全一致,实现语言不同 |
| 代理池管理 | `proxy_pool.go` | `ProxyPoolManager` + `ProxyQualityScorer` | Go 支持 3 种策略,Python 需增强加权选择 | 借鉴质量评分算法和黑名单机制 |
| 决策引擎 | `decision_engine.go` | `RiskDecisionEngine` | Go 使用接口回调,Python 用装饰器模式 | 风险指标和阈值完全一致 |
| 浏览器管理 | `browser_manager.go` | `BrowserSessionManager` | Go 用 `chromedp`,Python 用 `playwright` | 会话管理逻辑一致,浏览器库不同 |

#### 整合优先级矩阵

| 优先级 | 组件 | 来源 | 预期收益 | 实施难度 | 适用数据源 |
|--------|------|------|----------|----------|------------|
| 🔴 P0 | 自适应频率限制器 | rate_limiter.go | ⭐⭐⭐⭐⭐ | ⭐⭐ | 所有 |
| 🔴 P0 | 风险决策引擎 | decision_engine.go | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | 所有 |
| 🟡 P1 | TLS 指纹混淆 | tls_fingerprinter.go | ⭐⭐⭐⭐ | ⭐⭐⭐ | 雪球、股吧、巨潮 |
| 🟡 P1 | 代理质量评分 | proxy_pool.go | ⭐⭐⭐⭐ | ⭐⭐ | 分布式采集 |
| 🟢 P2 | 浏览器会话管理 | browser_manager.go | ⭐⭐⭐ | ⭐⭐⭐⭐ | 雪球、巨潮、股吧 |

#### 预期效果提升

| 指标 | 基础反风控 | + Seadex 高级组件 | 提升幅度 |
|------|-----------|-------------------|----------|
| 封禁率 | < 5% | < 1% | -80% |
| 成功率 | 90% | 98%+ | +8% |
| 代理利用率 | 60% | 85%+ | +42% |
| 自动恢复时间 | 30 分钟 | < 5 分钟 | -83% |
| 人工干预频率 | 每日 | 每周 | -86% |

### 7.9 异常自动恢复流程

#### 封禁自动检测与恢复

```
┌──────────────────────────────────────────────────────┐
│              异常自动恢复流程                          │
│                                                      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐          │
│  │ 阶段 1    │  │ 阶段 2    │  │ 阶段 3    │          │
│  │ 检测     │→│ 诊断     │→│ 恢复     │          │
│  │          │  │          │  │          │          │
│  │ 连续 3 次  │  │ 判断原因  │  │ 执行恢复  │          │
│  │ 403/429  │  │ IP/      │  │ 策略:     │          │
│  │          │  │ Cookie/  │  │ 1. 换代理  │          │
│  │          │  │ 频率/指纹 │  │ 2. 刷新凭证│          │
│  │          │  │          │  │ 3. 降频率  │          │
│  └──────────┘  └──────────┘  │ 4. 换指纹  │          │
│                              └──────────┘          │
│                                     │                │
│                              ┌──────┴──────┐        │
│                              │ 阶段 4       │        │
│                              │ 验证恢复    │        │
│                              │ 成功→继续   │        │
│                              │ 失败→升级处理│        │
│                              └─────────────┘        │
└──────────────────────────────────────────────────────┘
```

#### 恢复策略矩阵

| 场景 | 检测条件 | 诊断结果 | 恢复动作 | 冷却时间 | 升级条件 |
|------|---------|---------|---------|---------|---------|
| IP 封禁 | 连续 3 次 403 | IP 被列入黑名单 | 切换代理 + 等待 | 30 秒 | 连续 3 次切换失败 → 全站暂停 |
| Cookie 过期 | 返回登录页 | 凭证失效 | 刷新 Cookie | 5 秒 | 刷新 3 次失败 → 暂停该数据源 |
| 频率限制 | 429 响应 | 请求过快 | 间隔 ×3 + 等待 | 60 秒 | 连续 2 次 → 触发决策引擎 |
| 指纹识别 | 200 但返回空数据 | 指纹被识别 | 轮换 TLS/UA + 重试 | 10 秒 | 轮换 5 次失败 → 报告告警 |
| 验证码拦截 | 返回验证码页面 | 触发验证码 | 调用打码服务 | 30 秒 | 打码 3 次失败 → 暂停 |
| 全站封禁 | 所有代理均失败 | 网站升级反爬 | 全站暂停 + 告警 | 24 小时 | 人工介入 |

#### 自动恢复代码实现

```python
class AutoRecoveryManager:
    """自动恢复管理器"""
    
    def __init__(self):
        self.failure_tracker: Dict[str, List[FailureRecord]] = {}
        self.recovery_callbacks: Dict[str, callable] = {}
    
    async def handle_failure(
        self,
        site_name: str,
        response_status: int,
        session: SessionContext,
    ) -> RecoveryResult:
        """处理失败并尝试恢复"""
        self._record_failure(site_name, response_status)
        
        if not self._should_attempt_recovery(site_name):
            return RecoveryResult(
                success=False,
                action="too_many_failures",
                message="失败次数过多，等待冷却"
            )
        
        phase = self._diagnose_failure(site_name, response_status)
        return await self._execute_recovery(site_name, phase, session)
    
    def _diagnose_failure(
        self, site_name: str, status: int
    ) -> FailurePhase:
        """诊断失败原因"""
        if status == 403:
            return FailurePhase.IP_BAN
        elif status == 429:
            return FailurePhase.RATE_LIMIT
        elif status == 401:
            return FailurePhase.COOKIE_EXPIRED
        else:
            return FailurePhase.FINGERPRINT_DETECTED
    
    async def _execute_recovery(
        self,
        site_name: str,
        phase: FailurePhase,
        session: SessionContext,
    ) -> RecoveryResult:
        """执行恢复策略"""
        recovery_actions = {
            FailurePhase.IP_BAN: self._recover_ip_ban,
            FailurePhase.RATE_LIMIT: self._recover_rate_limit,
            FailurePhase.COOKIE_EXPIRED: self._recover_cookie,
            FailurePhase.FINGERPRINT_DETECTED: self._recover_fingerprint,
        }
        
        action = recovery_actions.get(phase)
        if action:
            return await action(site_name, session)
        
        return RecoveryResult(success=False, action="unknown", message="未知错误")
    
    async def _recover_ip_ban(
        self, site_name: str, session: SessionContext
    ) -> RecoveryResult:
        """恢复 IP 封禁"""
        new_proxy = await self.proxy_pool.get_proxy(site_name)
        if new_proxy:
            session.proxy = new_proxy
            await asyncio.sleep(30)
            return RecoveryResult(
                success=True,
                action="proxy_switched",
                message="已切换代理，等待 30 秒"
            )
        return RecoveryResult(success=False, action="no_proxy", message="无可用代理")
    
    async def _recover_rate_limit(
        self, site_name: str, session: SessionContext
    ) -> RecoveryResult:
        """恢复频率限制"""
        if self.rate_limiter:
            self.rate_limiter.report_block()
        await asyncio.sleep(60)
        return RecoveryResult(
            success=True,
            action="rate_reduced",
            message="已降低频率，等待 60 秒"
        )
    
    async def _recover_cookie(
        self, site_name: str, session: SessionContext
    ) -> RecoveryResult:
        """恢复 Cookie 过期"""
        if self.browser_session_mgr:
            new_creds = await self.browser_session_mgr.get_credentials(site_name)
            if new_creds:
                session.cookies = new_creds.cookies
                return RecoveryResult(
                    success=True,
                    action="cookie_refreshed",
                    message="已刷新 Cookie"
                )
        return RecoveryResult(success=False, action="cookie_fail", message="Cookie 刷新失败")
    
    async def _recover_fingerprint(
        self, site_name: str, session: SessionContext
    ) -> RecoveryResult:
        """恢复指纹识别"""
        if self.tls_manager:
            self.tls_manager.rotate_profile()
        self.header_manager.rotate_user_agent()
        await asyncio.sleep(10)
        return RecoveryResult(
            success=True,
            action="fingerprint_changed",
            message="已轮换 TLS 指纹和用户代理"
        )
    
    def _record_failure(self, site_name: str, status: int):
        """记录失败"""
        if site_name not in self.failure_tracker:
            self.failure_tracker[site_name] = []
        self.failure_tracker[site_name].append(
            FailureRecord(status=status, timestamp=datetime.now())
        )
    
    def _should_attempt_recovery(self, site_name: str) -> bool:
        """是否应该尝试恢复"""
        recent = self.failure_tracker.get(site_name, [])
        recent_5min = [
            r for r in recent 
            if (datetime.now() - r.timestamp).total_seconds() < 300
        ]
        return len(recent_5min) < 10
    
    def _get_recent_failures(
        self, site_name: str, window_seconds: int = 300
    ) -> List[FailureRecord]:
        """获取最近的失败记录"""
        recent = self.failure_tracker.get(site_name, [])
        cutoff = datetime.now() - timedelta(seconds=window_seconds)
        return [r for r in recent if r.timestamp > cutoff]
```

#### 冷却机制

```python
@dataclass
class CoolingConfig:
    initial_delay: float       # 初始冷却时间 (秒)
    max_delay: float           # 最大冷却时间 (秒)
    backoff_multiplier: float  # 退避倍数 (每次失败 ×2)
    reset_after_success: bool  # 成功后重置

class CoolingManager:
    """冷却管理器"""
    
    def __init__(self):
        self.cooling_until: Dict[str, datetime] = {}
        self.failure_count: Dict[str, int] = {}
        self.config = CoolingConfig(
            initial_delay=30,
            max_delay=3600,
            backoff_multiplier=2.0,
            reset_after_success=True
        )
    
    def is_cooling(self, site_name: str) -> bool:
        """检查是否在冷却中"""
        if site_name in self.cooling_until:
            return datetime.now() < self.cooling_until[site_name]
        return False
    
    def start_cooling(self, site_name: str):
        """开始冷却"""
        count = self.failure_count.get(site_name, 0) + 1
        self.failure_count[site_name] = count
        
        delay = min(
            self.config.initial_delay * (self.config.backoff_multiplier ** count),
            self.config.max_delay
        )
        self.cooling_until[site_name] = datetime.now() + timedelta(seconds=delay)
    
    def reset(self, site_name: str):
        """重置冷却 (成功时调用)"""
        if self.config.reset_after_success:
            self.failure_count.pop(site_name, None)
            self.cooling_until.pop(site_name, None)
```

---

### 7.10 反风控测试策略

#### 单元测试

```python
import pytest
from unittest.mock import Mock, patch

class TestAdaptiveRateLimiter:
    def test_initial_interval(self):
        limiter = AdaptiveRateLimiter(min_interval=1.0, max_interval=10.0)
        interval = limiter.calculate_interval()
        assert 1.0 <= interval <= 10.0
    
    def test_interval_increases_on_low_success_rate(self):
        limiter = AdaptiveRateLimiter(min_interval=1.0, max_interval=10.0)
        
        # 模拟低成功率
        for _ in range(5):
            limiter.report_success()
        for _ in range(10):
            limiter.report_failure()
        
        interval = limiter.calculate_interval()
        assert interval > limiter.base_min_interval
    
    def test_interval_decreases_on_high_success_rate(self):
        limiter = AdaptiveRateLimiter(min_interval=1.0, max_interval=10.0)
        
        # 模拟高成功率
        for _ in range(100):
            limiter.report_success()
        for _ in range(2):
            limiter.report_failure()
        
        interval = limiter.calculate_interval()
        assert interval <= limiter.base_min_interval * 1.5
    
    def test_block_penalty(self):
        limiter = AdaptiveRateLimiter(min_interval=1.0, max_interval=10.0)
        limiter.block_count = 6
        
        interval = limiter.calculate_interval()
        assert interval >= limiter.base_min_interval * 4
    
    def test_jitter_adds_randomness(self):
        limiter = AdaptiveRateLimiter(
            min_interval=1.0, max_interval=10.0, jitter_enabled=True
        )
        
        intervals = [limiter.calculate_interval() for _ in range(10)]
        assert len(set(intervals)) > 1  # 应该有不同值

class TestProxyQualityScorer:
    def test_calculate_score_high_quality(self):
        scorer = ProxyQualityScorer()
        stats = ProxyStats(
            success_rate=95,
            avg_latency=0.2,  # 200ms
            consecutive_fail=0,
            anonymity_level="elite"
        )
        score = scorer.calculate_quality_score(stats)
        assert score > 80
    
    def test_calculate_score_low_quality(self):
        scorer = ProxyQualityScorer()
        stats = ProxyStats(
            success_rate=50,
            avg_latency=1.0,  # 1000ms
            consecutive_fail=5,
            anonymity_level="transparent"
        )
        score = scorer.calculate_quality_score(stats)
        assert score < 40
    
    def test_weighted_selection_favors_high_score(self):
        scorer = ProxyQualityScorer()
        
        proxies = [
            ProxyInfo(ip="1.1.1.1", port=8080, proxy_type="datacenter"),
            ProxyInfo(ip="2.2.2.2", port=8080, proxy_type="datacenter"),
        ]
        
        scorer.proxy_stats["1.1.1.1"] = ProxyStats(success_rate=95, quality_score=90)
        scorer.proxy_stats["2.2.2.2"] = ProxyStats(success_rate=50, quality_score=30)
        
        # 运行 100 次，高质量代理应被选中更多
        high_count = 0
        for _ in range(100):
            selected = scorer.get_weighted_proxy(proxies)
            if selected.ip == "1.1.1.1":
                high_count += 1
        
        assert high_count > 70  # 应 > 70%

class TestRiskDecisionEngine:
    def test_low_risk(self):
        engine = RiskDecisionEngine()
        assessment = engine.assess_risk(
            data_source="test",
            metrics={
                "failure_rate": 0.05,
                "avg_latency": 500,
                "consecutive_failures": 0,
                "request_rate": 10,
                "error_response_rate": 0.05,
            }
        )
        assert assessment.level == RiskLevel.LOW
    
    def test_critical_risk(self):
        engine = RiskDecisionEngine()
        assessment = engine.assess_risk(
            data_source="test",
            metrics={
                "failure_rate": 0.8,
                "avg_latency": 10000,
                "consecutive_failures": 10,
                "request_rate": 200,
                "error_response_rate": 0.5,
            }
        )
        assert assessment.level == RiskLevel.CRITICAL

class TestTLSFingerprintManager:
    def test_rotate_profile_changes(self):
        manager = TLSFingerprintManager()
        initial = manager.current_profile
        manager.rotate_profile()
        assert manager.current_profile != initial
    
    def test_ja3_hash_present(self):
        manager = TLSFingerprintManager()
        for profile_name in manager.TLS_PROFILES:
            manager.current_profile = profile_name
            ja3 = manager.get_ja3_hash()
            assert ja3 != "", f"Profile {profile_name} missing JA3 hash"
```

#### 集成测试

```python
@pytest.mark.integration
class TestAntiDetectionIntegration:
    @pytest.mark.asyncio
    async def test_full_crawl_cycle(self):
        """测试完整采集周期"""
        coordinator = AntiDetectionCoordinator()
        
        session = await coordinator.create_session("xueqiu")
        assert session.proxy is not None
        assert session.headers is not None
        
        await coordinator.before_request("xueqiu", session)
        await coordinator.after_request("xueqiu", session, 200)
    
    @pytest.mark.asyncio
    async def test_ban_and_recovery(self):
        """测试封禁与恢复"""
        recovery = AutoRecoveryManager()
        session = SessionContext(site_name="xueqiu")
        
        result = await recovery.handle_failure("xueqiu", 403, session)
        assert result.action in ["proxy_switched", "rate_reduced"]
    
    @pytest.mark.asyncio
    async def test_rate_limiter_adaptation(self):
        """测试频率限制自适应"""
        coordinator = AntiDetectionCoordinator()
        
        # 模拟 10 次成功
        for _ in range(10):
            await coordinator.after_request("xueqiu", Mock(), 200)
        
        # 模拟 20 次失败
        for _ in range(20):
            await coordinator.after_request("xueqiu", Mock(), 500, "timeout")
        
        stats = coordinator.get_overall_stats()
        assert stats["xueqiu"]["success_rate"] < 0.5
```

#### 压力测试

```python
@pytest.mark.stress
class TestStressTesting:
    def test_concurrent_requests(self):
        """并发请求测试"""
        async def concurrent_crawl():
            coordinator = AntiDetectionCoordinator()
            session = await coordinator.create_session("xueqiu")
            await coordinator.before_request("xueqiu", session)
        
        import asyncio
        tasks = [concurrent_crawl() for _ in range(50)]
        asyncio.run(asyncio.gather(*tasks))
    
    def test_memory_leak(self):
        """内存泄漏测试"""
        import tracemalloc
        tracemalloc.start()
        
        coordinator = AntiDetectionCoordinator()
        
        for _ in range(1000):
            coordinator.get_overall_stats()
        
        current, peak = tracemalloc.get_traced_memory()
        assert peak < 100 * 1024 * 1024  # 峰值 < 100MB
```

---

## 💰 成本收益分析

### 投入成本

```
开发成本:
  - 7 个模块开发: ~8-10 人月
  - 预估人力成本: 8-10 万元

运行成本 (月度):
  - 新闻 API: 500-1000 元
  - 代理池: 750-1300 元
  - 验证码服务: 50-100 元
  - 账号维护: 100-200 元
  - GPU 电费: 500-800 元
  - 月度合计: 1900-3400 元

硬件成本:
  - RTX 4090 (已有): 0 元
  - 如新增: ~12000 元

年度总投入:
  - 开发 (一次性): 8-10 万元
  - 运行 (年度): 2.3-4.1 万元
  - 首年总计: 10.3-14.1 万元
```

### 预期收益

```
直接收益 (1000 万规模):
  - 年化收益提升: +5-8%
  - 年收益增加: 50-80 万元

间接收益:
  - 策略开发效率: 3-5 倍
  - 竞争优势提升

成本节约:
  - 智能过滤: 19 万元/年
  - 服务治理: 减少故障损失 5-10 万元/年

总投入 (首年): ~12 万元
总收益: ~70 万元
投入产出比: 1:6 (首年) / 1:23 (次年起)
```

---

## 📊 实施路线图

### Phase 1: 基础设施 (1-2 周)

**优先级**: 🔴 最高

```
Week 1:
  - 模块 1: 文本数据源管理
    - 实现 TextDataSourceManager
    - 接入新浪新闻 + 财联社
    - 创建 TextDataStorage

Week 2:
  - 模块 7: 反风控措施 (基础)
    - 实现请求头伪装
    - 实现代理池管理
    - 实现智能频率控制
  - 模块 2: 智能文本过滤
    - 实现四级过滤管线
```

**验收标准**:
- 新闻数据源可用率 > 99%
- 过滤率 > 90%
- 封禁率 < 5%

### Phase 2: 核心功能 (3-5 周)

**优先级**: 🔴 最高

```
Week 3:
  - 模块 7: 反风控措施 (进阶)
    - 实现浏览器指纹伪装
    - 实现 Cookie 池
    - 集成雪球 + 巨潮采集器

Week 4-5:
  - 模块 3: LLM 服务治理
    - 实现五级降级策略
    - 配置健康监控
    - 实现结果缓存

Week 6:
  - 模块 5: 显存调度
    - 实现时段调度
    - 配置显存策略
  - FinSenti-Qwen3.5-9B 集成
```

**验收标准**:
- 数据采集成功率 > 95%
- 服务可用性 > 99%
- 显存使用 < 8GB

### Phase 3: 验证优化 (6-8 周)

**优先级**: 🟡 高

```
Week 7-8:
  - 模块 4: 回测验证
    - 实现 IC 分析
    - 实现分层回测
    - 执行因子验证

Week 9:
  - 模块 6: 生命周期管理
    - 实现健康监控
    - 实现版本控制
    - 配置预警规则
```

**验收标准**:
- 因子 IC > 0.03
- 多空年化 > 10%
- 健康监控延迟 < 1 天

### Phase 4: 上线运行 (9-10 周)

**优先级**: 🟢 中

```
Week 10-11:
  - 集成测试
  - 性能优化
  - 反风控压力测试

Week 12:
  - 灰度上线
  - 监控告警
  - 文档完善
```

**验收标准**:
- 数据覆盖率 > 85%
- 封禁率 < 2%
- 年化收益提升 > 3%

---

## 📁 文档清单

| 编号 | 文档名称 | 文件路径 |
|-----|---------|---------|
| 0 | LLM 集成完整方案 | [llm_quantcore_integration_plan.md](file:///d:/PROJ/Quant/docs/llm_integration_complete_optimization.md) |
| 1 | 文本数据源管理 | [llm_optimization_01_text_data_pipeline.md](file:///d:/PROJ/Quant/docs/llm_optimization_01_text_data_pipeline.md) |
| 2 | 智能文本过滤 | [llm_optimization_02_smart_text_filter.md](file:///d:/PROJ/Quant/docs/llm_optimization_02_smart_text_filter.md) |
| 3 | LLM 服务治理 | [llm_optimization_03_llm_service_mesh.md](file:///d:/PROJ/Quant/docs/llm_optimization_03_llm_service_mesh.md) |
| 4 | 回测验证框架 | [llm_optimization_04_text_factor_backtester.md](file:///d:/PROJ/Quant/docs/llm_optimization_04_text_factor_backtester.md) |
| 5 | 显存智能调度 | [llm_optimization_05_gpu_scheduler.md](file:///d:/PROJ/Quant/docs/llm_optimization_05_gpu_scheduler.md) |
| 6 | 因子生命周期 | [llm_optimization_06_factor_lifecycle.md](file:///d:/PROJ/Quant/docs/llm_optimization_06_factor_lifecycle.md) |
| 7 | 反风控措施 (新增) | [llm_optimization_07_anti_detection.md](file:///d:/PROJ/Quant/docs/llm_optimization_07_anti_detection.md) |

---

## 🎯 关键决策点

| 决策 | 结论 | 理由 |
|-----|------|------|
| 是否引入 LLM？ | ✅ 是 | 收益明确，风险可控 |
| 引入几个模型？ | 1 个 (阶段 1) | FinSenti 专注文本因子 |
| 是否需要反风控？ | ✅ 是 | 无此无法稳定采集数据 |
| 代理类型选择？ | 混合 (住宅+数据中心) | 平衡成本与成功率 |
| 浏览器自动化？ | Playwright | 支持隐身模式，反检测成熟 |
| 验证码处理？ | 2Captcha API | 成本低，准确率高 |
| 何时启动？ | 立即 | 阶段 1 优先级最高 |

---

**文档版本**: v2.0  
**最终更新**: 2026-04-25  
**适用系统**: QuantCore v0.4.0 + Backend API  
**新增内容**: 模块 7 反风控措施完整方案
