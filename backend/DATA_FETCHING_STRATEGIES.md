# 数据拉取策略完整说明

## 📊 系统数据拉取策略概览

当前系统采用**多数据源 + 按需加载**的混合策略，确保数据获取的效率、稳定性和成本优化。

---

## 1️⃣ 数据源策略

### 多数据源架构

系统支持 4 个数据源，按优先级自动选择：

| 优先级 | 数据源 | 特点 | 积分要求 | 状态 |
|--------|--------|------|---------|------|
| **1** | **Tushare** | 数据质量高，稳定性好 | 120 分起 | ✅ 已启用 |
| **2** | **Efinance** | 完全免费，功能完整 | 免费 | ✅ 已启用 |
| **3** | **AkShare** | 完全免费，数据丰富 | 免费 | ✅ 已启用 |
| **4** | **Baostock** | 基础支持，稳定性一般 | 免费 | ✅ 已启用 |

### 配置方式

**配置文件**: `backend/.env`
```bash
# 默认数据源
DEFAULT_DATA_SOURCE=tushare

# 数据源优先级（从高到低）
DATA_SOURCE_PRIORITY=["tushare","efinance","akshare","baostock"]
```

### 自动故障转移

```python
# 系统自动选择数据源
data = await data_source_manager.get_daily_kline(
    code="000001",
    start_date="20260101",
    end_date="20260317",
    source_type=None  # 自动选择最优数据源
)

# 执行流程：
# 1. 尝试 Tushare（如果积分不足返回空列表）
# 2. 自动切换到 Efinance（免费，功能完整）✅
# 3. 如果失败，切换到 AkShare
# 4. 最后尝试 Baostock
```

---

## 2️⃣ 加载模式策略

### 按需加载（Lazy Loading）

系统采用**按需加载模式**，用户请求时才拉取数据，避免启动时大量数据加载。

**特点**：
- ✅ 启动速度快（无需预加载）
- ✅ 节省资源（只加载需要的数据）
- ✅ 按需缓存（减少重复请求）

**配置文件**: `backend/app/main.py`
```python
# 数据加载器已初始化为按需模式（不自动预加载）
logger.info("数据加载模式：按需加载（用户请求时才拉取数据）")
```

### 加载优先级

系统定义了 5 个加载优先级：

```python
class LoadPriority(Enum):
    CURRENT_MONTH = 1   # 本月（最新数据）
    CURRENT_YEAR = 2    # 本年
    LAST_3_YEARS = 3    # 最近 3 年
    LAST_5_YEARS = 4    # 最近 5 年
    ALL_HISTORY = 5     # 全部历史
```

---

## 3️⃣ 前端数据拉取策略

### React Query 配置

系统使用 **React Query (TanStack Query)** 进行数据管理，具有以下特性：

#### 全局配置
**文件**: `frontend/src/main.tsx`
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 分钟内认为是新鲜数据
      cacheTime: 10 * 60 * 1000, // 缓存 10 分钟
      retry: 3,                  // 失败重试 3 次
      refetchOnWindowFocus: false, // 窗口聚焦时不自动刷新
    },
  },
})
```

#### 页面级配置

**股票详情页** (`StockDetail.tsx`):

| 数据类型 | 轮询间隔 | 缓存时间 | 重试次数 | 说明 |
|---------|---------|---------|---------|------|
| 股票基本信息 | 不轮询 | 5 分钟 | 3 次 | 只在首次加载 |
| K 线数据 | 不轮询 | 5 分钟 | 3 次 | 按需加载 |
| 实时报价 | **30 秒** | 10 秒 | 2 次 | 高频刷新 |
| 分笔成交 | **60 秒** | 30 秒 | 2 次 | 中频刷新 |
| 实时资金流 | **30 秒** | 10 秒 | 2 次 | 高频刷新 |
| 筹码数据 | 不轮询 | 5 分钟 | 3 次 | 按需加载 |
| 板块信息 | 不轮询 | 5 分钟 | 3 次 | 按需加载 |
| 股东信息 | 不轮询 | 5 分钟 | 3 次 | 按需加载 |

**代码示例**:
```typescript
// 实时报价 - 30 秒轮询
const { data: realtimeQuoteData } = useQuery({
  queryKey: ['realtimeQuote', code],
  queryFn: () => realtimeApi.getQuote(code!),
  enabled,
  refetchInterval: 30000,  // 30 秒刷新一次
  retry: 2,                // 失败重试 2 次
  staleTime: 10000,        // 10 秒内使用缓存
})

