# 东方财富盘口异动和涨停板行情功能说明

**添加时间：** 2026-03-19  
**版本：** v1.1  
**状态：** ✅ 已完成

---

## 一、功能概述

本次更新添加了东方财富盘口异动和涨停板行情功能，提供以下数据：

1. **盘口异动数据** - 实时监控股票盘口异动情况
2. **板块异动详情** - 展示各板块异动统计
3. **涨停板行情** - 完整的涨停板数据，包括：
   - 涨停股池
   - 昨日涨停
   - 强势股
   - 次新股
4. **市场异动汇总** - 全市场异动统计

---

## 二、后端实现

### 2.1 数据模型

**文件：** `backend/app/models/unified_models.py`

新增数据模型：

```python
class StockChanges(BaseModel):
    """盘口异动数据模型"""
    time: str              # 异动时间
    code: str              # 股票代码
    name: str              # 股票名称
    board: str             # 所属板块
    related_info: str      # 相关信息
    change_type: str       # 异动类型

class StockBoardChange(BaseModel):
    """板块异动数据模型"""
    board_name: str        # 板块名称
    change_pct: float      # 涨跌幅（%）
    net_inflow: float      # 主力净流入（万元）
    change_count: int      # 板块异动总次数
    top_stock_code: str    # 最频繁个股代码
    top_stock_name: str    # 最频繁个股名称
    top_stock_type: str    # 最频繁个股类型
    change_types: List     # 异动类型列表

class StockZtPool(BaseModel):
    """涨停股池数据模型"""
    serial_no: int         # 序号
    code: str              # 股票代码
    name: str              # 股票名称
    change_pct: float      # 涨跌幅（%）
    latest_price: float    # 最新价
    turnover: float        # 成交额
    float_mv: float        # 流通市值
    total_mv: float        # 总市值
    turnover_rate: float   # 换手率（%）
    seal_fund: float       # 封板资金
    first_seal_time: str   # 首次封板时间
    last_seal_time: str    # 最后封板时间
    open_count: int        # 炸板次数
    zt_stats: str          # 涨停统计
    continuous_count: int  # 连板数
    industry: str          # 所属行业

class MarketChanges(BaseModel):
    """市场异动汇总"""
    timestamp: str         # 时间戳
    total_changes: int     # 总异动次数
    rocket_launch: int     # 火箭发射次数
    fast_rebound: int      # 快速反弹次数
    big_buy: int           # 大笔买入次数
    big_sell: int          # 大笔卖出次数
    limit_up: int          # 封涨停板次数
    limit_down: int        # 封跌停板次数
    high_dive: int         # 高台跳水次数

class StockZtPrevious(BaseModel):
    """昨日涨停股池数据模型"""
    serial_no: int         # 序号
    code: str              # 股票代码
    name: str              # 股票名称
    change_pct: float      # 涨跌幅（%）
    latest_price: float    # 最新价
    limit_up_price: float  # 涨停价
    turnover: float        # 成交额
    float_mv: float        # 流通市值
    total_mv: float        # 总市值
    turnover_rate: float   # 换手率（%）
    speed_pct: float       # 涨速（%）
    amplitude: float       # 振幅（%）
    yesterday_seal_time: str  # 昨日封板时间
    yesterday_continuous: int # 昨日连板数
    zt_stats: str          # 涨停统计
    industry: str          # 所属行业

class StockZtStrong(BaseModel):
    """强势股池数据模型"""
    serial_no: int         # 序号
    code: str              # 股票代码
    name: str              # 股票名称
    change_pct: float      # 涨跌幅（%）
    latest_price: float    # 最新价
    limit_up_price: float  # 涨停价
    turnover: float        # 成交额
    float_mv: float        # 流通市值
    total_mv: float        # 总市值
    turnover_rate: float   # 换手率（%）
    speed_pct: float       # 涨速（%）
    is_new_high: str       # 是否新高
    volume_ratio: float    # 量比
    zt_stats: str          # 涨停统计
    reason: str            # 入选理由
    industry: str          # 所属行业

class StockZtSubNew(BaseModel):
    """次新股池数据模型"""
    serial_no: int         # 序号
    code: str              # 股票代码
    name: str              # 股票名称
    change_pct: float      # 涨跌幅（%）
    latest_price: float    # 最新价
    limit_up_price: float  # 涨停价
    turnover: float        # 成交额
    float_mv: float        # 流通市值
    total_mv: float        # 总市值
    turnover_rate: float   # 转手率（%）
    open_days: int         # 开板几日
    open_date: str         # 开板日期
    list_date: str         # 上市日期
    is_new_high: str       # 是否新高
    zt_stats: str          # 涨停统计
    industry: str          # 所属行业
```

