# BaoStock 数据源 API 分类总览

**文档版本**: v1.0  
**更新日期**: 2026-03-19  
**数据源**: BaoStock 证券宝

---

## 📊 API 概览

BaoStock 适配器共提供 **34 个 API 方法**，分为 **10 大类别**：

| 类别 | 方法数 | 说明 | 状态 |
|------|-------|------|------|
| 📈 **K 线数据** | 4 | 股票/指数 K 线 | ✅ 已实现 |
| 📊 **估值指标** | 1 | 日频估值指标 | ✅ 已实现 |
| 💰 **分红除权** | 2 | 分红数据、复权因子 | ✅ 已实现 |
| 🏢 **股票信息** | 2 | 股票列表、基本信息 | ✅ 已实现 |
| 📐 **板块数据** | 2 | 行业板块、成分股 | ✅ 已实现 |
| 📉 **指数数据** | 1 | 指数 K 线 | ✅ 已实现 |
| 📊 **财务数据** | 8 | 季频盈利能力、营运能力、成长能力、偿债能力、现金流量、杜邦指数、业绩快报、业绩预告 | ✅ 已实现 |
| 🏦 **金融信息** | 5 | 存款利率、贷款利率、存款准备金率、货币供应量（月度）、货币供应量（年度） | ✅ 已实现 |
| 🔍 **其他数据** | 9 | 暂不支持的功能 | ⚠️ 预留接口 |

---

## 📈 一、K 线数据 API

### 1.1 股票 K 线

#### `get_kline()` - 日 K 线
```python
async def get_kline(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "qfq"  # qfq=前复权，hfq=后复权，""=不复权
) -> List[KLineData]:
    """
    获取日 K 线数据
    
    - 数据范围：1990-12-19 至今
    - 复权类型：前复权/后复权/不复权
    - 字段：date, code, open, high, low, close, volume, amount, turnover_rate
    """
```

**使用示例**:
```python
klines = await adapter.get_kline(
    code="600000",
    start_date="2023-01-01",
    end_date="2024-12-31",
    adjust="qfq"  # 前复权（推荐）
)
```

#### `get_weekly_kline()` - 周 K 线
```python
async def get_weekly_kline(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "qfq"
) -> List[KLineData]:
    """
    获取周 K 线数据
    
    - 每周最后一个交易日获取
    - 其他同日 K 线
    """
```

#### `get_monthly_kline()` - 月 K 线
```python
async def get_monthly_kline(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    adjust: str = "qfq"
) -> List[KLineData]:
    """
    获取月 K 线数据
    
    - 每月最后一个交易日获取
    - 其他同日 K 线
    """
```

### 1.2 指数 K 线

#### `get_index_kline()` - 指数 K 线
```python
async def get_index_kline(
    index_code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    frequency: str = "d"  # d=日，w=周，m=月
) -> List[KLineData]:
    """
    获取指数 K 线数据
    
    支持的指数类型:
    1. 综合指数 - sh.000001 上证指数，sz.399106 深证综指
    2. 规模指数 - sh.000016 上证 50，sh.000300 沪深 300
    3. 一级行业指数 - sh.000037 上证医药
    4. 二级行业指数 - sh.000952 300 地产
    5. 策略指数 - sh.000050 50 等权
    6. 成长指数 - sz.399376 小盘成长
    7. 价值指数 - sh.000029 180 价值
    8. 主题指数 - sh.000015 红利指数
    9. 基金指数 - sh.000011 上证基金指数
    10. 债券指数 - sh.000012 上证国债指数
    
    特点:
    - ❌ 指数没有分钟线数据
    - ✅ 数据范围：2006-01-01 至今
    - ✅ 不需要复权（adjustflag 固定为 3）
    """
```

**使用示例**:
```python
# 获取上证指数日线
index_klines = await adapter.get_index_kline(
    index_code="000001",  # 或 "sh.000001"
    start_date="2023-01-01",
    frequency="d"
)

# 获取沪深 300 周线
index_klines = await adapter.get_index_kline(
    index_code="000300",
    frequency="w"
)
```

---

## 📊 二、估值指标 API

### 2.1 日频估值指标

#### `get_valuation_indicators()` - 估值指标
```python
async def get_valuation_indicators(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取沪深 A 股估值指标（日频）
    
    支持的估值指标:
    - peTTM: 滚动市盈率 = (收盘价/每股盈余 TTM)
    - psTTM: 滚动市销率 = (收盘价/每股销售额 TTM)
    - pcfNcfTTM: 滚动市现率 = (收盘价/每股现金流 TTM)
    - pbMRQ: 市净率 = (收盘价/每股净资产)
    
    特点:
    - ✅ 仅支持日线，不支持周线、月线
    - ❌ 指数未提供估值数据
    - ✅ 数据范围：2006-01-01 至今
    """
```

**返回字段**:
```python
{
    "code": "600000",
    "date": "2024-12-31",
    "close": 10.50,
    "pe_ttm": 5.23,        # 滚动市盈率
    "pb_mrq": 0.65,        # 市净率
    "ps_ttm": 1.85,        # 滚动市销率
    "pcf_ncf_ttm": 4.32    # 滚动市现率
}
```

**使用示例**:
```python
valuation = await adapter.get_valuation_indicators(
    code="600000",
    start_date="2023-01-01",
    end_date="2024-12-31"
)
```

---

## 💰 三、分红除权 API

### 3.1 分红数据

#### `get_dividend_data()` - 除权除息信息
```python
async def get_dividend_data(
    code: str,
    start_year: int = 2006,
    end_year: Optional[int] = None,
    year_type: str = "report"  # "report"=预案公告年份，"operate"=除权除息年份
) -> List[Dict[str, Any]]:
    """
    获取除权除息信息（分红数据）
    
    返回字段（15 个）:
    - code: 证券代码
    - divid_pre_notice_date: 预披露公告日
    - divid_agm_pum_date: 股东大会公告日期
    - divid_plan_announce_date: 预案公告日
    - divid_plan_date: 分红实施公告日
    - divid_regist_date: 股权登记日
    - divid_operate_date: 除权除息日
    - divid_pay_date: 派息日
    - divid_stock_market_date: 红股上市交易日
    - divid_cash_ps_before_tax: 每股股利（税前）
    - divid_cash_ps_after_tax: 每股股利（税后）
    - divid_stocks_ps: 每股红股
    - divid_cash_stock: 分红送转（文本描述）
    - divid_reserve_to_stock_ps: 每股转增资本
    """
```

