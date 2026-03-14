# 数据库索引优化方案

## 概述

数据库索引是提升查询性能的关键手段。合理的索引可以减少 90% 以上的查询时间。

## 当前索引配置

### 1. StockInfo 表（股票信息）

**已有索引**:
- ✅ `code`: 唯一索引（主查询字段）
- ✅ `industry`: 普通索引
- ✅ `sector`: 普通索引
- ✅ `area`: 普通索引
- ✅ `idx_stock_industry_market`: 复合索引 (industry, market)
- ✅ `idx_stock_sector_market`: 复合索引 (sector, market)

**查询场景**:
```python
# ✅ 使用 code 索引
SELECT * FROM stock_info WHERE code = '000001'

# ✅ 使用 industry 索引
SELECT * FROM stock_info WHERE industry = '银行'

# ✅ 使用复合索引
SELECT * FROM stock_info WHERE industry = '银行' AND market = 'SH'
```

**优化建议**: 当前索引配置良好，无需额外优化

---

### 2. KLine 表（K 线数据）⭐ 重点优化

**已有索引**:
- ✅ `code`: 普通索引
- ✅ `date`: 普通索引
- ✅ `idx_kline_code_date`: 复合索引 (code, date)
- ✅ `idx_kline_code_adjust`: 复合索引 (code, adjust_type)
- ✅ `u_kline_code_date`: 唯一约束 (code, date, adjust_type)

**查询场景**:
```python
# ✅ 使用复合索引（最高效）
SELECT * FROM kline WHERE code = '000001' AND date >= '20240101'

# ✅ 使用复合索引
SELECT * FROM kline WHERE code = '000001' AND adjust_type = 'qfq'

# ⚠️ 仅使用 date 索引（效率较低）
SELECT * FROM kline WHERE date >= '20240101'
```

**性能分析**:
- 单只股票查询：**优秀**（使用 code 索引）
- 日期范围查询：**良好**（使用 code+date 复合索引）
- 跨股票日期查询：**一般**（仅使用 date 索引）

**优化建议**:

#### 新增索引 1：换手率索引（用于选股）
```python
Index("idx_kline_turnover_rate", "turnover_rate")
```

**使用场景**:
```python
# 查找高换手率股票
SELECT code, date, turnover_rate 
FROM kline 
WHERE turnover_rate > 10.0
```

#### 新增索引 2：成交量索引（用于异动监测）
```python
Index("idx_kline_volume", "volume")
```

**使用场景**:
```python
# 查找放量股票
SELECT code, date, volume 
FROM kline 
WHERE volume > avg_volume * 2
```

#### 新增索引 3：涨跌幅索引（用于行情分析）
```python
# 需要先添加涨跌幅字段
Index("idx_kline_change_pct", "change_pct")
```

**使用场景**:
```python
# 查找涨停股票
SELECT code, date, close 
FROM kline 
WHERE change_pct >= 9.8
```

---

### 3. TechnicalIndicatorDB 表（技术指标）

**已有索引**:
- ✅ `code`: 普通索引
- ✅ `date`: 普通索引
- ✅ `idx_indicator_code_date`: 复合索引 (code, date)
- ✅ `idx_indicator_ma`: 复合索引 (code, ma5, ma10, ma20)
- ✅ `u_indicator_code_date`: 唯一约束 (code, date)

**查询场景**:
```python
# ✅ 使用复合索引
SELECT * FROM technical_indicators 
WHERE code = '000001' AND date >= '20240101'

# ✅ 使用 MA 复合索引
SELECT * FROM technical_indicators 
WHERE code = '000001' AND ma5 > ma10
```

**优化建议**:

#### 新增索引 1：MACD 索引（用于策略选股）
```python
Index("idx_indicator_macd", "code", "macd", "macd_signal")
```

**使用场景**:
```python
# MACD 金叉选股
SELECT code, date, macd, macd_signal
FROM technical_indicators
WHERE macd > macd_signal AND macd_prev <= macd_signal_prev
```

#### 新增索引 2：RSI 索引（用于超买超卖）
```python
Index("idx_indicator_rsi", "code", "rsi6", "rsi12")
```

**使用场景**:
```python
# RSI 超卖选股
SELECT code, date, rsi6
FROM technical_indicators
WHERE rsi6 < 20
```

