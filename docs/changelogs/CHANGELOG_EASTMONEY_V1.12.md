# Quant 项目更新日志 - v1.12 A 股估值指标

## 版本信息
- **版本号**: v1.12
- **发布日期**: 2026-03-21
- **模块**: 东方财富数据模块

## 新增功能

### 1. 百度股市通估值指标

#### 1.1 A 股估值数据（stock_zh_valuation_baidu）
- **接口**: `/api/v1/eastmoney/stock-zh-valuation-baidu/{symbol}`
- **数据源**: 百度股市通
- **描述**: 获取 A 股上市公司的历史估值数据
- **输入参数**:
  - `symbol`: A 股代码（如：002044）
  - `indicator`: 估值指标类型
    - 总市值
    - 市盈率 (TTM)
    - 市盈率 (静)
    - 市净率
    - 市现率
  - `period`: 时间范围
    - 近一年
    - 近三年
    - 近五年
    - 近十年
    - 全部
- **输出字段**:
  - `date`: 日期
  - `value`: 估值指标值
- **数据范围**: 根据选择的 period 参数确定
- **前端页面**: `/eastmoney/a-share-valuation`（第一个 Tab）

### 2. 东方财富个股估值

#### 2.1 个股估值数据（stock_value_em）
- **接口**: `/api/v1/eastmoney/stock-value-em/{symbol}`
- **数据源**: 东方财富网 - 数据中心 - 估值分析
- **描述**: 获取个股的详细估值指标历史数据
- **输入参数**:
  - `symbol`: A 股代码（如：300766）
- **输出字段**:
  - `report_date`: 数据日期
  - `close_price`: 当日收盘价（元）
  - `change_pct`: 当日涨跌幅（%）
  - `total_mv`: 总市值（元）
  - `float_mv`: 流通市值（元）
  - `total_shares`: 总股本（股）
  - `float_shares`: 流通股本（股）
  - `pe_ttm`: 市盈率 (TTM)
  - `pe_static`: 市盈率 (静)
  - `pb`: 市净率
  - `peg`: PEG 值
  - `pc`: 市现率
  - `ps`: 市销率
- **数据范围**: 所有历史数据
- **前端页面**: `/eastmoney/a-share-valuation`（第二个 Tab）

### 3. 百度股市通涨跌投票

#### 3.1 涨跌投票数据（stock_zh_vote_baidu）
- **接口**: `/api/v1/eastmoney/stock-zh-vote-baidu/{symbol}`
- **数据源**: 百度股市通 - 股评 - 投票
- **描述**: 获取投资者对股票或指数的涨跌投票数据
- **输入参数**:
  - `symbol`: A 股股票或指数代码（如：000001）
  - `indicator`: 类型（指数/股票）
- **输出字段**:
  - `period`: 周期（今日/本周/本月/今年）
  - `vote_up`: 看涨票数
  - `vote_down`: 看跌票数
  - `vote_up_ratio`: 看涨比例（%）
  - `vote_down_ratio`: 看跌比例（%）
- **数据范围**: 4 个周期（今日、本周、本月、今年）
- **前端页面**: `/eastmoney/a-share-valuation`（第三个 Tab）

## 技术实现

### 后端变更

#### 1. 数据模型（`unified_models.py`）
- ✅ 已创建 `StockZhValuationBaidu` 模型
- ✅ 已创建 `StockValueEM` 模型（13 个字段）
- ✅ 已创建 `StockZhVoteBaidu` 模型

#### 2. 数据适配器（`eastmoney_adapter.py`）
- ✅ 已实现 `get_stock_zh_valuation_baidu()` 方法
  - 支持 symbol、indicator、period 三个参数
  - 缓存键包含所有参数组合
- ✅ 已实现 `get_stock_value_em()` 方法
  - 处理 13 个估值指标字段
- ✅ 已实现 `get_stock_zh_vote_baidu()` 方法
  - 支持股票和指数两种类型
- 缓存机制：60 秒 TTL
- 错误处理：异常时返回空列表并记录日志

