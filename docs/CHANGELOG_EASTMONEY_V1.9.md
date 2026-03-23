# 东方财富模块更新日志 v1.9

## 版本信息
- **版本号**: v1.9
- **发布日期**: 2026-03-21
- **功能模块**: 股东人数及持股集中度

## 新增功能

### 1. 股东人数及持股集中度

#### 接口信息
- **接口名称**: stock_hold_num_cninfo
- **目标地址**: https://webapi.cninfo.com.cn/#/thematicStatistics
- **描述**: 巨潮资讯 - 数据中心 - 专题统计 - 股东股本 - 股东人数及持股集中度
- **限量**: 单次指定 date 的股东人数及持股集中度数据，从 20170331 开始

#### 输入参数
| 名称 | 类型 | 描述 |
|------|------|------|
| date | str | date="20210630"; choice of {"XXXX0331", "XXXX0630", "XXXX0930", "XXXX1231"}; 从 20170331 开始 |

#### 输出参数
| 名称 | 类型 | 描述 |
|------|------|------|
| 证劵代码 | object | - |
| 证券简称 | object | - |
| 变动日期 | object | - |
| 本期股东人数 | int64 | - |
| 上期股东人数 | float64 | - |
| 股东人数增幅 | float64 | 注意单位：% |
| 本期人均持股数量 | int64 | 注意单位：万股 |
| 上期人均持股数量 | float64 | 注意单位：万股 |
| 人均持股数量增幅 | float64 | 注意单位：% |

#### 接口示例
```python
import akshare as ak

stock_hold_num_cninfo_df = ak.stock_hold_num_cninfo(date="20210630")
print(stock_hold_num_cninfo_df)
```

#### 数据示例
```
    证券代码  证券简称    变动日期    本期股东人数  ... 股东人数增幅  本期人均持股数量  上期人均持股数量  人均持股数量增幅
0   002054  德美化工  2021-06-30   17768  ...   -8.71    27134.0     24771.0       9.54
1   002055  得润电子  2021-06-30   57449  ...   15.55     8242.0      9524.0     -13.46
2   002056  横店东磁  2021-06-30   94339  ...    8.63    17243.0     18927.0      -8.90
3   600048  保利发展  2021-06-30  264212  ...    5.63    45303.0     47855.0      -5.33
4   002057  中钢天源  2021-06-30   44197  ...   -3.58    16883.0     12550.0      34.53
...    ...   ...         ...     ...  ...     ...        ...         ...        ...
4203 600918  中泰证券  2021-06-30  152424  ...   11.38    45719.0     50923.0     -10.22
4204 601375  中原证券  2021-06-30  158626  ...    2.38    29269.0     29966.0      -2.33
4205 601108  财通证券  2021-06-30  158061  ...   -5.50    22706.0     21458.0       5.82
4206 002945  华林证券  2021-06-30   54407  ...  -11.32    49626.0     44008.0      12.77
4207 601066  中信建投  2021-06-30  201162  ...    1.18    38559.0     39013.0      -1.16
```

### 2. 后端实现

#### 数据模型
**文件**: `backend/app/models/unified_models.py`

新增 1 个数据模型：

```python
class StockHoldNumCNInfo(BaseModel):
    """股东人数及持股集中度数据模型"""
    security_code: str = Field(..., description="证券代码")
    security_abbr: str = Field(..., description="证券简称")
    change_date: str = Field(..., description="变动日期")
    current_holder_count: Optional[int] = Field(None, description="本期股东人数")
    previous_holder_count: Optional[float] = Field(None, description="上期股东人数")
    holder_count_growth: Optional[float] = Field(None, description="股东人数增幅（%）")
    current_avg_shares: Optional[int] = Field(None, description="本期人均持股数量（万股）")
    previous_avg_shares: Optional[float] = Field(None, description="上期人均持股数量（万股）")
    avg_shares_growth: Optional[float] = Field(None, description="人均持股数量增幅（%）")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")
```

#### 数据适配器
**文件**: `backend/app/adapters/eastmoney_adapter.py`

新增 1 个方法：

