# 东方财富网数据接口更新日志 v1.16

## 版本信息
- **版本号**: v1.16
- **发布日期**: 2026-03-21
- **功能主题**: 沪深交易所融资融券数据

## 新增功能

### 1. 上海证券交易所 - 融资融券汇总

#### 接口信息
- **接口**: `stock_margin_sse`
- **端点**: `GET /api/v1/eastmoney/stock-margin-sse`
- **参数**:
  - `start_date`: 开始日期，格式 YYYYMMDD
  - `end_date`: 结束日期，格式 YYYYMMDD
- **描述**: 获取上海证券交易所融资融券汇总数据，支持查询指定时间段内的所有历史数据

#### 数据字段
| 字段名称 | 类型 | 描述 |
|---------|------|------|
| credit_trade_date | string | 信用交易日期 |
| margin_balance | int | 融资余额（元） |
| margin_buy | int | 融资买入额（元） |
| short_remaining | int | 融券余量 |
| short_remaining_amount | int | 融券余量金额（元） |
| short_sell | int | 融券卖出量 |
| total_margin_short_balance | int | 融资融券余额（元） |

#### 示例
```typescript
// 前端调用
const data = await eastMoneyApi.getStockMarginSse('20010106', '20210208');
```

---

### 2. 上海证券交易所 - 融资融券明细

#### 接口信息
- **接口**: `stock_margin_detail_sse`
- **端点**: `GET /api/v1/eastmoney/stock-margin-detail-sse/{date}`
- **参数**:
  - `date`: 交易日期，格式 YYYYMMDD
- **描述**: 获取上海证券交易所融资融券明细数据，返回指定交易日的所有标的证券数据

#### 数据字段
| 字段名称 | 类型 | 描述 |
|---------|------|------|
| credit_trade_date | string | 信用交易日期 |
| stock_code | string | 标的证券代码 |
| stock_name | string | 标的证券简称 |
| margin_balance | int | 融资余额（元） |
| margin_buy | int | 融资买入额（元） |
| margin_repay | int | 融资偿还额（元） |
| short_remaining | int | 融券余量 |
| short_sell | int | 融券卖出量 |
| short_repay | int | 融券偿还量 |

#### 示例
```typescript
// 前端调用
const data = await eastMoneyApi.getStockMarginDetailSse('20230922');
```

---

### 3. 深圳证券交易所 - 融资融券汇总

#### 接口信息
- **接口**: `stock_margin_szse`
- **端点**: `GET /api/v1/eastmoney/stock-margin-szse/{date}`
- **参数**:
  - `date`: 交易日期，格式 YYYYMMDD
- **描述**: 获取深圳证券交易所融资融券汇总数据

#### 数据字段
| 字段名称 | 类型 | 描述 | 单位 |
|---------|------|------|------|
| margin_buy | float | 融资买入额 | 亿元 |
| margin_balance | float | 融资余额 | 亿元 |
| short_sell | float | 融券卖出量 | 亿股/亿份 |
| short_remaining | float | 融券余量 | 亿股/亿份 |
| short_balance | float | 融券余额 | 亿元 |
| total_margin_short_balance | float | 融资融券余额 | 亿元 |

#### 示例
```typescript
// 前端调用
const data = await eastMoneyApi.getStockMarginSzse('20240411');
```

---

### 4. 深圳证券交易所 - 融资融券明细

#### 接口信息
- **接口**: `stock_margin_detail_szse`
- **端点**: `GET /api/v1/eastmoney/stock-margin-detail-szse/{date}`
- **参数**:
  - `date`: 交易日期，格式 YYYYMMDD
- **描述**: 获取深圳证券交易所融资融券交易明细数据

#### 数据字段
| 字段名称 | 类型 | 描述 |
|---------|------|------|
| stock_code | string | 证券代码 |
| stock_name | string | 证券简称 |
| margin_buy | int | 融资买入额（元） |
| margin_balance | int | 融资余额（元） |
| short_sell | int | 融券卖出量（股/份） |
| short_remaining | int | 融券余量（股/份） |
| short_balance | int | 融券余额（元） |
| total_margin_short_balance | int | 融资融券余额（元） |

#### 示例
```typescript
// 前端调用
const data = await eastMoneyApi.getStockMarginDetailSzse('20230925');
```

---

## 技术实现

### 后端变更

#### 1. 数据模型 (`backend/app/models/unified_models.py`)
新增 4 个 Pydantic 数据模型：
- `StockMarginSse`: 上交所融资融券汇总
- `StockMarginDetailSse`: 上交所融资融券明细
- `StockMarginSzse`: 深交所融资融券汇总
- `StockMarginDetailSzse`: 深交所融资融券明细

#### 2. 适配器 (`backend/app/adapters/eastmoney_adapter.py`)
新增 4 个异步方法：
- `get_stock_margin_sse(start_date, end_date)`: 获取上交所汇总
- `get_stock_margin_detail_sse(date)`: 获取上交所明细
- `get_stock_margin_szse(date)`: 获取深交所汇总
- `get_stock_margin_detail_szse(date)`: 获取深交所明细

