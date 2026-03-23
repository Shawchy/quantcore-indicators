# Quant 项目更新日志 - v1.13 市场统计指标

## 版本信息
- **版本号**: v1.13
- **发布日期**: 2026-03-21
- **模块**: 东方财富数据模块

## 新增功能

### 1. 创新高/新低统计

#### 1.1 市场创新高/新低数据（stock_a_high_low_statistics）
- **接口**: `/api/v1/eastmoney/stock-a-high-low-statistics`
- **数据源**: 乐咕乐股
- **描述**: 统计不同市场创 20/60/120 日新高、新低的个股数量
- **输入参数**:
  - `symbol`: 市场类型
    - `all`: 全部 A 股
    - `sz50`: 上证 50
    - `hs300`: 沪深 300
    - `zz500`: 中证 500
- **输出字段**:
  - `date`: 交易日
  - `close`: 相关指数收盘价
  - `high20`: 20 日新高数量
  - `low20`: 20 日新低数量
  - `high60`: 60 日新高数量
  - `low60`: 60 日新低数量
  - `high120`: 120 日新高数量
  - `low120`: 120 日新低数量
- **数据范围**: 近 2 年历史数据
- **前端页面**: `/eastmoney/market-statistics`（第一个 Tab）

### 2. 破净股统计

#### 2.1 破净股统计数据（stock_a_below_net_asset_statistics）
- **接口**: `/api/v1/eastmoney/stock-a-below-net-asset-statistics`
- **数据源**: 乐咕乐股
- **描述**: 统计不同市场破净股（股价低于每股净资产）的数量和比例
- **输入参数**:
  - `symbol`: 市场类型
    - 全部 A 股
    - 沪深 300
    - 上证 50
    - 中证 500
- **输出字段**:
  - `date`: 交易日
  - `below_net_asset`: 破净股家数
  - `total_company`: 总公司数
  - `below_net_asset_ratio`: 破净股比率
- **数据范围**: 所有历史数据（2005 年至今）
- **前端页面**: `/eastmoney/market-statistics`（第二个 Tab）

## 技术实现

### 后端变更

#### 1. 数据模型（`unified_models.py`）
- ✅ 已创建 `StockAHighLowStatistics` 模型（8 个字段）
- ✅ 已创建 `StockABelowNetAssetStatistics` 模型（4 个字段）

#### 2. 数据适配器（`eastmoney_adapter.py`）
- ✅ 已实现 `get_stock_a_high_low_statistics()` 方法
  - 支持 symbol 参数（all/sz50/hs300/zz500）
  - 处理 8 个数据字段
  - 缓存键包含 symbol 参数
- ✅ 已实现 `get_stock_a_below_net_asset_statistics()` 方法
  - 支持 symbol 参数（全部 A 股/沪深 300/上证 50/中证 500）
  - 处理 4 个数据字段
- 缓存机制：60 秒 TTL
- 错误处理：异常时返回空列表并记录日志

#### 3. API 端点（`eastmoney.py`）
- ✅ 添加 `GET /stock-a-high-low-statistics` 端点
  - Query 参数：symbol（默认 all）
- ✅ 添加 `GET /stock-a-below-net-asset-statistics` 端点
  - Query 参数：symbol（默认全部 A 股）

### 前端变更

#### 1. TypeScript 接口（`eastmoney.ts`）
- ✅ 添加 `StockAHighLowStatistics` 接口（8 个字段）
- ✅ 添加 `StockABelowNetAssetStatistics` 接口（4 个字段）
- ✅ 添加 `getStockAHighLowStatistics()` 方法
- ✅ 添加 `getStockABelowNetAssetStatistics()` 方法

#### 2. 页面组件
- ✅ 创建 `MarketStatisticsPage.tsx` 页面
  - 2 个 Tab 面板（创新高/新低、破净股）
  - 市场类型选择器
  - 查询/刷新按钮
  - 数据统计卡片
  - 数据表格展示（默认显示前 100 条）
  - 颜色标识（新高红色、新低绿色、破净股红色）

