# K 线图日期问题排查报告

## 📋 问题描述

用户反馈：**股票详情中 K 线图显示的是 2023 年数据，而不是最新历史数据**

**可能原因**:
1. 前端日期计算错误（3 年前 → 2023 年）
2. 后端日期格式转换错误
3. 数据源返回的日期不正确

---

## 🔍 问题排查

### 1️⃣ 前端日期计算

**文件**: `frontend/src/pages/DailyMarket.tsx`

**日期计算逻辑**:
```typescript
const startDate = getStartDate(period)
const endDate = getEndDate(period)

function getStartDate(period: string): string {
  const end = new Date()
  const start = new Date()
  
  switch (period) {
    case '1Y':
      start.setFullYear(end.getFullYear() - 1)
      break
    case '3Y':
      start.setFullYear(end.getFullYear() - 3)  // ← 3 年前
      break
    case '5Y':
      start.setFullYear(end.getFullYear() - 5)
      break
    case 'ALL':
      start.setFullYear(1990)
      break
  }
  
  return formatDateTime(start)  // 格式：YYYY-MM-DD
}
```

**分析**:
- 当前日期：2026-03-27
- 3 年前日期：2023-03-27 ✅ 计算正确
- **结论**: 前端日期计算没有问题

---

### 2️⃣ 后端日期处理

#### EFinance 适配器

**文件**: `app/adapters/efinance_adapter.py`

**日期处理逻辑**:
```python
async def get_kline(self, code, start_date, end_date, ...):
    # 格式化日期
    beg = start_date.replace('-', '') if start_date else '19000101'
    if len(beg) == 8 and '-' not in beg:
        pass  # 已经是 YYYYMMDD 格式
    elif len(beg) == 10:
        beg = beg.replace('-', '')
    
    end = end_date.replace('-', '') if end_date else '20500101'
    # ... 同样处理
    
    # 获取 K 线数据
    df = ef.stock.get_quote_history(code.zfill(6), beg=beg, end=end, ...)
```

**分析**:
- 输入：`2023-03-27` → 输出：`20230327` ✅ 格式正确
- 输入：`2026-03-27` → 输出：`20260327` ✅ 格式正确
- **结论**: 日期格式转换正确

#### AkShare 适配器

**文件**: `app/adapters/akshare_adapter.py`

**日期处理逻辑**:
```python
async def get_kline(self, code, start_date, end_date, ...):
    # 处理日期格式
    if start_date:
        start_date = start_date.replace('-', '') if '-' in start_date else start_date
    else:
        start_date = '19900101'
    
    if end_date:
        end_date = end_date.replace('-', '') if '-' in end_date else end_date
    else:
        end_date = datetime.now().strftime('%Y%m%d')
    
    # 获取 K 线数据
    df = ak.stock_zh_a_hist(
        symbol=code,
        period="daily",
        start_date=start_date,
        end_date=end_date
    )
```

**分析**:
- 输入：`2023-03-27` → 输出：`20230327` ✅ 格式正确
- 输入：`2026-03-27` → 输出：`20260327` ✅ 格式正确
- **结论**: 日期格式转换正确

---

### 3️⃣ 测试验证

**测试代码**:
```python
from datetime import datetime

# 测试前端传入的日期范围
end_date = datetime.now()
start_date = end_date.replace(year=end_date.year - 3)

end_date_str = end_date.strftime('%Y-%m-%d')  # 2026-03-27
start_date_str = start_date.strftime('%Y-%m-%d')  # 2023-03-27

# 调用数据源
klines = await adapter.get_kline(
    code="000001",
    start_date=start_date_str,  # 2023-03-27
    end_date=end_date_str       # 2026-03-27
)
```

**预期结果**:
- 应该返回 2023-03-27 到 2026-03-27 的 K 线数据
- 最新日期应该是 2026-03-27（或最近交易日）

**实际测试结果**:
```
【1】测试 EFinance 数据源...
❌ 错误：name 'period' is not defined

【2】测试 AkShare 数据源...
❌ 错误：'str' object cannot be interpreted as an integer
```

**发现问题**:
1. EFinance 适配器有 `period` 未定义的 bug
2. AkShare 适配器有日期类型转换的 bug

---

## 🔧 发现的 Bug

### Bug 1: EFinance 适配器 - `period` 未定义

**位置**: `app/adapters/efinance_adapter.py`  
**错误**: `name 'period' is not defined`

**可能代码**:
```python
# 某处使用了未定义的 period 变量
if period == 'daily':
    # ...
```

