# 量化系统文档索引

## 📚 文档分类

### 1. 架构决策记录 (ADR)
**位置**: [`docs/adr/`](file:///d:/PROJ/Quant/docs/adr/README.md)

| 文档 | 说明 | 重要性 |
|------|------|--------|
| [ADR-001](file:///d:/PROJ/Quant/docs/adr/ADR-001.md) | 数据中台架构选择 | ⭐⭐⭐⭐⭐ |
| [ADR-002](file:///d:/PROJ/Quant/docs/adr/ADR-002.md) | 多数据源智能路由策略 | ⭐⭐⭐⭐⭐ |
| [ADR-003](file:///d:/PROJ/Quant/docs/adr/ADR-003.md) | 统一数据模型设计 | ⭐⭐⭐⭐⭐ |
| [ADR-004](file:///d:/PROJ/Quant/docs/adr/ADR-004.md) | 分层存储策略 | ⭐⭐⭐⭐ |

**用途**: 理解系统架构设计思路和决策理由

---

### 2. API 文档
**位置**: 启动服务后访问 http://localhost:8000/docs

| 类型 | URL | 说明 |
|------|-----|------|
| **Swagger UI** | /docs | 交互式 API 文档 |
| **ReDoc** | /redoc | 美观的 API 文档 |
| **OpenAPI** | /openapi.json | API 定义 JSON |

**特性**:
- ✅ 50+ API 端点文档
- ✅ 在线测试功能
- ✅ 请求/响应示例
- ✅ 参数验证规则
- ✅ 认证说明

---

### 3. 技术设计文档
**位置**: `backend/` 目录

| 文档 | 说明 | 重要性 |
|------|------|--------|
| [DATA_UNIFIED_STORAGE_SOLUTION.md](file:///d:/PROJ/Quant/backend/DATA_UNIFIED_STORAGE_SOLUTION.md) | 统一存储方案 | ⭐⭐⭐⭐⭐ |
| [UNIFIED_DATA_ACCESS_DESIGN.md](file:///d:/PROJ/Quant/backend/UNIFIED_DATA_ACCESS_DESIGN.md) | 统一数据访问设计 | ⭐⭐⭐⭐⭐ |
| [DATA_SOURCE_SCENARIO_OPTIMIZATION.md](file:///d:/PROJ/Quant/backend/DATA_SOURCE_SCENARIO_OPTIMIZATION.md) | 数据源场景优化 | ⭐⭐⭐⭐ |
| [MULTI_DATA_SOURCE_SMART_ROUTING.md](file:///d:/PROJ/Quant/backend/MULTI_DATA_SOURCE_SMART_ROUTING.md) | 多数据源智能路由 | ⭐⭐⭐⭐ |
| [DATA_SOURCE_COMPARISON_REPORT_2026.md](file:///d:/PROJ/Quant/backend/DATA_SOURCE_COMPARISON_REPORT_2026.md) | 数据源对比报告 | ⭐⭐⭐ |
| [BAOSTOCK_API_SUMMARY.md](file:///d:/PROJ/Quant/backend/BAOSTOCK_API_SUMMARY.md) | BaoStock API 总结 | ⭐⭐ |
| [EFINANCE_API_REFERENCE.md](file:///d:/PROJ/Quant/backend/EFINANCE_API_REFERENCE.md) | EFinance API 参考 | ⭐⭐⭐ |

---

### 4. 快速指南
**位置**: `docs/` 目录

| 文档 | 说明 |
|------|------|
| [API_AND_ADR_GUIDE.md](file:///d:/PROJ/Quant/docs/API_AND_ADR_GUIDE.md) | API 和 ADR 使用指南 |
| [adr/README.md](file:///d:/PROJ/Quant/docs/adr/README.md) | ADR 索引和架构总览 |

---

## 🎯 快速导航

### 我想...

#### 了解系统架构
1. 阅读 [ADR-001](file:///d:/PROJ/Quant/docs/adr/ADR-001.md) - 数据中台架构
2. 查看 [架构总览图](file:///d:/PROJ/Quant/docs/adr/README.md#架构总览)
3. 参考 [统一数据访问设计](file:///d:/PROJ/Quant/backend/UNIFIED_DATA_ACCESS_DESIGN.md)

#### 学习数据源管理
1. 阅读 [ADR-002](file:///d:/PROJ/Quant/docs/adr/ADR-002.md) - 智能路由
2. 查看 [数据源对比报告](file:///d:/PROJ/Quant/backend/DATA_SOURCE_COMPARISON_REPORT_2026.md)
3. 参考 [场景优化指南](file:///d:/PROJ/Quant/backend/DATA_SOURCE_SCENARIO_OPTIMIZATION.md)

#### 理解数据模型
1. 阅读 [ADR-003](file:///d:/PROJ/Quant/docs/adr/ADR-003.md) - 统一模型
2. 查看 [`unified_models.py`](file:///d:/PROJ/Quant/backend/app/models/unified_models.py)
3. 参考 [数据标准化器](file:///d:/PROJ/Quant/backend/app/utils/data_normalizer.py)

#### 学习存储策略
1. 阅读 [ADR-004](file:///d:/PROJ/Quant/docs/adr/ADR-004.md) - 分层存储
2. 查看 [统一存储方案](file:///d:/PROJ/Quant/backend/DATA_UNIFIED_STORAGE_SOLUTION.md)
3. 参考 [`storage_router.py`](file:///d:/PROJ/Quant/backend/app/storage/storage_router.py)

#### 测试 API 接口
1. 启动后端服务：`python backend/main.py`
2. 访问 Swagger UI: http://localhost:8000/docs
3. 在线测试 API

#### 开发新功能
1. 阅读 [ADR 文档](file:///d:/PROJ/Quant/docs/adr/README.md) 了解架构原则
2. 查看 [API 文档](http://localhost:8000/docs) 了解现有接口
3. 参考 [开发者指南](file:///d:/PROJ/Quant/backend/DEVELOPER_GUIDE.md)

---

## 📊 系统架构图

```
┌─────────────────────────────────────────────────┐
│              前端层 (React)                      │
│  - Watchlist, Kline, Screener, Backtest        │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│          API 网关层 (FastAPI + Swagger)          │
│  - 50+ API 端点                                  │
│  - JWT 认证                                     │
│  - 参数验证                                     │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│       数据中台调度层 (核心)                       │
├─────────────────────────────────────────────────┤
│  DataSourceFactory (智能路由)                    │
│  UnifiedDataAdapter (统一适配器)                │
│  StorageRouter (存储路由)                        │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         数据源适配层 (5 个数据源)                  │
│  EFinance | AkShare | Baostock | TickFlow      │
└─────────────────────────────────────────────────┘
```

---

## 🔍 文档搜索

### 按关键词搜索

| 关键词 | 相关文档 |
|--------|---------|
| **数据中台** | ADR-001, DATA_UNIFIED_STORAGE_SOLUTION |
| **智能路由** | ADR-002, MULTI_DATA_SOURCE_SMART_ROUTING |
| **数据模型** | ADR-003, unified_models.py |
| **存储策略** | ADR-004, DATA_UNIFIED_STORAGE_SOLUTION |
| **API 文档** | Swagger UI (/docs), API_AND_ADR_GUIDE |
| **数据源** | DATA_SOURCE_COMPARISON_REPORT_2026 |

---

## 📝 文档维护

### 更新频率
- **API 文档**: 自动生成 (每次代码变更)
- **ADR 文档**: 架构变更时更新
- **技术文档**: 定期维护

### 贡献指南
1. 新增功能时更新 API 文档（自动）
2. 架构变更时创建/更新 ADR
3. 技术改进时更新设计文档
4. 提交 PR 时检查文档完整性

---

## 🎓 学习路径

### 初学者
1. 阅读 [架构总览](file:///d:/PROJ/Quant/docs/adr/README.md#架构总览)
2. 查看 [API 文档](http://localhost:8000/docs)
3. 学习 [ADR-001](file:///d:/PROJ/Quant/docs/adr/ADR-001.md) - 架构基础

### 进阶开发者
1. 精读所有 ADR 文档
2. 研究 [技术设计文档](file:///d:/PROJ/Quant/backend/UNIFIED_DATA_ACCESS_DESIGN.md)
3. 参与架构优化

### 架构师
1. 审查 ADR 决策
2. 优化存储策略
3. 设计新功能和模块

---

**最后更新**: 2026-03-28  
**维护者**: 架构团队  
**文档版本**: 1.0
