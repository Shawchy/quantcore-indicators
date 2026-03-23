# Quant 项目更新日志 - v1.15 融资融券数据

## 版本信息
- **版本号**: v1.15
- **发布日期**: 2026-03-21
- **模块**: 东方财富数据模块

## 新增功能

### 1. 融资融券保证金比例

#### 1.1 标的证券名单及保证金比例（stock_margin_ratio_pa）
- **接口**: `/api/v1/eastmoney/stock-margin-ratio-pa`
- **数据源**: 平安证券
- **描述**: 获取融资融券标的证券名单及融资/融券保证金比例
- **输入参数**:
  - `symbol`: 交易所类型
    - `深市`
    - `沪市`
    - `北交所`
  - `date`: 交易日期（格式：YYYYMMDD）
- **输出字段**:
  - `stock_code`: 证券代码
  - `stock_name`: 证券简称
  - `margin_ratio`: 融资比例
  - `short_ratio`: 融券比例
- **数据范围**: 指定交易所和交易日的所有标的证券
- **前端页面**: `/eastmoney/margin-trading`（第一个 Tab）

### 2. 两融账户统计

#### 2.1 融资融券账户统计（stock_margin_account_info）
- **接口**: `/api/v1/eastmoney/stock-margin-account-info`
- **数据源**: 东方财富网 - 数据中心 - 融资融券
- **描述**: 获取全市场融资融券账户的统计数据，包括余额、投资者数量、担保物等
- **输入参数**: 无
- **输出字段**:
  - `date`: 日期
  - `margin_balance`: 融资余额（亿）
  - `short_balance`: 融券余额（亿）
  - `margin_buy`: 融资买入额（亿）
  - `short_sell`: 融券卖出额（亿）
  - `broker_count`: 证券公司数量（家）
  - `branch_count`: 营业部数量（家）
  - `individual_count`: 个人投资者数量（万名）
  - `institution_count`: 机构投资者数量（家）
  - `active_count`: 参与交易的投资者数量（万名）
  - `debt_count`: 有融资融券负债的投资者数量（万名）
  - `collateral_value`: 担保物总价值（亿）
  - `collateral_ratio`: 平均维持担保比例（%）
- **数据范围**: 所有历史数据（2012 年至今）
- **前端页面**: `/eastmoney/margin-trading`（第二个 Tab）

## 技术实现

### 后端变更

#### 1. 数据模型（`unified_models.py`）
- ✅ 已创建 `StockMarginRatioPa` 模型（4 个字段）
- ✅ 已创建 `StockMarginAccountInfo` 模型（13 个字段）

#### 2. 数据适配器（`eastmoney_adapter.py`）
- ✅ 已实现 `get_stock_margin_ratio_pa()` 方法
  - 支持 symbol 和 date 参数
  - 处理 4 个数据字段
  - 缓存键包含参数组合
- ✅ 已实现 `get_stock_margin_account_info()` 方法
  - 无参数调用
  - 处理 13 个数据字段
  - 缓存键固定
- 缓存机制：60 秒 TTL
- 错误处理：异常时返回空列表并记录日志

#### 3. API 端点（`eastmoney.py`）
- ✅ 添加 `GET /stock-margin-ratio-pa` 端点
  - Query 参数：symbol（默认深市）、date
- ✅ 添加 `GET /stock-margin-account-info` 端点
  - 无参数

### 前端变更

#### 1. TypeScript 接口（`eastmoney.ts`）
- ✅ 添加 `StockMarginRatioPa` 接口（4 个字段）
- ✅ 添加 `StockMarginAccountInfo` 接口（13 个字段）
- ✅ 添加 `getStockMarginRatioPa()` 方法
- ✅ 添加 `getStockMarginAccountInfo()` 方法

