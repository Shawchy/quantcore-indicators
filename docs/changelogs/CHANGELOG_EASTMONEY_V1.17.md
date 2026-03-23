# 东方财富网数据接口更新日志 v1.17

## 版本信息
- **版本号**: v1.17
- **发布日期**: 2026-03-21
- **功能主题**: 深交所标的证券信息、东方财富盈利预测与行业板块数据

## 新增功能

### 1. 深圳证券交易所 - 标的证券信息

#### 接口信息
- **接口**: `stock_margin_underlying_info_szse`
- **端点**: `GET /api/v1/eastmoney/stock-margin-underlying-info-szse/{date}`
- **参数**:
  - `date`: 交易日期，格式 YYYYMMDD
- **描述**: 获取深圳证券交易所融资融券标的证券信息，包含融资标的、融券标的、当日可融资、当日可融券等信息

#### 数据字段
| 字段名称 | 类型 | 描述 |
|---------|------|------|
| stock_code | string | 证券代码 |
| stock_name | string | 证券简称 |
| margin_target | string | 融资标的（Y/N） |
| short_target | string | 融券标的（Y/N） |
| margin_available_today | string | 当日可融资（Y/N） |
| short_available_today | string | 当日可融券（Y/N） |
| short_sell_price_restriction | string | 融券卖出价格限制 |
| price_limit | string | 涨跌幅限制 |

#### 示例
```typescript
// 前端调用
const data = await eastMoneyApi.getStockMarginUnderlyingInfoSzse('20210727');
```

---

### 2. 东方财富网 - 盈利预测

#### 接口信息
- **接口**: `stock_profit_forecast_em`
- **端点**: `GET /api/v1/eastmoney/stock-profit-forecast-em`
- **参数**:
  - `symbol`: 行业板块名称，可选，默认为空（获取全部数据）
- **描述**: 获取东方财富网数据中心研究报告的盈利预测数据，包含机构评级和每股收益预测

#### 数据字段
| 字段名称 | 类型 | 描述 |
|---------|------|------|
| serial_number | int | 序号 |
| stock_code | string | 代码 |
| stock_name | string | 名称 |
| report_count | int | 研报数 |
| buy_rating | float | 买入评级数量 |
| add_rating | float | 增持评级数量 |
| neutral_rating | float | 中性评级数量 |
| reduce_rating | int | 减持评级数量 |
| sell_rating | int | 卖出评级数量 |
| eps_2022 | float | 2022 预测每股收益 |
| eps_2023 | float | 2023 预测每股收益 |
| eps_2024 | float | 2024 预测每股收益 |
| eps_2025 | float | 2025 预测每股收益 |

#### 示例
```typescript
// 获取全部盈利预测
const allData = await eastMoneyApi.getStockProfitForecastEm();

// 获取特定行业
const industryData = await eastMoneyApi.getStockProfitForecastEm('船舶制造');
```

---

### 3. 东方财富 - 行业板块

#### 接口信息
- **接口**: `stock_board_industry_name_em`
- **端点**: `GET /api/v1/eastmoney/stock-board-industry-name-em`
- **描述**: 获取东方财富沪深京行业板块的实时行情数据

#### 数据字段
| 字段名称 | 类型 | 描述 |
|---------|------|------|
| rank | int | 排名 |
| board_name | string | 板块名称 |
| board_code | string | 板块代码 |
| latest_price | float | 最新价 |
| change_amount | float | 涨跌额 |
| change_percent | float | 涨跌幅（%） |
| total_market_value | int | 总市值 |
| turnover_rate | float | 换手率（%） |
| rise_count | int | 上涨家数 |
| fall_count | int | 下跌家数 |
| leading_stock | string | 领涨股票 |
| leading_stock_change_percent | float | 领涨股票涨跌幅（%） |

#### 示例
```typescript
// 获取行业板块列表
const boards = await eastMoneyApi.getStockBoardIndustryNameEm();
```

---

### 4. 东方财富 - 行业板块实时行情

#### 接口信息
- **接口**: `stock_board_industry_spot_em`
- **端点**: `GET /api/v1/eastmoney/stock-board-industry-spot-em/{symbol}`
- **参数**:
  - `symbol`: 板块名称，如"小金属"
- **描述**: 获取指定行业板块的实时行情详细数据

