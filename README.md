# Quant Analysis System

个人股票量化分析系统 - 支持技术分析、板块分析、筹码选股、策略回测

## 项目结构

```
Quant/
├── backend/                 # 后端服务
│   ├── app/
│   │   ├── api/            # API路由层
│   │   ├── adapters/       # 数据接入层
│   │   ├── core/           # 核心计算层
│   │   ├── models/         # 数据模型
│   │   ├── services/       # 业务服务层
│   │   ├── storage/        # 存储层
│   │   └── config.py       # 配置管理
│   ├── requirements.txt
│   └── main.py
├── frontend/               # 前端应用
│   ├── src/
│   │   ├── components/     # 通用组件
│   │   ├── pages/          # 页面组件
│   │   ├── store/          # Redux状态
│   │   └── services/       # API服务
│   └── package.json
├── data/                   # 数据目录
├── docker-compose.yml
└── README.md
```

## 快速开始

### 后端启动

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 前端启动

```bash
cd frontend
npm install
npm run dev
```

### Docker部署

```bash
docker-compose up -d
```

## API文档

启动后端后访问:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 功能模块

### 1. 基础量化
- 个股基本信息查询
- 历史K线数据获取
- MA/RSI/MACD等技术指标计算
- 自选股管理

### 2. 板块分析
- 行业/概念板块展示
- 板块涨跌幅排行
- 板块成分股查询
- 领涨股自动标记

### 3. 筹码选股
- 股东人数数据获取
- 控盘度计算
- 高控盘股票筛选

### 4. 智能选股
- 多条件组合选股
- 市场统计分析

### 5. 策略管理
- 策略创建与配置
- 参数优化

### 6. 策略回测
- 回测配置
- 绩效指标展示
- 收益曲线可视化

## 技术栈

### 后端
- Python 3.11
- FastAPI
- SQLAlchemy + SQLite
- Pandas / Polars / NumPy
- AkShare / Baostock / yfinance / Tushare

### 前端
- React 18 + TypeScript
- Chakra UI
- Redux Toolkit
- ECharts
- Vite

## 配置说明

复制 `.env.example` 为 `.env` 并配置:

```
TUSHARE_TOKEN=your_token_here
```

## License

MIT
