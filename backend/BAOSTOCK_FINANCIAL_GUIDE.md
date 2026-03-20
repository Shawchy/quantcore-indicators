# BaoStock 季频财务数据综合使用指南

## 目录

- [概述](#概述)
- [季频偿债能力](#季频偿债能力)
- [季频现金流量](#季频现金流量)
- [季频杜邦指数](#季频杜邦指数)
- [综合财务分析](#综合财务分析)
- [常见问题](#常见问题)

---

## 概述

BaoStock 提供三大季频财务数据 API，全面评估企业财务状况：

1. **季频偿债能力** (`query_balance_data`)：评估企业偿债能力和财务风险
2. **季频现金流量** (`query_cash_flow_data`)：分析企业现金流状况
3. **季频杜邦指数** (`query_dupont_data`)：杜邦分析体系，分解 ROE 驱动因素

### 数据特点

- **数据范围**：2007 年至今
- **更新频率**：季度更新
- **数据源**：上市公司财报
- **适用场景**：财务分析、风险评估、投资决策

---

## 季频偿债能力

### API 接口

```python
async def get_balance_data(
    self,
    code: str,
    year: Optional[int] = None,
    quarter: Optional[int] = None
) -> List[Dict[str, Any]]
```

### 返回指标

| 字段名 | 指标名称 | 计算公式 | 合理范围 |
|-------|---------|---------|---------|
| `current_ratio` | 流动比率 | 流动资产/流动负债 | 1.5-2.5 |
| `quick_ratio` | 速动比率 | (流动资产 - 存货)/流动负债 | 0.8-1.2 |
| `cash_ratio` | 现金比率 | (货币资金 + 交易性金融资产)/流动负债 | 0.2-0.5 |
| `yoy_liability` | 总负债同比增长率 | (本期负债 - 上年同期负债)/上年同期负债 | - |
| `liability_to_asset` | 资产负债率 | 负债总额/资产总额 | 40%-60% |
| `asset_to_equity` | 权益乘数 | 资产总额/股东权益总额 | 1.5-3.0 |

### 使用示例

```python
from app.adapters.baostock_adapter import BaostockAdapter

adapter = BaostockAdapter()
await adapter.initialize()

try:
    # 获取最新季度偿债能力
    result = await adapter.get_balance_data(code="sh.600000")
    
    # 获取指定年份季度
    result = await adapter.get_balance_data(
        code="sh.600000",
        year=2023,
        quarter=2
    )
    
    # 分析结果
    for item in result:
        print(f"流动比率：{item['current_ratio']}")
        print(f"速动比率：{item['quick_ratio']}")
        print(f"资产负债率：{item['liability_to_asset']}")
        
finally:
    await adapter.close()
```

### 指标解读

#### 1. 流动比率 (Current Ratio)

- **含义**：衡量企业短期偿债能力
- **公式**：流动资产 ÷ 流动负债
- **解读**：
  - > 2.0：偿债能力强
  - 1.5-2.0：正常水平
  - < 1.0：短期偿债风险

#### 2. 速动比率 (Quick Ratio)

- **含义**：更严格的短期偿债能力指标
- **公式**：(流动资产 - 存货) ÷ 流动负债
- **解读**：
  - > 1.0：快速偿债能力强
  - 0.8-1.0：正常水平
  - < 0.5：快速偿债风险

#### 3. 现金比率 (Cash Ratio)

- **含义**：最保守的偿债能力指标
- **公式**：(货币资金 + 交易性金融资产) ÷ 流动负债
- **解读**：
  - 反映即时支付能力
  - 过高可能资金利用效率低

#### 4. 资产负债率 (Debt to Asset Ratio)

- **含义**：衡量长期偿债能力和财务杠杆
- **公式**：负债总额 ÷ 资产总额
- **解读**：
  - 40%-60%：合理水平
  - > 70%：财务风险较高
  - < 30%：财务政策保守

#### 5. 权益乘数 (Equity Multiplier)

- **含义**：反映财务杠杆程度
- **公式**：资产总额 ÷ 股东权益总额
- **解读**：
  - 越高表示财务杠杆越大
  - 与资产负债率正相关

---

## 季频现金流量

### API 接口

```python
async def get_cash_flow_data(
    self,
    code: str,
    year: Optional[int] = None,
    quarter: Optional[int] = None
) -> List[Dict[str, Any]]
```

### 返回指标

| 字段名 | 指标名称 | 计算公式 |
|-------|---------|---------|
| `ca_to_asset` | 流动资产占比 | 流动资产/总资产 |
| `nca_to_asset` | 非流动资产占比 | 非流动资产/总资产 |
| `tangible_asset_to_asset` | 有形资产占比 | 有形资产/总资产 |
| `ebit_to_interest` | 已获利息倍数 | 息税前利润/利息费用 |
| `cfo_to_or` | 现金收入比 | 经营现金净流量/营业收入 |
| `cfo_to_np` | 现金盈利比 | 经营现金净流量/净利润 |
| `cfo_to_gr` | 现金总收入比 | 经营现金净流量/营业总收入 |

### 使用示例

```python
adapter = BaostockAdapter()
await adapter.initialize()

try:
    # 获取现金流量数据
    result = await adapter.get_cash_flow_data(code="sh.600000")
    
    for item in result:
        print(f"流动资产占比：{item['ca_to_asset']}")
        print(f"已获利息倍数：{item['ebit_to_interest']}")
        print(f"现金收入比：{item['cfo_to_or']}")
        print(f"现金盈利比：{item['cfo_to_np']}")
        
finally:
    await adapter.close()
```

### 指标解读

#### 1. 已获利息倍数 (Interest Coverage Ratio)

- **含义**：衡量企业支付利息的能力
- **公式**：息税前利润 ÷ 利息费用
- **解读**：
  - > 3：支付利息能力强
  - 1.5-3：正常水平
  - < 1.5：利息支付风险

#### 2. 现金收入比 (CFO to Operating Revenue)

- **含义**：营业收入的现金含量
- **公式**：经营现金净流量 ÷ 营业收入
- **解读**：
  - > 0.1：收入质量好
  - 持续为正：经营健康
  - 持续为负：可能存在收入虚增

#### 3. 现金盈利比 (CFO to Net Profit)

- **含义**：净利润的现金保障程度
- **公式**：经营现金净流量 ÷ 净利润
- **解读**：
  - > 1：净利润有充足现金支持
  - ≈ 1：盈利质量良好
  - < 1：可能存在应收账款过多

---

## 季频杜邦指数

### API 接口

```python
async def get_dupont_data(
    self,
    code: str,
    year: Optional[int] = None,
    quarter: Optional[int] = None
) -> List[Dict[str, Any]]
```

### 返回指标

| 字段名 | 指标名称 | 计算公式 |
|-------|---------|---------|
| `dupont_roe` | 净资产收益率 | 归属母公司股东净利润/平均归母股东权益 |
| `dupont_asset_to_equity` | 权益乘数 | 平均总资产/平均归母股东权益 |
| `dupont_asset_turn` | 总资产周转率 | 营业总收入/平均总资产 |
| `dupont_pni_to_ni` | 归母净利率 | 归属母公司净利润/净利润 |
| `dupont_ni_to_gr` | 销售净利率 | 净利润/营业总收入 |
| `dupont_tax_burden` | 税负水平 | 净利润/利润总额 |
| `dupont_int_burden` | 利息负担 | 利润总额/息税前利润 |
| `dupont_ebit_to_gr` | 经营利润率 | 息税前利润/营业总收入 |

### 杜邦分析体系

```
ROE (净资产收益率)
= 净利润率 × 总资产周转率 × 权益乘数
= dupont_ni_to_gr × dupont_asset_turn × dupont_asset_to_equity

五因素杜邦分析:
ROE = 税负 × 利息负担 × 经营利润率 × 资产周转率 × 权益乘数
    = dupont_tax_burden × dupont_int_burden × dupont_ebit_to_gr 
      × dupont_asset_turn × dupont_asset_to_equity
```

### 使用示例

```python
adapter = BaostockAdapter()
await adapter.initialize()

try:
    # 获取杜邦指数
    result = await adapter.get_dupont_data(code="sh.600000")
    
    for item in result:
        roe = item['dupont_roe']
        profit_margin = item['dupont_ni_to_gr']
        asset_turnover = item['dupont_asset_turn']
        equity_multiplier = item['dupont_asset_to_equity']
        
        # 验证杜邦恒等式
        calculated_roe = profit_margin * asset_turnover * equity_multiplier
        
        print(f"ROE: {roe:.4f}")
        print(f"销售净利率：{profit_margin:.4f}")
        print(f"总资产周转率：{asset_turnover:.4f}")
        print(f"权益乘数：{equity_multiplier:.4f}")
        print(f"计算 ROE: {calculated_roe:.4f}")
        
finally:
    await adapter.close()
```

### 指标解读

#### 1. 净资产收益率 (ROE)

- **含义**：股东权益收益率，衡量股东投资回报
- **公式**：归属母公司股东净利润 ÷ 平均归母股东权益
- **解读**：
  - > 15%：优秀
  - 10%-15%：良好
  - < 5%：较差

#### 2. 销售净利率 (Net Profit Margin)

- **含义**：反映企业盈利能力
- **公式**：净利润 ÷ 营业总收入
- **解读**：
  - 高净利率：产品竞争力强
  - 低净利率：成本控制差或竞争激烈

#### 3. 总资产周转率 (Asset Turnover)

- **含义**：反映资产管理效率
- **公式**：营业总收入 ÷ 平均总资产
- **解读**：
  - 高周转：资产管理效率高
  - 低周转：资产闲置或销售不畅

#### 4. 权益乘数 (Equity Multiplier)

- **含义**：反映财务杠杆
- **公式**：平均总资产 ÷ 平均归母股东权益
- **解读**：
  - 高乘数：高财务杠杆，高风险高收益
  - 低乘数：低财务杠杆，稳健经营

---

## 综合财务分析

### 1. 财务健康状况评估

```python
def assess_financial_health(balance, cash_flow, dupont):
    """
    综合评估企业财务健康状况
    
    评估维度:
    1. 偿债能力 (40%)
    2. 现金流状况 (30%)
    3. 盈利能力 (30%)
    """
    score = 0
    
    # 偿债能力评分 (40 分)
    if balance['current_ratio'] > 1.5:
        score += 10
    if balance['quick_ratio'] > 1.0:
        score += 10
    if balance['liability_to_asset'] < 0.6:
        score += 10
    if balance['asset_to_equity'] < 3.0:
        score += 10
    
    # 现金流评分 (30 分)
    if cash_flow['ebit_to_interest'] > 3.0:
        score += 10
    if cash_flow['cfo_to_or'] > 0.1:
        score += 10
    if cash_flow['cfo_to_np'] > 1.0:
        score += 10
    
    # 盈利能力评分 (30 分)
    if dupont['dupont_roe'] > 0.10:
        score += 15
    if dupont['dupont_ni_to_gr'] > 0.10:
        score += 15
    
    # 评级
    if score >= 85:
        rating = 'AAA'
        comment = '财务非常健康'
    elif score >= 70:
        rating = 'AA'
        comment = '财务健康'
    elif score >= 55:
        rating = 'A'
        comment = '财务良好'
    elif score >= 40:
        rating = 'BBB'
        comment = '财务一般'
    else:
        rating = 'BB'
        comment = '财务风险较高'
    
    return score, rating, comment
```

### 2. ROE 驱动因素分析

```python
def analyze_roe_drivers(dupont_data):
    """
    分析 ROE 的驱动因素
    
    通过杜邦分析识别 ROE 变化的主要原因
    """
    analysis = []
    
    for i, item in enumerate(dupont_data):
        roe = item['dupont_roe']
        profit_margin = item['dupont_ni_to_gr']
        asset_turnover = item['dupont_asset_turn']
        equity_multiplier = item['dupont_asset_to_equity']
        
        # 判断 ROE 主要驱动因素
        drivers = []
        
        if profit_margin > 0.15:
            drivers.append('高净利率')
        if asset_turnover > 0.8:
            drivers.append('高周转')
        if equity_multiplier > 2.5:
            drivers.append('高杠杆')
        
        analysis.append({
            'period': item['stat_date'],
            'roe': roe,
            'main_drivers': drivers,
            'roe_quality': '高质量' if len(drivers) >= 2 else '一般'
        })
    
    return analysis
```

### 3. 财务风险预警

```python
def financial_warning_signals(balance, cash_flow, dupont):
    """
    识别财务风险信号
    
    预警信号:
    1. 偿债能力风险
    2. 现金流风险
    3. 盈利质量风险
    4. 财务杠杆风险
    """
    warnings = []
    
    # 偿债能力风险
    if balance['current_ratio'] < 1.0:
        warnings.append("⚠️ 流动比率低于 1，短期偿债风险")
    if balance['quick_ratio'] < 0.5:
        warnings.append("⚠️ 速动比率过低，快速偿债能力弱")
    if balance['liability_to_asset'] > 0.7:
        warnings.append("⚠️ 资产负债率过高，长期偿债风险")
    
    # 现金流风险
    if cash_flow['ebit_to_interest'] < 1.5:
        warnings.append("⚠️ 利息保障倍数低，利息支付风险")
    if cash_flow['cfo_to_np'] < 0.5:
        warnings.append("⚠️ 盈利现金含量低，盈利质量差")
    
    # 财务杠杆风险
    if dupont['dupont_asset_to_equity'] > 4.0:
        warnings.append("⚠️ 权益乘数过高，财务杠杆风险大")
    
    # ROE 质量风险
    if dupont['dupont_roe'] < 0.05:
        warnings.append("⚠️ ROE 过低，股东回报差")
    
    return warnings
```

### 4. 同业对比分析

```python
async def compare_financial_metrics(stocks):
    """
    对比多家公司的财务指标
    
    Args:
        stocks: 股票代码列表
    
    Returns:
        DataFrame: 财务指标对比表
    """
    adapter = BaostockAdapter()
    await adapter.initialize()
    
    try:
        comparison = []
        
        for code in stocks:
            # 获取三大财务数据
            balance = await adapter.get_balance_data(code=code)
            cash_flow = await adapter.get_cash_flow_data(code=code)
            dupont = await adapter.get_dupont_data(code=code)
            
            if balance and cash_flow and dupont:
                b = balance[0]
                c = cash_flow[0]
                d = dupont[0]
                
                comparison.append({
                    '代码': code,
                    '流动比率': b['current_ratio'],
                    '速动比率': b['quick_ratio'],
                    '资产负债率': b['liability_to_asset'],
                    'ROE': d['dupont_roe'],
                    '销售净利率': d['dupont_ni_to_gr'],
                    '总资产周转率': d['dupont_asset_turn'],
                    '权益乘数': d['dupont_asset_to_equity'],
                    '现金收入比': c['cfo_to_or']
                })
        
        return pd.DataFrame(comparison)
        
    finally:
        await adapter.close()
```

---

## 常见问题

### Q1: 三大财务数据 API 有什么区别？

**答**：
- **偿债能力**：评估企业偿还债务的能力，关注资产负债表
- **现金流量**：分析企业现金流状况，关注现金创造能力
- **杜邦指数**：分解 ROE 驱动因素，综合分析盈利模式

### Q2: 如何综合使用这三个 API？

**答**：建议按以下顺序分析：
1. 先用**偿债能力**评估财务风险
2. 再用**现金流量**评估盈利质量
3. 最后用**杜邦指数**分析盈利模式

### Q3: 哪些指标最重要？

**答**：核心指标：
- 偿债能力：流动比率、资产负债率
- 现金流量：现金收入比、已获利息倍数
- 杜邦指数：ROE、销售净利率、总资产周转率

### Q4: 如何判断财务数据是否健康？

**答**：健康标准：
- 流动比率 > 1.5
- 资产负债率 < 60%
- ROE > 10%
- 现金收入比 > 0.1
- 已获利息倍数 > 3

### Q5: 杜邦分析有什么实际应用？

**答**：
- **识别盈利模式**：高净利率型 vs 高周转型 vs 高杠杆型
- **对标分析**：与同行业对比找出差距
- **趋势分析**：追踪 ROE 变化原因
- **投资决策**：选择高质量 ROE 企业

---

## 相关文档

- [BaoStock 完整使用指南](./BAOSTOCK_COMPLETE_GUIDE.md)
- [季频盈利能力查询](./BAOSTOCK_PROFIT_GUIDE.md)
- [季频营运能力查询](./BAOSTOCK_OPERATION_GUIDE.md)
- [季频成长能力查询](./BAOSTOCK_GROWTH_GUIDE.md)
- [估值指标查询](./BAOSTOCK_VALUATION_GUIDE.md)
- [除权除息信息](./BAOSTOCK_DIVIDEND_GUIDE.md)
- [复权因子查询](./BAOSTOCK_FACTOR_GUIDE.md)
- [指数数据查询](./BAOSTOCK_INDEX_GUIDE.md)

---

## 参考资料

1. BaoStock 官网：http://www.baostock.com
2. 财务分析教程：https://www.investopedia.com/terms/f/financialratio.asp
3. 杜邦分析：https://www.investopedia.com/terms/d/dupontanalysis.asp
4. 现金流量分析：https://www.investopedia.com/terms/c/cashflow.asp

---

**文档最后更新**：2026-03-19  
**维护者**：Quant 团队  
**联系方式**：support@quant.com
