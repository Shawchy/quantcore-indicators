# 东方财富千股千评功能更新日志 - v1.2

**更新日期：** 2026-03-20  
**版本：** v1.2  
**类型：** 功能增强

---

## 🎉 新增功能

### 1. 千股千评接口

新增东方财富千股千评功能，提供全面的个股综合评价数据。

#### 1.1 千股千评总览 (stock_comment_em)
- **接口路径：** `/api/v1/eastmoney/stock-comment`
- **描述：** 获取所有股票的千股千评综合数据
- **参数：** 无
- **输出字段：**
  - 序号、代码、名称
  - 最新价、涨跌幅
  - 换手率、市盈率
  - 主力成本、机构参与度
  - 综合得分、上升、目前排名
  - 关注指数、交易日

**数据特点：**
- 覆盖全市场所有股票
- 每日盘后更新
- 包含多维度评价指标

#### 1.2 主力控盘 - 机构参与度 (stock_comment_detail_zlkp_jgcyd_em)
- **接口路径：** `/api/v1/eastmoney/stock-comment-detail-institution/{symbol}`
- **描述：** 获取指定股票的历史机构参与度数据
- **参数：** `symbol` - 股票代码（路径参数）
- **输出字段：**
  - 交易日
  - 机构参与度（%）

**数据说明：**
- 机构参与度反映主力控盘程度
- 提供历史趋势数据
- 帮助判断主力动向

#### 1.3 综合评价 - 历史评分 (stock_comment_detail_zhpj_lspf_em)
- **接口路径：** `/api/v1/eastmoney/stock-comment-detail-score/{symbol}`
- **描述：** 获取指定股票的历史综合评分
- **参数：** `symbol` - 股票代码（路径参数）
- **输出字段：**
  - 交易日
  - 综合评分（0-100 分）

**数据说明：**
- 综合评分反映股票整体质量
- 分数越高表示综合评价越好
- 提供历史变化趋势

---

## 📝 后端实现

### 2.1 数据模型

**文件：** `backend/app/models/unified_models.py`

新增 3 个数据模型：

```python
class StockComment(BaseModel):
    """千股千评数据模型"""
    serial_no: int                    # 序号
    code: str                         # 股票代码
    name: str                         # 股票名称
    latest_price: float               # 最新价
    change_pct: float                 # 涨跌幅（%）
    turnover_rate: float              # 换手率（%）
    pe_ratio: float                   # 市盈率
    main_force_cost: float            # 主力成本
    institution_participation: float  # 机构参与度（%）
    comprehensive_score: float        # 综合得分
    rise: int                         # 上升（正负号）
    current_rank: int                 # 目前排名
    attention_index: float            # 关注指数
    trading_day: str                  # 交易日

class StockCommentDetailInstitution(BaseModel):
    """千股千评详情 - 主力控盘 - 机构参与度"""
    trading_day: str                  # 交易日
    institution_participation: float  # 机构参与度（%）

class StockCommentDetailScore(BaseModel):
    """千股千评详情 - 综合评价 - 历史评分"""
    trading_day: str                  # 交易日
    score: float                      # 评分
```

### 2.2 适配器方法

**文件：** `backend/app/adapters/eastmoney_adapter.py`

新增 3 个适配器方法：

```python
async def get_stock_comment(self) -> List[StockComment]:
    """获取千股千评数据"""
    
async def get_stock_comment_detail_institution(self, symbol: str) -> List[StockCommentDetailInstitution]:
    """获取主力控盘 - 机构参与度"""
    
async def get_stock_comment_detail_score(self, symbol: str) -> List[StockCommentDetailScore]:
    """获取综合评价 - 历史评分"""
```

**特性：**
- ✅ 支持全量数据获取
- ✅ 支持个股详情查询
- ✅ 60 秒缓存机制
- ✅ 异步数据获取
- ✅ 基于 AKShare 实现

### 2.3 API 端点

**文件：** `backend/app/api/v1/endpoints/eastmoney.py`

新增 3 个 API 端点：

| 接口 | 路径 | 方法 | 描述 |
|------|------|------|------|
| 千股千评 | `/api/v1/eastmoney/stock-comment` | GET | 获取所有股票千股千评 |
| 机构参与度 | `/api/v1/eastmoney/stock-comment-detail-institution/{symbol}` | GET | 获取个股机构参与度历史 |
| 历史评分 | `/api/v1/eastmoney/stock-comment-detail-score/{symbol}` | GET | 获取个股历史评分 |

---

## 🎨 前端实现

### 3.1 服务接口

**文件：** `frontend/src/services/eastmoney.ts`

新增 TypeScript 接口和 API 方法：

```typescript
// 数据接口
export interface StockComment { ... }
export interface StockCommentDetailInstitution { ... }
export interface StockCommentDetailScore { ... }

// API 方法
getStockComment: () => ...
getStockCommentDetailInstitution: (symbol: string) => ...
getStockCommentDetailScore: (symbol: string) => ...
```

### 3.2 页面组件

**文件：** `frontend/src/pages/EastMoneyStockCommentPage.tsx`

新建千股千评页面，包含以下功能：

**主要功能：**
- ✅ 全市场股票列表展示
- ✅ 股票代码/名称搜索
- ✅ 综合统计信息
- ✅ 个股详情弹窗
- ✅ 机构参与度趋势图
- ✅ 历史评分趋势图

**页面特性：**
- 颜色标识（红色=上涨/积极，绿色=下跌/消极）
- 机构参与度高亮（>30% 显示红色徽章）
- 综合得分颜色区分（>60 分显示绿色徽章）
- 响应式表格布局
- 图表可视化展示