---

### 4. ChipData 表（筹码数据）

**已有索引**:
- ✅ `code`: 普通索引
- ✅ `date`: 普通索引
- ✅ `u_chip_code_date`: 唯一约束 (code, date)

**查询场景**:
```python
# ✅ 使用 code 索引
SELECT * FROM chip_data WHERE code = '000001'

# ✅ 使用 code+date 复合查询
SELECT * FROM chip_data 
WHERE code = '000001' AND date >= '20240101'
```

**优化建议**:

#### 新增索引 1：股东户数索引（用于筹码集中度分析）
```python
Index("idx_chip_shareholder_count", "shareholder_count")
```

**使用场景**:
```python
# 查找股东户数减少的股票
SELECT code, date, shareholder_count
FROM chip_data
WHERE shareholder_count < prev_count * 0.9
```

#### 新增索引 2：集中度索引（用于筹码峰分析）
```python
Index("idx_chip_concentration", "concentration")
```

**使用场景**:
```python
# 查找筹码高度集中的股票
SELECT code, date, concentration
FROM chip_data
WHERE concentration > 70
```

---

### 5. TradeRecord 表（交易记录）

**已有索引**:
- ✅ `backtest_id`: 普通索引

**查询场景**:
```python
# ✅ 使用 backtest_id 索引
SELECT * FROM trade_record WHERE backtest_id = 'backtest_001'
```

**优化建议**:

#### 新增索引 1：交易日期索引（用于绩效分析）
```python
Index("idx_trade_date", "trade_date")
```

**使用场景**:
```python
# 按日期统计交易
SELECT trade_date, COUNT(*), SUM(amount)
FROM trade_record
WHERE trade_date >= '20240101'
GROUP BY trade_date
```

#### 新增索引 2：股票代码索引（用于持仓分析）
```python
Index("idx_trade_code", "code")
```

**使用场景**:
```python
# 统计某股票的交易
SELECT code, COUNT(*), SUM(quantity)
FROM trade_record
WHERE code = '000001'
GROUP BY code
```

#### 新增索引 3：复合索引（用于回测分析）
```python
Index("idx_trade_backtest_date", "backtest_id", "trade_date")
```

**使用场景**:
```python
# 回测交易时间分布
SELECT * FROM trade_record
WHERE backtest_id = 'backtest_001'
  AND trade_date >= '20240101'
ORDER BY trade_date
```

---

## 索引优化实施

### 方案 1：修改表定义（推荐）

在 `app/storage/sqlite.py` 中添加索引：

```python
class KLine(Base):
    # ... 现有字段 ...
    
    __table_args__ = (
        UniqueConstraint("code", "date", "adjust_type", name="u_kline_code_date"),
        # 现有索引
        Index("idx_kline_code_date", "code", "date"),
        Index("idx_kline_code_adjust", "code", "adjust_type"),
        # 新增索引
        Index("idx_kline_turnover_rate", "turnover_rate"),
        Index("idx_kline_volume", "volume"),
    )
```

### 方案 2：SQL 添加索引（已建表）

对于已存在的表，使用 SQL 添加索引：

```sql
-- 添加换手率索引
CREATE INDEX idx_kline_turnover_rate ON kline(turnover_rate);

-- 添加成交量索引
CREATE INDEX idx_kline_volume ON kline(volume);

-- 添加 MACD 索引
CREATE INDEX idx_indicator_macd ON technical_indicators(code, macd, macd_signal);

-- 添加 RSI 索引
CREATE INDEX idx_indicator_rsi ON technical_indicators(code, rsi6, rsi12);

-- 添加交易日期索引
CREATE INDEX idx_trade_date ON trade_record(trade_date);

-- 添加交易代码索引
CREATE INDEX idx_trade_code ON trade_record(code);

-- 添加交易复合索引
CREATE INDEX idx_trade_backtest_date ON trade_record(backtest_id, trade_date);
```

---

## 索引使用监控

### 1. 查询执行计划

使用 `EXPLAIN` 查看查询是否使用索引：

```python
from sqlalchemy import text

async with get_session() as session:
    result = await session.execute(
        text("EXPLAIN QUERY PLAN SELECT * FROM kline WHERE code = '000001'")
    )
    print(result.fetchall())
```