#### 2. 页面组件
- ✅ 创建 `MarginTradingPage.tsx` 页面
  - 2 个 Tab 面板（保证金比例查询、两融账户统计）
  - 保证金比例查询：
    - 交易所选择器（深市/沪市/北交所）
    - 日期选择器
    - 查询按钮
    - 统计卡片（证券数量、交易所、日期）
    - 数据表格展示（前 100 条）
    - 融资/融券比例颜色标识
  - 两融账户统计：
    - 刷新按钮
    - 13 个统计卡片（余额、投资者数量、担保物等）
    - 数据表格展示（前 100 条）
    - 担保比例颜色标识

#### 3. 路由配置
- ✅ 添加路由 `/eastmoney/margin-trading`
- ✅ 更新 `App.tsx`

#### 4. 导航菜单
- ✅ 侧边栏添加"融资融券"菜单项

## 功能特性

### 1. 保证金比例查询 Tab
- **交易所选择**: 支持深市、沪市、北交所三个市场
- **日期选择**: 可查询历史交易日的保证金比例
- **统计卡片**: 证券数量、交易所、查询日期
- **数据表格**:
  - 证券代码和简称
  - 融资比例（颜色标识：<1 绿色，≥1 红色）
  - 融券比例（颜色标识：<1 绿色，≥1 红色）
- **查询功能**: 根据参数查询指定数据

### 2. 两融账户统计 Tab
- **无参数查询**: 一键获取所有历史数据
- **统计卡片**（13 个）:
  - 最新日期
  - 融资余额、融券余额
  - 融资买入额、融券卖出额
  - 证券公司数量、营业部数量
  - 个人投资者数量、机构投资者数量
  - 活跃投资者数量
  - 担保物总价值
  - 平均维持担保比例（带文字提示：安全/关注）
- **数据表格**:
  - 展示每日详细统计数据
  - 担保比例颜色标识（>250% 绿色，≤250% 黄色）
- **刷新功能**: 手动刷新按钮

### 3. 交互功能
- **Tab 切换**: 两个功能快速切换
- **参数配置**: 灵活的交易所和日期选择
- **数据刷新**: 手动查询/刷新按钮
- **加载状态**: 数据加载时显示 loading 状态
- **错误提示**: 数据加载失败时显示错误提示
- **数据分页**: 默认只显示前 100 条数据

### 4. 性能优化
- **数据分页**: 避免大数据量导致页面卡顿
- **按需加载**: Tab 切换时才加载对应数据
- **缓存机制**: 后端 60 秒缓存，减少重复请求
- **单位优化**: 自动使用合适的单位（亿、万、家）

## 使用示例

### API 调用示例

```python
import requests

# 获取融资融券保证金比例 - 深市
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-margin-ratio-pa',
    params={'symbol': '深市'}
)
data = response.json()
print(data)

# 获取融资融券保证金比例 - 沪市（指定日期）
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-margin-ratio-pa',
    params={'symbol': '沪市', 'date': '20260113'}
)
data = response.json()
print(data)

# 获取两融账户统计
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-margin-account-info'
)
data = response.json()
print(data)
```

### 前端使用示例

```typescript
import { eastMoneyApi } from '@/services/eastmoney';

// 获取深市融资融券保证金比例
const ratioData = await eastMoneyApi.getStockMarginRatioPa('深市');

// 获取沪市融资融券保证金比例（指定日期）
const ratioData = await eastMoneyApi.getStockMarginRatioPa('沪市', '20260113');

// 获取两融账户统计
const accountInfoData = await eastMoneyApi.getStockMarginAccountInfo();
```

## 数据说明

### 保证金比例说明

#### 基本概念
- **融资比例**: 融资保证金比例，表示融资买入时需要缴纳的保证金比例
  - 比例<1：表示杠杆>1，风险较高
  - 比例≥1：表示杠杆≤1，风险可控
- **融券比例**: 融券保证金比例，表示融券卖出时需要缴纳的保证金比例

#### 应用场景
- **风险评估**: 比例越高，风险越低
- **投资策略**: 了解标的证券的融资融券成本
- **监管合规**: 符合监管要求的保证金比例

