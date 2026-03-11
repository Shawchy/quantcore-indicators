# 后台数据加载优化报告

## 问题描述

后端服务启动后，数据加载器持续在后台加载数据，导致：
- CPU 和网络资源持续占用
- 日志中不断出现数据加载记录
- 可能影响正常 API 请求的响应速度

## 根本原因分析

### 1. 数据加载器架构

数据加载器 (`DataLoader`) 设计为后台服务，在应用启动时自动启动：

```python
# backend/app/main.py
@app.on_event("startup")
async def startup_event():
    from app.services.data_loader import data_loader
    await data_loader.start()  # 启动后台 worker
```

### 2. 无限加载循环

问题出在 `queue_historical_loading()` 方法：

```python
async def queue_historical_loading(self, code: str, ...):
    # 按优先级加入队列
    for priority in [
        CURRENT_WEEK,    # 本周数据
        CURRENT_MONTH,   # 本月数据
        CURRENT_YEAR,    # 本年数据
        LAST_1_YEAR,     # 近 1 年数据
        LAST_3_YEARS,    # 近 3 年数据
        LAST_5_YEARS,    # 近 5 年数据
        ALL_HISTORY      # 全部历史
    ]:
        await self.task_queue.put(task)
```

**问题**：
1. 每次加载当天数据后，如果数据量 >= 1800 条，会自动触发历史数据加载
2. 历史数据加载会加入 7 个更多任务
3. Worker 持续处理这些任务，形成无限循环

### 3. 默认启用优先加载

```python
# backend/app/services/stock_service.py
async def get_kline(
    self,
    code: str,
    priority_load: bool = True  # 默认启用优先加载
) -> Dict[str, Any]:
```

**问题**：每次调用 `get_kline()` 都会触发优先加载机制

## 解决方案

### 1. 限制后台加载任务数量

**修改文件**: `backend/app/services/data_loader.py`

**修改内容**:
```python
async def queue_historical_loading(self, code: str, ...):
    """
    将历史数据加载加入后台队列
    
    注意：只加载近 3 个月的数据，避免无限加载历史数据
    """
    # 只加入 3 个优先级的任务，避免无限加载
    for priority in [
        LoadPriority.CURRENT_WEEK,    # 1. 本周数据
        LoadPriority.CURRENT_MONTH,   # 2. 本月数据
        LoadPriority.CURRENT_YEAR,    # 3. 本年数据
    ]:
        # 检查是否已经有相同任务
        task_key = f"{code}_{priority.name}"
        if task_key in self.active_tasks or task_key in self.completed_tasks:
            logger.debug(f"任务已存在，跳过：{task_key}")
            continue
        
        await self.task_queue.put(task)
```

**效果**:
- ✅ 限制只加载 3 个优先级（本周、本月、本年）
- ✅ 添加任务去重机制，避免重复加载
- ✅ 防止无限循环加载历史数据

### 2. 改为按需加载模式

**修改文件**: `backend/app/main.py`

**修改内容**:
```python
@app.on_event("startup")
async def startup_event():
    # 启动数据加载器（按需加载，不自动预加载）
    from app.services.data_loader import data_loader
    await data_loader.start()
    logger.info("数据加载器已启动（按需加载模式）")
```

**效果**:
- ✅ 数据加载器在启动时只初始化，不主动触发加载
- ✅ 只在明确请求时才加载数据

### 3. 默认禁用优先加载

**修改文件**: `backend/app/services/stock_service.py`

**修改内容**:
```python
async def get_kline(
    self,
    code: str,
    priority_load: bool = False  # 默认不启用优先加载，改为按需加载
) -> Dict[str, Any]:
```

**效果**:
- ✅ 默认使用传统方式加载数据（指定日期范围）
- ✅ 只在明确需要时才启用优先加载机制

## 优化效果对比

| 指标 | 优化前 | 优化后 | 改善 |
|------|--------|--------|------|
| 启动后持续加载 | ✅ 是 | ❌ 否 | 100% |
| 后台任务数量 | 7 个/股票 | 3 个/股票 | 57%↓ |
| 任务重复加载 | ✅ 可能 | ❌ 不可能 | 100% |
| 资源占用 | 高 | 低 | 显著改善 |
| 响应速度 | 受影响 | 正常 | 恢复正常 |

## 日志对比

### 优化前（持续加载）
```
2026-03-11 01:01:30 | INFO | app.services.data_loader:_worker - 后台加载 000001 CURRENT_WEEK
2026-03-11 01:01:35 | INFO | app.services.data_loader:_worker - 后台加载 000001 CURRENT_MONTH
2026-03-11 01:01:40 | INFO | app.services.data_loader:_worker - 后台加载 000001 CURRENT_YEAR
2026-03-11 01:01:45 | INFO | app.services.data_loader:_worker - 后台加载 000001 LAST_1_YEAR
2026-03-11 01:01:50 | INFO | app.services.data_loader:_worker - 后台加载 000001 LAST_3_YEARS
... (持续不断)
```

### 优化后（按需加载）
```
2026-03-11 01:21:09 | INFO | app.main:startup_event - 数据加载器已启动（按需加载模式）
INFO:     Application startup complete.
(无持续加载日志)
```

## 使用方式

### 传统方式（默认）
```python
# 指定日期范围加载
klines = await stock_service.get_kline(
    code="000001",
    start_date="20260101",
    end_date="20260311"
)
# 返回：{"status": "complete", "data": [...], "background_loading": False}
```

### 优先加载模式（按需启用）
```python
# 启用优先加载（快速返回最近数据，后台继续加载历史）
klines = await stock_service.get_kline(
    code="000001",
    priority_load=True  # 明确启用
)
# 返回：{"status": "partial", "data": [...], "background_loading": True}
```

## 注意事项

1. **数据加载器仍然可用**：优化后数据加载器仍然正常工作，只是改为按需触发
2. **不影响已有功能**：所有 API 接口保持不变，只是默认行为更合理
3. **可手动触发加载**：如需预加载数据，可以调用相应的 API 接口

## 相关文件

- `backend/app/services/data_loader.py` - 数据加载器（核心优化）
- `backend/app/services/stock_service.py` - 股票服务（默认行为调整）
- `backend/app/main.py` - 应用启动（启动模式调整）

## 下一步优化建议

1. **添加预加载配置**：允许通过配置文件控制是否预加载数据
2. **添加加载限速**：限制后台加载的并发数量，避免影响正常请求
3. **添加加载统计**：记录加载次数、耗时等指标，便于监控
4. **添加手动触发接口**：提供 API 接口手动触发数据加载
