# TickFlow API 完整文档

## 📚 目录

- [TickFlow API 完整文档](#tickflow-api-完整文档)
  - [📚 目录](#-目录)
  - [1️⃣ K 线数据 API (klines)](#1-k-线数据-api-klines)
    - [1.1 get - 获取 K 线数据](#11-get---获取 k 线数据)
    - [1.2 batch - 批量获取 K 线](#12-batch---批量获取 k 线)
    - [1.3 ex_factors - 复权因子](#13-ex_factors---复权因子)
    - [1.4 intraday - 分时数据](#14-intraday---分时数据)
    - [1.5 intraday_batch - 批量分时](#15-intraday_batch---批量分时)
  - [2️⃣ 实时行情 API (quotes)](#2-实时行情-api-quotes)
    - [2.1 get - 获取实时行情](#21-get---获取实时行情)
    - [2.2 get_by_symbols - 按代码获取](#22-get_by_symbols---按代码获取)
    - [2.3 get_by_universes - 按标的池获取](#23-get_by_universes---按标的池获取)
  - [3️⃣ 标的信息 API (instruments)](#3-标的信息-api-instruments)
    - [3.1 get - 获取标的信息](#31-get---获取标的信息)
    - [3.2 batch - 批量获取](#32-batch---批量获取)
  - [4️⃣ 其他 API](#4-其他-api)
  - [5️⃣ 使用示例](#5-使用示例)
    - [5.1 免费服务示例](#51-免费服务示例)
    - [5.2 完整服务示例](#52-完整服务示例)
    - [5.3 批量获取示例](#53-批量获取示例)
  - [6️⃣ 数据格式说明](#6-数据格式说明)
    - [6.1 K 线数据字段](#61-k-线数据字段)
    - [6.2 实时行情字段](#62-实时行情字段)
    - [6.3 标的信息字段](#63-标的信息字段)
  - [7️⃣ 错误处理](#7-错误处理)

---

## 1️⃣ K 线数据 API (klines)

### 1.1 get - 获取 K 线数据

**功能**: 获取单只股票/指数的 K 线数据

**方法签名**:
```python
tf.klines.get(
    symbol: str,
    period: str = "1d",
    count: int = 100,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    as_dataframe: bool = True
) -> Union[pd.DataFrame, List[Dict]]
```

**参数说明**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| symbol | str | ✅ | - | 股票代码，如 "600000.SH" |
| period | str | ❌ | "1d" | K 线周期 |
| count | int | ❌ | 100 | 获取数据条数 |
| start_time | str | ❌ | None | 开始时间，格式 YYYY-MM-DD |
| end_time | str | ❌ | None | 结束时间，格式 YYYY-MM-DD |
| as_dataframe | bool | ❌ | True | 是否返回 DataFrame |

**支持的周期 (period)**:
| 周期 | 说明 | 免费服务 | 完整服务 |
|------|------|---------|---------|
| `1d` | 日 K 线 | ✅ | ✅ |
| `1w` | 周 K 线 | ✅ | ✅ |
| `1M` | 月 K 线 | ✅ | ✅ |
| `1Q` | 季 K 线 | ✅ | ✅ |
| `1Y` | 年 K 线 | ✅ | ✅ |
| `1m` | 1 分钟 | ❌ | ✅ |
| `5m` | 5 分钟 | ❌ | ✅ |
| `15m` | 15 分钟 | ❌ | ✅ |
| `30m` | 30 分钟 | ❌ | ✅ |
| `60m` | 60 分钟 | ❌ | ✅ |

**示例**:
```python
from tickflow import TickFlow

# 免费服务
tf = TickFlow.free()

# 获取浦发银行 100 条日 K 线数据
df = tf.klines.get("600000.SH", period="1d", count=100)
print(df.tail())

# 获取周 K 线数据
df_weekly = tf.klines.get("600000.SH", period="1w", count=50)

# 获取指定时间范围的数据
df = tf.klines.get(
    "600000.SH",
    period="1d",
    start_time="2024-01-01",
    end_time="2024-12-31"
)
```

**返回数据格式** (DataFrame):
```
        time        open    high     low   close      volume       amount
0 2024-01-02   10.25   10.38   10.20   10.35   1234567   12789000.00
1 2024-01-03   10.35   10.45   10.28   10.40   1345678   13987000.00
...
```

---

### 1.2 batch - 批量获取 K 线

**功能**: 批量获取多只股票的 K 线数据

**方法签名**:
```python
tf.klines.batch(
    symbols: List[str],
    period: str = "1d",
    count: int = 100,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> Dict[str, pd.DataFrame]
```

**参数说明**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| symbols | List[str] | ✅ | - | 股票代码列表 |
| period | str | ❌ | "1d" | K 线周期 |
| count | int | ❌ | 100 | 获取数据条数 |
| start_time | str | ❌ | None | 开始时间 |
| end_time | str | ❌ | None | 结束时间 |

**示例**:
```python
# 批量获取多只股票的日 K 线
symbols = ["600000.SH", "000001.SZ", "300750.SZ"]
data = tf.klines.batch(symbols, period="1d", count=100)

# data 是一个字典，key 为股票代码，value 为 DataFrame
for symbol, df in data.items():
    print(f"{symbol}: {len(df)} 条数据")
    print(df.tail())
```

---

### 1.3 ex_factors - 复权因子

**功能**: 获取股票的复权因子数据

**方法签名**:
```python
tf.klines.ex_factors(
    symbol: str,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None
) -> pd.DataFrame
```

**参数说明**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| symbol | str | ✅ | - | 股票代码 |
| start_time | str | ❌ | None | 开始时间 |
| end_time | str | ❌ | None | 结束时间 |

**示例**:
```python
# 获取浦发银行的复权因子
df = tf.klines.ex_factors("600000.SH")
print(df)
```

**返回数据**:
```
        time     adj_factor
0 2024-01-02     1.234567
1 2024-01-03     1.234567
...
```

---

### 1.4 intraday - 分时数据

**功能**: 获取单只股票的分时成交数据

**方法签名**:
```python
tf.klines.intraday(
    symbol: str,
    date: Optional[str] = None,
    as_dataframe: bool = True
) -> Union[pd.DataFrame, List[Dict]]
```

**参数说明**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| symbol | str | ✅ | - | 股票代码 |
| date | str | ❌ | 最新交易日 | 日期，格式 YYYY-MM-DD |
| as_dataframe | bool | ❌ | True | 是否返回 DataFrame |

**注意**: 需要完整服务（付费）

**示例**:
```python
# 获取今日分时数据
df = tf.klines.intraday("600000.SH")
print(df)

# 获取指定日期的分时数据
df = tf.klines.intraday("600000.SH", date="2024-01-15")
```

---

### 1.5 intraday_batch - 批量分时

**功能**: 批量获取多只股票的分时数据

**方法签名**:
```python
tf.klines.intraday_batch(
    symbols: List[str],
    date: Optional[str] = None
) -> Dict[str, pd.DataFrame]
```

**注意**: 需要完整服务（付费）

**示例**:
```python
symbols = ["600000.SH", "000001.SZ"]
data = tf.klines.intraday_batch(symbols)
```

---

## 2️⃣ 实时行情 API (quotes)

### 2.1 get - 获取实时行情

**功能**: 获取单只或多只股票的实时行情

**方法签名**:
```python
tf.quotes.get(
    symbols: List[str],
    as_dataframe: bool = False
) -> Union[List[Dict], pd.DataFrame]
```

**参数说明**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| symbols | List[str] | ✅ | - | 股票代码列表 |
| as_dataframe | bool | ❌ | False | 是否返回 DataFrame |

**注意**: 需要完整服务（付费）

**示例**:
```python
# 获取实时行情
quotes = tf.quotes.get(symbols=["600000.SH", "000001.SZ"])

for q in quotes:
    print(f"{q['symbol']}: {q['last_price']}")
```

---

### 2.2 get_by_symbols - 按代码获取

**功能**: 按股票代码获取实时行情（与 get 类似）

**方法签名**:
```python
tf.quotes.get_by_symbols(
    symbols: List[str],
    fields: Optional[List[str]] = None
) -> List[Dict]
```

**参数说明**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| symbols | List[str] | ✅ | - | 股票代码列表 |
| fields | List[str] | ❌ | None | 指定返回字段 |

**示例**:
```python
# 只获取指定字段
quotes = tf.quotes.get_by_symbols(
    symbols=["600000.SH", "000001.SZ"],
    fields=["symbol", "last_price", "change_percent"]
)
```

---

### 2.3 get_by_universes - 按标的池获取

**功能**: 按标的池（如沪深 300 成分股）获取实时行情

**方法签名**:
```python
tf.quotes.get_by_universes(
    universes: List[str],
    fields: Optional[List[str]] = None
) -> List[Dict]
```

**参数说明**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| universes | List[str] | ✅ | - | 标的池代码列表 |
| fields | List[str] | ❌ | None | 指定返回字段 |

**示例**:
```python
# 获取沪深 300 成分股的实时行情
quotes = tf.quotes.get_by_universes(
    universes=["000300.SH"],  # 沪深 300
    fields=["symbol", "last_price", "change_percent"]
)
```

---

## 3️⃣ 标的信息 API (instruments)

### 3.1 get - 获取标的信息

**功能**: 获取股票、指数等标的的基本信息

**方法签名**:
```python
tf.instruments.get(
    symbols: Optional[List[str]] = None,
    exchange: Optional[str] = None,
    types: Optional[List[str]] = None
) -> List[Instrument]
```

**参数说明**:
| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| symbols | List[str] | ❌ | None | 股票代码列表 |
| exchange | str | ❌ | None | 交易所代码 |
| types | List[str] | ❌ | None | 标的类型列表 |

**示例**:
```python
# 获取单只股票信息
insts = tf.instruments.get(symbols=["600000.SH"])
for inst in insts:
    print(f"{inst.symbol}: {inst.name} ({inst.exchange})")

# 获取上交所所有股票
insts = tf.instruments.get(exchange="SH")

# 获取所有类型
insts = tf.instruments.get(types=["stock", "index", "fund"])
```

**返回数据字段**:
```python
{
    'symbol': '600000.SH',      # 股票代码
    'name': '浦发银行',          # 股票名称
    'exchange': 'SH',           # 交易所
    'type': 'stock',            # 类型
    'industry': '银行',          # 行业
    'list_date': '1999-11-10',  # 上市日期
    'total_shares': 293524.0,   # 总股本（万股）
    'float_shares': 293524.0,   # 流通股本（万股）
}
```

---

### 3.2 batch - 批量获取

**功能**: 批量获取标的信息

**方法签名**:
```python
tf.instruments.batch(
    symbols: List[str]
) -> Dict[str, Instrument]
```

**示例**:
```python
symbols = ["600000.SH", "000001.SZ", "300750.SZ"]
data = tf.instruments.batch(symbols)

for symbol, inst in data.items():
    print(f"{symbol}: {inst.name}")
```

---

## 4️⃣ 其他 API

TickFlow 还可能提供以下 API（需查看最新文档）:

- **exchanges**: 交易所信息
- **universes**: 标的池（如沪深 300、中证 500 等）
- **trading_calendar**: 交易日历
- **adjustments**: 复权信息

---

## 5️⃣ 使用示例

### 5.1 免费服务示例

```python
from tickflow import TickFlow

# 初始化免费服务
tf = TickFlow.free()

# 1. 获取标的信息
insts = tf.instruments.get(symbols=["600000.SH", "000001.SZ"])
for inst in insts:
    print(f"{inst.symbol}: {inst.name}")

# 2. 获取日 K 线数据
df = tf.klines.get("600000.SH", period="1d", count=100)
print(df.tail())

# 3. 获取周 K 线数据
df_weekly = tf.klines.get("600000.SH", period="1w", count=50)

# 4. 批量获取 K 线
symbols = ["600000.SH", "000001.SZ", "300750.SZ"]
data = tf.klines.batch(symbols, period="1d", count=50)
```

### 5.2 完整服务示例

```python
from tickflow import TickFlow

# 初始化完整服务
tf = TickFlow(api_key="tk_4d7e268030a5449abbcc59b28f6e76b8")

# 1. 获取实时行情
quotes = tf.quotes.get(symbols=["600000.SH", "000001.SZ"])
for q in quotes:
    print(f"{q['symbol']}: {q['last_price']} ({q['change_percent']}%)")

# 2. 获取分钟 K 线
df_5m = tf.klines.get("600000.SH", period="5m", count=100)

# 3. 获取分时数据
df_intraday = tf.klines.intraday("600000.SH")

# 4. 获取复权因子
df_factors = tf.klines.ex_factors("600000.SH")
```

### 5.3 批量获取示例

```python
from tickflow import TickFlow

tf = TickFlow(api_key="your-api-key")

# 批量获取 100 只股票的日 K 线
symbols = [f"{code:06d}.SH" for code in range(600000, 600100)]
data = tf.klines.batch(symbols, period="1d", count=250)

# 批量获取实时行情
quotes = tf.quotes.get(symbols=symbols)

# 批量获取标的信息
insts = tf.instruments.batch(symbols)
```

---

## 6️⃣ 数据格式说明

### 6.1 K 线数据字段

| 字段 | 类型 | 说明 |
|------|------|------|
| time | str | 时间（日期） |
| open | float | 开盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| close | float | 收盘价 |
| volume | float | 成交量（手） |
| amount | float | 成交额（元） |

### 6.2 实时行情字段

| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | str | 股票代码 |
| name | str | 股票名称 |
| last_price | float | 最新价 |
| open | float | 今开 |
| high | float | 最高 |
| low | float | 最低 |
| prev_close | float | 昨收 |
| change | float | 涨跌额 |
| change_percent | float | 涨跌幅 (%) |
| volume | float | 成交量 |
| amount | float | 成交额 |
| bid | float | 买一价 |
| ask | float | 卖一价 |
| bid_volume | int | 买一量 |
| ask_volume | int | 卖一量 |
| total_market_cap | float | 总市值 |
| float_market_cap | float | 流通市值 |
| pe_ratio | float | 市盈率 |
| pb_ratio | float | 市净率 |
| turnover_rate | float | 换手率 (%) |
| volume_ratio | float | 量比 |

### 6.3 标的信息字段

| 字段 | 类型 | 说明 |
|------|------|------|
| symbol | str | 股票代码 |
| name | str | 股票名称 |
| exchange | str | 交易所 (SH/SZ) |
| type | str | 类型 (stock/index/fund) |
| industry | str | 行业 |
| list_date | str | 上市日期 |
| total_shares | float | 总股本（万股） |
| float_shares | float | 流通股本（万股） |

---

## 7️⃣ 错误处理

```python
from tickflow import TickFlow
from tickflow.exceptions import (
    TickFlowError,
    AuthenticationError,
    RateLimitError,
    NotFoundError
)

tf = TickFlow(api_key="your-api-key")

try:
    quotes = tf.quotes.get(symbols=["600000.SH"])
except AuthenticationError as e:
    print(f"认证失败：{e}")
except RateLimitError as e:
    print(f"请求频率超限：{e}")
except NotFoundError as e:
    print(f"数据未找到：{e}")
except TickFlowError as e:
    print(f"其他错误：{e}")
```

**常见错误码**:
| 错误 | 说明 | 解决方案 |
|------|------|---------|
| `AuthenticationError` | API Key 无效 | 检查 API Key 是否正确 |
| `RateLimitError` | 请求频率超限 | 降低请求频率 |
| `NotFoundError` | 数据未找到 | 检查股票代码是否正确 |
| `TimeoutError` | 请求超时 | 检查网络连接 |

---

## 📚 相关资源

- **官网**: https://tickflow.tech
- **文档**: https://tickflow.org
- **GitHub**: 待补充
- **支持**: support@tickflow.tech

---

**最后更新**: 2026-03-19
