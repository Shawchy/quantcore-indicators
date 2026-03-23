# 东方财富个股研报和公告功能更新日志 - v1.3

**更新日期：** 2026-03-20  
**版本：** v1.3  
**类型：** 功能增强

---

## 🎉 新增功能

### 1. 个股研报接口

新增东方财富个股研报功能，提供全面的个股研究报告数据。

#### 1.1 个股研报 (stock_research_report_em)
- **接口路径：** `/api/v1/eastmoney/stock-research-report/{symbol}`
- **描述：** 获取指定股票的所有研究报告
- **参数：** `symbol` - 股票代码（路径参数）
- **输出字段：**
  - 序号、股票代码、股票简称
  - 报告名称、东财评级、机构
  - 近一月个股研报数
  - 2024-2026 盈利预测（收益、市盈率）
  - 行业、日期、报告 PDF 链接

**数据特点：**
- 包含历史所有研报
- 提供盈利预测数据
- 支持 PDF 报告链接
- 覆盖全市场股票

### 2. 沪深京 A 股公告接口

#### 2.1 公告大全 (stock_notice_report)
- **接口路径：** `/api/v1/eastmoney/stock-notice-report`
- **描述：** 获取沪深京 A 股公告
- **参数：**
  - `symbol` - 公告类型（可选）
    - 全部、重大事项、财务报告、融资公告、风险提示、资产重组、信息变更、持股变动
  - `date` - 日期（可选，格式 YYYYMMDD，默认为今日）
- **输出字段：**
  - 代码、名称
  - 公告标题、公告类型
  - 公告日期、网址

**数据特点：**
- 支持 8 种公告类型筛选
- 支持历史日期查询
- 提供公告原文链接
- 每日更新

---

## 📝 后端实现

### 2.1 数据模型

**文件：** `backend/app/models/unified_models.py`

新增 2 个数据模型：

```python
class StockResearchReport(BaseModel):
    """个股研报数据模型"""
    serial_no: int                    # 序号
    stock_code: str                   # 股票代码
    stock_name: str                   # 股票简称
    report_name: str                  # 报告名称
    rating: str                       # 东财评级
    institution: str                  # 机构
    recent_report_count: int          # 近一月个股研报数
    forecast_2024_eps: Optional[float]  # 2024 盈利预测 - 收益
    forecast_2024_pe: Optional[float]   # 2024 盈利预测 - 市盈率
    forecast_2025_eps: Optional[float]  # 2025 盈利预测 - 收益
    forecast_2025_pe: Optional[float]   # 2025 盈利预测 - 市盈率
    forecast_2026_eps: Optional[float]  # 2026 盈利预测 - 收益
    forecast_2026_pe: Optional[float]   # 2026 盈利预测 - 市盈率
    industry: str                     # 行业
    report_date: str                  # 日期
    report_pdf_url: str               # 报告 PDF 链接

class StockNotice(BaseModel):
    """沪深京 A 股公告数据模型"""
    code: str                         # 代码
    name: str                         # 名称
    notice_title: str                 # 公告标题
    notice_type: str                  # 公告类型
    notice_date: str                  # 公告日期
    url: str                          # 网址
```

### 2.2 适配器方法

**文件：** `backend/app/adapters/eastmoney_adapter.py`

新增 2 个适配器方法：

```python
async def get_stock_research_report(self, symbol: str) -> List[StockResearchReport]:
    """获取个股研报数据"""
    
async def get_stock_notice_report(
    self, 
    symbol: str = "全部", 
    date: Optional[str] = None
) -> List[StockNotice]:
    """获取沪深京 A 股公告"""
```

**特性：**
- ✅ 支持个股研报全量获取
- ✅ 支持公告类型筛选
- ✅ 支持日期查询
- ✅ 60 秒缓存机制
- ✅ 异步数据获取
- ✅ 基于 AKShare 实现

### 2.3 API 端点

**文件：** `backend/app/api/v1/endpoints/eastmoney.py`

新增 2 个 API 端点：

| 接口 | 路径 | 方法 | 描述 |
|------|------|------|------|
| 个股研报 | `/api/v1/eastmoney/stock-research-report/{symbol}` | GET | 获取个股研报 |
| 公告大全 | `/api/v1/eastmoney/stock-notice-report` | GET | 获取沪深京公告 |

---

## 🎨 前端实现

### 3.1 服务接口

**文件：** `frontend/src/services/eastmoney.ts`

新增 TypeScript 接口和 API 方法：

```typescript
// 数据接口
export interface StockResearchReport { ... }
export interface StockNotice { ... }

// API 方法
getStockResearchReport: (symbol: string) => ...
getStockNoticeReport: (symbol: string, date?: string) => ...
```

### 3.2 页面组件

**文件：** `frontend/src/pages/EastMoneyResearchNoticePage.tsx`

新建研报公告页面，包含两个 Tab：

**Tab 1：个股研报**
- ✅ 股票代码输入框
- ✅ 研报数据表格
- ✅ 评级颜色标识（买入=绿色，增持=蓝色）
- ✅ PDF 报告链接（外链）
- ✅ 盈利预测数据展示

**Tab 2：沪深京公告**
- ✅ 公告类型下拉选择（8 种类型）
- ✅ 日期选择器
- ✅ 公告数据表格
- ✅ 公告原文链接（外链）
- ✅ Toast 提示反馈

**页面特性：**
- Tab 切换展示
- 响应式表格布局
- 外部链接直接打开
- 加载状态提示
- 错误提示友好

---

## 📊 接口示例

### 1. 获取个股研报

```bash
GET /api/v1/eastmoney/stock-research-report/000001
```

