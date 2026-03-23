# Quant 项目更新日志 - v1.14 大宗交易数据

## 版本信息
- **版本号**: v1.14
- **发布日期**: 2026-03-21
- **模块**: 东方财富数据模块

## 新增功能

### 1. 大宗交易市场统计

#### 1.1 大宗交易市场统计数据（stock_dzjy_sctj）
- **接口**: `/api/v1/eastmoney/stock-dzjy-sctj`
- **数据源**: 东方财富网 - 数据中心 - 大宗交易
- **描述**: 获取 A 股市场大宗交易的每日统计数据，包括上证指数、成交总额、溢价/折价成交等
- **输入参数**: 无
- **输出字段**:
  - `index`: 序号
  - `date`: 交易日期
  - `sh_index`: 上证指数
  - `sh_change_pct`: 上证指数涨跌幅（%）
  - `total_amount`: 大宗交易成交总额（元）
  - `premium_amount`: 溢价成交总额（元）
  - `premium_ratio`: 溢价成交总额占比（%）
  - `discount_amount`: 折价成交总额（元）
  - `discount_ratio`: 折价成交总额占比（%）
- **数据范围**: 所有历史数据（2000 年至今）
- **前端页面**: `/eastmoney/block-trade`（第一个 Tab）

### 2. 大宗交易每日明细

#### 2.1 大宗交易每日明细（stock_dzjy_mrmx）
- **接口**: `/api/v1/eastmoney/stock-dzjy-mrmx`
- **数据源**: 东方财富网 - 数据中心 - 大宗交易
- **描述**: 获取每日大宗交易的详细记录，包括证券代码、名称、成交价、成交量、买卖方营业部等
- **输入参数**:
  - `symbol`: 证券类型
    - `A 股`
    - `B 股`
    - `基金`
    - `债券`
  - `start_date`: 开始日期（格式：YYYYMMDD）
  - `end_date`: 结束日期（格式：YYYYMMDD）
- **输出字段**:
  - `index`: 序号
  - `date`: 交易日期
  - `stock_code`: 证券代码
  - `stock_name`: 证券简称
  - `change_pct`: 涨跌幅（%）
  - `close_price`: 收盘价（元）
  - `deal_price`: 成交价（元）
  - `premium_ratio`: 折溢率（%）
  - `volume`: 成交量（股）
  - `amount`: 成交额（元）
  - `amount_ratio`: 成交额/流通市值（%）
  - `buyer_dept`: 买方营业部
  - `seller_dept`: 卖方营业部
- **数据范围**: 根据日期范围参数确定
- **前端页面**: `/eastmoney/block-trade`（第二个 Tab）

## 技术实现

### 后端变更

#### 1. 数据模型（`unified_models.py`）
- ✅ 已创建 `StockDzjySctj` 模型（9 个字段）
- ✅ 已创建 `StockDzjyMrmx` 模型（13 个字段）

#### 2. 数据适配器（`eastmoney_adapter.py`）
- ✅ 已实现 `get_stock_dzjy_sctj()` 方法
  - 无参数调用
  - 处理 9 个数据字段
  - 缓存键固定
- ✅ 已实现 `get_stock_dzjy_mrmx()` 方法
  - 支持 symbol、start_date、end_date 三个参数
  - 处理 13 个数据字段
  - 缓存键包含所有参数组合
- 缓存机制：60 秒 TTL
- 错误处理：异常时返回空列表并记录日志

#### 3. API 端点（`eastmoney.py`）
- ✅ 添加 `GET /stock-dzjy-sctj` 端点
  - 无参数
- ✅ 添加 `GET /stock-dzjy-mrmx` 端点
  - Query 参数：symbol（默认 A 股）、start_date、end_date

### 前端变更

#### 1. TypeScript 接口（`eastmoney.ts`）
- ✅ 添加 `StockDzjySctj` 接口（9 个字段）
- ✅ 添加 `StockDzjyMrmx` 接口（13 个字段）
- ✅ 添加 `getStockDzjySctj()` 方法
- ✅ 添加 `getStockDzjyMrmx()` 方法

