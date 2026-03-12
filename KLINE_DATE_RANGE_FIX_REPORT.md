# K 线时间范围问题修复报告

## 📋 问题描述

用户报告：**K 线时间最小只能看到 3 月 2 号**，无法查看更早的历史数据。

## 🔍 问题原因

经过排查，发现了两个关键问题：

### 1. 前端默认日期范围限制
**文件**: `frontend/src/components/DailyKLine.tsx` 第 57 行

```typescript
// ❌ 问题：默认只显示近 1 年数据
const [dateRange, setDateRange] = useState<'all' | 'year' | 'month' | 'week'>('year')
```

当 `dateRange` 为 `'year'` 时，会过滤掉 1 年前的所有数据：
```typescript
case 'year':
  startDate = new Date(now.getTime() - 365 * 24 * 60 * 60 * 1000)
  break
```

### 2. 后端 API 调用未传递日期参数
**文件**: `frontend/src/pages/DailyMarket.tsx` 第 32-36 行

```typescript
// ❌ 问题：调用 API 时没有传递 start_date 和 end_date
const { data, isLoading, error } = useQuery({
  queryKey: ['kline', currentCode],
  queryFn: () => stockApi.getKline(currentCode), // 没有日期参数
  enabled: !!currentCode,
})
```

这导致后端可能只返回默认范围的数据（通常是最近部分数据）。

## ✅ 修复方案

### 修复 1: 修改默认日期范围为"全部"

**文件**: `frontend/src/components/DailyKLine.tsx` 第 57 行

```typescript
// ✅ 修复：默认显示全部数据
const [dateRange, setDateRange] = useState<'all' | 'year' | 'month' | 'week'>('all')
```

**效果**: 
- 默认显示所有可用的历史数据
- 用户可以通过下拉框选择查看"近 1 年"、"近 1 月"、"近 1 周"

### 修复 2: 后端 API 调用传递 3 年日期范围

**文件**: `frontend/src/pages/DailyMarket.tsx` 第 32-51 行

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

**效果**:
- 向后端请求近 3 年的完整数据
- 支持前复权数据（`adjust: 'qfq'`）
- 启用优先加载模式（`priorityLoad: true`）

## 📊 修复后的行为

### 数据加载
1. **默认加载**: 请求近 3 年的日线数据（2023 年 3 月 12 日 - 2026 年 3 月 12 日）
2. **数据展示**: 默认显示所有加载的数据
3. **日期过滤**: 用户可以手动选择查看不同时间段

### 用户操作
- ✅ **查看全部数据**: 默认显示全部历史数据
- ✅ **查看近 1 年**: 下拉选择"近 1 年"
- ✅ **查看近 1 月**: 下拉选择"近 1 月"
- ✅ **查看近 1 周**: 下拉选择"近 1 周"
- ✅ **缩放查看**: 使用 K 线图的缩放功能查看细节

## 🎯 技术细节

### 数据流
```
前端 (DailyMarket.tsx)
  ↓ 请求近 3 年数据
后端 API (/kline/{code})
  ↓ 从 Tushare/AkShare 获取
数据源
  ↓ 返回 K 线数据
前端组件 (DailyKLine.tsx)
  ↓ 显示全部数据（默认）
用户界面
```

### 日期格式化
所有日期在传输和显示时都使用 `YYYY-MM-DD` 格式：
- API 请求：`2023-03-12`
- 数据展示：`2023-03-12`（自动移除时分秒）

## 📝 修改文件清单

1. **frontend/src/components/DailyKLine.tsx**
   - 第 57 行：修改默认日期范围为 `'all'`

2. **frontend/src/pages/DailyMarket.tsx**
   - 第 32-51 行：添加日期计算函数，修改 API 调用传递日期参数

## 🔍 测试建议

1. **测试数据完整性**:
   - 刷新页面，确认可以看到 2023 年 3 月之前的数据
   - 检查数据表格，确认最早日期在 2023 年 3 月左右

2. **测试日期过滤**:
   - 切换不同的日期范围（全部/近 1 年/近 1 月/近 1 周）
   - 确认数据正确过滤

3. **测试缩放功能**:
   - 使用鼠标滚轮缩放 K 线图
   - 拖动底部滑块查看不同时间段
   - 确认最小可以看到单根 K 线

## 📌 注意事项

1. **数据量**: 3 年的日线数据约 730 条（250 个交易日/年），在合理范围内
2. **加载时间**: 首次加载可能需要 2-5 秒，取决于网络和数据源
3. **缓存**: 后端有缓存机制，重复访问相同股票会更快
4. **内存**: 前端组件会缓存数据，切换股票时自动更新

## ✨ 预期效果

修复后，用户应该能够：
- ✅ 看到至少 2023 年 3 月至今的所有 K 线数据
- ✅ 通过缩放查看任意时间段的细节
- ✅ 通过日期范围选择快速切换不同时间段
- ✅ 导出完整的历史数据（CSV 格式）

---

**修复时间**: 2026 年 3 月 12 日  
**影响范围**: 日线行情页面和 K 线图组件  
**向后兼容**: 是（不影响其他功能）
