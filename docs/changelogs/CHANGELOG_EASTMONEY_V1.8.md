# 东方财富模块更新日志 v1.8

## 版本信息
- **版本号**: v1.8
- **发布日期**: 2026-03-21
- **功能模块**: 行业分类与市盈率

## 新增功能

### 1. 申万行业分类变动历史

#### 接口信息
- **接口名称**: stock_industry_clf_hist_sw
- **目标地址**: http://www.swhyresearch.com/institute_sw/allIndex/downloadCenter/industryType
- **描述**: 申万宏源研究 - 行业分类 - 全部行业分类
- **限量**: 单次获取所有个股的行业分类变动历史数据

#### 输入参数
| 名称 | 类型 | 描述 |
|------|------|------|
| - | - | - |

#### 输出参数
| 名称 | 类型 | 描述 |
|------|------|------|
| symbol | object | 股票代码 |
| start_date | object | 计入日期 |
| industry_code | object | 申万行业代码 |
| update_time | object | 更新日期 |

#### 接口示例
```python
import akshare as ak

stock_industry_clf_hist_sw_df = ak.stock_industry_clf_hist_sw()
print(stock_industry_clf_hist_sw_df)
```

#### 数据示例
```
   symbol  start_date industry_code update_time
0  000001  1991-04-03        440101  2015-10-27
1  000001  2014-01-01        480101  2015-10-27
2  000001  2021-07-30        480301  2021-07-31
3  000002  1991-01-29        430101  2015-10-27
4  000003  1991-04-14        510101  2015-10-27
...     ...         ...           ...         ...
12360 873706  2024-03-12        640601  2024-03-13
12361 873726  2023-10-30        640209  2023-10-30
12362 873806  2024-01-17        710301  2024-01-17
12363 873833  2023-11-20        640106  2023-11-20
12364 874090  2023-08-21        370304  2023-08-21
```

### 2. 行业市盈率

#### 接口信息
- **接口名称**: stock_industry_pe_ratio_cninfo
- **目标地址**: http://webapi.cninfo.com.cn/#/thematicStatistics
- **描述**: 巨潮资讯 - 数据中心 - 行业分析 - 行业市盈率
- **限量**: 单次获取指定 symbol 在指定交易日的所有数据；只能获取近期的数据

#### 输入参数
| 名称 | 类型 | 描述 |
|------|------|------|
| symbol | str | symbol="证监会行业分类"; choice of {"证监会行业分类", "国证行业分类"} |
| date | str | date="20210910"; 交易日 |

#### 输出参数
| 名称 | 类型 | 描述 |
|------|------|------|
| 变动日期 | object | - |
| 行业分类 | object | - |
| 行业层级 | int64 | - |
| 行业编码 | object | - |
| 行业名称 | object | - |
| 公司数量 | float64 | - |
| 纳入计算公司数量 | float64 | - |
| 总市值 - 静态 | float64 | 注意单位：亿元 |
| 净利润 - 静态 | float64 | 注意单位：亿元 |
| 静态市盈率 - 加权平均 | float64 | - |
| 静态市盈率 - 中位数 | float64 | - |
| 静态市盈率 - 算术平均 | float64 | - |

#### 接口示例
```python
import akshare as ak

stock_industry_pe_ratio_cninfo_df = ak.stock_industry_pe_ratio_cninfo(
    symbol="国证行业分类", 
    date="20240617"
)
print(stock_industry_pe_ratio_cninfo_df)
```

#### 数据示例
```
    变动日期        行业分类      行业层级  ... 静态市盈率 - 加权平均  静态市盈率 - 中位数  静态市盈率 - 算术平均
0   2024-06-17  国证行业分类标准 2019     1  ...        11.54        15.75         49.19
1   2024-06-17  国证行业分类标准 2019     2  ...        11.54        15.75         49.19
2   2024-06-17  国证行业分类标准 2019     3  ...        18.44        22.05         28.24
3   2024-06-17  国证行业分类标准 2019     4  ...        19.23        21.45         30.02
4   2024-06-17  国证行业分类标准 2019     4  ...        18.10        24.86         25.35
..         ...             ...   ...  ...          ...          ...           ...
288 2024-06-17  国证行业分类标准 2019     4  ...         NaN          NaN           NaN
289 2024-06-17  国证行业分类标准 2019     3  ...        19.59        22.28         43.17
290 2024-06-17  国证行业分类标准 2019     4  ...        19.59        22.28         43.17
291 2024-06-17  国证行业分类标准 2019     3  ...        14.12        14.12         14.12
292 2024-06-17  国证行业分类标准 2019     4  ...        14.12        14.12         14.12
```

### 3. 后端实现

#### 数据模型
**文件**: `backend/app/models/unified_models.py`

新增 2 个数据模型：

