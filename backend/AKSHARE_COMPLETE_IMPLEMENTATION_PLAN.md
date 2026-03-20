# AKShare 122 个接口 - 完整实施方案（基于实测文章深度学习）

**制定时间**: 2026-03-20  
**参考来源**: 实测 Python AKShare 122 个股票数据接口（16 集系列）+ 龙虎榜/分红/解禁等专项实测  
**目标**: 基于实测结果，分阶段实现最有价值的 API 接口

---

## 📊 接口全景图（已实测验证）

### 已实现接口（30 个）✅

**基础数据** (3 个):
- ✅ `stock_info_sh_sz_name_code` - 沪深股票名称及代码
- ✅ `stock_info_a_code_name` - A 股股票代码及名称
- ✅ `stock_info_sh_delist` - 沪深 A 股退市股票

**实时行情** (5 个):
- ✅ `stock_zh_a_spot_em` - 全 A 股实时行情
- ✅ `stock_sh_a_spot_em` - 沪 A 股实时行情
- ✅ `stock_sz_a_spot_em` - 深 A 股实时行情
- ✅ `stock_bj_a_spot_em` - 京 A 股实时行情
- ✅ `stock_kc_a_spot_em` - 科创板实时行情

**K 线数据** (8 个):
- ✅ `stock_zh_a_hist` - A 股历史 K 线
- ✅ `stock_zh_a_hist_min_em` - A 股分时 K 线
- ✅ `stock_hk_hist` - 港股历史 K 线
- ✅ `stock_us_hist` - 美股历史 K 线
- ✅ 等...

**财务数据** (4 个):
- ✅ `stock_balance_sheet_by_report_em` - 资产负债表
- ✅ `stock_income_statement_by_report_em` - 利润表
- ✅ `stock_cash_flow_statement_by_report_em` - 现金流量表
- ✅ `stock_yjbg_em` - 业绩快报

**资金流向** (3 个):
- ✅ `stock_individual_fund_flow` - 个股资金流向
- ✅ `stock_market_fund_flow` - 市场资金流向
- ✅ `stock_board_industry_fund_flow` - 行业资金流向

**估值指标** (2 个):
- ✅ `stock_board_industry_name_em` - 行业估值
- ✅ `stock_board_concept_name_em` - 概念估值

**其他** (5 个):
- ✅ `stock_fhps_em` - 分红送转
- ✅ `get_individual_info()` - 个股详细资料
- ✅ `get_all_a_shares_spot()` - 全市场实时行情
- ✅ `get_performance_express()` - 业绩快报
- ✅ `get_restricted_share_unlock()` - 限售解禁

---

## 🎯 待实现接口（按实测价值排序）

### P0+ - 市场情绪监控（4 个）⭐⭐⭐⭐⭐

**实测验证**: 涨停/跌停数据是短线交易的核心参考

#### 1. 涨停股池 ⭐⭐⭐⭐⭐
**接口**: `stock_zt_pool_em()`

**实测数据字段**（16 个）:
- 代码、名称、涨跌幅、最新价
- 成交额、流通市值、总市值
- 换手率、封板资金
- 首次封板时间、最后封板时间
- 炸板次数、涨停统计、连板数
- 所属行业

**使用场景**:
- 涨停板复盘（每日必用）
- 连板股追踪（龙头识别）
- 市场情绪监控
- 封板质量分析

**实现难度**: ⭐

**缓存策略**: 1 天（历史数据不变）

---

#### 2. 跌停股池 ⭐⭐⭐⭐⭐
**接口**: `stock_zt_pool_dtgc_em()`

**实测数据字段**（16 个）:
- 代码、名称、涨跌幅、最新价
- 成交额、流通市值、总市值
- 动态市盈率、换手率
- 封单资金、最后封板时间
- 板上成交额、连续跌停、开板次数
- 所属行业

**使用场景**:
- 风险股监控
- 跌停板分析
- 弱势股识别
- 恐慌情绪判断

**实现难度**: ⭐

---

#### 3. 炸板股池 ⭐⭐⭐⭐
**接口**: `stock_zt_pool_zbgc_em()`

**实测数据字段**（16 个）:
- 代码、名称、涨跌幅、最新价、涨停价
- 成交额、流通市值、总市值
- 换手率、涨速
- 首次封板时间、炸板次数、涨停统计
- 振幅、所属行业

**使用场景**:
- 炸板股分析
- 封板质量评估
- 主力出货识别

**实现难度**: ⭐

---

#### 4. 创新高/新低统计 ⭐⭐⭐⭐⭐
**接口**: `stock_a_high_low_statistics()`

**实测数据字段**（8 个）:
- date: 交易日
- close: 相关指数收盘价
- high20/low20: 20 日新高/新低数量
- high60/low60: 60 日新高/新低数量
- high120/low120: 120 日新高/新低数量