**使用示例**:
```python
# 获取 2015-2024 年分红数据
dividend_data = await adapter.get_dividend_data(
    code="600000",
    start_year=2015,
    end_year=2024,
    year_type="report"
)

# 计算累计分红
total_dividend = sum(
    d['divid_cash_ps_before_tax'] 
    for d in dividend_data 
    if d['divid_cash_ps_before_tax']
)
```

### 3.2 复权因子

#### `get_adjust_factor()` - 复权因子
```python
async def get_adjust_factor(
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取复权因子信息
    
    BaoStock 使用"涨跌幅复权法"计算复权因子
    
    返回字段（5 个）:
    - code: 证券代码
    - divid_operate_date: 除权除息日期
    - fore_adjust_factor: 向前复权因子
    - back_adjust_factor: 向后复权因子
    - adjust_factor: 本次复权因子
    
    复权因子说明:
    - foreAdjustFactor = 除权日前收盘价 / 除权日前收盘价
    - backAdjustFactor = 除权日前收盘价 / 除权日前收盘价
    - 基于复权因子与日 K 线数据可生成复权行情
    """
```

**使用示例**:
```python
# 获取复权因子
factors = await adapter.get_adjust_factor(
    code="600000",
    start_date="2015-01-01",
    end_date="2024-12-31"
)

# 计算累积复权因子
cumulative_factor = 1.0
for factor in factors:
    cumulative_factor *= factor['fore_adjust_factor']
```

---

## 🏢 四、股票信息 API

### 4.1 股票列表

#### `get_stock_list()` - 股票列表
```python
async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
    """
    获取 A 股股票列表
    
    Args:
        market: 市场代码（可选）
    
    Returns:
        List[StockBasicInfo]: 股票列表
    
    返回字段:
    - code: 股票代码（6 位数字）
    - name: 证券名称
    - market: 市场（SH/SZ）
    - industry: 所属行业
    - list_date: 上市日期
    """
```

### 4.2 股票信息

#### `get_stock_info()` - 股票基本信息
```python
async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
    """
    获取股票基本信息
    
    Args:
        code: 股票代码
    
    Returns:
        Optional[StockBasicInfo]: 股票信息，获取失败返回 None
    """
```

---

## 📐 五、板块数据 API

### 5.1 板块列表

#### `get_sector_list()` - 行业板块列表
```python
async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
    """
    获取行业板块列表
    
    Args:
        sector_type: 板块类型
    
    Returns:
        List[SectorInfo]: 板块列表
    """
```

### 5.2 板块成分股

#### `get_sector_components()` - 板块成分股
```python
async def get_sector_components(self, sector_code: str) -> List[str]:
    """
    获取板块成分股
    
    Args:
        sector_code: 板块代码
    
    Returns:
        List[str]: 成分股代码列表
    """
```

**使用示例**:
```python
# 获取行业板块列表
sectors = await adapter.get_sector_list()

# 获取银行业成分股
bank_stocks = await adapter.get_sector_components("银行业")
```

---

## 📊 六、财务数据 API

### 6.1 季频盈利能力

#### `get_profit_data()` - 季频盈利能力

```python
async def get_profit_data(
    self,
    code: str,
    year: Optional[int] = None,
    quarter: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    获取季频盈利能力数据
    
    通过 API 接口获取季频盈利能力信息，可以通过参数设置获取对应年份、季度数据
    
    返回字段 (10 个):
    - code: 证券代码
    - pub_date: 公司发布财报的日期
    - stat_date: 财报统计的季度的最后一天
    - roe_avg: 净资产收益率 (平均)(%)
    - np_margin: 销售净利率 (%)
    - gp_margin: 销售毛利率 (%)
    - net_profit: 净利润 (元)
    - eps_ttm: 每股收益
    - mb_revenue: 主营营业收入 (元)
    - total_share: 总股本
    - liqa_share: 流通股本
    
    数据范围:
    - ✅ 从 2007 年至今
    - ✅ 季度更新
    """
```

**返回示例**:
```python
{
    "code": "sh.600000",
    "pub_date": "2023-08-30",
    "stat_date": "2023-06-30",
    "roe_avg": 8.52,        # 净资产收益率
    "np_margin": 25.3,      # 销售净利率
    "gp_margin": 35.8,      # 销售毛利率
    "net_profit": 5200000000.0,  # 净利润
    "eps_ttm": 1.52,        # 每股收益
    "mb_revenue": 20500000000.0,  # 主营营业收入
    "total_share": 34200000000.0,  # 总股本
    "liqa_share": 29800000000.0   # 流通股本
}
```

**使用示例**:
```python
# 获取最新季度盈利能力
profit = await adapter.get_profit_data(code="sh.600000")

# 获取指定年份季度
profit = await adapter.get_profit_data(
    code="sh.600000",
    year=2023,
    quarter=2
)

# 获取多年数据（趋势分析）
all_profits = []
for year in range(2020, 2024):
    result = await adapter.get_profit_data(
        code="sh.600000",
        year=year,
        quarter=2
    )
    all_profits.extend(result)
```

### 6.2 季频营运能力

#### `get_operation_data()` - 季频营运能力

```python
async def get_operation_data(
    self,
    code: str,
    year: Optional[int] = None,
    quarter: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    获取季频营运能力数据
    
    通过 API 接口获取季频营运能力信息，可以通过参数设置获取对应年份、季度数据
    
    返回字段 (8 个):
    - code: 证券代码
    - pub_date: 公司发布财报的日期
    - stat_date: 财报统计的季度的最后一天
    - nr_turn_ratio: 应收账款周转率 (次)
    - nr_turn_days: 应收账款周转天数 (天)
    - inv_turn_ratio: 存货周转率 (次)
    - inv_turn_days: 存货周转天数 (天)
    - ca_turn_ratio: 流动资产周转率 (次)
    - asset_turn_ratio: 总资产周转率 (次)
    
    数据范围:
    - ✅ 从 2007 年至今
    - ✅ 季度更新
    """
```

