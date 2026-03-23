# 东方财富模块更新日志 v1.7

## 版本信息
- **版本号**: v1.7
- **发布日期**: 2026-03-21
- **功能模块**: 股票列表（沪深京）

## 新增功能

### 1. 股票列表 API

#### 1.1 沪深京 A 股股票列表

**接口信息**
- **接口名称**: stock_info_a_code_name
- **数据源**: 沪深京三个交易所
- **描述**: 沪深京 A 股股票代码和股票简称数据
- **限量**: 单次获取所有 A 股股票代码和简称数据

**输入参数**
| 名称 | 类型 | 描述 |
|------|------|------|
| - | - | - |

**输出参数**
| 名称 | 类型 | 描述 |
|------|------|------|
| code | object | 股票代码 |
| name | object | 股票简称 |

**接口示例**
```python
import akshare as ak

stock_info_a_code_name_df = ak.stock_info_a_code_name()
print(stock_info_a_code_name_df)
```

**数据示例**
```
    code    name
0   000001  平安银行
1   000002  万  科 A
2   000004  国华网安
3   000005  ST 星源
4   000006  深振业 A
      ...    ...
4623 871396  常辅股份
4624 871553  凯腾精工
4625 871642  通易航天
4626 871981  晶赛科技
4627 872925  锦好医疗
```

#### 1.2 上海证券交易所股票列表

**接口信息**
- **接口名称**: stock_info_sh_name_code
- **目标地址**: https://www.sse.com.cn/assortment/stock/list/share/
- **描述**: 上海证券交易所股票代码和简称数据
- **限量**: 单次获取所有上海证券交易所股票代码和简称数据

**输入参数**
| 名称 | 类型 | 描述 |
|------|------|------|
| symbol | str | symbol="主板 A 股"; choice of {"主板 A 股", "主板 B 股", "科创板"} |

**输出参数**
| 名称 | 类型 | 描述 |
|------|------|------|
| 证券代码 | object | - |
| 证券简称 | object | - |
| 公司全称 | object | - |
| 上市日期 | object | - |

**接口示例**
```python
import akshare as ak

stock_info_sh_name_code_df = ak.stock_info_sh_name_code(symbol="主板 A 股")
print(stock_info_sh_name_code_df)
```

**数据示例**
```
    证券代码  证券简称      公司全称           上市日期
0   600000  浦发银行  上海浦东发展银行股份有限公司  1999-11-10
1   600004  白云机场  广州白云国际机场股份有限公司  2003-04-28
2   600006  东风汽车  东风汽车股份有限公司      1999-07-27
3   600007  中国国贸  中国国际贸易中心股份有限公司  1999-03-12
4   600008  首创环保  北京首创生态环保集团股份  2000-04-27
      ...   ...         ...         ...
1691 605580  恒盛能源  恒盛能源股份有限公司    2021-08-19
1692 605588  冠石科技  南京冠石科技股份有限公司  2021-08-12
1693 605589  圣泉集团  济南圣泉集团股份有限公司  2021-08-10
1694 605598  上海港湾  上海港湾基础建设 (集团)  2021-09-17
1695 605599  菜百股份  北京菜市口百货股份有限公司  2021-09-09
```

#### 1.3 深圳证券交易所股票列表

**接口信息**
- **接口名称**: stock_info_sz_name_code
- **目标地址**: https://www.szse.cn/market/product/stock/list/index.html
- **描述**: 深证证券交易所股票代码和股票简称数据
- **限量**: 单次获取深证证券交易所股票代码和简称数据

**输入参数**
| 名称 | 类型 | 描述 |
|------|------|------|
| symbol | str | symbol="A 股列表"; choice of {"A 股列表", "B 股列表", "CDR 列表", "AB 股列表"} |

**输出参数-A 股列表**
| 名称 | 类型 | 描述 |
|------|------|------|
| 板块 | object | - |
| A 股代码 | object | - |
| A 股简称 | object | - |
| A 股上市日期 | object | - |
| A 股总股本 | object | - |
| A 股流通股本 | object | - |
| 所属行业 | object | - |

**接口示例**
```python
import akshare as ak

stock_info_sz_name_code_df = ak.stock_info_sz_name_code(symbol="A 股列表")
print(stock_info_sz_name_code_df)
```

