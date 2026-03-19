# efinance K 线周期优化指南

## 📊 优化内容

已优化 `get_kline` 接口，支持多种 K 线周期：

### 支持的周期

| 周期代码 | 说明 | efinance klt 参数 |
|---------|------|------------------|
| `1m` | 1 分钟 | 1 |
| `5m` | 5 分钟 | 5 |
| `15m` | 15 分钟 | 15 |
| `30m` | 30 分钟 | 30 |
| `60m` | 60 分钟 | 60 |
| `daily` | 日线（默认） | 101 |
| `weekly` | 周线 | 102 |
| `monthly` | 月线 | 103 |

### 复权方式

| 复权代码 | 说明 | efinance fqt 参数 |
|---------|------|------------------|
| `qfq` | 前复权（默认） | 1 |
| `hfq` | 后复权 | 2 |
| `no` | 不复权 | 0 |

## 🎯 使用示例

### 1. 日线数据（默认）

```python
from app.adapters.factory import DataSourceManager

adapter = await DataSourceManager.get_adapter("efinance")

# 日线数据（默认周期）
klines = await adapter.get_kline("600519")
print(f"贵州茅台日线数据：{len(klines)}条")

# 指定日期范围
klines = await adapter.get_kline(
    "600519",
    start_date="2024-01-01",
    end_date="2024-12-31",
    period="daily"
)
```

### 2. 分钟线数据

```python
# 1 分钟线
klines = await adapter.get_kline("600519", period="1m")

# 5 分钟线
klines = await adapter.get_kline("600519", period="5m")

# 15 分钟线
klines = await adapter.get_kline("600519", period="15m")

# 30 分钟线
klines = await adapter.get_kline("600519", period="30m")

# 60 分钟线
klines = await adapter.get_kline("600519", period="60m")
```

### 3. 周线和月线

```python
# 周线
klines = await adapter.get_kline("600519", period="weekly")

# 月线
klines = await adapter.get_kline("600519", period="monthly")
```

### 4. 复权设置

```python
# 前复权（默认）
klines = await adapter.get_kline("600519", adjust="qfq")

# 后复权
klines = await adapter.get_kline("600519", adjust="hfq")

# 不复权
klines = await adapter.get_kline("600519", adjust="no")
```

### 5. 组合使用

```python
# 60 分钟线 + 前复权 + 指定日期范围
klines = await adapter.get_kline(
    "600519",
    start_date="2024-01-01",
    end_date="2024-12-31",
    adjust="qfq",
    period="60m"
)

# 周线 + 后复权
klines = await adapter.get_kline(
    "600519",
    adjust="hfq",
    period="weekly"
)
```

## 📈 数据字段

返回的 K 线数据包含以下字段：

```python
for kline in klines:
    print(f"日期：{kline.date}")
    print(f"开盘：{kline.open}")
    print(f"最高：{kline.high}")
    print(f"最低：{kline.low}")
    print(f"收盘：{kline.close}")
    print(f"成交量：{kline.volume}")
    print(f"成交额：{kline.amount}")
    print(f"换手率：{kline.turnover_rate}")
    print(f"前收盘：{kline.pre_close}")
```

## 🔧 缓存机制

不同周期的 K 线数据使用独立的缓存：

```python
# 日线缓存（5 分钟）
cache_key_daily = adapter._get_cache_key('kline', code="600519", period="daily")

# 60 分钟缓存（5 分钟）
cache_key_60m = adapter._get_cache_key('kline', code="600519", period="60m")

# 周线缓存（5 分钟）
cache_key_weekly = adapter._get_cache_key('kline', code="600519", period="weekly")
```

**缓存时间**：所有 K 线数据统一缓存 5 分钟

## 📊 性能优化

### 1. 批量获取多周期数据

```python
# 同时获取多个周期
periods = ["daily", "weekly", "monthly"]
results = {}

for period in periods:
    klines = await adapter.get_kline("600519", period=period)
    results[period] = klines
    print(f"{period}: {len(klines)}条")
```

### 2. 利用缓存减少请求

