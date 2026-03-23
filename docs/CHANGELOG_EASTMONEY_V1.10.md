# 东方财富模块更新日志 v1.10

## 版本信息
- **版本号**: v1.10
- **发布日期**: 2026-03-21
- **功能模块**: 美港目标价（美股/港股）

## 新增功能

### 1. 美港目标价

#### 接口信息
- **接口名称**: stock_price_js
- **目标地址**: https://www.ushknews.com/report.html
- **描述**: 美港电讯 - 美港目标价数据
- **限量**: 单次获取所有数据，数据从 2019-至今；该接口暂时不能使用

#### 输入参数
| 名称 | 类型 | 描述 |
|------|------|------|
| symbol | str | symbol="us"; choice of {"us", "hk"} |

#### 输出参数
| 名称 | 类型 | 描述 |
|------|------|------|
| 日期 | object | - |
| 个股名称 | object | - |
| 评级 | object | - |
| 先前目标价 | float64 | - |
| 最新目标价 | float64 | - |
| 机构名称 | object | - |

#### 接口示例
```python
import akshare as ak

# 获取美股目标价
stock_price_js_df = ak.stock_price_js(symbol="us")
print(stock_price_js_df)

# 获取港股目标价
stock_price_js_df = ak.stock_price_js(symbol="hk")
print(stock_price_js_df)
```

#### 数据示例
```
       日期             个股名称      评级  先前目标价  最新目标价    机构名称
0   2022-02-12  Teladoc Health(TDOC.N)    买入    NaN  121.0      高盛
1   2022-02-12       Cloudflare(NET.N)   None  132.0  150.0  KeyBanc
2   2022-02-12             Zillow(Z.O)   None   74.0   76.0   摩根士丹利
3   2022-02-11             Zillow(Z.O)   None  105.0  115.0  Benchmark
4   2022-02-11       Cloudflare(NET.N)    中性  210.0  130.0      贝雅
...         ...                     ...    ...    ...    ...     ...
46039 2019-01-02       美国银行 (BAC.N)  与大市持平   37.0   34.0     巴克莱
46040 2019-01-02       亚马逊 (AMZN.O)    买入    NaN    NaN  加拿大皇家银行
46041 2019-01-02        苹果 (AAPL.O)   跑赢大市  266.0  228.0    摩根大通
46042 2019-01-02        苹果 (AAPL.O)   跑赢大市    NaN  220.0  加拿大皇家银行
46043 2019-01-01         强生 (JNJ.N)    中性  139.0  148.0      花旗
```

### 2. 后端实现

#### 数据模型
**文件**: `backend/app/models/unified_models.py`

新增 1 个数据模型：

```python
class StockPriceJS(BaseModel):
    """美港目标价数据模型"""
    date: str = Field(..., description="日期")
    stock_name: str = Field(..., description="个股名称")
    rating: Optional[str] = Field(None, description="评级")
    previous_target: Optional[float] = Field(None, description="先前目标价")
    latest_target: Optional[float] = Field(None, description="最新目标价")
    institution: str = Field(..., description="机构名称")
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他字段")
```

#### 数据适配器
**文件**: `backend/app/adapters/eastmoney_adapter.py`

新增 1 个方法：

```python
async def get_stock_price_js(self, symbol: str = "us") -> List[StockPriceJS]:
    """获取美港目标价
    
    Args:
        symbol: 市场类型，可选值："us"（美股）、"hk"（港股）
    
    Returns:
        美港目标价数据列表
    """
```

功能特性：
- 支持缓存（TTL 60 秒）
- 异步数据获取
- 完整的错误处理
- 支持美股和港股两个市场
- 自动数据类型转换

#### API 端点
**文件**: `backend/app/api/v1/endpoints/eastmoney.py`

新增 1 个端点：

```python
@router.get("/stock-price-js", response_model=ResponseModel[List[StockPriceJS]])
async def get_stock_price_js(
    symbol: str = Query("us", description="市场类型：us（美股）、hk（港股）")
):
    """获取美港目标价"""
```

**API 示例**:
```
# 获取美股目标价
GET /api/v1/eastmoney/stock-price-js?symbol=us

# 获取港股目标价
GET /api/v1/eastmoney/stock-price-js?symbol=hk
```

### 3. 前端实现

#### TypeScript 接口
**文件**: `frontend/src/services/eastmoney.ts`

新增 1 个接口：

```typescript
export interface StockPriceJS {
  date: string;
  stock_name: string;
  rating: string | null;
  previous_target: number | null;
  latest_target: number | null;
  institution: string;
  extra_fields?: Record<string, any>;
}
```

#### API 服务
**文件**: `frontend/src/services/eastmoney.ts`

新增 1 个方法：

```typescript
getStockPriceJS: (symbol: string = 'us') =>
  api.get<StockPriceJS[]>(`/eastmoney/stock-price-js`, {
    params: { symbol }
  })
```

