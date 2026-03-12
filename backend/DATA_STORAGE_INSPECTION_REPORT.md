# 后端数据存储逻辑检查报告

**检查时间**: 2026-03-12 18:15  
**检查范围**: 数据库模型、存储服务、数据加载器、Tushare 集成  
**报告状态**: ✅ 完成

---

## 📊 一、数据库模型和表结构

### 1.1 数据库配置

| 配置项 | 值 |
|--------|-----|
| **数据库类型** | SQLite (异步 AioSQLite) |
| **ORM 框架** | SQLAlchemy 2.0 (异步) |
| **数据库文件** | `d:\Project\Quant\backend\data\sqlite\quant.db` |
| **数据目录** | `d:\Project\Quant\backend\data\` |

### 1.2 数据库表结构列表

系统共有 **9 张表**，覆盖股票、行情、指标、筹码等核心数据：

| 序号 | 表名 | 用途 | 字段数 | 索引/约束 | 存储内容 |
|------|------|------|--------|----------|---------|
| 1 | **stock_info** | 股票基本信息 | 11 | code 唯一索引，industry/sector/market 复合索引 | 5000+ 只股票基础信息 |
| 2 | **kline** | K 线行情数据 | 11 | (code, date, adjust_type) 唯一约束，3 个复合索引 | 日线/指数线数据 |
| 3 | **technical_indicators** | 技术指标数据 | 13 | (code, date) 唯一约束，MA 复合索引 | MA/RSI/MACD 指标 |
| 4 | **watchlist** | 用户自选股 | 5 | code 唯一约束 | 用户收藏股票列表 |
| 5 | **chip_data** | 筹码股东数据 | 7 | (code, date) 唯一约束 | 股东人数、筹码集中度 |
| 6 | **sector_info** | 板块信息 | 7 | code 唯一索引 | 行业/概念板块信息 |
| 7 | **strategy** | 策略配置 | 8 | strategy_id 唯一约束 | 量化策略配置 |
| 8 | **backtest_record** | 回测记录 | 12 | backtest_id 唯一约束 | 回测结果记录 |
| 9 | **trade_record** | 交易记录 | 10 | backtest_id 索引 | 回测交易明细 |

### 1.3 核心表详细结构

#### **stock_info (股票信息表)**
```python
字段列表:
- id: 主键 (自增)
- code: 股票代码 (唯一索引，VARCHAR(10))
- name: 股票名称 (VARCHAR(50))
- market: 所属市场 (SH/SZ)
- industry: 行业 (索引，VARCHAR(50))
- sector: 板块 (索引，VARCHAR(50))
- area: 地区 (索引，VARCHAR(50))
- list_date: 上市日期 (VARCHAR(20))
- total_shares: 总股本 (FLOAT)
- float_shares: 流通股本 (FLOAT)
- updated_at: 更新时间 (DATETIME)

复合索引:
- idx_stock_industry_market: (industry, market)
- idx_stock_sector_market: (sector, market)
```

#### **kline (K 线数据表)**
```python
字段列表:
- id: 主键 (自增)
- code: 股票代码 (索引，VARCHAR(10))
- date: 交易日期 (索引，VARCHAR(20))
- open: 开盘价 (FLOAT)
- high: 最高价 (FLOAT)
- low: 最低价 (FLOAT)
- close: 收盘价 (FLOAT)
- volume: 成交量 (FLOAT)
- amount: 成交额 (FLOAT)
- turnover_rate: 换手率 (FLOAT)
- adjust_type: 复权类型 (qfq/hfq/none, VARCHAR(10))

约束:
- u_kline_code_date: UNIQUE(code, date, adjust_type)

