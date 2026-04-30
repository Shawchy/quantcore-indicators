# Quant 量化分析系统

个人全栈量化分析平台 — 支持技术分析、板块分析、筹码选股、策略回测、Rust 高性能引擎

## 项目架构

```
Quant/
├── backend/                    # 后端服务 (FastAPI + Python 3.12+)
│   ├── app/
│   │   ├── api/v1/endpoints/  # API 路由层 (229 个端点)
│   │   ├── adapters/          # 数据接入层 (7 大数据源)
│   │   ├── services/          # 业务服务层 (22 个服务)
│   │   ├── storage/           # 存储层 (SQLite + Parquet + Cache)
│   │   ├── middleware/        # 中间件 (限流/断路器/监控)
│   │   ├── models/            # 数据模型
│   │   └── core/              # 核心计算层
│   ├── tests/
│   └── requirements.txt
├── frontend/                   # 前端应用 (React 18 + TypeScript)
│   ├── src/
│   │   ├── pages/             # 页面组件 (29 个页面)
│   │   ├── components/        # 通用组件
│   │   ├── services/          # API 服务
│   │   ├── store/             # Redux 状态管理
│   │   └── hooks/             # 自定义 Hooks
│   └── package.json
├── quantcore/                  # Rust 量化引擎
│   ├── rust-engine/           # 回测引擎 + 风控 + 绩效分析
│   └── python-api/            # PyO3 Python 桥接
└── quantcore-indicators/       # Rust 技术指标库
    ├── src/                   # 21 个核心指标 (numpy 零拷贝)
    └── python/                # Python 绑定
```

## 技术栈

### 后端
- **Python 3.12+** / FastAPI / Uvicorn
- **数据源**: EFinance / AkShare / BaoStock / TickFlow / YFinance / Tushare / Playwright
- **存储**: SQLite (WAL) + Parquet (PyArrow) + LRU 异步缓存
- **指标**: Rust 引擎 → TA-Lib → pandas-ta 智能降级
- **反风控**: TLS 指纹伪装 + 凭证注入 + Playwright 兜底
- **中间件**: 限流器 / 断路器 / 性能监控 / 指标收集

### 前端
- **React 18** + TypeScript 6 + Vite 6
- **Chakra UI** + Emotion
- **Redux Toolkit** + React Query
- **ECharts** + KLineCharts + Recharts
- **@tanstack/react-virtual** (虚拟列表)
- **Sentry** (错误监控)

### Rust 引擎
- **Rust 1.83+** / PyO3 0.28
- 回测引擎 (20x 性能提升 vs Backtrader)
- 21 个技术指标 (WMA/CCI 64-73x 加速 vs pandas-ta)
- numpy 零拷贝数据传输

## 快速开始

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Linux/Mac
.\venv\Scripts\Activate         # Windows

pip install -r requirements.txt
cp .env.example .env            # 配置环境变量
uvicorn app.main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

### Rust 引擎 (可选)

```bash
cd quantcore/rust-engine
cargo build --release
```

## 功能模块

### 数据接入 (7 大数据源)
| 数据源 | 类型 | 反风控 | 说明 |
|--------|------|--------|------|
| EFinance | 东方财富 | ✅ TLS+凭证 | 默认主力 |
| AkShare | 开源财经 | ✅ TLS+凭证 | 122+ 接口 |
| BaoStock | 证券宝 | - | 历史数据 |
| TickFlow | 专业数据 | - | WebSocket 实时 |
| YFinance | Yahoo | - | 海外市场 |
| Tushare | 金融数据 | - | Token 管理 |
| Playwright | 浏览器 | ✅ 无头浏览器 | 反爬兜底 |

### 核心功能
- **行情分析** — 实时行情 / K线图 / 技术指标 / 板块分析
- **筹码选股** — 股东人数 / 控盘度 / 筹码分布
- **智能选股** — 多条件组合 / 市场统计
- **策略回测** — Rust 引擎 / 绩效分析 / 风险评估
- **东方财富** — 涨跌停 / 千股千评 / 机构调研 / 龙虎榜
- **基金分析** — 基金排行 / 持仓 / 阶段涨幅
- **资金流向** — 大盘资金 / 板块资金 / 个股资金
- **LLM 集成** — Qwen 助手 / 金融情感分析 / 信号融合

### 前端页面 (29 个)
Dashboard / StockDetail / Watchlist / SectorAnalysis / ChipSelection / Screener / Strategy / Backtest / DailyMarket / MarketRanking / Billboard / EastMoney (6 页面) / Fund (5 页面) 等

## API 文档

启动后端后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 文档索引

| 文档 | 说明 |
|------|------|
| [backend/DEVELOPER_GUIDE.md](backend/DEVELOPER_GUIDE.md) | 后端开发者指南 |
| [backend/API_REFERENCE.md](backend/API_REFERENCE.md) | 数据适配器 API 参考 |
| [backend/DEPENDENCIES_GUIDE.md](backend/DEPENDENCIES_GUIDE.md) | 依赖安装指南 |
| [backend/ANTI_WIND_README.md](backend/ANTI_WIND_README.md) | 反风控策略说明 |
| [KLINE_CHART_USAGE.md](KLINE_CHART_USAGE.md) | K线图使用指南 |
| [KLINE_CHART_ARCHITECTURE.md](KLINE_CHART_ARCHITECTURE.md) | K线图架构设计 |
| [WEBSOCKET_GUIDE.md](WEBSOCKET_GUIDE.md) | WebSocket 方案 |
| [EASTMONEY_FEATURE.md](EASTMONEY_FEATURE.md) | 东方财富功能 |
| [CHANGELOG_EASTMONEY.md](CHANGELOG_EASTMONEY.md) | 东方财富更新日志 |
| [quantcore/README.md](quantcore/README.md) | Rust 引擎文档 |
| [quantcore-indicators/README.md](quantcore-indicators/README.md) | 指标库文档 |

## License

MIT