#### 数据字段
| 字段名称 | 类型 | 描述 |
|---------|------|------|
| item | string | 项目（最新、最高、最低、开盘等） |
| value | float | 数值 |

#### 示例
```typescript
// 获取小金属板块实时行情
const spotData = await eastMoneyApi.getStockBoardIndustrySpotEm('小金属');
```

---

### 5. 东方财富 - 行业板块成份股

#### 接口信息
- **接口**: `stock_board_industry_cons_em`
- **端点**: `GET /api/v1/eastmoney/stock-board-industry-cons-em/{symbol}`
- **参数**:
  - `symbol`: 板块名称或板块代码，如"小金属"或"BK1027"
- **描述**: 获取指定行业板块的所有成份股数据

#### 数据字段
| 字段名称 | 类型 | 描述 |
|---------|------|------|
| serial_number | int | 序号 |
| stock_code | string | 代码 |
| stock_name | string | 名称 |
| latest_price | float | 最新价 |
| change_percent | float | 涨跌幅（%） |
| change_amount | float | 涨跌额 |
| volume | float | 成交量（手） |
| amount | float | 成交额 |
| amplitude | float | 振幅（%） |
| high | float | 最高 |
| low | float | 最低 |
| open | float | 今开 |
| prev_close | float | 昨收 |
| turnover_rate | float | 换手率（%） |
| pe_ratio_dynamic | float | 市盈率 - 动态 |
| pb_ratio | float | 市净率 |

#### 示例
```typescript
// 获取小金属板块成份股
const consData = await eastMoneyApi.getStockBoardIndustryConsEm('小金属');

// 使用板块代码
const consDataByCode = await eastMoneyApi.getStockBoardIndustryConsEm('BK1027');
```

---

## 技术实现

### 后端变更

#### 1. 数据模型 (`backend/app/models/unified_models.py`)
新增 5 个 Pydantic 数据模型：
- `StockMarginUnderlyingInfoSzse`: 深交所标的证券信息
- `StockProfitForecastEm`: 东方财富盈利预测
- `StockBoardIndustryNameEm`: 东方财富行业板块
- `StockBoardIndustrySpotEm`: 行业板块实时行情
- `StockBoardIndustryConsEm`: 行业板块成份股

#### 2. 适配器 (`backend/app/adapters/eastmoney_adapter.py`)
新增 5 个异步方法：
- `get_stock_margin_underlying_info_szse(date)`: 获取深交所标的证券信息
- `get_stock_profit_forecast_em(symbol)`: 获取盈利预测
- `get_stock_board_industry_name_em()`: 获取行业板块列表
- `get_stock_board_industry_spot_em(symbol)`: 获取行业板块实时行情
- `get_stock_board_industry_cons_em(symbol)`: 获取行业板块成份股

#### 3. API 端点 (`backend/app/api/v1/endpoints/eastmoney.py`)
新增 5 个 RESTful API 端点：
- `GET /stock-margin-underlying-info-szse/{date}`: 深交所标的证券信息
- `GET /stock-profit-forecast-em`: 盈利预测
- `GET /stock-board-industry-name-em`: 行业板块列表
- `GET /stock-board-industry-spot-em/{symbol}`: 行业板块实时行情
- `GET /stock-board-industry-cons-em/{symbol}`: 行业板块成份股

### 前端变更

#### 1. TypeScript 接口 (`frontend/src/services/eastmoney.ts`)
新增 5 个 TypeScript 接口和 API 方法：
- `StockMarginUnderlyingInfoSzse` + `getStockMarginUnderlyingInfoSzse()`
- `StockProfitForecastEm` + `getStockProfitForecastEm()`
- `StockBoardIndustryNameEm` + `getStockBoardIndustryNameEm()`
- `StockBoardIndustrySpotEm` + `getStockBoardIndustrySpotEm()`
- `StockBoardIndustryConsEm` + `getStockBoardIndustryConsEm()`

---

## 功能特性

### 1. 标的证券信息
- **全面信息**: 提供融资标的、融券标的、当日可融资、当日可融券等完整信息
- **价格限制**: 包含融券卖出价格限制和涨跌幅限制
- **按日查询**: 支持指定交易日期查询

### 2. 盈利预测
- **机构评级**: 提供近 6 个月机构投资评级（买入、增持、中性、减持、卖出）
- **收益预测**: 提供 2022-2025 年每股收益预测
- **研报统计**: 显示研报数量和机构评级分布
- **行业筛选**: 支持按行业板块筛选数据