**数据示例**
```
    板块   A 股代码  A 股简称   A 股上市日期    A 股总股本      A 股流通股本    所属行业
0   主板  000001   平安银行  1991-04-03  19,405,918,198  19,405,513,424  J 金融业
1   主板  000002  万  科 A  1991-01-29   9,724,196,533   9,716,935,865  K 房地产
2   主板  000004   国华网安  1990-12-01     132,380,282     126,288,093  I 信息技术
3   主板  000005   ST 星源  1990-12-10   1,058,536,842   1,057,875,742  N 公共环保
4   主板  000006   深振业 A  1992-04-27   1,349,995,046   1,349,987,396  K 房地产
   ...     ...    ...         ...             ...             ...     ...
2838 创业板  301568    思泰克  2023-11-28     103,258,400      24,487,502  C 制造业
2839 创业板  301577   美信科技  2024-01-24      44,260,000      11,095,149  C 制造业
2840 创业板  301578   辰奕智能  2023-12-28      48,000,000      11,378,776  C 制造业
2841 创业板  301589   诺瓦星云  2024-02-08      51,360,000       7,702,090  C 制造业
2842 创业板  301591  C 肯特股份  2024-02-28      84,120,000      19,943,633  C 制造业
```

#### 1.4 北京证券交易所股票列表

**接口信息**
- **接口名称**: stock_info_bj_name_code
- **目标地址**: https://www.bse.cn/nq/listedcompany.html
- **描述**: 北京证券交易所股票代码和简称数据
- **限量**: 单次获取北京证券交易所所有的股票代码和简称数据

**输入参数**
| 名称 | 类型 | 描述 |
|------|------|------|
| - | - | - |

**输出参数**
| 名称 | 类型 | 描述 |
|------|------|------|
| 证券代码 | object | - |
| 证券简称 | object | - |
| 总股本 | int64 | 注意单位：股 |
| 流通股本 | int64 | 注意单位：股 |
| 上市日期 | object | - |
| 所属行业 | object | - |
| 地区 | object | - |
| 报告日期 | object | - |

**接口示例**
```python
import akshare as ak

stock_info_bj_name_code_df = ak.stock_info_bj_name_code()
print(stock_info_bj_name_code_df)
```

**数据示例**
```
    证券代码  证券简称    总股本   ...   所属行业   地区    报告日期
0   430017  星昊医药  122577200  ...  医药制造业  北京市  2024-02-29
1   430047  诺思兰德  274873974  ...  医药制造业  北京市  2024-02-29
2   430090  同辉信息  199333546  ...  软件和信息  北京市  2024-02-29
3   430139  华岭股份  266800000  ...  计算机通信  上海市  2024-02-29
4   430198  微创光电  161363872  ...  计算机通信  湖北省  2024-02-29
..    ...   ...      ...  ...     ...   ...       ...
239 873693   阿为特   72700000  ...  金属制品业  上海市  2024-02-29
240 873703  广厦环能   76900000  ...  专用设备业  北京市  2024-02-29
241 873726  卓兆点胶   82077246  ...  专用设备业  江苏省  2024-02-29
242 873806   云星宇  300736667  ...  软件和信息  北京市  2024-02-29
243 873833  美心翼申   82360000  ...  通用设备业  重庆市  2024-02-29
```

### 2. 后端实现

#### 数据模型
**文件**: `backend/app/models/unified_models.py`

新增 4 个数据模型：

```python
class StockInfoA(BaseModel):
    """沪深京 A 股股票列表数据模型"""
    code: str = Field(..., description="股票代码")
    name: str = Field(..., description="股票简称")

class StockInfoSH(BaseModel):
    """上海证券交易所股票列表数据模型"""
    security_code: str = Field(..., description="证券代码")
    security_abbr: str = Field(..., description="证券简称")
    company_name: str = Field(..., description="公司全称")
    list_date: str = Field(..., description="上市日期")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")

class StockInfoSZ(BaseModel):
    """深圳证券交易所股票列表数据模型"""
    board: str = Field(..., description="板块")
    stock_code: str = Field(..., description="A 股代码")
    stock_abbr: str = Field(..., description="A 股简称")
    list_date: str = Field(..., description="A 股上市日期")
    total_shares: int = Field(None, description="A 股总股本")
    circulating_shares: int = Field(None, description="A 股流通股本")
    industry: str = Field(..., description="所属行业")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")

class StockInfoBJ(BaseModel):
    """北京证券交易所股票列表数据模型"""
    security_code: str = Field(..., description="证券代码")
    security_abbr: str = Field(..., description="证券简称")
    total_shares: int = Field(..., description="总股本")
    circulating_shares: int = Field(..., description="流通股本")
    list_date: str = Field(..., description="上市日期")
    industry: str = Field(..., description="所属行业")
    region: str = Field(..., description="地区")
    report_date: str = Field(..., description="报告日期")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")
```

#### 数据适配器
**文件**: `backend/app/adapters/eastmoney_adapter.py`

新增 4 个方法：