### 2.2 数据适配器

**文件：** `backend/app/adapters/eastmoney_adapter.py`

核心方法：

```python
class EastMoneyAdapter(BaseDataAdapter):
    """东方财富数据适配器"""
    
    async def get_stock_changes(self, symbol: str) -> List[StockChanges]:
        """获取盘口异动数据"""
        
    async def get_board_changes(self) -> List[StockBoardChange]:
        """获取板块异动详情"""
        
    async def get_zt_pool(self, date: Optional[str] = None) -> List[StockZtPool]:
        """获取涨停股池数据"""
        
    async def get_zt_pool_previous(self, date: Optional[str] = None) -> List[StockZtPrevious]:
        """获取昨日涨停股池数据"""
        
    async def get_zt_pool_strong(self, date: Optional[str] = None) -> List[StockZtStrong]:
        """获取强势股池数据"""
        
    async def get_zt_pool_sub_new(self, date: Optional[str] = None) -> List[StockZtSubNew]:
        """获取次新股池数据"""
        
    async def get_market_changes_summary(self) -> MarketChanges:
        """获取市场异动汇总"""
```

**特性：**
- ✅ 支持 22 种异动类型
- ✅ 60 秒缓存机制
- ✅ 异步数据获取
- ✅ 基于 AKShare 实现

### 2.3 API 端点

**文件：** `backend/app/api/v1/endpoints/eastmoney.py`

#### 接口列表

| 接口 | 路径 | 方法 | 描述 |
|------|------|------|------|
| 盘口异动 | `/api/v1/eastmoney/changes` | GET | 获取指定类型的盘口异动 |
| 板块异动 | `/api/v1/eastmoney/board-changes` | GET | 获取板块异动详情 |
| 涨停股池 | `/api/v1/eastmoney/zt-pool` | GET | 获取涨停股池数据 |
| 昨日涨停 | `/api/v1/eastmoney/zt-pool-previous` | GET | 获取昨日涨停股池数据 |
| 强势股 | `/api/v1/eastmoney/zt-pool-strong` | GET | 获取强势股池数据 |
| 次新股 | `/api/v1/eastmoney/zt-pool-sub-new` | GET | 获取次新股池数据 |
| 市场汇总 | `/api/v1/eastmoney/market-changes-summary` | GET | 获取市场异动汇总 |
| 异动类型 | `/api/v1/eastmoney/change-types` | GET | 获取所有异动类型 |

#### 接口示例

**1. 获取盘口异动**

```bash
GET /api/v1/eastmoney/changes?symbol=大笔买入
```

响应：
```json
{
  "code": 0,
  "message": "获取成功，共 3174 条",
  "data": [
    {
      "time": "14:55:51",
      "code": "872953",
      "name": "国子软件",
      "board": "大笔买入",
      "related_info": "124230,19.24000,0.300000",
      "change_type": "大笔买入"
    }
  ]
}
```

**2. 获取板块异动**

```bash
GET /api/v1/eastmoney/board-changes
```

响应：
```json
{
  "code": 0,
  "message": "获取成功，共 568 个板块",
  "data": [
    {
      "board_name": "融资融券",
      "change_pct": -2.10,
      "net_inflow": -6560076.199,
      "change_count": 9321,
      "top_stock_code": "N 新恒泰",
      "top_stock_name": "大笔卖出",
      "change_types": [{"t": 8201, "ct": 10821}]
    }
  ]
}
```

**3. 获取涨停股池**

```bash
GET /api/v1/eastmoney/zt-pool?date=20241008
```

