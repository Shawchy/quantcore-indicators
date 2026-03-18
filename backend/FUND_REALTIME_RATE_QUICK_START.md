# 基金实时估算涨跌幅 API - 快速使用指南

## 概述

实现了基金实时估算涨跌幅 API，支持单只和多只基金查询。

**数据来源：** efinance (天天基金网)  
**缓存时间：** 60 秒  
**更新时间：** 交易日 15:00

---

## 快速开始

### 后端调用

```python
from app.adapters.factory import data_source_manager

# 单只基金
rate_info = await data_source_manager.get_fund_realtime_increase_rate(
    fund_codes='161725',
    source_type='efinance'
)

# 多只基金
rate_list = await data_source_manager.get_fund_realtime_increase_rate(
    fund_codes=['161725', '005827'],
    source_type='efinance'
)
```

### 前端调用

```typescript
import { fundApi } from '@/services/fund'

// 单只基金
const { data } = await fundApi.getFundRealtimeRate('161725')
console.log(data.estimate_change_pct)

// 多只基金
const { data } = await fundApi.getFundRealtimeRate(['161725', '005827'])
data.forEach(fund => {
  console.log(`${fund.name}: ${fund.estimate_change_pct}%`)
})
```

---

## API 端点

### 单只基金
```http
GET /api/v1/fund/realtime-rate/161725
```

### 多只基金
```http
GET /api/v1/fund/realtime-rate/161725,005827
```

---

## 返回数据

```json
{
    "success": true,
    "data": {
        "code": "161725",
        "name": "招商中证白酒指数 (LOF)A",
        "net_value": 2.3908,
        "nav_date": "2026-03-17",
        "estimate_time": "2026-03-17 15:00",
        "estimate_change_pct": 0.64
    }
}
```

**字段说明：**
- `code`: 基金代码
- `name`: 基金名称
- `net_value`: 最新净值
- `nav_date`: 净值公开日期
- `estimate_time`: 估算时间
- `estimate_change_pct`: 估算涨跌幅（%）

---

## 测试

### 运行测试脚本
```bash
cd d:\PROJ\Quant\backend
python test_fund_realtime_rate.py
```

### 测试结果
✅ 单只基金查询 - 通过  
✅ 多只基金批量查询 - 通过  
✅ 缓存机制 - 通过

---

## 注意事项

1. **实时性：** 仅在交易日 15:00 有估算涨跌幅，非交易时间返回最新净值
2. **缓存：** 60 秒缓存，避免频繁请求
3. **批量查询：** 推荐批量查询多只基金，效率更高

---

## 相关文件

- 后端实现：`app/adapters/efinance_adapter.py`
- API 路由：`app/api/v1/endpoints/fund.py`
- 前端服务：`frontend/src/services/fund.ts`
- 详细文档：`FUND_REALTIME_RATE_API_SUMMARY.md`

---

**实施时间：** 2026-03-18  
**测试状态：** ✅ 通过  
**部署状态：** 待部署
