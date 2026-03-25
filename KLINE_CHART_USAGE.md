# 现代化 KLineChart 使用指南

## 📋 概述

这是一个完全自主开发的现代化 K 线图表系统，采用 Canvas 渲染、Web Workers 多线程处理和智能 React Hooks，完全替换 ECharts。

---

## ✅ 已实现的功能

### 后端（FastAPI + pandas-ta）

- ✅ **chart_data_service.py** - 图表数据服务
  - K 线数据获取（日/周/月/分钟线）
  - 技术指标计算（MA、MACD、RSI、KDJ、BOLL、ATR）
  - 性能监控

- ✅ **kline.py** - RESTful API 端点
  - `GET /api/v1/kline/{code}` - 获取 K 线数据（带指标）
  - `GET /api/v1/kline/{code}/latest` - 获取最新 K 线
  - `POST /api/v1/indicators/calculate` - 批量计算指标
  - `GET /api/v1/indicators/list` - 获取可用指标列表

### 前端（React + Canvas）

- ✅ **Web Workers**
  - `data.worker.ts` - 数据处理 Worker
  - `worker.pool.ts` - Worker 池管理

- ✅ **React Hooks**
  - `useKLine.ts` - 统一的 K 线图表 Hook
  - `useKLineData.ts` - 数据获取 Hook
  - `useKLineCalc.ts` - 指标计算 Hook
  - `useKLineRender.ts` - 渲染优化 Hook

- ✅ **图表组件**
  - `KLineChart.tsx` - 主组件
  - `CanvasChart.tsx` - Canvas 渲染引擎
  - `VolumeChart.tsx` - 成交量图

- ✅ **类型定义**
  - `chart.ts` - 完整的 TypeScript 类型

---

## 🚀 快速开始

### 1. 后端配置

确保后端服务已启动：

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

验证 API 端点：

```bash
# 测试 K 线 API
curl "http://localhost:8000/api/v1/kline/000001?k_type=daily&indicators=MA,MACD,RSI"

# 查看指标列表
curl "http://localhost:8000/api/v1/indicators/list"
```

### 2. 前端使用

#### 基础用法

```tsx
import React from 'react'
import { KLineChart } from '@/components/charts/KLineChart'

function StockDetail() {
  return (
    <div>
      <h1>个股详情 - 000001</h1>
      <KLineChart
        code="000001"
        kType="daily"
        indicators={['MA', 'MACD', 'RSI']}
        height="600px"
        showVolume={true}
      />
    </div>
  )
}

export default StockDetail
```

#### 高级用法

```tsx
import React, { useState } from 'react'
import { KLineChart } from '@/components/charts/KLineChart'
import type { KType, IndicatorType } from '@/types/chart'

function AdvancedChart() {
  const [kType, setKType] = useState<KType>('daily')
  const [indicators, setIndicators] = useState<IndicatorType[]>(['MA', 'MACD', 'RSI'])

  const handleZoom = (scale: number) => {
    console.log('缩放:', scale)
  }

  const handlePan = (offset: number) => {
    console.log('平移:', offset)
  }

  return (
    <div>
      <div style={{ marginBottom: '16px' }}>
        <select
          value={kType}
          onChange={(e) => setKType(e.target.value as KType)}
          style={{ marginRight: '8px', padding: '4px 8px' }}
        >
          <option value="daily">日线</option>
          <option value="weekly">周线</option>
          <option value="monthly">月线</option>
        </select>

        <button
          onClick={() => setIndicators(['MA', 'MACD', 'RSI', 'KDJ'])}
          style={{ marginLeft: '8px', padding: '4px 8px' }}
        >
          添加 KDJ
        </button>
      </div>

      <KLineChart
        code="000001"
        kType={kType}
        indicators={indicators}
        height="700px"
        showVolume={true}
        showIndicators={true}
        useWorker={true}
        useWebSocket={true}
        onZoom={handleZoom}
        onPan={handlePan}
      />
    </div>
  )
}

export default AdvancedChart
```

---

## 📊 API 文档

### GET /api/v1/kline/{code}

获取 K 线数据（带技术指标）

**参数：**
- `code` (路径参数) - 股票代码，如 `000001`
- `k_type` (查询参数) - K 线类型：`daily`, `weekly`, `monthly`, `1m`, `5m`, etc.
- `start_date` (可选) - 开始日期：`YYYY-MM-DD`
- `end_date` (可选) - 结束日期：`YYYY-MM-DD`
- `indicators` (可选) - 指标列表：`MA`, `MACD`, `RSI`, `KDJ`, `BOLL`, `ATR`
- `adjust` (可选) - 复权类型：`qfq` (前复权), `hfq` (后复权), `no` (不复权)
- `use_cache` (可选) - 是否使用缓存：`true`/`false`

**响应示例：**

```json
{
  "status": "success",
  "data": [
    {
      "date": "2024-01-01",
      "open": 10.5,
      "high": 11.2,
      "low": 10.3,
      "close": 11.0,
      "volume": 1234567,
      "amount": 13579246,
      "turnover_rate": 2.5
    }
  ],
  "indicators": {
    "MA": [
      {
        "date": "2024-01-01",
        "ma5": 10.8,
        "ma10": 10.5,
        "ma20": 10.2,
        "ma60": 9.8
      }
    ],
    "MACD": [...],
    "RSI": [...],
    "KDJ": [...]
  },
  "metadata": {
    "code": "000001",
    "k_type": "daily",
    "count": 100,
    "adjust": "qfq"
  },
  "performance": {
    "fetch_time_ms": 50,
    "calc_time_ms": 30,
    "total_ms": 80
  }
}
```