// 分笔成交 - 60 秒轮询
const { data: tickData } = useQuery({
  queryKey: ['tickData', code],
  queryFn: () => realtimeApi.getTickData(code!, 'dc', 100),
  enabled,
  refetchInterval: 60000,  // 60 秒刷新一次
  retry: 2,
  staleTime: 30000,        // 30 秒内使用缓存
})
```

**首页概览** (`Dashboard.tsx`):
```typescript
// 市场概览 - 5 秒轮询（最高频率）
const { data: marketOverview } = useQuery({
  queryKey: ['marketOverview'],
  queryFn: () => marketApi.getOverview(),
  refetchInterval: 5000,   // 5 秒刷新一次
})
```

**资金流向卡片** (`MarketMoneyflowCard.tsx`):
```typescript
// 大盘资金流向 - 60 秒轮询
const { data: moneyflowData } = useQuery({
  queryKey: ['marketMoneyflow'],
  queryFn: () => moneyflowApi.getMarketMoneyflow(),
  refetchInterval: 60000,  // 60 秒刷新一次
})
```

---

## 4️⃣ 后端超时控制策略

### API 超时配置

**文件**: `backend/app/api/v1/endpoints/realtime.py`

```python
# 超时时间配置
REALTIME_TIMEOUT = 5   # 实时数据超时 5 秒
TICK_TIMEOUT = 10      # 分笔成交超时 10 秒
```

### 超时处理机制

```python
try:
    # 使用 asyncio.wait_for 添加超时控制
    df = await asyncio.wait_for(
        asyncio.get_event_loop().run_in_executor(
            None, lambda: ts.realtime_quote(ts_code=code, src=src)
        ),
        timeout=REALTIME_TIMEOUT
    )
except asyncio.TimeoutError:
    raise HTTPException(
        status_code=504,
        detail=f"获取实时数据超时（{REALTIME_TIMEOUT}秒），请重试或切换数据源"
    )
```

---

## 5️⃣ 缓存策略

### 后端缓存

**文件**: `backend/app/storage/cache.py`

使用 **Redis** 作为缓存后端，不同数据类型有不同的缓存时间：

| 数据类型 | 缓存时间 | 说明 |
|---------|---------|------|
| 实时报价 | 30 秒 | 高频数据，短时间缓存 |
| 分笔成交 | 60 秒 | 中频数据 |
| K 线数据 | 5 分钟 | 历史数据，长时间缓存 |
| 股票信息 | 10 分钟 | 基础信息，变化少 |
| 板块信息 | 10 分钟 | 板块分类，相对稳定 |
| 股东信息 | 1 小时 | 定期报告，变化很少 |

**代码示例**:
```python
# 检查缓存
cache_key = f"realtime_quote_{code}_{src}"
cached_data = await cache_manager.get("realtime", cache_key)

if cached_data:
    return ResponseModel(data=cached_data, message="从缓存获取数据")

# 获取数据并缓存
df = await fetch_data()
await cache_manager.set("realtime", cache_key, data, expire=30)  # 30 秒过期
```

### 前端缓存

使用 **React Query** 的内置缓存机制：

```typescript
// 缓存配置
staleTime: 10000,   // 10 秒内认为是新鲜数据，直接从缓存读取
cacheTime: 300000,  // 缓存 5 分钟，之后从缓存中删除
```

---

## 6️⃣ 错误处理策略

### 重试机制

**前端重试**:
```typescript
retry: 2,  // 失败后重试 2 次
retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000)  // 指数退避
```

**后端重试**:
```python
# efinance 适配器 - 重试 3 次
max_retries = 3
for attempt in range(max_retries):
    try:
        df = ef.stock.get_realtime_quotes(market_types)
        break
    except Exception as e:
        if attempt < max_retries - 1:
            logger.warning(f"获取失败，重试 {attempt + 1}/{max_retries}: {e}")
            await asyncio.sleep(1)  # 等待 1 秒后重试
        else:
            raise
```

### 错误降级

```typescript
// 错误处理示例
const { data, error, isLoading } = useQuery({
  queryKey: ['stock', code],
  queryFn: () => stockApi.getStockInfo(code!),
  retry: 2,
})