#### 美港目标价页面
**文件**: `frontend/src/pages/StockPriceTargetPage.tsx`

新功能：
- **2 个 Tab 面板**: 
  - 美股目标价（46000+ 条数据）
  - 港股目标价
- **评级颜色标识**:
  - 绿色：买入、增持、跑赢大市等看多评级
  - 红色：卖出、减持、跑输大市等看空评级
  - 黄色：中性、持有等中性评级
- **目标价变动幅度**: 自动计算并显示目标价调整幅度
- **数据表格**: 展示 7 个字段
  - 日期、个股名称、评级
  - 先前目标价、最新目标价
  - 变动幅度、机构名称
- **数据说明**: 详细的数据说明和使用指南

#### 路由配置
**文件**: `frontend/src/App.tsx`

新增路由：
```typescript
<Route path="eastmoney/stock-price-target" element={<StockPriceTargetPage />} />
```

## 技术架构

### 后端技术
- **框架**: FastAPI
- **数据验证**: Pydantic
- **异步处理**: AsyncIO
- **数据源**: 美港电讯
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
用户请求 → 前端 API 服务 → FastAPI 端点 → EastMoneyAdapter → AKShare → 美港电讯
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

# 获取美股目标价
response = requests.get(
    "http://localhost:8000/api/v1/eastmoney/stock-price-js",
    params={"symbol": "us"}
)
data = response.json()
print(data)

# 获取港股目标价
response = requests.get(
    "http://localhost:8000/api/v1/eastmoney/stock-price-js",
    params={"symbol": "hk"}
)
data = response.json()
print(data)
```

### 前端页面访问

访问地址：`http://localhost:3000/eastmoney/stock-price-target`

**功能操作**:
1. 切换 Tab 查看美股或港股数据
2. 查看机构评级（颜色标识）
3. 查看目标价变动幅度
4. 查看详细数据表格

## 数据更新频率

- **更新来源**: 美港电讯官方网站
- **更新时间**: 实时获取最新机构评级
- **数据范围**: 2019 年至今
- **数据特点**: 包含美股和港股两个市场

## 注意事项

1. **市场类型**:
   - us：美股市场
   - hk：港股市场

2. **评级说明**:
   - **看多评级**（绿色）：买入、增持、跑赢大市、Outperform、Overweight、Buy
   - **看空评级**（红色）：卖出、减持、跑输大市、Underperform、Underweight、Sell
   - **中性评级**（黄色）：中性、持有、与大市持平、Hold、Neutral

3. **目标价单位**: 美元（USD）或港元（HKD）

4. **变动幅度计算**: （最新目标价 - 先前目标价）/ 先前目标价 × 100%

5. **缓存时间**: 60 秒，相同请求在 60 秒内会返回缓存数据

6. **接口限制**: 该接口暂时不能使用，数据可能不完整

7. **数据特点**: 
   - 部分数据可能缺少先前目标价或最新目标价
   - 部分评级可能为 None

## 性能优化

1. **缓存机制**: 60 秒 TTL 缓存，减少重复请求
2. **异步处理**: 使用 asyncio 异步获取数据，不阻塞主线程
3. **数据分页**: 前端表格默认展示前 100 条数据，避免一次性渲染过多数据
4. **按需加载**: Tab 面板按需渲染，提升页面性能
5. **评级颜色**: 前端自动识别评级类型并显示颜色

## 后续规划

- [ ] 添加个股目标价历史趋势图表
- [ ] 支持机构评级统计排行
- [ ] 添加目标价准确性分析
- [ ] 支持导出 Excel/CSV 功能
- [ ] 添加评级变化追踪功能

## 相关文件清单

### 后端文件
- `backend/app/models/unified_models.py` - 数据模型定义（新增 1 个模型）
- `backend/app/adapters/eastmoney_adapter.py` - 数据适配器（新增 1 个方法）
- `backend/app/api/v1/endpoints/eastmoney.py` - API 端点（新增 1 个端点）

### 前端文件
- `frontend/src/services/eastmoney.ts` - API 服务（新增 1 个接口和 1 个方法）
- `frontend/src/pages/StockPriceTargetPage.tsx` - 美港目标价页面（新建）
- `frontend/src/App.tsx` - 路由配置（新增 1 个路由）

## 测试建议

### 后端测试
```bash
# 测试美股目标价
curl "http://localhost:8000/api/v1/eastmoney/stock-price-js?symbol=us"

# 测试港股目标价
curl "http://localhost:8000/api/v1/eastmoney/stock-price-js?symbol=hk"
```

### 前端测试
1. 访问美港目标价页面
2. 测试 2 个 Tab 切换
3. 测试评级颜色标识
4. 测试目标价变动幅度计算
5. 测试数据表格展示

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
- **v1.9**: 股东人数及持股集中度功能
- **v1.10**: 美港目标价功能（当前版本）

## 联系方式

如有问题或建议，请联系开发团队。