**返回示例**:
```python
{
    "code": "sh.600000",
    "pub_date": "2023-08-30",
    "stat_date": "2023-06-30",
    "nr_turn_ratio": 2.5,       # 应收账款周转率
    "nr_turn_days": 72.0,       # 应收账款周转天数
    "inv_turn_ratio": null,     # 存货周转率（银行业不适用）
    "inv_turn_days": null,      # 存货周转天数
    "ca_turn_ratio": 0.15,      # 流动资产周转率
    "asset_turn_ratio": 0.05    # 总资产周转率
}
```

**使用示例**:
```python
# 获取最新季度营运能力
operation = await adapter.get_operation_data(code="sh.600000")

# 获取指定年份季度
operation = await adapter.get_operation_data(
    code="sh.600000",
    year=2023,
    quarter=2
)

# 趋势分析
all_operations = []
for year in range(2020, 2024):
    for quarter in [1, 2, 3, 4]:
        result = await adapter.get_operation_data(
            code="sh.600000",
            year=year,
            quarter=quarter
        )
        all_operations.extend(result)
```

**营运能力指标说明**:

| 指标 | 说明 | 计算公式 |
|-----|------|---------|
| **应收账款周转率** | 反映收账速度 | 营业收入 / 平均应收账款 |
| **应收账款周转天数** | 回收款项平均天数 | 季报天数 / 周转率 |
| **存货周转率** | 反映存货管理效率 | 营业成本 / 平均存货 |
| **存货周转天数** | 售出存货平均天数 | 季报天数 / 周转率 |
| **流动资产周转率** | 流动资产利用效率 | 营业总收入 / 平均流动资产 |
| **总资产周转率** | 全部资产利用效率 | 营业总收入 / 平均总资产 |

### 6.3 季频成长能力

#### `get_growth_data()` - 季频成长能力

```python
async def get_growth_data(
    self,
    code: str,
    year: Optional[int] = None,
    quarter: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    获取季频成长能力数据
    
    通过 API 接口获取季频成长能力信息，可以通过参数设置获取对应年份、季度数据
    
    返回字段 (7 个):
    - code: 证券代码
    - pub_date: 公司发布财报的日期
    - stat_date: 财报统计的季度的最后一天
    - yoy_equity: 净资产同比增长率 (%)
    - yoy_asset: 总资产同比增长率 (%)
    - yoy_ni: 净利润同比增长率 (%)
    - yoy_eps_basic: 基本每股收益同比增长率 (%)
    - yoy_pni: 归属母公司股东净利润同比增长率 (%)
    
    数据范围:
    - ✅ 从 2007 年至今
    - ✅ 季度更新
    """
```

**返回示例**:
```python
{
    "code": "sh.600000",
    "pub_date": "2023-08-30",
    "stat_date": "2023-06-30",
    "yoy_equity": 8.52,      # 净资产同比增长率
    "yoy_asset": 6.35,       # 总资产同比增长率
    "yoy_ni": 12.45,         # 净利润同比增长率
    "yoy_eps_basic": 12.30,  # 基本每股收益同比增长率
    "yoy_pni": 11.85         # 归属母公司股东净利润同比增长率
}
```

**使用示例**:
```python
# 获取最新季度成长能力
growth = await adapter.get_growth_data(code="sh.600000")

# 获取指定年份季度
growth = await adapter.get_growth_data(
    code="sh.600000",
    year=2023,
    quarter=2
)

# 趋势分析
all_growths = []
for year in range(2020, 2024):
    for quarter in [1, 2, 3, 4]:
        result = await adapter.get_growth_data(
            code="sh.600000",
            year=year,
            quarter=quarter
        )
        all_growths.extend(result)
```

**成长能力指标说明**:

| 指标 | 说明 | 计算公式 |
|-----|------|---------|
| **净资产同比增长率** | 反映净资产增长速度 | (本期净资产 - 上年同期净资产) / 上年同期净资产 |
| **总资产同比增长率** | 反映总资产扩张速度 | (本期总资产 - 上年同期总资产) / 上年同期总资产 |
| **净利润同比增长率** | 反映净利润成长性 | (本期净利润 - 上年同期净利润) / 上年同期净利润 |
| **每股收益同比增长率** | 反映每股收益成长性 | (本期每股收益 - 上年同期每股收益) / 上年同期每股收益 |
| **归母净利润同比增长率** | 反映归母股东净利润成长性 | (本期归母净利润 - 上年同期归母净利润) / 上年同期归母净利润 |

### 6.4 季频偿债能力

#### `get_balance_data()` - 季频偿债能力

```python
async def get_balance_data(
    self,
    code: str,
    year: Optional[int] = None,
    quarter: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    获取季频偿债能力数据
    
    通过 API 接口获取季频偿债能力信息，可以通过参数设置获取对应年份、季度数据
    
    返回字段 (8 个):
    - code: 证券代码
    - pub_date: 公司发布财报的日期
    - stat_date: 财报统计的季度的最后一天
    - current_ratio: 流动比率
    - quick_ratio: 速动比率
    - cash_ratio: 现金比率
    - yoy_liability: 总负债同比增长率 (%)
    - liability_to_asset: 资产负债率
    - asset_to_equity: 权益乘数
    
    数据范围:
    - ✅ 从 2007 年至今
    - ✅ 季度更新
    """
```

**返回示例**:
```python
{
    "code": "sh.600000",
    "pub_date": "2023-08-30",
    "stat_date": "2023-06-30",
    "current_ratio": 1.25,        # 流动比率
    "quick_ratio": 0.95,          # 速动比率
    "cash_ratio": 0.35,           # 现金比率
    "yoy_liability": 8.5,         # 总负债同比增长率
    "liability_to_asset": 0.85,   # 资产负债率
    "asset_to_equity": 6.67       # 权益乘数
}
```

**使用示例**:
```python
# 获取最新季度偿债能力
balance = await adapter.get_balance_data(code="sh.600000")

# 获取指定年份季度
balance = await adapter.get_balance_data(
    code="sh.600000",
    year=2023,
    quarter=2
)
```

**偿债能力指标说明**:

| 指标 | 说明 | 计算公式 | 合理范围 |
|-----|------|---------|---------|
| **流动比率** | 反映短期偿债能力 | 流动资产/流动负债 | 1.5-2.5 |
| **速动比率** | 反映快速偿债能力 | (流动资产 - 存货)/流动负债 | 0.8-1.2 |
| **现金比率** | 反映即时偿债能力 | (货币资金 + 交易性金融资产)/流动负债 | 0.2-0.5 |
| **资产负债率** | 反映长期偿债能力 | 负债总额/资产总额 | 40%-60% |
| **权益乘数** | 反映财务杠杆程度 | 资产总额/股东权益总额 | 1.5-3.0 |