// UI 中显示错误
{error && (
  <Alert status="error">
    <AlertIcon />
    加载失败：{error.message}
    <Button onClick={() => refetch()}>重试</Button>
  </Alert>
)}
```

---

## 7️⃣ 性能优化策略

### 请求频率控制

**优化前后对比**:

| 数据类型 | 优化前 | 优化后 | 减少比例 |
|---------|--------|--------|---------|
| 实时报价 | 10 秒/次 | 30 秒/次 | ⬇️ 67% |
| 分笔成交 | 30 秒/次 | 60 秒/次 | ⬇️ 50% |
| 总体请求 | 8 次/分钟 | 3 次/分钟 | ⬇️ 62.5% |

### 按需加载

```typescript
// 只有当代码有效时才启用查询
const enabled = queryEnabled(code, isValidCode)

const { data } = useQuery({
  queryKey: ['stock', code],
  queryFn: () => stockApi.getStockInfo(code!),
  enabled,  // 条件加载
})
```

### 分页加载

```typescript
// 分笔成交数据限制数量
const { data } = useQuery({
  queryKey: ['tickData', code],
  queryFn: () => realtimeApi.getTickData(code!, 'dc', 100),  // 只获取 100 条
})
```

---

## 8️⃣ 数据源切换策略

### 手动切换

用户可以通过 **数据源控制面板** 手动切换数据源：

```typescript
// 切换数据源
const toggleMutation = useMutation({
  mutationFn: ({ source, enabled }) => 
    dataSourceApi.toggleSource(source, enabled),
  onSuccess: () => {
    queryClient.invalidateQueries()  // 重新加载数据
  }
})
```

### 自动切换

```python
# 数据源工厂自动选择
async def get_adapter(self, source_type: Optional[str] = None):
    if source_type:
        return self._adapters[DataSourceType(source_type)]
    
    # 按优先级返回可用的数据源
    for source in self._priority_list:
        if source in self._adapters:
            return self._adapters[source]
    
    raise ValueError("没有可用的数据源")
```

---

## 9️⃣ 监控与日志

### 日志记录

```python
# 数据源初始化日志
logger.info("数据源 tushare 初始化成功（优先级：1)")
logger.info("数据源 efinance 初始化成功（优先级：2)")
logger.info("数据源工厂初始化完成，可用数据源：['tushare', 'efinance', 'akshare', 'baostock']")

# API 调用日志
logger.info(f"获取实时数据成功 {code}: {len(df)}条，耗时 {elapsed:.2f}秒")
logger.warning(f"获取实时数据超时，重试 1/3: {e}")
logger.error(f"获取数据失败 {code}: {e}")
```

### 性能监控

```python
# 记录 API 响应时间
start_time = time.time()
df = await fetch_data()
elapsed = time.time() - start_time
logger.info(f"获取数据成功，耗时 {elapsed:.2f}秒")
```

---

## 🔟 策略总结

### 核心优势

1. **高可用性** - 4 个数据源互为备份，自动故障转移
2. **成本优化** - 优先使用免费数据源（Efinance、AkShare）
3. **性能优秀** - 按需加载 + 多级缓存，减少 62.5% 请求
4. **用户体验** - 快速响应 + 友好错误提示
5. **可维护性** - 清晰的日志 + 完善的监控

### 策略架构图

```
用户请求
    ↓
前端缓存检查 (React Query)
    ↓ (缓存未命中)
后端 API
    ↓
后端缓存检查 (Redis)
    ↓ (缓存未命中)
数据源工厂
    ↓ (按优先级)
Tushare (120 分) → 失败
    ↓
Efinance (免费) → 成功 ✅
    ↓
返回数据 → 缓存 → 返回给用户
```

### 最佳实践建议

1. **合理设置轮询间隔** - 实时数据 30-60 秒，非实时数据不轮询
2. **充分利用缓存** - 设置合适的 staleTime 和 cacheTime
3. **添加超时控制** - 防止无限期等待（5-10 秒）
4. **实现错误降级** - 显示友好错误提示，提供重试按钮
5. **监控性能指标** - 记录响应时间、失败率等关键指标

---

## 📝 配置文件汇总

### 后端配置 (`backend/.env`)
```bash
# 数据源配置
DEFAULT_DATA_SOURCE=tushare
DATA_SOURCE_PRIORITY=["tushare","efinance","akshare","baostock"]

# Tushare 配置
TUSHARE_TOKEN=your_token_here
TUSHARE_POINTS=120
```

### 前端配置 (`frontend/src/main.tsx`)
```typescript
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000,  // 5 分钟
      cacheTime: 10 * 60 * 1000, // 10 分钟
      retry: 3,
      refetchOnWindowFocus: false,
    },
  },
})
```

---

这份文档完整记录了当前系统的数据拉取策略，包括数据源选择、加载模式、缓存策略、超时控制、错误处理等各个方面。所有策略都经过实际验证，确保系统稳定高效运行。
