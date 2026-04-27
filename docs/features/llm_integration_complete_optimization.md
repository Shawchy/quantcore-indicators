# LLM 集成 QuantCore 完整优化方案

## 📊 文档概览

本文档是 **LLM 集成 QuantCore 系统** 的完整优化方案，包含 6 个优化模块的详细设计：

- ✅ **优化 1**: 文本数据源管理管线
- ✅ **优化 2**: 智能文本过滤器
- ✅ **优化 3**: LLM 服务治理层
- ✅ **优化 4**: 文本因子回测验证框架
- ✅ **优化 5**: GPU 显存智能调度器
- ✅ **优化 6**: 因子生命周期管理

---

## 🎯 核心设计理念

### 问题 - 方案对应关系

| 问题 | 优化模块 | 解决效果 |
|-----|---------|---------|
| 数据源分散 | 优化 1: 文本数据管线 | 统一采集，标准化管理 |
| 处理量过大 | 优化 2: 智能过滤 | 过滤 91%，降低成本 |
| 服务不稳定 | 优化 3: 服务治理 | 可用性 95% → 99.9% |
| 有效性未知 | 优化 4: 回测验证 | 科学验证因子质量 |
| 显存冲突 | 优化 5: 显存调度 | OOM 降低到 0 |
| 因子衰减 | 优化 6: 生命周期 | 失效预警提前 30 倍 |

---

## 🏗️ 完整架构

```
┌─────────────────────────────────────────────────────────┐
│                    数据源层 (优化 1)                       │
│                                                         │
│  新闻 API │ 公告爬虫 │ 社交媒体 │ 研报数据库              │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                 智能过滤层 (优化 2)                        │
│                                                         │
│  去重 → 相关性 → 质量 → 重要性排序                        │
│  58300 条/天 → 5000 条/天 (减少 91%)                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              LLM 服务层 (优化 3)                          │
│                                                         │
│  服务治理: 重试 + 降级 + 缓存 + 限流 + 健康监控           │
│  可用性: 99.9%                                          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              显存调度层 (优化 5)                          │
│                                                         │
│  时段感知 + 按需加载 + 智能卸载 + OOM 保护               │
│  显存峰值: 16GB → 6.5GB (减少 60%)                      │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              因子生产层                                   │
│                                                         │
│  FinSenti-Qwen3.5-9B (文本因子工厂)                      │
│  输出: 标准化因子值 (-1 到 +1)                            │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              验证管理层 (优化 4 + 6)                      │
│                                                         │
│  回测验证: IC 分析 + 分层回测 + 独立性检验               │
│  生命周期: 健康监控 + 版本控制 + 失效预警                │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              应用层                                       │
│                                                         │
│  Alpha 工厂 │ 多因子模型 │ 组合优化 │ 策略回测            │
└─────────────────────────────────────────────────────────┘
```

---

## 📋 模块详细设计

### 模块 1: 文本数据源管理管线