### 6.5 季频现金流量

#### `get_cash_flow_data()` - 季频现金流量

```python
async def get_cash_flow_data(
    self,
    code: str,
    year: Optional[int] = None,
    quarter: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    获取季频现金流量数据
    
    通过 API 接口获取季频现金流量信息，可以通过参数设置获取对应年份、季度数据
    
    返回字段 (9 个):
    - code: 证券代码
    - pub_date: 公司发布财报的日期
    - stat_date: 财报统计的季度的最后一天
    - ca_to_asset: 流动资产/总资产
    - nca_to_asset: 非流动资产/总资产
    - tangible_asset_to_asset: 有形资产/总资产
    - ebit_to_interest: 已获利息倍数
    - cfo_to_or: 经营活动现金净流量/营业收入
    - cfo_to_np: 经营活动现金净流量/净利润
    - cfo_to_gr: 经营活动现金净流量/营业总收入
    
    数据范围:
    - ✅ 从 2007 年至今
    - ✅ 季度更新
    """
```

**返回示例**:
```python
{
    "code": "sh.600000",
    "pub_date": "2023-08-30",
    "stat_date": "2023-06-30",
    "ca_to_asset": 0.65,           # 流动资产/总资产
    "nca_to_asset": 0.35,          # 非流动资产/总资产
    "tangible_asset_to_asset": 0.95, # 有形资产/总资产
    "ebit_to_interest": 5.2,       # 已获利息倍数
    "cfo_to_or": 0.12,             # 经营现金净流量/营业收入
    "cfo_to_np": 1.25,             # 经营现金净流量/净利润
    "cfo_to_gr": 0.10              # 经营现金净流量/营业总收入
}
```

**使用示例**:
```python
# 获取最新季度现金流量
cash_flow = await adapter.get_cash_flow_data(code="sh.600000")

# 获取指定年份季度
cash_flow = await adapter.get_cash_flow_data(
    code="sh.600000",
    year=2023,
    quarter=2
)
```

**现金流量指标说明**:

| 指标 | 说明 | 计算公式 |
|-----|------|---------|
| **ca_to_asset** | 流动资产占比 | 流动资产/总资产 |
| **nca_to_asset** | 非流动资产占比 | 非流动资产/总资产 |
| **tangible_asset_to_asset** | 有形资产占比 | 有形资产/总资产 |
| **ebit_to_interest** | 已获利息倍数 | 息税前利润/利息费用 |
| **cfo_to_or** | 现金收入比 | 经营现金净流量/营业收入 |
| **cfo_to_np** | 现金盈利比 | 经营现金净流量/净利润 |
| **cfo_to_gr** | 现金总收入比 | 经营现金净流量/营业总收入 |

### 6.6 季频杜邦指数

#### `get_dupont_data()` - 季频杜邦指数

```python
async def get_dupont_data(
    self,
    code: str,
    year: Optional[int] = None,
    quarter: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    获取季频杜邦指数数据
    
    通过 API 接口获取季频杜邦指数信息，可以通过参数设置获取对应年份、季度数据
    
    返回字段 (10 个):
    - code: 证券代码
    - pub_date: 公司发布财报的日期
    - stat_date: 财报统计的季度的最后一天
    - dupont_roe: 净资产收益率
    - dupont_asset_to_equity: 权益乘数
    - dupont_asset_turn: 总资产周转率
    - dupont_pni_to_ni: 归属母公司净利润/净利润
    - dupont_ni_to_gr: 净利润/营业总收入
    - dupont_tax_burden: 税负水平
    - dupont_int_burden: 利息负担
    - dupont_ebit_to_gr: 息税前利润/营业总收入
    
    数据范围:
    - ✅ 从 2007 年至今
    - ✅ 季度更新
    """
```

**返回示例**:
```python
{
    "code": "sh.600000",
    "pub_date": "2023-08-30",
    "stat_date": "2023-06-30",
    "dupont_roe": 0.075,            # 净资产收益率
    "dupont_asset_to_equity": 15.59, # 权益乘数
    "dupont_asset_turn": 0.014,     # 总资产周转率
    "dupont_pni_to_ni": 0.987,      # 归属母公司净利润/净利润
    "dupont_ni_to_gr": 0.342,       # 净利润/营业总收入
    "dupont_tax_burden": 0.776,     # 税负水平
    "dupont_int_burden": 0.95,      # 利息负担
    "dupont_ebit_to_gr": 0.45       # 息税前利润/营业总收入
}
```

**使用示例**:
```python
# 获取最新季度杜邦指数
dupont = await adapter.get_dupont_data(code="sh.600000")

# 获取指定年份季度
dupont = await adapter.get_dupont_data(
    code="sh.600000",
    year=2023,
    quarter=2
)
```

**杜邦指数指标说明**:

| 指标 | 说明 | 计算公式 |
|-----|------|---------|
| **dupont_roe** | 净资产收益率 | 归属母公司股东净利润/平均归母股东权益 |
| **dupont_asset_to_equity** | 权益乘数 | 平均总资产/平均归母股东权益 |
| **dupont_asset_turn** | 总资产周转率 | 营业总收入/平均总资产 |
| **dupont_pni_to_ni** | 归母净利率 | 归属母公司净利润/净利润 |
| **dupont_ni_to_gr** | 销售净利率 | 净利润/营业总收入 |
| **dupont_tax_burden** | 税负水平 | 净利润/利润总额 |
| **dupont_int_burden** | 利息负担 | 利润总额/息税前利润 |
| **dupont_ebit_to_gr** | 经营利润率 | 息税前利润/营业总收入 |

**杜邦分析体系**:

```
ROE = 净利润率 × 总资产周转率 × 权益乘数
    = dupont_ni_to_gr × dupont_asset_turn × dupont_asset_to_equity
```

### 6.7 季频业绩快报

#### `get_performance_express_report()` - 季频公司业绩快报