```python
async def get_stock_info_a_code_name(self) -> List[StockInfoA]:
    """获取沪深京 A 股股票列表"""

async def get_stock_info_sh_name_code(self, symbol: str = "主板 A 股") -> List[StockInfoSH]:
    """获取上海证券交易所股票列表"""

async def get_stock_info_sz_name_code(self, symbol: str = "A 股列表") -> List[StockInfoSZ]:
    """获取深圳证券交易所股票列表"""

async def get_stock_info_bj_name_code(self) -> List[StockInfoBJ]:
    """获取北京证券交易所股票列表"""
```

功能特性：
- 支持缓存（TTL 60 秒）
- 异步数据获取
- 完整的错误处理
- 自动数据类型转换

#### API 端点
**文件**: `backend/app/api/v1/endpoints/eastmoney.py`

新增 4 个端点：

```python
@router.get("/stock-info-a", response_model=ResponseModel[List[StockInfoA]])
async def get_stock_info_a():
    """获取沪深京 A 股股票列表"""

@router.get("/stock-info-sh/{symbol}", response_model=ResponseModel[List[StockInfoSH]])
async def get_stock_info_sh(symbol: str = Path(..., description="板块类型")):
    """获取上海证券交易所股票列表"""

@router.get("/stock-info-sz/{symbol}", response_model=ResponseModel[List[StockInfoSZ]])
async def get_stock_info_sz(symbol: str = Path(..., description="板块类型")):
    """获取深圳证券交易所股票列表"""

@router.get("/stock-info-bj", response_model=ResponseModel[List[StockInfoBJ]])
async def get_stock_info_bj():
    """获取北京证券交易所股票列表"""
```

**API 示例**:
```
# 获取沪深京 A 股列表
GET /api/v1/eastmoney/stock-info-a

# 获取上海证券交易所主板 A 股
GET /api/v1/eastmoney/stock-info-sh/主板 A 股

# 获取上海证券交易所科创板
GET /api/v1/eastmoney/stock-info-sh/科创板

# 获取深圳证券交易所 A 股
GET /api/v1/eastmoney/stock-info-sz/A 股列表

# 获取北京证券交易所股票
GET /api/v1/eastmoney/stock-info-bj
```

### 3. 前端实现

#### TypeScript 接口
**文件**: `frontend/src/services/eastmoney.ts`

新增 4 个接口：

```typescript
export interface StockInfoA {
  code: string;
  name: string;
}

export interface StockInfoSH {
  security_code: string;
  security_abbr: string;
  company_name: string;
  list_date: string;
  extra_fields?: Record<string, any>;
}

export interface StockInfoSZ {
  board: string;
  stock_code: string;
  stock_abbr: string;
  list_date: string;
  total_shares: number | null;
  circulating_shares: number | null;
  industry: string;
  extra_fields?: Record<string, any>;
}

export interface StockInfoBJ {
  security_code: string;
  security_abbr: string;
  total_shares: number;
  circulating_shares: number;
  list_date: string;
  industry: string;
  region: string;
  report_date: string;
  extra_fields?: Record<string, any>;
}
```

#### API 服务
**文件**: `frontend/src/services/eastmoney.ts`

新增 4 个方法：

```typescript
getStockInfoA: () =>
  api.get<StockInfoA[]>('/eastmoney/stock-info-a'),

getStockInfoSH: (symbol: string = '主板 A 股') =>
  api.get<StockInfoSH[]>(`/eastmoney/stock-info-sh/${encodeURIComponent(symbol)}`),

getStockInfoSZ: (symbol: string = 'A 股列表') =>
  api.get<StockInfoSZ[]>(`/eastmoney/stock-info-sz/${encodeURIComponent(symbol)}`),

getStockInfoBJ: () =>
  api.get<StockInfoBJ[]>('/eastmoney/stock-info-bj')
```

#### 股票列表页面
**文件**: `frontend/src/pages/StockListPage.tsx`

新功能：
- **4 个 Tab 面板**: 分类展示不同交易所的股票列表
  - 沪深京 A 股
  - 上海证券交易所
  - 深圳证券交易所
  - 北京证券交易所
- **搜索功能**: 支持股票代码或简称搜索
- **板块选择**: 支持选择不同板块（主板、科创板、创业板等）
- **分页展示**: 每个表格默认展示前 100 条数据
- **数据说明**: 详细的数据说明和使用指南

#### 路由配置
**文件**: `frontend/src/App.tsx`

新增路由：
```typescript
<Route path="eastmoney/stock-list" element={<StockListPage />} />
```

## 技术架构

### 后端技术
- **框架**: FastAPI
- **数据验证**: Pydantic
- **异步处理**: AsyncIO
- **数据源**: AKShare
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
用户请求 → 前端 API 服务 → FastAPI 端点 → EastMoneyAdapter → AKShare → 交易所官网
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