#### 3. 路由配置
- ✅ 添加路由 `/eastmoney/market-statistics`
- ✅ 更新 `App.tsx`

#### 4. 导航菜单
- ✅ 侧边栏添加"市场统计"菜单项

## 功能特性

### 1. 创新高/新低统计 Tab
- **市场选择**: 支持 4 个市场（全部 A 股、上证 50、沪深 300、中证 500）
- **多维度统计**: 20 日/60 日/120 日新高和新低
- **统计卡片**: 
  - 最新日期和指数收盘价
  - 20 日新高/新低对比
  - 60 日新高/新低对比
  - 120 日新高/新低对比
- **颜色标识**:
  - 新高：红色 Badge（代表上涨动能）
  - 新低：绿色 Badge（代表下跌动能）
- **数据表格**: 展示所有时间周期的详细数据

### 2. 破净股统计 Tab
- **市场选择**: 支持 4 个市场（全部 A 股、沪深 300、上证 50、中证 500）
- **统计卡片**:
  - 最新日期
  - 破净股家数
  - 总公司数
  - 破净股比率（带文字提示：偏高/正常）
- **颜色标识**: 破净股家数使用红色 Badge
- **比率提示**: 
  - 破净比率>10%：显示"偏高"
  - 破净比率≤10%：显示"正常"
- **数据表格**: 展示历史破净股数据

### 3. 交互功能
- **Tab 切换**: 两个统计功能快速切换
- **市场选择**: 灵活选择不同市场
- **数据刷新**: 手动查询/刷新按钮
- **加载状态**: 数据加载时显示 loading 状态
- **错误提示**: 数据加载失败时显示错误提示
- **数据分页**: 默认只显示前 100 条数据

### 4. 性能优化
- **数据分页**: 避免大数据量导致页面卡顿
- **按需加载**: Tab 切换时才加载对应数据
- **缓存机制**: 后端 60 秒缓存，减少重复请求

## 使用示例

### API 调用示例

```python
import requests

# 获取创新高/新低统计 - 全部 A 股
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-a-high-low-statistics',
    params={'symbol': 'all'}
)
data = response.json()
print(data)

# 获取创新高/新低统计 - 沪深 300
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-a-high-low-statistics',
    params={'symbol': 'hs300'}
)
data = response.json()
print(data)

# 获取破净股统计 - 全部 A 股
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-a-below-net-asset-statistics',
    params={'symbol': '全部 A 股'}
)
data = response.json()
print(data)

# 获取破净股统计 - 沪深 300
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-a-below-net-asset-statistics',
    params={'symbol': '沪深 300'}
)
data = response.json()
print(data)
```

### 前端使用示例

```typescript
import { eastMoneyApi } from '@/services/eastmoney';

// 获取创新高/新低数据 - 全部 A 股
const hlData = await eastMoneyApi.getStockAHighLowStatistics('all');

// 获取创新高/新低数据 - 沪深 300
const hlData = await eastMoneyApi.getStockAHighLowStatistics('hs300');

// 获取破净股数据 - 全部 A 股
const bnData = await eastMoneyApi.getStockABelowNetAssetStatistics('全部 A 股');

// 获取破净股数据 - 沪深 300
const bnData = await eastMoneyApi.getStockABelowNetAssetStatistics('沪深 300');
```

## 数据说明

### 创新高/新低统计说明

#### 统计口径
- **20 日新高**: 当日收盘价创过去 20 个交易日新高的股票数量
- **20 日新低**: 当日收盘价创过去 20 个交易日新低的股票数量
- **60 日新高/新低**: 同理，统计 60 个交易日
- **120 日新高/新低**: 同理，统计 120 个交易日

#### 应用场景
- **市场情绪判断**: 新高股票多表示市场强势，新低股票多表示市场弱势
- **趋势确认**: 指数上涨 + 新高股票增多 = 健康上涨
- **背离信号**: 指数上涨 + 新高股票减少 = 潜在顶部背离
- **超跌反弹**: 新低股票极端增多后可能出现反弹