```python
async def get_stock_hold_num_cninfo(self, date: str) -> List[StockHoldNumCNInfo]:
    """获取股东人数及持股集中度"""
```

功能特性：
- 支持缓存（TTL 60 秒）
- 异步数据获取
- 完整的错误处理
- 自动数据类型转换
- 支持查询不同报告期数据

#### API 端点
**文件**: `backend/app/api/v1/endpoints/eastmoney.py`

新增 1 个端点：

```python
@router.get("/stock-hold-num-cninfo", response_model=ResponseModel[List[StockHoldNumCNInfo]])
async def get_stock_hold_num_cninfo(
    date: str = Query(..., description="报告期，格式 YYYYMMDD，如：20210630")
):
    """获取股东人数及持股集中度"""
```

**API 示例**:
```
# 获取 2021 年中报股东人数
GET /api/v1/eastmoney/stock-hold-num-cninfo?date=20210630

# 获取 2020 年报股东人数
GET /api/v1/eastmoney/stock-hold-num-cninfo?date=20201231

# 获取 2021 年三季报股东人数
GET /api/v1/eastmoney/stock-hold-num-cninfo?date=20210930
```

### 3. 前端实现

#### TypeScript 接口
**文件**: `frontend/src/services/eastmoney.ts`

新增 1 个接口：

```typescript
export interface StockHoldNumCNInfo {
  security_code: string;
  security_abbr: string;
  change_date: string;
  current_holder_count: number | null;
  previous_holder_count: number | null;
  holder_count_growth: number | null;
  current_avg_shares: number | null;
  previous_avg_shares: number | null;
  avg_shares_growth: number | null;
  extra_fields?: Record<string, any>;
}
```

#### API 服务
**文件**: `frontend/src/services/eastmoney.ts`

新增 1 个方法：

```typescript
getStockHoldNumCNInfo: (date: string) =>
  api.get<StockHoldNumCNInfo[]>(`/eastmoney/stock-hold-num-cninfo`, {
    params: { date }
  })
```

#### 股东人数页面
**文件**: `frontend/src/pages/StockHolderPage.tsx`

新功能：
- **报告期选择**: 支持选择不同报告期（一季报、中报、三季报、年报）
- **搜索功能**: 支持股票代码或简称搜索
- **统计数据卡片**: 4 个关键统计指标
  - 平均股东人数
  - 平均增幅
  - 股东增加公司数
  - 股东减少公司数
- **数据表格**: 展示 9 个详细指标
  - 证券代码、证券简称、变动日期
  - 本期股东人数、上期股东人数
  - 股东人数增幅（%）
  - 本期人均持股、上期人均持股
  - 人均持股增幅（%）
- **数据说明**: 详细的数据说明和分析意义

#### 路由配置
**文件**: `frontend/src/App.tsx`

新增路由：
```typescript
<Route path="eastmoney/stock-holder" element={<StockHolderPage />} />
```

## 技术架构

### 后端技术
- **框架**: FastAPI
- **数据验证**: Pydantic
- **异步处理**: AsyncIO
- **数据源**: 巨潮资讯（CNINFO）
- **缓存**: 内存缓存（TTL 60 秒）
- **日志**: Loguru

### 前端技术
- **框架**: React 18
- **语言**: TypeScript
- **UI 库**: Chakra UI
- **HTTP 客户端**: Axios
- **状态管理**: React Hooks

### 数据流程
```
用户请求 → 前端 API 服务 → FastAPI 端点 → EastMoneyAdapter → AKShare → 巨潮资讯
                                              ↓
                                          缓存层（60 秒）
                                              ↓
                                          数据模型验证
                                              ↓
                                          返回 JSON 响应
```

## 使用示例

### 后端 API 调用

**Python 示例**:
```python
import requests

# 获取 2021 年中报股东人数
response = requests.get(
    "http://localhost:8000/api/v1/eastmoney/stock-hold-num-cninfo",
    params={"date": "20210630"}
)
data = response.json()
print(data)

# 获取 2020 年报股东人数
response = requests.get(
    "http://localhost:8000/api/v1/eastmoney/stock-hold-num-cninfo",
    params={"date": "20201231"}
)
data = response.json()
print(data)
```

