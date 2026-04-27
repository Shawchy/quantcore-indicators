# Quant 量化系统文档中心

**版本**: v2.0 | **最后更新**: 2026-04-27

本项目文档经过全面整理，按类型组织为以下目录结构，便于快速查找和维护。

---

## 📚 文档目录结构

```
docs/
├── README.md                    # 文档索引（本文件）
├── architecture/                # 架构设计文档 (9)
├── guides/                      # 使用与开发指南 (3)
├── features/                    # 功能实现文档 (15)
├── changelogs/                  # 版本更新日志 (12)
├── reports/                     # 检查与实施报告 (5)
└── adr/                         # 架构决策记录 (4, 子目录)
```

---

## 🏗️ 架构设计文档 (`architecture/`)

系统架构设计、数据流、存储方案等技术文档。

| 文档 | 说明 | 重要度 |
|------|------|--------|
| [ADR-001.md](file:///d:/PROJ/Quant/docs/architecture/ADR-001.md) | 数据中台架构选择 | ⭐⭐⭐⭐⭐ |
| [ADR-002.md](file:///d:/PROJ/Quant/docs/architecture/ADR-002.md) | 多数据源智能路由策略 | ⭐⭐⭐⭐⭐ |
| [ADR-003.md](file:///d:/PROJ/Quant/docs/architecture/ADR-003.md) | 统一数据模型设计 | ⭐⭐⭐⭐⭐ |
| [ADR-004.md](file:///d:/PROJ/Quant/docs/architecture/ADR-004.md) | 分层存储策略 | ⭐⭐⭐⭐ |
| [adr/README.md](file:///d:/PROJ/Quant/docs/architecture/adr/README.md) | ADR 索引和架构总览 | ⭐⭐⭐⭐⭐ |
| [DATA_CLASSIFICATION_STORAGE_PLAN.md](file:///d:/PROJ/Quant/docs/architecture/DATA_CLASSIFICATION_STORAGE_PLAN.md) | 数据分类存储方案 | ⭐⭐⭐⭐ |
| [DATA_MIDDLE_PLATFORM_OPTIMIZATION_PLAN.md](file:///d:/PROJ/Quant/docs/architecture/DATA_MIDDLE_PLATFORM_OPTIMIZATION_PLAN.md) | 数据中台优化方案 | ⭐⭐⭐⭐ |
| [DATA_PLATFORM_OPTIMIZATION_MASTER_PLAN.md](file:///d:/PROJ/Quant/docs/architecture/DATA_PLATFORM_OPTIMIZATION_MASTER_PLAN.md) | 数据平台优化总方案 | ⭐⭐⭐⭐⭐ |
| [DATA_STORAGE_DEEP_OPTIMIZATION_PLAN.md](file:///d:/PROJ/Quant/docs/architecture/DATA_STORAGE_DEEP_OPTIMIZATION_PLAN.md) | 数据存储深度优化 | ⭐⭐⭐⭐ |

---

## 📖 使用与开发指南 (`guides/`)

API 使用、数据源配置、优化实施等指南。

| 文档 | 说明 |
|------|------|
| [API_AND_ADR_GUIDE.md](file:///d:/PROJ/Quant/docs/guides/API_AND_ADR_GUIDE.md) | API 和 ADR 使用指南 |
| [TUSHARE_GUIDE.md](file:///d:/PROJ/Quant/docs/guides/TUSHARE_GUIDE.md) | Tushare 数据源配置指南 |
| [OPTIMIZATION_IMPLEMENTATION_GUIDE.md](file:///d:/PROJ/Quant/docs/guides/OPTIMIZATION_IMPLEMENTATION_GUIDE.md) | 优化实施指南 |

---

## 🚀 功能实现文档 (`features/`)

LLM 集成、量化框架集成、文本因子模型等功能文档。

### LLM 集成系列

| 文档 | 说明 |
|------|------|
| [llm_integration_complete_optimization.md](file:///d:/PROJ/Quant/docs/features/llm_integration_complete_optimization.md) | LLM 集成完整优化方案 |
| [llm_optimization_01_text_data_pipeline.md](file:///d:/PROJ/Quant/docs/features/llm_optimization_01_text_data_pipeline.md) | 文本数据管线设计 |
| [llm_optimization_02_smart_text_filter.md](file:///d:/PROJ/Quant/docs/features/llm_optimization_02_smart_text_filter.md) | 智能文本过滤器 |
| [llm_optimization_03_llm_service_mesh.md](file:///d:/PROJ/Quant/docs/features/llm_optimization_03_llm_service_mesh.md) | LLM 服务网格 |
| [llm_optimization_04_text_factor_backtester.md](file:///d:/PROJ/Quant/docs/features/llm_optimization_04_text_factor_backtester.md) | 文本因子回测器 |
| [llm_optimization_05_gpu_scheduler.md](file:///d:/PROJ/Quant/docs/features/llm_optimization_05_gpu_scheduler.md) | GPU 显存调度器 |
| [llm_optimization_06_factor_lifecycle.md](file:///d:/PROJ/Quant/docs/features/llm_optimization_06_factor_lifecycle.md) | 因子生命周期管理 |
| [llm_optimization_complete_integration.md](file:///d:/PROJ/Quant/docs/features/llm_optimization_complete_integration.md) | 完整集成方案 |

### LLM 选型与评估

| 文档 | 说明 |
|------|------|
| [financial_llm_evaluation.md](file:///d:/PROJ/Quant/docs/features/financial_llm_evaluation.md) | 金融 LLM 评估报告 |
| [finsenti_text_factor_model.md](file:///d:/PROJ/Quant/docs/features/finsenti_text_factor_model.md) | 文本因子情感模型 |
| [llm_final_decision.md](file:///d:/PROJ/Quant/docs/features/llm_final_decision.md) | LLM 最终选型决策 |
| [llm_memory_optimization.md](file:///d:/PROJ/Quant/docs/features/llm_memory_optimization.md) | LLM 内存优化 |
| [llm_single_model_selection.md](file:///d:/PROJ/Quant/docs/features/llm_single_model_selection.md) | 单模型选型方案 |

### 量化框架集成

| 文档 | 说明 |
|------|------|
| [llm_quantcore_integration_plan.md](file:///d:/PROJ/Quant/docs/features/llm_quantcore_integration_plan.md) | LLM + QuantCore 集成计划 |

---

## 📊 版本更新日志 (`changelogs/`)

各版本的功能更新和修复记录。

| 文档 | 版本 |
|------|------|
| [CHANGELOG_EASTMONEY_V1.6.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.6.md) | V1.6 |
| [CHANGELOG_EASTMONEY_V1.7.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.7.md) | V1.7 |
| [CHANGELOG_EASTMONEY_V1.8.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.8.md) | V1.8 |
| [CHANGELOG_EASTMONEY_V1.9.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.9.md) | V1.9 |
| [CHANGELOG_EASTMONEY_V1.10.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.10.md) | V1.10 |
| [CHANGELOG_EASTMONEY_V1.11.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.11.md) | V1.11 |
| [CHANGELOG_EASTMONEY_V1.12.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.12.md) | V1.12 |
| [CHANGELOG_EASTMONEY_V1.13.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.13.md) | V1.13 |
| [CHANGELOG_EASTMONEY_V1.14.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.14.md) | V1.14 |
| [CHANGELOG_EASTMONEY_V1.15.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.15.md) | V1.15 |
| [CHANGELOG_EASTMONEY_V1.16.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.16.md) | V1.16 |
| [CHANGELOG_EASTMONEY_V1.17.md](file:///d:/PROJ/Quant/docs/changelogs/CHANGELOG_EASTMONEY_V1.17.md) | V1.17 |

---

## 📋 检查与实施报告 (`reports/`)

系统检查报告、实施总结等。

| 文档 | 说明 |
|------|------|
| [IMPLEMENTATION_PROGRESS_REPORT.md](file:///d:/PROJ/Quant/docs/reports/IMPLEMENTATION_PROGRESS_REPORT.md) | 实施进度报告 |
| [IMPLEMENTATION_SUMMARY.md](file:///d:/PROJ/Quant/docs/reports/IMPLEMENTATION_SUMMARY.md) | 实施总结 |
| [STAGE2_MONITORING_IMPLEMENTATION_SUMMARY.md](file:///d:/PROJ/Quant/docs/reports/STAGE2_MONITORING_IMPLEMENTATION_SUMMARY.md) | 阶段 2 监控实施总结 |
| [STAGE3_LIFECYCLE_IMPLEMENTATION_SUMMARY.md](file:///d:/PROJ/Quant/docs/reports/STAGE3_LIFECYCLE_IMPLEMENTATION_SUMMARY.md) | 阶段 3 生命周期实施总结 |
| [document_governance_and_framework_integration_report_20260427.md](file:///d:/PROJ/Quant/docs/reports/document_governance_and_framework_integration_report_20260427.md) | 文档治理与框架集成报告 |

---

## 🎯 快速导航

### 我想...

| 目标 | 推荐阅读 |
|------|---------|
| 了解系统架构 | [ADR-001](file:///d:/PROJ/Quant/docs/architecture/ADR-001.md) → [架构总览](file:///d:/PROJ/Quant/docs/architecture/adr/README.md) |
| 学习数据源管理 | [ADR-002](file:///d:/PROJ/Quant/docs/architecture/ADR-002.md) → [数据平台优化方案](file:///d:/PROJ/Quant/docs/architecture/DATA_PLATFORM_OPTIMIZATION_MASTER_PLAN.md) |
| 理解数据模型 | [ADR-003](file:///d:/PROJ/Quant/docs/architecture/ADR-003.md) → `backend/app/models/unified_models.py` |
| 学习存储策略 | [ADR-004](file:///d:/PROJ/Quant/docs/architecture/ADR-004.md) → [数据分类存储方案](file:///d:/PROJ/Quant/docs/architecture/DATA_CLASSIFICATION_STORAGE_PLAN.md) |
| LLM 集成 | [完整优化方案](file:///d:/PROJ/Quant/docs/features/llm_integration_complete_optimization.md) → [集成计划](file:///d:/PROJ/Quant/docs/features/llm_quantcore_integration_plan.md) |
| 量化框架 | [QuantCore README](file:///d:/PROJ/Quant/quantcore/README.md) → [指标库 README](file:///d:/PROJ/Quant/quantcore-indicators/README.md) |
| 开发新功能 | [ADR 文档](file:///d:/PROJ/Quant/docs/architecture/) → [开发者指南](file:///d:/PROJ/Quant/backend/DEVELOPER_GUIDE.md) |
| 查看更新日志 | [changelogs/](file:///d:/PROJ/Quant/docs/changelogs/) |

---

## 📊 系统架构总览

```
┌─────────────────────────────────────────────────┐
│              前端层 (React)                      │
│  - Watchlist, Kline, Screener, Backtest        │
│  - 基金分析、东方财富模块                       │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│          API 网关层 (FastAPI + Swagger)          │
│  - 70+ API 端点                                  │
│  - JWT 认证 + 限流 + 断路器                     │
│  - LLM 助手服务                                  │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│       数据中台调度层 (核心)                       │
├─────────────────────────────────────────────────┤
│  - Smart Router (智能路由)                      │
│  - Unified Adapter (统一适配器)                 │
│  - Storage Router (存储路由)                    │
│  - LRU Cache + Parquet + SQLite                │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         数据源适配层 (7 个数据源)                  │
│  EFinance | AkShare | Baostock | YFinance      │
│  Playwright | TickFlow | Tushare                │
└─────────────────────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│      量化计算层 (待集成)                          │
│  - quantcore-indicators (Rust 指标库)           │
│  - QuantCore (Rust 回测引擎)                    │
└─────────────────────────────────────────────────┘
```

---

## 📝 文档维护规范

### 命名规范
- 统一使用英文小写 + 下划线命名
- 文档标题清晰描述内容
- CHANGELOG 按版本命名

### 版本控制
- 每个文档添加版本号和最后更新日期
- 架构变更时创建/更新 ADR
- 功能变更时更新 features/ 文档

### 定期审查
- 每季度审查一次文档
- 标记过时内容并移至 archive/
- 合并同类文档减少冗余

### 贡献指南
1. 新增功能时同步更新文档
2. 架构变更时创建 ADR
3. 提交代码前检查文档完整性
4. 使用统一的文档模板

---

## 🎓 学习路径

### 初学者
1. 阅读 [架构总览](file:///d:/PROJ/Quant/docs/architecture/adr/README.md)
2. 查看 [API 文档](http://localhost:8000/docs)（启动服务后）
3. 学习 [ADR-001](file:///d:/PROJ/Quant/docs/architecture/ADR-001.md) 了解架构基础

### 进阶开发者
1. 精读所有 ADR 文档
2. 研究 [技术设计文档](file:///d:/PROJ/Quant/docs/architecture/)
3. 参与功能开发和架构优化

### 架构师
1. 审查 ADR 决策
2. 优化存储策略和性能
3. 设计新功能和模块

---

**维护者**: 量化系统团队  
**文档版本**: 2.0
