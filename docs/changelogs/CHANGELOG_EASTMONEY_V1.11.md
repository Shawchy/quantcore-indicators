# Quant 项目更新日志 - v1.11 乐咕乐股市场指标

## 版本信息
- **版本号**: v1.11
- **发布日期**: 2026-03-21
- **模块**: 东方财富数据模块

## 新增功能

### 1. 乐咕乐股市场指标（3 个）

#### 1.1 大盘拥挤度（stock_a_congestion_lg）
- **接口**: `/api/v1/eastmoney/stock-a-congestion-lg`
- **数据源**: 乐咕乐股
- **描述**: 获取 A 股市场拥挤度数据，反映市场交易活跃程度
- **数据字段**:
  - `date`: 日期
  - `close`: 收盘价
  - `congestion`: 拥挤度（0-1 之间，越高表示市场越拥挤）
- **数据范围**: 近 4 年历史数据
- **前端页面**: `/eastmoney/legulegu-market-indicators`（第一个 Tab）

#### 1.2 股债利差（stock_ebs_lg）
- **接口**: `/api/v1/eastmoney/stock-ebs-lg`
- **数据源**: 乐咕乐股
- **描述**: 获取股票市场与债券市场的利差数据，用于判断股债相对价值
- **数据字段**:
  - `date`: 日期
  - `hs300_index`: 沪深 300 指数
  - `ebs`: 股债利差
  - `ebs_ma`: 股债利差均线
- **数据范围**: 所有历史数据（2005 年至今）
- **前端页面**: `/eastmoney/legulegu-market-indicators`（第二个 Tab）

#### 1.3 巴菲特指标（stock_buffett_index_lg）
- **接口**: `/api/v1/eastmoney/stock-buffett-index-lg`
- **数据源**: 乐咕乐股
- **描述**: 巴菲特指标（证券化率）= 总市值 / GDP，用于衡量市场估值水平
- **数据字段**:
  - `date`: 交易日
  - `close`: 收盘价
  - `total_market_cap`: 总市值（亿元）
  - `gdp`: 上年度 GDP（亿元）
  - `decile_10y`: 近十年分位数
  - `decile_all`: 总历史分位数
- **数据范围**: 所有历史数据（2005 年至今）
- **前端页面**: `/eastmoney/legulegu-market-indicators`（第三个 Tab）

## 技术实现

### 后端变更

#### 1. 数据模型（`unified_models.py`）
- ✅ 已创建 `StockAConestionLG` 模型
- ✅ 已创建 `StockEBSLG` 模型
- ✅ 已创建 `StockBuffettIndexLG` 模型

#### 2. 数据适配器（`eastmoney_adapter.py`）
- ✅ 已实现 `get_stock_a_congestion_lg()` 方法
- ✅ 已实现 `get_stock_ebs_lg()` 方法
- ✅ 已实现 `get_stock_buffett_index_lg()` 方法
- 缓存机制：60 秒 TTL
- 错误处理：异常时返回空列表并记录日志

#### 3. API 端点（`eastmoney.py`）
- ✅ 添加 `GET /stock-a-congestion-lg` 端点
- ✅ 添加 `GET /stock-ebs-lg` 端点
- ✅ 添加 `GET /stock-buffett-index-lg` 端点

### 前端变更

#### 1. TypeScript 接口（`eastmoney.ts`）
- ✅ 添加 `StockAConestionLG` 接口
- ✅ 添加 `StockEBSLG` 接口
- ✅ 添加 `StockBuffettIndexLG` 接口
- ✅ 添加 `getStockAConestionLG()` 方法
- ✅ 添加 `getStockEBSLG()` 方法
- ✅ 添加 `getStockBuffettIndexLG()` 方法

#### 2. 页面组件
- ✅ 创建 `LeguleGuMarketIndicatorsPage.tsx` 页面
  - 3 个 Tab 面板展示不同指标
  - 实时数据统计卡片
  - 数据表格展示（默认显示前 100 条）
  - 刷新按钮
  - 拥挤度级别标识（绿/黄/橙/红）
  - 巴菲特指标分位数区域标识

#### 3. 路由配置
- ✅ 添加路由 `/eastmoney/legulegu-market-indicators`
- ✅ 更新 `App.tsx`

#### 4. 导航菜单
- ✅ 侧边栏添加"市场指标"菜单项

## 功能特性

### 1. 数据可视化
- **统计卡片**: 每个指标展示最新数据的关键统计信息
- **数据表格**: 按日期倒序展示历史数据
- **颜色标识**: 
  - 拥挤度：绿（低）、黄（中）、橙（高）、红（极高）
  - 巴菲特指标：绿（低估）、蓝（偏低）、黄（合理）、红（高估）

