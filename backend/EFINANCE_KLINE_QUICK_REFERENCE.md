# efinance K 线周期 - 快速参考

## 🎯 周期代码

| 代码 | 说明 | efinance klt |
|-----|------|-------------|
| `1m` | 1 分钟线 | 1 |
| `5m` | 5 分钟线 | 5 |
| `15m` | 15 分钟线 | 15 |
| `30m` | 30 分钟线 | 30 |
| `60m` | 60 分钟线 | 60 |
| `daily` | 日线（默认） | 101 |
| `weekly` | 周线 | 102 |
| `monthly` | 月线 | 103 |

## 📊 复权方式

| 代码 | 说明 | efinance fqt |
|-----|------|-------------|
| `qfq` | 前复权（默认） | 1 |
| `hfq` | 后复权 | 2 |
| `no` | 不复权 | 0 |

## 🔧 快速使用

### 日线
```python
klines = await adapter.get_kline("600519")
```

### 60 分钟线
```python
klines = await adapter.get_kline("600519", period="60m")
```

### 周线
```python
klines = await adapter.get_kline("600519", period="weekly")
```

### 指定日期 + 复权
```python
klines = await adapter.get_kline(
    "600519",
    start_date="2024-01-01",
    end_date="2024-12-31",
    adjust="qfq",
    period="60m"
)
```

## 📈 数据字段

```python
for kline in klines:
    kline.date        # 日期
    kline.open        # 开盘价
    kline.high        # 最高价
    kline.low         # 最低价
    kline.close       # 收盘价
    kline.volume      # 成交量
    kline.amount      # 成交额
    kline.turnover_rate  # 换手率
    kline.pre_close   # 前收盘价
```

## ⚠️ 注意事项

### 分钟线数据量大
```python
# ✅ 推荐：指定日期范围
klines = await adapter.get_kline(
    "600519",
    period="60m",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# ❌ 不推荐：获取全量
klines = await adapter.get_kline("600519", period="1m")
```

### 复权选择
- **前复权（qfq）**：技术分析（推荐）
- **后复权（hfq）**：收益计算
- **不复权（no）**：历史价格

## 🧪 测试命令

```bash
python test_efinance_kline_periods.py
```

## 📖 完整文档

- [使用指南](./EFINANCE_KLINE_PERIODS.md)
- [优化总结](./EFINANCE_KLINE_OPTIMIZATION_COMPLETE.md)

---

**提示**：所有 K 线数据都包含反风控机制！
