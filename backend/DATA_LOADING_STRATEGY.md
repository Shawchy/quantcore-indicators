# 分层数据加载功能说明

## 📊 功能概述

分层数据加载功能实现了智能的数据加载策略，优先加载最新数据，然后在后台逐步加载历史数据，确保用户能够快速获取到最新的行情数据。

## 🎯 加载策略

### 优先级顺序

系统按照以下优先级加载数据：

| 优先级 | 范围 | 说明 | 数据量估算 |
|--------|------|------|-----------|
| **1. 当天数据** | 今日 | 最新交易日数据 | ~1 条 |
| **2. 本周数据** | 最近 7 天 | 最近 5 个交易日 | ~5 条 |
| **3. 本月数据** | 本月至今 | 本月所有交易日 | ~20 条 |
| **4. 本年数据** | 年初至今 | 本年度所有交易日 | ~250 条 |
| **5. 近 1 年** | 最近 365 天 | 过去一年的完整数据 | ~250 条 |
| **6. 近 3 年** | 最近 3 年 | 中期历史数据 | ~750 条 |
| **7. 近 5 年** | 最近 5 年 | 长期历史数据 | ~1250 条 |
| **8. 全部历史** | 上市至今 | 完整历史数据 | 视情况而定 |

### 加载流程

```
用户请求
    ↓
[同步加载] 当天数据 → 立即返回
    ↓
[后台队列] 本周数据
    ↓
[后台队列] 本月数据
    ↓
[后台队列] 本年数据
    ↓
[后台队列] 近 1 年数据
    ↓
[后台队列] 近 3 年数据
    ↓
[后台队列] 近 5 年数据
    ↓
[后台队列] 全部历史数据
```

## 🔧 技术实现

### 1. 加载优先级枚举

```python
class LoadPriority(Enum):
    """加载优先级"""
    TODAY = 1           # 当天数据
    CURRENT_WEEK = 2    # 本周数据
    CURRENT_MONTH = 3   # 本月数据
    CURRENT_YEAR = 4    # 本年数据
    LAST_1_YEAR = 5     # 近 1 年
    LAST_3_YEARS = 6    # 近 3 年
    LAST_5_YEARS = 7    # 近 5 年
    ALL_HISTORY = 8     # 全部历史
```

### 2. 核心方法

#### `load_kline_priority()` - 分层加载 K 线数据

```python
async def load_kline_priority(
    code: str,
    data_source_manager,
    data_persistence,
    priority: LoadPriority = LoadPriority.TODAY
) -> LoadProgress
```

**功能**：
- 根据优先级加载指定范围的数据
- 立即返回当前优先级的数据
- 自动判断是否需要继续加载历史数据
- 如果数据量接近上限（1800 条），自动触发后台加载

**返回值**：
```python
LoadProgress(
    code="000001",
    status="partial",  # 部分加载完成
    data=[...],        # K 线数据列表
    coverage={
        "start_date": "20260310",
        "end_date": "20260310",
        "loaded": 1,
        "total_expected": 250
    },
    background_loading=True,
    total_expected=250,
    loaded=1
)
```

#### `queue_historical_loading()` - 后台队列加载

```python
async def queue_historical_loading(
    code: str,
    data_source_manager,
    data_persistence
)
```

**功能**：
- 将历史数据加载任务加入后台队列
- 按优先级顺序加载：近 1 年 → 近 3 年 → 近 5 年 → 全部历史
- 后台异步执行，不阻塞用户请求

#### `_worker()` - 后台工作协程

```python
async def _worker()
```

**功能**：
- 持续监听任务队列
- 按优先级处理加载任务
- 自动保存数据到数据库
- 记录加载日志

## 📝 使用示例

### 基础用法

```python
from app.services.data_loader import data_loader, LoadPriority
from app.adapters import data_source_manager
from app.services.data_persistence import data_persistence

# 1. 优先加载当天数据（立即返回）
progress = await data_loader.load_kline_priority(
    code="000001",
    data_source_manager=data_source_manager,
    data_persistence=data_persistence,
    priority=LoadPriority.TODAY
)

print(f"已加载 {progress.loaded} 条数据")
print(f"数据范围：{progress.coverage['start_date']} - {progress.coverage['end_date']}")
print(f"后台加载中：{progress.background_loading}")
```

### 加载不同优先级的数据

```python
# 加载本周数据
progress = await data_loader.load_kline_priority(
    code="000001",
    data_source_manager=data_source_manager,
    data_persistence=data_persistence,
    priority=LoadPriority.CURRENT_WEEK
)

# 加载本月数据
progress = await data_loader.load_kline_priority(
    code="000001",
    data_source_manager=data_source_manager,
    data_persistence=data_persistence,
    priority=LoadPriority.CURRENT_MONTH
)

# 加载本年数据
progress = await data_loader.load_kline_priority(
    code="000001",
    data_source_manager=data_source_manager,
    data_persistence=data_persistence,
    priority=LoadPriority.CURRENT_YEAR
)
```