**修复建议**:
```python
# 应该使用 klt 参数判断周期
if klt == 101:  # 日线
    # ...
elif klt == 102:  # 周线
    # ...
```

---

### Bug 2: AkShare 适配器 - 日期类型错误

**位置**: `app/adapters/akshare_adapter.py:371`  
**错误**: `'str' object cannot be interpreted as an integer`

**可能代码**:
```python
df = ak.stock_zh_a_hist(
    symbol=code,
    period="daily",
    start_date=start_date,  # 字符串 '20230327'
    end_date=end_date       # 字符串 '20260327'
)
```

**问题**: AkShare 可能期望整数类型的日期

**修复建议**:
```python
# 尝试不使用分隔符的日期格式
df = ak.stock_zh_a_hist(
    symbol=code,
    period="daily",
    start_date=20230327,  # 整数
    end_date=20260327     # 整数
)
```

---

## 💡 根本原因分析

### 用户看到的 K 线图是 2023 年数据的可能原因：

1. **数据源只返回了部分数据**
   - 可能由于网络问题
   - 可能由于 API 限流
   - 可能由于缓存问题

2. **前端只显示了部分数据**
   - 可能前端有数据量限制（如只显示前 100 条）
   - 可能前端图表库渲染问题

3. **日期范围计算错误**
   - ✅ 前端计算正确（2023-03-27 到 2026-03-27）
   - ✅ 后端格式转换正确
   - ❌ 但数据源可能没有正确返回最新数据

4. **缓存问题**
   - 可能缓存了旧的查询结果
   - 缓存时间过长

---

## ✅ 解决方案

### 1. 修复 EFinance 适配器 Bug

**查找并修复 `period` 未定义的问题**：

```python
# 在 app/adapters/efinance_adapter.py 中
# 找到使用 period 的地方并修复

# 错误代码：
if period == 'daily':
    klt = 101

# 修复后：
if klt == 101:  # 日线
    pass
```

### 2. 修复 AkShare 适配器 Bug

**修改日期类型为整数**：

```python
# 在 app/adapters/akshare_adapter.py 中

# 错误代码：
start_date = start_date.replace('-', '')  # 返回字符串
df = ak.stock_zh_a_hist(
    symbol=code,
    start_date=start_date,  # 字符串
    end_date=end_date       # 字符串
)

# 修复后：
start_date_int = int(start_date.replace('-', ''))
end_date_int = int(end_date.replace('-', ''))
df = ak.stock_zh_a_hist(
    symbol=code,
    start_date=start_date_int,  # 整数
    end_date=end_date_int       # 整数
)
```

### 3. 优化日期范围计算

**在前端添加调试日志**：

```typescript
console.log('日期范围:', {
  period,
  startDate,
  endDate,
  startTimestamp: new Date(startDate).getTime(),
  endTimestamp: new Date(endDate).getTime()
})
```

### 4. 检查数据源返回

**在后端添加调试日志**：

```python
logger.info(f"获取 K 线数据：{code}")
logger.info(f"日期范围：{start_date} 到 {end_date}")
logger.info(f"返回数据条数：{len(klines)}")
if klines:
    logger.info(f"最早日期：{klines[0].date}")
    logger.info(f"最新日期：{klines[-1].date}")
```

### 5. 清除缓存

**清除旧缓存数据**：

```bash
# 删除缓存目录
rm -rf backend/data/cache/*
# 或重启服务
```

---

## 📝 总结

### ✅ 已确认

1. ✅ 前端日期计算正确（3 年前 = 2023 年）
2. ✅ 后端日期格式转换正确
3. ❌ EFinance 适配器有 `period` 未定义的 bug
4. ❌ AkShare 适配器有日期类型转换的 bug

### 🔧 待修复

1. 🔧 修复 EFinance 适配器的 `period` 未定义问题
2. 🔧 修复 AkShare 适配器的日期类型问题
3. 🔧 添加详细的调试日志
4. 🔧 测试数据源返回的最新日期

### 📌 建议

1. **优先修复 Bug** - 先修复两个数据源的 bug
2. **添加日志** - 在关键位置添加日志便于排查
3. **测试验证** - 修复后重新测试日期是否正确
4. **检查缓存** - 确保不是缓存导致的旧数据

---

**排查日期**: 2026-03-27  
**影响范围**: 
- `app/adapters/efinance_adapter.py` (Bug: period 未定义)
- `app/adapters/akshare_adapter.py` (Bug: 日期类型错误)

**状态**: 🔍 待修复