复合索引:
- idx_kline_code_date: (code, date)
- idx_kline_code_adjust: (code, adjust_type)
```

#### **technical_indicators (技术指标表)**
```python
字段列表:
- id: 主键 (自增)
- code: 股票代码 (索引，VARCHAR(10))
- date: 交易日期 (索引，VARCHAR(20))
- ma5/ma10/ma20/ma60: 均线系列 (FLOAT)
- rsi6/rsi12/rsi24: RSI 指标 (FLOAT)
- macd/macd_signal/macd_hist: MACD 指标 (FLOAT)

约束:
- u_indicator_code_date: UNIQUE(code, date)

复合索引:
- idx_indicator_code_date: (code, date)
- idx_indicator_ma: (code, ma5, ma10, ma20)
```

---

## 📁 二、数据存储目录结构

### 2.1 完整目录结构

```
d:\Project\Quant\backend\
├── data/
│   ├── sqlite/
│   │   └── quant.db                    # SQLite 数据库文件 (~10-100MB)
│   ├── parquet/
│   │   ├── kline/                      # K 线数据 Parquet 文件
│   │   │   ├── 000001/
│   │   │   │   ├── 2023.parquet
│   │   │   │   ├── 2024.parquet
│   │   │   │   └── 2025.parquet
│   │   │   ├── 000002/
│   │   │   │   └── ...
│   │   │   └── {code}_{adjust}.parquet # 扁平化存储（兼容旧格式）
│   │   ├── indicators/
│   │   │   └── {code}.parquet          # 技术指标数据
│   │   ├── chip/
│   │   │   └── {code}.parquet          # 筹码数据
│   │   └── backtest/
│   │       ├── {backtest_id}.parquet   # 回测结果
│   │       ├── {backtest_id}.trades.parquet
│   │       └── {backtest_id}.equity.parquet
│   └── trading_days_cache.json         # 交易日历缓存 (24 小时 TTL)
│
└── app/
    ├── storage/
    │   ├── sqlite.py                   # SQLite 数据库操作 (200 行)
    │   ├── cache.py                    # 缓存管理器 (AsyncLRUCache)
    │   └── parquet_store.py            # Parquet 文件存储 (186 行)
    └── services/
        ├── data_loader.py              # 分层数据加载器
        ├── data_persistence.py         # 数据持久化服务 (273 行)
        ├── stock_service.py            # 股票服务（业务逻辑）
        └── sector_service.py           # 板块服务
```

### 2.2 存储策略

| 数据类型 | 存储位置 | 存储格式 | 说明 |
|---------|---------|---------|------|
| **股票基本信息** | SQLite (stock_info) | 关系型表 | 5000+ 只股票，低频更新 |
| **K 线数据** | SQLite + Parquet | 混合存储 | 热数据在 DB，冷数据在 Parquet |
| **技术指标** | SQLite + Parquet | 混合存储 | 与 K 线数据关联 |
| **筹码数据** | SQLite + Parquet | 混合存储 | 低频更新 |
| **回测结果** | Parquet | 列式存储 | 大数据量，适合分析 |
| **交易日历** | JSON 文件 | 本地缓存 | 24 小时 TTL |

---

## 🔄 三、数据加载策略

### 3.1 分层加载优先级机制

系统实现了 **智能分层数据加载策略**，通过 [`DataLoader`](d:\Project\Quant\backend\app\services\data_loader.py) 实现：

| 优先级 | 枚举值 | 日期范围 | 加载方式 | 用途 | 预计数据量 |
|--------|--------|---------|---------|------|-----------|
| **1** | CURRENT_MONTH | 本月 1 日至今 | 同步阻塞 | 日常看盘 | ~20 条 |
| **2** | CURRENT_YEAR | 本年 1 月 1 日至今 | 同步阻塞 | 年度分析 | ~250 条 |
| **3** | LAST_3_YEARS | 最近 3 年 | 后台异步 | 中期回测 | ~750 条 |
| **4** | LAST_5_YEARS | 最近 5 年 | 后台异步 | 长期回测 | ~1250 条 |
| **5** | ALL_HISTORY | 全部历史 | 后台异步 | 完整回测 | 2000+ 条 |

### 3.2 加载流程图

```
用户请求 (GET /api/v1/stock/kline/daily/000001)
    ↓
