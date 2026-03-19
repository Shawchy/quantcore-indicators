# TickFlow 已实现接口清单

## 📊 总览

在 [`tickflow_adapter.py`](d:\PROJ\Quant\backend\app\adapters\tickflow_adapter.py) 中已实现的 TickFlow 数据源适配器接口。

---

## ✅ 已实现的核心接口

### 1. 基础管理接口

| 接口 | 状态 | 说明 |
|------|------|------|
| `initialize()` | ✅ 已实现 | 初始化 TickFlow 客户端（支持免费/付费服务） |
| `close()` | ✅ 已实现 | 关闭 TickFlow 客户端 |
| `_test_connection()` | ✅ 已实现 | 测试连接 |
| `_get_from_cache()` | ✅ 已实现 | 从缓存获取数据 |
| `_set_to_cache()` | ✅ 已实现 | 设置缓存 |
| `_symbol_to_tickflow()` | ✅ 已实现 | 股票代码转换（6 位 → TickFlow 格式） |
| `_symbol_from_tickflow()` | ✅ 已实现 | 股票代码转换（TickFlow 格式 → 6 位） |

---

### 1.5 交易所接口（新增）

| 接口 | 状态 | 免费 | 付费 | 说明 |
|------|------|------|------|------|
| `get_exchanges()` | ✅ 已实现 | ✅ | ✅ | 获取交易所列表 |

**实现细节**:
```python
# 获取交易所列表
exchanges = await adapter.get_exchanges()
# 返回：[
#   {'exchange': 'SH', 'region': 'CN', 'count': 3332},
#   {'exchange': 'SZ', 'region': 'CN', 'count': 3895},
#   {'exchange': 'BJ', 'region': 'CN', 'count': 299},
#   {'exchange': 'SHFE', 'region': 'CN', 'count': 20},  # 上期所
#   {'exchange': 'DCE', 'region': 'CN', 'count': 26},   # 大商所
#   {'exchange': 'CZCE', 'region': 'CN', 'count': 26},  # 郑商所
#   {'exchange': 'CFFEX', 'region': 'CN', 'count': 8},  # 中金所
#   {'exchange': 'INE', 'region': 'CN', 'count': 5},    # 能源中心
#   {'exchange': 'GFEX', 'region': 'CN', 'count': 5},   # 广期所
# ]
```

**支持的交易所**:
| 交易所代码 | 名称 | 地区 | 标的类型 |
|-----------|------|------|---------|
| SH | 上海证券交易所 | CN | A 股、债券、基金 |
| SZ | 深圳证券交易所 | CN | A 股、债券、基金 |
| BJ | 北京证券交易所 | CN | A 股 |
| SHFE | 上海期货交易所 | CN | 期货 |
| DCE | 大连商品交易所 | CN | 期货 |
| CZCE | 郑州商品交易所 | CN | 期货 |
| CFFEX | 中国金融期货交易所 | CN | 金融期货 |
| INE | 上海国际能源交易中心 | CN | 原油期货 |
| GFEX | 广州期货交易所 | CN | 期货 |

**缓存策略**:
- 交易所列表缓存 1 小时
- 自动从 TickFlow SDK 获取最新数据

---

### 2. 股票信息接口

| 接口 | 状态 | 免费 | 付费 | 说明 |
|------|------|------|------|------|
| `get_stock_list()` | ⚠️ 部分实现 | ❌ | ❌ | TickFlow 不支持获取全部股票列表 |
| `get_stock_info(code)` | ✅ 已实现 | ✅ | ✅ | 获取单只股票基本信息 |
| `get_instruments(symbols)` | ✅ 已实现 | ✅ | ✅ | 批量获取标的信息 |

**实现细节**:
```python
# 获取单只股票信息
info = await adapter.get_stock_info("600000")
# 返回：StockBasicInfo(code='600000', name='浦发银行', market='SH', ...)

# 批量获取标的信息
insts = await adapter.get_instruments(["600000.SH", "000001.SZ"])
# 返回：[{'symbol': '600000.SH', 'name': '浦发银行', ...}, ...]
```

---

### 3. K 线数据接口

