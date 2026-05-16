# Quant 量化分析系统 - 开发者文档

**版本**: 3.0.0  
**更新日期**: 2026-04-29  
**技术栈**: FastAPI + React 18 + TypeScript + Rust

---

## 目录

1. [快速开始](#快速开始)
2. [系统架构](#系统架构)
3. [数据源管理](#数据源管理)
4. [API 参考](#api-参考)
5. [存储层](#存储层)
6. [中间件](#中间件)
7. [Rust 引擎](#rust-引擎)
8. [部署指南](#部署指南)
9. [开发指南](#开发指南)
10. [常见问题](#常见问题)

---

## 快速开始

### 环境要求

- Python >= 3.12
- Node.js >= 18
- Rust >= 1.83 (可选，用于编译 Rust 引擎)
- Git

### 后端安装

```bash
cd backend
python -m venv venv
.\venv\Scripts\Activate          # Windows
source venv/bin/activate         # Linux/Mac

pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端安装

```bash
cd frontend
npm install
npm run dev
```

### Rust 引擎编译 (可选)

```bash
cd quantcore/rust-engine
cargo build --release
```

### 访问系统

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/api/v1
- Swagger 文档：http://localhost:8000/docs
- ReDoc 文档：http://localhost:8000/redoc

---

## 系统架构

### 分层架构

```
┌──────────────────────────────────────────────────────────┐
│                  Frontend (React 18 + TS 6)              │
│  Chakra UI + Zustand + React Query + ECharts      │
│  KLineCharts + @tanstack/react-virtual + Sentry         │
└────────────────────────┬─────────────────────────────────┘
                         │ HTTP/REST API
┌────────────────────────▼─────────────────────────────────┐
│                  Backend (FastAPI + Python 3.12+)         │
│  ┌────────────────────────────────────────────────────┐  │
│  │  API Router (229 endpoints, 67 routers)            │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Services (22 services)                            │  │
│  │  - StockService / ChartDataService / SectorService │  │
│  │  - MoneyflowService / ChipService / Screener       │  │
│  │  - FinancialLLMRouter / QwenAssistant              │  │
│  │  - HybridRealtimeService / SmartPollingService     │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  DataSourceManager (统一管理器)                     │  │
│  │  ├── DataSourceFactory (工厂 + 缓存)               │  │
│  │  │   ├── EFinanceAdapter    (东方财富, 默认)       │  │
│  │  │   ├── AkShareAdapter     (开源财经, 122+ 接口)  │  │
│  │  │   ├── BaostockAdapter    (证券宝)               │  │
│  │  │   ├── TickFlowAdapter    (专业数据, WebSocket)  │  │
│  │  │   └── YFinanceAdapter    (Yahoo, 海外)          │  │
│  │  ├── UnifiedDataAdapter  (API + Playwright 降级)    │  │
│  │  ├── SmartDataSourceSwitcher (智能切换)             │  │
│  │  ├── DynamicPriorityManager (动态优先级)            │  │
│  │  └── BatchRequestOptimizer (批量优化)               │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Middleware                                        │  │
│  │  - TokenBucketRateLimiter (限流器)                  │  │
│  │  - CircuitBreaker (断路器)                          │  │
│  │  - PerformanceMonitor (性能监控)                     │  │
│  │  - MetricsCollector (指标收集)                       │  │
│  └────────────────────────────────────────────────────┘  │
│  ┌────────────────────────────────────────────────────┐  │
│  │  Storage Layer                                     │  │
│  │  - SQLite (WAL 模式, 22 ORM 表)                    │  │
│  │  - Parquet (PyArrow, 列式存储)                      │  │
│  │  - LRU Async Cache (内存缓存, 命中率 85%+)          │  │
│  └────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────┘
                         │ PyO3
┌────────────────────────▼─────────────────────────────────┐
│              Rust Engine (quantcore)                      │
│  - BacktestEngine (回测引擎, 20x vs Backtrader)          │
│  - MatchingEngine (订单匹配)                              │
│  - RiskManager + RiskMonitor (风控)                       │
│  - PerformanceAnalyzer (绩效分析)                         │
│  - 21 Technical Indicators (64-73x vs pandas-ta)         │
└──────────────────────────────────────────────────────────┘
```

### 目录结构

```
Quant/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # 67 个 API 路由文件
│   │   ├── adapters/            # 数据源适配器 + 反风控
│   │   ├── services/            # 22 个业务服务
│   │   ├── storage/             # 三层存储
│   │   ├── middleware/          # 4 个中间件
│   │   ├── models/              # 数据模型 (Pydantic + dataclass)
│   │   ├── core/                # 核心计算
│   │   └── config.py            # 配置管理
│   ├── tests/
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── pages/               # 29 个页面组件
│   │   ├── components/          # 通用组件
│   │   ├── services/            # API 服务
│   │   ├── store/               # Zustand 状态管理
│   │   └── hooks/               # 自定义 Hooks
│   └── package.json
├── quantcore/
│   ├── rust-engine/             # Rust 回测引擎 (33 个 .rs 文件)
│   └── python-api/              # PyO3 Python 桥接
├── quantcore-indicators/
│   ├── src/                     # Rust 指标库 (5 个 .rs 文件, 21 指标)
│   └── python/                  # Python 绑定
└── README.md
```

---

## 数据源管理

### 支持的数据源

| 数据源 | 类型 | 费用 | 反风控 | 状态 |
|--------|------|------|--------|------|
| EFinance | 东方财富 | 免费 | ✅ TLS+凭证 | ✅ 默认 |
| AkShare | 开源财经 | 免费 | ✅ TLS+凭证 | ✅ 可用 (122+ 接口) |
| BaoStock | 证券宝 | 免费 | - | ✅ 可用 |
| TickFlow | 专业数据 | 付费 | - | ⚠️ 需配置 |
| YFinance | Yahoo | 免费 | - | ⚠️ 国际数据 |
| Tushare | 金融数据 | 免费 | - | ⚠️ 需 Token |
| Playwright | 浏览器 | 免费 | ✅ 无头浏览器 | ✅ 兜底方案 |

### 数据源优先级

系统配置的数据源优先级（从高到低）：

```python
DATA_SOURCE_PRIORITY = ["efinance", "akshare", "baostock", "tickflow"]
```

### 智能故障转移

```python
from app.adapters.factory import data_source_manager

klines = await data_source_manager.get_kline(
    code="600000",
    start_date="2024-01-01",
    end_date="2024-12-31",
    adjust="qfq"
)
# 自动尝试：efinance → akshare → baostock → tickflow
```

### 临时优先级参数

```http
GET /api/v1/stock/600000/kline?source_priority=efinance,akshare
```

### 反风控策略

系统已集成完整的反风控策略，详见 [ANTI_WIND_README.md](./ANTI_WIND_README.md)

核心防御层级：
1. **TLS 指纹伪装** (curl_cffi, chrome120) — 核心防御
2. **凭证注入模式** (Playwright Cookie → curl_cffi) — 关键机制
3. **智能重试降级** (错误分类 + 指数退避) — 兜底方案
4. **请求频率控制** (自适应延迟) — 基础防御
5. **请求头轮换** (4 个主流浏览器) — 辅助伪装

---

## API 参考

### 核心 API 端点 (229 个)

#### 股票相关 (13 个)
- `GET /stock/{code}` — 股票基本信息
- `GET /stock/{code}/kline` — K 线数据
- `GET /stock/{code}/kline/weekly` — 周线
- `GET /stock/{code}/kline/monthly` — 月线
- `GET /stock/{code}/indicators` — 技术指标
- `GET /stock/{code}/realtime` — 实时行情
- `GET /stock/search` — 搜索股票
- `GET /stock/list` — 股票列表
- `GET /stock/top-list` — 龙虎榜
- `GET /stock/forecast/{code}` — 业绩预告
- `GET /stock/moneyflow/{code}` — 资金流向
- `GET /stock/market/index` — 大盘指数
- `GET /stock/market/realtime` — 大盘实时行情

#### K 线图表 (4 个)
- `GET /kline/{code}` — K 线数据 (含指标)
- `GET /kline/{code}/latest` — 最新 K 线
- `POST /indicators/calculate` — 批量计算指标
- `GET /indicators/list` — 可用指标列表

#### 板块相关 (4 个)
- `GET /sector/list` — 板块列表
- `GET /sector/ranking` — 板块排行
- `GET /sector/components/{code}` — 成分股
- `GET /sector/leaders/{code}` — 领涨股

#### 筹码相关 (4 个)
- `GET /chip/data/{code}` — 筹码数据
- `GET /chip/control-degree/{code}` — 控盘度
- `GET /chip/screen` — 筹码选股
- `GET /chip/ranking` — 筹码排行

#### 选股相关 (6 个)
- `POST /screener/query` — 条件选股
- `GET /screener/market-stats` — 市场统计
- `GET /screener/preset-conditions` — 预设条件

#### 策略回测 (12 个)
- `GET /strategy/list` — 策略列表
- `POST /strategy/create` — 创建策略
- `POST /backtest/run` — 执行回测
- `GET /backtest/result/{id}` — 回测结果

#### 自选股 (5 个)
- `GET /watchlist/list` — 自选列表
- `POST /watchlist/add` — 添加自选
- `DELETE /watchlist/remove/{code}` — 删除自选
- `GET /watchlist/quotes` — 自选股行情

#### 基金相关 (9 个)
- `GET /fund/list` — 基金列表
- `GET /fund/{code}` — 基金详情
- `GET /fund/ranking` — 基金排行
- `GET /fund/position/{code}` — 基金持仓

#### 数据源管理 (9 个)
- `GET /data-source/health` — 健康状态
- `GET /data-source/sources` — 可用数据源
- `POST /data-source/switch` — 切换数据源
- `GET /data-source/stats/{source}` — 数据源统计
- `POST /data-source-control/toggle` — 启用/禁用

#### 东方财富 (6 个)
- 涨跌停 / 千股千评 / 机构调研 / 龙虎榜 / 研报 / 公告

#### 认证 (4 个)
- `POST /auth/login` — 登录
- `POST /auth/logout` — 登出
- `POST /auth/refresh` — 刷新 Token
- `GET /auth/me` — 当前用户

#### 监控 (8 个)
- `GET /metrics/*` — Prometheus 指标

#### 其他
- 市场行情 / 资金流向 / 股东数据 / 财务数据 / 审计日志 / 备份恢复 / 生命周期管理

---

## 存储层

### 三层存储架构

| 层级 | 技术 | 用途 | 特点 |
|------|------|------|------|
| 热数据 | SQLite (WAL) | 元数据 + 近期数据 | 22 个 ORM 表，ACID |
| 温数据 | Parquet (PyArrow) | 历史时序数据 | 列式压缩，高效查询 |
| 缓存 | LRU Async Cache | 高频访问数据 | TTL 过期，命中率 85%+ |

### 核心存储服务

- **UnifiedStorageService** — 统一存储接口
- **ParquetManager** — Parquet 文件管理
- **CacheManager** — 多级缓存管理 (从 UNIFIED_DATA_CONFIGS 加载 11 个缓存)
- **LocalDatabaseService** — SQLite 数据库服务

---

## 中间件

| 中间件 | 类名 | 功能 |
|--------|------|------|
| 限流器 | `TokenBucketRateLimiter` | 令牌桶限流 |
| 断路器 | `CircuitBreaker` | 故障隔离，3 状态切换 |
| 性能监控 | `PerformanceMiddleware` | 请求耗时追踪 |
| 指标收集 | `MetricsCollector` | Prometheus 指标导出 |

---

## Rust 引擎

### quantcore (回测引擎)

| 模块 | Struct | 功能 |
|------|--------|------|
| core | Bar, Tick, Trade, Order, Position, Portfolio | 核心数据结构 |
| engine | BacktestEngine, BacktestEngineV2, MatchingEngine | 回测 + 订单匹配 |
| strategy | StrategyContext, StrategyRunner | 策略执行 |
| risk | RiskManager, RiskMonitor | 风控 + 实时监控 |
| performance | PerformanceAnalyzer, ReportGenerator | 绩效分析 |
| data | DataLoader, DataCache | 数据加载 + 缓存 |

### quantcore-indicators (指标库)

21 个核心指标：MA, EMA, WMA, DEMA, TEMA, HMA, ROC, MACD, RSI, Bollinger, ATR, NATR, CCI, KDJ, OBV, Williams %R, ADX, Stochastic, VWAP, PSAR

**智能选择机制**：Rust 引擎 → TA-Lib → pandas-ta

详见 [quantcore-indicators/README.md](../quantcore-indicators/README.md)

---

## 部署指南

### 开发环境

```bash
# 后端
cd backend
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm run dev
```

### 生产环境

```bash
# Docker
docker-compose up -d

# Gunicorn
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_NAME` | 应用名称 | Quant Analysis System |
| `DEBUG` | 调试模式 | True |
| `DEFAULT_DATA_SOURCE` | 默认数据源 | efinance |
| `SECRET_KEY` | JWT 密钥 | **必须设置** |
| `LOG_LEVEL` | 日志级别 | INFO |
| `TUSHARE_TOKEN` | Tushare Token | 可选 |

---

## 开发指南

### 添加新数据源

1. 创建适配器类 (继承 `BaseDataAdapter`)
2. 注册到 `DataSourceFactory._ADAPTER_CLASSES`
3. 更新 `DataSourceType` 枚举
4. 配置优先级

### 添加新 API 端点

1. 创建路由文件 (`app/api/v1/endpoints/`)
2. 注册路由 (`app/api/v1/__init__.py`)

### 添加新技术指标

1. 在 `quantcore-indicators/src/core.rs` 实现 Rust 版本
2. 在 `pyo3_bindings.rs` 添加 Python 绑定
3. 在 `indicators_manager.py` 注册智能选择规则

---

## 常见问题

### 1. 数据源初始化失败

检查 `.env` 中 `TUSHARE_TOKEN` 是否正确，或切换默认数据源为 `efinance`

### 2. 前端无法连接后端

检查后端是否启动 (http://localhost:8000)，检查 CORS 配置

### 3. Rust 引擎编译失败

确保 Rust >= 1.83，Windows 下建议使用 WSL2 编译

### 4. pandas-ta 安装失败

pandas-ta 不支持 Python 3.14，建议使用 Python 3.12。系统会自动降级到 TA-Lib 或 Rust 指标引擎

### 5. TLS 指纹被识别

```bash
pip install --upgrade curl_cffi
```

详见 [ANTI_WIND_README.md](./ANTI_WIND_README.md)

---

**最后更新**: 2026-04-29  
**文档版本**: v3.0