[同步阶段] 优先加载本月数据 (20 条，<100ms)
    ↓
返回响应 (status: "partial", background_loading: true)
    ↓
[后台队列] 自动加入本年数据加载任务
    ↓
[后台队列] 自动加入近 3 年数据加载任务
    ↓
[后台队列] 自动加入近 5 年数据加载任务
    ↓
[后台队列] 自动加入全部历史数据加载任务
```

### 3.3 加载模式对比

| 模式 | 启动加载 | 按需加载 | 当前使用 |
|------|---------|---------|---------|
| **策略** | 启动时预加载所有热门股票 | 用户请求时才加载 | ✅ 按需加载 |
| **优点** | 首次访问快 | 节省资源，按需分配 | - |
| **缺点** | 启动慢，占用资源 | 首次访问稍慢 | - |
| **实现** | 未使用 | 默认启用 | ✅ |

### 3.4 后台工作协程

后台加载器 (`DataLoader._worker()`) 持续运行：

```python
async def _worker(self):
    """后台加载工作协程"""
    while self._running:
        try:
            # 从队列获取任务
            task = await self.task_queue.get()
            
            # 按优先级顺序处理
            if task.priority == LoadPriority.LAST_3_YEARS:
                # 加载 3 年数据
                klines = await data_source.get_kline(...)
                await data_persistence.save_klines(...)
            
            elif task.priority == LoadPriority.LAST_5_YEARS:
                # 加载 5 年数据
                ...
            
            elif task.priority == LoadPriority.ALL_HISTORY:
                # 加载全部历史
                ...
            
        except Exception as e:
            logger.error(f"后台加载失败：{e}")
```

---

## 💾 四、缓存机制和 TTL 配置

### 4.1 多层缓存架构

系统实现了 **4 层缓存体系**：

```
┌─────────────────────────────────────┐
│ 第 1 层：内存 LRU 缓存 (AsyncLRUCache) │
│ - 容量：200-500 条                   │
│ - TTL: 60-3600 秒                    │
│ - 用途：实时行情、热点数据           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ 第 2 层：SQLite 数据库                 │
│ - 容量：无限                         │
│ - TTL: 永久（手动更新）              │
│ - 用途：历史 K 线、股票信息           │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ 第 3 层：Parquet 文件存储              │
│ - 容量：磁盘限制                     │
│ - TTL: 永久（定期清理）              │
│ - 用途：冷数据、回测结果             │
└─────────────────────────────────────┘
              ↓
