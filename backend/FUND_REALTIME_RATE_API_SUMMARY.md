# 基金实时估算涨跌幅 API 实施总结

## 实施时间
2026-03-18 19:30

## 实施内容

### 1. 后端实现

#### 1.1 efinance 适配器

**文件：** `app/adapters/efinance_adapter.py`

**新增方法：**
```python
async def get_fund_realtime_increase_rate(
    self,
    fund_codes: Union[str, List[str]]
) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    """获取基金实时估算涨跌幅度"""
```

**功能特性：**
- ✅ 支持单只基金查询（返回 dict）
- ✅ 支持多只基金批量查询（返回 list）
- ✅ 缓存机制（60 秒，实时数据）
- ✅ 频率控制
- ✅ 安全的数据解析（处理 NaN、null 等异常值）

**返回数据：**
```python
# 单只基金
{
    'code': '161725',
    'name': '招商中证白酒指数 (LOF)A',
    'net_value': 2.8856,
    'nav_date': '2021-09-07',
    'estimate_time': '2021-09-07 15:00',
    'estimate_change_pct': 0.64
}

# 多只基金
[
    {
        'code': '161725',
        'name': '招商中证白酒指数 (LOF)A',
        'net_value': 2.8856,
        'nav_date': '2021-09-07',
        'estimate_time': '2021-09-07 15:00',
        'estimate_change_pct': 0.64
    },
    {
        'code': '005827',
        'name': '易方达蓝筹精选混合',
        'net_value': 2.5704,
        'nav_date': '2021-09-07',
        'estimate_time': '2021-09-07 15:00',
        'estimate_change_pct': 0.67
    }
]
```

---

#### 1.2 API 路由

**文件：** `app/api/v1/endpoints/fund.py`

**新增端点：**
```python
@router.get("/realtime-rate/{fund_codes}", response_model=ResponseModel[Union[dict, List[dict]]])
async def get_fund_realtime_increase_rate(fund_codes: str)
```

**接口说明：**

**单只基金：**
```http
GET /api/v1/fund/realtime-rate/161725
```

**多只基金：**
```http
GET /api/v1/fund/realtime-rate/161725,005827
```

**响应格式：**
```json
{
    "success": true,
    "code": "OK",
    "message": "操作成功",
    "data": {
        "code": "161725",
        "name": "招商中证白酒指数 (LOF)A",
        "net_value": 2.8856,
        "nav_date": "2021-09-07",
        "estimate_time": "2021-09-07 15:00",
        "estimate_change_pct": 0.64
    }
}
```

---

### 2. 前端实现

#### 2.1 TypeScript 类型定义

**文件：** `frontend/src/services/fund.ts`

**新增接口：**
```typescript
/** 基金实时估算涨跌幅信息 */
export interface FundRealtimeRateInfo {
  code: string                    // 基金代码
  name: string                    // 基金名称
  net_value?: number              // 最新净值
  nav_date?: string               // 最新净值公开日期
  estimate_time?: string          // 估算时间
  estimate_change_pct?: number    // 估算涨跌幅（%）
}
```

---

#### 2.2 API 服务方法

**文件：** `frontend/src/services/fund.ts`

**新增方法：**
```typescript
/**
 * 获取基金实时估算涨跌幅度
 * 
 * @param fundCodes 基金代码（单只或多只）
 */
getFundRealtimeRate: (fundCodes: string | string[]) => {
  const codeParam = Array.isArray(fundCodes) 
    ? fundCodes.join(',') 
    : fundCodes
  
  return api.get<FundRealtimeRateInfo | FundRealtimeRateInfo[]>(
    `/fund/realtime-rate/${codeParam}`
  )
}
```

**使用示例：**

**单只基金：**
```typescript
// 获取单只基金实时估算涨跌幅
const rateInfo = await fundApi.getFundRealtimeRate('161725')
console.log('估算涨跌幅:', rateInfo.data.estimate_change_pct)
```

**多只基金：**
```typescript
// 获取多只基金实时估算涨跌幅
const rateList = await fundApi.getFundRealtimeRate(['161725', '005827'])
rateList.data.forEach(fund => {
  console.log(`${fund.name}: ${fund.estimate_change_pct}%`)
})
```

---

### 3. 核心特点

#### 3.1 实时性
- **缓存时间：** 60 秒（实时数据）
- **估算时间：** 交易日 15:00 的估算值
- **数据来源：** 天天基金网

#### 3.2 灵活性
- **单只查询：** 精准查询单只基金
- **批量查询：** 一次请求获取多只基金数据
- **自动识别：** 根据参数自动判断单只或批量

#### 3.3 稳定性
- **频率控制：** 自适应延迟，降低风控风险
- **失败重试：** 带重试机制，提高成功率
- **异常处理：** 完善的错误处理和日志记录

---

## 使用场景

### 场景 1：单只基金实时监控
```typescript
// 实时监控单只基金的估算涨跌幅
const fund = await fundApi.getFundRealtimeRate('161725')
if (fund.data.estimate_change_pct > 2) {
  console.log('涨幅超过 2%，关注！')
}
```

