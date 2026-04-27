# API 文档和架构决策记录使用指南

## 📚 文档导航

### 1. API Swagger 文档

#### 访问方式
启动后端服务后，访问以下 URL 查看 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

#### 功能特性
- ✅ 完整的 API 接口文档
- ✅ 在线测试功能
- ✅ 请求/响应示例
- ✅ 参数验证规则
- ✅ 认证说明
- ✅ 50+ API 标签分类

#### 文档内容
Swagger 文档包含以下模块：

1. **认证** - JWT Token 获取和验证
2. **个股信息** - 股票基础数据、财务数据
3. **板块分析** - 行业板块、概念板块
4. **筹码选股** - 筹码分布、股东人数
5. **资金流向** - 个股/市场/板块资金流
6. **策略回测** - 策略管理、回测系统
7. **市场行情** - 实时行情、市场统计
8. **数据源管理** - 数据源健康检查、性能统计
9. **技术指标** - MA/MACD/RSI/KDJ 等指标计算
10. **K 线图表** - 日/周/月/分钟 K 线数据

---

### 2. 架构决策记录 (ADR)

#### 目录位置
```
docs/adr/
├── README.md              # ADR 索引和架构总览
├── ADR-001.md            # 数据中台架构选择
├── ADR-002.md            # 多数据源智能路由策略
├── ADR-003.md            # 统一数据模型设计
└── ADR-004.md            # 分层存储策略
```

#### ADR 文档说明

##### ADR-001: 数据中台架构选择
**解决的问题**:
- 多数据源接入导致代码复杂
- 前端耦合数据源差异
- 扩展困难

**核心决策**:
- 采用轻量化数据中台架构
- 实现 DataSourceFactory 智能路由
- 实现 UnifiedDataAdapter 统一适配器
- 实现 StorageRouter 存储路由