# 获取沪深京 A 股列表
response = requests.get("http://localhost:8000/api/v1/eastmoney/stock-info-a")
data = response.json()
print(data)

# 获取上海证券交易所科创板
response = requests.get("http://localhost:8000/api/v1/eastmoney/stock-info-sh/科创板")
data = response.json()
print(data)

# 获取深圳证券交易所 A 股
response = requests.get("http://localhost:8000/api/v1/eastmoney/stock-info-sz/A 股列表")
data = response.json()
print(data)

# 获取北京证券交易所股票
response = requests.get("http://localhost:8000/api/v1/eastmoney/stock-info-bj")
data = response.json()
print(data)
```

### 前端页面访问

访问地址：`http://localhost:3000/eastmoney/stock-list`

**功能操作**:
1. 切换 Tab 查看不同交易所的股票列表
2. 使用搜索框搜索股票代码或简称
3. 选择不同板块查看对应股票列表
4. 查看股票详细信息（代码、简称、上市日期等）

## 数据更新频率

- **更新来源**: 上海证券交易所、深圳证券交易所、北京证券交易所官方网站
- **更新时间**: 随交易所公告实时更新
- **数据范围**: 包含所有在交易所上市的 A 股股票

## 注意事项

1. **股票代码**: 
   - 上交所：6 位数字（600xxx、601xxx、603xxx、605xxx、688xxx）
   - 深交所：6 位数字（000xxx、001xxx、002xxx、003xxx、300xxx、301xxx）
   - 北交所：6 位数字（43xxxx、83xxxx、87xxxx 等）

2. **板块类型**:
   - 上交所：主板 A 股、主板 B 股、科创板
   - 深交所：A 股列表、B 股列表、CDR 列表、AB 股列表
   - 北交所：全部

3. **数据单位**:
   - 股本数据：股

4. **缓存时间**: 60 秒，相同请求在 60 秒内会返回缓存数据

5. **性能优化**: 前端表格默认展示前 100 条数据，避免一次性渲染过多数据

## 性能优化

1. **缓存机制**: 60 秒 TTL 缓存，减少重复请求
2. **异步处理**: 使用 asyncio 异步获取数据，不阻塞主线程
3. **数据分页**: 前端表格默认展示前 100 条数据，避免一次性渲染过多数据
4. **按需加载**: Tab 面板按需渲染，提升页面性能
5. **搜索优化**: 前端搜索过滤，实时响应

## 后续规划

- [ ] 添加股票详情页面
- [ ] 支持股票收藏功能
- [ ] 添加股票分类筛选（行业、地区等）
- [ ] 支持导出 Excel/CSV 功能
- [ ] 添加股票行情实时展示

## 相关文件清单

### 后端文件
- `backend/app/models/unified_models.py` - 数据模型定义（新增 4 个模型）
- `backend/app/adapters/eastmoney_adapter.py` - 数据适配器（新增 4 个方法）
- `backend/app/api/v1/endpoints/eastmoney.py` - API 端点（新增 4 个端点）

### 前端文件
- `frontend/src/services/eastmoney.ts` - API 服务（新增 4 个接口和 4 个方法）
- `frontend/src/pages/StockListPage.tsx` - 股票列表页面（新建）
- `frontend/src/App.tsx` - 路由配置（新增 1 个路由）

## 测试建议

### 后端测试
```bash
# 测试沪深京 A 股列表
curl "http://localhost:8000/api/v1/eastmoney/stock-info-a"

# 测试上海证券交易所
curl "http://localhost:8000/api/v1/eastmoney/stock-info-sh/主板 A 股"
curl "http://localhost:8000/api/v1/eastmoney/stock-info-sh/科创板"

# 测试深圳证券交易所
curl "http://localhost:8000/api/v1/eastmoney/stock-info-sz/A 股列表"

# 测试北京证券交易所
curl "http://localhost:8000/api/v1/eastmoney/stock-info-bj"
```

### 前端测试
1. 访问股票列表页面
2. 测试 4 个 Tab 切换
3. 测试搜索功能
4. 测试板块选择功能
5. 测试数据展示完整性

## 版本历史

- **v1.0**: 盘口异动和涨停板行情
- **v1.1**: 涨停股池详细功能
- **v1.2**: 千股千评功能
- **v1.3**: 研报公告功能
- **v1.4**: 资产负债表功能
- **v1.5**: 利润表和现金流量表功能
- **v1.6**: 新浪财经财务指标功能
- **v1.7**: 股票列表功能（沪深京）（当前版本）

## 联系方式

如有问题或建议，请联系开发团队。