### 场景 2：基金池批量监控
```typescript
// 批量监控基金池中的基金
const fundPool = ['161725', '005827', '005918']
const rates = await fundApi.getFundRealtimeRate(fundPool)

// 按涨跌幅排序
rates.data.sort((a, b) => b.estimate_change_pct - a.estimate_change_pct)
console.log('涨幅榜:', rates.data[0].name)
```

### 场景 3：基金对比分析
```typescript
// 对比多只同类基金的实时表现
const techFunds = ['005827', '005918', '001234']
const rates = await fundApi.getFundRealtimeRate(techFunds)

// 计算平均涨跌幅
const avgChange = rates.data.reduce((sum, f) => sum + f.estimate_change_pct, 0) / rates.data.length
console.log('科技基金平均估算涨幅:', avgChange.toFixed(2) + '%')
```

---

## 文件清单

### 后端文件
- ✅ `app/adapters/efinance_adapter.py` - 新增 `get_fund_realtime_increase_rate()` 方法
- ✅ `app/api/v1/endpoints/fund.py` - 新增 `/realtime-rate/{fund_codes}` 端点

### 前端文件
- ✅ `frontend/src/services/fund.ts` - 新增 `FundRealtimeRateInfo`、`getFundRealtimeRate()`

---

## 与历史净值 API 的对比

| 维度 | 实时估算涨跌幅 | 历史净值 |
|------|---------------|---------|
| **数据性质** | 实时估算（交易日 15:00） | 历史净值（每日公布） |
| **缓存时间** | 60 秒 | 10 分钟 |
| **核心字段** | estimate_change_pct（估算涨跌幅） | unit_nav（单位净值） |
| **典型场景** | 实时监控、盘中跟踪 | 历史分析、业绩对比 |
| **更新频率** | 交易日实时更新 | 每日更新一次 |

---

## 注意事项

### 1. 实时性说明
- **估算时间：** 仅在交易日 15:00 有估算值
- **非交易时间：** 返回最新净值的估算涨跌幅（可能与实际有偏差）
- **节假日：** 无实时更新，返回最近交易日数据

### 2. 数据准确性
- **估算值：** 基于基金持仓和实时股价估算，仅供参考
- **实际净值：** 以基金公司官方公布为准
- **误差范围：** 可能存在一定误差（特别是仓位变化较大的基金）

### 3. 使用建议
- **实时监控：** 推荐 60 秒刷新一次（缓存时间）
- **批量查询：** 推荐批量查询多只基金，减少请求次数
- **数据验证：** 重要决策请结合官方净值数据

---

## 测试建议

### 单元测试
```python
async def test_get_fund_realtime_increase_rate_single():
    """测试单只基金查询"""
    adapter = EFinanceAdapter()
    result = await adapter.get_fund_realtime_increase_rate('161725')
    assert result is not None
    assert result['code'] == '161725'
    assert 'estimate_change_pct' in result

async def test_get_fund_realtime_increase_rate_batch():
    """测试多只基金批量查询"""
    adapter = EFinanceAdapter()
    result = await adapter.get_fund_realtime_increase_rate(['161725', '005827'])
    assert isinstance(result, list)
    assert len(result) > 0
    assert all('estimate_change_pct' in item for item in result)
```

### 集成测试
```typescript
// 测试单只基金
test('获取单只基金实时估算涨跌幅', async () => {
  const { data } = await fundApi.getFundRealtimeRate('161725')
  expect(data.code).toBe('161725')
  expect(data.estimate_change_pct).toBeDefined()
})

// 测试多只基金
test('获取多只基金实时估算涨跌幅', async () => {
  const { data } = await fundApi.getFundRealtimeRate(['161725', '005827'])
  expect(Array.isArray(data)).toBe(true)
  expect(data.length).toBeGreaterThan(0)
})
```

---

## 总结

### 实施成果

✅ **功能完整** - 支持单只查询和批量查询  
✅ **实时性强** - 60 秒缓存，交易日实时更新  
✅ **数据准确** - 来源于天天基金网，基于实时股价估算  
✅ **使用灵活** - 可根据场景选择单只或批量查询  
✅ **性能优秀** - 批量查询效率高，风控概率低  

### 核心优势

- **实时监控** - 交易日 15:00 实时更新，跟踪基金表现
- **批量能力** - 一次请求获取多只基金估算数据
- **缓存优化** - 60 秒缓存，平衡实时性和性能
- **使用简单** - 一行代码即可查询

### 推荐使用策略

| 场景 | 推荐方法 | 原因 |
|------|---------|------|
| 单只基金监控 | `getFundRealtimeRate('code')` | 精准查询，实时性强 |
| 基金池监控 | `getFundRealtimeRate(['code1', 'code2'])` | 高效，一次请求获取多只数据 |
| 盘中跟踪 | 60 秒刷新一次 | 匹配缓存时间，避免频繁请求 |
| 历史分析 | 使用 `getFundHistory()` | 历史净值更准确 |

---

**实施完成时间：** 2026-03-18 19:30  
**实施者：** AI Assistant  
**测试状态：** ✅ 代码编译通过  
**部署状态：** 待部署  
**维护者：** Quant 团队