#### 3. API 端点（`eastmoney.py`）
- ✅ 添加 `GET /stock-zh-valuation-baidu/{symbol}` 端点
  - Query 参数：indicator、period
- ✅ 添加 `GET /stock-value-em/{symbol}` 端点
- ✅ 添加 `GET /stock-zh-vote-baidu/{symbol}` 端点
  - Query 参数：indicator

### 前端变更

#### 1. TypeScript 接口（`eastmoney.ts`）
- ✅ 添加 `StockZhValuationBaidu` 接口
- ✅ 添加 `StockValueEM` 接口（13 个字段）
- ✅ 添加 `StockZhVoteBaidu` 接口
- ✅ 添加 `getStockZhValuationBaidu()` 方法
- ✅ 添加 `getStockValueEM()` 方法
- ✅ 添加 `getStockZhVoteBaidu()` 方法

#### 2. 页面组件
- ✅ 创建 `AShareValuationPage.tsx` 页面
  - 3 个 Tab 面板（百度估值、个股估值、涨跌投票）
  - 股票代码输入框
  - 估值指标选择器（5 种指标）
  - 时间范围选择器（5 个选项）
  - 投票类型选择器（股票/指数）
  - 查询/刷新按钮
  - 数据统计卡片
  - 数据表格展示（默认显示前 100 条）
  - 投票比例颜色标识（绿色看涨、红色看跌）

#### 3. 路由配置
- ✅ 添加路由 `/eastmoney/a-share-valuation`
- ✅ 更新 `App.tsx`

#### 4. 导航菜单
- ✅ 侧边栏添加"估值指标"菜单项

## 功能特性

### 1. 百度估值 Tab
- **参数选择**: 支持选择 5 种估值指标和 5 个时间范围
- **数据展示**: 日期和指标值两列
- **统计卡片**: 最新日期、最新指标值、数据条数
- **灵活性**: 用户可自由切换不同指标和时间范围

### 2. 个股估值 Tab
- **完整估值指标**: 13 个估值指标一次性展示
- **统计卡片**: 8 个关键指标（收盘价、涨跌幅、PE、PB、总市值、PEG、市销率）
- **数据表格**: 展示所有估值指标的历史数据
- **单位转换**: 总市值自动转换为"亿"单位

### 3. 涨跌投票 Tab
- **多周期展示**: 同时展示今日、本周、本月、今年四个周期
- **统计卡片**: 4 个周期的投票数据
- **颜色标识**: 
  - 看涨：绿色 Badge
  - 看跌：红色 Badge
- **比例显示**: 自动格式化百分比

### 4. 交互功能
- **Tab 切换**: 三个功能之间快速切换
- **参数配置**: 灵活的参数选择器
- **数据刷新**: 手动查询/刷新按钮
- **加载状态**: 数据加载时显示 loading 状态
- **错误提示**: 数据加载失败时显示错误提示
- **输入验证**: 股票代码必填验证

### 5. 性能优化
- **数据分页**: 默认只显示前 100 条数据
- **按需加载**: Tab 切换时才加载对应数据
- **缓存机制**: 后端 60 秒缓存，减少重复请求

## 使用示例

### API 调用示例

```python
import requests

# 获取百度估值数据 - 总市值（近一年）
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-zh-valuation-baidu/002044',
    params={'indicator': '总市值', 'period': '近一年'}
)
data = response.json()
print(data)

# 获取东方财富个股估值数据
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-value-em/300766'
)
data = response.json()
print(data)

# 获取百度涨跌投票数据 - 上证指数
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-zh-vote-baidu/000001',
    params={'indicator': '指数'}
)
data = response.json()
print(data)
```

### 前端使用示例

```typescript
import { eastMoneyApi } from '@/services/eastmoney';

// 获取百度估值数据
const valuationData = await eastMoneyApi.getStockZhValuationBaidu(
  '002044', 
  '总市值', 
  '近一年'
);

// 获取个股估值数据
const valueData = await eastMoneyApi.getStockValueEM('300766');

// 获取涨跌投票数据
const voteData = await eastMoneyApi.getStockZhVoteBaidu('000001', '指数');
```

## 数据说明

### 估值指标说明