```python
# 第一次：实际请求
klines1 = await adapter.get_kline("600519", period="daily")

# 5 分钟内：直接返回缓存
klines2 = await adapter.get_kline("600519", period="daily")  # 无网络请求

# 不同周期：独立缓存
klines3 = await adapter.get_kline("600519", period="60m")  # 新的请求
```

### 3. 频率控制

所有 K 线请求都自动包含频率控制：

```python
# 自动延迟 1-2 秒（根据时间段调整）
klines = await adapter.get_kline("600519", period="1m")

# 交易时段：2-4 秒延迟
# 非交易时段：1-2 秒延迟
# 夜间：0.5-1.5 秒延迟
```

## ⚠️ 注意事项

### 1. 数据量

- **分钟线**：数据量较大，建议指定日期范围
- **日线**：数据量适中，适合获取全量数据
- **周线/月线**：数据量较小，适合长期趋势分析

```python
# ✅ 推荐：分钟线指定日期范围
klines = await adapter.get_kline(
    "600519",
    period="60m",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# ❌ 不推荐：分钟线获取全量数据
klines = await adapter.get_kline("600519", period="1m")  # 数据量巨大
```

### 2. 数据更新频率

- **分钟线**：交易时段实时更新
- **日线**：交易日 15:00 后更新
- **周线/月线**：定期更新

### 3. 复权处理

- **前复权（qfq）**：推荐用于技术分析
- **后复权（hfq）**：推荐用于计算总收益
- **不复权（no）**：推荐用于查看历史真实价格

## 🧪 测试示例

```python
import asyncio
from app.adapters.efinance_adapter import EFinanceAdapter

async def test_kline_periods():
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    periods = ["1m", "5m", "30m", "60m", "daily", "weekly", "monthly"]
    
    for period in periods:
        try:
            klines = await adapter.get_kline("600519", period=period)
            print(f"✓ {period}: {len(klines)}条")
        except Exception as e:
            print(f"✗ {period}: {e}")

asyncio.run(test_kline_periods())
```

## 📖 底层实现

### efinance 参数映射

```python
# 周期映射
period_map = {
    '1m': 1,      # 1 分钟
    '5m': 5,      # 5 分钟
    '15m': 15,    # 15 分钟
    '30m': 30,    # 30 分钟
    '60m': 60,    # 60 分钟
    'daily': 101, # 日线
    'weekly': 102, # 周线
    'monthly': 103 # 月线
}

# 复权映射
adjust_map = {
    'qfq': 1,   # 前复权
    'hfq': 2,   # 后复权
    'no': 0,    # 不复权
}

# 调用 efinance
df = ef.stock.get_quote_history(
    code.zfill(6),
    period=klt,      # 周期
    fqt=fqt,         # 复权
    beg=start_date,  # 开始日期
    end=end_date     # 结束日期
)
```

## 📊 应用场景

### 1. 短线交易（分钟线）

```python
# 5 分钟线 - 适合日内交易
klines = await adapter.get_kline(
    "600519",
    period="5m",
    start_date="2024-12-01",
    end_date="2024-12-31"
)
```

### 2. 中线趋势（日线/周线）

```python
# 日线 - 适合中线分析
klines = await adapter.get_kline(
    "600519",
    period="daily",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# 周线 - 适合长期趋势
klines = await adapter.get_kline(
    "600519",
    period="weekly",
    start_date="2020-01-01",
    end_date="2024-12-31"
)
```

### 3. 长线投资（月线）

```python
# 月线 - 适合长线投资分析
klines = await adapter.get_kline(
    "600519",
    period="monthly",
    start_date="2010-01-01",
    end_date="2024-12-31"
)
```

## 🎯 总结

**优化成果**：
- ✅ 支持 8 种 K 线周期（1m/5m/15m/30m/60m/daily/weekly/monthly）
- ✅ 支持 3 种复权方式（qfq/hfq/no）
- ✅ 自动缓存不同周期数据
- ✅ 内置频率控制和失败重试
- ✅ 完整的文档和示例

**使用建议**：
- 分钟线：指定日期范围，避免数据量过大
- 日线：适合日常分析，数据量适中
- 周线/月线：适合长期趋势分析
- 复权：技术分析用前复权，收益计算用后复权

---

**提示**：所有 K 线数据都包含反风控机制，可安全使用！