```python
class StockIndustryClfHistSW(BaseModel):
    """申万行业分类变动历史数据模型"""
    symbol: str = Field(..., description="股票代码")
    start_date: str = Field(..., description="计入日期")
    industry_code: str = Field(..., description="申万行业代码")
    update_time: str = Field(..., description="更新日期")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")

class StockIndustryPERatio(BaseModel):
    """行业市盈率数据模型"""
    change_date: str = Field(..., description="变动日期")
    industry_class: str = Field(..., description="行业分类")
    industry_level: int = Field(..., description="行业层级")
    industry_code: str = Field(..., description="行业编码")
    industry_name: str = Field(..., description="行业名称")
    company_count: Optional[float] = Field(None, description="公司数量")
    calc_company_count: Optional[float] = Field(None, description="纳入计算公司数量")
    total_market_cap: Optional[float] = Field(None, description="总市值 - 静态（亿元）")
    net_profit: Optional[float] = Field(None, description="净利润 - 静态（亿元）")
    pe_static_weighted: Optional[float] = Field(None, description="静态市盈率 - 加权平均")
    pe_static_median: Optional[float] = Field(None, description="静态市盈率 - 中位数")
    pe_static_arithmetic: Optional[float] = Field(None, description="静态市盈率 - 算术平均")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")
```

#### 数据适配器
**文件**: `backend/app/adapters/eastmoney_adapter.py`

新增 2 个方法：

```python
async def get_stock_industry_clf_hist_sw(self) -> List[StockIndustryClfHistSW]:
    """获取申万行业分类变动历史"""

async def get_stock_industry_pe_ratio_cninfo(
    self, 
    symbol: str = "国证行业分类", 
    date: str = None
) -> List[StockIndustryPERatio]:
    """获取行业市盈率"""
```

功能特性：
- 支持缓存（TTL 60 秒）
- 异步数据获取
- 完整的错误处理
- 自动数据类型转换
- 支持指定日期查询（行业市盈率）

#### API 端点
**文件**: `backend/app/api/v1/endpoints/eastmoney.py`

新增 2 个端点：

```python
@router.get("/stock-industry-clf-hist-sw", response_model=ResponseModel[List[StockIndustryClfHistSW]])
async def get_stock_industry_clf_hist_sw():
    """获取申万行业分类变动历史"""

@router.get("/stock-industry-pe-ratio/{symbol}", response_model=ResponseModel[List[StockIndustryPERatio]])
async def get_stock_industry_pe_ratio(
    symbol: str = Path(..., description="行业分类类型"),
    date: Optional[str] = Query(None, description="交易日，格式 YYYYMMDD")
):
    """获取行业市盈率"""
```

**API 示例**:
```
# 获取申万行业分类变动历史
GET /api/v1/eastmoney/stock-industry-clf-hist-sw

# 获取国证行业分类市盈率（最近日期）
GET /api/v1/eastmoney/stock-industry-pe-ratio/国证行业分类

# 获取指定日期的市盈率数据
GET /api/v1/eastmoney/stock-industry-pe-ratio/国证行业分类?date=20240617

# 获取证监会行业分类市盈率
GET /api/v1/eastmoney/stock-industry-pe-ratio/证监会行业分类
```

### 4. 前端实现

#### TypeScript 接口
**文件**: `frontend/src/services/eastmoney.ts`

新增 2 个接口：

```typescript
export interface StockIndustryClfHistSW {
  symbol: string;
  start_date: string;
  industry_code: string;
  update_time: string;
  extra_fields?: Record<string, any>;
}

export interface StockIndustryPERatio {
  change_date: string;
  industry_class: string;
  industry_level: number;
  industry_code: string;
  industry_name: string;
  company_count: number | null;
  calc_company_count: number | null;
  total_market_cap: number | null;
  net_profit: number | null;
  pe_static_weighted: number | null;
  pe_static_median: number | null;
  pe_static_arithmetic: number | null;
  extra_fields?: Record<string, any>;
}
```

#### API 服务
**文件**: `frontend/src/services/eastmoney.ts`

新增 2 个方法：

```typescript
getStockIndustryClfHistSW: () =>
  api.get<StockIndustryClfHistSW[]>('/eastmoney/stock-industry-clf-hist-sw'),

getStockIndustryPERatio: (symbol: string, date?: string) =>
  api.get<StockIndustryPERatio[]>(
    `/eastmoney/stock-industry-pe-ratio/${encodeURIComponent(symbol)}`,
    { params: { date } }
  )
```

#### 行业分类页面
**文件**: `frontend/src/pages/IndustryClassificationPage.tsx`

新功能：
- **2 个 Tab 面板**: 
  - 申万行业分类变动历史
  - 行业市盈率
- **搜索功能**: 支持股票代码、行业名称或代码搜索
- **行业分类选择**: 支持选择证监会行业分类或国证行业分类
- **日期选择**: 支持指定交易日查询市盈率数据
- **数据展示**: 
  - 申万行业分类：股票代码、计入日期、行业代码、更新日期
  - 行业市盈率：12 个详细指标（变动日期、行业名称、公司数量、总市值、净利润、三种市盈率等）
- **数据说明**: 详细的数据说明和使用指南

#### 路由配置
**文件**: `frontend/src/App.tsx`

新增路由：
```typescript
<Route path="eastmoney/industry-classification" element={<IndustryClassificationPage />} />
```

## 技术架构