### 前端页面访问

访问地址：`http://localhost:3000/eastmoney/stock-holder`

**功能操作**:
1. 输入报告期（如：20210630）
2. 点击"查询"按钮
3. 查看统计数据卡片
4. 使用搜索框搜索特定股票
5. 查看详细数据表格

## 数据更新频率

- **更新来源**: 巨潮资讯数据服务平台
- **更新时间**: 随上市公司定期报告更新
- **数据范围**: 从 20170331 开始至今
- **报告期类型**:
  - XXXX0331：第一季度报告
  - XXXX0630：半年度报告
  - XXXX0930：第三季度报告
  - XXXX1231：年度报告

## 注意事项

1. **报告期格式**: YYYYMMDD（如：20210630）

2. **可选报告期**:
   - 0331：第一季度（一季报）
   - 0630：第二季度（中报）
   - 0930：第三季度（三季报）
   - 1231：第四季度（年报）

3. **数据单位**:
   - 股东人数：人
   - 人均持股数量：万股
   - 增幅：百分比（%）

4. **分析意义**:
   - **股东人数增加**: 筹码分散，通常视为利空信号
   - **股东人数减少**: 筹码集中，通常视为利好信号
   - **人均持股增加**: 说明筹码趋向集中，主力可能在收集筹码
   - **人均持股减少**: 说明筹码趋向分散，主力可能在派发筹码

5. **缓存时间**: 60 秒，相同请求在 60 秒内会返回缓存数据

6. **数据限制**: 只能获取从 20170331 开始的数据

## 性能优化

1. **缓存机制**: 60 秒 TTL 缓存，减少重复请求
2. **异步处理**: 使用 asyncio 异步获取数据，不阻塞主线程
3. **数据分页**: 前端表格默认展示前 100 条数据，避免一次性渲染过多数据
4. **搜索优化**: 前端搜索过滤，实时响应
5. **统计计算**: 前端实时计算统计数据，减少后端压力

## 后续规划

- [ ] 添加股东人数历史趋势图表
- [ ] 支持个股股东人数变化追踪
- [ ] 添加股东人数与股价走势对比
- [ ] 支持导出 Excel/CSV 功能
- [ ] 添加筹码集中度分析

## 相关文件清单

### 后端文件
- `backend/app/models/unified_models.py` - 数据模型定义（新增 1 个模型）
- `backend/app/adapters/eastmoney_adapter.py` - 数据适配器（新增 1 个方法）
- `backend/app/api/v1/endpoints/eastmoney.py` - API 端点（新增 1 个端点）

### 前端文件
- `frontend/src/services/eastmoney.ts` - API 服务（新增 1 个接口和 1 个方法）
- `frontend/src/pages/StockHolderPage.tsx` - 股东人数页面（新建）
- `frontend/src/App.tsx` - 路由配置（新增 1 个路由）

## 测试建议

### 后端测试
```bash
# 测试 2021 年中报股东人数
curl "http://localhost:8000/api/v1/eastmoney/stock-hold-num-cninfo?date=20210630"

# 测试 2020 年报股东人数
curl "http://localhost:8000/api/v1/eastmoney/stock-hold-num-cninfo?date=20201231"

# 测试 2021 年三季报股东人数
curl "http://localhost:8000/api/v1/eastmoney/stock-hold-num-cninfo?date=20210930"
```

### 前端测试
1. 访问股东人数页面
2. 测试不同报告期查询
3. 测试搜索功能
4. 测试统计数据展示
5. 测试数据表格展示
6. 测试增幅颜色标识（红绿）

## 版本历史

- **v1.0**: 盘口异动和涨停板行情
- **v1.1**: 涨停股池详细功能
- **v1.2**: 千股千评功能
- **v1.3**: 研报公告功能
- **v1.4**: 资产负债表功能
- **v1.5**: 利润表和现金流量表功能
- **v1.6**: 新浪财经财务指标功能
- **v1.7**: 股票列表功能（沪深京）
- **v1.8**: 行业分类与市盈率功能
- **v1.9**: 股东人数及持股集中度功能（当前版本）

## 联系方式

如有问题或建议，请联系开发团队。
