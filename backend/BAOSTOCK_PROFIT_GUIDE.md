# BaoStock 季频盈利能力查询指南

**文档版本**: v1.0  
**更新日期**: 2026-03-19  
**主题**: 季频盈利能力数据查询指南

---

## 📋 目录

1. [季频盈利能力简介](#季频盈利能力简介)
2. [API 使用方法](#api 使用方法)
3. [返回数据说明](#返回数据说明)
4. [财务指标解读](#财务指标解读)
5. [使用示例](#使用示例)
6. [在 Quant 项目中的使用](#在 quant-项目中的使用)
7. [财务分析方法](#财务分析方法)
8. [注意事项](#注意事项)

---

## 季频盈利能力简介

### 什么是季频盈利能力？

**季频盈利能力**是反映上市公司在每个季度（3 个月）经营获利能力的财务指标集合。

### 为什么重要？

盈利能力指标帮助投资者：
- ✅ **评估公司赚钱能力** - ROE、毛利率、净利率
- ✅ **对比同行业公司** - 横向比较
- ✅ **跟踪业绩趋势** - 季度环比、同比
- ✅ **价值投资决策** - 基本面分析

### 数据范围

- **开始时间**: 2007 年至今
- **更新频率**: 季度更新
- **发布时间**: 季报披露后（4 月、8 月、10 月）

---

## API 使用方法

### 函数签名

```python
rs = bs.query_profit_data(
    code,              # 股票代码（必需）
    year='',           # 年份（可选）
    quarter=''         # 季度（可选）
)
```

### 参数说明

| 参数 | 说明 | 是否必填 | 默认值 |
|------|------|---------|--------|
| **code** | 股票代码，格式 sh.xxxxxx 或 sz.xxxxxx | 是 | - |
| **year** | 统计年份 | 否 | 当前年 |
| **quarter** | 统计季度（1-4） | 否 | 当前季度 |

### quarter 参数说明

| 值 | 季度 | 统计期间 | 披露时间 |
|----|------|---------|---------|
| **1** | 一季报 | 1 月 1 日 -3 月 31 日 | 4 月 |
| **2** | 中报 | 1 月 1 日 -6 月 30 日 | 8 月 |
| **3** | 三季报 | 1 月 1 日 -9 月 30 日 | 10 月 |
| **4** | 年报 | 1 月 1 日 -12 月 31 日 | 次年 4 月 |

---

## 返回数据说明

### 10 个核心字段

| 字段 | 说明 | 类型 | 单位 |
|------|------|------|------|
| **code** | 证券代码 | String | - |
| **pubDate** | 公司发布财报的日期 | Date | - |
| **statDate** | 财报统计的季度最后一天 | Date | - |
| **roeAvg** | 净资产收益率 (平均)(%) | Double | % |
| **npMargin** | 销售净利率 (%) | Double | % |
| **gpMargin** | 销售毛利率 (%) | Double | % |
| **netProfit** | 净利润 | Double | 元 |
| **epsTTM** | 每股收益 | Double | 元/股 |
| **MBRevenue** | 主营营业收入 | Double | 元 |
| **totalShare** | 总股本 | Double | 股 |
| **liqaShare** | 流通股本 | Double | 股 |

---

## 财务指标解读

### 1. ROE (净资产收益率)

**公式**:
```
ROE = 归属母公司股东净利润 / [(期初权益 + 期末权益)/2] × 100%
```

**说明**:
- 反映股东权益的收益水平
- 巴菲特最看重的财务指标
- 衡量公司使用股东资金赚钱的效率

**解读**:
| ROE 值 | 评价 | 说明 |
|-------|------|------|
| > 20% | 优秀 | 持续高 ROE 是牛股特征 |
| 15-20% | 良好 | 盈利能力较强 |
| 10-15% | 一般 | 行业平均水平 |
| < 10% | 较差 | 盈利能力弱 |

### 2. 销售毛利率 (gpMargin)

**公式**:
```
毛利率 = (营业收入 - 营业成本) / 营业收入 × 100%
```

**说明**:
- 反映产品或服务的获利空间
- 高毛利率通常意味着强竞争优势
- 不同行业差异较大

**解读**:
| 毛利率 | 行业特征 |
|-------|---------|
| > 40% | 高科技、医药、品牌消费 |
| 20-40% | 一般制造业、消费品 |
| < 20% | 传统制造业、零售业 |

### 3. 销售净利率 (npMargin)

**公式**:
```
净利率 = 净利润 / 营业收入 × 100%
```

**说明**:
- 反映公司最终盈利能力
- 扣除所有费用后的利润率
- 衡量经营管理效率

### 4. 每股收益 (epsTTM)

**公式**:
```
EPS = 归属母公司股东的净利润 TTM / 最新总股本
```

**说明**:
- TTM = 滚动 12 个月
- 反映每股创造的利润
- 计算 PE 的基础

### 5. 净利润 (netProfit)

**说明**:
- 公司最终盈利金额
- 同比增长率很重要
- 关注扣非净利润

---

## 使用示例

### 示例 1：获取单季度盈利能力

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()
print('login respond error_code:'+lg.error_code)
print('login respond  error_msg:'+lg.error_msg)

# 查询 2017 年 Q2 盈利能力
rs = bs.query_profit_data(
    code="sh.600000",
    year=2017,
    quarter=2
)

# 转换为 DataFrame
profit_list = []
while (rs.error_code == '0') & rs.next():
    profit_list.append(rs.get_row_data())

result = pd.DataFrame(profit_list, columns=rs.fields)

# 输出
print(result)
result.to_csv("profit_data.csv", index=False, encoding='utf-8-sig')

bs.logout()
```

### 示例 2：获取多年季度数据

```python
import baostock as bs
import pandas as pd

lg = bs.login()

# 获取 2020-2024 年所有季度数据
all_profits = []

for year in range(2020, 2025):
    for quarter in range(1, 5):
        rs = bs.query_profit_data(
            code="sh.600000",
            year=year,
            quarter=quarter
        )
        
        while (rs.error_code == '0') & rs.next():
            all_profits.append(rs.get_row_data())

df = pd.DataFrame(all_profits, columns=rs.fields)
print(f"共获取 {len(df)} 条数据")
print(df[['statDate', 'roeAvg', 'npMargin', 'gpMargin', 'netProfit']])

bs.logout()
```

### 示例 3：分析盈利能力趋势

```python
import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt

lg = bs.login()

# 获取贵州茅台 2020-2024 年数据
profits = []
for year in range(2020, 2025):
    for quarter in range(1, 5):
        rs = bs.query_profit_data(
            code="sh.600519",
            year=year,
            quarter=quarter
        )
        
        while (rs.error_code == '0') & rs.next():
            profits.append(rs.get_row_data())

df = pd.DataFrame(profits, columns=rs.fields)
df['statDate'] = pd.to_datetime(df['statDate'])

# 转换数值类型
for col in ['roeAvg', 'npMargin', 'gpMargin', 'netProfit']:
    df[col] = pd.to_numeric(df[col], errors='coerce')

# 绘制趋势图
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# ROE 趋势
axes[0, 0].plot(df['statDate'], df['roeAvg'], marker='o')
axes[0, 0].set_title('ROE 趋势')
axes[0, 0].grid(True)

# 毛利率趋势
axes[0, 1].plot(df['statDate'], df['gpMargin'], marker='s', color='green')
axes[0, 1].set_title('毛利率趋势')
axes[0, 1].grid(True)

# 净利率趋势
axes[1, 0].plot(df['statDate'], df['npMargin'], marker='^', color='red')
axes[1, 0].set_title('净利率趋势')
axes[1, 0].grid(True)

# 净利润趋势
axes[1, 1].bar(df['statDate'], df['netProfit']/1e8, color='orange')
axes[1, 1].set_title('净利润 (亿元)')
axes[1, 1].grid(True)

plt.tight_layout()
plt.show()

bs.logout()
```

### 示例 4：对比同行业多家公司

```python
import baostock as bs
import pandas as pd

lg = bs.login()

# 银行股列表
banks = [
    ("sh.600000", "浦发银行"),
    ("sh.600016", "民生银行"),
    ("sh.600036", "招商银行"),
    ("sh.601398", "工商银行")
]

# 获取最新季度数据
latest_profits = []

for code, name in banks:
    rs = bs.query_profit_data(
        code=code,
        year=2024,
        quarter=2  # 最新季度
    )
    
    while (rs.error_code == '0') & rs.next():
        row = rs.get_row_data()
        latest_profits.append({
            'code': code,
            'name': name,
            'roe': float(row[3]) if row[3] else 0,
            'np_margin': float(row[4]) if row[4] else 0,
            'gp_margin': float(row[5]) if row[5] else 0,
            'net_profit': float(row[6]) if row[6] else 0
        })

# 对比分析
df = pd.DataFrame(latest_profits)
print("\n银行股盈利能力对比:")
print(df[['name', 'roe', 'np_margin', 'gp_margin']])

# 排序
print("\n按 ROE 排序:")
print(df.sort_values('roe', ascending=False)[['name', 'roe']])

bs.logout()
```

### 示例 5：筛选高 ROE 股票

```python
import baostock as bs
import pandas as pd

lg = bs.login()

# 获取股票列表
rs = bs.query_stock_basic()
stock_list = []
while (rs.error_code == '0') & rs.next():
    row = rs.get_row_data()
    code = row[0]
    if code.startswith(("sh.6", "sz.0", "sz.3")):
        stock_list.append((code, row[1]))

print(f"共找到 {len(stock_list)} 只股票")

# 筛选高 ROE 股票
high_roe_stocks = []

for code, name in stock_list[:100]:  # 测试前 100 只
    rs = bs.query_profit_data(
        code=code,
        year=2024,
        quarter=2
    )
    
    while (rs.error_code == '0') & rs.next():
        row = rs.get_row_data()
        roe = float(row[3]) if row[3] else 0
        
        # ROE > 15%
        if roe > 15:
            high_roe_stocks.append({
                'code': code,
                'name': name,
                'roe': roe,
                'np_margin': float(row[4]) if row[4] else 0,
                'net_profit': float(row[6]) if row[6] else 0
            })

# 排序
high_roe_stocks.sort(key=lambda x: x['roe'], reverse=True)

print("\n高 ROE 股票 (ROE>15%):")
for stock in high_roe_stocks[:20]:
    print(f"{stock['code']} {stock['name']}: "
          f"ROE={stock['roe']:.2f}%, "
          f"净利率={stock['np_margin']:.2f}%")

bs.logout()
```

---

## 在 Quant 项目中的使用

### 通过 BaoStock 适配器

```python
from app.adapters.baostock_adapter import BaostockAdapter

adapter = BaostockAdapter()
await adapter.initialize()

# 获取季频盈利能力
profit_data = await adapter.get_profit_data(
    code="600000",
    year=2024,
    quarter=2
)

# 处理数据
for profit in profit_data:
    print(f"代码：{profit['code']}")
    print(f"  统计日期：{profit['stat_date']}")
    print(f"  ROE: {profit['roe_avg']}%")
    print(f"  毛利率：{profit['gp_margin']}%")
    print(f"  净利率：{profit['np_margin']}%")
    print(f"  净利润：{profit['net_profit']/1e8:.2f}亿元")

await adapter.close()
```

### 在策略中的应用

```python
# 基于 ROE 的选股策略
async def select_high_roe_stocks():
    """选择高 ROE 股票"""
    
    # 获取股票池
    stocks = await stock_service.get_stock_list()
    
    high_roe_stocks = []
    
    for stock in stocks:
        # 获取最新季度数据
        profit_data = await adapter.get_profit_data(
            code=stock.code,
            year=2024,
            quarter=2
        )
        
        if profit_data and len(profit_data) > 0:
            latest = profit_data[0]
            
            # ROE > 15% 且 净利率 > 10%
            if (latest['roe_avg'] and latest['roe_avg'] > 15 and
                latest['np_margin'] and latest['np_margin'] > 10):
                high_roe_stocks.append({
                    'code': stock.code,
                    'name': stock.name,
                    'roe': latest['roe_avg'],
                    'np_margin': latest['np_margin']
                })
    
    # 按 ROE 排序
    high_roe_stocks.sort(key=lambda x: x['roe'], reverse=True)
    return high_roe_stocks[:20]  # 返回前 20 只
```

---

## 财务分析方法

### 1. 趋势分析

**同比分析** (Year-over-Year):
```python
# 对比今年 Q2 vs 去年 Q2
current_roe = get_roe(2024, 2)
last_year_roe = get_roe(2023, 2)
yoy_growth = (current_roe - last_year_roe) / last_year_roe * 100
```

**环比分析** (Quarter-over-Quarter):
```python
# 对比 Q2 vs Q1
q2_roe = get_roe(2024, 2)
q1_roe = get_roe(2024, 1)
qoq_growth = (q2_roe - q1_roe) / q1_roe * 100
```

### 2. 杜邦分析

**杜邦公式**:
```
ROE = 净利率 × 总资产周转率 × 权益乘数
```

通过杜邦分析可以分解 ROE 的来源：
- 高净利率 = 产品竞争力强
- 高周转率 = 管理效率高
- 高权益乘数 = 财务杠杆高

### 3. 行业对比

```python
# 计算行业平均 ROE
industry_roe = industry_profits['roe_avg'].mean()

# 对比个股与行业
if stock_roe > industry_roe * 1.5:
    print("显著高于行业平均水平")
elif stock_roe > industry_roe:
    print("高于行业平均水平")
else:
    print("低于行业平均水平")
```

---

## 注意事项

### ⚠️ 重要提示

#### 1. 数据发布时间

| 季度 | 统计期间 | 披露时间 |
|------|---------|---------|
| 一季报 | 1-3 月 | 4 月 1 日 -4 月 30 日 |
| 中报 | 1-6 月 | 7 月 1 日 -8 月 31 日 |
| 三季报 | 1-9 月 | 10 月 1 日 -10 月 31 日 |
| 年报 | 1-12 月 | 次年 1 月 -4 月 30 日 |

**注意**: 在披露期结束后才能获取完整数据

#### 2. 财务数据单位

```python
# 净利润、营收单位是"元"，不是"万元"或"亿元"
net_profit_yuan = profit['net_profit']  # 元
net_profit_yi = net_profit_yuan / 1e8    # 转换为亿元
```

#### 3. TTM 概念

**TTM **(Trailing Twelve Months) - 滚动 12 个月

```python
# epsTTM 是滚动 12 个月的每股收益
# 不是单季度的 EPS
```

#### 4. 财务造假识别

**警示信号**:
- ❌ ROE 突然大幅上升
- ❌ 毛利率远高于同行
- ❌ 净利润增长但现金流为负
- ❌ 应收账款异常增长

#### 5. 不同行业差异

| 行业 | ROE 特征 | 毛利率特征 |
|------|---------|-----------|
| 银行 | 10-15% | 50-70% |
| 白酒 | 20-30% | 70-90% |
| 医药 | 15-20% | 60-80% |
| 制造 | 8-15% | 20-40% |
| 零售 | 10-15% | 15-25% |

#### 6. 数据质量

- ✅ 数据来源：上市公司财报
- ✅ 计算准确：按证监会公式
- ⚠️ 注意：财报可能后期调整

---

## 总结

### 季频盈利能力应用

| 应用场景 | 使用方法 | 说明 |
|---------|---------|------|
| **基本面分析** | ROE、毛利率、净利率 | 评估盈利能力 |
| **选股策略** | 筛选高 ROE 股票 | 价值投资 |
| **趋势跟踪** | 季度环比、同比 | 业绩变化 |
| **行业对比** | 同行业对比分析 | 相对估值 |

### 关键指标

| 指标 | 重要性 | 说明 |
|------|-------|------|
| **ROE** | ⭐⭐⭐⭐⭐ | 最核心指标 |
| **毛利率** | ⭐⭐⭐⭐ | 产品竞争力 |
| **净利率** | ⭐⭐⭐⭐ | 最终盈利能力 |
| **EPS** | ⭐⭐⭐ | 每股收益 |

### 最佳实践

```python
# 1. 获取多年数据
profits = []
for year in range(2020, 2025):
    for quarter in range(1, 5):
        profit = await adapter.get_profit_data(
            code="600000",
            year=year,
            quarter=quarter
        )
        profits.extend(profit)

# 2. 分析趋势
roe_trend = [p['roe_avg'] for p in profits]
if all(x > y for x, y in zip(roe_trend[1:], roe_trend[:-1])):
    print("ROE 持续上升")

# 3. 行业对比
industry_avg = calculate_industry_average('银行业')
if current_roe > industry_avg:
    print("优于行业平均水平")
```

---

## 相关资源

### 官方文档
- **BaoStock 官网**: http://www.baostock.com
- **季频盈利能力 API**: http://baostock.com/baostock/index.php/季频盈利能力

### 项目文档
- [BaoStock 完整使用指南](file://m:\Project\Quant\backend\BAOSTOCK_COMPLETE_GUIDE.md)
- [BaoStock 估值指标查询](file://m:\Project\Quant\backend\BAOSTOCK_VALUATION_GUIDE.md)

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19  
**维护者**: Quant Team

**祝投资顺利！** 📈✨
