# EFinance Adapter API 参考文档

## 概述

[EFinanceAdapter](file://d:\PROJ\Quant\backend\app\adapters\efinance_adapter.py#L53-L1186) 是一个基于 **efinance** 库的金融数据接口适配器，提供免费的 A 股、基金、期货等金融数据。

### 特点

- ✅ **完全免费** - 无需注册，无需 token
- ✅ **数据丰富** - 来源于东方财富网
- ✅ **实时数据** - 支持实时行情、历史 K 线
- ✅ **内置缓存** - 提高性能，减少请求
- ✅ **重试机制** - 网络不稳定时自动重试

### 支持的数据类型

- A 股（沪深、创业板、科创板）
- 基金（ETF、LOF）
- 期货
- 可转债
- 港股、美股、中概股
- 指数

---

## 已实现的接口

### 1. 股票基本信息

#### `get_stock_list()` - 获取股票列表
```python
async def get_stock_list() -> List[StockBasicInfo]
```
**返回**: 所有 A 股股票的基本信息列表

**字段**:
- `code`: 股票代码
- `name`: 股票名称
- `market`: 市场 (SH/SZ)
- `total_shares`: 总股本
- `float_shares`: 流通股本

---

#### `get_stock_info(code)` - 获取单只股票信息
```python
async def get_stock_info(code: str) -> Optional[StockBasicInfo]
```
**参数**:
- `code`: 股票代码（6 位数字）

**返回**: 单只股票的详细信息

**字段**:
- `code`: 股票代码
- `name`: 股票名称
- `market`: 市场 (SH/SZ)
- `industry`: 所属行业
- `total_shares`: 总股本
- `float_shares`: 流通股本

**说明**:
- 使用 `efinance.stock.get_base_info` 接口
- 自动识别市场（6 开头为沪市，0/3 开头为深市）
- 自动补零（传入 `1` 会自动转换为 `000001`）
- 缓存时间：10 分钟

---

#### `get_stock_info_batch(codes)` - 批量获取股票信息（新增）
```python
async def get_stock_info_batch(codes: List[str]) -> List[StockBasicInfo]
```
**参数**:
- `codes`: 股票代码列表，例如 `['600519', '000001', '300750']`

**返回**: 多只股票的基本信息列表

**字段**:
- `code`: 股票代码
- `name`: 股票名称
- `market`: 市场 (SH/SZ)
- `industry`: 所属行业
- `total_shares`: 总股本
- `float_shares`: 流通股本

**说明**:
- 使用 `efinance.stock.get_base_info` 批量接口
- 比循环调用 `get_stock_info` 效率更高
- 自动过滤无效代码
- 缓存时间：10 分钟

**示例**:
```python
# 批量获取多只股票信息
codes = ['600519', '000001', '300750']
stocks = await adapter.get_stock_info_batch(codes)

for stock in stocks:
    print(f"{stock.code} - {stock.name} | 行业：{stock.industry}")
    print(f"  总股本：{stock.total_shares/1e8:.2f}亿股")
    print(f"  流通股本：{stock.float_shares/1e8:.2f}亿股")
    print("---")
```

**对比**:
```python
# ❌ 低效方式：循环调用
stocks = []
for code in codes:
    stock = await adapter.get_stock_info(code)
    if stock:
        stocks.append(stock)

# ✅ 高效方式：批量调用
stocks = await adapter.get_stock_info_batch(codes)
```

---

### 2. K 线数据

#### `get_kline(code, start_date, end_date, adjust)` - 获取日 K 线
```python
async def get_kline(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "qfq"
) -> List[KLineData]
```
**参数**:
- `code`: 股票代码
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
- `adjust`: 复权类型 (qfq-前复权，hfq-后复权，空 - 不复权)

**返回**: 日 K 线数据列表

**字段**:
- `date`: 日期
- `open`: 开盘价
- `high`: 最高价
- `low`: 最低价
- `close`: 收盘价
- `volume`: 成交量
- `amount`: 成交额
- `turnover_rate`: 换手率
- `pre_close`: 昨收价

---

#### `get_deal_detail(code, max_count)` - 获取成交明细（新增）
```python
async def get_deal_detail(
    code: str,
    max_count: int = 1000000
) -> List[Dict[str, Any]]
```
**参数**:
- `code`: 股票代码
- `max_count`: 最近的最大数据条数，默认 1000000

**返回**: 成交明细列表

**字段**:
- `code`: 股票代码
- `name`: 股票名称
- `prev_close`: 昨收价
- `time`: 时间（HH:MM:SS）
- `price`: 成交价
- `volume`: 成交量（手）
- `order_type`: 单数

**说明**:
- 获取最新交易日的逐笔成交明细
- 数据来源于东方财富网
- 缓存时间：5 分钟

**示例**:
```python
# 获取贵州茅台成交明细
deals = await adapter.get_deal_detail("600519")

for deal in deals[:10]:  # 显示前 10 条
    print(f"{deal['time']} - 成交价：{deal['price']:.2f}元，成交量：{deal['volume']}手，单数：{deal['order_type']}")
```

**输出示例**:
```
09:15:03 - 成交价：1794.92 元，成交量：5 手，单数：0
09:15:06 - 成交价：1809.00 元，成交量：21 手，单数：0
09:15:09 - 成交价：1809.00 元，成交量：24 手，单数：0
...
15:00:00 - 成交价：1835.00 元，成交量：893 手，单数：406
```

---

#### `get_weekly_kline()` - 获取周 K 线
```python
async def get_weekly_kline(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "qfq"
) -> List[KLineData]
```
**特点**: 带重试机制（最多 3 次），缓存 30 分钟

---

#### `get_monthly_kline()` - 获取月 K 线
```python
async def get_monthly_kline(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "qfq"
) -> List[KLineData]
```
**特点**: 带重试机制（最多 3 次），缓存 30 分钟

---

### 3. 实时行情

#### `get_realtime_quote(code)` - 获取单只股票实时行情（精准查询）
```python
async def get_realtime_quote(code: str) -> Dict[str, Any]
```
**参数**:
- `code`: 股票代码

**返回**: 实时行情字典

**字段**:
- `code`: 股票代码
- `name`: 股票名称
- `price`: 最新价
- `change`: 涨跌额
- `change_pct`: 涨跌幅
- `high`: 最高价
- `low`: 最低价
- `open`: 今开
- `prev_close`: 昨收
- `volume`: 成交量
- `amount`: 成交额
- `turnover_rate`: 换手率
- `quote_time`: 行情时间

**说明**:
- 使用 `efinance.stock.get_quote_snapshot` 接口
- 适合精准查询**单只股票**的最新行情
- 缓存时间：60 秒

**示例**:
```python
# 查询单只股票
quote = await adapter.get_realtime_quote("601012")
print(f"隆基绿能：{quote['price']}元，涨跌幅：{quote['change_pct']}%")
```

---

#### `get_latest_quote(codes)` - 获取股票最新行情（批量精准查询）
```python
async def get_latest_quote(
    codes: Union[str, List[str]]
) -> Union[Dict[str, Any], List[Dict[str, Any]]]
```
**参数**:
- `codes`: 股票代码或股票代码列表
  - 单只股票：`'601012'`
  - 多只股票：`['601012', '300274', '002594']`

**返回**:
- 单只股票：返回单个字典
- 多只股票：返回字典列表

**字段**:
- `code`: 股票代码
- `name`: 股票名称
- `price`: 最新价
- `change`: 涨跌额
- `change_pct`: 涨跌幅
- `high`: 最高价
- `low`: 最低价
- `open`: 今开
- `prev_close`: 昨收
- `volume`: 成交量
- `amount`: 成交额
- `turnover_rate`: 换手率
- `pe_ratio`: 市盈率 (动)
- `pb_ratio`: 市净率
- `total_market_cap`: 总市值
- `float_market_cap`: 流通市值

**说明**:
- 使用 `efinance.stock.get_latest_quote` 接口（或 `get_quote` 别名）
- 适合精准查询**指定股票**的最新行情
- 支持单只或多只股票批量查询
- 缓存时间：60 秒

**示例**:
```python
# 单只股票
quote = await adapter.get_latest_quote("601012")

# 多只股票批量查询
quotes = await adapter.get_latest_quote(["601012", "300274", "002594"])

for quote in quotes:
    print(f"{quote['name']}: {quote['price']}元，涨跌幅：{quote['change_pct']}%")
```

---

#### `get_market_realtime_quotes(market_types, fs, fields, retry, timeout)` - 获取市场/板块实时行情（批量筛选）
```python
async def get_market_realtime_quotes(
    market_types: Optional[List[str]] = None,
    fs: Optional[str] = None,
    fields: Optional[List[str]] = None,
    retry: int = 3,
    timeout: int = 15
) -> List[MarketQuote]
```
**参数**:
- `market_types`: 市场类型列表（可选）
  - `'沪深 A 股'`（默认，不传参数）
  - `'沪 A'`, `'深 A'`, `'北 A'`
  - `'创业板'`, `'科创板'`
  - `'ETF'`, `'LOF'`
  - `'行业板块'`, `'概念板块'`
  - `'港股'`, `'美股'`, `'中概股'`
  - `'可转债'`, `'期货'`
  - `'沪深系列指数'`, `'上证系列指数'`, `'深证系列指数'`

- `fs`: **筛选条件（优先级高于 market_types）**，支持：
  - **板块代码**：`'884723'`（光伏概念）、`'000300'`（沪深 300）、`'399006'`（创业板）
  - **市场类型**：`'mkt:1'`（沪市）、`'mkt:0'`（深市）、`'mkt:2'`（北交所）
  - **自定义条件**：
    - `'pctChg:>0'` - 上涨股票
    - `'pctChg:<0'` - 下跌股票
    - `'totMv:>50000000000'` - 总市值>500 亿
    - `'vol:>100000'` - 成交量>10 万手
    - `'price:>10'` - 股价>10 元
  - **多条件组合**：`'884723,pctChg:>0,totMv:>20000000000'`（光伏板块 + 上涨 + 市值>200 亿）

- `fields`: 自定义返回字段列表（可选），默认返回全部字段
- `retry`: 重试次数，默认 3 次
- `timeout`: 超时时间（秒），默认 15 秒

**返回**: 市场实时行情列表

**字段**:
- `code`: 股票代码
- `name`: 股票名称
- `change_pct`: 涨跌幅
- `price`: 最新价
- `high`: 最高价
- `low`: 最低价
- `open`: 今开
- `change`: 涨跌额
- `turnover_rate`: 换手率
- `volume_ratio`: 量比
- `pe_ratio`: 市盈率
- `volume`: 成交量
- `amount`: 成交额
- `prev_close`: 昨收
- `total_market_cap`: 总市值
- `float_market_cap`: 流通市值
- `market_type`: 市场类型

**说明**:
- 使用 `efinance.stock.get_realtime_quotes` 接口
- 支持多维度筛选，适合**批量获取特定范围**股票数据
- **可用于获取 A 股股票列表和数量**
- 缓存时间：60 秒

**示例**:

```python
# 1. 获取光伏板块（884723）所有股票
quotes = await adapter.get_market_realtime_quotes(fs="884723")
print(f"光伏板块股票数量：{len(quotes)}")

# 2. 获取北交所（mkt:2）所有股票
quotes = await adapter.get_market_realtime_quotes(fs="mkt:2")
print(f"北交所股票数量：{len(quotes)}")

# 3. 获取沪深 300（000300）成分股
quotes = await adapter.get_market_realtime_quotes(fs="000300")
print(f"沪深 300 成分股数量：{len(quotes)}")

# 4. 获取光伏板块中上涨的股票
quotes = await adapter.get_market_realtime_quotes(fs="884723,pctChg:>0")

# 5. 获取光伏板块中上涨且市值>200 亿的股票
quotes = await adapter.get_market_realtime_quotes(fs="884723,pctChg:>0,totMv:>20000000000")

# 6. 获取创业板（399006）所有股票
quotes = await adapter.get_market_realtime_quotes(fs="399006")
print(f"创业板股票数量：{len(quotes)}")

# 7. 获取科创板（000688）所有股票
quotes = await adapter.get_market_realtime_quotes(fs="000688")
print(f"科创板股票数量：{len(quotes)}")

# 8. 获取全部沪深 A 股股票列表
quotes = await adapter.get_market_realtime_quotes()
print(f"沪深 A 股总数量：{len(quotes)}")

# 9. 按市场类型获取（传统方式）
quotes = await adapter.get_market_realtime_quotes(['沪 A', '深 A'])

# 10. 遍历股票列表
for quote in quotes[:10]:  # 显示前 10 只
    print(f"{quote.code} - {quote.name}: {quote.price:.2f}元，涨跌幅：{quote.change_pct:.2f}%")
```

**常用板块代码**:

| 板块名称 | 板块代码 | 说明 |
|---------|---------|------|
| 光伏概念 | 884723 | 光伏产业相关股票 |
| 储能 | 884937 | 储能产业相关股票 |
| 新能源汽车 | 884931 | 新能源汽车产业链 |
| 芯片概念 | 884943 | 半导体芯片相关 |
| 沪深 300 | 000300 | A 股核心 300 只股票 |
| 上证 50 | 000016 | 沪市超大型股票 |
| 创业板 | 399006 | 深交所创业板 |
| 科创板 | 000688 | 上交所科创板 |
| 北证 50 | 899050 | 北交所 50 只股票 |

**市场类型代码**:

| 代码 | 说明 |
|-----|------|
| mkt:1 | 沪市 A 股 |
| mkt:0 | 深市 A 股 |
| mkt:2 | 北交所 |

**输出示例**:
```
光伏板块股票数量：158
前 10 只股票：
688599 - 天合光能：35.50 元，涨跌幅：2.50%
601012 - 隆基绿能：28.80 元，涨跌幅：1.20%
300274 - 阳光电源：95.60 元，涨跌幅：-0.50%
...
```

---

### 📊 三个实时行情接口对比

| 维度 | get_realtime_quote | get_latest_quote | get_market_realtime_quotes |
|-----|-------------------|------------------|---------------------------|
| **核心定位** | 单只股票精准查询 | 多只股票精准查询 | 批量筛选获取 |
| **筛选方式** | 无 | 无 | 支持 fs 参数（板块/市场/自定义） |
| **输入参数** | 单只股票代码 | 股票代码或列表 | 市场类型、筛选条件、自定义字段 |
| **返回范围** | 单只股票 | 指定股票 | 符合条件的所有股票 |
| **字段灵活性** | 固定字段 | 固定字段 | 支持 fields 自定义 |
| **性能/效率** | 适合单只查询 | 适合多只精准查询 | 适合批量获取 |
| **典型场景** | 查单只股票最新价 | 跟踪多只核心股票 | 板块分析、市场筛选 |

**选型建议**:
- **查单只股票** → `get_realtime_quote` 或 `get_latest_quote("601012")`
- **查多只指定股票** → `get_latest_quote(["601012", "300274"])`
- **查整个板块** → `get_market_realtime_quotes(fs="884723")`
- **查市场全部股票** → `get_market_realtime_quotes()`
- **带条件筛选** → `get_market_realtime_quotes(fs="884723,pctChg:>0")`

---

### 4. 板块数据

#### `get_sector_list(sector_type)` - 获取板块列表
```python
async def get_sector_list(sector_type: str = "industry") -> List[SectorInfo]
```
**参数**:
- `sector_type`: 板块类型
  - `'industry'`: 行业板块
  - `'concept'`: 概念板块

**返回**: 板块列表

---

#### `get_sector_components(sector_code)` - 获取板块成分股
```python
async def get_sector_components(sector_code: str) -> List[str]
```
**状态**: ⚠️ 暂不支持（返回空列表）

---

#### `get_belong_board(code)` - 获取股票所属板块
```python
async def get_belong_board(code: str) -> List[BoardInfo]
```
**参数**:
- `code`: 股票代码

**返回**: 所属板块列表

**字段**:
- `code`: 板块代码
- `name`: 板块名称
- `board_type`: 板块类型（行业/概念/地域/指数）
- `close_price`: 板块价格
- `change_pct`: 板块涨跌幅

**板块类型说明**:
- **行业板块** (BK04xx): 酿酒行业、水泥建材、医药生物等
- **概念板块** (BK05xx/BK09xx/BK10xx): 5G 概念、芯片概念、新能源等
- **地域板块** (BK01xx): 贵州板块、广东板块、北京板块等
- **指数板块** (BK06xx/BK07xx/BK08xx): 上证 50、沪深 300、创业板指等

**示例**:
```python
# 获取贵州茅台所属板块
boards = await adapter.get_belong_board("600519")

for board in boards:
    print(f"{board.name} ({board.code})")
    print(f"  类型：{board.board_type}")
    print(f"  涨跌幅：{board.change_pct:.2f}%")
    print("---")
```

**输出示例**:
```
酿酒行业 (BK0477)
  类型：行业板块
  涨跌幅：0.56%
---
贵州板块 (BK0173)
  类型：地域板块
  涨跌幅：-1.27%
---
上证 50_ (BK0611)
  类型：指数板块
  涨跌幅：0.60%
---
```

---

### 5. 资金流向

#### `get_today_bill(trade_date)` - 获取当日资金流向
```python
async def get_today_bill(trade_date: Optional[str] = None) -> List[CapitalFlowItem]
```
**参数**:
- `trade_date`: 交易日期 (YYYY-MM-DD)，默认今日

**返回**: 所有股票当日资金流向

**字段**:
- `code`: 股票代码
- `name`: 股票名称
- `close_price`: 最新价
- `change_pct`: 涨跌幅
- `main_net_amount`: 主力净流入
- `main_net_amount_rate`: 主力净流入率
- `buy_elg_amount`: 超大单净流入
- `buy_lg_amount`: 大单净流入
- `buy_md_amount`: 中单净流入
- `buy_sm_amount`: 小单净流入

**缓存**: 60 秒

---

#### `get_history_bill(code)` - 获取历史资金流向（新增）
```python
async def get_history_bill(code: str) -> List[Dict[str, Any]]
```
**参数**:
- `code`: 股票代码

**返回**: 历史资金流向列表（按日期倒序排列）

**字段**:
- `code`: 股票代码
- `name`: 股票名称
- `date`: 日期
- `main_net_amount`: 主力净流入（元）
- `sm_net_amount`: 小单净流入（元）
- `md_net_amount`: 中单净流入（元）
- `lg_net_amount`: 大单净流入（元）
- `elg_net_amount`: 超大单净流入（元）
- `main_net_ratio`: 主力净流入占比（%）
- `sm_net_ratio`: 小单流入净占比（%）
- `md_net_ratio`: 中单流入净占比（%）
- `lg_net_ratio`: 大单流入净占比（%）
- `elg_net_ratio`: 超大单流入净占比（%）
- `close_price`: 收盘价（元）
- `change_pct`: 涨跌幅（%）

**说明**:
- 获取股票历史的每日资金流向数据
- 数据来源于东方财富网
- 按日期倒序排列（最新的在前）
- 缓存时间：10 分钟

**示例**:
```python
# 获取贵州茅台历史资金流向
history = await adapter.get_history_bill("600519")

for bill in history[:10]:  # 显示最近 10 天
    print(f"{bill['date']}: 主力净流入 {bill['main_net_amount']/10000:.2f}万元")
    print(f"  超大单：{bill['elg_net_amount']/10000:.2f}万元，大单：{bill['lg_net_amount']/10000:.2f}万元")
    print(f"  中单：{bill['md_net_amount']/10000:.2f}万元，小单：{bill['sm_net_amount']/10000:.2f}万元")
    print(f"  收盘价：{bill['close_price']:.2f}元，涨跌幅：{bill['change_pct']:.2f}%")
    print("---")
```

**输出示例**:
```
20240318: 主力净流入 15000.00 万元
  超大单：8000.00 万元，大单：7000.00 万元
  中单：-5000.00 万元，小单：-10000.00 万元
  收盘价：1835.00 元，涨跌幅：2.50%
---
20240315: 主力净流入 -8000.00 万元
  超大单：-5000.00 万元，大单：-3000.00 万元
  中单：3000.00 万元，小单：5000.00 万元
  收盘价：1790.00 元，涨跌幅：-1.20%
---
```

---

#### `get_history_bill(code, start_date, end_date)` - 获取历史资金流向
```python
async def get_history_bill(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[CapitalFlowItem]
```
**参数**:
- `code`: 股票代码
- `start_date`: 开始日期
- `end_date`: 结束日期

**返回**: 历史资金流向列表

---

### 6. 龙虎榜

#### `get_daily_billboard(start_date, end_date)` - 获取龙虎榜单
```python
async def get_daily_billboard(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[BillboardEntry]
```
**参数**:
- `start_date`: 开始日期，格式 `YYYY-MM-DD`
  - `None`: 最新一个榜单公开日（默认）
  - `'2024-03-18'`: 指定日期
- `end_date`: 结束日期，格式 `YYYY-MM-DD`
  - `None`: 与 start_date 相同（默认）
  - `'2024-03-22'`: 指定结束日期

**返回**: 龙虎榜数据列表

**字段**:
- `code`: 股票代码
- `name`: 股票名称
- `close_price`: 收盘价
- `change_pct`: 涨跌幅
- `turnover_amount`: 成交额
- `net_amount`: 龙虎榜净买额
- `buy_amount`: 龙虎榜买入额
- `sell_amount`: 龙虎榜卖出额
- `reason`: 上榜原因
- `trade_date`: 上榜日期

**上榜原因类型**:
- 日涨幅偏离值达到 7% 的前 5 只证券
- 日跌幅偏离值达到 7% 的前 5 只证券
- 日振幅值达到 15% 的前 5 只证券
- 日换手率达到 20% 的前 5 只证券
- 连续三个交易日内，涨幅偏离值累计达到 20% 的证券
- 有价格涨跌幅限制的日换手率达到 30% 的前五只证券
- 等等...

**示例**:
```python
# 获取最新龙虎榜
billboard = await adapter.get_daily_billboard()

# 获取指定日期的龙虎榜
billboard = await adapter.get_daily_billboard(start_date="2024-03-18")

# 获取日期区间的龙虎榜
billboard = await adapter.get_daily_billboard(
    start_date="2024-03-18",
    end_date="2024-03-22"
)

# 遍历龙虎榜数据
for entry in billboard:
    print(f"{entry.name} ({entry.code})")
    print(f"  收盘价：{entry.close_price:.2f}元，涨跌幅：{entry.change_pct:.2f}%")
    print(f"  龙虎榜净买额：{entry.net_amount/10000:.2f}万元")
    print(f"  上榜原因：{entry.reason}")
    print(f"  上榜日期：{entry.trade_date}")
    print("---")
```

**输出示例**:
```
贵州茅台 (600519)
  收盘价：1700.00 元，涨跌幅：2.50%
  龙虎榜净买额：15000.00 万元
  上榜原因：日涨幅偏离值达到 7% 的前 5 只证券
  上榜日期：20240318
---
宁德时代 (300750)
  收盘价：200.50 元，涨跌幅：-1.20%
  龙虎榜净买额：-8000.00 万元
  上榜原因：日振幅值达到 15% 的前 5 只证券
  上榜日期：20240318
---
```

**说明**:
- 数据来源于东方财富网
- 龙虎榜数据通常在交易日收盘后公布（约 16:30-17:30）
- 非交易日或无龙虎榜时返回空列表
- 缓存时间：5 分钟

---

### 7. 指数成分股（优化）

#### `get_members(index_code)` - 获取指数成分股
```python
async def get_members(index_code: str) -> List[IndexComponent]
```
**参数**:
- `index_code`: 指数代码或指数名称
  - **指数代码**：`'000300'`（沪深 300）、`'000016'`（上证 50）、`'399006'`（创业板指）
  - **指数名称**：`'沪深 300'`、`'中证白酒'`、`'光伏产业'`

**返回**: 指数成分股列表

**字段**:
- `index_code`: 指数代码
- `index_name`: 指数名称
- `code`: 股票代码
- `name`: 股票名称
- `weight`: 股票权重（%）

**说明**:
- 使用 `efinance.stock.get_members` 接口
- 支持通过指数代码或指数名称查询
- 部分科创板股票权重可能为 NaN
- 缓存时间：30 分钟

**示例**:
```python
# 1. 获取沪深 300 成分股
components = await adapter.get_members("000300")
print(f"沪深 300 成分股数量：{len(components)}")

# 2. 获取中证白酒成分股
components = await adapter.get_members("中证白酒")
print(f"中证白酒成分股数量：{len(components)}")

# 3. 获取上证 50 成分股
components = await adapter.get_members("000016")

# 4. 获取创业板指成分股
components = await adapter.get_members("399006")

# 5. 获取光伏产业成分股
components = await adapter.get_members("光伏产业")

# 6. 遍历成分股（按权重排序）
components.sort(key=lambda x: x.weight or 0, reverse=True)
for comp in components[:10]:  # 显示前 10 大权重股
    print(f"{comp.name} ({comp.code}): 权重 {comp.weight:.2f}%")
```

**输出示例**:
```
沪深 300 成分股数量：300
前 10 大权重股：
贵州茅台 (600519): 权重 4.77%
工商银行 (601398): 权重 3.46%
建设银行 (601939): 权重 3.12%
招商银行 (600036): 权重 2.65%
中国石油 (601857): 权重 2.37%
...

中证白酒成分股数量：16
前 5 大权重股：
贵州茅台 (600519): 权重 49.25%
五粮液 (000858): 权重 18.88%
山西汾酒 (600809): 权重 8.45%
泸州老窖 (000568): 权重 7.03%
洋河股份 (002304): 权重 5.72%
```

**常用指数代码**:

| 指数名称 | 指数代码 | 成分股数量 |
|---------|---------|-----------|
| 沪深 300 | 000300 | 300 |
| 上证 50 | 000016 | 50 |
| 中证 500 | 000905 | 500 |
| 创业板指 | 399006 | 100 |
| 科创 50 | 000688 | 50 |
| 中证白酒 | 399997 | 16 |
| 光伏产业 | 931151 | 50+ |
| 新能源汽车 | 399976 | 50+ |

---

### 8. 股东人数（筹码）

#### `get_chip_data(code, start_date, end_date)` - 获取筹码数据
```python
async def get_chip_data(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[ChipData]
```
**参数**:
- `code`: 股票代码
- `start_date`: 开始日期
- `end_date`: 结束日期

**返回**: 股东人数数据列表

**字段**:
- `code`: 股票代码
- `date`: 公告日期
- `shareholder_count`: 股东人数

---

### 9. 前十大股东

#### `get_top10_stock_holder_info(code)` - 获取前十大股东信息
```python
async def get_top10_stock_holder_info(code: str) -> List[ShareholderInfo]
```
**参数**:
- `code`: 股票代码

**返回**: 前十大股东信息列表

**字段**:
- `code`: 股票代码
- `shareholder_name`: 股东名称
- `shareholder_type`: 股东类型
- `hold_amount`: 持股数量
- `hold_ratio`: 持股比例
- `change_amount`: 持股变化
- `change_ratio`: 持股变化比例
- `report_date`: 报告期

**特点**: 支持'亿'、'万'等单位自动转换

---

### 10. 财务业绩（新增）

#### `get_financial_performance(code, report_date, report_type)` - 获取财务业绩数据
```python
async def get_financial_performance(
    code: str,
    report_date: Optional[str] = None,
    report_type: str = "quarterly"
) -> List[FinancialPerformance]
```
**参数**:
- `code`: 股票代码
- `report_date`: 报告日期，格式 `'YYYY-MM-DD'`
  - `None`: 获取最新季报（默认）
  - `'2024-03-31'`: 获取 2024 年一季报
  - `'2023-12-31'`: 获取 2023 年年报
- `report_type`: 报告类型（默认 `'quarterly'`）

**返回**: 财务业绩数据列表（按公告日期倒序排列）

**字段**:
- `code`: 股票代码
- `name`: 股票简称
- `report_date`: 公告日期
- `revenue`: 营业收入（元）
- `revenue_growth`: 营业收入同比增长（%）
- `revenue_qoq`: 营业收入季度环比（%）
- `net_profit`: 净利润（元）
- `net_profit_growth`: 净利润同比增长（%）
- `net_profit_qoq`: 净利润季度环比（%）
- `eps`: 每股收益（元/股）
- `bvps`: 每股净资产（元/股）
- `roe`: 净资产收益率（%）
- `gross_margin`: 销售毛利率（%）
- `cfps`: 每股经营现金流量（元/股）

**说明**:
- 数据来源于东方财富网
- 支持获取最新季报或指定报告期的数据
- 自动按公告日期排序（最新的在前）
- 缓存时间：10 分钟

**示例**:
```python
# 获取贵州茅台最新季报
performances = await adapter.get_financial_performance("600519")

# 获取贵州茅台 2023 年年报
performances_2023 = await adapter.get_financial_performance(
    "600519",
    report_date="2023-12-31"
)

# 获取贵州茅台 2024 年一季报
performances_2024q1 = await adapter.get_financial_performance(
    "600519",
    report_date="2024-03-31"
)

for perf in performances:
    print(f"公告日期：{perf.report_date}")
    print(f"营业收入：{perf.revenue/100000000:.2f}亿，同比增长：{perf.revenue_growth:.2f}%")
    print(f"净利润：{perf.net_profit/100000000:.2f}亿，同比增长：{perf.net_profit_growth:.2f}%")
    print(f"ROE: {perf.roe:.2f}%，毛利率：{perf.gross_margin:.2f}%")
    print("---")
```

#### `get_all_report_dates()` - 获取所有可用报告期
```python
async def get_all_report_dates() -> List[Dict[str, str]]
```
**返回**: 报告期列表，每个包含 `date` 和 `name`

**示例**:
```python
dates = await adapter.get_all_report_dates()
for item in dates:
    print(f"{item['date']}: {item['name']}")
# 输出：
# 2024-03-31: 2024 年 一季报
# 2023-12-31: 2023 年 年报
# 2023-09-30: 2023 年 三季报
# ...
```

#### `get_historical_financial_performance(code, limit)` - 获取历史多个季度
```python
async def get_historical_financial_performance(
    code: str,
    limit: int = 10
) -> List[FinancialPerformance]
```
**参数**:
- `code`: 股票代码
- `limit`: 获取最近几个季度（默认 10 个）

**返回**: 历史财务业绩数据列表

**示例**:
```python
# 获取贵州茅台最近 10 个季度的财务数据
history = await adapter.get_historical_financial_performance("600519", limit=10)

for perf in history:
    print(f"{perf.report_date}: 营收{perf.revenue/1e8:.1f}亿，净利{perf.net_profit/1e8:.1f}亿")
```

---

## 缓存机制

### 缓存策略

| 数据类型 | 缓存时间 | 说明 |
|---------|---------|------|
| 实时行情 | 60 秒 | 快速变化的数据 |
| K 线数据 | 5 分钟 | 历史数据相对稳定 |
| 股票列表 | 30 分钟 | 基本不变 |
| 股票信息 | 10 分钟 | 变化较少 |
| 板块数据 | 5 分钟 | 中等频率 |
| 资金流向 | 60 秒 | 每日更新 |
| 周/月 K 线 | 30 分钟 | 非常稳定 |

### 缓存优势

- ✅ 减少 API 请求次数
- ✅ 提高响应速度
- ✅ 降低网络错误概率
- ✅ 支持离线访问（缓存有效期内）

---

## 重试机制

### 自动重试

以下接口支持自动重试（最多 3 次）：

1. `get_weekly_kline()` - 周 K 线
2. `get_monthly_kline()` - 月 K 线
3. `get_market_realtime_quotes()` - 市场实时行情

### 重试策略

- **延迟递增**: 每次重试间隔递增
  - 第 1 次重试：0.5 秒
  - 第 2 次重试：1.0 秒
  - 第 3 次重试：1.5 秒

- **超时控制**: 15 秒超时自动重试

- **降级策略**: 市场数据失败时使用默认市场类型

---

## 使用示例

### 1. 初始化适配器

```python
from app.adapters import EFinanceAdapter

adapter = EFinanceAdapter()
success = await adapter.initialize()
```

### 2. 获取股票列表

```python
stocks = await adapter.get_stock_list()
for stock in stocks:
    print(f"{stock.code} - {stock.name}")
```

### 3. 获取日 K 线数据

```python
klines = await adapter.get_kline(
    code="000001",
    start_date="2024-01-01",
    end_date="2024-12-31",
    adjust="qfq"
)
```

### 4. 获取实时行情

```python
quote = await adapter.get_realtime_quote("000001")
print(f"最新价：{quote['price']}, 涨跌幅：{quote['change_pct']}%")
```

### 5. 获取市场实时行情

```python
# 获取沪深 A 股行情
quotes = await adapter.get_market_realtime_quotes()

# 获取创业板行情
quotes = await adapter.get_market_realtime_quotes(['创业板'])

# 获取多个市场类型
quotes = await adapter.get_market_realtime_quotes(['沪 A', '深 A'])
```

### 6. 获取龙虎榜数据

```python
billboard = await adapter.get_daily_billboard("2024-03-18")
for entry in billboard:
    print(f"{entry.name}: {entry.reason}")
```

### 7. 获取资金流向

```python
# 今日资金流向
flows = await adapter.get_today_bill()

# 历史资金流向
history = await adapter.get_history_bill(
    code="000001",
    start_date="2024-01-01",
    end_date="2024-03-18"
)
```

---

## 与其他数据源对比

| 特性 | EFinance | Tushare | AkShare | Baostock |
|-----|----------|---------|---------|----------|
| 费用 | 免费 | 积分制 | 免费 | 免费 |
| 注册 | 不需要 | 需要 | 不需要 | 需要 |
| Token | 不需要 | 需要 | 不需要 | 需要 |
| 实时行情 | ✅ | ✅ | ✅ | ❌ |
| 历史 K 线 | ✅ | ✅ | ✅ | ✅ |
| 周/月 K 线 | ✅ | ✅ | ✅ | ✅ |
| 资金流向 | ✅ | ✅ | ✅ | ❌ |
| 龙虎榜 | ✅ | ✅ | ✅ | ❌ |
| 股东人数 | ✅ | ✅ | ✅ | ❌ |
| 缓存机制 | ✅ | ✅ | ✅ | ❌ |
| 重试机制 | ✅ | ✅ | ❌ | ❌ |

---

## 注意事项

### 1. 数据准确性

- 数据来源于东方财富网，可能存在延迟
- 实时行情在交易时段更新，非交易时段为最后收盘价

### 2. 使用限制

- 虽然是免费数据，但请合理使用，避免频繁请求
- 建议充分利用缓存机制

### 3. 日期格式

- 输入：`YYYY-MM-DD` (如：`2024-03-18`)
- 输出：`YYYYMMDD` (如：`20240318`)

### 4. 股票代码

- 自动补零：传入 `1` 会自动转换为 `000001`
- 自动识别市场：6 开头为沪市，0/3 开头为深市

### 5. 复权处理

- `qfq`: 前复权（推荐，默认）
- `hfq`: 后复权
- `""`: 不复权

---

## 故障排除

### 常见问题

#### 1. 获取数据为空

```python
# 检查 efinance 是否安装
from app.adapters.efinance_adapter import EF_AVAILABLE
print(f"EFinance available: {EF_AVAILABLE}")

# 检查网络
import efinance as ef
df = ef.stock.get_realtime_quotes()
print(df.head())
```

#### 2. 日期格式错误

确保日期格式正确：
```python
# ✅ 正确
start_date = "2024-01-01"

# ❌ 错误
start_date = "20240101"
start_date = "2024/01/01"
```

#### 3. 缓存导致数据不更新

清除缓存：
```python
adapter._cache.clear()
adapter._cache_timestamp.clear()
```

---

## 参考资料

- **GitHub**: https://github.com/Micro-sun/efinance
- **文档**: https://efinance.readthedocs.io/
- **PyPI**: https://pypi.org/project/efinance/

---

## 更新日志

### 2026-03-18
- ✅ **新增财报接口** - 添加 `get_financial_performance()` 方法
- ✅ 支持季度财务业绩数据（营业收入、净利润、ROE 等）
- ✅ 添加 `FinancialPerformance` 数据类
- ✅ 所有适配器实现财报接口抽象方法

### 2024-03-18
- ✅ 添加周 K 线和月 K 线支持
- ✅ 实现重试机制
- ✅ 优化缓存策略
- ✅ 添加超时控制
- ✅ 实现降级策略

---

**最后更新**: 2024-03-18
