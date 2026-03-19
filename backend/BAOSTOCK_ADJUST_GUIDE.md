# BaoStock 复权数据详解

**文档版本**: v1.0  
**更新日期**: 2026-03-19  
**主题**: 复权方法、数据说明、使用注意事项

---

## 📋 目录

1. [复权方法简介](#复权方法简介)
2. [BaoStock 复权方法](#baostock 复权方法)
3. [复权类型选择](#复权类型选择)
4. [数据字段说明](#数据字段说明)
5. [使用示例](#使用示例)
6. [注意事项](#注意事项)
7. [与其他软件对比](#与其他软件对比)

---

## 复权方法简介

### 为什么要复权？

股票在交易过程中会发生**除权除息**事件：

- **分红派息** - 公司向股东分配现金红利
- **送红股** - 公司向股东赠送股票
- **配股** - 公司向股东发行新股融资

这些事件会导致股价出现"跳空"，为了保持价格的连续性和可比性，需要对历史价格进行调整，这就是**复权**。

### 复权的本质

复权是通过调整历史价格，使得 K 线图在除权除息日保持连续，便于技术分析和收益计算。

---

## BaoStock 复权方法

### 涨跌幅复权法

BaoStock 使用**"涨跌幅复权法"**进行复权计算。

#### 核心原理

通过复权因子调整价格，确保：
- ✅ 可以准确计算资金收益率
- ✅ 初始投入资金运用率为 100%
- ✅ 不会因为分红导致投资减少
- ✅ 不会因为配股导致投资增加

#### 复权因子计算

```
复权因子 = (除权前一日收盘价 / 除权后理论价格)

前复权价格 = 实际价格 × 复权因子
```

#### 除权除息价计算

**1. 除息价（现金分红）**:
```
除息价 = 股权登记日收盘价 - 每股红利
```

**2. 除权价（送红股）**:
```
除权价 = 股权登记日收盘价 / (1 + 每股送股数)
```

**3. 除权价（配股）**:
```
除权价 = (股权登记日收盘价 + 配股价 × 每股配股数) / (1 + 每股配股数)
```

**4. 除权除息价（组合）**:
```
除权除息价 = (股权登记日收盘价 - 每股红利 + 配股价 × 每股配股数) / 
            (1 + 每股送股数 + 每股配股数)
```

### 复权类型

BaoStock 支持三种复权类型：

| 类型 | adjustflag | 说明 | 适用场景 |
|------|-----------|------|---------|
| **前复权** | 2 | 以最新价格为基准，向前调整历史价格 | ✅ 技术分析、回测 |
| **后复权** | 1 | 以最早价格为基准，向后调整历史价格 | 计算累计收益 |
| **不复权** | 3 | 使用原始价格 | 查看实际交易价格 |

#### 前复权（推荐）

**特点**:
- 保持当前价格不变
- 调整历史价格
- K 线图从左到右逐渐降低（考虑了分红送股）

**优点**:
- ✅ 便于技术分析
- ✅ 与当前价格一致
- ✅ 适合回测策略

**示例**:
```
假设股票 10 送 10，除权前价格 20 元，除权后价格 10 元

前复权后：
- 除权前价格调整为：10 元
- 除权后价格保持：10 元
- K 线图连续
```

#### 后复权

**特点**:
- 保持历史价格不变
- 调整当前价格
- K 线图从左到右逐渐升高

**优点**:
- ✅ 反映真实投资收益
- ✅ 便于计算累计收益率

**示例**:
```
假设股票 10 送 10，除权前价格 20 元，除权后价格 10 元

后复权后：
- 除权前价格保持：20 元
- 除权后价格调整为：20 元
- K 线图连续
```

#### 不复权

**特点**:
- 使用交易所公布的原始价格
- K 线图在除权日会出现跳空

**适用场景**:
- 查看实际交易价格
- 分析除权除息影响

---

## 复权类型选择

### 推荐使用策略

| 使用场景 | 推荐复权类型 | 原因 |
|---------|------------|------|
| **技术分析** | 前复权 (qfq) | 与当前价格一致，指标计算准确 |
| **策略回测** | 前复权 (qfq) | 收益率计算准确，避免分红再投资问题 |
| **收益计算** | 后复权 (hfq) | 反映真实投资收益 |
| **实际交易** | 不复权 | 查看真实交易价格 |

### 在 Quant 项目中的使用

```python
from app.adapters import data_source_manager

# 推荐使用前复权（默认）
klines = await data_source_manager.get_kline(
    code="601398",
    start_date="2020-01-01",
    end_date="2024-12-31",
    adjust="qfq"  # 前复权（推荐）
)

# 后复权
klines = await data_source_manager.get_kline(
    code="601398",
    adjust="hfq"  # 后复权
)

# 不复权
klines = await data_source_manager.get_kline(
    code="601398",
    adjust=""  # 不复权
)
```

---

## 数据字段说明

### 日线指标字段

| 字段名 | 类型 | 说明 | 算法 |
|-------|------|------|------|
| **date** | String | 交易所日期 | YYYY-MM-DD |
| **code** | String | 证券代码 | sh.xxxxxx |
| **open** | Double | 开盘价 | 元 |
| **high** | Double | 最高价 | 元 |
| **low** | Double | 最低价 | 元 |
| **close** | Double | 收盘价 | 元 |
| **preclose** | Double | 前收盘价 | 除权除息调整后的价格 |
| **volume** | Long | 成交量 | 股 |
| **amount** | Double | 成交额 | 元 |
| **adjustflag** | Integer | 复权状态 | 1=后复权，2=前复权，3=不复权 |
| **turn** | Double | 换手率 | % |
| **tradestatus** | Integer | 交易状态 | 1=正常，0=停牌 |
| **pctChg** | Double | 涨跌幅 | % |
| **peTTM** | Double | 滚动市盈率 | - |
| **psTTM** | Double | 滚动市销率 | - |
| **pcfNcfTTM** | Double | 滚动市现率 | - |
| **pbMRQ** | Double | 市净率 | - |
| **isST** | Integer | 是否 ST | 1=是，0=否 |

### 前收盘价说明

**preclose** 字段是理解复权的关键：

- **正常情况**: preclose = 前一日 actual close
- **除权除息日**: preclose = 除权除息价（经交易所计算并公布）
- **首发日**: preclose = 发行价

**示例**:
```
股票 600000 在 2017-07-03 发生 10 派 1 元（每股分红 0.1 元）

股权登记日 (2017-06-30): 收盘价 = 12.65 元
除息日 (2017-07-03): 
  - 实际开盘 = 12.64 元
  - 前收盘价 = 12.55 元 (12.65 - 0.1)
  - 涨跌幅 = (12.56 - 12.55) / 12.55 = 0.08%
```

### 周/月线指标

| 字段名 | 说明 | 算法 |
|-------|------|------|
| date | 行情日期 | 周/月最后一个交易日 |
| open | 开盘价 | 周/月首个交易日开盘价 |
| high | 最高价 | 周/月内最高价 |
| low | 最低价 | 周/月内最低价 |
| close | 收盘价 | 周/月最后交易日收盘价 |
| volume | 成交量 | 周/月累计成交量 |
| amount | 成交额 | 周/月累计成交额 |
| turn | 换手率 | 周/月平均换手率 |
| pctChg | 涨跌幅 | [(期末收盘价 - 期初前收盘价) / 期初前收盘价] × 100% |

### 分钟线指标（5/15/30/60 分钟）

| 字段名 | 说明 |
|-------|------|
| date | 交易所日期 |
| time | 交易所时间 (YYYYMMDDHHMMSSsss) |
| open | 开盘价 |
| high | 最高价 |
| low | 最低价 |
| close | 收盘价 |
| volume | 累计成交量 |
| amount | 累计成交额 |
| adjustflag | 复权状态 |

**注意**: 分钟线不包含指数数据，时间范围为近 5 年。

---

## 使用示例

### 示例 1：获取前复权日线数据

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()

# 获取前复权日线数据
rs = bs.query_history_k_data_plus(
    "sh.600000",
    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,pctChg",
    start_date="2023-01-01",
    end_date="2024-12-31",
    frequency="d",
    adjustflag="2"  # 前复权
)

# 转换为 DataFrame
data_list = []
while (rs.error_code == "0") & rs.next():
    data_list.append(rs.get_row_data())

df = pd.DataFrame(data_list, columns=rs.fields)

# 分析
print(df.describe())
print(f"最新收盘价：{df.iloc[-1]['close']}")
print(f"区间涨跌幅：{df.iloc[-1]['pctChg']}%")

# 登出
bs.logout()
```

### 示例 2：对比不同复权方式

```python
import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt

lg = bs.login()

# 获取不同复权方式的数据
adjust_types = {"qfq": "2", "hfq": "1", "none": "3"}
results = {}

for name, flag in adjust_types.items():
    rs = bs.query_history_k_data_plus(
        "sh.600000",
        "date,close",
        start_date="2020-01-01",
        end_date="2024-12-31",
        frequency="d",
        adjustflag=flag
    )
    
    data_list = []
    while (rs.error_code == "0") & rs.next():
        data_list.append(rs.get_row_data())
    
    df = pd.DataFrame(data_list, columns=rs.fields)
    df['close'] = df['close'].astype(float)
    results[name] = df['close']

# 绘制对比图
plt.figure(figsize=(14, 7))
for name, series in results.items():
    plt.plot(series.index, series.values, label=name)

plt.title('不同复权方式对比')
plt.xlabel('日期')
plt.ylabel('收盘价')
plt.legend()
plt.grid(True)
plt.show()

bs.logout()
```

### 示例 3：计算收益率（使用前复权）

```python
import baostock as bs
import pandas as pd

lg = bs.login()

# 获取前复权数据
rs = bs.query_history_k_data_plus(
    "sh.600000",
    "date,close,pctChg",
    start_date="2023-01-01",
    end_date="2024-12-31",
    frequency="d",
    adjustflag="2"
)

data_list = []
while (rs.error_code == "0") & rs.next():
    data_list.append(rs.get_row_data())

df = pd.DataFrame(data_list, columns=rs.fields)

# 计算累计收益率
df['close'] = df['close'].astype(float)
df['pctChg'] = df['pctChg'].astype(float)

# 累计收益率
cumulative_return = (df['close'].iloc[-1] / df['close'].iloc[0] - 1) * 100
print(f"累计收益率：{cumulative_return:.2f}%")

# 年化收益率
days = len(df)
annual_return = ((1 + cumulative_return/100) ** (252/days) - 1) * 100
print(f"年化收益率：{annual_return:.2f}%")

bs.logout()
```

---

## 注意事项

### ⚠️ 重要提示

#### 1. 复权方式差异

**BaoStock vs 其他软件**:
- BaoStock 使用"涨跌幅复权法"
- 同花顺、通达信等可能使用其他方法
- **结果可能存在差异**，这是正常现象

**建议**:
- ✅ 在同一系统内保持一致
- ✅ 回测和实盘使用同一复权方式
- ✅ 不要混用不同系统的复权数据

#### 2. 停牌股票处理

```python
# 停牌时特征
# - open = high = low = close (都为前一日收盘价)
# - volume = 0
# - amount = 0
# - turn = None (空字符串)
# - tradestatus = 0

# 处理方法
result["turn"] = [0 if x == "" else float(x) for x in result["turn"]]
```

#### 3. 数据精度

| 字段 | 精度 | 单位 |
|------|------|------|
| open/high/low/close | 小数点后 4 位 | 元 |
| volume | 整数 | 股 |
| amount | 小数点后 4 位 | 元 |
| turn | 小数点后 6 位 | % |
| pctChg | 小数点后 6 位 | % |

#### 4. 日期格式

- **输入**: YYYY-MM-DD 或 YYYYMMDD
- **输出**: YYYY-MM-DD

```python
# 推荐格式
start_date = "2023-01-01"  # ✅
start_date = "20230101"    # ✅ 也可以

# 在项目中统一使用 YYYY-MM-DD
```

#### 5. 复权因子更新

- **日 K 线**: 交易日 18:00 更新
- **周 K 线**: 周六 17:30 更新
- **月 K 线**: 每月 1 号 17:30 更新

**建议**: 在交易日晚间获取最新复权数据

---

## 与其他软件对比

### 复权方法对比

| 软件/平台 | 复权方法 | 说明 |
|----------|---------|------|
| **BaoStock** | 涨跌幅复权法 | 确保资金运用率 100% |
| **同花顺** | 乘数复权法 | 使用复权因子连乘 |
| **通达信** | 除权除息复权 | 传统复权方法 |
| **东方财富** | 混合复权法 | 结合多种方法 |

### 数据差异示例

假设股票 600000 在 2023-06-30 实施 10 派 5 元（每股分红 0.5 元）：

| 日期 | 实际收盘价 | BaoStock 前复权 | 同花顺前复权 | 差异 |
|------|-----------|---------------|------------|------|
| 2023-06-29 | 10.50 | 9.98 | 9.97 | 0.01 |
| 2023-06-30 | 10.00 | 9.50 | 9.49 | 0.01 |
| 2023-07-03 | 10.20 | 9.70 | 9.70 | 0.00 |

**差异原因**:
- 复权因子计算方法不同
- 小数点精度处理不同
- 更新时点不同

### 使用建议

#### ✅ 推荐做法

1. **统一数据源**: 始终使用同一数据源
2. **统一复权方式**: 前后端使用相同复权类型
3. **定期验证**: 与其他软件对比验证数据准确性
4. **记录复权类型**: 在数据库中标记复权类型

#### ❌ 避免做法

1. **混用数据源**: BaoStock + 其他软件数据混用
2. **频繁切换复权**: 今天前复权，明天后复权
3. **忽略复权差异**: 直接对比不同系统数据

---

## 总结

### BaoStock 复权优势

1. ✅ **免费开放** - 无需付费即可使用
2. ✅ **方法科学** - 涨跌幅复权法适合收益计算
3. ✅ **数据完整** - 1990 年至今完整历史数据
4. ✅ **更新及时** - 交易日当晚更新

### 适用场景

| 场景 | 推荐复权 | 原因 |
|------|---------|------|
| 技术分析 | 前复权 | 与当前价格一致 |
| 策略回测 | 前复权 | 收益率计算准确 |
| 收益统计 | 后复权 | 反映真实收益 |
| 实盘交易 | 不复权 | 实际成交价格 |

### 最佳实践

```python
# 在 Quant 项目中的标准用法
from app.adapters import data_source_manager

# 1. 默认使用前复权
klines = await data_source_manager.get_kline(
    code="601398",
    adjust="qfq"  # 前复权（推荐）
)

# 2. 明确指定复权类型
klines = await data_source_manager.get_kline(
    code="601398",
    start_date="2020-01-01",
    end_date="2024-12-31",
    adjust="qfq"  # 始终使用前复权
)

# 3. 在数据库中标记
# kline_table: {code, date, open, high, low, close, adjust_type='qfq', ...}
```

---

## 相关资源

### 官方文档
- **BaoStock 官网**: http://www.baostock.com
- **复权因子简介**: http://baostock.com/baostock/index.php/复权因子简介
- **历史行情 API**: http://baostock.com/baostock/index.php/证券历史交易数据

### 项目文档
- [BaoStock 完整使用指南](file://m:\Project\Quant\backend\BAOSTOCK_COMPLETE_GUIDE.md)
- [多数据源智能路由](file://m:\Project\Quant\backend\MULTI_DATA_SOURCE_SMART_ROUTING.md)

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19  
**维护者**: Quant Team

**祝数据使用顺利！** 📊✨
