# 统一数据适配器 API 参考

**版本:** 2.0  
**更新日期:** 2026-04-29

---

## 目录

1. [快速开始](#快速开始)
2. [DataSourceManager](#datasourcemanager)
3. [DataSourceFactory](#datasourcefactory)
4. [BaseDataAdapter](#basedataadapter)
5. [数据模型](#数据模型)
6. [使用示例](#使用示例)

---

## 快速开始

### 基本用法

```python
from app.adapters.factory import data_source_manager

# 获取 K 线数据（自动故障转移）
klines = await data_source_manager.get_kline(
    code="600000",
    start_date="2024-01-01",
    end_date="2024-12-31",
    adjust="qfq"
)

# 获取实时行情
quote = await data_source_manager.get_realtime_quote("600000")

# 获取股票列表
stocks = await data_source_manager.get_stock_list()

# 指定数据源
klines = await data_source_manager.get_kline(
    code="600000",
    source_type="akshare"
)
```

---

## DataSourceManager

统一数据源管理器，核心业务接口。

### 获取方式

```python
from app.adapters.factory import data_source_manager
```

### 核心方法

#### 股票数据

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_stock_list(market=None, source_type=None)` | `list[StockBasicInfo]` | 获取股票列表 |
| `get_stock_info(code, source_type=None)` | `Optional[StockBasicInfo]` | 获取股票信息 |
| `get_kline(code, start_date, end_date, adjust, source_type=None)` | `list[KLineData]` | 获取 K 线数据 |
| `get_market_index_kline(index_code, start_date, end_date, source_type=None)` | `list[KLineData]` | 获取指数 K 线 |
| `get_realtime_quote(code, source_type=None)` | `Dict[str, Any]` | 获取实时行情 |
| `get_market_realtime_quotes(market_types, source_type=None)` | `list` | 获取市场行情列表 |

#### 板块数据

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_sector_list(sector_type, source_type=None)` | `list[SectorInfo]` | 获取板块列表 |
| `get_sector_components(sector_code, source_type=None)` | `list[str]` | 获取板块成分股 |

#### 筹码数据

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_chip_data(code, start_date, end_date, source_type=None)` | `list[ChipData]` | 获取筹码数据 |

#### 基金数据

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_fund_codes(fund_type, source_type=None)` | `list[dict]` | 获取基金代码列表 |
| `get_fund_base_info(fund_codes, source_type=None)` | `Union[FundInfo, list[FundInfo]]` | 获取基金基本信息 |
| `get_fund_realtime_increase_rate(fund_codes, source_type=None)` | `Union[dict, list[dict]]` | 获取基金实时涨跌幅 |
| `get_fund_quote_history(fund_code, pz, source_type=None)` | `list[dict]` | 获取基金历史行情 |
| `get_fund_quote_history_multi(fund_codes, pz, source_type=None)` | `dict` | 获取多只基金历史行情 |
| `get_fund_invest_position(fund_code, dates, source_type=None)` | `list[dict]` | 获取基金持仓 |
| `get_fund_period_change(fund_code, source_type=None)` | `list[dict]` | 获取基金阶段涨跌幅 |
| `get_fund_types_percentage(fund_code, dates, source_type=None)` | `list[dict]` | 获取基金持仓类型占比 |

#### 资金流向

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_today_bill(trade_date, source_type=None)` | `list` | 获取今日资金流向 |
| `get_history_bill(code, start_date, end_date, source_type=None)` | `list` | 获取历史资金流向 |

#### 财务数据

| 方法 | 返回类型 | 说明 |
|------|---------|------|
| `get_top10_stock_holder_info(code, top, source_type=None)` | `list` | 获取前十大股东 |

### 内部机制

- **故障转移**：`_try_sources(data_type, method_name, *args, **kwargs)` — 按优先级尝试多个数据源
- **动态优先级**：`_get_source_priority(data_type)` — 根据数据类型获取优先级列表
- **批量优化**：集成 `BatchRequestOptimizer`
- **智能预加载**：集成 `SmartPreloader`

---

## DataSourceFactory

数据源工厂，管理适配器实例的创建和缓存。

### 核心方法

| 方法 | 说明 |
|------|------|
| `async initialize(default_source=None)` | 初始化所有启用的适配器 |
| `get_adapter(source_type=None)` | 获取适配器（支持降级） |
| `get_available_sources()` | 获取可用数据源列表 |
| `async close_all()` | 关闭所有适配器 |

### 适配器注册

```python
_ADAPTER_CLASSES = {
    DataSourceType.AKSHARE: AkShareAdapter,
    DataSourceType.BAOSTOCK: BaostockAdapter,
    DataSourceType.EFINANCE: EFinanceAdapter,
    DataSourceType.TICKFLOW: TickFlowAdapter,
    DataSourceType.YFINANCE: YFinanceAdapter,
}
```

---

## BaseDataAdapter

所有数据源适配器的抽象基类。

### 抽象方法（子类必须实现）

| 方法 | 说明 |
|------|------|
| `source_type -> DataSourceType` | 返回数据源类型枚举 |
| `async initialize() -> bool` | 初始化适配器 |
| `async close() -> None` | 关闭适配器 |
| `async get_stock_list(market) -> List[StockBasicInfo]` | 获取股票列表 |
| `async get_stock_info(code) -> Optional[StockBasicInfo]` | 获取股票信息 |
| `async get_kline(code, start_date, end_date, adjust, period) -> List[KLineData]` | 获取 K 线数据 |

### 内置功能

- **智能缓存**：`_get_from_cache()` / `_save_to_cache()` — TTL 过期 + LRU 淘汰
- **持久化**：`_get_from_sqlite()` / `_save_to_parquet()` — SQLite + Parquet 双存储
- **异步上下文**：`async with adapter:` 支持

### 适配器实现

| 适配器 | 数据源 | 特点 |
|--------|--------|------|
| `EFinanceAdapter` | 东方财富 | 默认主力，TLS 指纹 + 凭证注入 |
| `AkShareAdapter` | 开源财经 | 122+ 接口，TLS 指纹 + 凭证注入 |
| `BaostockAdapter` | 证券宝 | 稳定历史数据 |
| `TickFlowAdapter` | 专业数据 | WebSocket 实时推送 |
| `YFinanceAdapter` | Yahoo | 海外市场 |
| `UnifiedDataAdapter` | AKShare + Playwright | API/浏览器自动降级 |

---

## 数据模型

### 适配器层数据模型 (dataclass)

#### StockBasicInfo

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | str | 股票代码 |
| `name` | str | 股票名称 |
| `market` | str | 市场 |
| `industry` | str | 行业 |
| `sector` | str | 板块 |
| `area` | str | 地区 |
| `list_date` | str | 上市日期 |
| `total_shares` | float | 总股本 |
| `float_shares` | float | 流通股本 |

#### KLineData

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | str | 股票代码 |
| `date` | str | 日期 |
| `open` | float | 开盘价 |
| `high` | float | 最高价 |
| `low` | float | 最低价 |
| `close` | float | 收盘价 |
| `volume` | float | 成交量 |
| `amount` | float | 成交额 |
| `turnover_rate` | float | 换手率 |
| `pre_close` | float | 昨收价 |

#### MarketQuote

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | str | 股票代码 |
| `name` | str | 股票名称 |
| `price` | float | 最新价 |
| `change_pct` | float | 涨跌幅 |
| `volume` | float | 成交量 |
| `amount` | float | 成交额 |
| `pe_ratio` | float | 市盈率 |
| `total_market_cap` | float | 总市值 |
| `float_market_cap` | float | 流通市值 |

### 统一数据模型 (Pydantic)

#### UnifiedKLine

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | str | 股票代码 |
| `date` | str | 日期 |
| `open/high/low/close` | float | OHLC |
| `volume` | float | 成交量 |
| `amount` | float | 成交额 |
| `turnover_rate` | float | 换手率 |
| `adjust_type` | AdjustType | 复权类型 |
| `source` | DataSourceType | 数据来源 |
| `quality_score` | float | 质量评分 |

#### AdjustType 枚举

| 值 | 说明 |
|----|------|
| `QFQ` | 前复权 |
| `HFQ` | 后复权 |
| `NONE` | 不复权 |

#### MarketType 枚举

| 值 | 说明 |
|----|------|
| `SH` | 上海 |
| `SZ` | 深圳 |
| `BJ` | 北京 |

---

## 使用示例

### 基本数据获取

```python
from app.adapters.factory import data_source_manager

klines = await data_source_manager.get_kline(
    code="600000",
    start_date="2024-01-01",
    end_date="2024-12-31",
    adjust="qfq"
)
```

### 指定数据源

```python
klines = await data_source_manager.get_kline(
    code="600000",
    start_date="2024-01-01",
    end_date="2024-12-31",
    source_type="akshare"
)
```

### 直接使用适配器

```python
from app.adapters.factory import DataSourceFactory

await DataSourceFactory.initialize()
adapter = DataSourceFactory.get_adapter("efinance")
klines = await adapter.get_kline(code="600000", start_date="2024-01-01")
```

### 批量优化

```python
from app.adapters.batch_optimizer import DataSourceBatchAdapter

batch_adapter = DataSourceBatchAdapter(adapter)
results = await batch_adapter.get_kline_batch(
    codes=["600000", "000001", "300750"],
    start_date="2024-01-01",
    end_date="2024-12-31"
)
```

---

**文档版本:** 2.0  
**最后更新:** 2026-04-29