**输出示例**:
```
(0, 0, 0, 'SEARCH kline USING INDEX idx_kline_code_date (code=?)')
```
✅ 表示使用了索引

### 2. 索引使用统计

```sql
-- SQLite 索引使用统计
SELECT 
    name,
    tbl_name,
    sql
FROM sqlite_master 
WHERE type = 'index'
  AND tbl_name IN ('kline', 'stock_info', 'technical_indicators');
```

---

## 索引优化原则

### 1. 为高频查询创建索引

**应该创建索引的场景**:
- ✅ 主键字段（自动创建）
- ✅ 外键字段
- ✅ WHERE 子句中的字段
- ✅ JOIN 连接字段
- ✅ ORDER BY 排序字段
- ✅ GROUP BY 分组字段
- ✅ 复合查询的多个字段

**不应创建索引的场景**:
- ❌ 表数据量很小（< 1000 条）
- ❌ 很少查询的字段
- ❌ 频繁更新的字段
- ❌ 性别、状态等低基数字段

### 2. 复合索引最左匹配原则

```python
# 复合索引 (code, date, adjust_type)

# ✅ 使用索引
WHERE code = '000001'
WHERE code = '000001' AND date >= '20240101'
WHERE code = '000001' AND date >= '20240101' AND adjust_type = 'qfq'

# ⚠️ 部分使用索引
WHERE date >= '20240101'  # 跳过 code
WHERE adjust_type = 'qfq'  # 跳过 code, date

# ❌ 不使用索引
WHERE date >= '20240101' AND adjust_type = 'qfq'  # 跳过 code
```

### 3. 索引数量控制

**建议**:
- 单表索引数：5-10 个为宜
- 复合索引字段数：2-4 个为宜
- 定期清理无用索引

**索引过多问题**:
- 降低写入性能（每次 INSERT/UPDATE 都要更新索引）
- 占用更多磁盘空间
- 优化器选择困难

---

## 性能提升预期

### KLine 表查询优化

| 查询场景 | 无索引 | 单字段索引 | 复合索引 | 提升倍数 |
|---------|--------|-----------|---------|---------|
| 单只股票查询 | 500ms | 50ms | 10ms | **50 倍** |
| 日期范围查询 | 1000ms | 200ms | 20ms | **50 倍** |
| 多条件查询 | 2000ms | 500ms | 30ms | **67 倍** |
| 换手率选股 | 3000ms | 300ms | - | **10 倍** |

### TechnicalIndicatorDB 表查询优化

| 查询场景 | 无索引 | 有索引 | 提升倍数 |
|---------|--------|--------|---------|
| 指标查询 | 800ms | 50ms | **16 倍** |
| MACD 选股 | 5000ms | 200ms | **25 倍** |
| RSI 选股 | 5000ms | 150ms | **33 倍** |

---

## 实施计划

### 阶段 1：已完成 ✅
- [x] 分析现有索引配置
- [x] 识别性能瓶颈

### 阶段 2：进行中 🔄
- [ ] 添加 KLine 表新索引（turnover_rate, volume）
- [ ] 添加 TechnicalIndicatorDB 表新索引（MACD, RSI）
- [ ] 添加 ChipData 表新索引（concentration）
- [ ] 添加 TradeRecord 表新索引（trade_date, code）

### 阶段 3：验证 ⏳
- [ ] 性能基准测试
- [ ] 索引使用监控
- [ ] 查询执行计划分析

---

## 监控与维护

### 1. 定期分析索引使用情况

```sql
-- 查看索引大小
SELECT 
    name,
    tbl_name,
    pgsize_size(sql) as index_size
FROM sqlite_master 
WHERE type = 'index';
```

### 2. 重建索引（优化碎片）

```sql
-- 重建所有索引
REINDEX;

-- 重建指定索引
REINDEX idx_kline_code_date;
```

### 3. 删除无用索引

```sql
-- 删除索引
DROP INDEX idx_name;
```

---

## 参考资源

1. [SQLite Query Planner](https://www.sqlite.org/queryplanner.html)
2. [SQLite Indexes](https://www.sqlite.org/optoverview.html)
3. [SQLAlchemy Index Documentation](https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.Index)

---

**创建时间**: 2026-03-14  
**状态**: 实施中  
**优先级**: 高  
**预期性能提升**: 10-67 倍
