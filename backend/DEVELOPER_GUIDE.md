# TickFlow 量化交易系统 - 开发者文档

**版本**: 1.0.0  
**更新日期**: 2026-03-20  
**技术栈**: FastAPI + React + TypeScript

---

## 📚 目录

1. [快速开始](#快速开始)
2. [系统架构](#系统架构)
3. [数据源管理](#数据源管理)
4. [API 参考](#api-参考)
5. [数据库设计](#数据库设计)
6. [部署指南](#部署指南)
7. [开发指南](#开发指南)
8. [常见问题](#常见问题)

---

## 🚀 快速开始

### 1. 环境要求

- Python >= 3.12
- Node.js >= 18
- Git

### 2. 后端安装

```bash
cd backend

# 创建虚拟环境
python -m venv venv
.\venv\Scripts\Activate  # Windows
source venv/bin/activate  # Linux/Mac

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置必要的配置

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 前端安装

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

### 4. 访问系统

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/api/v1
- API 文档：http://localhost:8000/docs

---

## 🏗️ 系统架构

### 分层架构

```
┌─────────────────────────────────────────────────┐
│              Frontend (React + TS)              │
│  Chakra UI + Redux Toolkit + ECharts + Vite    │
└───────────────────┬─────────────────────────────┘
                    │ HTTP/REST API
┌───────────────────▼─────────────────────────────┐
│              Backend (FastAPI + Python)          │
│  ┌─────────────────────────────────────────┐    │
│  │  API Router (60+ endpoints)             │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │  Adapters (5 data sources)              │    │
│  │  - efinance (default)                   │    │
│  │  - akshare                              │    │
│  │  - baostock                             │    │
│  │  - tickflow                             │    │
│  │  - yfinance                             │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │  Services (Business Logic)              │    │
│  └─────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────┐    │
│  │  Storage Layer                          │    │
│  │  - SQLite (metadata)                    │    │
│  │  - Parquet (historical data)            │    │
│  │  - Cache (in-memory)                    │    │
│  └─────────────────────────────────────────┘    │
└─────────────────────────────────────────────────┘
```

### 目录结构

```
Quant/
├── backend/
│   ├── app/
│   │   ├── api/v1/endpoints/    # API 路由层
│   │   ├── adapters/            # 数据源适配器
│   │   ├── services/            # 业务逻辑层
│   │   ├── storage/             # 数据存储层
│   │   ├── core/                # 核心功能
│   │   ├── models/              # 数据模型
│   │   └── middleware/          # 中间件
│   ├── tests/                   # 测试文件
│   └── requirements.txt         # 依赖配置
├── frontend/
│   ├── src/
│   │   ├── components/          # 通用组件
│   │   ├── pages/               # 页面组件
│   │   ├── services/            # API 服务
│   │   ├── store/               # Redux 状态管理
│   │   └── hooks/               # 自定义 Hooks
│   └── package.json             # 依赖配置
└── README.md                    # 项目说明
```

---

## 📊 数据源管理

### 支持的数据源

| 数据源 | 类型 | 费用 | 状态 |
|--------|------|------|------|
| EFinance | 东方财富 | 免费 | ✅ 默认 |
| AkShare | 开源财经 | 免费 | ✅ 可用 |
| BaoStock | 证券宝 | 免费 | ✅ 可用 |
| TickFlow | 专业数据 | 付费 | ⚠️ 需配置 |
| YFinance | Yahoo | 免费 | ⚠️ 国际数据 |

### 数据源优先级

系统配置的数据源优先级（从高到低）：

```python
DATA_SOURCE_PRIORITY = ["efinance", "akshare", "baostock", "tickflow"]
```

### 智能故障转移

当高优先级数据源失败时，系统自动尝试下一个数据源：

```python
# 示例：获取 K 线数据
klines = await data_source_manager.get_kline(
    code="600000",
    start_date="2024-01-01",
    end_date="2024-12-31",
    adjust="qfq"
)
# 自动尝试：efinance → akshare → baostock → tickflow
```

### 临时优先级参数

可以在 API 请求时临时指定数据源优先级：

```http
GET /api/v1/stock/600000/kline?source_priority=efinance,akshare
```

---

## 🔌 API 参考

### 核心 API 端点

#### 认证相关
- `POST /auth/login` - 用户登录
- `POST /auth/logout` - 用户登出
- `POST /auth/refresh` - 刷新 Token
- `GET /auth/me` - 获取当前用户信息

#### 股票相关
- `GET /stock/{code}` - 获取股票基本信息
- `GET /stock/{code}/kline` - 获取 K 线数据
- `GET /stock/{code}/kline/weekly` - 获取周线数据
- `GET /stock/{code}/kline/monthly` - 获取月线数据
- `GET /stock/{code}/indicators` - 获取技术指标
- `GET /stock/{code}/realtime` - 获取实时行情
- `GET /stock/search` - 搜索股票

#### 板块相关
- `GET /sector/list` - 获取板块列表
- `GET /sector/ranking` - 获取板块排行
- `GET /sector/components/{code}` - 获取成分股
- `GET /sector/leaders/{code}` - 获取领涨股

#### 筹码相关
- `GET /chip/data/{code}` - 获取筹码数据
- `GET /chip/control-degree/{code}` - 获取控盘度
- `GET /chip/screen` - 筹码选股
- `GET /chip/ranking` - 筹码排行

#### 选股相关
- `POST /screener/query` - 条件选股
- `GET /screener/market-stats` - 市场统计
- `GET /screener/preset-conditions` - 预设条件

#### 策略回测
- `GET /strategy/list` - 策略列表
- `POST /strategy/create` - 创建策略
- `POST /backtest/run` - 执行回测
- `GET /backtest/result/{id}` - 获取回测结果

#### 自选股
- `GET /watchlist/list` - 获取自选列表
- `POST /watchlist/add` - 添加自选
- `DELETE /watchlist/remove/{code}` - 删除自选
- `GET /watchlist/quotes` - 自选股行情

#### 市场行情
- `GET /market/market-ranking` - 市场排行
- `GET /market/market-overview` - 市场概览
- `GET /market/sector-performance` - 板块表现

#### 基金相关
- `GET /fund/list` - 基金列表
- `GET /fund/{code}` - 基金详情
- `GET /fund/ranking` - 基金排行
- `GET /fund/position/{code}` - 基金持仓

### 统一数据适配器 API

#### 基本用法

```python
from app.adapters.unified_adapter import EFinanceUnifiedAdapter

adapter = EFinanceUnifiedAdapter()
await adapter.initialize()

# 获取 K 线数据
klines = await adapter.get_unified_kline(
    code="600000",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# 获取实时行情
quote = await adapter.get_unified_realtime_quote("600000")

# 获取技术指标
indicators = await adapter.get_unified_indicators("600000")
```

#### 核心方法

| 方法 | 说明 | 参数 |
|------|------|------|
| `get_unified_kline()` | 获取 K 线 | code, start_date, end_date, adjust |
| `get_unified_realtime_quote()` | 实时行情 | code |
| `get_unified_indicators()` | 技术指标 | code, indicators |
| `get_unified_stock_list()` | 股票列表 | market |
| `get_unified_stock_info()` | 股票信息 | code |

---

## 🗄️ 数据库设计

### 核心表结构

#### 1. StockInfo - 股票基本信息

```python
class StockInfo:
    code: str          # 股票代码（索引）
    name: str          # 股票名称
    market: str        # 市场（SH/SZ）
    industry: str      # 所属行业
    sector: str        # 所属板块
    area: str          # 地区
    list_date: str     # 上市日期
    total_shares: float  # 总股本
    float_shares: float  # 流通股本
```

#### 2. KLine - K 线数据

```python
class KLine:
    code: str          # 股票代码（索引）
    date: str          # 日期（索引）
    open: float        # 开盘价
    high: float        # 最高价
    low: float         # 最低价
    close: float       # 收盘价
    volume: float      # 成交量
    amount: float      # 成交额
    turnover_rate: float  # 换手率
    adjust_type: str   # 复权类型（qfq/hfq/不复权）
```

#### 3. TechnicalIndicatorDB - 技术指标

```python
class TechnicalIndicatorDB:
    code: str          # 股票代码
    date: str          # 日期
    ma5: float         # 5 日均线
    ma10: float        # 10 日均线
    ma20: float        # 20 日均线
    ma60: float        # 60 日均线
    rsi6: float        # RSI(6)
    rsi12: float       # RSI(12)
    rsi24: float       # RSI(24)
    macd: float        # MACD
    macd_signal: float # MACD 信号线
    macd_hist: float   # MACD 柱状图
```

#### 4. ChipData - 筹码数据

```python
class ChipData:
    code: str          # 股票代码
    date: str          # 日期
    shareholder_count: float  # 股东人数
    avg_shares_per_holder: float  # 户均持股
    control_degree: float  # 控盘度
    concentration: float  # 集中度
```

#### 5. Strategy - 策略配置

```python
class Strategy:
    strategy_id: str   # 策略 ID
    name: str          # 策略名称
    strategy_type: str # 策略类型
    config: str        # 策略配置（JSON）
    is_active: bool    # 是否启用
```

#### 6. BacktestRecord - 回测记录

```python
class BacktestRecord:
    backtest_id: str   # 回测 ID
    strategy_id: str   # 策略 ID
    start_date: str    # 开始日期
    end_date: str      # 结束日期
    initial_capital: float  # 初始资金
    final_capital: float    # 最终资金
    total_return: float     # 总收益率
    annual_return: float    # 年化收益
    max_drawdown: float     # 最大回撤
    sharpe_ratio: float     # 夏普比率
```

### 索引优化

系统为关键查询字段创建了复合索引：

```python
# KLine 表索引
Index("idx_kline_code_date", "code", "date")  # 个股查询
Index("idx_kline_code_adjust", "code", "adjust_type")  # 复权查询
Index("idx_kline_volume_date", "volume", "date")  # 成交量排序
Index("idx_kline_turnover_date", "turnover_rate", "date")  # 换手率排序
```

---

## 🚀 部署指南

### 开发环境部署

#### 1. 后端配置

创建 `.env` 文件：

```env
# 应用配置
APP_NAME=Quant Analysis System
APP_VERSION=1.0.0
DEBUG=True

# 数据库配置
DATABASE_URL=sqlite+aiosqlite:///./data/sqlite/quant.db
DATA_DIR=./data
SQLITE_DIR=./data/sqlite
PARQUET_DIR=./data/parquet

# 数据源配置
DEFAULT_DATA_SOURCE=efinance
DATA_SOURCE_PRIORITY=efinance,akshare,baostock,tickflow

# 认证配置
SECRET_KEY=your-secret-key-here  # 必须设置！
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=./logs/quant.log

# CORS 配置
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]
```

#### 2. 安装依赖

```bash
cd backend

# 完整安装（推荐）
pip install -r requirements.txt

# 最小化安装（快速测试）
pip install -r requirements-minimal.txt

# 开发环境安装
pip install -r requirements-dev.txt
```

#### 3. 初始化数据库

```bash
# 启动应用时自动初始化
uvicorn app.main:app --reload
```

### 生产环境部署

#### 1. 使用 Docker

```bash
# 构建镜像
docker-compose build

# 启动服务
docker-compose up -d

# 查看日志
docker-compose logs -f
```

#### 2. 使用 Gunicorn

```bash
# 安装 gunicorn
pip install gunicorn

# 启动服务
gunicorn app.main:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --timeout 120
```

### 性能优化建议

1. **使用 Redis 缓存**
   - 缓存热点数据（实时行情、技术指标）
   - 减少数据库查询

2. **数据库优化**
   - 定期清理过期数据
   - 使用连接池

3. **前端优化**
   - 启用 CDN
   - 压缩静态资源
   - 使用 Service Worker

---

## 💻 开发指南

### 添加新的数据源

1. 创建适配器类：

```python
# adapters/new_adapter.py
from .base import BaseDataAdapter

class NewAdapter(BaseDataAdapter):
    async def initialize(self) -> bool:
        # 初始化逻辑
        return True
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        # 获取股票信息
        pass
    
    async def get_kline(self, code: str, ...) -> List[KLineData]:
        # 获取 K 线数据
        pass
```

2. 注册到工厂：

```python
# adapters/factory.py
adapters_config = {
    DataSourceType.NEW_ADAPTER: (NewAdapter, True),
}
```

3. 更新配置：

```python
# config.py
DATA_SOURCE_PRIORITY = ["new_adapter", "efinance", ...]
```

### 添加新的 API 端点

1. 创建路由文件：

```python
# api/v1/endpoints/new_feature.py
from fastapi import APIRouter, Depends

router = APIRouter()

@router.get("/new-feature")
async def get_new_feature(current_user: User = Depends(get_current_user)):
    return {"feature": "data"}
```

2. 注册路由：

```python
# api/v1/__init__.py
api_router.include_router(new_feature_router, prefix="/new-feature", tags=["新特性"])
```

### 添加新的技术指标

```python
# services/indicators.py
def calculate_custom_indicator(df: pd.DataFrame) -> pd.Series:
    """计算自定义指标"""
    # 实现计算逻辑
    result = df['close'].rolling(window=20).mean()
    return result
```

---

## ❓ 常见问题

### 1. 数据源初始化失败

**问题**: `Tushare 连接测试失败：抱歉，您没有接口访问权限`

**解决方案**:
- 检查 `.env` 文件中的 `TUSHARE_TOKEN` 是否正确
- 确认 Tushare 积分是否足够
- 或者切换默认数据源为 `efinance`

### 2. 数据库文件不存在

**问题**: `sqlite3.OperationalError: unable to open database file`

**解决方案**:
```bash
# 创建数据目录
mkdir -p backend/data/sqlite
mkdir -p backend/data/parquet
```

### 3. 前端无法连接后端

**问题**: `Network Error` 或 `CORS error`

**解决方案**:
- 检查后端是否启动（http://localhost:8000）
- 检查 `.env` 中的 `CORS_ORIGINS` 配置
- 确认前端 API 配置正确

### 4. K 线数据加载慢

**问题**: 数据加载时间过长

**解决方案**:
- 使用按需加载模式（Lazy Loading）
- 缩小日期范围
- 检查网络连接

### 5. Token 刷新失败

**问题**: `401 Unauthorized`

**解决方案**:
- 清除浏览器缓存
- 重新登录
- 检查 `SECRET_KEY` 配置

---

## 📝 附录

### A. 环境变量说明

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `APP_NAME` | 应用名称 | Quant Analysis System |
| `DEBUG` | 调试模式 | True |
| `DEFAULT_DATA_SOURCE` | 默认数据源 | efinance |
| `SECRET_KEY` | JWT 密钥 | **必须设置** |
| `LOG_LEVEL` | 日志级别 | INFO |

### B. 数据源对比

| 特性 | EFinance | AkShare | BaoStock | TickFlow |
|------|----------|---------|----------|----------|
| 费用 | 免费 | 免费 | 免费 | 付费 |
| 实时行情 | ✅ | ✅ | ❌ | ✅ |
| K 线数据 | ✅ | ✅ | ✅ | ✅ |
| 财务数据 | ⚠️ | ✅ | ✅ | ✅ |
| 稳定性 | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

### C. 性能指标

| 指标 | 目标值 | 当前值 |
|------|--------|--------|
| API 响应时间 | < 200ms | ~150ms |
| K 线加载时间 | < 2s | ~1.5s |
| 实时行情更新 | < 1s | ~500ms |
| 数据库查询 | < 50ms | ~30ms |

---

## 🔗 相关资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [React 官方文档](https://react.dev/)
- [TypeScript 官方文档](https://www.typescriptlang.org/)
- [ECharts 官方文档](https://echarts.apache.org/)

---

**文档维护者**: TickFlow Team  
**最后更新**: 2026-03-20