---

## 🎨 组件 Props

### KLineChart

| 属性 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `code` | `string` | 必填 | 股票代码 |
| `kType` | `KType` | `'daily'` | K 线类型 |
| `indicators` | `IndicatorType[]` | `['MA', 'MACD', 'RSI']` | 技术指标列表 |
| `height` | `string` | `'500px'` | 图表高度 |
| `showVolume` | `boolean` | `true` | 是否显示成交量 |
| `showIndicators` | `boolean` | `true` | 是否显示指标图 |
| `useWorker` | `boolean` | `true` | 是否使用 Web Worker |
| `useWebSocket` | `boolean` | `true` | 是否使用 WebSocket |
| `onZoom` | `(scale: number) => void` | - | 缩放回调 |
| `onPan` | `(offset: number) => void` | - | 平移回调 |

---

## ⚡ 性能优化

### 1. 数据缓存

系统自动缓存 API 响应（5 分钟），减少重复请求：

```typescript
// 缓存策略
const CACHE_DURATION = 5 * 60 * 1000 // 5 分钟

// 禁用缓存
<KLineChart code="000001" useCache={false} />
```

### 2. Web Worker

使用 Web Worker 处理数据，不阻塞 UI 线程：

```typescript
// 启用 Worker（默认开启）
<KLineChart code="000001" useWorker={true} />
```

### 3. 渲染优化

- 防抖渲染（100ms）
- requestAnimationFrame 动画
- Canvas 离屏渲染

---

## 🔧 自定义配置

### 颜色配置

```typescript
const customConfig = {
  colors: {
    up: '#ef232a',      // A 股上涨 - 红色
    down: '#14cf1a',    // A 股下跌 - 绿色
    ma5: '#ff9800',     // MA5 - 橙色
    ma10: '#2196f3',    // MA10 - 蓝色
    ma20: '#9c27b0',    // MA20 - 紫色
    ma60: '#795548'     // MA60 - 棕色
  }
}
```

### 指标配置

```typescript
// 自定义指标组合
const indicators: IndicatorType[] = [
  'MA',      // 移动平均线
  'MACD',    // 异同移动平均线
  'RSI',     // 相对强弱指标
  'KDJ',     // 随机指标
  'BOLL',    // 布林带
  'ATR'      // 平均真实波幅
]
```

---

## 📝 使用示例

### 示例 1：基础个股 K 线图

```tsx
import { KLineChart } from '@/components/charts/KLineChart'

function BasicExample() {
  return (
    <KLineChart
      code="000001"
      kType="daily"
      height="500px"
    />
  )
}
```

### 示例 2：多指标分析

```tsx
function MultiIndicatorExample() {
  return (
    <KLineChart
      code="300750"
      kType="daily"
      indicators={['MA', 'MACD', 'RSI', 'KDJ', 'BOLL']}
      height="800px"
      showVolume={true}
      showIndicators={true}
    />
  )
}
```

### 示例 3：分钟线图表

```tsx
function MinuteChartExample() {
  return (
    <KLineChart
      code="000001"
      kType="5m"  // 5 分钟线
      indicators={['MA', 'MACD']}
      height="600px"
    />
  )
}
```

### 示例 4：自定义交互

```tsx
function InteractiveExample() {
  const handleZoom = (scale: number) => {
    console.log('缩放比例:', scale)
    // 可以在这里更新状态
  }

  const handlePan = (offset: number) => {
    console.log('平移距离:', offset)
    // 可以在这里更新状态
  }

  return (
    <KLineChart
      code="000001"
      onZoom={handleZoom}
      onPan={handlePan}
    />
  )
}
```

---

## 🐛 故障排查

### 问题 1：图表不显示

**检查：**
1. 后端服务是否启动
2. API 端点是否可访问
3. 浏览器控制台是否有错误

**解决：**
```bash
# 测试 API
curl "http://localhost:8000/api/v1/kline/000001"

# 查看后端日志
tail -f logs/quant.log
```

### 问题 2：指标不显示

**检查：**
1. 是否正确请求了指标
2. 后端是否返回了指标数据

**解决：**
```typescript
// 明确指定指标
<KLineChart
  code="000001"
  indicators={['MA', 'MACD', 'RSI']}
/>
```

### 问题 3：性能问题

**优化建议：**
1. 减少初始加载的数据量
2. 使用数据缓存
3. 启用 Web Worker
4. 减少不必要的重渲染

---

## 📚 相关文档

- [架构设计](file://d:\PROJ\Quant\KLINE_CHART_ARCHITECTURE.md)
- [实现指南](file://d:\PROJ\Quant\KLINE_CHART_IMPLEMENTATION_GUIDE.md)
- [后端 API](file://d:\PROJ\Quant\backend\app\api\v1\endpoints\kline.py)
- [数据服务](file://d:\PROJ\Quant\backend\app\services\chart_data_service.py)

---

## 🎯 下一步

### 待完善功能

- [ ] MACD 指标图组件
- [ ] RSI 指标图组件
- [ ] KDJ 指标图组件
- [ ] BOLL 指标图组件
- [ ] 十字光标
- [ ] 工具提示（Tooltip）
- [ ] 缩放和平移优化
- [ ] 更多技术指标

---

**文档版本：** v1.0.0  
**创建时间：** 2026-03-24  
**状态：** 核心功能已完成，持续优化中