**参数**:
- symbol: "all"（全部 A 股）、"sz50"、"hs300"、"zz500"

**使用场景**:
- 市场趋势判断
- 情绪周期分析
- 牛熊分界监控

**实现难度**: ⭐

---

### P0+ - 龙虎榜系列（6 个）⭐⭐⭐⭐⭐

**实测验证**: 龙虎榜数据是洞察主力动向的核心窗口

#### 5. 龙虎榜详情 ⭐⭐⭐⭐⭐
**接口**: `stock_lhb_detail_em()`

**实测数据字段**（21 个）:
- 代码、名称、上榜日
- 收盘价、涨跌幅
- 龙虎榜净买额、买入额、卖出额、成交额
- 市场总成交额
- 净买额占比、成交额占比
- 换手率、流通市值
- 上榜原因
- 上榜后 1/2/5/10 日涨跌幅

**参数**:
- start_date, end_date

**使用场景**:
- 主力动向追踪
- 游资席位分析
- 个股热度判断

**实现难度**: ⭐⭐

---

#### 6. 机构买卖统计 ⭐⭐⭐⭐⭐
**接口**: `stock_lhb_jgmmtj_em()`

**实测数据字段**（16 个）:
- 代码、名称
- 收盘价、涨跌幅
- 买方机构数、卖方机构数
- 机构买入总额、卖出总额、净额
- 市场总成交额
- 机构净买额占比
- 换手率、流通市值
- 上榜原因、上榜日期

**使用场景**:
- 机构动向分析
- 主力持仓判断

**实现难度**: ⭐⭐

---

#### 7. 营业部排行 ⭐⭐⭐⭐⭐
**接口**: `stock_lhb_yybph_em()`

**实测数据字段**（17 个）:
- 营业部名称
- 上榜后 1/2/3/4/10 天数据:
  - 买入次数
  - 平均涨幅
  - 上涨概率

**参数**:
- symbol: "近一月"、"近三月"、"近六月"、"近一年"

**使用场景**:
- 知名游资追踪
- 营业部胜率分析
- 龙虎榜跟车策略

**实现难度**: ⭐

---

#### 8. 龙虎榜详情（新浪） ⭐⭐⭐
**接口**: `stock_lhb_detail_daily_sina()`

**数据字段**:
- 股票代码、名称
- 收盘价、对应值
- 成交量、成交额
- 指标（振幅值、换手率、涨幅偏离值等）

**使用场景**:
- 多数据源验证

---

### P1 - 财务深度（4 个）⭐⭐⭐⭐⭐

**实测验证**: 财务指标是价值投资的核心依据

#### 9. 财务分析主要指标 ⭐⭐⭐⭐⭐
**接口**: `stock_financial_analysis_indicator_em()`

**实测数据字段**（60+ 个）:
**核心指标**:
- EPS: 基本每股收益、扣非每股收益、稀释每股收益
- BPS: 每股净资产
- 每股公积金、每股未分配利润、每股经营现金流
- 营业总收入、毛利润、归属净利润、扣非净利润
- 营业总收入同比增长、归属净利润同比增长
- ROE: 净资产收益率（加权）、ROE（扣非/加权）
- 毛利率、净利率、实际税率
- 流动比率、速动比率、资产负债率
- 总资产周转率、存货周转率、应收账款周转率

**参数**:
- symbol: 股票代码
- indicator: "按报告期"、"按单季度"

**使用场景**:
- 财务健康度分析
- 成长性筛选
- ROE 选股策略

**实现难度**: ⭐⭐

---

#### 10. 历史分红 ⭐⭐⭐⭐
**接口**: `stock_history_dividend()`

**实测数据字段**（8 个）:
- 代码、名称、上市日期
- 累计股息、年均股息
- 分红次数
- 融资总额、融资次数

**使用场景**:
- 高股息率选股
- 分红历史记录

**实现难度**: ⭐

---

#### 11. 分红详情（巨潮） ⭐⭐⭐⭐
**接口**: `stock_dividend_cninfo()`

**实测数据字段**（12 个）:
- 实施方案公告日期
- 送股比例、转增比例、派息比例
- 股权登记日、除权日、派息日
- 分红类型、报告时间

**使用场景**:
- 分红方案详情

---

### P1 - 限售解禁（3 个）⭐⭐⭐⭐

**实测验证**: 解禁数据是风险预警的重要参考

#### 12. 限售解禁详情 ⭐⭐⭐⭐⭐
**接口**: `stock_restricted_release_detail_em()`

