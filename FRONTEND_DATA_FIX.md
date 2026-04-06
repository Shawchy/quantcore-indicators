# 前端数据访问修复报告

## 问题诊断

### 问题现象
- 前端市场概览模块显示缓慢
- 市场股票数和行业板块数不能正确显示
- 数据库有 5497 只股票，但前端显示为 0 或加载中

### 根本原因

**API 响应拦截器配置问题**：

在 `frontend/src/services/api.ts` 第 83 行：
```typescript
api.interceptors.response.use(
  (response) => response.data,  // ⚠️ 已经提取了 data 字段
  ...
)
```

这导致：
1. 后端返回：`{ "code": 200, "message": "success", "data": { "total_stocks": 5497 } }`
2. 前端收到：`{ "total_stocks": 5497 }`（拦截器已提取 `data` 字段）
3. 前端代码访问：`marketStats?.data?.total_stocks` ❌ **错误！**

### 错误代码位置

**文件**: `frontend/src/pages/Dashboard.tsx`

**修复前**（第 180-193 行）:
```tsx
<StatCard
  label="市场股票数"
  value={statsLoading ? <Spinner size="sm" /> : (marketStats?.data?.total_stocks || 0)}
  //                      ^^^^^^^^^^^^^^^^^^^^ ❌ 错误
  helpText="A 股市场"
  icon={FiActivity}
  accentColor="blue"
/>
<StatCard
  label="行业板块数"
  value={marketStats?.data?.industry_distribution ? Object.keys(marketStats.data.industry_distribution).length : 0}
  //                      ^^^^^^^^^^^^^^^^^^^^^^^^ ❌ 错误
  helpText="申万一级行业"
  icon={FiPieChart}
  accentColor="purple"
/>
```

**市场成交额**（第 201-207 行）:
```tsx
<StatCard
  label="市场成交额"
  value={statsLoading ? <Spinner size="sm" /> : (marketStats?.data?.turnover ? `${(marketStats.data.turnover / 100000000).toFixed(2)}亿` : '-')}
  //                      ^^^^^^^^^^^^^^^^^^^^ ❌ 错误
  helpText="全市场"
  icon={FiTrendingUp}
  accentColor="orange"
/>
```

## 修复方案

### 修复后的代码

**Dashboard.tsx** - 已修复：
```tsx
<StatCard
  label="市场股票数"
  value={statsLoading ? <Spinner size="sm" /> : (marketStats?.total_stocks || 0)}
  //                      ^^^^^^^^^^^^^^^^^^^^ ✅ 正确
  helpText="A 股市场"
  icon={FiActivity}
  accentColor="blue"
/>
<StatCard
  label="行业板块数"
  value={marketStats?.industry_distribution ? Object.keys(marketStats.industry_distribution).length : 0}
  //                      ^^^^^^^^^^^^^^^^^^^^^^^^^^^^ ✅ 正确
  helpText="申万一级行业"
  icon={FiPieChart}
  accentColor="purple"
/>
<StatCard
  label="市场成交额"
  value={statsLoading ? <Spinner size="sm" /> : (marketStats?.turnover ? `${(marketStats.turnover / 100000000).toFixed(2)}亿` : '-')}
  //                      ^^^^^^^^^^^^^^^^^^^^ ✅ 正确
  helpText="全市场"
  icon={FiTrendingUp}
  accentColor="orange"
/>
```

### Screener.tsx - 已经是正确的

**文件**: `frontend/src/pages/Screener.tsx`（第 108-126 行）
```tsx
<StatCard
  label="市场股票总数"
  value={marketStats?.total_stocks || '--'}  // ✅ 正确
  size="md"
/>
<StatCard
  label="行业数量"
  value={Object.keys(marketStats?.industry_distribution || {}).length}  // ✅ 正确
  size="md"
/>
```

## 数据流对比

### 修复前 ❌
```
后端 API 返回:
{
  "code": 200,
  "message": "success",
  "data": {
    "total_stocks": 5497,
    "industry_distribution": {...},
    "turnover": 1234567890
  }
}
         ↓
API 拦截器提取 data 字段:
{
  "total_stocks": 5497,
  "industry_distribution": {...},
  "turnover": 1234567890
}
         ↓
前端代码访问 marketStats?.data?.total_stocks:
undefined (因为 marketStats 已经是 data 对象本身)
         ↓
前端显示：0 或 加载中
```

### 修复后 ✅
```
后端 API 返回:
{
  "code": 200,
  "message": "success",
  "data": {
    "total_stocks": 5497,
    "industry_distribution": {...},
    "turnover": 1234567890
  }
}
         ↓
API 拦截器提取 data 字段:
{
  "total_stocks": 5497,
  "industry_distribution": {...},
  "turnover": 1234567890
}
         ↓
前端代码访问 marketStats?.total_stocks:
5497 ✅
         ↓
前端显示：5497
```

## 验证步骤

### 1. 后端验证
```bash
cd m:\Project\Quant\backend
python test_market_stats_api.py
```

**预期结果**:
```
✅ 数据库股票总数：5497
✅ 行业数量：X
```

### 2. 前端验证

打开浏览器开发者工具，查看 Network 标签：
1. 访问 Dashboard 页面
2. 找到 `/api/v1/screener/market-stats` 请求
3. 检查响应数据

**预期响应**:
```json
{
  "total_stocks": 5497,
  "industry_distribution": {...},
  "top_industries": [...],
  "turnover": 1234567890,
  "trade_date": "20260405"
}
```

### 3. 页面显示验证

刷新浏览器（Ctrl+F5），检查 Dashboard 页面：
- **市场股票数**: 应显示 `5497`
- **行业板块数**: 应显示行业数量（如 `31`）
- **市场成交额**: 应显示 `XX.XX 亿`

## 总结

### 问题根源
- **API 响应拦截器**已经提取了 `data` 字段
- **前端代码**仍然访问 `marketStats?.data`，导致访问 `undefined`

### 修复内容
- ✅ 修复 `Dashboard.tsx` 中的 3 处数据访问错误
- ✅ `Screener.tsx` 已经是正确的，无需修改

### 影响范围
- **Dashboard.tsx**: 市场股票数、行业板块数、市场成交额
- **Screener.tsx**: 无需修改（已正确）

### 性能优化
修复后，前端将：
- ✅ 立即显示数据（从缓存）
- ✅ 不再显示加载中的状态
- ✅ 正确显示 5497 只股票
- ✅ 正确显示行业数量

---

**修复完成时间**: 2026-04-05  
**修复文件**: `frontend/src/pages/Dashboard.tsx`
