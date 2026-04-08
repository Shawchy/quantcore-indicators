# 交易时段智能时效性检查

## 概述

数据时效性检查器现已支持**交易时段智能判断**，根据当前是否在交易时段、是否已收盘、是否是交易日等因素，智能决定数据是否需要更新。

## 核心特性

### 1. 交易时段识别

系统会自动识别当前时间属于：
- **交易时段**：9:30-11:30（早盘）或 13:00-15:00（午盘）
- **非交易时段**：
  - 未开盘（15:00 之前，9:30 之前）
  - 已收盘（15:00 之后）
  - 非交易日（周末、节假日）

### 2. 智能判断策略

根据不同交易时段，采用不同的时效性判断策略：

| 时段 | 数据日期 | 判断策略 | 说明 |
|------|---------|---------|------|
| **交易时段** | 任意 | 标准有效期判断 | 数据变化快，使用标准有效期 |
| **已收盘** | 今天 | ✅ 有效 | 今天的数据，收盘后仍然有效 |
| **已收盘** | 非今天 | 标准有效期判断 | 使用固定有效期判断 |
| **非交易日** | 最新交易日 | ✅ 有效 | 使用最新交易日数据，有效 |
| **非交易日** | 非最新 | 标准有效期判断 | 使用固定有效期判断 |
| **周末** | 周五 | ✅ 有效 | 周五数据在周末有效 |

## 交易时段定义

### A 股交易时间

```python
# 早盘：9:30 - 11:30
MORNING_START = (9, 30)
MORNING_END = (11, 30)

# 午盘：13:00 - 15:00
AFTERNOON_START = (13, 0)
AFTERNOON_END = (15, 0)
```

### 时段判断

```python
from app.utils.data_freshness_checker import MarketSession

# 判断是否在交易时段
is_trading = MarketSession.is_trading_time()  # True/False

# 判断是否已收盘
is_closed = MarketSession.is_market_closed()  # True/False
```

## 使用示例

### 示例 1：基本使用（自动启用交易时段检查）

```python
from app.utils.data_freshness_checker import DataFreshnessChecker
from app.storage.sqlite import MarketTurnover

async def get_market_turnover(session):
    checker = DataFreshnessChecker(session)
    
    # 自动启用交易时段检查
    data, is_stale = await checker.check_freshness(
        MarketTurnover,
        'market_turnover',
        enable_session_check=True  # 启用智能判断
    )
    
    if is_stale:
        # 需要获取新数据
        return await fetch_from_api()
    else:
        return data
```

### 示例 2：禁用交易时段检查

```python
# 使用固定有效期判断（不启用智能判断）
data, is_stale = await checker.check_freshness(
    MarketTurnover,
    'market_turnover',
    enable_session_check=False,  # 禁用智能判断
    custom_max_age_hours=40      # 使用固定 40 小时
)
```

### 示例 3：实时行情（高频数据）

```python
from app.storage.sqlite import RealtimeQuote

async def get_realtime_quote(session, code: str):
    checker = DataFreshnessChecker(session)
    
    # 交易时段：数据变化快，2 小时有效期
    # 非交易时段：使用最新数据，不频繁更新
    data, is_stale = await checker.check_freshness(
        RealtimeQuote,
        'realtime_quote',
        filter_conditions={'code': code}
    )
    
    if is_stale:
        return await fetch_quote_from_api(code)
    else:
        return data
```

## 实际场景分析

### 场景 1：交易日 10:00（交易时段）

**状态**:
- 当前时间：10:00
- 时段：交易时段（早盘）
- 数据：昨天 15:00 收盘数据

**判断**:
```
数据年龄：19 小时
有效期：40 小时
判断：✅ 有效（19 < 40）
结果：使用昨天收盘数据
```

### 场景 2：交易日 16:00（已收盘）

**状态**:
- 当前时间：16:00
- 时段：已收盘
- 数据：今天 15:00 收盘数据

**判断**:
```
数据年龄：1 小时
判断：✅ 有效（今天数据 + 已收盘）
结果：使用今天收盘数据
说明：即使只有 1 小时，因为是今天数据且已收盘，认为有效
```

### 场景 3：交易日 14:00（交易时段）

**状态**:
- 当前时间：14:00
- 时段：交易时段（午盘）
- 数据：昨天 15:00 收盘数据

**判断**:
```
数据年龄：23 小时
有效期：40 小时
判断：✅ 有效（23 < 40）
结果：使用昨天收盘数据
说明：虽然是交易时段，但数据仍在有效期内
```

### 场景 4：周六 10:00（非交易日）

**状态**:
- 当前时间：周六 10:00
- 时段：非交易日
- 数据：周五 15:00 收盘数据

**判断**:
```
数据年龄：19 小时
判断：✅ 有效（周五数据 + 周末）
结果：使用周五收盘数据
说明：周末不交易，周五数据在周末有效
```

### 场景 5：周一 09:00（非交易时段）

**状态**:
- 当前时间：周一 09:00
- 时段：未开盘
- 数据：周五 15:00 收盘数据

**判断**:
```
数据年龄：66 小时
有效期：40 小时
判断：❌ 过期（66 > 40）
结果：需要获取新数据
说明：周一应该使用新数据
```

### 场景 6：周一 15:30（已收盘）

**状态**:
- 当前时间：周一 15:30
- 时段：已收盘
- 数据：周一 15:00 收盘数据

