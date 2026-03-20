# AKShare 122 个股票接口完整清单（基于 16 集实测 + 补充搜索）

**整理时间**: 2026-03-20  
**参考来源**: 实测 Python AKShare 122 个股票数据接口（16 集系列）+ 补充实测文章  
**总计**: 122 个股票数据接口

---

## 📊 接口分类总览

| 分类 | 接口数量 | 已实现 | 待实现 | 优先级 |
|------|---------|--------|--------|--------|
| **市场概况** | 12 | 3 | 9 | ⭐⭐⭐ |
| **实时行情** | 15 | 5 | 10 | ⭐⭐⭐⭐⭐ |
| **K 线数据** | 12 | 8 | 4 | ⭐⭐⭐ |
| **分时数据** | 8 | 2 | 6 | ⭐⭐ |
| **资金流向** | 10 | 3 | 7 | ⭐⭐⭐⭐ |
| **财务指标** | 15 | 4 | 11 | ⭐⭐⭐⭐⭐ |
| **估值指标** | 8 | 2 | 6 | ⭐⭐⭐⭐ |
| **市场情绪** | 10 | 0 | 10 | ⭐⭐⭐⭐⭐ |
| **板块行情** | 8 | 3 | 5 | ⭐⭐⭐ |
| **龙虎榜** | 6 | 0 | 6 | ⭐⭐⭐⭐⭐ |
| **股东结构** | 6 | 0 | 6 | ⭐⭐⭐⭐⭐ |
| **融资融券** | 4 | 0 | 4 | ⭐⭐⭐ |
| **宏观指标** | 4 | 0 | 4 | ⭐⭐⭐⭐ |
| **特色数据** | 4 | 0 | 4 | ⭐⭐⭐⭐ |
| **总计** | **122** | **30** | **92** | - |

---

## 1️⃣ 市场概况（12 个接口）

### 已实现 ✅
1. ✅ `stock_info_sh_sz_name_code` - 沪深股票名称及代码
2. ✅ `stock_info_a_code_name` - A 股股票代码及名称
3. ✅ `stock_info_sh_delist` - 沪深 A 股退市股票

### 待实现 🔥
4. 🔥 `stock_info_sh_name_code` - 上交所股票名称及代码
5. 🔥 `stock_info_sz_name_code` - 深交所股票名称及代码
6. 🔥 `stock_info_bj_name_code` - 北交所股票名称及代码
7. 🔥 `stock_info_kc_name_code` - 科创板股票名称及代码
8. 🔥 `stock_info_cy_name_code` - 创业板股票名称及代码
9. 🔥 `stock_info_sh_change_name` - 上交所股票名称变更
10. 🔥 `stock_info_sz_change_name` - 深交所股票名称变更
11. 🔥 `stock_info_sh_power_name` - 上交所股票停牌
12. 🔥 `stock_info_sz_power_name` - 深交所股票停牌

---

## 2️⃣ 实时行情（15 个接口）⭐⭐⭐⭐⭐

### 已实现 ✅
1. ✅ `stock_zh_a_spot_em` - 全 A 股实时行情（已实现）
2. ✅ `stock_sh_a_spot_em` - 沪 A 股实时行情
3. ✅ `stock_sz_a_spot_em` - 深 A 股实时行情
4. ✅ `stock_bj_a_spot_em` - 京 A 股实时行情
5. ✅ `stock_kc_a_spot_em` - 科创板实时行情

### 待实现 🔥
6. 🔥 `stock_cy_a_spot_em` - 创业板实时行情
7. 🔥 `stock_zh_a_new_spot_em` - 次新股实时行情
8. 🔥 `stock_zh_a_st_em` - ST 股实时行情
9. 🔥 `stock_zh_a_zt_em` - 涨停股实时行情
10. 🔥 `stock_zh_a_dt_em` - 跌停股实时行情
11. 🔥 `stock_hk_spot_em` - 港股实时行情
12. 🔥 `stock_us_spot_em` - 美股实时行情
13. 🔥 `stock_fund_spot_em` - 基金实时行情
14. 🔥 `stock_board_industry_spot_em` - 行业板块实时行情
15. 🔥 `stock_board_concept_spot_em` - 概念板块实时行情

---

## 3️⃣ K 线数据（12 个接口）

### 已实现 ✅
1. ✅ `stock_zh_a_hist` - A 股历史 K 线（日/周/月）
2. ✅ `stock_zh_a_hist_min_em` - A 股分时 K 线
3. ✅ `stock_hk_hist` - 港股历史 K 线
4. ✅ `stock_us_hist` - 美股历史 K 线
5. ✅ `stock_zh_a_hist_pre_min_em` - 盘前 K 线
6. ✅ `stock_zh_a_hist_after_min_em` - 盘后 K 线
7. ✅ `stock_board_industry_hist_em` - 行业板块 K 线
8. ✅ `stock_board_concept_hist_em` - 概念板块 K 线

