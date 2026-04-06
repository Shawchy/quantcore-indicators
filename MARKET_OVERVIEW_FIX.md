# 市场概览加载缓慢问题修复报告

## 问题总结

### 问题现象
1. 前端市场股票数、市场成交额、大盘走势（上证指数）一直处于加载中
2. 浏览器控制台报错：`Unchecked runtime.lastError: The message port closed before a response was received`
3. API 请求超时（>10 秒）

### 根本原因

**后端 API 响应阻塞**：
1. **数据库连接池过小**: 默认 size=5, overflow=10，导致并发请求时连接耗尽
2. **凭证注入阻塞**: `market_turnover_service` 在获取成交额时调用 `_ensure_credentials()`，等待浏览器启动获取 Cookie
3. **无超时保护**: 获取成交额数据没有超时限制，可能无限期等待

### 后端日志证据
```
2026-04-05 19:20:37 | INFO | app.services.market_turnover_service:fetch_and_save_latest:263 - 
正在确保 akshare 凭证注入和 TLS 指纹伪装...

2026-04-05 19:20:18 | WARNING | app.services.sector_service:get_sector_list:40 - 
从数据库读取板块列表失败：QueuePool limit of size 5 overflow 10 reached, connection timed out, timeout 30.00
```

## 修复方案

### 1. 优化数据库连接池配置

**文件**: `backend/app/storage/sqlite.py`

**修复内容**:
```python
engine = create_async_engine(
    f"sqlite+aiosqlite:///{db_file}",
    echo=settings.DEBUG,
    pool_size=20,  # 增加连接池大小（5 → 20）
    max_overflow=20,  # 增加最大溢出连接数（10 → 20）
    pool_pre_ping=True,  # 连接前 ping 测试
    pool_recycle=3600,  # 1 小时回收连接
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
```

**效果**:
- ✅ 并发连接数提升 4 倍（5 → 20）
- ✅ 最大连接数提升 2 倍（15 → 40）
- ✅ 连接回收机制避免僵死连接

### 2. 添加超时保护

**文件**: `backend/app/services/market_turnover_service.py`

**修复内容**:
```python
async def fetch_and_save_latest(self, session):
    try:
        # 使用 asyncio.wait_for 添加超时保护
        try:
            result = await asyncio.wait_for(
                self._fetch_turnover_data(trade_date),
                timeout=15.0  # 15 秒超时
            )
            
            if result:
                # 保存数据...
                return data
            
        except asyncio.TimeoutError:
            logger.error(f"获取成交额数据超时（15 秒），返回默认值")
            # 超时返回默认值，避免阻塞 UI
            return {
                'trade_date': trade_date,
                'sh_turnover': 0.0,
                'sz_turnover': 0.0,
                'total_turnover': 0.0,
                'stock_count': 0
            }
```

**效果**:
- ✅ 避免无限期等待凭证注入
- ✅ 超时后返回默认值，UI 可以正常显示
- ✅ 不影响其他 API 请求

### 3. 前端错误处理优化

**文件**: `frontend/src/services/api.ts`

**修复内容**:
```typescript
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000, // 降低超时（60s → 30s）
  // ...
})
```

**文件**: `frontend/src/pages/Dashboard.tsx`

**修复内容**:
```typescript
const { data: marketStats, isLoading: statsLoading, error: statsError } = useQuery({
  queryKey: ['marketStats', selectedDate],
  queryFn: () => screenerApi.getMarketStats(selectedDate),
  refetchInterval: false,
  staleTime: 5 * 60 * 1000,
  gcTime: 10 * 60 * 1000,
  retry: 2, // 失败重试 2 次
  retryDelay: 1000, // 重试间隔 1 秒
})

// 调试：打印错误信息
if (statsError) {
  console.error('市场统计数据获取失败:', statsError)
}
```

**效果**:
- ✅ 更快失败，避免长时间等待
- ✅ 自动重试机制
- ✅ 错误日志便于调试

### 4. 数据访问路径修复

**文件**: `frontend/src/pages/Dashboard.tsx`

**修复内容**:
```tsx
// 修复前
value={marketStats?.data?.total_stocks || 0}

// 修复后
value={marketStats?.total_stocks || 0}
```

**原因**: API 拦截器已经提取了 `data` 字段

## 验证步骤

### 1. 重启后端服务
```bash
# 停止当前服务（Ctrl+C）
# 重新启动
cd m:\Project\Quant\backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 快速诊断测试
```bash
cd m:\Project\Quant\backend
python quick_diagnosis.py
```

**预期结果**:
```
1. 健康检查... ✅
2. 市场统计数据... ✅ 响应时间：<5 秒
3. 实时行情... ✅ 响应时间：<3 秒
```

### 3. 前端验证

1. **清除浏览器缓存**: Ctrl+Shift+Delete
2. **强制刷新页面**: Ctrl+F5
3. **打开开发者工具**（F12）查看：
   - Network 标签：`/api/v1/screener/market-stats` 响应时间
   - Console 标签：是否有错误信息

**预期显示**:
- ✅ 市场股票数：5497
- ✅ 行业板块数：XX 个
- ✅ 市场成交额：XX.XX 亿（或 0.00 亿，如果超时）
- ✅ 上证指数：XXXX.XX（或 -，如果超时）

## 性能对比

### 修复前
| 指标 | 数值 | 状态 |
|------|------|------|
| 市场统计 API 响应时间 | >30 秒 | ❌ 超时 |
| 数据库连接池使用率 | 100% | ❌ 耗尽 |
| 前端加载状态 | 一直加载中 | ❌ 阻塞 |

### 修复后
| 指标 | 预期值 | 状态 |
|------|--------|------|
| 市场统计 API 响应时间 | <5 秒 | ✅ 正常 |
| 数据库连接池使用率 | <50% | ✅ 充足 |
| 前端加载状态 | <3 秒显示 | ✅ 流畅 |

## 总结

### 问题根源
1. **数据库连接池过小** → 并发请求时连接耗尽
2. **凭证注入阻塞** → 等待浏览器启动获取 Cookie
3. **无超时保护** → 可能无限期等待
4. **数据访问路径错误** → 访问 `marketStats?.data` 而不是 `marketStats`

### 修复内容
1. ✅ 增加数据库连接池（size: 5→20, overflow: 10→20）
2. ✅ 添加超时保护（15 秒超时，返回默认值）
3. ✅ 优化前端错误处理（重试、超时、日志）
4. ✅ 修复数据访问路径（`marketStats?.total_stocks`）

### 预期效果
- ✅ 市场概览加载时间：>30 秒 → <5 秒
- ✅ 前端不再一直加载中
- ✅ 超时后显示默认值，UI 正常

---

**修复完成时间**: 2026-04-05  
**修复文件**:
- `backend/app/storage/sqlite.py`
- `backend/app/services/market_turnover_service.py`
- `frontend/src/services/api.ts`
- `frontend/src/pages/Dashboard.tsx`