响应：
```json
{
  "code": 0,
  "message": "获取成功，共 776 只涨停股",
  "data": [
    {
      "serial_no": 1,
      "code": "000004",
      "name": "国华网安",
      "change_pct": 10.0,
      "latest_price": 17.93,
      "turnover": 123000000,
      "float_mv": 4227000000,
      "total_mv": 6606000000,
      "turnover_rate": 2.91,
      "seal_fund": 534000000,
      "first_seal_time": "09:25:00",
      "last_seal_time": "09:25:00",
      "open_count": 0,
      "zt_stats": "5/5",
      "continuous_count": 5,
      "industry": "光学光电"
    }
  ]
}
```

**4. 获取市场异动汇总**

```bash
GET /api/v1/eastmoney/market-changes-summary
```

响应：
```json
{
  "code": 0,
  "message": "获取成功",
  "data": {
    "timestamp": "2026-03-19T15:00:00",
    "total_changes": 5680,
    "rocket_launch": 1258,
    "fast_rebound": 523,
    "big_buy": 1205,
    "big_sell": 979,
    "limit_up": 85,
    "limit_down": 35,
    "high_dive": 601
  }
}
```

**5. 获取异动类型列表**

```bash
GET /api/v1/eastmoney/change-types
```

响应：
```json
{
  "code": 0,
  "message": "获取成功",
  "data": [
    {"key": "rocket", "name": "火箭发射"},
    {"key": "rebound", "name": "快速反弹"},
    {"key": "big_buy", "name": "大笔买入"},
    ...
  ]
}
```

---

## 三、前端实现

### 3.1 服务接口

**文件：** `frontend/src/services/eastmoney.ts`

```typescript
export const eastMoneyApi = {
  getStockChanges: (symbol: string) => ...,
  getBoardChanges: () => ...,
  getZtPool: (date?: string) => ...,
  getMarketChangesSummary: () => ...,
  getChangeTypes: () => ...,
};
```

### 3.2 页面组件

#### 1. 盘口异动页面

**文件：** `frontend/src/pages/EastMoneyChangesPage.tsx`

**功能：**
- ✅ 异动类型下拉选择
- ✅ 市场异动汇总统计
- ✅ 实时数据表格展示
- ✅ 自动刷新功能

**特性：**
- 颜色标识（红色=买入，绿色=卖出）
- 实时更新
- 响应式布局

#### 2. 涨停板行情页面

**文件：** `frontend/src/pages/EastMoneyZtPoolPage.tsx`

**功能：**
- ✅ 日期选择器
- ✅ 涨停统计信息
- ✅ 完整涨停股池数据
- ✅ 连板数高亮显示

**特性：**
- 统计卡片展示
- 连板数颜色区分
- 炸板次数标识

#### 3. 综合涨停板行情页面

**文件：** `frontend/src/pages/EastMoneyZtBoardPage.tsx`

**功能：**
- ✅ Tab 切换展示 4 种类型
- ✅ 涨停股池
- ✅ 昨日涨停
- ✅ 强势股
- ✅ 次新股
- ✅ 日期选择器
- ✅ 各类型统计信息

**特性：**
- 一体化展示
- 分类统计卡片
- 颜色标识涨跌幅
- 响应式表格布局

---

## 四、异动类型说明

### 4.1 买入信号（红色）

| 类型 | 说明 |
|------|------|
| 火箭发射 | 股价快速拉升 |
| 快速反弹 | 快速反弹上涨 |
| 大笔买入 | 大额买单成交 |
| 封涨停板 | 涨停板封死 |
| 打开跌停板 | 跌停板打开 |
| 有大买盘 | 买盘有大单 |
| 竞价上涨 | 集合竞价上涨 |
| 高开 5 日线 | 高开突破 5 日线 |
| 向上缺口 | 形成向上跳空缺口 |
| 60 日新高 | 创 60 日新高 |
| 60 日大幅上涨 | 60 日大幅上涨 |

### 4.2 卖出信号（绿色）

| 类型 | 说明 |
|------|------|
| 加速下跌 | 加速下跌 |
| 高台跳水 | 股价快速跳水 |
| 大笔卖出 | 大额卖单成交 |
| 封跌停板 | 跌停板封死 |
| 打开涨停板 | 涨停板打开 |
| 有大卖盘 | 卖盘有大单 |
| 竞价下跌 | 集合竞价下跌 |
| 低开 5 日线 | 低开跌破 5 日线 |
| 向下缺口 | 形成向下跳空缺口 |
| 60 日新低 | 创 60 日新低 |
| 60 日大幅下跌 | 60 日大幅下跌 |