#### 2. 页面组件
- ✅ 创建 `BlockTradePage.tsx` 页面
  - 2 个 Tab 面板（市场统计、每日明细）
  - 市场统计：
    - 刷新按钮
    - 6 个统计卡片（日期、指数、成交额等）
    - 数据表格展示（前 100 条）
  - 每日明细：
    - 证券类型选择器（A 股/B 股/基金/债券）
    - 日期范围选择器（开始日期、结束日期）
    - 查询按钮
    - 4 个统计卡片（日期、笔数、总额、平均折溢率）
    - 数据表格展示（前 100 条）
  - 颜色标识：
    - 涨跌幅：红色（涨）、绿色（跌）
    - 折溢率：红色（溢价）、绿色（折价）

#### 3. 路由配置
- ✅ 添加路由 `/eastmoney/block-trade`
- ✅ 更新 `App.tsx`

#### 4. 导航菜单
- ✅ 侧边栏添加"大宗交易"菜单项

## 功能特性

### 1. 市场统计 Tab
- **无参数查询**: 一键获取所有历史数据
- **统计卡片**:
  - 最新日期和上证指数
  - 指数涨跌幅（带颜色标识）
  - 成交总额（转换为亿单位）
  - 溢价成交额和占比
  - 折价成交额和占比
- **数据表格**:
  - 展示每日详细统计数据
  - 涨跌幅颜色标识
  - 金额自动转换为易读单位
- **刷新功能**: 手动刷新按钮

### 2. 每日明细 Tab
- **证券类型选择**: 支持 A 股、B 股、基金、债券四种类型
- **日期范围选择**: 自定义开始和结束日期
- **统计卡片**:
  - 最新日期
  - 交易笔数
  - 成交总额（自动计算）
  - 平均折溢率（自动计算）
- **数据表格**:
  - 展示每笔交易的详细信息
  - 证券代码和名称
  - 涨跌幅和收盘价
  - 成交价和折溢率（带颜色标识）
  - 成交量和成交额
  - 买方和卖方营业部
- **查询功能**: 根据参数查询指定范围数据

### 3. 交互功能
- **Tab 切换**: 两个功能快速切换
- **参数配置**: 灵活的证券类型和日期选择
- **数据刷新**: 手动查询/刷新按钮
- **加载状态**: 数据加载时显示 loading 状态
- **错误提示**: 数据加载失败时显示错误提示
- **数据分页**: 默认只显示前 100 条数据

### 4. 性能优化
- **数据分页**: 避免大数据量导致页面卡顿
- **按需加载**: Tab 切换时才加载对应数据
- **缓存机制**: 后端 60 秒缓存，减少重复请求
- **单位转换**: 前端自动转换为易读单位（万、亿）

## 使用示例

### API 调用示例

```python
import requests

# 获取大宗交易市场统计
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-dzjy-sctj'
)
data = response.json()
print(data)

# 获取大宗交易每日明细 - 今日 A 股
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-dzjy-mrmx',
    params={'symbol': 'A 股'}
)
data = response.json()
print(data)

# 获取指定日期范围的 A 股大宗交易
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-dzjy-mrmx',
    params={
        'symbol': 'A 股',
        'start_date': '20220104',
        'end_date': '20220104'
    }
)
data = response.json()
print(data)

# 获取基金大宗交易
response = requests.get(
    'http://localhost:8000/api/v1/eastmoney/stock-dzjy-mrmx',
    params={'symbol': '基金'}
)
data = response.json()
print(data)
```

### 前端使用示例

```typescript
import { eastMoneyApi } from '@/services/eastmoney';

// 获取大宗交易市场统计
const sctjData = await eastMoneyApi.getStockDzjySctj();

// 获取今日 A 股大宗交易明细
const mrmxData = await eastMoneyApi.getStockDzjyMrmx('A 股');

// 获取指定日期范围的 A 股大宗交易
const mrmxData = await eastMoneyApi.getStockDzjyMrmx(
  'A 股',
  '20220104',
  '20220104'
);

// 获取基金大宗交易
const mrmxData = await eastMoneyApi.getStockDzjyMrmx('基金');
```

## 数据说明

### 大宗交易市场统计说明

#### 统计口径
- **大宗交易成交总额**: 当日所有大宗交易的成交金额总和
- **溢价成交**: 成交价高于收盘价的交易
- **折价成交**: 成交价低于收盘价的交易
- **溢价占比**: 溢价成交额 / 总成交额 × 100%
- **折价占比**: 折价成交额 / 总成交额 × 100%