响应示例：
```json
{
  "code": 0,
  "message": "获取成功，共 277 条",
  "data": [
    {
      "serial_no": 1,
      "stock_code": "000001",
      "stock_name": "平安银行",
      "report_name": "深度研究报告",
      "rating": "买入",
      "institution": "国信证券",
      "recent_report_count": 10,
      "forecast_2024_eps": 1.23,
      "forecast_2024_pe": 8.5,
      "forecast_2025_eps": 1.45,
      "forecast_2025_pe": 7.2,
      "forecast_2026_eps": 1.67,
      "forecast_2026_pe": 6.3,
      "industry": "银行",
      "report_date": "2025-01-10",
      "report_pdf_url": "https://pdf.dfcfw.com/pdf/H3_AP202501101641890..."
    }
  ]
}
```

### 2. 获取公告

```bash
GET /api/v1/eastmoney/stock-notice-report?symbol=财务报告&date=20240613
```

响应示例：
```json
{
  "code": 0,
  "message": "获取成功，共 139 条",
  "data": [
    {
      "code": "123122",
      "name": "某某转债",
      "notice_title": "2024 年年度报告",
      "notice_type": "财务报告",
      "notice_date": "2024-06-13",
      "url": "https://data.eastmoney.com/notices/detail/1231..."
    }
  ]
}
```

---

## 🎯 使用场景

### 1. 个股研报查询
- 查看券商对个股的评级
- 了解盈利预测数据
- 追踪机构观点变化
- 下载 PDF 原文报告

### 2. 公告信息获取
- 查看公司最新公告
- 筛选财务报告
- 关注重大事项
- 追踪风险提示

### 3. 投资决策支持
- 综合多家机构观点
- 分析盈利预测趋势
- 及时了解公司动态
- 评估投资风险

---

## 📈 数据说明

### 评级说明
- **买入：** 预期涨幅超过 15%
- **增持：** 预期涨幅 5%-15%
- **中性：** 预期涨幅-5%-5%
- **减持：** 预期跌幅超过 5%
- **卖出：** 强烈看空

### 盈利预测
- **EPS（每股收益）：** 预测未来几年的每股收益
- **PE（市盈率）：** 预测未来几年的市盈率
- 数据来源：各券商研究报告
- 仅供参考，不构成投资建议

### 公告类型
- **全部：** 所有类型公告
- **重大事项：** 重大经营决策、并购重组等
- **财务报告：** 年报、季报、业绩预告等
- **融资公告：** 增发、配股、债券发行等
- **风险提示：** 风险警示、诉讼等
- **资产重组：** 资产收购、出售等
- **信息变更：** 公司名称、地址变更等
- **持股变动：** 股东增减持等

---

## 🔧 技术亮点

### 1. 数据处理
- ✅ 支持大量数据加载（数百条研报）
- ✅ 可选值处理（盈利预测可能为空）
- ✅ PDF 链接提取
- ✅ 高效缓存机制

### 2. 用户体验
- ✅ Tab 切换展示
- ✅ 搜索提示
- ✅ 外部链接直接打开
- ✅ Toast 反馈提示
- ✅ 加载状态显示

### 3. 性能优化
- ✅ 60 秒缓存
- ✅ 异步数据获取
- ✅ 按需加载
- ✅ 表格虚拟滚动（大数据量时）

---

## ⚠️ 注意事项

### 1. 数据更新
- 个股研报：不定时更新（券商发布）
- 公告数据：每日更新
- 盈利预测：多家机构可能不同

### 2. 数据说明
- 研报数据来自各大券商
- 盈利预测为机构预测值
- 评级标准可能因机构而异
- PDF 链接可能失效

### 3. 使用建议
- 仅供参考，不构成投资建议
- 建议查看原文报告
- 关注多家机构观点
- 注意数据时效性

---

## 📚 相关文件

### 后端文件
- ✅ `backend/app/models/unified_models.py` - 数据模型
- ✅ `backend/app/adapters/eastmoney_adapter.py` - 数据适配器
- ✅ `backend/app/api/v1/endpoints/eastmoney.py` - API 端点

### 前端文件
- ✅ `frontend/src/services/eastmoney.ts` - API 服务
- ✅ `frontend/src/pages/EastMoneyResearchNoticePage.tsx` - 页面组件
- ✅ `frontend/src/App.tsx` - 路由配置
- ✅ `frontend/src/components/Sidebar.tsx` - 菜单配置

---

## 🔗 相关链接

- 东方财富个股研报：https://data.eastmoney.com/report/stock.jshtml
- 东方财富公告大全：https://data.eastmoney.com/notices/hsa/5.html
- AKShare 文档：https://akshare.akfamily.xyz/

---

## 📋 菜单结构

东方财富模块现在包含 4 个子功能：

```
东方财富 (FiCpu)
├── 涨停板行情 → /eastmoney/zt-board
├── 盘口异动 → /eastmoney/changes
├── 千股千评 → /eastmoney/stock-comment
└── 研报公告 → /eastmoney/research-notice (新增)
```

---

## 📊 功能总览

东方财富模块现已提供 **13 个 API 接口**：

| 类别 | 接口数量 | 接口列表 |
|------|---------|---------|
| 盘口异动 | 2 | changes, board-changes |
| 涨停板 | 4 | zt-pool, zt-pool-previous, zt-pool-strong, zt-pool-sub-new |
| 千股千评 | 3 | stock-comment, stock-comment-detail-institution, stock-comment-detail-score |
| 研报公告 | 2 | stock-research-report, stock-notice-report |
| 市场汇总 | 1 | market-changes-summary |
| 基础数据 | 1 | change-types |

---

**更新完成！** 🎉

个股研报和公告功能已完整实现，提供全面的研究报告和公告信息查询功能！