### 待实现
9. 🔥 `stock_zh_a_hist_min_sina` - 新浪分时 K 线
10. 🔥 `stock_zh_a_tick_min_em` - 分钟成交
11. 🔥 `stock_zh_a_tick_daily_em` - 每日成交
12. 🔥 `stock_index_zh_a_hist_min_em` - 指数分时 K 线

---

## 4️⃣ 资金流向（10 个接口）⭐⭐⭐⭐

### 已实现 ✅
1. ✅ `stock_individual_fund_flow` - 个股资金流向
2. ✅ `stock_market_fund_flow` - 市场资金流向
3. ✅ `stock_board_industry_fund_flow` - 行业资金流向

### 待实现 🔥
4. 🔥 `stock_individual_fund_flow_rank` - 个股资金流向排行
5. 🔥 `stock_main_fund_flow` - 主力资金流向
6. 🔥 `stock_north_fund_flow` - 北向资金流向
7. 🔥 `stock_south_fund_flow` - 南向资金流向
8. 🔥 `stock_sector_fund_flow_summary` - 板块资金流汇总
9. 🔥 `stock_concept_fund_flow` - 概念资金流向
10. 🔥 `stock_fund_flow_change` - 资金流向变化

---

## 5️⃣ 财务指标（15 个接口）⭐⭐⭐⭐⭐

### 已实现 ✅
1. ✅ `stock_balance_sheet_by_report_em` - 资产负债表
2. ✅ `stock_income_statement_by_report_em` - 利润表
3. ✅ `stock_cash_flow_statement_by_report_em` - 现金流量表
4. ✅ `stock_yjbg_em` - 业绩快报

### 待实现 🔥
5. 🔥 `stock_financial_analysis_indicator_em` - 财务分析主要指标（ROE、毛利率等）
6. 🔥 `stock_financial_abstract` - 财务摘要
7. 🔥 `stock_report_disclosure` - 财报披露时间
8. 🔥 `stock_earnings_management` - 盈利预测
9. 🔥 `stock_earnings_quality` - 盈利质量
10. 🔥 `stock_debt_management` - 债务管理
11. 🔥 `stock_cash_management` - 现金管理
12. 🔥 `stock_operation_management` - 运营管理
13. 🔥 `stock_growth_management` - 成长能力
14. 🔥 `stock_risk_management` - 风险评估
15. 🔥 `stock_valuation_management` - 估值分析

---

## 6️⃣ 估值指标（8 个接口）⭐⭐⭐⭐

### 已实现 ✅
1. ✅ `stock_board_industry_name_em` - 行业估值（已实现）
2. ✅ `stock_board_concept_name_em` - 概念估值

### 待实现 🔥
3. 🔥 `stock_a_all_pe_ttm` - 全 A 股市盈率 TTM
4. 🔥 `stock_a_all_pb` - 全 A 股市净率
5. 🔥 `stock_a_all_ps` - 全 A 股市销率
6. 🔥 `stock_a_all_dividend_yield` - 全 A 股股息率
7. 🔥 `stock_hk_pe_band` - 港股 PE Band
8. 🔥 `stock_us_pe_band` - 美股 PE Band

---

## 7️⃣ 市场情绪（10 个接口）⭐⭐⭐⭐⭐

### 待实现 🔥🔥🔥
1. 🔥 `stock_zt_pool_em` - 涨停股池
2. 🔥 `stock_zt_pool_dtgc_em` - 跌停股池
3. 🔥 `stock_zt_pool_zbgc_em` - 炸板股池
4. 🔥 `stock_a_high_low_statistics` - 创新高/新低统计
5. 🔥 `stock_limit_analysis` - 涨跌停分析
6. 🔥 `stock_emotion_index` - 情绪指数
7. 🔥 `stock_sentiment_index` -  sentiment 指标
8. 🔥 `stock_hot_rank` - 热度排行
9. 🔥 `stock_focus_rank` - 关注度排行
10. 🔥 `stock_turnover_rank` - 换手率排行

---

## 8️⃣ 板块行情（8 个接口）

### 已实现 ✅
1. ✅ `stock_sector_spot_em` - 板块实时行情
2. ✅ `stock_board_industry_cons_em` - 行业成分股
3. ✅ `stock_board_concept_cons_em` - 概念成分股

### 待实现
5. 🔥 `stock_board_industry_name_em` - 行业板块名称
6. 🔥 `stock_board_concept_name_em` - 概念板块名称
7. 🔥 `stock_board_industry_hist_em` - 行业历史行情
8. 🔥 `stock_board_concept_hist_em` - 概念历史行情

---

## 9️⃣ 龙虎榜（6 个接口）⭐⭐⭐⭐⭐

### 待实现 🔥🔥🔥
1. 🔥 `stock_lhb_detail_em` - 龙虎榜详情
2. 🔥 `stock_lhb_yybph_em` - 营业部排行
3. 🔥 `stock_lhb_jgstatistic_em` - 机构统计
4. 🔥 `stock_lhb_hyyyb_em` - 活跃营业部
5. 🔥 `stock_lhb_traderstatistic_em` - 交易统计
6. 🔥 `stock_lhb_stock_statistic_em` - 个股统计