| 接口 | 状态 | 免费 | 付费 | 说明 |
|------|------|------|------|------|
| `get_kline(code, period, ...)` | ✅ 已实现 | ✅ (仅日线) | ✅ (全周期) | 获取 K 线数据 |
| `get_weekly_kline(code)` | ✅ 已实现 | ✅ | ✅ | 获取周 K 线 |
| `get_monthly_kline(code)` | ✅ 已实现 | ✅ | ✅ | 获取月 K 线 |

**支持的周期**:
| 周期 | 方法 | 免费 | 付费 |
|------|------|------|------|
| 日 K | `period='daily'` | ✅ | ✅ |
| 周 K | `get_weekly_kline()` | ✅ | ✅ |
| 月 K | `get_monthly_kline()` | ✅ | ✅ |
| 分钟 K 线 | `period='5m'` 等 | ❌ | ✅ |

**实现细节**:
```python
# 获取日 K 线
klines = await adapter.get_kline("600000", period="daily")
# 返回：[KLineData(code='600000', date='20240102', open=10.25, high=10.38, ...), ...]

# 获取周 K 线
klines = await adapter.get_weekly_kline("600000")

# 获取月 K 线
klines = await adapter.get_monthly_kline("600000")

# 获取 5 分钟 K 线（仅付费服务）
klines = await adapter.get_kline("600000", period="5m")
```

**缓存策略**:
- K 线数据缓存 5 分钟
- 自动处理股票代码格式转换
- 支持日期范围过滤

---

### 4. 实时行情接口

| 接口 | 状态 | 免费 | 付费 | 说明 |
|------|------|------|------|------|
| `get_realtime_quote(code)` | ✅ 已实现 | ❌ | ✅ | 获取实时行情 |

**实现细节**:
```python
# 获取实时行情（仅付费服务）
quote = await adapter.get_realtime_quote("600000")
# 返回：{
#   'code': '600000',
#   'name': '浦发银行',
#   'price': 10.33,
#   'change': 0.15,
#   'change_pct': 1.47,
#   'volume': 1234567,
#   'amount': 12789000.0,
#   ...
# }
```

**缓存策略**:
- 实时行情缓存 10 秒（TickFlow 更新快）
- 免费服务返回空字典并记录警告

---

### 5. 板块相关接口

| 接口 | 状态 | 免费 | 付费 | 说明 |
|------|------|------|------|------|
| `get_sector_list()` | ⚠️ 占位 | ❌ | ❌ | TickFlow 不支持 |
| `get_sector_components()` | ⚠️ 占位 | ❌ | ❌ | TickFlow 不支持 |
| `get_belong_board(code)` | ⚠️ 占位 | ❌ | ❌ | TickFlow 不支持 |

**实现**: 返回空列表并记录警告日志

---

### 6. 资金流向接口

| 接口 | 状态 | 免费 | 付费 | 说明 |
|------|------|------|------|------|
| `get_today_bill()` | ⚠️ 占位 | ❌ | ❌ | TickFlow 不支持 |
| `get_history_bill()` | ⚠️ 占位 | ❌ | ❌ | TickFlow 不支持 |

**实现**: 返回空列表并记录警告日志

---

### 7. 股东信息接口

| 接口 | 状态 | 免费 | 付费 | 说明 |
|------|------|------|------|------|
| `get_top10_stock_holder_info()` | ⚠️ 占位 | ❌ | ❌ | TickFlow 不支持 |

**实现**: 返回空列表并记录警告日志

---

### 8. 指数成分股接口

| 接口 | 状态 | 免费 | 付费 | 说明 |
|------|------|------|------|------|
| `get_members(index_code)` | ⚠️ 占位 | ❌ | ❌ | TickFlow 不支持 |

**实现**: 返回空列表并记录警告日志

---

### 9. 市场实时行情接口

| 接口 | 状态 | 免费 | 付费 | 说明 |
|------|------|------|------|------|
| `get_market_realtime_quotes()` | ⚠️ 占位 | ❌ | ❌ | TickFlow 不支持批量 |

**实现**: 返回空列表并记录警告日志

---

### 10. 筹码数据接口