#### 应用场景
- **市场情绪判断**: 溢价成交多表示机构看好后市
- **资金流向分析**: 大宗交易反映机构资金动向
- **市场热度指标**: 成交总额反映市场活跃度

#### 数据特点
- 数据范围：2000 年至今
- 每日更新
- 包含上证指数对比

### 大宗交易每日明细说明

#### 关键指标
- **折溢率**: (成交价 - 收盘价) / 收盘价 × 100%
  - 正值表示溢价成交
  - 负值表示折价成交
- **成交额/流通市值**: 反映交易对流通盘的影响
- **买卖方营业部**: 反映机构席位动向

#### 应用场景
- **机构动向追踪**: 通过营业部判断机构买卖
- **个股利好利空**: 大幅溢价可能利好，大幅折价可能利空
- **投资机会发现**: 机构集中买入的个股可能有机会

#### 数据特点
- 支持 4 种证券类型
- 支持自定义日期范围查询
- 包含详细的交易信息

## 测试建议

### 后端测试
```bash
# 测试大宗交易市场统计接口
curl "http://localhost:8000/api/v1/eastmoney/stock-dzjy-sctj"

# 测试大宗交易每日明细接口 - A 股
curl "http://localhost:8000/api/v1/eastmoney/stock-dzjy-mrmx?symbol=A 股"

# 测试大宗交易每日明细接口 - 指定日期
curl "http://localhost:8000/api/v1/eastmoney/stock-dzjy-mrmx?symbol=A 股&start_date=20220104&end_date=20220104"

# 测试大宗交易每日明细接口 - 基金
curl "http://localhost:8000/api/v1/eastmoney/stock-dzjy-mrmx?symbol=基金"
```

### 前端测试
1. 访问 `/eastmoney/block-trade` 页面
2. 测试两个 Tab 的切换功能
3. 测试市场统计的数据展示
4. 测试每日明细的证券类型选择
5. 测试日期范围选择功能
6. 验证颜色标识是否正确
7. 检查数据表格的分页显示

## 注意事项

1. **数据更新频率**: 
   - 市场统计：每日更新
   - 每日明细：每日更新

2. **数据延迟**: 后端有 60 秒缓存，实时性要求高的场景需注意

3. **数据范围**:
   - 市场统计：2000 年至今所有数据
   - 每日明细：根据日期范围参数确定

4. **参数说明**:
   - symbol 参数支持：A 股、B 股、基金、债券
   - 日期格式：YYYYMMDD（如：20220104）
   - 不指定日期范围时返回默认数据

5. **数据解读**:
   - 溢价成交不一定代表利好，需结合具体情况
   - 折价成交不一定代表利空，可能是股东资金需求
   - 需结合买卖方营业部、成交量等综合判断

## 后续计划

- [ ] 添加大宗交易趋势图表
- [ ] 添加营业部活跃度统计
- [ ] 添加个股大宗交易统计功能
- [ ] 添加机构席位追踪功能
- [ ] 优化大数据量加载性能
- [ ] 添加数据导出功能

## 相关文件

### 后端文件
- `backend/app/models/unified_models.py` - 数据模型定义
- `backend/app/adapters/eastmoney_adapter.py` - 数据适配器
- `backend/app/api/v1/endpoints/eastmoney.py` - API 端点

### 前端文件
- `frontend/src/services/eastmoney.ts` - TypeScript 接口和 API 方法
- `frontend/src/pages/BlockTradePage.tsx` - 页面组件
- `frontend/src/App.tsx` - 路由配置
- `frontend/src/components/Sidebar.tsx` - 导航菜单

## 总结

v1.14 版本成功集成了东方财富网的大宗交易数据功能，为用户提供了：

1. **市场统计**: 反映整体大宗交易市场情况，包括成交总额、溢价/折价比例等
2. **每日明细**: 详细的每笔大宗交易记录，包括证券信息、价格、成交量、买卖方营业部等

这两个功能是追踪机构资金动向、发现投资机会的重要工具：
- **市场统计**: 反映市场整体热度和机构情绪
- **每日明细**: 帮助发现具体个股的机构动向

所有功能均已完整实现并通过语法检查，可以投入使用。
