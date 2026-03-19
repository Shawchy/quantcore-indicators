# BaoStock 估值指标查询指南

**文档版本**: v1.0  
**更新日期**: 2026-03-19  
**主题**: 沪深 A 股估值指标（日频）查询指南

---

## 📋 目录

1. [估值指标简介](#估值指标简介)
2. [支持的估值指标](#支持的估值指标)
3. [数据范围说明](#数据范围说明)
4. [API 使用方法](#api 使用方法)
5. [使用示例](#使用示例)
6. [在 Quant 项目中的使用](#在 quant-项目中的使用)
7. [估值分析方法](#估值分析方法)
8. [注意事项](#注意事项)

---

## 估值指标简介

### 什么是估值指标？

估值指标是用于评估股票价格是否合理的财务指标，通过将股价与公司的财务数据（如盈利、销售、现金流、净资产等）进行比较，帮助投资者判断股票的投资价值。

### 为什么使用 TTM？

**TTM **(Trailing Twelve Months) - 滚动 12 个月

- ✅ **时效性强** - 使用最近 12 个月的数据
- ✅ **连续性好** - 不受财年截止影响
- ✅ **反映现状** - 更能反映公司当前经营状况

### 估值指标的作用

1. **判断价格高低** - 识别低估/高估股票
2. **横向对比** - 同行业内公司对比
3. **纵向分析** - 历史估值水平对比
4. **投资决策** - 买入/卖出参考依据

---

## 支持的估值指标

### 1. 滚动市盈率 (peTTM)

**公式**: 
```
peTTM = 收盘价 / 每股盈余 (EPS)TTM
```

**说明**:
- 最常用的估值指标
- 反映投资者愿意为每元盈利支付的价格
- 适用于盈利稳定的成熟企业

**解读**:
| peTTM 值 | 估值水平 | 说明 |
|---------|---------|------|
| < 15 | 低估 | 可能被低估，或增长前景差 |
| 15-25 | 合理 | 估值合理 |
| > 25 | 高估 | 可能被高估，或增长预期高 |
| < 0 | 亏损 | 企业亏损 |

**适用行业**:
- ✅ 消费、医药、金融等盈利稳定行业
- ❌ 周期性行业、亏损企业

### 2. 滚动市销率 (psTTM)

**公式**:
```
psTTM = 收盘价 / 每股销售额 TTM
```

**说明**:
- 适用于未盈利企业
- 不受会计政策影响
- 适合成长型企业

**解读**:
| psTTM 值 | 估值水平 |
|---------|---------|
| < 3 | 低估 |
| 3-8 | 合理 |
| > 8 | 高估 |

**适用行业**:
- ✅ 互联网、生物科技等成长型企业
- ✅ 未盈利企业
- ✅ 销售收入稳定的企业

### 3. 滚动市现率 (pcfNcfTTM)

**公式**:
```
pcfNcfTTM = 收盘价 / 每股现金流 TTM
```

**说明**:
- 基于现金流，更难被操纵
- 反映企业真实盈利能力
- 适合现金流稳定的企业

**解读**:
| pcfNcfTTM 值 | 估值水平 |
|-------------|---------|
| < 10 | 低估 |
| 10-20 | 合理 |
| > 20 | 高估 |

**适用行业**:
- ✅ 现金流稳定的企业
- ✅ 重资产行业
- ❌ 现金流波动大的企业

### 4. 市净率 (pbMRQ)

**公式**:
```
pbMRQ = 收盘价 / 每股净资产 (MRQ)
```

**说明**:
- MRQ = Most Recent Quarter（最近季度）
- 反映企业清算价值
- 适合重资产企业

**解读**:
| pbMRQ 值 | 估值水平 |
|---------|---------|
| < 1.5 | 低估 |
| 1.5-3 | 合理 |
| > 3 | 高估 |

**适用行业**:
- ✅ 银行、保险、地产等重资产行业
- ❌ 轻资产、知识密集型企业

---

## 数据范围说明

### 时间范围

| 数据类型 | 开始日期 | 说明 |
|---------|---------|------|
| 日频估值 | 2006-01-01 | 所有 A 股 |
| 周/月估值 | ❌ 不支持 | 仅有日线数据 |

### 支持股票

- ✅ 上海 A 股 (600000-609999)
- ✅ 深圳 A 股 (000001-002999, 300000-300999)
- ❌ B 股
- ❌ 指数
- ❌ 基金

### 数据字段

| 字段 | 类型 | 说明 | 精度 |
|------|------|------|------|
| date | String | 日期 | YYYY-MM-DD |
| code | String | 股票代码 | sh.xxxxxx |
| close | Double | 收盘价 | 4 位小数 |
| peTTM | Double | 滚动市盈率 | 4 位小数 |
| psTTM | Double | 滚动市销率 | 4 位小数 |
| pcfNcfTTM | Double | 滚动市现率 | 4 位小数 |
| pbMRQ | Double | 市净率 | 4 位小数 |

---

## API 使用方法

### 函数签名

```python
rs = bs.query_history_k_data_plus(
    security_code,    # 股票代码（必需）
    fields,           # 指标字段（必需）
    start_date='',    # 开始日期（可选）
    end_date='',      # 结束日期（可选）
    frequency='d',    # 频率（固定为 d）
    adjustflag='3'    # 复权类型（固定为 3）
)
```

### 参数说明

| 参数 | 说明 | 是否必填 | 示例 |
|------|------|---------|------|
| **security_code** | 股票代码 | 是 | `sh.600000` |
| **fields** | 估值指标字段 | 是 | `date,close,peTTM,pbMRQ,psTTM,pcfNcfTTM` |
| **start_date** | 开始日期 | 否 | `2023-01-01` |
| **end_date** | 结束日期 | 否 | `2024-12-31` |
| **frequency** | 频率 | 否 | `d`（固定） |
| **adjustflag** | 复权类型 | 否 | `3`（固定） |

### 必填字段

```python
# ✅ 必须包含 close 收盘价
fields = "date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM"

# ❌ 错误：缺少 close
fields = "date,code,peTTM,pbMRQ,psTTM,pcfNcfTTM"
```

---

## 使用示例

### 示例 1：获取单只股票估值数据

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()
print('login respond error_code:'+lg.error_code)
print('login respond  error_msg:'+lg.error_msg)

# 获取浦发银行估值指标
rs = bs.query_history_k_data_plus(
    "sh.600000",
    "date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM",
    start_date='2023-01-01',
    end_date='2024-12-31',
    frequency="d",
    adjustflag="3"
)

# 转换为 DataFrame
result_list = []
while (rs.error_code == '0') & rs.next():
    result_list.append(rs.get_row_data())

result = pd.DataFrame(result_list, columns=rs.fields)

# 保存
result.to_csv("600000_valuation.csv", index=False, encoding='utf-8-sig')
print(f"共获取 {len(result)} 条估值数据")

bs.logout()
```

### 示例 2：获取多只股票估值对比

```python
import baostock as bs
import pandas as pd

lg = bs.login()

# 银行股列表
banks = [
    ("sh.600000", "浦发银行"),
    ("sh.600016", "民生银行"),
    ("sh.600036", "招商银行")
]

for code, name in banks:
    rs = bs.query_history_k_data_plus(
        code,
        "date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM",
        start_date='2024-01-01',
        end_date='2024-12-31',
        frequency="d",
        adjustflag="3"
    )
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    df = pd.DataFrame(data_list, columns=rs.fields)
    
    # 计算最新估值
    latest = df.iloc[-1] if len(df) > 0 else None
    if latest is not None:
        print(f"{name}: PE={latest['peTTM']}, PB={latest['pbMRQ']}, PS={latest['psTTM']}")

bs.logout()
```

### 示例 3：估值历史走势分析

```python
import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt

lg = bs.login()

# 获取贵州茅台估值数据
rs = bs.query_history_k_data_plus(
    "sh.600519",
    "date,close,peTTM,pbMRQ",
    start_date='2020-01-01',
    end_date='2024-12-31',
    frequency="d",
    adjustflag="3"
)

data_list = []
while (rs.error_code == '0') & rs.next():
    data_list.append(rs.get_row_data())

df = pd.DataFrame(data_list, columns=rs.fields)
df['date'] = pd.to_datetime(df['date'])
df.set_index('date', inplace=True)

# 转换类型
for col in ['peTTM', 'pbMRQ']:
    df[col] = df[col].astype(float)

# 绘制估值走势
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))

# PE 走势
ax1.plot(df.index, df['peTTM'], linewidth=2)
ax1.axhline(y=25, color='r', linestyle='--', label='高估线 (25)')
ax1.axhline(y=15, color='g', linestyle='--', label='低估线 (15)')
ax1.set_title('贵州茅台 PE-TTM 走势')
ax1.legend()
ax1.grid(True)

# PB 走势
ax2.plot(df.index, df['pbMRQ'], linewidth=2, color='orange')
ax2.axhline(y=3, color='r', linestyle='--', label='高估线 (3)')
ax2.axhline(y=1.5, color='g', linestyle='--', label='低估线 (1.5)')
ax2.set_title('贵州茅台 PB-MRQ 走势')
ax2.legend()
ax2.grid(True)

plt.tight_layout()
plt.show()

bs.logout()
```

### 示例 4：估值分位数计算

```python
import baostock as bs
import pandas as pd
import numpy as np

lg = bs.login()

# 获取历史估值数据（5 年）
rs = bs.query_history_k_data_plus(
    "sh.600000",
    "date,peTTM,pbMRQ,psTTM,pcfNcfTTM",
    start_date='2019-01-01',
    end_date='2024-12-31',
    frequency="d",
    adjustflag="3"
)

data_list = []
while (rs.error_code == '0') & rs.next():
    data_list.append(rs.get_row_data())

df = pd.DataFrame(data_list, columns=rs.fields)

# 转换类型
for col in ['peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']:
    df[col] = df[col].astype(float)

# 计算当前估值分位数
latest = df.iloc[-1]
percentiles = {}

for col in ['peTTM', 'pbMRQ', 'psTTM', 'pcfNcfTTM']:
    # 计算当前值在历史中的位置
    pct = (df[col] < latest[col]).mean() * 100
    percentiles[col] = pct
    print(f"{col}: 当前值={latest[col]:.2f}, 历史分位数={pct:.1f}%")

# 判断估值水平
print("\n估值判断:")
for metric, pct in percentiles.items():
    if pct < 20:
        print(f"{metric}: 低估（低于{100-pct:.0f}%的历史时期）")
    elif pct > 80:
        print(f"{metric}: 高估（高于{pct:.0f}%的历史时期）")
    else:
        print(f"{metric}: 合理")

bs.logout()
```

### 示例 5：估值选股策略

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
    # 筛选 A 股
    if code.startswith(("sh.6", "sz.0", "sz.3")):
        stock_list.append(code)

print(f"共找到 {len(stock_list)} 只股票")

# 获取最新估值数据（最近一个交易日）
import datetime
end_date = datetime.datetime.now().strftime("%Y-%m-%d")
start_date = (datetime.datetime.now() - datetime.timedelta(days=10)).strftime("%Y-%m-%d")

low_pe_stocks = []

for code in stock_list[:50]:  # 仅测试前 50 只
    rs = bs.query_history_k_data_plus(
        code,
        "date,code,close,peTTM,pbMRQ",
        start_date=start_date,
        end_date=end_date,
        frequency="d",
        adjustflag="3"
    )
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    if len(data_list) > 0:
        latest = data_list[-1]
        pe = float(latest[3]) if latest[3] else 999
        pb = float(latest[4]) if latest[4] else 999
        
        # 筛选低估值股票
        if 0 < pe < 15 and 0 < pb < 2:
            low_pe_stocks.append({
                'code': latest[1],
                'close': latest[2],
                'pe': pe,
                'pb': pb
            })

# 排序
low_pe_stocks.sort(key=lambda x: x['pe'])

print("\n低估值股票（PE<15, PB<2）:")
for stock in low_pe_stocks[:10]:
    print(f"{stock['code']}: PE={stock['pe']:.2f}, PB={stock['pb']:.2f}")

bs.logout()
```

---

## 在 Quant 项目中的使用

### 通过 BaoStock 适配器

```python
from app.adapters.baostock_adapter import BaostockAdapter

# 初始化
adapter = BaostockAdapter()
await adapter.initialize()

# 获取估值指标
valuation_data = await adapter.get_valuation_indicators(
    code="600000",
    start_date="2023-01-01",
    end_date="2024-12-31"
)

# 处理数据
for item in valuation_data:
    print(f"日期：{item['date']}, PE: {item['pe_ttm']}, PB: {item['pb_mrq']}")

await adapter.close()
```

### 在策略中的应用

```python
# 低估值选股策略
from app.services.stock_service import StockService

service = StockService()

# 获取股票池
stocks = await service.get_stock_list()

low_valuation_stocks = []

for stock in stocks:
    # 获取最新估值
    valuation = await data_source_manager.get_valuation_indicators(
        code=stock.code,
        start_date="2024-12-01",
        end_date="2024-12-31"
    )
    
    if valuation and len(valuation) > 0:
        latest = valuation[-1]
        
        # 低估值筛选
        if (latest['pe_ttm'] and 0 < latest['pe_ttm'] < 15 and
            latest['pb_mrq'] and 0 < latest['pb_mrq'] < 2):
            low_valuation_stocks.append({
                'code': stock.code,
                'name': stock.name,
                'pe': latest['pe_ttm'],
                'pb': latest['pb_mrq']
            })

# 排序并选择前 10 只
low_valuation_stocks.sort(key=lambda x: x['pe'])
print(f"找到 {len(low_valuation_stocks)} 只低估值股票")
```

---

## 估值分析方法

### 1. 横向对比法

**同行业对比**:
```python
# 对比银行股估值
banks = {
    "sh.600000": "浦发银行",
    "sh.600016": "民生银行",
    "sh.600036": "招商银行",
    "sh.601398": "工商银行"
}

for code, name in banks.items():
    valuation = await get_latest_valuation(code)
    print(f"{name}: PE={valuation['pe']}, PB={valuation['pb']}")
```

### 2. 纵向对比法

**历史估值对比**:
```python
# 获取 5 年历史数据
valuation_history = await get_valuation_history(
    code="600000",
    start_date="2019-01-01",
    end_date="2024-12-31"
)

# 计算历史平均和分位数
avg_pe = valuation_history['pe_ttm'].mean()
current_pe = valuation_history['pe_ttm'].iloc[-1]
percentile = (valuation_history['pe_ttm'] < current_pe).mean()

print(f"当前 PE: {current_pe}, 历史平均：{avg_pe:.2f}")
print(f"历史分位数：{percentile*100:.1f}%")
```

### 3. 综合估值法

**多指标综合评估**:
```python
def calculate_valuation_score(pe, pb, ps):
    """计算综合估值得分（0-100，越低越低估）"""
    # 权重：PE 40%, PB 30%, PS 30%
    score = pe * 0.4 + pb * 0.3 + ps * 0.3
    return score

# 对股票池进行评分
for stock in stock_pool:
    valuation = await get_latest_valuation(stock.code)
    score = calculate_valuation_score(
        valuation['pe_ttm'] or 0,
        valuation['pb_mrq'] or 0,
        valuation['ps_ttm'] or 0
    )
    stock.valuation_score = score

# 按得分排序
stock_pool.sort(key=lambda x: x.valuation_score)
```

---

## 注意事项

### ⚠️ 重要提示

#### 1. 仅支持日线

```python
# ✅ 正确：使用日线
rs = bs.query_history_k_data_plus(
    "sh.600000",
    fields="...",
    frequency="d"
)

# ❌ 错误：不支持周线、月线
rs = bs.query_history_k_data_plus(
    "sh.600000",
    fields="...",
    frequency="w"  # 不支持！
)
```

#### 2. 指数无估值数据

```python
# ❌ 错误：指数没有估值数据
rs = bs.query_history_k_data_plus(
    "sh.000001",  # 上证指数
    fields="date,peTTM,pbMRQ"  # 会返回空数据
)

# ✅ 正确：仅支持个股
rs = bs.query_history_k_data_plus(
    "sh.600000",  # 个股
    fields="date,peTTM,pbMRQ"
)
```

#### 3. 负值处理

```python
# 负值表示亏损或现金流为负
if pe_ttm < 0:
    print("企业亏损，PE 无意义")

if pcf_ncf_ttm < 0:
    print("现金流为负，PCF 无意义")
```

#### 4. 不同行业估值差异

| 行业 | 合理 PE | 合理 PB | 说明 |
|------|--------|--------|------|
| 银行 | 5-10 | 0.5-1.5 | 低估值行业 |
| 消费 | 15-30 | 3-8 | 高估值行业 |
| 科技 | 20-50 | 5-15 | 高成长高估值 |
| 周期 | 10-20 | 1-3 | 周期性波动 |

#### 5. 数据更新时间

- **更新频率**: 每日更新
- **更新时间**: 交易日 17:30 后
- **建议**: 在交易日晚间获取最新数据

#### 6. 数据质量

- ✅ 数据来源：交易所官方数据
- ✅ 计算准确：基于财报数据计算
- ⚠️ 注意：财报发布后可能调整

---

## 总结

### 估值指标特点

| 指标 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| **peTTM** | 最常用，易理解 | 不适用亏损企业 | 盈利稳定企业 |
| **psTTM** | 适用未盈利企业 | 忽略盈利能力 | 成长型企业 |
| **pcfNcfTTM** | 难被操纵 | 波动较大 | 现金流稳定企业 |
| **pbMRQ** | 反映清算价值 | 忽略盈利能力 | 重资产企业 |

### 推荐使用策略

1. **多指标结合** - 不要单一依赖某个指标
2. **行业对比** - 同行业内横向对比
3. **历史对比** - 与自身历史对比
4. **综合考虑** - 结合成长性、盈利能力

### 最佳实践

```python
# 1. 获取完整估值数据
valuation = await adapter.get_valuation_indicators(
    code="600000",
    start_date="2020-01-01",
    end_date="2024-12-31"
)

# 2. 计算历史分位数
pe_percentile = calculate_percentile(valuation, 'pe_ttm')

# 3. 行业对比
industry_avg = get_industry_average('银行业')

# 4. 综合判断
if pe_percentile < 20 and current_pe < industry_avg:
    print("低估，可关注")
elif pe_percentile > 80:
    print("高估，谨慎")
else:
    print("估值合理")
```

---

## 相关资源

### 官方文档
- **BaoStock 官网**: http://www.baostock.com
- **历史行情 API**: http://baostock.com/baostock/index.php/证券历史交易数据
- **估值指标说明**: http://baostock.com/baostock/index.php/沪深 A 股估值指标

### 项目文档
- [BaoStock 完整使用指南](file://m:\Project\Quant\backend\BAOSTOCK_COMPLETE_GUIDE.md)
- [BaoStock 指数数据查询](file://m:\Project\Quant\backend\BAOSTOCK_INDEX_GUIDE.md)

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19  
**维护者**: Quant Team

**祝投资顺利！** 📈✨