#### 总市值
- **含义**: 股票总市值 = 股价 × 总股本
- **单位**: 元
- **用途**: 衡量公司规模

#### 市盈率 (TTM)
- **含义**: 滚动市盈率 = 总市值 / 最近 12 个月净利润
- **用途**: 衡量投资回收期，越低越好
- **合理范围**: 通常 10-30 倍为合理区间

#### 市盈率 (静)
- **含义**: 静态市盈率 = 总市值 / 上一年度净利润
- **用途**: 基于历史数据的估值指标

#### 市净率 (PB)
- **含义**: 市净率 = 股价 / 每股净资产
- **用途**: 衡量股价相对净资产的溢价程度
- **合理范围**: 通常 1-5 倍，不同行业差异大

#### 市现率 (PC)
- **含义**: 市现率 = 总市值 / 经营现金流净额
- **用途**: 衡量股价与现金流的关系

#### PEG 值
- **含义**: PEG = 市盈率 / 净利润增长率
- **用途**: 考虑成长性的估值指标
- **合理范围**: 通常 1 左右为合理，<1 表示低估

#### 市销率 (PS)
- **含义**: 市销率 = 总市值 / 营业收入
- **用途**: 适用于未盈利公司的估值

### 涨跌投票说明
- **数据来源**: 百度股市通用户投票
- **周期**: 今日、本周、本月、今年
- **指标**: 看涨比例、看跌比例
- **用途**: 反映市场情绪

## 测试建议

### 后端测试
```bash
# 测试百度估值接口
curl "http://localhost:8000/api/v1/eastmoney/stock-zh-valuation-baidu/002044?indicator=总市值&period=近一年"

# 测试个股估值接口
curl "http://localhost:8000/api/v1/eastmoney/stock-value-em/300766"

# 测试涨跌投票接口
curl "http://localhost:8000/api/v1/eastmoney/stock-zh-vote-baidu/000001?indicator=指数"
```

### 前端测试
1. 访问 `/eastmoney/a-share-valuation` 页面
2. 测试三个 Tab 的切换功能
3. 测试百度估值的参数选择和查询功能
4. 测试个股估值的数据展示
5. 测试涨跌投票的颜色标识
6. 验证数据表格的分页显示

## 注意事项

1. **数据更新频率**: 
   - 百度估值：每日更新
   - 个股估值：每日更新
   - 涨跌投票：实时或每日更新

2. **数据延迟**: 后端有 60 秒缓存，实时性要求高的场景需注意

3. **数据范围**:
   - 百度估值：根据选择的 period 参数确定
   - 个股估值：所有历史数据
   - 涨跌投票：4 个固定周期

4. **指标选择**: 不同股票可能缺少某些估值指标数据

5. **投票数据**: 涨跌投票反映市场情绪，不构成投资建议

## 后续计划

- [ ] 添加估值指标图表可视化（趋势图、对比图）
- [ ] 添加估值分位数计算和历史对比
- [ ] 添加行业估值对比功能
- [ ] 添加估值预警功能
- [ ] 优化大数据量加载性能
- [ ] 添加更多估值指标（如 EV/EBITDA 等）

## 相关文件

### 后端文件
- `backend/app/models/unified_models.py` - 数据模型定义
- `backend/app/adapters/eastmoney_adapter.py` - 数据适配器
- `backend/app/api/v1/endpoints/eastmoney.py` - API 端点

### 前端文件
- `frontend/src/services/eastmoney.ts` - TypeScript 接口和 API 方法
- `frontend/src/pages/AShareValuationPage.tsx` - 页面组件
- `frontend/src/App.tsx` - 路由配置
- `frontend/src/components/Sidebar.tsx` - 导航菜单

## 总结

v1.12 版本成功集成了百度股市通和东方财富网的估值指标功能，为用户提供了：

1. **百度估值**: 5 种估值指标 × 5 个时间范围的灵活查询
2. **个股估值**: 13 个全面的估值指标历史数据
3. **涨跌投票**: 4 个周期的市场情绪指标

所有功能均已完整实现并通过语法检查，可以投入使用。