**实测数据字段**（12 个）:
- 股票代码、股票简称
- 解禁时间
- 限售股类型、解禁数量、实际解禁数量
- 实际解禁市值
- 占解禁前流通市值比例
- 解禁前一交易日收盘价
- 解禁前 20 日涨跌幅、解禁后 20 日涨跌幅

**参数**:
- start_date, end_date

**使用场景**:
- 解禁风险预警
- 抛压分析

**实现难度**: ⭐⭐

---

#### 13. 解禁批次 ⭐⭐⭐⭐
**接口**: `stock_restricted_release_queue_em()`

**实测数据字段**（13 个）:
- 解禁时间、解禁股东数
- 解禁数量、实际解禁数量、未解禁数量
- 实际解禁数量市值
- 占总市值比例、占流通市值比例
- 解禁前一交易日收盘价
- 限售股类型
- 解禁前/后 20 日涨跌幅

**使用场景**:
- 个股解禁历史

---

#### 14. 解禁股东 ⭐⭐⭐
**接口**: `stock_restricted_release_stockholder_em()`

**实测数据字段**（10 个）:
- 股东名称
- 解禁数量、实际解禁数量
- 解禁市值
- 锁定期、剩余未解禁数量
- 限售股类型、进度

**使用场景**:
- 股东解禁详情

---

### P2 - 盘口异动（2 个）⭐⭐⭐⭐

**实测验证**: 盘口异动是短线捕捉热点的利器

#### 15. 盘口异动数据 ⭐⭐⭐⭐
**接口**: `stock_changes_em()`

**异动类型**:
- 火箭发射、快速反弹
- 大笔买入、大笔卖出
- 封涨停板、打开跌停板
- 竞价上涨、竞价下跌
- 60 日新高、60 日新低
- 等 20+ 种异动

**实测数据字段**（5 个）:
- 时间、代码、名称
- 板块、相关信息

**使用场景**:
- 短线机会捕捉
- 主力资金追踪

**实现难度**: ⭐⭐

---

#### 16. 板块异动详情 ⭐⭐⭐⭐
**接口**: `stock_board_change_em()`

**实测数据字段**（8 个）:
- 板块名称、涨跌幅
- 主力净流入
- 板块异动总次数
- 板块异动最频繁个股及类型
- 板块具体异动类型列表及次数

**使用场景**:
- 热点板块追踪
- 板块轮动分析

---

## 📋 分阶段实施计划

### 第一阶段（1 周）- 市场情绪监控 ⭐⭐⭐⭐⭐

**目标**: 实现涨停/跌停监控

**任务**:
1. ✅ 涨停股池 `stock_zt_pool_em()`
2. ✅ 跌停股池 `stock_zt_pool_dtgc_em()`
3. ✅ 炸板股池 `stock_zt_pool_zbgc_em()`
4. ✅ 创新高/新低统计 `stock_a_high_low_statistics()`

**预期成果**:
- 涨停复盘功能
- 市场情绪监控面板
- 连板股追踪

**API 端点**:
```
GET /api/v1/market/limit-up/{date}
GET /api/v1/market/limit-down/{date}
GET /api/v1/market/broken-limit/{date}
GET /api/v1/market/high-low-statistics
```

---

### 第二阶段（1 周）- 龙虎榜系列 ⭐⭐⭐⭐⭐

**目标**: 实现龙虎榜数据

**任务**:
1. ✅ 龙虎榜详情 `stock_lhb_detail_em()`
2. ✅ 机构买卖统计 `stock_lhb_jgmmtj_em()`
3. ✅ 营业部排行 `stock_lhb_yybph_em()`

**预期成果**:
- 龙虎榜复盘
- 机构动向分析
- 游资席位追踪

**API 端点**:
```
GET /api/v1/market/lhb-detail/{start_date}/{end_date}
GET /api/v1/market/lhb-institution/{start_date}/{end_date}
GET /api/v1/market/lhb-yyb-rank/{period}
```

---

### 第三阶段（1 周）- 财务深度 ⭐⭐⭐⭐⭐

**目标**: 实现财务指标深度分析

**任务**:
1. ✅ 财务分析主要指标 `stock_financial_analysis_indicator_em()`
2. ✅ 历史分红 `stock_history_dividend()`
3. ✅ 分红详情 `stock_dividend_cninfo()`

**预期成果**:
- 财务健康度评分
- ROE 选股策略
- 高股息率股票池

**API 端点**:
```
GET /api/v1/stock/{code}/financial-indicators
GET /api/v1/stock/{code}/dividend-history
GET /api/v1/stock/{code}/dividend-detail
```

---

### 第四阶段（1 周）- 限售解禁 ⭐⭐⭐⭐

**目标**: 实现解禁风险预警

**任务**:
1. ✅ 限售解禁详情 `stock_restricted_release_detail_em()`
2. ✅ 解禁批次 `stock_restricted_release_queue_em()`
3. ✅ 解禁股东 `stock_restricted_release_stockholder_em()`

