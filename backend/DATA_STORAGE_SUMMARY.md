# 数据存储逻辑快速总结

**检查时间**: 2026-03-12 18:15  
**核心结论**: ✅ 存储逻辑完整，分类清晰，Tushare 120 分数据已完全存储

---

## 📊 一句话总结

**系统实现了完整的分层数据存储架构**：
- **数据库**: 9 张表，覆盖所有核心数据
- **存储**: SQLite(热) + Parquet(冷) + 内存缓存
- **加载**: 5 级优先级，智能按需加载
- **Tushare**: 120 分基础数据已完整存储，高级数据自动降级到 AkShare

---

## 🗄️ 数据库表结构（9 张表）

| 表名 | 用途 | 数据量 | 状态 |
|------|------|--------|------|
| stock_info | 股票基本信息 | 5000+ | ✅ 已存储 |
| kline | K 线行情数据 | 每只 2000+ 条 | ✅ 已存储 |
| technical_indicators | 技术指标 | 每只 2000+ | ✅ 已存储 |
| chip_data | 筹码数据 | 按需 | ✅ 已存储 |
| sector_info | 板块信息 | 100+ | ✅ 已存储 |
| watchlist | 自选股 | 用户定义 | ✅ 已存储 |
| strategy | 策略配置 | 用户定义 | ✅ 已存储 |
| backtest_record | 回测记录 | 用户定义 | ✅ 已存储 |
| trade_record | 交易记录 | 用户定义 | ✅ 已存储 |

---

## 📁 数据存储位置

```
data/
├── sqlite/
│   └── quant.db              # 主数据库 (10-100MB)
├── parquet/
│   ├── kline/{code}/         # K 线数据（按年分区）
│   ├── indicators/{code}.parquet
│   ├── chip/{code}.parquet
│   └── backtest/{id}.parquet
└── trading_days_cache.json    # 交易日历缓存
```

---

## 🔄 数据加载策略

### 5 级优先级加载

```
用户请求
    ↓
[同步] 本月数据 (20 条，<100ms) ← 立即返回
    ↓
[后台] 本年数据 (250 条)
    ↓
[后台] 近 3 年数据 (750 条)
    ↓
[后台] 近 5 年数据 (1250 条)
    ↓
[后台] 全部历史 (2000+ 条)
```

| 优先级 | 范围 | 加载方式 | 用途 |
|--------|------|---------|------|
| 1 | 本月 | 同步 | 日常看盘 |
| 2 | 本年 | 同步 | 年度分析 |
| 3 | 近 3 年 | 后台 | 中期回测 |
| 4 | 近 5 年 | 后台 | 长期回测 |
| 5 | 全部 | 后台 | 完整回测 |

---

## 💾 缓存系统

### 7 种缓存类型

| 缓存 | 容量 | TTL | 用途 |
|------|------|-----|------|
| realtime | 500 | 60s | 实时行情 |
| kline | 200 | 300s | K 线数据 |
| indicators | 200 | 300s | 技术指标 |
| sector | 100 | 300s | 板块数据 |
| chip | 200 | 600s | 筹码数据 |
| screener | 50 | 120s | 选股结果 |
| backtest | 20 | 3600s | 回测结果 |

---

## 📡 Tushare 数据存储状态

### ✅ 已完整存储（120 分基础）

- [x] 股票基本信息 → stock_info 表
- [x] 日线行情 → kline 表 + Parquet
- [x] 复权因子 → 整合到 kline 表
- [x] 指数基本信息 → stock_info 表
- [x] 指数日线 → kline 表
- [x] 交易日历 → JSON 缓存

### ⚠️ 使用 AkShare 补充（需要更高级 Tushare 积分）

| 数据类型 | Tushare 积分 | 当前方案 |
|---------|------------|---------|
| 财务数据 | 800 | ✅ AkShare |
| 周月线 | 2000 | ✅ AkShare |
| 分钟线 | 5000 | ✅ AkShare |
| 资金流向 | 5000 | ✅ AkShare |
| 筹码分布 | 10000 | ✅ AkShare |

---

## 🎯 核心优化点

### 1. 批量保存优化（性能提升 10-50 倍）

```python
# 优化前：N 次查询 + N 次插入
for kline in klines:
    if not exists(kline):
        insert(kline)

# 优化后：1 次查询 + 1 次批量插入
existing = query_all_dates()
to_insert = [k for k in klines if k.date not in existing]
bulk_insert(to_insert)
```

### 2. 分层加载优化

```python
# 优先加载本月数据（快速响应）
progress = await load_priority(CURRENT_MONTH)
return {"status": "partial", "background_loading": True}

# 后台自动补全历史数据
await queue_historical_loading(LAST_3_YEARS)
await queue_historical_loading(LAST_5_YEARS)
```

### 3. 混合存储策略

```
热数据（最近 1 年） → SQLite + 内存缓存
冷数据（1 年前）   → Parquet 文件
实时行情         → 内存缓存 (60s TTL)
```

---

## ✅ 验证结果

### 问题 1: Tushare 可用接口的数据是否已储存？
**答案**: ✅ **是的**
- 120 分基础接口数据已完整存储
- 股票信息、日线行情、指数数据全部入库
- 高级接口数据（财务、分钟线等）使用 AkShare 补充

### 问题 2: 数据是否分类储存和加载？
**答案**: ✅ **是的，非常完善**

**分类存储**:
- 按数据类型：stock_info / kline / indicators / chip_data
- 按复权类型：qfq / hfq / none
- 按日期分区：按年分区 Parquet 文件
- 按市场分类：SH / SZ / 指数

**分类加载**:
- 5 级优先级加载策略
- 同步加载最新数据 + 后台补全历史
- 按需加载模式（非启动预加载）
- 智能缓存管理（7 种 TTL）

---

## 📋 关键文件清单

| 文件 | 作用 | 行数 |
|------|------|------|
| `app/storage/sqlite.py` | 数据库模型和操作 | 200 |
| `app/storage/cache.py` | 缓存管理器 | 150 |
| `app/storage/parquet_store.py` | Parquet 文件存储 | 186 |
| `app/services/data_loader.py` | 分层数据加载器 | 300+ |
| `app/services/data_persistence.py` | 数据持久化服务 | 273 |
| `app/utils/tushare_api_registry.py` | Tushare API 注册表 | 200+ |
| `app/adapters/tushare_adapter.py` | Tushare 适配器 | 662 |

---

## 🎓 最佳实践建议

1. **数据查询**: 使用 `priority_load=True` 快速响应
2. **数据保存**: 批量保存，避免单条插入
3. **缓存**: 实时行情用 realtime，K 线用 kline 缓存
4. **数据源**: Tushare 失败自动降级到 AkShare
5. **性能**: 使用复合索引，避免全表扫描

---

## 📄 详细报告

完整报告见：[`DATA_STORAGE_INSPECTION_REPORT.md`](d:\Project\Quant\backend\DATA_STORAGE_INSPECTION_REPORT.md)

---

**总结**: 数据存储逻辑完整、分类清晰、加载策略优化，Tushare 120 分基础数据已完全存储，高级数据通过 AkShare 补充，系统运行正常。