### 查看加载进度

```python
# 获取加载进度
load_progress = data_loader.get_load_progress("000001")

if load_progress:
    print(f"加载状态：{load_progress.status}")
    print(f"已加载：{load_progress.loaded} / {load_progress.total_expected}")
    print(f"后台加载中：{load_progress.background_loading}")
```

## 🚀 性能优化

### 1. 智能判断

系统会自动判断是否需要继续加载历史数据：

```python
# 如果单次加载数据量 >= 1800 条，说明数据源返回了上限
# 自动触发后台加载剩余历史数据
has_more = len(klines) >= 1800

if has_more and priority in [LoadPriority.TODAY, LoadPriority.CURRENT_WEEK, LoadPriority.CURRENT_MONTH]:
    await self.queue_historical_loading(code, data_source_manager, data_persistence)
```

### 2. 后台异步加载

- 使用 `asyncio.Queue` 管理加载任务
- 单个工作协程按顺序处理任务
- 不阻塞主线程和用户请求

### 3. 数据持久化

- 加载的数据立即保存到数据库
- 避免重复加载
- 支持增量更新

## 📊 日志示例

### 正常加载日志

```
2026-03-10 23:38:38 | INFO | app.services.data_loader:start:71 - 数据加载器已启动
2026-03-10 23:38:39 | INFO | app.services.data_loader:load_kline_priority:150 - 加载 K 线数据 000001 优先级 TODAY
2026-03-10 23:38:40 | INFO | app.services.data_persistence:save_klines:45 - 保存 K 线数据 000001 - 1 条
2026-03-10 23:38:40 | INFO | app.services.data_loader:_worker:262 - 后台加载 000001 优先级 LAST_1_YEAR
2026-03-10 23:38:45 | INFO | app.services.data_loader:_process_task:302 - 后台加载完成 000001 LAST_1_YEAR - 250 条数据
```

### 无数据日志

```
2026-03-10 23:38:45 | WARNING | app.services.data_loader:_process_task:305 - 后台加载无数据 000001 LAST_5_YEARS
```

### 错误日志

```
2026-03-10 23:38:45 | ERROR | app.services.data_loader:load_kline_priority:176 - 加载 K 线数据失败 000001: 网络错误
```

## 🎯 最佳实践

### 1. 默认使用 TODAY 优先级

```python
# 推荐：默认加载当天数据
progress = await data_loader.load_kline_priority(
    code="000001",
    data_source_manager=data_source_manager,
    data_persistence=data_persistence,
    priority=LoadPriority.TODAY  # 默认值
)
```

### 2. 根据场景选择优先级

```python
# 场景 1：快速查看最新行情
priority = LoadPriority.TODAY

# 场景 2：查看本周走势
priority = LoadPriority.CURRENT_WEEK

# 场景 3：查看本月表现
priority = LoadPriority.CURRENT_MONTH

# 场景 4：年度分析
priority = LoadPriority.CURRENT_YEAR

# 场景 5：历史回测
priority = LoadPriority.ALL_HISTORY
```

### 3. 监控后台加载

```python
# 定期检查加载进度
while True:
    progress = data_loader.get_load_progress("000001")
    if progress and progress.status == "complete":
        print("所有数据加载完成")
        break
    await asyncio.sleep(1)
```

## 🔍 故障排除

### 问题 1：数据加载慢

**原因**：网络延迟或数据源响应慢

**解决方案**：
- 使用更高的优先级（如 TODAY）
- 等待后台异步加载完成
- 检查网络连接

### 问题 2：数据不完整

**原因**：单次请求达到数据源上限

**解决方案**：
- 系统会自动触发后台加载
- 检查 `background_loading` 标志
- 等待后台加载完成

### 问题 3：重复加载

**原因**：数据库未正确保存

**解决方案**：
- 检查数据库连接
- 查看持久化日志
- 确认数据已保存

## 📈 性能指标

| 指标 | 目标值 | 说明 |
|------|--------|------|
| 当天数据加载时间 | < 1 秒 | 立即返回最新数据 |
| 本周数据加载时间 | < 2 秒 | 快速获取近期数据 |
| 本月数据加载时间 | < 3 秒 | 月度数据快速加载 |
| 后台加载速度 | 50-100 条/秒 | 异步加载历史数据 |
| 内存占用 | < 100MB | 分批加载，避免内存溢出 |

## 🎉 总结

分层数据加载功能通过智能的优先级策略，确保用户能够：

1. **快速获取**最新数据（当天、本周）
2. **无感知**加载历史数据（后台异步）
3. **灵活选择**加载范围（8 个优先级）
4. **高效利用**网络和存储资源

这种设计在保证用户体验的同时，最大化了数据加载的效率。

---

**更新时间**: 2026-03-10  
**版本**: v2.0  
**状态**: ✅ 已部署