#### 3. API 端点 (`backend/app/api/v1/endpoints/eastmoney.py`)
新增 4 个 RESTful API 端点：
- `GET /stock-margin-sse`: 上交所汇总
- `GET /stock-margin-detail-sse/{date}`: 上交所明细
- `GET /stock-margin-szse/{date}`: 深交所汇总
- `GET /stock-margin-detail-szse/{date}`: 深交所明细

### 前端变更

#### 1. TypeScript 接口 (`frontend/src/services/eastmoney.ts`)
新增 4 个 TypeScript 接口和 API 方法：
- `StockMarginSse` + `getStockMarginSse()`
- `StockMarginDetailSse` + `getStockMarginDetailSse()`
- `StockMarginSzse` + `getStockMarginSzse()`
- `StockMarginDetailSzse` + `getStockMarginDetailSzse()`

#### 2. 页面组件 (`frontend/src/pages/MarginTradingPage.tsx`)
- 新增 4 个 Tab 页面：
  - 上交所汇总（Tab 2）
  - 上交所明细（Tab 3）
  - 深交所汇总（Tab 4）
  - 深交所明细（Tab 5）
- 添加对应的状态管理和数据获取方法
- 实现数据展示和统计信息

---

## 功能特性

### 1. 数据查询
- **上交所汇总**: 支持日期范围查询，可获取历史所有数据
- **上交所明细**: 按交易日查询，返回当日所有标的证券明细
- **深交所汇总**: 按交易日查询，返回当日汇总数据
- **深交所明细**: 按交易日查询，返回当日所有证券明细

### 2. 数据展示
- **统计概览**: 每个 Tab 都提供关键指标统计卡片
- **表格展示**: 支持最多显示前 100 条数据
- **数据提示**: 超过 100 条时显示提示信息

### 3. 用户体验
- **日期选择器**: 提供直观的日期选择界面
- **加载状态**: 查询时显示加载动画
- **错误提示**: 查询失败时显示错误信息
- **成功提示**: 查询成功时显示数据条数

---

## 数据说明

### 单位说明
- **上交所数据**: 金额单位为元（元）
- **深交所汇总**: 金额单位为亿元，数量单位为亿股/亿份
- **深交所明细**: 金额单位为元（元），数量单位为股/份

### 数据来源
- 上海证券交易所：`http://www.sse.com.cn/market/othersdata/margin/sum/`
- 深圳证券交易所：`https://www.szse.cn/disclosure/margin/margin/index.html`
- 数据通过 AKShare 库获取

---

## 使用示例

### 后端 API 调用

```python
import httpx

# 上交所汇总（日期范围查询）
async def get_sse_margin_summary():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/eastmoney/stock-margin-sse",
            params={"start_date": "20010106", "end_date": "20210208"}
        )
        return response.json()

# 上交所明细（指定日期）
async def get_sse_margin_detail():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/eastmoney/stock-margin-detail-sse/20230922"
        )
        return response.json()

# 深交所汇总（指定日期）
async def get_szse_margin_summary():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/eastmoney/stock-margin-szse/20240411"
        )
        return response.json()

# 深交所明细（指定日期）
async def get_szse_margin_detail():
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "http://localhost:8000/api/v1/eastmoney/stock-margin-detail-szse/20230925"
        )
        return response.json()
```

### 前端调用

```typescript
import { eastMoneyApi } from '@/services/eastmoney';

// 上交所汇总
const sseSummary = await eastMoneyApi.getStockMarginSse('20010106', '20210208');

// 上交所明细
const sseDetail = await eastMoneyApi.getStockMarginDetailSse('20230922');

// 深交所汇总
const szseSummary = await eastMoneyApi.getStockMarginSzse('20240411');

// 深交所明细
const szseDetail = await eastMoneyApi.getStockMarginDetailSzse('20230925');
```

---

## 性能优化

### 缓存机制
- 所有接口均实现缓存，TTL 为 60 秒
- 相同参数的查询会直接返回缓存数据
- 减少重复请求，提高响应速度

### 数据限制
- 前端表格最多显示前 100 条数据
- 避免大量数据渲染导致页面卡顿
- 完整数据可通过 API 获取

---

## 注意事项

1. **日期格式**: 所有日期参数必须为 YYYYMMDD 格式
2. **单位差异**: 注意上交所和深交所数据的单位差异
3. **数据量**: 上交所汇总接口可能返回大量历史数据
4. **交易日期**: 查询的日期应为交易日，非交易日可能无数据

---

## 版本统计

- **新增数据模型**: 4 个
- **新增适配器方法**: 4 个
- **新增 API 端点**: 4 个
- **新增前端接口**: 4 个
- **新增页面 Tab**: 4 个
- **总计新增接口**: 4 个

---

## 下一版本计划

- [ ] 融资融券担保物数据
- [ ] 融资融券历史统计
- [ ] 融资融券市场分析报告
- [ ] 数据导出功能

---

**更新完成时间**: 2026-03-21
**开发者**: AI Assistant
