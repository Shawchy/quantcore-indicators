# 东方财富模块更新日志 v1.6

## 版本信息
- **版本号**: v1.6
- **发布日期**: 2026-03-20
- **功能模块**: 新浪财经财务指标

## 新增功能

### 1. 新浪财经财务指标 API

#### 接口信息
- **接口名称**: stock_financial_analysis_indicator
- **数据源**: 新浪财经
- **目标地址**: https://money.finance.sina.com.cn/corp/go.php/vFD_FinancialGuideLine/stockid/600004/ctrl/2019/displaytype/4.phtml
- **描述**: 新浪财经 - 财务分析 - 财务指标
- **限量**: 单次获取指定 symbol 和 start_year 的所有财务指标历史数据

#### 输入参数
| 名称 | 类型 | 描述 |
|------|------|------|
| symbol | str | symbol="600004"; 股票代码 |
| start_year | str | start_year="2020"; 开始查询的时间 |

#### 输出参数（86 个财务指标）

**每股指标（11 个）**
- 摊薄每股收益 (元)
- 加权每股收益 (元)
- 每股收益_调整后 (元)
- 扣除非经常性损益后的每股收益 (元)
- 每股净资产_调整前 (元)
- 每股净资产_调整后 (元)
- 每股经营性现金流 (元)
- 每股资本公积金 (元)
- 每股未分配利润 (元)
- 调整后的每股净资产 (元)

**盈利能力（20 个）**
- 总资产利润率 (%)
- 主营业务利润率 (%)
- 总资产净利润率 (%)
- 成本费用利润率 (%)
- 营业利润率 (%)
- 主营业务成本率 (%)
- 销售净利率 (%)
- 股本报酬率 (%)
- 加权净资产报酬率 (%)
- 资产报酬率 (%)
- 销售毛利率 (%)
- 三项费用比重
- 非主营比重
- 主营利润比重
- 股息发放率 (%)
- 投资收益率 (%)
- 主营业务利润 (元)
- 净资产收益率 (%)
- 加权净资产收益率 (%)
- 扣除非经常性损益后的净利润 (元)

**成长能力（4 个）**
- 主营业务收入增长率 (%)
- 净利润增长率 (%)
- 净资产增长率 (%)
- 总资产增长率 (%)

**营运能力（10 个）**
- 应收账款周转率 (次)
- 应收账款周转天数 (天)
- 存货周转天数 (天)
- 存货周转率 (次)
- 固定资产周转率 (次)
- 总资产周转率 (次)
- 总资产周转天数 (天)
- 流动资产周转率 (次)
- 流动资产周转天数 (天)
- 股东权益周转率 (次)

**偿债能力（17 个）**
- 流动比率
- 速动比率
- 现金比率 (%)
- 利息支付倍数
- 长期债务与营运资金比率 (%)
- 股东权益比率 (%)
- 长期负债比率 (%)
- 股东权益与固定资产比率 (%)
- 负债与所有者权益比率 (%)
- 长期资产与长期资金比率 (%)
- 资本化比率 (%)
- 固定资产净值率 (%)
- 资本固定化比率 (%)
- 产权比率 (%)
- 清算价值比率 (%)
- 固定资产比重 (%)
- 资产负债率 (%)

**现金流量指标（5 个）**
- 经营现金净流量对销售收入比率 (%)
- 资产的经营现金流量回报率 (%)
- 经营现金净流量与净利润的比率 (%)
- 经营现金净流量对负债比率 (%)
- 现金流量比率 (%)

**投资明细（6 个）**
- 短期股票投资 (元)
- 短期债券投资 (元)
- 短期其它经营性投资 (元)
- 长期股票投资 (元)
- 长期债券投资 (元)
- 长期其它经营性投资 (元)

**应收款项明细（12 个）**
- 1 年以内应收帐款 (元)
- 1-2 年以内应收帐款 (元)
- 2-3 年以内应收帐款 (元)
- 3 年以内应收帐款 (元)
- 1 年以内预付货款 (元)
- 1-2 年以内预付货款 (元)
- 2-3 年以内预付货款 (元)
- 3 年以内预付货款 (元)
- 1 年以内其它应收款 (元)
- 1-2 年以内其它应收款 (元)
- 2-3 年以内其它应收款 (元)
- 3 年以内其它应收款 (元)

### 2. 后端实现

#### 数据模型
**文件**: `backend/app/models/unified_models.py`

新增 `StockFinancialIndicator` 数据模型：
```python
class StockFinancialIndicator(BaseModel):
    """新浪财经财务指标数据模型
    
    包含 86 个财务指标字段，这里列出主要字段，其他字段使用额外字段存储
    """
    date: Optional[str] = Field(None, description="日期")
    diluted_eps: Optional[float] = Field(None, description="摊薄每股收益 (元)")
    weighted_eps: Optional[float] = Field(None, description="加权每股收益 (元)")
    # ... 其他 80+ 个字段
    extra_fields: Optional[Dict[str, Any]] = Field(default_factory=dict, description="其他财务指标")
```

#### 数据适配器
**文件**: `backend/app/adapters/eastmoney_adapter.py`

新增方法：
```python
async def get_financial_analysis_indicator(self, symbol: str, start_year: str) -> List[StockFinancialIndicator]:
    """获取新浪财经财务指标"""
```