**判断**:
```
数据年龄：0.5 小时
判断：✅ 有效（今天数据 + 已收盘）
结果：使用周一收盘数据
```

### 场景 7：国庆节长假

**状态**:
- 当前时间：10 月 3 日（周四，国庆节）
- 时段：非交易日
- 数据：9 月 30 日（周一）15:00 收盘数据

**判断**:
```
数据年龄：72 小时
判断：✅ 有效（最新交易日数据 + 非交易日）
结果：使用 9 月 30 日数据
说明：节假日不交易，使用节前数据
```

## 日志输出

### 交易时段

```
2026-04-08 10:30:00 | DEBUG | app.utils.data_freshness_checker:check_freshness:245 - 数据有效：market_turnover, age=19.00h < max=40h, session=交易时段
```

### 已收盘

```
2026-04-08 16:00:00 | DEBUG | app.utils.data_freshness_checker:check_freshness:245 - 数据有效：market_turnover, age=1.00h < max=40h, session=已收盘
```

### 非交易日

```
2026-04-13 10:00:00 | DEBUG | app.utils.data_freshness_checker:check_freshness:245 - 数据有效：market_turnover, age=19.00h < max=40h, session=非交易日（周末）
```

### 数据过期

```
2026-04-08 10:30:00 | INFO | app.utils.data_freshness_checker:check_freshness:238 - 数据已过期：market_turnover, age=50.00h > max=40h, session=交易时段
```

## 支持的数据类型

以下数据类型会自动启用交易时段智能判断：

- `realtime_quote` - 实时行情
- `tick_data` - 分时数据
- `kline_daily` - 日 K 线
- `market_turnover` - 市场成交额 ⭐
- `moneyflow` - 资金流向
- `billboard` - 龙虎榜

其他数据类型使用固定有效期判断。

## 降级处理

系统具有完善的降级机制：

1. **交易日历服务不可用**: 使用简单判断（排除周末）
2. **API 获取失败**: 使用本地缓存
3. **数据库异常**: 返回默认值

```python
# 交易日历服务加载失败
async def _get_trading_calendar(self):
    if self._trading_calendar is None:
        try:
            from app.services.trading_calendar import trading_calendar
            await trading_calendar.ensure_initialized()
            self._trading_calendar = trading_calendar
        except Exception as e:
            logger.warning(f"加载交易日历服务失败：{e}")
            self._trading_calendar = None  # 降级处理
    return self._trading_calendar
```

## 性能优化

### 1. 懒加载交易日历

```python
# 只在需要时才加载交易日历服务
async def _get_trading_calendar(self):
    if self._trading_calendar is None:
        # 首次调用时加载
        ...
    return self._trading_calendar
```

### 2. 缓存判断结果

```python
# 内存缓存判断结果
is_trading = MarketSession.is_trading_time()  # 快速判断
```

### 3. 异步处理

```python
# 所有 I/O 操作都是异步的
data, is_stale = await checker.check_freshness(...)
```

## 最佳实践

### 1. 根据数据类型选择

```python
# 高频数据：自动启用智能判断
data, is_stale = await checker.check_freshness(
    RealtimeQuote, 'realtime_quote'
)

# 静态数据：使用固定有效期
data, is_stale = await checker.check_freshness(
    StockList, 'stock_list', custom_max_age_hours=2160
)
```

### 2. 结合业务需求

```python
# 盘中实时数据：交易时段频繁更新
if MarketSession.is_trading_time():
    data, is_stale = await checker.check_freshness(
        RealtimeQuote, 'realtime_quote',
        custom_max_age_hours=0.5  # 30 分钟
    )
else:
    # 非交易时段：使用最新数据
    data, is_stale = await checker.check_freshness(
        RealtimeQuote, 'realtime_quote',
        custom_max_age_hours=24  # 24 小时
    )
```

### 3. 监控日志

```python
# 生产环境建议设置 INFO 级别日志
# 可以清晰看到数据时效性判断结果

2026-04-08 10:30:00 | INFO | 数据已过期：market_turnover, age=50.00h > max=40h, session=交易时段
2026-04-08 16:00:00 | DEBUG | 数据有效：market_turnover, age=1.00h < max=40h, session=已收盘
```

## 配置说明

### 交易时段配置

```python
class MarketSession:
    # 可根据实际情况调整交易时间
    MORNING_START = (9, 30)    # 早盘开始
    MORNING_END = (11, 30)     # 早盘结束
    AFTERNOON_START = (13, 0)  # 午盘开始
    AFTERNOON_END = (15, 0)    # 午盘结束
```

### 有效期配置

```python
class DataFreshnessPolicy:
    POLICIES = {
        'realtime_quote': 2.0,    # 实时行情 - 2 小时
        'market_turnover': 40,    # 市场成交额 - 40 小时
        # ... 其他配置
    }
```

## 总结

交易时段智能时效性检查提供了：

- ✅ **智能判断**: 根据交易时段自动调整策略
- ✅ **灵活配置**: 支持自定义交易时间和有效期
- ✅ **降级处理**: 服务不可用时自动降级
- ✅ **性能优化**: 懒加载、缓存、异步处理
- ✅ **详细日志**: 便于监控和调试

在实际应用中，可以显著减少不必要的 API 请求，同时保证数据的时效性。