| 接口 | 状态 | 免费 | 付费 | 说明 |
|------|------|------|------|------|
| `get_chip_data()` | ⚠️ 占位 | ❌ | ❌ | TickFlow 不支持 |

**实现**: 返回空列表并记录警告日志

---

## 📊 实现状态统计

| 类别 | 已实现 | 占位 | 总计 | 完成率 |
|------|--------|------|------|--------|
| **核心功能** | 7 | 0 | 7 | 100% |
| **股票信息** | 2 | 1 | 3 | 67% |
| **K 线数据** | 3 | 0 | 3 | 100% |
| **实时行情** | 1 | 0 | 1 | 100% |
| **交易所信息** | 1 | 0 | 1 | 100% |
| **板块相关** | 0 | 3 | 3 | 0% |
| **资金流向** | 0 | 2 | 2 | 0% |
| **股东信息** | 0 | 1 | 1 | 0% |
| **指数成分** | 0 | 1 | 1 | 0% |
| **市场概况** | 0 | 1 | 1 | 0% |
| **筹码数据** | 0 | 1 | 1 | 0% |
| **总计** | **14** | **10** | **24** | **58%** |

---

## 🎯 实际可用的功能

### 免费服务（无需 API Key）

✅ **可用功能**:
1. 获取单只股票信息
2. 批量获取标的信息
3. 获取日 K 线数据
4. 获取周 K 线数据
5. 获取月 K 线数据

❌ **不可用功能**:
- 实时行情
- 分钟级 K 线
- 板块信息
- 资金流向
- 股东信息

### 完整服务（需要 API Key）

✅ **额外可用功能**:
1. 实时行情
2. 分钟级 K 线（1m/5m/15m/30m/60m）
3. 分时数据（需直接调用 SDK）

---

## 💻 使用示例

### 示例 1：免费服务获取日 K 线

```python
from app.adapters.factory import data_source_manager

# 初始化
await data_source_manager.initialize()

# 获取日 K 线（自动使用免费服务）
klines = await data_source_manager.get_kline(
    "600000",
    source_type="tickflow"
)
print(f"获取 {len(klines)} 条数据")
```

### 示例 2：付费服务获取实时行情

```python
# 配置 API Key 后
quote = await data_source_manager.get_realtime_quote(
    "600000",
    source_type="tickflow"
)
print(f"最新价：{quote['price']}")
```

### 示例 3：获取股票信息

```python
info = await data_source_manager.get_stock_info(
    "600000",
    source_type="tickflow"
)
print(f"{info.code}: {info.name} ({info.market})")
```

---

## 🔧 直接调用 TickFlow SDK

对于适配器未实现的功能，可以直接使用 TickFlow SDK：

### 获取分时数据

```python
from tickflow import TickFlow

tf = TickFlow(api_key="tk_4d7e268030a5449abbcc59b28f6e76b8")

# 分时数据（适配器未实现，直接调用 SDK）
df = tf.klines.intraday("600000.SH")
```

### 批量获取 K 线

```python
# 批量获取（适配器未实现，直接调用 SDK）
symbols = ["600000.SH", "000001.SZ"]
data = tf.klines.batch(symbols, period="1d", count=100)
```

### 获取复权因子

```python
# 复权因子（适配器未实现，直接调用 SDK）
df = tf.klines.ex_factors("600000.SH")
```

---

## 📝 注意事项

1. **股票代码格式**: 适配器自动处理格式转换
   - 输入：`"600000"`
   - TickFlow: `"600000.SH"`

2. **缓存机制**: 所有数据都有内存缓存
   - K 线：5 分钟
   - 股票信息：10 分钟
   - 实时行情：10 秒

3. **错误处理**: 所有接口都有完整的错误处理和日志记录

4. **免费服务限制**: 免费服务不提供实时行情和分钟 K 线

---

## 🚀 后续可实现的接口

以下接口可以通过直接调用 TickFlow SDK 实现：

1. `get_intraday()` - 分时数据
2. `get_kline_batch()` - 批量 K 线
3. `get_ex_factors()` - 复权因子
4. `get_trading_calendar()` - 交易日历

---

**最后更新**: 2026-03-19
