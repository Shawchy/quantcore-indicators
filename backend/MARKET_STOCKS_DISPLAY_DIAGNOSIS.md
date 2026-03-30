# 市场股票数显示问题诊断报告

## 问题描述

用户报告：**"市场股票数无法正常显示"**

## 诊断结果

### 后端 API 测试

**测试脚本**: `test_market_stats_api_direct.py`

**结果**:
```
API 返回数据:
  total_stocks: 5830 ✅
  turnover: 18530.71亿 ✅
  trade_date: 20260327 ✅
  top_industries: 10 个 ✅

✅ 市场股票数正确！
```

### 数据库查询测试

**测试脚本**: `test_market_stats.py`

**结果**:
```
股票总数: 5830 ✅

前 5 只股票:
  000001: 平安银行
  002378: 章源钨业
  600519: 贵州茅台
  000858: 五 粮 液
  600036: 招商银行
```

### API 端点分析

**文件**: `app/api/v1/endpoints/screener.py`

**代码逻辑**:
```python
@router.get("/market-stats")
async def get_market_statistics(...):
    # 1. 检查缓存
    cached_data = await api_cache.get('api_stats', cache_key)
    if cached_data:
        return ResponseModel(data=cached_data)  # ✅ 缓存命中
    
    # 2. 查询数据库
    result = await session.execute(select(func.count()).select_from(StockInfo))
    total_count = result.scalar()  # 5830 ✅
    
    # 3. 返回数据
    return ResponseModel(data={
        "total_stocks": total_count or 0,  # ✅ 返回 5830
        ...
    })
```

### 前端显示分析

**文件**: `frontend/src/pages/Dashboard.tsx`

**代码**:
```typescript
<StatCard
  label="市场股票数"
  value={statsLoading ? <Spinner size="sm" /> : (marketStats?.data?.total_stocks || 0)}
  helpText="A 股市场"
/>
```

**数据流**:
```
API 返回: { data: { total_stocks: 5830 } }
         ↓
React Query: marketStats.data.total_stocks = 5830
         ↓
StatCard: value = 5830 ✅
```

## 可能的问题

### 1. 前端缓存问题

**症状**: 前端显示旧数据（可能是之前只有 7 只股票时的缓存）

**解决方案**:
```typescript
// 清除 React Query 缓存
queryClient.invalidateQueries(['marketStats'])
```

### 2. API 缓存问题

**症状**: 后端缓存了旧数据

**解决方案**:
```python
# 清除后端缓存
await api_cache.delete('api_stats', {'date': None})
```

### 3. 前端未刷新

**症状**: 前端页面没有重新获取数据

**解决方案**: 刷新浏览器页面（Ctrl+F5）

## 修复步骤

### 步骤 1: 清除后端缓存

```bash
# 运行清除缓存脚本
python clear_market_stats_cache.py
```

### 步骤 2: 清除前端缓存

在浏览器中：
1. 打开开发者工具（F12）
2. Application → Storage → Clear site data
3. 或按 Ctrl+Shift+Delete 清除缓存

### 步骤 3: 强制刷新前端

```
按 Ctrl+F5 强制刷新页面
```

## 验证数据

### 后端数据验证

```bash
# 测试 API
python test_market_stats_api_direct.py

# 预期输出
total_stocks: 5830 ✅
```

### 前端数据验证

打开浏览器控制台，执行：
```javascript
console.log(marketStats?.data?.total_stocks)
// 预期输出: 5830
```

## 相关文件

### 后端文件
- `app/api/v1/endpoints/screener.py` - API 端点
- `app/storage/sqlite.py` - 数据库模型
- `app/utils/api_cache_stats.py` - 缓存管理

### 前端文件
- `src/pages/Dashboard.tsx` - Dashboard 页面
- `src/services/api.ts` - API 调用
- `src/components/StatCard.tsx` - 统计卡片组件

## 总结

### 数据验证结果

| 项目 | 状态 | 值 |
|------|------|-----|
| 数据库股票数 | ✅ 正确 | 5830 |
| API 返回值 | ✅ 正确 | 5830 |
| 缓存机制 | ✅ 正常 | 5 分钟 |
| 前端显示 | ⏳ 待验证 | - |

### 可能原因

1. **前端缓存未更新** - 最可能的原因
2. **浏览器缓存** - 需要强制刷新
3. **API 缓存** - 已有 5 分钟缓存

### 下一步操作

1. ✅ 验证后端数据正确
2. ⏳ 清除前端缓存
3. ⏳ 强制刷新浏览器
4. ⏳ 验证前端显示

**后端数据完全正确，问题可能在前端缓存！请按 Ctrl+F5 强制刷新浏览器页面。**