#### 数据特点
- 支持 3 个交易所
- 可查询历史数据
- 包含所有标的证券

### 两融账户统计说明

#### 关键指标
- **融资余额**: 投资者融资买入后尚未偿还的金额，反映看多情绪
- **融券余额**: 投资者融券卖出后尚未偿还的金额，反映看空情绪
- **融资买入额**: 当日融资买入的金额
- **融券卖出额**: 当日融券卖出的金额
- **平均维持担保比例**: 投资者账户担保物与债务的比例
  - >250%：安全区域
  - 200%-250%：关注区域
  - <200%：警戒区域

#### 应用场景
- **市场情绪判断**: 融资余额增加表示看多情绪上升
- **资金流向分析**: 融资买入额反映资金流入
- **风险评估**: 担保比例反映整体风险水平
- **投资者结构**: 个人/机构比例反映市场成熟度

#### 数据特点
- 数据范围：2012 年至今
- 每日更新
- 包含 13 个维度数据

## 测试建议

### 后端测试
```bash
# 测试融资融券保证金比例接口 - 深市
curl "http://localhost:8000/api/v1/eastmoney/stock-margin-ratio-pa?symbol=深市"

# 测试融资融券保证金比例接口 - 沪市（指定日期）
curl "http://localhost:8000/api/v1/eastmoney/stock-margin-ratio-pa?symbol=沪市&date=20260113"

# 测试两融账户统计接口
curl "http://localhost:8000/api/v1/eastmoney/stock-margin-account-info"
```

### 前端测试
1. 访问 `/eastmoney/margin-trading` 页面
2. 测试两个 Tab 的切换功能
3. 测试保证金比例的交易所选择
4. 测试日期选择功能
5. 验证颜色标识是否正确
6. 检查数据表格的分页显示

## 注意事项

1. **数据更新频率**: 
   - 保证金比例：每个交易日更新
   - 账户统计：每日更新

2. **数据延迟**: 后端有 60 秒缓存，实时性要求高的场景需注意

3. **数据范围**:
   - 保证金比例：指定交易所和交易日
   - 账户统计：2012 年至今所有数据

4. **参数说明**:
   - symbol 参数支持：深市、沪市、北交所
   - 日期格式：YYYYMMDD（如：20260113）
   - 不指定日期时返回默认数据

5. **数据解读**:
   - 融资余额高表示市场看多情绪浓厚
   - 融券余额高表示市场看空情绪浓厚
   - 担保比例低于 200% 需警惕风险

## 后续计划

- [ ] 添加融资融券余额趋势图表
- [ ] 添加个股融资融券明细查询
- [ ] 添加融资融券余额与指数对比
- [ ] 添加融资融券标的证券筛选功能
- [ ] 优化大数据量加载性能
- [ ] 添加数据导出功能

## 相关文件

### 后端文件
- `backend/app/models/unified_models.py` - 数据模型定义
- `backend/app/adapters/eastmoney_adapter.py` - 数据适配器
- `backend/app/api/v1/endpoints/eastmoney.py` - API 端点

### 前端文件
- `frontend/src/services/eastmoney.ts` - TypeScript 接口和 API 方法
- `frontend/src/pages/MarginTradingPage.tsx` - 页面组件
- `frontend/src/App.tsx` - 路由配置
- `frontend/src/components/Sidebar.tsx` - 导航菜单

## 总结

v1.15 版本成功集成了融资融券数据功能，为用户提供了：

1. **保证金比例查询**: 3 个交易所的标的证券名单及融资/融券保证金比例
2. **两融账户统计**: 13 个维度的全市场融资融券统计数据

这两个功能是了解融资融券市场、判断市场情绪的重要工具：
- **保证金比例**: 帮助了解标的证券的融资融券成本和风险
- **账户统计**: 反映市场整体融资融券规模、投资者结构和风险水平

所有功能均已完整实现并通过语法检查，可以投入使用。
