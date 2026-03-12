# K 线滑块日期范围问题修复报告

## 📋 问题描述

**用户报告**: K 线图的滑块只能滑到 3 月 2 号，无法查看更早的历史数据。

## 🔍 问题排查过程

### 1. 检查数据库
```bash
最早日期：2026-02-09, 最晚日期：2026-03-12, 总数：18 条
```

**发现**: 数据库中只有从 2 月 9 号到 3 月 12 号的 18 条记录，而不是 3 年的历史数据。

### 2. 检查代码逻辑

**文件**: `backend/app/services/stock_service.py`

```python
async def _load_kline_traditional(...):
    db_klines = await data_persistence.get_klines_from_db(...)
    
    if db_klines and len(db_klines) >= 100:
        klines = db_klines  # 使用数据库数据
    else:
        klines = await data_source_manager.get_kline(...)  # 从数据源获取
```

逻辑正确：当数据库记录少于 100 条时，应该从数据源（Tushare/AkShare）重新获取。

### 3. 测试数据源调用

创建测试脚本验证数据源是否正常工作：

```python
result = await stock_service.get_kline(
    code="000001",
    start_date="2023-03-12",
    end_date="2026-03-12",
    priority_load=False
)
```

**发现错误**: 
```
加载失败：数据源工厂未初始化，请先调用 initialize()
```

### 4. 检查数据源初始化

**文件**: `backend/app/main.py`

```python
# ❌ 问题代码
def init_data_source_sync():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(data_source_manager.initialize())
    except Exception as e:
        logger.error(f"数据源初始化失败：{e}")
    finally:
        loop.close()

# 在后台线程中执行
executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
asyncio.get_event_loop().run_in_executor(executor, init_data_source_sync)
```

**根本原因**: 
- 数据源初始化在后台线程中异步执行
- 当 API 请求到达时，数据源可能还没有初始化完成
- 导致 `data_source_manager.get_kline()` 调用失败
- 最终只能使用数据库中的部分数据（18 条）

## ✅ 修复方案

### 修复 1: 同步初始化数据源

**文件**: `backend/app/main.py` 第 88-99 行

```python
# ✅ 修复：同步初始化数据源，确保 API 请求前数据源已就绪
from app.adapters import data_source_manager
try:
    await data_source_manager.initialize()
    logger.info(f"数据源初始化完成，默认数据源：{data_source_manager._default_source}")
except Exception as e:
    logger.error(f"数据源初始化失败：{e}")
```

**效果**:
- 后端启动时会等待数据源初始化完成
- 确保第一个 API 请求到达时数据源已经就绪
- 可以正常从 Tushare/AkShare 获取历史数据

### 修复 2: 添加详细日志

**文件**: `backend/app/services/stock_service.py`

添加了详细的日志输出，方便调试：
- 缓存命中日志
- 数据库查询结果日志
- 数据源调用日志
- 数据保存日志
- 最终返回数据量日志

### 修复 3: 前端请求 3 年数据

**文件**: `frontend/src/pages/DailyMarket.tsx`

```typescript
// 计算日期范围（近 3 年）
const getEndDate = () => {
  const now = new Date()
  return now.toISOString().split('T')[0]
}

const getStartDate = () => {
  const now = new Date()
  now.setFullYear(now.getFullYear() - 3) // 3 年前
  return now.toISOString().split('T')[0]
}

// 获取 K 线数据
const { data, isLoading, error } = useQuery({
  queryKey: ['kline', currentCode],
  queryFn: () => stockApi.getKline(currentCode, {
    startDate: getStartDate(),
    endDate: getEndDate(),
    adjust: 'qfq',
    priorityLoad: true,
  }),
  enabled: !!currentCode,
})
```

## 📊 修复后的行为

### 后端启动
1. 数据库初始化完成
2. **等待数据源初始化完成**（新增）
3. 数据加载器启动
4. 性能监控启动

### 数据加载流程
1. 前端请求近 3 年数据（2023-03-12 到 2026-03-12）
2. 后端查询数据库（可能只有部分数据）
3. 如果数据库数据不足 100 条，从数据源重新获取
4. 保存到数据库
5. 返回完整数据给前端

### 用户体验
- ✅ 可以看到 3 年的历史数据
- ✅ 滑块可以滑动到 3 年前的日期
- ✅ K 线图显示完整的历史走势
- ✅ 数据表格显示所有历史数据

## 📝 修改文件清单

1. **backend/app/main.py**
   - 第 88-99 行：修改数据源初始化方式为同步
   - 删除后台线程初始化逻辑

2. **backend/app/services/stock_service.py**
   - 第 155-200 行：添加详细日志输出

3. **frontend/src/pages/DailyMarket.tsx**
   - 第 32-51 行：添加日期计算函数，请求 3 年数据

4. **frontend/src/components/DailyKLine.tsx**
   - 第 57 行：修改默认日期范围为 `'all'`

## 🔍 验证步骤

1. **重启后端服务**
   ```bash
   cd d:\Project\Quant\backend
   python -m uvicorn app.main:app --reload
   ```

2. **查看启动日志**
   ```
   数据源初始化完成，默认数据源：tushare
   ```

3. **刷新前端页面**
   - 打开 http://localhost:5173/daily
   - 选择任意股票（如 000001）

4. **检查数据完整性**
   - K 线图应该显示 3 年数据
   - 滑块可以滑动到 2023 年 3 月
   - 数据表格显示约 730 条记录

5. **查看后端日志**
   ```
   数据库查询结果：18 条，日期范围：2023-03-12 - 2026-03-12
   数据库数据不足，从数据源获取：000001, 日期范围：2023-03-12 - 2026-03-12
   数据源返回 730 条 K 线：000001
   保存 730 条 K 线数据到数据库：000001
   返回 730 条 K 线数据：000001
   ```

## ⚠️ 注意事项

1. **启动时间**: 数据源同步初始化可能会增加 2-5 秒的启动时间
2. **首次加载**: 第一次请求某只股票时会从数据源拉取数据，可能需要 3-10 秒
3. **后续请求**: 数据已缓存到数据库，后续请求会非常快
4. **数据量**: 3 年数据约 730 条（250 个交易日/年），在合理范围内

## 🎯 预期效果

修复后，用户应该能够：
- ✅ 看到 2023 年 3 月至今的所有 K 线数据
- ✅ 滑块自由滑动到任意历史日期
- ✅ 通过缩放查看任意时间段的细节
- ✅ 导出完整的历史数据（CSV 格式）

---

**修复时间**: 2026 年 3 月 12 日  
**根本原因**: 数据源在后台线程中异步初始化，API 请求到达时数据源尚未就绪  
**影响范围**: 所有需要获取历史 K 线数据的场景  
**向后兼容**: 是（不影响其他功能）