```python
async def get_performance_express_report(
    self,
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取季频公司业绩快报数据
    
    通过 API 接口获取季频公司业绩快报信息，可以通过参数设置获取起止年份数据
    
    返回字段 (11 个):
    - code: 证券代码
    - performance_exp_pub_date: 业绩快报披露日
    - performance_exp_stat_date: 业绩快报统计日期
    - performance_exp_update_date: 业绩快报披露日 (最新)
    - performance_express_total_asset: 业绩快报总资产
    - performance_express_net_asset: 业绩快报净资产
    - performance_express_eps_chg_pct: 业绩每股收益增长率
    - performance_express_roe_wa: 业绩快报净资产收益率 ROE-加权
    - performance_express_eps_diluted: 业绩快报每股收益 EPS-摊薄
    - performance_express_gr_yoy: 业绩快报营业总收入同比
    - performance_express_op_yoy: 业绩快报营业利润同比
    
    数据范围:
    - ✅ 从 2006 年至今
    - ⚠️ 除特殊情况外，交易所未要求必须发布
    """
```

**返回示例**:
```python
{
    "code": "sh.600000",
    "performance_exp_pub_date": "2017-01-04",
    "performance_exp_stat_date": "2016-12-31",
    "performance_exp_update_date": "2017-01-04",
    "performance_express_total_asset": 5857263000000.0,  # 总资产
    "performance_express_net_asset": 338027000000.0,      # 净资产
    "performance_express_eps_chg_pct": 0.115412,          # 每股收益增长率
    "performance_express_roe_wa": 16.35,                  # ROE-加权
    "performance_express_eps_diluted": 2.40,              # EPS-摊薄
    "performance_express_gr_yoy": 0.097234,               # 营业总收入同比
    "performance_express_op_yoy": 0.054384                # 营业利润同比
}
```

