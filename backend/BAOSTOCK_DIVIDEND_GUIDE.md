# BaoStock 除权除息信息查询指南

**文档版本**: v1.0  
**更新日期**: 2026-03-19  
**主题**: 除权除息信息（分红数据）查询指南

---

## 📋 目录

1. [除权除息简介](#除权除息简介)
2. [API 使用方法](#api 使用方法)
3. [返回数据说明](#返回数据说明)
4. [使用示例](#使用示例)
5. [在 Quant 项目中的使用](#在 quant-项目中的使用)
6. [分红数据分析](#分红数据分析)
7. [注意事项](#注意事项)

---

## 除权除息简介

### 什么是除权除息？

**除权除息**是上市公司向股东分配利润时的重要环节：

- **除息** - 派发现金红利
- **除权** - 送红股或转增股本
- **除权除息** - 同时派现和送股

### 重要日期

| 日期 | 说明 | 影响 |
|------|------|------|
| **预案公告日** | 董事会提出分红方案 | 市场预期 |
| **股东大会日** | 股东大会审议分红方案 | 方案通过 |
| **实施公告日** | 公布具体实施日期 | 确定时间表 |
| **股权登记日** | 登记在册股东享有分红权 | 最后买入日 |
| **除权除息日** | 股价进行调整 | 股价跳空 |
| **派息日** | 现金红利到账 | 资金到账 |
| **红股上市日** | 送转股上市交易 | 股份到账 |

### 查询意义

1. **历史分红统计** - 评估公司分红政策
2. **股息率计算** - 计算投资回报率
3. **复权计算** - 理解复权因子来源
4. **投资决策** - 高分红股票筛选

---

## API 使用方法

### 函数签名

```python
rs = bs.query_dividend_data(
    code,              # 股票代码（必需）
    year,              # 年份（必需）
    yearType="report"  # 年份类型（必需）
)
```

### 参数说明

| 参数 | 说明 | 是否必填 | 示例 |
|------|------|---------|------|
| **code** | 股票代码，格式 sh.xxxxxx 或 sz.xxxxxx | 是 | `sh.600000` |
| **year** | 年份 | 是 | `2023` |
| **yearType** | 年份类型 | 否 | `report` 或 `operate` |

### yearType 参数

| 值 | 说明 | 用途 |
|----|------|------|
| **report** | 预案公告年份（默认） | 查看公司哪年公告分红 |
| **operate** | 除权除息年份 | 查看哪年实际实施分红 |

**示例**:
- 2023 年 5 月公告 2022 年度分红方案
  - `year="2022", yearType="report"` - 按预案公告年份
  - `year="2023", yearType="operate"` - 按除权除息年份

---

## 返回数据说明

### 日期字段

| 字段 | 说明 | 格式 |
|------|------|------|
| **code** | 证券代码 | sh.xxxxxx |
| **divid_pre_notice_date** | 预披露公告日 | YYYY-MM-DD |
| **divid_agm_pum_date** | 股东大会公告日期 | YYYY-MM-DD |
| **divid_plan_announce_date** | 预案公告日 | YYYY-MM-DD |
| **divid_plan_date** | 分红实施公告日 | YYYY-MM-DD |
| **divid_regist_date** | 股权登记日 | YYYY-MM-DD |
| **divid_operate_date** | 除权除息日 | YYYY-MM-DD |
| **divid_pay_date** | 派息日 | YYYY-MM-DD |
| **divid_stock_market_date** | 红股上市交易日 | YYYY-MM-DD |

### 金额字段

| 字段 | 说明 | 单位 |
|------|------|------|
| **divid_cash_ps_before_tax** | 每股股利（税前） | 元 |
| **divid_cash_ps_after_tax** | 每股股利（税后） | 元 |
| **divid_stocks_ps** | 每股红股 | 股 |
| **divid_cash_stock** | 分红送转 | 文本描述 |
| **divid_reserve_to_stock_ps** | 每股转增资本 | 股 |

### 分红类型

**分红方案通常表述为**: "10 派 X 元送 Y 股转 Z 股"

- **10 派 X 元** - 每 10 股派发现金 X 元
- **10 送 Y 股** - 每 10 股送红股 Y 股
- **10 转 Z 股** - 每 10 股转增 Z 股

**示例**:
- "10 派 7.57 元" → 每股派现 0.757 元
- "10 转 1 派 5.15 元" → 每股转 0.1 股，派现 0.515 元
- "10 转 3 派 2 元" → 每股转 0.3 股，派现 0.2 元

---

## 使用示例

### 示例 1：获取单只股票历史分红数据

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()
print('login respond error_code:'+lg.error_code)
print('login respond  error_msg:'+lg.error_msg)

# 获取浦发银行 2015-2017 年分红数据
rs_list = []

for year in [2015, 2016, 2017]:
    rs = bs.query_dividend_data(
        code="sh.600000",
        year=str(year),
        yearType="report"
    )
    
    while (rs.error_code == '0') & rs.next():
        rs_list.append(rs.get_row_data())

# 转换为 DataFrame
result = pd.DataFrame(rs_list, columns=rs.fields)

# 保存
result.to_csv("dividend_data.csv", index=False, encoding='utf-8-sig')
print(result)

bs.logout()
```

### 示例 2：获取多年分红数据

```python
import baostock as bs
import pandas as pd

lg = bs.login()

# 获取 2010-2024 年全部分红数据
rs_list = []

for year in range(2010, 2025):
    rs = bs.query_dividend_data(
        code="sh.600000",
        year=str(year),
        yearType="report"
    )
    
    if rs.error_code == '0':
        while rs.next():
            rs_list.append(rs.get_row_data())
    else:
        print(f"{year}年数据获取失败：{rs.error_msg}")

result = pd.DataFrame(rs_list, columns=rs.fields)
print(f"共获取 {len(result)} 条分红数据")
print(result[['divid_operate_date', 'divid_cash_ps_before_tax', 
              'divid_stocks_ps', 'divid_reserve_to_stock_ps']])

bs.logout()
```

### 示例 3：分析分红历史

```python
import baostock as bs
import pandas as pd

lg = bs.login()

# 获取贵州茅台全部分红数据
rs_list = []
for year in range(2001, 2025):
    rs = bs.query_dividend_data(
        code="sh.600519",
        year=str(year),
        yearType="operate"
    )
    
    while (rs.error_code == '0') & rs.next():
        rs_list.append(rs.get_row_data())

df = pd.DataFrame(rs_list, columns=rs.fields)

# 转换类型
df['divid_cash_ps_before_tax'] = pd.to_numeric(
    df['divid_cash_ps_before_tax'], errors='coerce'
)
df['divid_operate_date'] = pd.to_datetime(df['divid_operate_date'])

# 分析
print("=== 贵州茅台分红分析 ===")
print(f"分红次数：{len(df)}")
print(f"累计每股派现：{df['divid_cash_ps_before_tax'].sum():.2f}元")
print(f"平均每年派现：{df['divid_cash_ps_before_tax'].mean():.2f}元")
print(f"最大单次派现：{df['divid_cash_ps_before_tax'].max():.2f}元")

# 按年度统计
df['year'] = df['divid_operate_date'].dt.year
yearly = df.groupby('year')['divid_cash_ps_before_tax'].sum()
print("\n年度分红统计:")
print(yearly)

bs.logout()
```

### 示例 4：筛选高分红股票

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

# 统计近 3 年分红数据
high_dividend_stocks = []

for code, name in stock_list[:100]:  # 测试前 100 只
    total_dividend = 0
    years_with_dividend = 0
    
    for year in range(2021, 2024):
        rs = bs.query_dividend_data(
            code=code,
            year=str(year),
            yearType="operate"
        )
        
        year_dividend = 0
        while (rs.error_code == '0') & rs.next():
            row = rs.get_row_data()
            cash = float(row[9]) if row[9] else 0
            year_dividend += cash
        
        if year_dividend > 0:
            years_with_dividend += 1
            total_dividend += year_dividend
    
    # 连续 3 年分红
    if years_with_dividend == 3:
        high_dividend_stocks.append({
            'code': code,
            'name': name,
            'total_dividend': total_dividend,
            'years': years_with_dividend
        })

# 按分红总额排序
high_dividend_stocks.sort(key=lambda x: x['total_dividend'], reverse=True)

print("\n连续 3 年高分红股票:")
for stock in high_dividend_stocks[:20]:
    print(f"{stock['code']} {stock['name']}: "
          f"累计{stock['total_dividend']:.2f}元/股")

bs.logout()
```

### 示例 5：计算股息率

```python
import baostock as bs
import pandas as pd

lg = bs.login()

# 获取某股票分红数据和股价
code = "sh.600000"

# 1. 获取分红数据
dividend_data = []
for year in range(2020, 2024):
    rs = bs.query_dividend_data(
        code=code,
        year=str(year),
        yearType="operate"
    )
    
    while (rs.error_code == '0') & rs.next():
        row = rs.get_row_data()
        dividend_data.append({
            'date': row[6],  # 除权除息日
            'dividend': float(row[9]) if row[9] else 0
        })

# 2. 获取对应日期股价
for div in dividend_data:
    rs = bs.query_history_k_data_plus(
        code,
        "date,close",
        start_date=div['date'],
        end_date=div['date'],
        frequency="d"
    )
    
    while (rs.error_code == '0') & rs.next():
        row = rs.get_row_data()
        div['close'] = float(row[1])
        # 计算股息率
        div['yield'] = (div['dividend'] / div['close']) * 100

# 输出
print(f"\n{code} 股息率分析:")
for div in dividend_data:
    if 'close' in div:
        print(f"{div['date']}: "
              f"分红{div['dividend']:.3f}元，"
              f"股价{div['close']:.2f}元，"
              f"股息率{div['yield']:.2f}%")

bs.logout()
```

---

## 在 Quant 项目中的使用

### 通过 BaoStock 适配器

```python
from app.adapters.baostock_adapter import BaostockAdapter

adapter = BaostockAdapter()
await adapter.initialize()

# 获取除权除息信息
dividend_data = await adapter.get_dividend_data(
    code="600000",
    start_year=2015,
    end_year=2024,
    year_type="report"  # 或 "operate"
)

# 处理数据
for item in dividend_data:
    print(f"代码：{item['code']}")
    print(f"  除权除息日：{item['divid_operate_date']}")
    print(f"  每股派现 (税前): {item['divid_cash_ps_before_tax']}")
    print(f"  每股送股：{item['divid_stocks_ps']}")
    print(f"  每股转增：{item['divid_reserve_to_stock_ps']}")

await adapter.close()
```

### 在策略中的应用

```python
# 高分红选股策略
from app.services.stock_service import StockService

service = StockService()

# 获取股票池
stocks = await service.get_stock_list()

high_dividend_stocks = []

for stock in stocks:
    # 获取近 3 年分红数据
    dividend_data = await data_source_manager.get_dividend_data(
        code=stock.code,
        start_year=2021,
        end_year=2023
    )
    
    # 计算累计分红
    total_dividend = sum(
        d['divid_cash_ps_before_tax'] 
        for d in dividend_data 
        if d['divid_cash_ps_before_tax']
    )
    
    # 连续分红年份
    years_with_dividend = len([
        d for d in dividend_data 
        if d['divid_cash_ps_before_tax'] and d['divid_cash_ps_before_tax'] > 0
    ])
    
    # 筛选条件：连续 3 年分红，累计分红>1 元
    if years_with_dividend == 3 and total_dividend > 1.0:
        high_dividend_stocks.append({
            'code': stock.code,
            'name': stock.name,
            'total_dividend': total_dividend,
            'years': years_with_dividend
        })

# 排序
high_dividend_stocks.sort(key=lambda x: x['total_dividend'], reverse=True)
print(f"找到 {len(high_dividend_stocks)} 只高分红股票")
```

---

## 分红数据分析

### 分红指标计算

#### 1. 累计分红

```python
def calculate_total_dividend(dividend_data):
    """计算累计每股分红"""
    total = 0
    for d in dividend_data:
        if d['divid_cash_ps_before_tax']:
            total += d['divid_cash_ps_before_tax']
    return total
```

#### 2. 分红频率

```python
def calculate_dividend_frequency(dividend_data):
    """计算分红频率（年）"""
    if not dividend_data:
        return 0
    
    years = set()
    for d in dividend_data:
        if d['divid_operate_date']:
            year = int(d['divid_operate_date'][:4])
            years.add(year)
    
    return len(years)
```

#### 3. 平均股息率

```python
def calculate_avg_yield(dividend_data, price_data):
    """计算平均股息率"""
    yields = []
    
    for div in dividend_data:
        if not div['divid_cash_ps_before_tax']:
            continue
        
        # 查找对应日期股价
        div_date = div['divid_operate_date']
        price = find_price_on_date(price_data, div_date)
        
        if price and price > 0:
            yield_rate = div['divid_cash_ps_before_tax'] / price
            yields.append(yield_rate)
    
    return sum(yields) / len(yields) if yields else 0
```

### 分红政策分类

| 类型 | 特征 | 代表行业 |
|------|------|---------|
| **稳定分红型** | 每年固定分红，金额稳定 | 银行、公用事业 |
| **成长型** | 分红少，利润再投资 | 科技、生物医药 |
| **周期型** | 盈利好时分红，差时不分 | 资源、周期股 |
| **铁公鸡** | 很少或不分红 | 亏损企业 |

### 分红偏好分析

```python
# 分析公司分红偏好
def analyze_dividend_policy(dividend_data):
    """分析公司分红政策"""
    if not dividend_data:
        return "无分红记录"
    
    cash_dividends = [
        d['divid_cash_ps_before_tax'] 
        for d in dividend_data 
        if d['divid_cash_ps_before_tax']
    ]
    
    stock_dividends = [
        d['divid_stocks_ps'] 
        for d in dividend_data 
        if d['divid_stocks_ps'] and d['divid_stocks_ps'] > 0
    ]
    
    # 判断类型
    if len(cash_dividends) == 0:
        return "铁公鸡（不分红）"
    elif len(stock_dividends) > len(cash_dividends) / 2:
        return "偏好送股"
    elif sum(cash_dividends) / len(cash_dividends) > 0.5:
        return "高现金分红"
    else:
        return "常规现金分红"
```

---

## 注意事项

### ⚠️ 重要提示

#### 1. 年份类型选择

```python
# ✅ 正确：明确年份类型
# 查询 2022 年度分红（2023 年公告）
rs = bs.query_dividend_data(
    code="sh.600000",
    year="2022",
    yearType="report"  # 按预案公告年份
)

# 查询 2023 年实施的分红
rs = bs.query_dividend_data(
    code="sh.600000",
    year="2023",
    yearType="operate"  # 按除权除息年份
)
```

#### 2. 数据范围

- **开始年份**: 2006 年
- **结束年份**: 当前年份
- **建议**: 获取多年数据时循环遍历年份

#### 3. 空值处理

```python
# 某些字段可能为空
dividend = {
    'divid_cash_ps_before_tax': float(row[9]) if row[9] else None,
    'divid_stocks_ps': float(row[11]) if row[11] else None
}

# 计算时注意处理 None 值
total = sum(
    d['divid_cash_ps_before_tax'] 
    for d in dividends 
    if d['divid_cash_ps_before_tax'] is not None
)
```

#### 4. 税后金额差异

```python
# 税后金额可能有两个值（差别税率）
# 示例：0.6813 或 0.71915
# 原因：持股期限不同，税率不同
# - 持股<1 个月：20% 税率
# - 持股 1 个月 -1 年：10% 税率
# - 持股>1 年：免税
```

#### 5. 送转股区别

| 类型 | 来源 | 会计处理 |
|------|------|---------|
| **送股** | 未分配利润 | 利润分配 |
| **转增** | 资本公积 | 资本公积转增 |

**对投资者的影响**: 相同，都是增加股数

#### 6. 数据更新时间

- **更新时间**: 公司公告后更新
- **建议**: 在年报季（3-4 月）后获取最新数据

---

## 总结

### 除权除息信息应用

| 应用场景 | 使用方法 | 说明 |
|---------|---------|------|
| **分红统计** | 获取历年分红数据 | 评估分红政策 |
| **股息率计算** | 分红金额/股价 | 投资回报率 |
| **复权计算** | 理解复权因子 | 价格连续性 |
| **高分红选股** | 筛选连续分红股票 | 价值投资 |

### 关键指标

| 指标 | 说明 | 计算 |
|------|------|------|
| **每股分红** | 每股派现金额 | 直接获取 |
| **股息率** | 分红/股价 | 股息率 = 每股分红/股价 |
| **分红率** | 分红/净利润 | 需要净利润数据 |
| **累计分红** | 历史分红总和 | 多年数据累加 |

### 最佳实践

```python
# 1. 获取完整历史数据
dividend_data = await adapter.get_dividend_data(
    code="600000",
    start_year=2010,
    end_year=2024
)

# 2. 计算累计分红
total = sum(
    d['divid_cash_ps_before_tax'] 
    for d in dividend_data 
    if d['divid_cash_ps_before_tax']
)

# 3. 统计分红年份
years = len(set(
    d['divid_operate_date'][:4] 
    for d in dividend_data 
    if d['divid_operate_date']
))

# 4. 判断分红政策
if years >= 5 and total > 2.0:
    print("稳定高分红股票")
```

---

## 相关资源

### 官方文档
- **BaoStock 官网**: http://www.baostock.com
- **除权除息 API**: http://baostock.com/baostock/index.php/除权除息信息

### 项目文档
- [BaoStock 完整使用指南](file://m:\Project\Quant\backend\BAOSTOCK_COMPLETE_GUIDE.md)
- [BaoStock 复权数据详解](file://m:\Project\Quant\backend\BAOSTOCK_ADJUST_GUIDE.md)

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19  
**维护者**: Quant Team

**祝投资顺利！** 📈✨