### 后端技术
- **框架**: FastAPI
- **数据验证**: Pydantic
- **异步处理**: AsyncIO
- **数据源**: 
  - 申万宏源研究（行业分类）
  - 巨潮资讯（行业市盈率）
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
用户请求 → 前端 API 服务 → FastAPI 端点 → EastMoneyAdapter → AKShare → 数据源
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

# 获取申万行业分类变动历史
response = requests.get("http://localhost:8000/api/v1/eastmoney/stock-industry-clf-hist-sw")
data = response.json()
print(data)

# 获取国证行业分类市盈率（最近日期）
response = requests.get(
    "http://localhost:8000/api/v1/eastmoney/stock-industry-pe-ratio/国证行业分类"
)
data = response.json()
print(data)

# 获取指定日期的市盈率数据
response = requests.get(
    "http://localhost:8000/api/v1/eastmoney/stock-industry-pe-ratio/国证行业分类",
    params={"date": "20240617"}
)
data = response.json()
print(data)
```

### 前端页面访问

访问地址：`http://localhost:3000/eastmoney/industry-classification`

**功能操作**:
1. 切换 Tab 查看不同功能
2. 使用搜索框搜索股票代码、行业名称或代码
3. 在行业市盈率 Tab 选择行业分类类型（证监会/国证）
4. 输入日期查询历史市盈率数据
5. 查看详细的行业指标数据

## 数据更新频率

- **申万行业分类**: 随申万宏源研究发布的行业分类更新
- **行业市盈率**: 随交易日更新，只能获取近期数据
- **数据来源**: 
  - 申万宏源研究官方网站
  - 巨潮资讯数据中心

## 注意事项

1. **行业分类类型**:
   - 证监会行业分类：中国证监会发布的行业分类标准
   - 国证行业分类：国证指数公司发布的行业分类标准

2. **日期格式**: YYYYMMDD（如：20240617）

3. **数据单位**:
   - 总市值：亿元
   - 净利润：亿元
   - 市盈率：倍数

4. **市盈率类型**:
   - 静态市盈率 - 加权平均：按市值加权平均计算
   - 静态市盈率 - 中位数：行业市盈率中位数
   - 静态市盈率 - 算术平均：简单算术平均计算

5. **缓存时间**: 60 秒，相同请求在 60 秒内会返回缓存数据

6. **数据限制**: 行业市盈率数据只能获取近期数据，无法获取历史太久远的数据

## 性能优化

1. **缓存机制**: 60 秒 TTL 缓存，减少重复请求
2. **异步处理**: 使用 asyncio 异步获取数据，不阻塞主线程
3. **数据分页**: 前端表格默认展示前 100 条数据，避免一次性渲染过多数据
4. **按需加载**: Tab 面板按需渲染，提升页面性能
5. **搜索优化**: 前端搜索过滤，实时响应

## 后续规划

- [ ] 添加行业分类树形结构展示
- [ ] 支持行业市盈率历史趋势图表
- [ ] 添加行业对比分析功能
- [ ] 支持导出 Excel/CSV 功能
- [ ] 添加行业轮动分析

## 相关文件清单

### 后端文件
- `backend/app/models/unified_models.py` - 数据模型定义（新增 2 个模型）
- `backend/app/adapters/eastmoney_adapter.py` - 数据适配器（新增 2 个方法）
- `backend/app/api/v1/endpoints/eastmoney.py` - API 端点（新增 2 个端点）

### 前端文件
- `frontend/src/services/eastmoney.ts` - API 服务（新增 2 个接口和 2 个方法）
- `frontend/src/pages/IndustryClassificationPage.tsx` - 行业分类页面（新建）
- `frontend/src/App.tsx` - 路由配置（新增 1 个路由）

## 测试建议

### 后端测试
```bash
# 测试申万行业分类变动历史
curl "http://localhost:8000/api/v1/eastmoney/stock-industry-clf-hist-sw"

# 测试行业市盈率（国证行业分类，最近日期）
curl "http://localhost:8000/api/v1/eastmoney/stock-industry-pe-ratio/国证行业分类"

# 测试行业市盈率（指定日期）
curl "http://localhost:8000/api/v1/eastmoney/stock-industry-pe-ratio/国证行业分类?date=20240617"

# 测试证监会行业分类市盈率
curl "http://localhost:8000/api/v1/eastmoney/stock-industry-pe-ratio/证监会行业分类"
```

### 前端测试
1. 访问行业分类页面
2. 测试 2 个 Tab 切换
3. 测试搜索功能
4. 测试行业分类选择
5. 测试日期查询功能
6. 测试数据展示完整性

## 版本历史

- **v1.0**: 盘口异动和涨停板行情
- **v1.1**: 涨停股池详细功能
- **v1.2**: 千股千评功能
- **v1.3**: 研报公告功能
- **v1.4**: 资产负债表功能
- **v1.5**: 利润表和现金流量表功能
- **v1.6**: 新浪财经财务指标功能
- **v1.7**: 股票列表功能（沪深京）
- **v1.8**: 行业分类与市盈率功能（当前版本）

## 联系方式

如有问题或建议，请联系开发团队。