┌─────────────────────────────────────┐
│ 第 4 层：本地 JSON 缓存                │
│ - 容量：小文件                       │
│ - TTL: 24 小时                       │
│ - 用途：交易日历、配置信息           │
└─────────────────────────────────────┘
```

### 4.2 内存缓存配置

| 缓存类型 | 容量 | TTL | 用途 | 命中率统计 |
|---------|------|-----|------|-----------|
| **realtime** | 500 | 60 秒 | 实时行情 | hits/misses/hit_rate |
| **kline** | 200 | 300 秒 | K 线数据 | 5 分钟过期 |
| **indicators** | 200 | 300 秒 | 技术指标 | 5 分钟过期 |
| **sector** | 100 | 300 秒 | 板块数据 | 5 分钟过期 |
| **chip** | 200 | 600 秒 | 筹码数据 | 10 分钟过期 |
| **screener** | 50 | 120 秒 | 选股结果 | 2 分钟过期 |
| **backtest** | 20 | 3600 秒 | 回测结果 | 1 小时过期 |

### 4.3 缓存命中率统计

缓存管理器提供详细的命中率统计：

```python
{
    "size": 45,                    # 当前缓存数量
    "max_size": 200,               # 最大容量
    "ttl": 300,                    # 过期时间（秒）
    "hits": 1234,                  # 命中次数
    "misses": 56,                  # 未命中次数
    "evictions": 12,               # 淘汰次数
    "hit_rate": "95.67%"           # 命中率百分比
}
```

---

## 📡 五、Tushare 可用接口的数据存储情况

### 5.1 Tushare API 分组和存储映射

根据 [`tushare_api_registry.py`](d:\Project\Quant\backend\app\utils\tushare_api_registry.py) 和 [`tushare_adapter.py`](d:\Project\Quant\backend\app\adapters\tushare_adapter.py):

| 分组 | 所需积分 | 接口数量 | 存储状态 | 存储表 | 实现状态 |
|------|---------|---------|---------|--------|---------|
| **BASIC** | 120 | 4 | ✅ 已存储 | stock_info | ✅ 完整实现 |
| **KLINE** | 120 | 4 | ✅ 已存储 | kline + Parquet | ✅ 完整实现 |
| **INDEX** | 120 | 2 | ✅ 已存储 | kline (指数代码) | ✅ 完整实现 |
| **FUND** | 120 | 3 | ⚠️ 部分存储 | 支持但未完全实现 | 🔄 部分实现 |
| **MACRO** | 120 | 4 | ⚠️ 部分存储 | 支持但未完全实现 | 🔄 部分实现 |
| **TRADING** | 200 | 4 | ⚠️ 部分存储 | 支持但未完全实现 | 🔄 部分实现 |
| **FINANCE** | 800 | 6 | ❌ 未存储 | 需要更高积分 | ❌ 未实现 |
| **WEEKLY** | 2000 | 2 | ❌ 未存储 | 需要更高积分 | ❌ 未实现 |
| **INTRADAY** | 5000 | 3 | ❌ 未存储 | 需要更高积分 | ❌ 未实现 |
| **MONEYFLOW** | 5000 | 2 | ❌ 未存储 | 需要更高积分 | ❌ 未实现 |
| **CHIP** | 10000 | 3 | ⚠️ 部分存储 | chip_data (结构已建) | 🔄 部分实现 |
| **LEVEL2** | 10000 | 1 | ❌ 未存储 | 需要更高积分 | ❌ 未实现 |
| **FORECAST** | 10000 | 2 | ❌ 未存储 | 需要更高积分 | ❌ 未实现 |

### 5.2 已完整存储的数据（120 分基础）

✅ **以下数据已完全存储并可正常使用**:

| 接口名称 | API 代码 | 存储位置 | 更新频率 | 数据量 |
|---------|---------|---------|---------|-------|
| 股票基本信息 | stock_basic | stock_info 表 | 低频 | 5000+ 条 |
| 日线行情 | daily | kline 表 + Parquet | 每日 | 每只股票 2000+ 条 |
| 复权因子 | adj_factor | 整合到 kline 表 | 每日 | 每只股票 2000+ 条 |
| 指数基本信息 | index_basic | stock_info 表 | 低频 | 100+ 条 |
| 指数日线 | index_daily | kline 表 | 每日 | 每指数 2000+ 条 |
| 交易日历 | trade_cal | JSON 缓存 | 每年 | 365 条/年 |

### 5.3 需要更高级权限的数据

❌ **以下数据未实现存储** (需要更高级 Tushare 积分):

| 数据类型 | 所需积分 | 原因 | 替代方案 |
|---------|---------|------|---------|
| 财务数据 (income/balancesheet/cashflow) | 800 | 积分不足 | 使用 AkShare |
| 周线/月线数据 (weekly/monthly) | 2000 | 积分不足 | 使用 AkShare |
| 分钟级数据 (intraday/bar) | 5000 | 积分不足 | 使用 AkShare |
| 资金流向 (moneyflow) | 5000 | 积分不足 | 使用 AkShare |
| 筹码分布 (chip_distribution) | 10000 | 积分不足 | 使用 AkShare |
| Level-2 数据 | 10000 | 积分不足 | 暂不支持 |
| 业绩预告/快报 (forecast/express) | 2000 | 积分不足 | 使用 AkShare |

---

## 📂 六、数据分类存储和加载机制

### 6.1 数据分类存储

**按数据类型分类**:
```
SQLite 数据库 (quant.db)
├── stock_info        - 股票基础信息 (5000+ 只)
├── kline            - K 线行情数据 (日线)
├── technical_indicators - 技术指标 (MA/RSI/MACD)
├── chip_data        - 筹码股东数据
├── sector_info      - 板块信息
└── watchlist        - 用户自选股