**统计卡片：**
- 股票总数
- 上涨股票数
- 下跌股票数
- 平均综合得分

**详情弹窗：**
- Tab 切换展示
  - 机构参与度趋势（折线图）
  - 历史评分趋势（折线图）
- 使用 Recharts 图表库
- 交互式数据展示

---

## 📊 接口示例

### 1. 获取千股千评

```bash
GET /api/v1/eastmoney/stock-comment
```

响应示例：
```json
{
  "code": 0,
  "message": "获取成功，共 5081 条",
  "data": [
    {
      "serial_no": 1,
      "code": "000001",
      "name": "平安银行",
      "latest_price": 10.50,
      "change_pct": -1.01,
      "turnover_rate": 0.43,
      "pe_ratio": 4.90,
      "main_force_cost": 10.84,
      "institution_participation": 43.84,
      "comprehensive_score": 64.67,
      "rise": 1090,
      "current_rank": 1608,
      "attention_index": 87.6,
      "trading_day": "2024-09-25"
    }
  ]
}
```

### 2. 获取机构参与度

```bash
GET /api/v1/eastmoney/stock-comment-detail-institution/600000
```

响应示例：
```json
{
  "code": 0,
  "message": "获取成功，共 40 条",
  "data": [
    {
      "trading_day": "2024-07-25",
      "institution_participation": 28.91
    },
    {
      "trading_day": "2024-07-26",
      "institution_participation": 30.97
    }
  ]
}
```

### 3. 获取历史评分

```bash
GET /api/v1/eastmoney/stock-comment-detail-score/600000
```

响应示例：
```json
{
  "code": 0,
  "message": "获取成功，共 40 条",
  "data": [
    {
      "trading_day": "2024-08-13",
      "score": 62.51
    },
    {
      "trading_day": "2024-08-14",
      "score": 61.67
    }
  ]
}
```

---

## 🎯 使用场景

### 1. 个股综合评价
- 查看股票综合得分
- 了解机构参与度
- 判断主力控盘程度
- 评估股票整体质量

### 2. 趋势分析
- 观察机构参与度变化趋势
- 追踪历史评分走势
- 发现主力动向
- 预测股票表现

### 3. 选股参考
- 筛选高综合得分股票
- 寻找机构高度控盘股票
- 关注评分上升趋势股票
- 发现被低估的股票

---

## 📈 数据说明

### 综合评分
- **评分范围：** 0-100 分
- **评分维度：**
  - 主力控盘
  - 舆情监控
  - 市场热度
  - 趋势研判
  - 资金动向
  - 财务评估
- **评分说明：**
  - 60 分以上：表现良好
  - 70 分以上：表现优秀
  - 80 分以上：表现极佳

### 机构参与度
- **计算方式：** 基于机构持仓、交易活跃度等数据
- **参与程度分类：**
  - < 20%：低度参与
  - 20%-40%：中度参与
  - > 40%：高度参与（完全控盘）
- **参考意义：**
  - 高参与度表示主力控盘明显
  - 持续上升表示主力介入加深
  - 大幅下降可能表示主力撤离

### 上升指标
- **含义：** 综合评分变化趋势
- **正值：** 评分上升，排名提升
- **负值：** 评分下降，排名下滑
- **绝对值：** 变化幅度

---

## 🔧 技术亮点

### 1. 数据处理
- ✅ 全量数据加载（5000+ 股票）
- ✅ 高效缓存机制
- ✅ 异步并发请求
- ✅ 数据格式统一

### 2. 可视化展示
- ✅ Recharts 图表库集成
- ✅ 交互式趋势图
- ✅ 实时数据更新
- ✅ 响应式设计

### 3. 用户体验
- ✅ 快速搜索功能
- ✅ 详情弹窗展示
- ✅ 颜色标识直观
- ✅ 统计信息一目了然

---

## ⚠️ 注意事项

### 1. 数据更新
- 千股千评数据：每日盘后更新
- 历史数据：提供最近几个月数据
- 实时性：T+1 更新机制

### 2. 性能考虑
- 全量数据较大（5000+ 条）
- 已实现 60 秒缓存
- 建议合理设置刷新频率
- 大数据量时使用搜索过滤

### 3. 数据说明
- 评分仅供参考，不构成投资建议
- 机构参与度为估算值
- 历史数据不代表未来表现

---

## 📚 相关文件

### 后端文件
- ✅ `backend/app/models/unified_models.py` - 数据模型
- ✅ `backend/app/adapters/eastmoney_adapter.py` - 数据适配器
- ✅ `backend/app/api/v1/endpoints/eastmoney.py` - API 端点

### 前端文件
- ✅ `frontend/src/services/eastmoney.ts` - API 服务
- ✅ `frontend/src/pages/EastMoneyStockCommentPage.tsx` - 页面组件
- ✅ `frontend/src/App.tsx` - 路由配置
- ✅ `frontend/src/components/Sidebar.tsx` - 菜单配置

---

## 🔗 相关链接

- 东方财富千股千评：https://data.eastmoney.com/stockcomment/
- 个股示例（浦发银行）：https://data.eastmoney.com/stockcomment/stock/600000.html
- AKShare 文档：https://akshare.akfamily.xyz/

---

## 📋 菜单结构

东方财富模块现在包含 3 个子功能：

```
东方财富 (FiCpu)
├── 涨停板行情 → /eastmoney/zt-board
├── 盘口异动 → /eastmoney/changes
└── 千股千评 → /eastmoney/stock-comment (新增)
```

---

**更新完成！** 🎉

千股千评功能已完整实现，提供全面的个股综合评价和趋势分析功能！
