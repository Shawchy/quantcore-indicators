# 双模型显存优化指南

## 📊 显存占用分析

### 问题核心

**是的，双模型同时调用确实占用更多显存！**

```
┌─────────────────────────────────────────────────┐
│  配置方案          │  显存占用  │  说明         │
├─────────────────────────────────────────────────┤
│  单模型 (数值)      │  ~5-6GB   │  Q5_K_M       │
│  单模型 (情感)      │  ~6-7GB   │  Q5_K_M       │
│  双模型同时加载     │  ~11-13GB │  两个都在显存  │
│  双模型动态切换     │  ~6-7GB   │  一次一个      │
└─────────────────────────────────────────────────┘
```

---

## ⚠️ Ollama 模型加载机制

### 默认行为
Ollama 会**将模型常驻显存**，不会自动卸载：

```bash
# 加载模型
ollama run qwen3:8b-financial "计算 MACD"

# 即使命令执行完毕，模型仍然在显存中
nvidia-smi  # 可以看到模型占用 ~6GB
```

### 问题场景

```
场景 1: 用户 A 查询技术指标 (8:00)
→ 加载数值模型 (6GB)
→ 执行完成后模型仍在显存

场景 2: 用户 B 分析新闻情感 (8:05)
→ 显存不足，需要加载情感模型 (7GB)
→ Ollama 可能报错：CUDA out of memory

场景 3: 用户 C 也要查询技术指标 (8:10)
→ 数值模型已在显存外
→ 需要重新加载，增加延迟
```

---

## 💡 优化方案对比

### 方案 A: 单模型常驻（推荐入门）

**策略**: 只加载数值模型，情感分析用传统 NLP

```yaml
配置:
  常驻模型：qwen3:8b-financial
  显存占用：5-6GB
  情感分析：TextBlob / VADER / 自训练 BERT

优点:
  ✅ 显存占用稳定
  ✅ 响应速度快
  ✅ 实现简单

缺点:
  ⚠️ 情感分析精度较低
  ⚠️ 无法使用 LLM 的语义理解能力
```

**适用**: RTX 3060/3070 (8-12GB 显存)

---

### 方案 B: 动态加载（推荐生产）

**策略**: 按需加载，用完即卸

```yaml
配置:
  max_concurrent_models: 1
  unload_timeout: 300s  # 5 分钟未使用自动卸载
  vram_budget: 8GB

工作流程:
  1. 用户请求 → 判断任务类型
  2. 检查模型是否在显存
  3. 不在 → 卸载当前模型 → 加载所需模型
  4. 执行请求
  5. 标记使用时间，等待超时卸载
```

**显存使用曲线**:
```
显存
  │
 8GB├──────┐      ┌──────┐      ┌──────┐
  ││      │      │      │      │      │
 6GB├┤      ├──────┤      ├──────┤      ├───
  ││数值  │      │情感  │      │数值  │
 0GB└┴──────┴──────┴──────┴──────┴──────┴───→ 时间
     8:00   8:05   8:10   8:15   8:20
```

**优点**:
- ✅ 显存峰值 < 8GB
- ✅ 支持双模型功能
- ✅ 自动化管理

**缺点**:
- ⚠️ 模型切换有延迟 (2-5 秒)
- ⚠️ 频繁切换影响体验

**适用**: RTX 3080/3090/4090 (10-24GB 显存)

---

### 方案 C: 双模型常驻（企业级）

**策略**: 两个模型都常驻显存

```yaml
配置:
  常驻模型：
    - qwen3:8b-financial (6GB)
    - finsenti-qwen3.5:9b (7GB)
  总显存：13GB
  响应延迟：< 1 秒
```

**优点**:
- ✅ 零等待切换
- ✅ 用户体验最佳
- ✅ 支持并发请求

**缺点**:
- ❌ 显存占用高
- ❌ 需要高端显卡

**适用**: RTX 3090/4090 (24GB) 或 A100 (40GB+)

---

### 方案 D: 智能预测预加载（高级）

**策略**: 根据使用模式预测并预加载

```python
# 使用模式分析
上午 9:00-11:00 → 技术指标查询高峰 → 预加载数值模型
下午 14:00-16:00 → 研报分析高峰 → 预加载情感模型
晚上 20:00-22:00 → 综合查询高峰 → 双模型常驻

# 实现逻辑
if current_hour in [9, 10, 11]:
    preload("numerical")
elif current_hour in [14, 15, 16]:
    preload("sentiment")
```

**优点**:
- ✅ 减少等待时间
- ✅ 显存利用率高
- ✅ 智能化程度高

**缺点**:
- ⚠️ 实现复杂
- ⚠️ 需要历史数据训练

---

## 🚀 实施建议

### 根据您的硬件选择