Parquet 文件 (data/parquet/)
├── kline/
│   ├── {code}/
│   │   ├── 2023.parquet    - 按年分区
│   │   ├── 2024.parquet
│   │   └── 2025.parquet
│   └── {code}_{adjust}.parquet  - 扁平化存储（兼容）
├── indicators/
│   └── {code}.parquet    - 技术指标
├── chip/
│   └── {code}.parquet    - 筹码数据
└── backtest/
    ├── {backtest_id}.parquet
    ├── {backtest_id}.trades.parquet
    └── {backtest_id}.equity.parquet
```

**按复权类型分类**:
- `qfq` (前复权) - ✅ 默认存储
- `hfq` (后复权) - ⚠️ 支持但未默认
- `none` (不复权) - ⚠️ 支持但未默认

**按市场分类**:
- `SH` (上海) - 600/601/603 开头
- `SZ` (深圳) - 000/001/002/003 开头
- 指数 - 000001/399001/399006 等

### 6.2 数据加载机制详解

**1. 优先加载模式** ([`stock_service.py`](d:\Project\Quant\backend\app\services\stock_service.py)):

```python
async def get_kline(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    priority_load: bool = True  # 默认启用优先加载
) -> Dict[str, Any]:
    
    if priority_load:
        # 优先加载本月数据
        progress = await data_loader.load_kline_priority(
            code=code,
            priority=LoadPriority.CURRENT_MONTH
        )
        
        # 后台自动加入历史数据加载队列
        return {
            "status": "partial",
            "data": progress.data,
            "background_loading": True,
            "coverage": progress.coverage
        }
    else:
        # 传统模式：加载指定日期范围
        klines = await _load_kline_traditional(
            code=code,
            start_date=start_date,
            end_date=end_date
        )
        return {
            "status": "complete",
            "data": klines
        }
```

**2. 后台工作协程**:
- 持续监听任务队列 (`asyncio.Queue`)
- 按优先级顺序处理 (3 年→5 年→全部历史)
- 自动保存到 SQLite 和 Parquet
- 失败重试机制（指数退避）

**3. 数据查询优化**:
- 批量查询已存在记录（一次查询代替 N 次）
- 复合索引加速查询（code+date, code+adjust_type）
- Parquet 文件支持日期范围过滤
- 增量更新（只插入新数据）

### 6.3 数据持久化优化

[`DataPersistence`](d:\Project\Quant\backend\app\services\data_persistence.py) 实现了高性能数据保存：

```python
async def save_klines(
    self,
    code: str,
    klines: List[KLineData],
    adjust: str = "qfq"
) -> int:
    """
    批量保存 K 线数据（优化版）
    
    优化点：
    1. 批量查询已存在记录（一次查询代替 N 次查询）
    2. 批量插入（add_all 代替逐条 add）
    3. 一次 commit（减少事务开销）
    
    性能提升：10-50 倍
    """
    
    async with get_session() as session:
        # 1. 批量查询已存在的记录
        dates = [k.date for k in klines]
        existing_query = await session.execute(
            select(KLineDB.date).where(
                and_(
                    KLineDB.code == code,
                    KLineDB.date.in_(dates),
                    KLineDB.adjust_type == adjust
                )
            )
        )
        existing_dates = set(existing_query.scalars().all())
        
        # 2. 过滤出需要插入的记录
        to_insert = [
            KLineDB(...)
            for k in klines if k.date not in existing_dates
        ]
        
        # 3. 批量插入（一次 commit）
        if to_insert:
            session.add_all(to_insert)
            await session.commit()
            
            # 4. 归档到 Parquet
            await self._save_to_parquet(code, to_insert, adjust)
            
            return len(to_insert)
    
    return 0
