# BaoStock 复权因子查询指南

**文档版本**: v1.0  
**更新日期**: 2026-03-19  
**主题**: 复权因子信息查询指南

---

## 📋 目录

1. [复权因子简介](#复权因子简介)
2. [API 使用方法](#api 使用方法)
3. [返回数据说明](#返回数据说明)
4. [复权因子计算](#复权因子计算)
5. [使用示例](#使用示例)
6. [在 Quant 项目中的使用](#在 quant-项目中的使用)
7. [注意事项](#注意事项)

---

## 复权因子简介

### 什么是复权因子？

**复权因子**是用于调整股票价格，使其在除权除息日保持连续性的关键数据。

### 为什么需要复权因子？

股票在**除权除息**时，股价会发生跳空：

- **派息** - 股价下跌（分红部分）
- **送股** - 股价除权（股本增加）
- **配股** - 股价调整（融资行为）

为了保持 K 线图的连续性，需要使用复权因子调整历史价格。

### BaoStock 复权方法

BaoStock 使用**"涨跌幅复权法"**计算复权因子：

**核心原理**:
- 确保资金收益率为 100%
- 不会因为分红导致投资减少
- 不会因为配股导致投资增加

**详细说明**:
- [BaoStock 复权因子简介.pdf](media:BaoStock 复权因子简介.pdf)
- [BaoStock 前复权日 K 线数据计算简介.pdf](media:BaoStock 前复权日 K 线数据计算简介.pdf)

---

## API 使用方法

### 函数签名

```python
rs = bs.query_adjust_factor(
    code,              # 股票代码（必需）
    start_date='',     # 开始日期（可选）
    end_date=''        # 结束日期（可选）
)
```

### 参数说明

| 参数 | 说明 | 是否必填 | 示例 |
|------|------|---------|------|
| **code** | 股票代码，格式 sh.xxxxxx 或 sz.xxxxxx | 是 | `sh.600000` |
| **start_date** | 开始日期，YYYY-MM-DD | 否 | `2015-01-01` |
| **end_date** | 结束日期，YYYY-MM-DD | 否 | `2017-12-31` |

**默认值**:
- `start_date`: 2015-01-01
- `end_date`: 当前日期

---

## 返回数据说明

### 复权因子字段

| 字段 | 说明 | 类型 |
|------|------|------|
| **code** | 证券代码 | String |
| **dividOperateDate** | 除权除息日期 | Date |
| **foreAdjustFactor** | 向前复权因子 | Double |
| **backAdjustFactor** | 向后复权因子 | Double |
| **adjustFactor** | 本次复权因子 | Double |

### 复权因子类型

#### 1. 向前复权因子 (foreAdjustFactor)

**公式**:
```
foreAdjustFactor = 除权日前收盘价 / 除权日最近前收盘价
```

**用途**: 向前调整历史价格，保持当前价格不变

**特点**:
- ✅ 与当前价格一致
- ✅ 适合技术分析和回测
- ✅ 最常用的复权方式

#### 2. 向后复权因子 (backAdjustFactor)

**公式**:
```
backAdjustFactor = 除权日最近前收盘价 / 除权日前收盘价
```

**用途**: 向后调整当前价格，保持历史价格不变

**特点**:
- ✅ 反映真实投资收益
- ✅ 适合计算累计收益
- ❌ 当前价格可能很高

#### 3. 本次复权因子 (adjustFactor)

**说明**: 当次除权除息的复权因子

**用途**: 计算复权价格

---

## 复权因子计算

### 复权价格计算

#### 前复权价格

```python
# 前复权收盘价
adjusted_close = close / fore_adjust_factor

# 前复权开盘价
adjusted_open = open / fore_adjust_factor

# 前复权最高价
adjusted_high = high / fore_adjust_factor

# 前复权最低价
adjusted_low = low / fore_adjust_factor
```

#### 后复权价格

```python
# 后复权收盘价
adjusted_close = close * back_adjust_factor

# 后复权开盘价
adjusted_open = open * back_adjust_factor

# 后复权最高价
adjusted_high = high * back_adjust_factor

# 后复权最低价
adjusted_low = low * back_adjust_factor
```

### 示例计算

**假设**:
- 除权日前收盘价：10.00 元
- 除权日方案：10 派 5 元（每股派 0.5 元）
- 除权日理论价格：9.50 元

**计算**:
```
foreAdjustFactor = 10.00 / 9.50 = 1.0526
backAdjustFactor = 9.50 / 10.00 = 0.95

# 前复权
除权日前价格调整：10.00 / 1.0526 = 9.50 元
除权日后价格保持：9.50 元

# 后复权
除权日前价格保持：10.00 元
除权日后价格调整：9.50 * 0.95 = 10.00 元
```

### 多次除权处理

当股票多次除权时，使用**累积复权因子**:

```python
# 累积向前复权因子
cumulative_fore_factor = factor1 * factor2 * factor3 * ...

# 前复权价格
adjusted_price = original_price / cumulative_fore_factor
```

---

## 使用示例

### 示例 1：获取单只股票复权因子

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()
print('login respond error_code:'+lg.error_code)
print('login respond  error_msg:'+lg.error_msg)

# 查询 2015-2017 年复权因子
rs = bs.query_adjust_factor(
    code="sh.600000",
    start_date="2015-01-01",
    end_date="2017-12-31"
)

# 转换为 DataFrame
rs_list = []
while (rs.error_code == '0') & rs.next():
    rs_list.append(rs.get_row_data())

result = pd.DataFrame(rs_list, columns=rs.fields)

# 保存
result.to_csv("adjust_factor.csv", index=False, encoding='utf-8-sig')
print(result)

bs.logout()
```

### 示例 2：计算前复权价格

```python
import baostock as bs
import pandas as pd

lg = bs.login()

# 1. 获取 K 线数据
kline_rs = bs.query_history_k_data_plus(
    "sh.600000",
    "date,code,open,high,low,close",
    start_date="2017-01-01",
    end_date="2017-12-31",
    frequency="d",
    adjustflag="3"  # 不复权
)

kline_list = []
while (kline_rs.error_code == '0') & kline_rs.next():
    kline_list.append(kline_rs.get_row_data())

kline_df = pd.DataFrame(kline_list, columns=kline_rs.fields)

# 2. 获取复权因子
factor_rs = bs.query_adjust_factor(
    code="sh.600000",
    start_date="2017-01-01",
    end_date="2017-12-31"
)

factor_list = []
while (factor_rs.error_code == '0') & factor_rs.next():
    factor_list.append(factor_rs.get_row_data())

factor_df = pd.DataFrame(factor_list, columns=factor_rs.fields)

# 3. 计算前复权价格
if len(factor_df) > 0:
    # 使用最新复权因子
    latest_factor = float(factor_df.iloc[-1]['foreAdjustFactor'])
    
    kline_df['open'] = kline_df['open'].astype(float) / latest_factor
    kline_df['high'] = kline_df['high'].astype(float) / latest_factor
    kline_df['low'] = kline_df['low'].astype(float) / latest_factor
    kline_df['close'] = kline_df['close'].astype(float) / latest_factor
    
    print("前复权价格计算完成")
    print(kline_df.tail())

bs.logout()
```

### 示例 3：获取全部 A 股复权因子

```python
import baostock as bs
import pandas as pd
from datetime import datetime, timedelta

lg = bs.login()

# 获取股票列表
rs = bs.query_stock_basic()
stock_list = []
while (rs.error_code == '0') & rs.next():
    row = rs.get_row_data()
    code = row[0]
    if code.startswith(("sh.6", "sz.0", "sz.3")):
        stock_list.append(code)

print(f"共找到 {len(stock_list)} 只股票")

# 获取每只股票的复权因子（最近一年）
end_date = datetime.now()
start_date = end_date - timedelta(days=365)

all_factors = {}

for i, code in enumerate(stock_list[:50]):  # 测试前 50 只
    rs = bs.query_adjust_factor(
        code=code,
        start_date=start_date.strftime("%Y-%m-%d"),
        end_date=end_date.strftime("%Y-%m-%d")
    )
    
    factors = []
    while (rs.error_code == '0') & rs.next():
        factors.append(rs.get_row_data())
    
    if factors:
        all_factors[code] = factors
        print(f"{code}: {len(factors)} 次除权")
    
    if (i + 1) % 10 == 0:
        print(f"已处理 {i+1}/{len(stock_list)} 只股票")

print(f"\n共 {len(all_factors)} 只股票有除权记录")

bs.logout()
```

### 示例 4：分析除权频率

```python
import baostock as bs
import pandas as pd
from collections import Counter

lg = bs.login()

# 获取浦发银行历史复权因子
rs = bs.query_adjust_factor(
    code="sh.600000",
    start_date="2010-01-01",
    end_date="2024-12-31"
)

factors = []
while (rs.error_code == '0') & rs.next():
    factors.append(rs.get_row_data())

df = pd.DataFrame(factors, columns=rs.fields)

# 转换日期
df['dividOperateDate'] = pd.to_datetime(df['dividOperateDate'])
df['year'] = df['dividOperateDate'].dt.year
df['month'] = df['dividOperateDate'].dt.month

# 分析
print("=== 除权除息分析 ===")
print(f"总除权次数：{len(df)}")
print(f"平均每年除权：{len(df)/len(df['year'].unique()):.2f} 次")

# 按年份统计
yearly = df.groupby('year').size()
print("\n年度除权统计:")
print(yearly)

# 按月份统计
monthly = df.groupby('month').size()
print("\n月度除权统计:")
for month, count in monthly.items():
    print(f"{month}月：{count}次")

# 复权因子统计
print("\n复权因子统计:")
print(f"向前复权因子范围：{df['foreAdjustFactor'].min():.4f} - {df['foreAdjustFactor'].max():.4f}")
print(f"向后复权因子范围：{df['backAdjustFactor'].min():.4f} - {df['backAdjustFactor'].max():.4f}")

bs.logout()
```

---

## 在 Quant 项目中的使用

### 通过 BaoStock 适配器

```python
from app.adapters.baostock_adapter import BaostockAdapter

adapter = BaostockAdapter()
await adapter.initialize()

# 获取复权因子
adjust_factors = await adapter.get_adjust_factor(
    code="600000",
    start_date="2015-01-01",
    end_date="2024-12-31"
)

# 处理数据
for factor in adjust_factors:
    print(f"除权日：{factor['divid_operate_date']}")
    print(f"  向前复权因子：{factor['fore_adjust_factor']}")
    print(f"  向后复权因子：{factor['back_adjust_factor']}")
    print(f"  本次复权因子：{factor['adjust_factor']}")

await adapter.close()
```

### 复权价格计算

```python
# 使用复权因子计算复权价格
async def calculate_adjusted_price(code: str):
    """计算前复权价格"""
    
    # 1. 获取不复权 K 线数据
    klines = await data_source_manager.get_kline(
        code=code,
        adjust="none"  # 不复权
    )
    
    # 2. 获取复权因子
    factors = await adapter.get_adjust_factor(
        code=code,
        start_date=klines[0].date,
        end_date=klines[-1].date
    )
    
    if not factors:
        return klines
    
    # 3. 使用最新复权因子
    latest_factor = factors[-1]['fore_adjust_factor']
    
    # 4. 计算复权价格
    adjusted_klines = []
    for kline in klines:
        adjusted = KLineData(
            code=kline.code,
            date=kline.date,
            open=kline.open / latest_factor,
            high=kline.high / latest_factor,
            low=kline.low / latest_factor,
            close=kline.close / latest_factor,
            volume=kline.volume,
            amount=kline.amount
        )
        adjusted_klines.append(adjusted)
    
    return adjusted_klines
```

---

## 注意事项

### ⚠️ 重要提示

#### 1. 复权因子与复权 K 线的关系

BaoStock 的 `query_history_k_data_plus()` API 已经内置了复权处理：

```python
# ✅ 推荐：直接使用复权 K 线
rs = bs.query_history_k_data_plus(
    "sh.600000",
    "date,code,open,high,low,close",
    start_date="2015-01-01",
    end_date="2024-12-31",
    frequency="d",
    adjustflag="2"  # 前复权
)

# 不需要手动使用复权因子计算
```

#### 2. 复权因子的用途

复权因子主要用于：
- ✅ 理解复权计算原理
- ✅ 自定义复权算法
- ✅ 验证复权数据准确性
- ✅ 学术研究

**一般用户**建议直接使用 `adjustflag` 参数获取复权 K 线。

#### 3. 数据范围

- **开始日期**: 2015-01-01（默认）
- **结束日期**: 当前日期（默认）
- **建议**: 获取较长时间范围以包含所有除权记录

#### 4. 复权因子更新

- **更新时间**: 除权除息日后更新
- **更新频率**: 不定期（随公司公告）
- **建议**: 定期获取最新数据

#### 5. 精度问题

复权因子精度：小数点后 6 位

```python
# 计算时注意精度
adjusted_price = round(close / fore_adjust_factor, 4)
```

#### 6. 多次除权处理

当股票多次除权时，应使用**累积复权因子**:

```python
# 累积向前复权因子
cumulative_factor = 1.0
for factor in factors:
    cumulative_factor *= factor['fore_adjust_factor']

# 使用累积因子调整价格
adjusted_price = original_price / cumulative_factor
```

---

## 总结

### 复权因子应用

| 应用场景 | 使用方法 | 说明 |
|---------|---------|------|
| **直接获取复权 K 线** | adjustflag 参数 | 推荐使用 |
| **自定义复权算法** | 复权因子计算 | 灵活控制 |
| **验证数据准确性** | 对比复权因子 | 数据校验 |
| **学术研究** | 分析复权规律 | 理论研究 |

### 复权因子类型对比

| 类型 | 公式 | 用途 | 特点 |
|------|------|------|------|
| **向前复权** | 前收盘价/前收盘价 | 技术分析 | 与当前价格一致 |
| **向后复权** | 前收盘价/前收盘价 | 收益计算 | 反映真实收益 |
| **本次复权** | 当次复权因子 | 单次调整 | 用于累积计算 |

### 最佳实践

```python
# 1. 优先使用内置复权 K 线
klines = await adapter.get_kline(
    code="600000",
    adjust="qfq"  # 前复权
)

# 2. 需要时使用复权因子
factors = await adapter.get_adjust_factor(
    code="600000",
    start_date="2015-01-01",
    end_date="2024-12-31"
)

# 3. 计算累积复权因子
cumulative_factor = 1.0
for factor in factors:
    cumulative_factor *= factor['fore_adjust_factor']

# 4. 验证复权价格
adjusted_close = original_close / cumulative_factor
```

---

## 相关资源

### 官方文档
- **BaoStock 官网**: http://www.baostock.com
- **复权因子 API**: http://baostock.com/baostock/index.php/复权因子
- **复权因子简介**: 媒体文件:BaoStock 复权因子简介.pdf
- **前复权计算**: 媒体文件:BaoStock 前复权日 K 线数据计算简介.pdf

### 项目文档
- [BaoStock 完整使用指南](file://m:\Project\Quant\backend\BAOSTOCK_COMPLETE_GUIDE.md)
- [BaoStock 复权数据详解](file://m:\Project\Quant\backend\BAOSTOCK_ADJUST_GUIDE.md)
- [BaoStock 除权除息信息](file://m:\Project\Quant\backend\BAOSTOCK_DIVIDEND_GUIDE.md)

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19  
**维护者**: Quant Team

**祝数据获取顺利！** 📊✨