**使用示例**:
```python
# 获取业绩快报
report = await adapter.get_performance_express_report(
    code="sh.600000",
    start_date="2015-01-01",
    end_date="2017-12-31"
)

# 获取最新年度业绩快报
report = await adapter.get_performance_express_report(
    code="sh.600000",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

**业绩快报指标说明**:

| 指标 | 说明 | 作用 |
|-----|------|------|
| **业绩快报披露日** | 业绩快报正式披露日期 | 了解信息披露时间 |
| **业绩快报统计日期** | 业绩快报对应的统计期末 | 确定数据所属期间 |
| **总资产** | 企业资产总额 | 反映企业规模 |
| **净资产** | 股东权益总额 | 反映股东权益规模 |
| **每股收益增长率** | EPS 同比增长率 | 反映股东收益成长性 |
| **ROE-加权** | 加权净资产收益率 | 反映股东权益收益水平 |
| **EPS-摊薄** | 摊薄每股收益 | 反映每股盈利水平 |
| **营业总收入同比** | 营收增长率 | 反映业务规模成长性 |
| **营业利润同比** | 营业利润增长率 | 反映核心利润成长性 |

**业绩快报特点**:

- ✅ **提前披露**：在正式财报前披露，让投资者提前了解业绩
- ⚠️ **非强制**：除特殊情况外，交易所未要求必须发布
- 📊 **数据范围**：2006 年至今
- 🔍 **重要参考**：是预测正式财报的重要参考

### 6.8 季频业绩预告

#### `get_forecast_report()` - 季频公司业绩预告

```python
async def get_forecast_report(
    self,
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取季频公司业绩预告数据
    
    通过 API 接口获取季频公司业绩预告信息，可以通过参数设置获取起止年份数据
    
    返回字段 (7 个):
    - code: 证券代码
    - profit_forcast_exp_pub_date: 业绩预告发布日期
    - profit_forcast_exp_stat_date: 业绩预告统计日期
    - profit_forcast_type: 业绩预告类型
    - profit_forcast_abstract: 业绩预告摘要
    - profit_forcast_chg_pct_up: 预告归母净利润增长上限 (%)
    - profit_forcast_chg_pct_dwn: 预告归母净利润增长下限 (%)
    
    数据范围:
    - ✅ 从 2003 年至今
    - ⚠️ 除特殊情况外，交易所未要求必须发布
    """
```

**返回示例**:
```python
{
    "code": "sh.600000",
    "profit_forcast_exp_pub_date": "2011-01-05",
    "profit_forcast_exp_stat_date": "2010-12-31",
    "profit_forcast_type": "略增",
    "profit_forcast_abstract": "预计公司 2010 年年度归属于上市公司股东净利润为 190.76 亿元，较上年同期增长 44.33％。",
    "profit_forcast_chg_pct_up": 44.33,  # 增长上限
    "profit_forcast_chg_pct_dwn": 44.33  # 增长下限
}
```

**使用示例**:
```python
# 获取业绩预告
forecast = await adapter.get_forecast_report(
    code="sh.600000",
    start_date="2010-01-01",
    end_date="2017-12-31"
)

# 获取最新年度业绩预告
forecast = await adapter.get_forecast_report(
    code="sh.600000",
    start_date="2023-01-01",
    end_date="2023-12-31"
)
```

**业绩预告指标说明**:

| 指标 | 说明 | 作用 |
|-----|------|------|
| **业绩预告发布日期** | 业绩预告正式披露日期 | 了解信息披露时间 |
| **业绩预告统计日期** | 业绩预告对应的统计期末 | 确定数据所属期间 |
| **业绩预告类型** | 预告业绩变化类型 | 略增、略减、预增、预减、扭亏、续亏等 |
| **业绩预告摘要** | 业绩预告文字描述 | 了解详细业绩信息 |
| **净利润增长上限** | 预告归母净利润增长上限 (%) | 预期业绩增长上限 |
| **净利润增长下限** | 预告归母净利润增长下限 (%) | 预期业绩增长下限 |

**业绩预告类型**:

| 类型 | 说明 | 通常标准 |
|-----|------|---------|
| **预增** | 预计净利润大幅增长 | 同比增长≥50% |
| **略增** | 预计净利润小幅增长 | 0%<同比增长<50% |
| **预减** | 预计净利润大幅减少 | 同比下跌≥50% |
| **略减** | 预计净利润小幅减少 | -50%<同比增长<0% |
| **扭亏** | 预计由亏损转为盈利 | 上年同期亏损 |
| **续亏** | 预计继续亏损 | 连续两年亏损 |
| **首亏** | 预计首次亏损 | 上年同期盈利 |
| **续盈** | 预计继续盈利 | 持续盈利 |

**业绩预告特点**:

- ✅ **提前预警**：在正式财报前披露业绩预期
- ⚠️ **非强制**：除特殊情况外，交易所未要求必须发布
- 📊 **数据范围**：2003 年至今（比业绩快报更早）
- 🔍 **区间预测**：提供业绩增长区间范围
- 📝 **文字摘要**：包含详细的业绩说明文字

**业绩预告 vs 业绩快报**:

| 对比项 | 业绩预告 | 业绩快报 |
|-------|---------|---------|
| **披露时间** | 更早（通常提前 1-2 月） | 较晚（通常提前 1-2 周） |
| **数据精度** | 区间预测 | 具体数值 |
| **数据范围** | 2003 年至今 | 2006 年至今 |
| **强制性** | 非强制 | 非强制 |
| **主要内容** | 净利润增长区间 | 总资产、净资产、ROE 等 |

---

## 🏦 八、金融信息 API

### 8.1 存款利率

#### `get_deposit_rate_data()` - 存款利率

```python
async def get_deposit_rate_data(
    self,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取存款利率数据
    
    通过 API 接口获取存款利率，可以通过参数设置获取对应起止日期的数据
    
    返回字段 (11 个):
    - pub_date: 发布日期
    - demand_deposit_rate: 活期存款 (不定期)
    - fixed_deposit_rate_3_month: 定期存款 (三个月)
    - fixed_deposit_rate_6_month: 定期存款 (半年)
    - fixed_deposit_rate_1_year: 定期存款整存整取 (一年)
    - fixed_deposit_rate_2_year: 定期存款整存整取 (二年)
    - fixed_deposit_rate_3_year: 定期存款整存整取 (三年)
    - fixed_deposit_rate_5_year: 定期存款整存整取 (五年)
    - installment_fixed_deposit_rate_1_year: 零存整取等定期存款 (一年)
    - installment_fixed_deposit_rate_3_year: 零存整取等定期存款 (三年)
    - installment_fixed_deposit_rate_5_year: 零存整取等定期存款 (五年)
    """
```

**返回示例**:
```python
{
    "pub_date": "2015-03-01",
    "demand_deposit_rate": 0.35,           # 活期存款利率
    "fixed_deposit_rate_3_month": 2.10,    # 三个月定期
    "fixed_deposit_rate_6_month": 2.30,    # 半年定期
    "fixed_deposit_rate_1_year": 2.50,     # 一年定期
    "fixed_deposit_rate_2_year": 3.10,     # 二年定期
    "fixed_deposit_rate_3_year": 3.75,     # 三年定期
    "fixed_deposit_rate_5_year": 2.10,     # 五年定期
    "installment_fixed_deposit_rate_1_year": 2.30,  # 零存整取一年
    "installment_fixed_deposit_rate_3_year": None,
    "installment_fixed_deposit_rate_5_year": None
}
```

**使用示例**:
```python
# 获取 2015 年存款利率
rates = await adapter.get_deposit_rate_data(
    start_date="2015-01-01",
    end_date="2015-12-31"
)

# 获取最新存款利率
rates = await adapter.get_deposit_rate_data()
```

### 8.2 贷款利率

#### `get_loan_rate_data()` - 贷款利率

```python
async def get_loan_rate_data(
    self,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取贷款利率数据
    
    通过 API 接口获取贷款利率，可以通过参数设置获取对应起止日期的数据
    
    返回字段 (8 个):
    - pub_date: 发布日期
    - loan_rate_6_month: 6 个月贷款利率
    - loan_rate_6_month_to_1_year: 6 个月至 1 年贷款利率
    - loan_rate_1_year_to_3_year: 1 年至 3 年贷款利率
    - loan_rate_3_year_to_5_year: 3 年至 5 年贷款利率
    - loan_rate_above_5_year: 5 年以上贷款利率
    - mortgate_rate_below_5_year: 5 年以下住房公积金贷款利率
    - mortgate_rate_above_5_year: 5 年以上住房公积金贷款利率
    """
```

**返回示例**:
```python
{
    "pub_date": "2010-10-20",
    "loan_rate_6_month": 5.10,              # 6 个月贷款利率
    "loan_rate_6_month_to_1_year": 5.56,    # 6 个月至 1 年
    "loan_rate_1_year_to_3_year": 5.60,     # 1 年至 3 年
    "loan_rate_3_year_to_5_year": 5.96,     # 3 年至 5 年
    "loan_rate_above_5_year": 6.14,         # 5 年以上
    "mortgate_rate_below_5_year": 3.50,     # 公积金 5 年以下
    "mortgate_rate_above_5_year": 4.05      # 公积金 5 年以上
}
```

**使用示例**:
```python
# 获取 2010-2015 年贷款利率
rates = await adapter.get_loan_rate_data(
    start_date="2010-01-01",
    end_date="2015-12-31"
)

# 获取最新贷款利率
rates = await adapter.get_loan_rate_data()
```

### 8.3 存款准备金率

#### `get_required_reserve_ratio_data()` - 存款准备金率

```python
async def get_required_reserve_ratio_data(
    self,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    year_type: int = 0
) -> List[Dict[str, Any]]:
    """
    获取存款准备金率数据
    
    通过 API 接口获取存款准备金率，可以通过参数设置获取对应起止日期的数据
    
    返回字段 (6 个):
    - pub_date: 公告日期
    - effective_date: 生效日期
    - big_institutions_ratio_pre: 大型金融机构调整前
    - big_institutions_ratio_after: 大型金融机构调整后
    - medium_institutions_ratio_pre: 中小型金融机构调整前
    - medium_institutions_ratio_after: 中小型金融机构调整后
    
    参数:
    - year_type: 年份类型（0=公告日期，1=生效日期）
    """
```

**返回示例**:
```python
{
    "pub_date": "2010-01-12",
    "effective_date": "2010-01-18",
    "big_institutions_ratio_pre": 15.5,     # 大型机构调整前
    "big_institutions_ratio_after": 16.0,   # 大型机构调整后
    "medium_institutions_ratio_pre": 13.5,  # 中小型机构调整前
    "medium_institutions_ratio_after": 14.0 # 中小型机构调整后
}
```

**使用示例**:
```python
# 获取 2010-2015 年存款准备金率
ratios = await adapter.get_required_reserve_ratio_data(
    start_date="2010-01-01",
    end_date="2015-12-31"
)

# 按生效日期查询
ratios = await adapter.get_required_reserve_ratio_data(
    start_date="2010-01-01",
    end_date="2015-12-31",
    year_type=1  # 按生效日期查询
)
```

**金融指标说明**:

| 指标类型 | 指标 | 说明 |
|---------|------|------|
| **存款利率** | 活期存款利率 | 不定期存款利率 |
| | 定期存款利率 | 3 个月、半年、1 年、2 年、3 年、5 年 |
| | 零存整取利率 | 1 年、3 年、5 年 |
| **贷款利率** | 短期贷款利率 | 6 个月、6 个月 -1 年 |
| | 中长期贷款利率 | 1-3 年、3-5 年、5 年以上 |
| | 公积金贷款利率 | 5 年以下、5 年以上 |
| **存款准备金率** | 大型机构 | 调整前、调整后 |
| | 中小型机构 | 调整前、调整后 |

### 8.4 月度货币供应量

#### `get_money_supply_data_month()` - 月度货币供应量

```python
async def get_money_supply_data_month(
    self,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取月度货币供应量数据
    
    通过 API 接口获取货币供应量，可以通过参数设置获取对应起止日期的数据
    
    返回字段 (11 个):
    - stat_year: 统计年度
    - stat_month: 统计月份
    - m0_month: 货币供应量 M0（月）
    - m0_yoy: 货币供应量 M0（同比）
    - m0_chain_relative: 货币供应量 M0（环比）
    - m1_month: 货币供应量 M1（月）
    - m1_yoy: 货币供应量 M1（同比）
    - m1_chain_relative: 货币供应量 M1（环比）
    - m2_month: 货币供应量 M2（月）
    - m2_yoy: 货币供应量 M2（同比）
    - m2_chain_relative: 货币供应量 M2（环比）
    """
```

**返回示例**:
```python
{
    "stat_year": 2010,
    "stat_month": 1,
    "m0_month": 40758.58,        # M0 供应量（亿元）
    "m0_yoy": -0.79,            # M0 同比增速（%）
    "m0_chain_relative": 6.57,  # M0 环比增速（%）
    "m1_month": 229588.98,      # M1 供应量（亿元）
    "m1_yoy": 38.96,            # M1 同比增速（%）
    "m1_chain_relative": 3.68,  # M1 环比增速（%）
    "m2_month": 625609.29,      # M2 供应量（亿元）
    "m2_yoy": 25.98,            # M2 同比增速（%）
    "m2_chain_relative": 2.52   # M2 环比增速（%）
}
```

**使用示例**:
```python
# 获取 2010-2015 年月度货币供应量
data = await adapter.get_money_supply_data_month(
    start_date="2010-01",
    end_date="2015-12"
)

# 获取最新月度货币供应量
data = await adapter.get_money_supply_data_month()
```

### 8.5 年度货币供应量

#### `get_money_supply_data_year()` - 年度货币供应量（年底余额）

```python
async def get_money_supply_data_year(
    self,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    获取年度货币供应量数据（年底余额）
    
    通过 API 接口获取货币供应量（年底余额），可以通过参数设置获取对应起止日期的数据
    
    返回字段 (7 个):
    - stat_year: 统计年度
    - m0_year: 年货币供应量 M0（亿元）
    - m0_year_yoy: 年货币供应量 M0（同比）
    - m1_year: 年货币供应量 M1（亿元）
    - m1_year_yoy: 年货币供应量 M1（同比）
    - m2_year: 年货币供应量 M2（亿元）
    - m2_year_yoy: 年货币供应量 M2（同比）
    """
```

**返回示例**:
```python
{
    "stat_year": 2010,
    "m0_year": 44628.17,        # M0 年底余额（亿元）
    "m0_year_yoy": 16.70,       # M0 同比增速（%）
    "m1_year": 266621.54,       # M1 年底余额（亿元）
    "m1_year_yoy": 21.20,       # M1 同比增速（%）
    "m2_year": 725851.80,       # M2 年底余额（亿元）
    "m2_year_yoy": 19.70        # M2 同比增速（%）
}
```

**使用示例**:
```python
# 获取 2010-2015 年年度货币供应量
data = await adapter.get_money_supply_data_year(
    start_date="2010",
    end_date="2015"
)

# 获取最新年度货币供应量
data = await adapter.get_money_supply_data_year()
```

**货币供应量指标说明**:

| 指标类型 | 指标 | 说明 | 计算公式 |
|---------|------|------|---------|
| **M0** | 流通中现金 | 银行体系以外流通的现金 | - |
| **M1** | 狭义货币 | M0 + 单位活期存款 | M0 + 企业活期存款 |
| **M2** | 广义货币 | M1 + 准货币 | M1 + 定期存款 + 储蓄存款 |
| **同比** | 同比增长率 | 与上年同期相比的增速 | (本期 - 上年同期) / 上年同期 × 100% |
| **环比** | 环比增长率 | 与上月相比的增速 | (本期 - 上期) / 上期 × 100% |

**货币层次说明**:

```
中国货币供应量层次:

M0 = 流通中的现金
   └─ 最具流动性
   └─ 反映居民和企业手持现金

M1 = M0 + 单位活期存款
   └─ 狭义货币供应量
   └─ 反映企业资金松紧
   └─ 经济景气度指标

M2 = M1 + 准货币
   = M1 + 单位定期存款 + 居民储蓄存款 + 其他存款
   └─ 广义货币供应量
   └─ 反映社会总需求
   └─ 通货膨胀指标

剪刀差:
- M1 增速 > M2 增速：经济活跃，投资消费旺盛
- M1 增速 < M2 增速：经济放缓，资金定期化
```

---

## ⚠️ 九、预留接口（暂不支持）

以下 API 已预留接口，但 BaoStock 暂不支持：

### 7.1 实时行情

```python
async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
    """获取实时行情（BaoStock 暂不支持）"""
    return {}

async def get_market_realtime_quotes(self, market_types: Optional[List[str]] = None) -> List[MarketQuote]:
    """获取市场实时行情（BaoStock 暂不支持）"""
    return []
```

### 7.2 筹码数据

```python
async def get_chip_data(
    self,
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[ChipData]:
    """获取筹码数据（BaoStock 暂不支持）"""
    return []
```

### 7.3 龙虎榜

```python
async def get_daily_billboard(self, trade_date: Optional[str] = None) -> List[BillboardEntry]:
    """获取龙虎榜单数据（BaoStock 暂不支持）"""
    return []
```

### 7.4 所属板块

```python
async def get_belong_board(self, code: str) -> List[BoardInfo]:
    """获取股票所属板块（BaoStock 暂不支持）"""
    return []
```

### 7.5 指数成分股

```python
async def get_members(self, index_code: str) -> List[IndexComponent]:
    """获取指数成分股（BaoStock 暂不支持）"""
    return []
```

### 7.6 资金流向

```python
async def get_today_bill(self, trade_date: Optional[str] = None) -> List[CapitalFlowItem]:
    """获取当日资金流向（BaoStock 暂不支持）"""
    return []

async def get_history_bill(
    self,
    code: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[CapitalFlowItem]:
    """获取历史资金流向（BaoStock 暂不支持）"""
    return []
```

### 7.7 股东信息

```python
async def get_top10_stock_holder_info(self, code: str) -> List[ShareholderInfo]:
    """获取前十大股东信息（BaoStock 暂不支持）"""
    return []
```

### 7.8 财务业绩

```python
async def get_financial_performance(
    self,
    code: str,
    report_date: Optional[str] = None,
    report_type: str = "quarterly"
) -> List[FinancialPerformance]:
    """获取财务业绩数据（BaoStock 暂不支持）"""
    return []
```

---

## 📋 七、API 使用频率统计

### 已实现功能使用频率

| 功能类别 | 调用频率 | 重要性 | 说明 |
|---------|---------|--------|------|
| **K 线数据** | ⭐⭐⭐⭐⭐ | 极高 | 最基础功能 |
| **估值指标** | ⭐⭐⭐⭐ | 高 | 估值分析 |
| **分红除权** | ⭐⭐⭐ | 中 | 分红研究 |
| **股票信息** | ⭐⭐⭐⭐ | 高 | 基础数据 |
| **板块数据** | ⭐⭐⭐ | 中 | 行业分析 |
| **指数数据** | ⭐⭐⭐⭐ | 高 | 大盘分析 |
| **财务数据** | ⭐⭐⭐⭐ | 高 | 基本面分析 |

### 推荐数据源配置

```python
# backend/app/config.py
DATA_SOURCE_PRIORITY = [
    "tushare",      # 主要数据源（如果有 Token）
    "efinance",     # 第二数据源（免费，数据全）
    "akshare",      # 第三数据源（免费，开源）
    "baostock"      # 备用数据源（免费，稳定）
]

# 如果无 Tushare Token
DATA_SOURCE_PRIORITY = [
    "efinance",     # 主要数据源
    "akshare",      # 第二数据源
    "baostock"      # 备用数据源
]
```

---

## 🎯 八、API 选择建议

### 不同场景的数据源选择

| 使用场景 | 推荐数据源 | 原因 |
|---------|-----------|------|
| **日常 K 线查询** | EFinance/BaoStock | 免费、稳定 |
| **历史数据回测** | BaoStock | 免费、数据完整 |
| **估值指标分析** | BaoStock | 免费、指标全 |
| **分红数据研究** | BaoStock | 历史数据完整 |
| **财务数据分析** | BaoStock | 季频财务数据 |
| **实时行情** | EFinance | 支持实时数据 |
| **资金流向** | EFinance/AkShare | BaoStock 不支持 |
| **龙虎榜** | EFinance/AkShare | BaoStock 不支持 |

### BaoStock 优势场景

✅ **推荐使用 BaoStock**:
- 历史 K 线数据（1990 年至今）
- 估值指标查询（PE/PB/PS/PCF）
- 分红除权数据
- 复权因子计算
- 指数 K 线数据
- 季频财务数据（盈利能力、营运能力）
- 作为备用数据源

❌ **不推荐使用 BaoStock**:
- 实时行情查询
- 资金流向分析
- 龙虎榜数据
- 股东持股信息
- 财务业绩数据

---

## 📚 九、相关文档

### BaoStock 系列文档

1. [BaoStock 完整使用指南](file://m:\Project\Quant\backend\BAOSTOCK_COMPLETE_GUIDE.md)
2. [BaoStock 复权数据详解](file://m:\Project\Quant\backend\BAOSTOCK_ADJUST_GUIDE.md)
3. [BaoStock 指数数据查询](file://m:\Project\Quant\backend\BAOSTOCK_INDEX_GUIDE.md)
4. [BaoStock 估值指标查询](file://m:\Project\Quant\backend\BAOSTOCK_VALUATION_GUIDE.md)
5. [BaoStock 除权除息信息](file://m:\Project\Quant\backend\BAOSTOCK_DIVIDEND_GUIDE.md)
6. [BaoStock 复权因子查询](file://m:\Project\Quant\backend\BAOSTOCK_FACTOR_GUIDE.md)
7. [BaoStock 季频盈利能力](file://m:\Project\Quant\backend\BAOSTOCK_PROFIT_GUIDE.md)
8. [BaoStock 季频营运能力](file://m:\Project\Quant\backend\BAOSTOCK_OPERATION_GUIDE.md)
9. [BaoStock 季频成长能力](file://m:\Project\Quant\backend\BAOSTOCK_GROWTH_GUIDE.md)
10. [BaoStock API 分类总览](file://m:\Project\Quant\backend\BAOSTOCK_API_SUMMARY.md)（本文档）

### 官方资源

- **官网**: http://www.baostock.com
- **文档**: http://baostock.com/baostock/index.html
- **PyPI**: https://pypi.python.org/pypi/baostock

---

## 总结

### BaoStock API 特点

| 特点 | 说明 |
|------|------|
| **完全免费** | 无需注册，无积分要求 |
| **数据完整** | 1990 年至今完整历史数据 |
| **Python 友好** | pandas DataFrame 格式 |
| **易于集成** | 简单 API，快速上手 |
| **适合离线** | 可批量下载历史数据 |
| **财务数据** | 季频盈利能力、营运能力 |

### 已实现功能

✅ **34 个 API 方法**  
✅ **10 大功能类别**  
✅ **9 份详细文档**  
✅ **完整代码实现**  
✅ **丰富使用示例**  

---

**文档版本**: v1.7  
**最后更新**: 2026-03-19  
**更新内容**: 添加货币供应量 API（月度、年度）  
**维护者**: Quant Team

**祝数据获取顺利！** 📊✨