**预期成果**:
- 解禁风险预警
- 抛压分析

**API 端点**:
```
GET /api/v1/stock/restricted-release/{start_date}/{end_date}
GET /api/v1/stock/{code}/restricted-queue
GET /api/v1/stock/{code}/restricted-stockholder/{date}
```

---

### 第五阶段（1 周）- 盘口异动 ⭐⭐⭐⭐

**目标**: 实现盘口异动监控

**任务**:
1. ✅ 盘口异动数据 `stock_changes_em()`
2. ✅ 板块异动详情 `stock_board_change_em()`

**预期成果**:
- 短线机会捕捉
- 热点板块追踪

**API 端点**:
```
GET /api/v1/market/changes/{symbol}
GET /api/v1/market/board-change
```

---

## 🔧 技术实现要点

### 1. 数据模型定义（基于实测字段）

```python
@dataclass
class LimitUpStock:
    """涨停股"""
    code: str
    name: str
    change_pct: float
    latest_price: float
    turnover_rate: float
    limit_up_count: int  # 连板数
    first_limit_time: str
    last_limit_time: str
    seal_amount: float  # 封板资金
    industry: str

@dataclass
class LHBEntry:
    """龙虎榜条目"""
    code: str
    name: str
    close_price: float
    change_pct: float
    lhb_net_buy: float  # 龙虎榜净买额
    lhb_buy: float  # 买入额
    lhb_sell: float  # 卖出额
    lhb_turnover: float  # 成交额
    market_turnover: float  # 市场总成交额
    net_ratio: float  # 净买额占比
    turnover_ratio: float  # 成交额占比
    reason: str  # 上榜原因
    post_1d_change: float  # 上榜后 1 日涨跌幅
    post_2d_change: float
    post_5d_change: float
    post_10d_change: float

@dataclass
class FinancialIndicator:
    """财务指标"""
    code: str
    report_date: str
    eps_basic: float  # 基本每股收益
    eps_diluted: float  # 稀释每股收益
    bps: float  # 每股净资产
    roe_weighted: float  # ROE（加权）
    gross_margin: float  # 毛利率
    net_margin: float  # 净利率
    revenue_growth: float  # 营收同比增长
    net_profit_growth: float  # 净利润同比增长
    asset_liability_ratio: float  # 资产负债率
```

### 2. 缓存策略（基于数据特性）

| 数据类型 | 缓存时间 | 说明 |
|----------|----------|------|
| 涨停/跌停 | 1 天 | 历史数据不变 |
| 龙虎榜 | 1 天 | 每日更新 |
| 财务指标 | 1 周 | 季报更新 |
| 分红数据 | 1 周 | 定期报告 |
| 解禁数据 | 1 天 | 历史数据不变 |
| 盘口异动 | 实时 | 盘中实时更新 |

### 3. 反风控措施

- User-Agent 轮换
- 频率控制（自适应延迟）
- 本地缓存优化
- 失败重试机制
- 异常熔断机制

---

## 📊 预期收益

### 功能增强

| 功能模块 | 当前 | 实施后 | 提升 |
|----------|------|--------|------|
| **市场情绪** | 0 个 | 4 个 | +∞ |
| **龙虎榜** | 0 个 | 6 个 | +∞ |
| **财务分析** | 4 个 | 8 个 | +100% |
| **风险预警** | 1 个 | 4 个 | +300% |
| **盘口监控** | 0 个 | 2 个 | +∞ |

### 使用场景

1. **涨停复盘**: 每日涨停股统计、连板股追踪
2. **龙虎榜分析**: 主力动向、游资席位
3. **财务选股**: ROE、毛利率、成长性
4. **风险预警**: 解禁抛压、跌停监控
5. **短线机会**: 盘口异动、板块轮动

---

## 📚 参考资料

- [实测 Python AKShare 122 个股票数据接口（16 集系列）](https://www.toutiao.com/article/7588400522185540146/)
- [龙虎榜数据接口实测](https://www.toutiao.com/article/7590343240868545070/)
- [分红送转接口实测](https://www.toutiao.com/article/7591129327861858862/)
- [限售解禁接口实测](https://www.toutiao.com/article/7591314742577250842/)
- [财务指标接口实测](https://www.toutiao.com/article/7589606831790604826/)
- [财务报表接口实测](https://www.toutiao.com/article/7589600546181497395/)
- [盘口异动接口实测](https://www.toutiao.com/article/7590697016754323994/)

---

**制定者**: AI Code Assistant  
**制定时间**: 2026-03-20  
**建议**: 优先实施**市场情绪监控类 API**（涨停/跌停/创新高统计），这类数据对于短线交易和情绪判断最有价值！