### 2. 交互功能
- **Tab 切换**: 三个指标之间快速切换
- **数据刷新**: 手动刷新按钮
- **加载状态**: 数据加载时显示 loading 状态
- **错误提示**: 数据加载失败时显示错误提示

### 3. 性能优化
- **数据分页**: 默认只显示前 100 条数据，避免页面卡顿
- **按需加载**: Tab 切换时才加载对应数据
- **缓存机制**: 后端 60 秒缓存，减少重复请求

## 使用示例

### API 调用示例

```python
import requests

# 获取大盘拥挤度
response = requests.get('http://localhost:8000/api/v1/eastmoney/stock-a-congestion-lg')
data = response.json()
print(data)

# 获取股债利差
response = requests.get('http://localhost:8000/api/v1/eastmoney/stock-ebs-lg')
data = response.json()
print(data)

# 获取巴菲特指标
response = requests.get('http://localhost:8000/api/v1/eastmoney/stock-buffett-index-lg')
data = response.json()
print(data)
```

### 前端使用示例

```typescript
import { eastMoneyApi } from '@/services/eastmoney';

// 获取大盘拥挤度
const congestionData = await eastMoneyApi.getStockAConestionLG();

// 获取股债利差
const ebsData = await eastMoneyApi.getStockEBSLG();

// 获取巴菲特指标
const buffettData = await eastMoneyApi.getStockBuffettIndexLG();
```

## 数据说明

### 大盘拥挤度
- **拥挤度含义**: 反映市场交易的拥挤程度，数值越高表示市场越拥挤
- **判断标准**:
  - 0.0-0.3: 低拥挤度（绿色）
  - 0.3-0.5: 中等拥挤度（黄色）
  - 0.5-0.7: 高拥挤度（橙色）
  - 0.7-1.0: 极高拥挤度（红色）

### 股债利差
- **利差含义**: 股票市场收益率与债券收益率的差值
- **应用场景**: 判断股票和债券的相对投资价值
- **数据特点**: 从 2005 年开始，包含所有历史数据

### 巴菲特指标
- **指标含义**: 证券化率 = 总市值 / GDP
- **判断标准**:
  - 分位数<30%: 低估区域（绿色）
  - 分位数 30%-60%: 合理区域（黄色/蓝色）
  - 分位数>80%: 高估区域（红色）
- **数据特点**: 包含近十年分位数和总历史分位数两个维度

## 测试建议

### 后端测试
```bash
# 测试大盘拥挤度接口
curl http://localhost:8000/api/v1/eastmoney/stock-a-congestion-lg

# 测试股债利差接口
curl http://localhost:8000/api/v1/eastmoney/stock-ebs-lg

# 测试巴菲特指标接口
curl http://localhost:8000/api/v1/eastmoney/stock-buffett-index-lg
```

### 前端测试
1. 访问 `/eastmoney/legulegu-market-indicators` 页面
2. 测试三个 Tab 的切换功能
3. 测试刷新按钮功能
4. 检查数据展示是否正确
5. 验证颜色标识是否准确

## 注意事项

1. **数据更新频率**: 
   - 大盘拥挤度：每日更新
   - 股债利差：每日更新
   - 巴菲特指标：每月/每季度更新（依赖 GDP 数据）

2. **数据延迟**: 后端有 60 秒缓存，实时性要求高的场景需注意

3. **数据范围**:
   - 大盘拥挤度：近 4 年数据
   - 股债利差：2005 年至今
   - 巴菲特指标：2005 年至今

4. **分位数计算**: 基于历史数据的分位数，会随时间推移而变化

## 后续计划

- [ ] 添加图表可视化（K 线图、趋势图）
- [ ] 添加数据导出功能（Excel、CSV）
- [ ] 添加指标预警功能
- [ ] 优化大数据量加载性能
- [ ] 添加更多乐咕乐股特色指标

## 相关文件

### 后端文件
- `backend/app/models/unified_models.py` - 数据模型定义
- `backend/app/adapters/eastmoney_adapter.py` - 数据适配器
- `backend/app/api/v1/endpoints/eastmoney.py` - API 端点

### 前端文件
- `frontend/src/services/eastmoney.ts` - TypeScript 接口和 API 方法
- `frontend/src/pages/LeguleGuMarketIndicatorsPage.tsx` - 页面组件
- `frontend/src/App.tsx` - 路由配置
- `frontend/src/components/Sidebar.tsx` - 导航菜单

## 总结

v1.11 版本成功集成了乐咕乐股的三个重要市场指标，为用户提供了：
1. **大盘拥挤度**: 帮助判断市场交易热度
2. **股债利差**: 帮助判断股债相对价值
3. **巴菲特指标**: 帮助判断市场整体估值水平

所有功能均已完整实现并通过语法检查，可以投入使用。