功能特性：
- 支持缓存（TTL 60 秒）
- 异步数据获取
- 完整的错误处理
- 自动数据类型转换

#### API 端点
**文件**: `backend/app/api/v1/endpoints/eastmoney.py`

新增端点：
```python
@router.get("/financial-indicator/{symbol}", response_model=ResponseModel[List[StockFinancialIndicator]])
async def get_financial_indicator(
    symbol: str = Path(..., description="股票代码"),
    start_year: Optional[str] = Query(None, description="开始年份")
):
    """获取新浪财经财务指标"""
```

**API 示例**:
```
GET /api/v1/eastmoney/financial-indicator/600004?start_year=2020
```

### 3. 前端实现

#### TypeScript 接口
**文件**: `frontend/src/services/eastmoney.ts`

新增接口：
```typescript
export interface StockFinancialIndicator {
  date: string | null;
  diluted_eps: number | null;
  weighted_eps: number | null;
  // ... 其他 80+ 个字段
  extra_fields: Record<string, any>;
}
```

#### API 服务
**文件**: `frontend/src/services/eastmoney.ts`

新增方法：
```typescript
getFinancialIndicator: (symbol: string, startYear?: string) =>
  api.get<StockFinancialIndicator[]>(`/eastmoney/financial-indicator/${symbol}`, {
    params: { start_year: startYear || '2020' }
  })
```

#### 财务指标页面
**文件**: `frontend/src/pages/SinaFinancialIndicatorPage.tsx`

新功能：
- **主要指标卡片**: 展示 8 个关键财务指标
- **分类展示**: 5 个 Tab 面板分类展示不同维度指标
  - 每股指标
  - 盈利能力
  - 成长能力
  - 营运能力
  - 偿债能力
- **完整数据**: 展示所有 86 个财务指标
- **搜索功能**: 支持股票代码和开始年份查询
- **数据说明**: 详细的数据说明和使用指南

#### 路由配置
**文件**: `frontend/src/App.tsx`

新增路由：
```typescript
<Route path="eastmoney/sina-financial-indicator" element={<SinaFinancialIndicatorPage />} />
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
用户请求 → 前端 API 服务 → FastAPI 端点 → EastMoneyAdapter → AKShare → 新浪财经
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

# 获取南方航空 2020 年以来的财务指标
response = requests.get(
    "http://localhost:8000/api/v1/eastmoney/financial-indicator/600004",
    params={"start_year": "2020"}
)
data = response.json()
print(data)
```

### 前端页面访问

访问地址：`http://localhost:3000/eastmoney/sina-financial-indicator`

**功能操作**:
1. 输入股票代码（如：600004）
2. 输入开始年份（如：2020）
3. 点击"查询"按钮
4. 查看主要指标卡片
5. 切换 Tab 查看不同类别的财务指标
6. 查看完整数据表格

## 数据更新频率

- **更新来源**: 上市公司定期报告（季报、半年报、年报）
- **更新时间**: 随上市公司公告实时更新
- **历史数据**: 从指定开始年份至今的所有历史数据

## 注意事项

1. **股票代码格式**: 使用 6 位数字代码（如：600004），不需要市场前缀
2. **开始年份**: 建议使用 2019 年或之后的年份，数据更完整
3. **数据单位**: 
   - 金额类指标：元
   - 比率类指标：百分比（%）
   - 周转率类指标：次
   - 周转天数类指标：天
4. **空值处理**: 部分指标在某些报告期可能为空值（null），展示为"-"
5. **缓存时间**: 60 秒，相同请求在 60 秒内会返回缓存数据

## 性能优化

1. **缓存机制**: 60 秒 TTL 缓存，减少重复请求
2. **异步处理**: 使用 asyncio 异步获取数据，不阻塞主线程
3. **数据分页**: 前端表格默认展示前 20 条数据，避免一次性渲染过多数据
4. **按需加载**: Tab 面板按需渲染，提升页面性能

## 后续规划

- [ ] 添加财务指标趋势图表
- [ ] 支持多股票对比分析
- [ ] 添加财务指标预警功能
- [ ] 支持自定义指标筛选
- [ ] 导出 Excel/PDF 功能

## 相关文件清单

### 后端文件
- `backend/app/models/unified_models.py` - 数据模型定义
- `backend/app/adapters/eastmoney_adapter.py` - 数据适配器
- `backend/app/api/v1/endpoints/eastmoney.py` - API 端点

### 前端文件
- `frontend/src/services/eastmoney.ts` - API 服务
- `frontend/src/pages/SinaFinancialIndicatorPage.tsx` - 财务指标页面
- `frontend/src/App.tsx` - 路由配置

## 测试建议

### 后端测试
```bash
# 测试 API 端点
curl "http://localhost:8000/api/v1/eastmoney/financial-indicator/600004?start_year=2020"
```

### 前端测试
1. 访问财务指标页面
2. 测试不同股票代码查询
3. 测试不同年份查询
4. 测试各 Tab 面板切换
5. 测试数据展示完整性

## 版本历史

- **v1.0**: 盘口异动和涨停板行情
- **v1.1**: 涨停股池详细功能
- **v1.2**: 千股千评功能
- **v1.3**: 研报公告功能
- **v1.4**: 资产负债表功能
- **v1.5**: 利润表和现金流量表功能
- **v1.6**: 新浪财经财务指标功能（当前版本）

## 联系方式

如有问题或建议，请联系开发团队。