---

## 五、使用指南

### 5.1 后端使用

```python
from app.adapters.eastmoney_adapter import EastMoneyAdapter

adapter = EastMoneyAdapter()
await adapter.initialize()

# 获取盘口异动
changes = await adapter.get_stock_changes('大笔买入')

# 获取板块异动
board_changes = await adapter.get_board_changes()

# 获取涨停股池
zt_pool = await adapter.get_zt_pool('20241008')

# 获取市场汇总
summary = await adapter.get_market_changes_summary()

await adapter.close()
```

### 5.2 前端使用

```typescript
import { eastMoneyApi } from '@/services/eastmoney';

// 获取盘口异动
const changes = await eastMoneyApi.getStockChanges('大笔买入');

// 获取板块异动
const boardChanges = await eastMoneyApi.getBoardChanges();

// 获取涨停股池
const ztPool = await eastMoneyApi.getZtPool('20241008');

// 获取市场汇总
const summary = await eastMoneyApi.getMarketChangesSummary();
```

---

## 六、数据来源

- **数据源：** 东方财富网
- **接口实现：** AKShare
- **目标地址：**
  - 盘口异动：http://quote.eastmoney.com/changes/
  - 涨停板行情：https://quote.eastmoney.com/ztb/detail

---

## 七、注意事项

### 7.1 数据限制

- 盘口异动：返回最近交易日数据
- 涨停股池：只能获取近期数据
- 缓存时间：60 秒

### 7.2 性能优化

- ✅ 启用缓存机制
- ✅ 异步数据获取
- ✅ 分批加载数据
- ✅ 前端虚拟列表（大数据量时）

### 7.3 错误处理

- 网络超时：10 秒
- 数据为空：返回空数组
- 异常捕获：记录日志并返回友好提示

---

## 八、后续优化

### 8.1 功能增强

- [ ] 添加实时推送（WebSocket）
- [ ] 支持自定义预警
- [ ] 添加异动趋势图表
- [ ] 支持历史数据查询

### 8.2 性能优化

- [ ] 增量更新机制
- [ ] 前端数据分页
- [ ] 服务端聚合统计
- [ ] 缓存策略优化

### 8.3 用户体验

- [ ] 添加筛选功能
- [ ] 支持导出 Excel
- [ ] 添加自选股异动监控
- [ ] 移动端适配

---

## 九、测试建议

### 9.1 后端测试

```bash
# 测试 API 端点
curl http://localhost:8000/api/v1/eastmoney/changes?symbol=大笔买入
curl http://localhost:8000/api/v1/eastmoney/board-changes
curl http://localhost:8000/api/v1/eastmoney/zt-pool
curl http://localhost:8000/api/v1/eastmoney/market-changes-summary
```

### 9.2 前端测试

```bash
cd frontend
npm run dev
# 访问 http://localhost:5173
```

---

## 十、相关文件清单

### 后端文件
- ✅ `backend/app/models/unified_models.py` - 数据模型
- ✅ `backend/app/adapters/eastmoney_adapter.py` - 数据适配器
- ✅ `backend/app/api/v1/endpoints/eastmoney.py` - API 端点
- ✅ `backend/app/api/v1/__init__.py` - 路由注册
- ✅ `backend/app/adapters/base.py` - 基础类（添加 EASTMONEY 枚举）

### 前端文件
- ✅ `frontend/src/services/eastmoney.ts` - API 服务
- ✅ `frontend/src/pages/EastMoneyChangesPage.tsx` - 盘口异动页面
- ✅ `frontend/src/pages/EastMoneyZtPoolPage.tsx` - 涨停板行情页面（旧版）
- ✅ `frontend/src/pages/EastMoneyZtBoardPage.tsx` - 综合涨停板行情页面（推荐）

---

**文档生成时间：** 2026-03-20  
**版本：** v1.1  
**状态：** ✅ 已完成并可用