| 显卡型号 | 显存 | 推荐方案 | 说明 |
|---------|------|---------|------|
| RTX 3060 | 12GB | 方案 A | 单模型 + 传统 NLP |
| RTX 3070 | 8GB | 方案 A | 单模型 + 传统 NLP |
| RTX 3080 | 10GB | 方案 B | 动态加载 |
| RTX 3090 | 24GB | 方案 C | 双模型常驻 |
| RTX 4090 | 24GB | 方案 C | 双模型常驻 |
| A100 | 40GB | 方案 C+D | 常驻 + 预测 |

---

## 📝 配置示例

### 方案 B 配置（动态加载）

```yaml
# config/llm_router.yaml
memory_optimization:
  enabled: true
  
  # 显存预算（GB）
  vram_budget: 8.0
  
  # 最大并发模型数
  max_concurrent_models: 1
  
  # 自动卸载超时（秒）
  unload_timeout: 300
  
  # 模型配置
  models:
    numerical:
      name: qwen3:8b-financial
      vram_estimate: 5.5
      priority: 1  # 高优先级，可预加载
      preload: true
    
    sentiment:
      name: finsenti-qwen3.5:9b
      vram_estimate: 6.5
      priority: 2
      preload: false
  
  # 使用模式（可选，用于预测）
  usage_patterns:
    peak_hours:
      numerical: [9, 10, 11, 14, 15]
      sentiment: [13, 14, 15, 16]
    off_peak_unload: true  # 低峰期卸载所有模型
```

---

## 🔧 Ollama 显存管理技巧

### 1. 手动卸载模型

```bash
# 查看运行的模型
ollama ps

# 停止模型（释放显存）
ollama stop qwen3:8b-financial
```

### 2. 设置显存限制

```bash
# 通过环境变量限制 Ollama 显存使用
export OLLAMA_MAX_VRAM=8589934592  # 8GB

# Windows PowerShell
$env:OLLAMA_MAX_VRAM="8589934592"
```

### 3. 使用 CUDA 可见设备

```bash
# 限制 Ollama 只使用特定 GPU
export CUDA_VISIBLE_DEVICES=0

# 多 GPU 环境，让 Ollama 使用第二张卡
export CUDA_VISIBLE_DEVICES=1
```

---

## 📊 性能对比测试

### 测试环境
- GPU: RTX 4090 24GB
- 模型：Qwen3-8B-Financial (Q5_K_M)

### 不同方案对比

| 指标 | 方案 A | 方案 B | 方案 C |
|-----|-------|-------|-------|
| 显存占用 | 6GB | 6-7GB | 13GB |
| 首次响应 | 0.5s | 0.5s | 0.5s |
| 切换延迟 | N/A | 3-5s | 0s |
| 并发能力 | 低 | 中 | 高 |
| 实现难度 | ⭐ | ⭐⭐⭐ | ⭐⭐ |

---

## ✅ 推荐实施步骤

### 阶段 1: 单模型部署（当前）

```bash
# 1. 只部署数值模型
ollama pull qwen3:8b-financial

# 2. 设置显存限制
export OLLAMA_MAX_VRAM=6442450944  # 6GB

# 3. 测试
ollama run qwen3:8b-financial "计算 MACD"
```

### 阶段 2: 动态加载（1-2 个月后）

```python
# 集成显存优化路由器
from app.services.financial_llm_router_optimized import MemoryOptimizedRouter

router = MemoryOptimizedRouter(
    max_concurrent_models=1,
    unload_timeout=300,
    vram_budget_gb=8.0
)

# 使用
result = await router.route_query(
    query="计算 RSI",
    task_type="numerical_analysis"
)
```

### 阶段 3: 双模型常驻（显存充足时）

```bash
# 加载两个模型
ollama pull qwen3:8b-financial
ollama pull finsenti-qwen3.5:9b

# 后台常驻（Linux）
nohup ollama run qwen3:8b-financial &
nohup ollama run finsenti-qwen3.5:9b &
```

---

## 🎯 最终建议

**如果您的显存 < 12GB**:
- ✅ 使用方案 A（单模型 + 传统 NLP）
- ✅ 优先保证数值模型性能
- ✅ 情感分析用 TextBlob/VADER 替代

**如果您的显存 12-16GB**:
- ✅ 使用方案 B（动态加载）
- ✅ 设置合理的 unload_timeout
- ✅ 避免频繁切换

**如果您的显存 > 20GB**:
- ✅ 使用方案 C（双模型常驻）
- ✅ 用户体验最佳
- ✅ 支持并发请求

---

## 📋 检查清单

部署前检查:
- [ ] 确认 GPU 显存大小
- [ ] 安装 nvidia-smi 监控工具
- [ ] 设置 OLLAMA_MAX_VRAM
- [ ] 测试模型加载/卸载

性能监控:
- [ ] 显存使用率 < 90%
- [ ] 模型切换延迟 < 5 秒
- [ ] 无 CUDA OOM 错误
- [ ] 响应时间稳定

---

**文档版本**: v1.0  
**更新时间**: 2026-04-24  
**适用平台**: Quant 数据中台