### 3. 行业板块
- **板块列表**: 提供所有行业板块的实时行情和排名
- **领涨股票**: 显示每个板块的领涨股票及其涨跌幅
- **实时数据**: 包含最新价、涨跌幅、成交量、换手率等实时数据
- **成份股查询**: 支持查询板块的所有成份股

### 4. 数据关联
- **板块联动**: 可以通过行业板块列表获取板块代码，再查询实时行情和成份股
- **投资决策**: 盈利预测数据可作为投资决策参考

---

## 使用场景

### 1. 融资融券分析
- 查询深交所标的证券信息，了解哪些股票可以进行融资融券
- 分析标的证券的融资融券状态和价格限制

### 2. 投资价值分析
- 查看机构对股票的评级和盈利预测
- 对比不同年份的每股收益预测趋势
- 按行业查看盈利预测，发现投资机会

### 3. 行业板块监控
- 监控行业板块的实时行情和涨跌幅
- 发现领涨板块和领涨股票
- 分析板块资金流向和活跃度

### 4. 成份股分析
- 获取行业板块的所有成份股
- 对比成份股的表现
- 发现板块内的龙头股票

---

## 数据说明

### 数据来源
- 深圳证券交易所：`https://www.szse.cn/disclosure/margin/object/index.html`
- 东方财富网：`http://data.eastmoney.com/report/profitforecast.jshtml`
- 东方财富行业板块：`https://quote.eastmoney.com/center/boardlist.html#industry_board`
- 数据通过 AKShare 库获取

### 注意事项

1. **日期格式**: 所有日期参数必须为 YYYYMMDD 格式
2. **行业板块**: 盈利预测接口支持传入行业板块名称进行筛选
3. **板块代码**: 成份股查询支持板块名称或板块代码
4. **数据时效**: 行情数据为实时数据，盈利预测数据定期更新

---

## API 调用示例

### 后端 API 调用

```python
import httpx

# 深交所标的证券信息
async def get_szse_underlying_info():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/eastmoney/stock-margin-underlying-info-szse/20210727"
        )
        return response.json()

# 盈利预测
async def get_profit_forecast():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/eastmoney/stock-profit-forecast-em",
            params={"symbol": "船舶制造"}
        )
        return response.json()

# 行业板块列表
async def get_industry_boards():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/eastmoney/stock-board-industry-name-em"
        )
        return response.json()

# 行业板块实时行情
async def get_board_spot():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/eastmoney/stock-board-industry-spot-em/小金属"
        )
        return response.json()

# 行业板块成份股
async def get_board_constituents():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/eastmoney/stock-board-industry-cons-em/小金属"
        )
        return response.json()
```

### 前端调用

```typescript
import { eastMoneyApi } from '@/services/eastmoney';

// 深交所标的证券信息
const underlyingInfo = await eastMoneyApi.getStockMarginUnderlyingInfoSzse('20210727');

// 盈利预测（全部）
const allForecasts = await eastMoneyApi.getStockProfitForecastEm();

// 盈利预测（特定行业）
const industryForecasts = await eastMoneyApi.getStockProfitForecastEm('船舶制造');

// 行业板块列表
const boards = await eastMoneyApi.getStockBoardIndustryNameEm();

// 行业板块实时行情
const boardSpot = await eastMoneyApi.getStockBoardIndustrySpotEm('小金属');

// 行业板块成份股
const boardConstituents = await eastMoneyApi.getStockBoardIndustryConsEm('小金属');
```

---

## 性能优化

### 缓存机制
- 所有接口均实现缓存，TTL 为 60 秒
- 相同参数的查询会直接返回缓存数据
- 减少重复请求，提高响应速度

### 数据筛选
- 盈利预测支持按行业板块筛选，减少数据传输量
- 成份股查询支持板块代码，提高查询效率

---

## 版本统计

- **新增数据模型**: 5 个
- **新增适配器方法**: 5 个
- **新增 API 端点**: 5 个
- **新增前端接口**: 5 个
- **总计新增接口**: 5 个

---

## 下一版本计划

- [ ] 更多行业数据接口
- [ ] 板块资金流向分析
- [ ] 盈利预测历史数据对比
- [ ] 数据导出功能
- [ ] 前端页面展示优化

---

**更新完成时间**: 2026-03-21  
**开发者**: AI Assistant