**代码位置**:
- [`backend/app/adapters/factory.py`](file:///d:/PROJ/Quant/backend/app/adapters/factory.py)
- [`backend/app/adapters/unified_adapter.py`](file:///d:/PROJ/Quant/backend/app/adapters/unified_adapter.py)

##### ADR-002: 多数据源智能路由策略
**解决的问题**:
- 单一数据源风险
- 数据质量波动
- 响应速度差异

**核心决策**:
- 实现智能路由 + 降级链机制
- 配置数据源优先级
- 实现健康检查机制
- 场景化路由配置

**性能提升**:
- 平均响应时间：3500ms → 650ms (81% ↓)
- 成功率：85% → 99% (16% ↑)

**代码位置**:
- [`backend/app/adapters/factory.py`](file:///d:/PROJ/Quant/backend/app/adapters/factory.py)
- [`backend/app/utils/data_source_health.py`](file:///d:/PROJ/Quant/backend/app/utils/data_source_health.py)

##### ADR-003: 统一数据模型设计
**解决的问题**:
- 字段命名不一致
- 数据格式差异
- 数据质量参差

**核心决策**:
- 设计 100+ Pydantic 统一模型
- 实现 DataNormalizer 标准化器
- 实现数据验证器
- 质量评分机制

**模型体系**:
- UnifiedKLine (K 线)
- UnifiedRealtimeQuote (实时行情)
- TechnicalIndicator (技术指标)
- StockFinancialIndicator (86 个财务指标)
- 等 100+ 模型

**代码位置**:
- [`backend/app/models/unified_models.py`](file:///d:/PROJ/Quant/backend/app/models/unified_models.py)
- [`backend/app/utils/data_normalizer.py`](file:///d:/PROJ/Quant/backend/app/utils/data_normalizer.py)

##### ADR-004: 分层存储策略
**解决的问题**:
- 数据量大 (50GB+)
- 查询性能要求高
- 存储成本高

**核心决策**:
- 热数据 (<90 天): SQLite
- 温数据 (>90 天): Parquet (snappy 压缩)
- 实时数据：LRU Cache
- 统一存储路由接口

**性能提升**:
- 平均查询时间：350ms → 25ms (93% ↓)
- 存储空间：50GB → 15GB (70% ↓)
- 缓存命中率：87%

**代码位置**:
- [`backend/app/storage/storage_router.py`](file:///d:/PROJ/Quant/backend/app/storage/storage_router.py)
- [`backend/app/storage/sqlite.py`](file:///d:/PROJ/Quant/backend/app/storage/sqlite.py)
- [`backend/app/storage/parquet_manager.py`](file:///d:/PROJ/Quant/backend/app/storage/parquet_manager.py)

---

## 🏗️ 架构总览

```
┌─────────────────────────────────────────────────┐
│              前端层 (React + TypeScript)          │
│  - 组件库、状态管理、WebSocket                   │
└──────────────────┬──────────────────────────────┘
                   │ REST API / WebSocket
┌──────────────────▼──────────────────────────────┐
│          API 网关层 (FastAPI + Swagger)          │ ⭐ 文档化
│  - Swagger 文档                                  │
│  - JWT 认证                                     │
│  - 参数验证                                     │
│  - 性能监控                                     │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│       数据中台调度层 (核心架构)                   │ ⭐ 智能化
├─────────────────────────────────────────────────┤
│ 1️⃣ DataSourceFactory - 智能路由                 │
│    - 主备源选择 (ADR-002)                       │
│    - 故障降级                                   │
├─────────────────────────────────────────────────┤
│ 2️⃣ UnifiedDataAdapter - 统一适配器              │
│    - 数据标准化 (ADR-003)                       │
│    - 质量验证                                   │
│    - 指标计算                                   │
├─────────────────────────────────────────────────┤
│ 3️⃣ StorageRouter - 存储路由                     │
│    - SQLite (热数据 <90 天) (ADR-004)            │
│    - Parquet (温数据 >90 天)                    │
│    - LRU Cache (实时缓存)                       │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│         数据源适配层 (5 个数据源)                  │
│  - EFinance (主力)                               │
│  - AkShare (主力)                                │
│  - Baostock (主力)                               │
│  - TickFlow (可选)                               │
└─────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 查看 API 文档
```bash
# 启动后端服务
cd backend
python main.py

# 访问 Swagger UI
http://localhost:8000/docs

# 访问 ReDoc
http://localhost:8000/redoc
```

### 2. 阅读 ADR 文档
```bash
# 查看 ADR 索引
cat docs/adr/README.md

# 查看具体 ADR
cat docs/adr/ADR-001.md  # 数据中台架构
cat docs/adr/ADR-002.md  # 智能路由
cat docs/adr/ADR-003.md  # 统一模型
cat docs/adr/ADR-004.md  # 分层存储
```

### 3. 代码示例

#### 调用 K 线 API (Swagger 测试)
```http
GET /api/v1/kline/000001?k_type=daily&start_date=2024-01-01&end_date=2024-12-31&indicators=MA,MACD,RSI&adjust=qfq
Authorization: Bearer <your_token>
```

#### 查看数据源健康状态
```http
GET /api/v1/data-source/health
Authorization: Bearer <your_token>
```

---

## 📖 相关文档

### 技术文档
- [开发者指南](file:///d:/PROJ/Quant/backend/DEVELOPER_GUIDE.md)
- [API 参考手册](file:///d:/PROJ/Quant/backend/API_REFERENCE.md)
- [数据源对比报告](file:///d:/PROJ/Quant/backend/DATA_SOURCE_COMPARISON_REPORT_2026.md)
- [统一存储方案](file:///d:/PROJ/Quant/backend/DATA_UNIFIED_STORAGE_SOLUTION.md)

### 业务文档
- [数据源场景优化](file:///d:/PROJ/Quant/backend/DATA_SOURCE_SCENARIO_OPTIMIZATION.md)
- [多数据源智能路由](file:///d:/PROJ/Quant/backend/MULTI_DATA_SOURCE_SMART_ROUTING.md)

---

## 🎯 最佳实践

### 1. 使用 Swagger 文档
- ✅ 在线测试 API 接口
- ✅ 查看请求/响应示例
- ✅ 了解参数验证规则
- ✅ 学习认证流程

### 2. 参考 ADR 决策
- ✅ 理解架构设计思路
- ✅ 学习技术选型理由
- ✅ 了解权衡分析
- ✅ 遵循设计原则

### 3. 扩展开发
- ✅ 新增数据源：参考 ADR-001，添加适配器
- ✅ 新增业务：参考 ADR-003，定义统一模型
- ✅ 优化存储：参考 ADR-004，调整存储策略

---

## 📝 文档维护

### 更新 Swagger 文档
Swagger 文档会自动从 FastAPI 路由和 Pydantic 模型生成，无需手动维护。

### 新增 ADR 文档
1. 复制 ADR 模板
2. 填写决策内容
3. 更新 README.md 索引
4. 提交代码审查

### ADR 模板
```markdown
# ADR-XXX: 标题

## 状态
[已采纳 | 讨论中 | 已废弃]

## 背景
为什么要做这个决策

## 决策
具体选择了什么方案

## 后果
### 正面影响
- 好处列表

### 负面影响
- 代价列表

## 参考链接
- 代码位置
- 相关文档
```

---

**最后更新**: 2026-03-28  
**维护者**: 架构团队