```

---

## 🎯 七、总结

### ✅ 已实现的功能

1. **完整的数据库模型**: 9 张表覆盖股票、K 线、指标、筹码、回测等核心数据
2. **分层存储架构**: SQLite(热数据) + Parquet(冷数据) + 内存缓存 (LRU)
3. **智能加载策略**: 优先加载最新数据，后台补全历史，支持 5 个优先级
4. **多级缓存系统**: 7 种缓存类型，TTL 从 60 秒到 3600 秒可配置
5. **数据分类存储**: 按类型、复权方式、日期分区存储
6. **高性能持久化**: 批量查询 + 批量插入，性能提升 10-50 倍
7. **Tushare 集成**: 120 分基础数据已完整存储，高级数据支持降级

### ⚠️ 待完善的功能

1. **Tushare 高级接口**: 需要更高级积分才能完整实现财务、分钟级等数据
   - 当前使用 AkShare 作为补充
   - 建议：获取 2000 积分以支持周月线、财务数据

2. **预加载机制**: 目前仅按需加载，可添加盘前预加载热门股票
   - 建议：每日开盘前预加载 TOP50 活跃股票

3. **数据更新策略**: 增量更新已实现，但定期全量校验未实现
   - 建议：每周执行一次全量校验，确保数据一致性

4. **分布式缓存**: 当前使用内存缓存，多实例部署需 Redis
   - 建议：生产环境使用 Redis 作为共享缓存

5. **数据清理机制**: Parquet 支持定期清理，但未自动执行
   - 建议：添加定时任务，清理 3 年前的按年分区文件

### 📊 数据存储统计

| 统计项 | 数值 | 说明 |
|--------|------|------|
| **数据库文件** | `data/sqlite/quant.db` | ~10-100MB (根据数据量) |
| **Parquet 文件** | `data/parquet/` | 按股票代码分目录 |
| **缓存配置** | 7 种类型 | TTL: 60s - 3600s |
| **数据加载** | 5 个优先级 | 同步 + 后台异步 |
| **Tushare 接口** | 11 个可用 | 120 分基础权限 |
| **AkShare 补充** | 全接口可用 | 免费数据源 |

### 🎓 最佳实践

1. **数据查询**: 优先使用 `priority_load=True`，快速返回最新数据
2. **数据保存**: 使用批量保存，避免单条插入
3. **缓存使用**: 实时行情用 realtime 缓存，K 线用 kline 缓存
4. **数据源切换**: Tushare 失败自动降级到 AkShare
5. **性能优化**: 使用复合索引，避免全表扫描

---

## 📋 八、验证清单

### 数据库模型
- [x] 9 张表已创建
- [x] 索引和约束已配置
- [x] 复合索引优化查询

### 存储服务
- [x] SQLite 异步操作
- [x] Parquet 文件存储
- [x] 批量保存优化

### 数据加载
- [x] 分层加载策略
- [x] 后台工作协程
- [x] 优先加载模式

### 缓存系统
- [x] 7 种缓存类型
- [x] TTL 配置
- [x] 命中率统计

### Tushare 集成
- [x] 120 分基础数据已存储
- [ ] 2000 分进阶数据（需要更高积分）
- [x] 降级到 AkShare

---

**报告生成完成**  
**检查者**: AI Assistant  
**状态**: ✅ 数据存储逻辑完整，分类清晰，加载策略优化