#### 数据特点
- 剔除了停牌股票
- 数据范围：近 2 年
- 支持 4 个主要市场指数

### 破净股统计说明

#### 破净股定义
- **破净股**: 股价低于每股净资产的股票
- **市净率 (PB) < 1**: 即股价/每股净资产 < 1

#### 应用场景
- **市场底部判断**: 破净股比例高通常表示市场处于底部区域
- **价值投资参考**: 破净股可能存在投资价值
- **市场情绪指标**: 破净股比例极端高表示市场过度悲观

#### 判断标准
- **破净比率<5%**: 市场估值正常
- **破净比率 5%-10%**: 市场估值偏低
- **破净比率>10%**: 市场估值显著偏低（底部区域）
- **破净比率>20%**: 市场极度低估（历史性底部）

#### 数据特点
- 数据范围：2005 年至今
- 支持 4 个主要市场
- 包含家数、总数、比率三个维度

## 测试建议

### 后端测试
```bash
# 测试创新高/新低接口 - 全部 A 股
curl "http://localhost:8000/api/v1/eastmoney/stock-a-high-low-statistics?symbol=all"

# 测试创新高/新低接口 - 沪深 300
curl "http://localhost:8000/api/v1/eastmoney/stock-a-high-low-statistics?symbol=hs300"

# 测试破净股接口 - 全部 A 股
curl "http://localhost:8000/api/v1/eastmoney/stock-a-below-net-asset-statistics?symbol=全部 A 股"

# 测试破净股接口 - 沪深 300
curl "http://localhost:8000/api/v1/eastmoney/stock-a-below-net-asset-statistics?symbol=沪深 300"
```

### 前端测试
1. 访问 `/eastmoney/market-statistics` 页面
2. 测试两个 Tab 的切换功能
3. 测试不同市场类型的选择
4. 测试查询/刷新功能
5. 验证颜色标识是否正确
6. 检查数据表格的分页显示

## 注意事项

1. **数据更新频率**: 
   - 创新高/新低：每日更新
   - 破净股：每日更新

2. **数据延迟**: 后端有 60 秒缓存，实时性要求高的场景需注意

3. **数据范围**:
   - 创新高/新低：近 2 年数据
   - 破净股：2005 年至今所有数据

4. **统计说明**: 创新高/新低数据已剔除停牌股票

5. **投资建议**: 破净股仅作为参考指标，不构成投资建议

## 后续计划

- [ ] 添加创新高/新低趋势图表
- [ ] 添加破净股比例历史对比图
- [ ] 添加市场宽度指标（新高 - 新低）/ 总股票数
- [ ] 添加不同市场之间的对比功能
- [ ] 优化大数据量加载性能
- [ ] 添加数据导出功能

## 相关文件

### 后端文件
- `backend/app/models/unified_models.py` - 数据模型定义
- `backend/app/adapters/eastmoney_adapter.py` - 数据适配器
- `backend/app/api/v1/endpoints/eastmoney.py` - API 端点

### 前端文件
- `frontend/src/services/eastmoney.ts` - TypeScript 接口和 API 方法
- `frontend/src/pages/MarketStatisticsPage.tsx` - 页面组件
- `frontend/src/App.tsx` - 路由配置
- `frontend/src/components/Sidebar.tsx` - 导航菜单

## 总结

v1.13 版本成功集成了乐咕乐股的两个重要市场统计指标，为用户提供了：

1. **创新高/新低统计**: 4 个市场 × 3 个时间周期（20/60/120 日）的新高新低数据
2. **破净股统计**: 4 个市场的破净股家数、总公司数、破净比率历史数据

这两个指标是判断市场情绪和估值水平的重要工具：
- **创新高/新低**: 反映市场短期动能和趋势强度
- **破净股比率**: 反映市场长期估值水平和底部区域

所有功能均已完整实现并通过语法检查，可以投入使用。