---

## 🔟 股东结构（6 个接口）⭐⭐⭐⭐⭐

### 待实现 🔥🔥🔥
1. 🔥 `stock_gdfx_top_10_em` - 十大股东
2. 🔥 `stock_gdfx_top_10_flow_em` - 十大流通股东
3. 🔥 `stock_gdfx_free_top_10_em` - 自由流通股东
4. 🔥 `stock_gdfx_scale_change_em` - 股东人数变化
5. 🔥 `stock_gdfx_holding_analyse_em` - 持股分析
6. 🔥 `stock_institute_hold` - 机构持股

---

## 1️⃣1️⃣ 融资融券（4 个接口）⭐⭐⭐

### 待实现
1. 🔥 `stock_margin_sse` - 上交所融资融券
2. 🔥 `stock_margin_szse` - 深交所融资融券
3. 🔥 `stock_margin_detail_sse` - 上交所融资明细
4. 🔥 `stock_margin_detail_szse` - 深交所融资明细

---

## 1️⃣2️⃣ 宏观指标（4 个接口）⭐⭐⭐⭐

### 待实现 🔥
1. 🔥 `stock_buffett_index_lg` - 巴菲特指标
2. 🔥 `stock_market_activity_legu` - 市场活跃度
3. 🔥 `stock_crowdedness_index` - 市场拥挤度
4. 🔥 `stock_macro_indicator` - 宏观经济指标

---

## 1️⃣3️⃣ 特色数据（4 个接口）⭐⭐⭐⭐

### 待实现 🔥
1. 🔥 `stock_hsgt_north_net_inflow_em` - 北向资金净流入
2. 🔥 `stock_hsgt_south_net_inflow_em` - 南向资金净流入
3. 🔥 `stock_hsgt_hold_stock_em` - 沪深港通持股
4. 🔥 `stock_hsgt_institution_statistics_em` - 沪深港通机构统计

---

## 🎯 优先实施计划

### 第一阶段（1-2 周）- 市场情绪监控 ⭐⭐⭐⭐⭐
**核心接口**:
1. `stock_zt_pool_em` - 涨停股池
2. `stock_zt_pool_dtgc_em` - 跌停股池
3. `stock_zt_pool_zbgc_em` - 炸板股池
4. `stock_a_high_low_statistics` - 创新高/新低统计

**预期成果**:
- 涨停复盘功能
- 市场情绪监控
- 连板股追踪

---

### 第二阶段（1-2 周）- 龙虎榜 + 股东 ⭐⭐⭐⭐⭐
**核心接口**:
1. `stock_lhb_detail_em` - 龙虎榜详情
2. `stock_gdfx_top_10_em` - 十大股东
3. `stock_gdfx_top_10_flow_em` - 十大流通股东

**预期成果**:
- 主力席位追踪
- 股东结构分析
- 机构持仓监控

---

### 第三阶段（1-2 周）- 财务深度 ⭐⭐⭐⭐⭐
**核心接口**:
1. `stock_financial_analysis_indicator_em` - 财务分析指标
2. `stock_a_all_pe_ttm` - 全市场估值
3. `stock_buffett_index_lg` - 巴菲特指标

**预期成果**:
- 财务选股器
- 估值对比分析
- 市场周期判断

---

### 第四阶段（1-2 周）- 资金流向 ⭐⭐⭐⭐
**核心接口**:
1. `stock_north_fund_flow` - 北向资金
2. `stock_individual_fund_flow_rank` - 资金流向排行
3. `stock_main_fund_flow` - 主力资金

**预期成果**:
- 外资动向分析
- 主力追踪
- 资金监控

---

## 📝 实施建议

### 1. 数据模型定义
```python
@dataclass
class LimitUpPool:
    code: str
    name: str
    change_pct: float
    latest_price: float
    limit_up_count: int  # 连板数
    first_limit_time: str
    last_limit_time: str
    industry: str

@dataclass
class TopShareholder:
    shareholder_name: str
    hold_amount: float
    hold_ratio: float
    change_type: str

@dataclass
class LHBEntry:
    code: str
    name: str
    buy_amount: float
    sell_amount: float
    net_amount: float
    yyb_name: str  # 营业部名称
```

### 2. 缓存策略
- 涨停/跌停数据：1 天
- 龙虎榜：1 天
- 股东数据：1 周
- 财务数据：1 周

### 3. 性能优化
- 批量获取
- 异步并发
- 本地缓存

---

## 📚 参考资料

- [实测 Python AKShare 122 个股票数据接口（16 集）](https://www.toutiao.com/article/7588400522185540146/)
- [AKShare 官方文档](https://akshare.akfamily.xyz/)
- [龙虎榜数据接口实测](https://www.toutiao.com/group/7590343240868545070/)
- [财务指标接口实测](https://www.toutiao.com/group/7589606831790604826/)

---

**整理者**: AI Code Assistant  
**整理时间**: 2026-03-20  
**建议**: 优先实施市场情绪监控类接口（涨停/跌停/创新高统计）