**文档**: [llm_optimization_01_text_data_pipeline.md](file:///d:/PROJ/Quant/docs/llm_optimization_01_text_data_pipeline.md)

**核心组件**:
```python
# 1. 统一数据模型
class TextItem:
    text_id: str
    source: TextSourceType
    title: str
    content: str
    related_symbols: List[str]
    publish_time: datetime

# 2. 数据源接口
class TextDataSource(ABC):
    async def fetch_latest(symbols, limit)
    async def fetch_by_date(date, symbols)

# 3. 数据源管理器
class TextDataSourceManager:
    async def fetch_daily_texts(symbols, date)
    async def health_check_all()

# 4. 数据存储
class TextDataStorage:
    def save_texts(texts)
    def query_texts(date, symbols)
```

**数据覆盖**:
- 新闻: 8000 条/天 (5 分钟更新)
- 公告: 250 条/天 (1 小时更新)
- 社交媒体: 50000 条/天 (1 分钟更新)
- 研报: 50 条/天 (日更)

**预期效果**:
- 采集延迟 < 5 分钟
- 去重率 > 20%
- 查询延迟 < 100ms
- 可用性 > 99%

---

### 模块 2: 智能文本过滤器

**文档**: [llm_optimization_02_smart_text_filter.md](file:///d:/PROJ/Quant/docs/llm_optimization_02_smart_text_filter.md)

**四级过滤管线**:
```
原始文本 (58300)
  ↓ [去重过滤 40%]
35000 条
  ↓ [相关性过滤 57%]
15000 条
  ↓ [质量过滤 33%]
10000 条
  ↓ [重要性排序 50%]
5000 条 (最终输出)
```

**核心组件**:
```python
# 1. 去重过滤器
class DedupFilter:
    - MD5 Hash + SimHash
    - 24 小时时间窗口

# 2. 相关性过滤器
class RelevanceFilter:
    - 股票代码匹配
    - 行业板块匹配
    - 关注列表匹配

# 3. 质量评估过滤器
class QualityFilter:
    - 广告检测
    - 垃圾内容检测
    - 文本长度检查

# 4. 重要性排序器
class ImportanceRanker:
    - 关键词评分
    - 来源权重
    - 时效性评分
```

**成本节约**:
- 处理量: -91%
- 计算时间: -92%
- API 费用: -91% (17490 元/月 → 1590 元/月)
- 年度节约: 19 万元

---

### 模块 3: LLM 服务治理层

**文档**: [llm_optimization_03_llm_service_mesh.md](file:///d:/PROJ/Quant/docs/llm_optimization_03_llm_service_mesh.md)

**五级降级策略**:
```
Level 0: LLM 主模型 (FinSenti-Qwen3.5-9B)
  ↓ 失败
Level 1: LLM 备用模型 (Qwen3.5-9B)
  ↓ 失败
Level 2: BERT 模型
  ↓ 失败
Level 3: 规则方法
  ↓ 失败
Level 4: 默认值 (中性因子)
```

**核心组件**:
```python
# 1. 健康检查器
class LLMHealthChecker:
    async def start_monitoring()
    async def check() -> status

# 2. 降级管理器
class DegradationManager:
    async def execute_with_degradation(func)

# 3. 重试管理器
class RetryManager:
    async def execute_with_retry(func)
    - 指数退避 + 随机抖动

# 4. 结果缓存
class LLMResultCache:
    - LRU 缓存
    - TTL 过期

# 5. 限流保护器
class TokenBucketRateLimiter:
    async def acquire() -> bool

# 6. 服务治理主类
class LLMServiceMesh:
    async def query(text)
    async def batch_query(texts)
```

**效果**:
- 可用性: 95% → 99.9%
- 错误率: 5% → < 0.1%
- 缓存命中率: 30-50%
- 降级成功率: 99%

---

### 模块 4: 文本因子回测验证框架

**文档**: [llm_optimization_04_text_factor_backtester.md](file:///d:/PROJ/Quant/docs/llm_optimization_04_text_factor_backtester.md)

**五步验证流程**:
```
Step 1: IC 分析
  - IC 均值 > 0.03
  - ICIR > 0.5
  - T 值 > 2.0

Step 2: 分层回测
  - 十分组 (Q1-Q10)
  - 多空收益 > 10%/年
  - 单调性检验

Step 3: 风险调整收益
  - 夏普比率 > 1.0
  - 最大回撤 < 20%

Step 4: 因子独立性
  - 与传统因子相关性 < 0.7
  - 增量 R² > 5%

Step 5: 消融实验
  - 逐个移除因子
  - 计算贡献度
```

**核心组件**:
```python
# 1. IC 分析器
class ICAnalyzer:
    def analyze(factor_data, return_data) -> ICResult

# 2. 分层回测器
class LayeredBacktester:
    def run(factor_data, return_data) -> LayeredBacktestResult

# 3. 因子独立性检验器
class FactorIndependenceTester:
    def test(target_factor, other_factors, returns)

# 4. 消融实验器
class AblationStudy:
    def run(factors, returns, strategy_func)

# 5. 主验证器
class TextFactorValidator:
    def validate(factor_name, factor_data, return_data)
    -> FactorValidationReport
```

**通过标准**:
- IC 均值 > 0.03
- 多空年化 > 10%
- 夏普 > 1.0
- 增量 R² > 5%

---

### 模块 5: GPU 显存智能调度器

**文档**: [llm_optimization_05_gpu_scheduler.md](file:///d:/PROJ/Quant/docs/llm_optimization_05_gpu_scheduler.md)

**三时段调度策略**:
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

**核心组件**:
```python
# 1. GPU 监控器
class GPUMonitor:
    def get_status() -> GPUStatus
    def is_safe_to_load(required_memory) -> bool

# 2. 模型生命周期管理器
class ModelLifecycleManager:
    async def load_model(model_name)
    async def unload_model(model_name)
    async def unload_idle_models()

# 3. 时段调度器
class TimeBasedScheduler:
    async def execute_period_schedule()

# 4. 智能调度主类
class GPUScheduler:
    async def start()
    async def query_with_model(model_name, query_func)
```

**效果**:
- OOM 次数: 频繁 → 0
- 显存峰值: 16GB → 6.5GB
- 模型切换延迟: < 5 秒
- GPU 利用率: +30%

---

### 模块 6: 因子生命周期管理

**文档**: [llm_optimization_06_factor_lifecycle.md](file:///d:/PROJ/Quant/docs/llm_optimization_06_factor_lifecycle.md)

**生命周期阶段**:
```
创建 → 验证 → 上线 → 监控 → 衰减? → 更新/下线
```

**核心组件**:
```python
# 1. 健康监控器
class FactorHealthMonitor:
    def check_health(factor_name, ic_history)
    -> FactorHealthReport
    - 状态: healthy/warning/critical
    - 衰减率计算
    - 预计到达临界天数

# 2. 版本控制器
class FactorVersionControl:
    def create_version(factor_name, model_version)
    def get_latest_version(factor_name)
    def deprecate_version(version_id)

# 3. 更新管理器
class FactorUpdateManager:
    async def check_and_update(factor_name)
    async def update_after_model_upgrade()
```

**效果**:
- 失效发现时间: 1-3 月 → 1-3 天
- 策略损失: 5-10% → < 1%
- 版本管理: 清晰隔离
- 回滚能力: 支持

---

## 📊 实施路线图

### 阶段 0: 基础设施 (1-2 周) ⭐⭐⭐⭐⭐

**优先级**: 最高 (必须完成)

**任务**:
```
Week 1:
  - 优化 1: 文本数据源管理
    - 实现 TextDataSourceManager
    - 接入新闻/公告/舆情数据源
    - 创建 TextDataStorage

Week 2:
  - 优化 2: 智能文本过滤
    - 实现四级过滤管线
    - 配置过滤参数
    - 测试过滤效果
```

**验收标准**:
- 数据源可用率 > 99%
- 过滤率 > 90%
- 处理延迟 < 1 秒

---

### 阶段 1: 核心功能 (3-6 周) ⭐⭐⭐⭐⭐

**优先级**: 最高 (核心功能)

**任务**:
```
Week 3-4:
  - 部署 FinSenti-Qwen3.5-9B
  - 优化 3: LLM 服务治理
    - 实现降级策略
    - 配置健康监控
    - 测试降级流程

Week 5-6:
  - 集成到 Alpha 工厂
    - 修改 factory.py
    - 添加文本因子生产
    - 单元测试

Week 7-8:
  - 优化 5: 显存调度
    - 实现时段调度
    - 配置显存策略
    - 压力测试
```

**验收标准**:
- 因子生产成功率 > 99%
- 服务可用性 > 99.9%
- 显存使用 < 8GB

---

### 阶段 2: 验证优化 (7-9 周) ⭐⭐⭐⭐

**优先级**: 高 (质量保证)

**任务**:
```
Week 9-10:
  - 优化 4: 回测验证
    - 实现 IC 分析
    - 实现分层回测
    - 执行因子验证

Week 11-12:
  - 优化 6: 生命周期
    - 实现健康监控
    - 实现版本控制
    - 配置预警规则
```

**验收标准**:
- 因子 IC > 0.03
- 多空年化 > 10%
- 健康监控延迟 < 1 天

---

### 阶段 3: 上线运行 (10-12 周) ⭐⭐⭐

**优先级**: 中 (生产部署)

**任务**:
```
Week 13-14:
  - 集成测试
  - 性能优化
  - 文档完善

Week 15-16:
  - 灰度上线
  - 监控告警
  - 用户培训
```

**验收标准**:
- 实盘跟踪误差 < 5%
- 年化收益提升 > 3%
- 用户满意度 > 90%

---

## 💰 成本收益分析

### 投入成本

```
人力成本:
  - 1 人 × 3 月 = 3 人月

计算成本:
  - GPU: RTX 4090 (已有) = 0 元
  - 显存: 6.5GB (单模型)

数据成本:
  - 新闻 API: 1000 元/月
  - 公告爬虫: 0 元
  - 社交媒体: 0 元
  - 月度总计: 1000 元

开发成本:
  - 3 个月开发: ~5 万元
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
  - 服务治理: 减少故障损失

总投入: ~6 万元/年
总收益: ~70 万元/年
投入产出比: 1:12
```

---

## 📁 已创建文档清单

| 编号 | 文档名称 | 文件路径 |
|-----|---------|---------|
| 0 | LLM 集成方案 (原版) | [llm_quantcore_integration_plan.md](file:///d:/PROJ/Quant/docs/llm_quantcore_integration_plan.md) |
| 1 | 文本数据源管理 | [llm_optimization_01_text_data_pipeline.md](file:///d:/PROJ/Quant/docs/llm_optimization_01_text_data_pipeline.md) |
| 2 | 智能文本过滤 | [llm_optimization_02_smart_text_filter.md](file:///d:/PROJ/Quant/docs/llm_optimization_02_smart_text_filter.md) |
| 3 | LLM 服务治理 | [llm_optimization_03_llm_service_mesh.md](file:///d:/PROJ/Quant/docs/llm_optimization_03_llm_service_mesh.md) |
| 4 | 回测验证框架 | [llm_optimization_04_text_factor_backtester.md](file:///d:/PROJ/Quant/docs/llm_optimization_04_text_factor_backtester.md) |
| 5 | 显存智能调度 | [llm_optimization_05_gpu_scheduler.md](file:///d:/PROJ/Quant/docs/llm_optimization_05_gpu_scheduler.md) |
| 6 | 因子生命周期 | [llm_optimization_06_factor_lifecycle.md](file:///d:/PROJ/Quant/docs/llm_optimization_06_factor_lifecycle.md) |

---

## 🎯 总结

### 核心价值

**问题**：现有 NLP 能力不足，无法量化文本因子

**方案**：引入 FinSenti-Qwen3.5-9B 作为文本因子专用模型

**优化**：6 个优化模块确保可落地、可验证、可维护

**收益**：年化收益 +5-8%，投入产出比 1:12

### 关键决策点

| 决策 | 结论 | 理由 |
|-----|------|------|
| 是否引入 LLM？ | ✅ 是 | 收益明确，风险可控 |
| 引入几个模型？ | 1 个 (阶段 1) | FinSenti 专注文本因子 |
| 是否需要优化？ | ✅ 是 | 6 个模块确保生产级 |
| 何时启动？ | 立即 | 阶段 0 优先级最高 |

### 下一步行动

1. **本周**: 评审方案，确认优先级
2. **下周**: 启动阶段 0 (基础设施)
3. **1 个月内**: 完成数据源和过滤管线
4. **3 个月内**: 上线文本因子生产

---

**文档版本**: v1.0  
**最终更新**: 2026-04-24  
**适用系统**: QuantCore v0.4.0 + Backend API  
**推荐方案**: 三阶段实施 (阶段 0 → 1 → 2 → 3)
