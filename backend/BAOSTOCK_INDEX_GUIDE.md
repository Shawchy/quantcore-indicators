# BaoStock 指数数据查询指南

**文档版本**: v1.0  
**更新日期**: 2026-03-19  
**主题**: 指数 K 线数据查询完整指南

---

## 📋 目录

1. [支持的指数类型](#支持的指数类型)
2. [数据范围说明](#数据范围说明)
3. [API 使用方法](#api 使用方法)
4. [使用示例](#使用示例)
5. [在 Quant 项目中的使用](#在 quant-项目中的使用)
6. [注意事项](#注意事项)

---

## 支持的指数类型

BaoStock 支持以下 10 类指数数据：

### 1. 综合指数

| 代码 | 名称 | 市场 |
|------|------|------|
| sh.000001 | 上证指数 | 上海 |
| sz.399106 | 深证综指 | 深圳 |
| sh.000002 | A 股指数 | 上海 |
| sh.000003 | B 股指数 | 上海 |

### 2. 规模指数

| 代码 | 名称 | 说明 |
|------|------|------|
| sh.000016 | 上证 50 | 上海市场规模最大的 50 只股票 |
| sh.000300 | 沪深 300 | 沪深两市市值最大的 300 只股票 |
| sh.000905 | 中证 500 | 扣除沪深 300 后的 500 只股票 |
| sz.399001 | 深证成指 | 深圳市场成分股指数 |
| sz.399005 | 中小板指 | 中小板指数 |
| sz.399006 | 创业板指 | 创业板指数 |

### 3. 一级行业指数

| 代码 | 名称 |
|------|------|
| sh.000037 | 上证医药 |
| sh.000038 | 上证金融 |
| sh.000039 | 上证材料 |
| sh.000040 | 上证能源 |
| sz.399433 | 国证交运 |
| sz.399434 | 国证金融 |

### 4. 二级行业指数

| 代码 | 名称 |
|------|------|
| sh.000952 | 300 地产 |
| sz.399951 | 300 银行 |
| sh.000953 | 300 非银 |
| sh.000954 | 300 化工 |

### 5. 策略指数

| 代码 | 名称 |
|------|------|
| sh.000050 | 50 等权 |
| sh.000982 | 500 等权 |
| sh.000030 | 180RWA |
| sh.000073 | 180 成长 |

### 6. 成长指数

| 代码 | 名称 |
|------|------|
| sz.399376 | 小盘成长 |
| sz.399372 | 大盘成长 |
| sh.000028 | 180 成长 |

### 7. 价值指数

| 代码 | 名称 |
|------|------|
| sh.000029 | 180 价值 |
| sh.000031 | 红利低波 |
| sz.399373 | 大盘价值 |

### 8. 主题指数

| 代码 | 名称 |
|------|------|
| sh.000015 | 红利指数 |
| sh.000063 | 上证周期 |
| sh.000064 | 非周期 |
| sh.000065 | 上证资源 |

### 9. 基金指数

| 代码 | 名称 |
|------|------|
| sh.000011 | 上证基金指数 |
| sz.399305 | 基金指数 |

### 10. 债券指数

| 代码 | 名称 |
|------|------|
| sh.000012 | 上证国债指数 |
| sh.000013 | 上证企债指数 |

---

## 数据范围说明

### 时间范围

| 数据类型 | 开始日期 | 说明 |
|---------|---------|------|
| 日 K 线 | 2006-01-01 | 所有指数 |
| 周 K 线 | 2006-01-01 | 所有指数 |
| 月 K 线 | 2006-01-01 | 所有指数 |
| 分钟线 | ❌ 不支持 | 指数无分钟数据 |

### 数据字段

**日线指标**:
```
date,code,open,high,low,close,preclose,volume,amount,pctChg
```

**周/月线指标**:
```
date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg
```

**字段说明**:

| 字段 | 类型 | 说明 | 精度 |
|------|------|------|------|
| date | String | 日期 | YYYY-MM-DD |
| code | String | 指数代码 | sh.xxxxxx |
| open | Double | 开盘价 | 4 位小数 |
| high | Double | 最高价 | 4 位小数 |
| low | Double | 最低价 | 4 位小数 |
| close | Double | 收盘价 | 4 位小数 |
| preclose | Double | 前收盘价 | 4 位小数 |
| volume | Long | 成交量 | 股 |
| amount | Double | 成交额 | 元 |
| pctChg | Double | 涨跌幅 | 6 位小数 |

**注意**: 指数数据**没有**以下字段：
- ❌ turn (换手率)
- ❌ tradestatus (交易状态)
- ❌ isST (是否 ST)
- ❌ peTTM, pbMRQ, psTTM, pcfNcfTTM (估值指标)

---

## API 使用方法

### 函数签名

```python
rs = bs.query_history_k_data_plus(
    security_code,    # 指数代码（必需）
    fields,           # 指标字段（必需）
    start_date='',    # 开始日期（可选）
    end_date='',      # 结束日期（可选）
    frequency='d',    # 频率（可选）
    adjustflag='3'    # 复权类型（固定为 3）
)
```

### 参数说明

| 参数 | 说明 | 是否必填 | 示例 |
|------|------|---------|------|
| **security_code** | 指数代码，格式 sh.xxxxxx 或 sz.xxxxxx | 是 | `sh.000001` |
| **fields** | 指标字段，逗号分隔 | 是 | `date,open,high,low,close` |
| **start_date** | 开始日期，YYYY-MM-DD | 否 | `2023-01-01` |
| **end_date** | 结束日期，YYYY-MM-DD | 否 | `2024-12-31` |
| **frequency** | 数据类型 | 否 | `d`=日，`w`=周，`m`=月 |
| **adjustflag** | 复权类型（指数固定为 3） | 否 | `3` |

### frequency 参数

| 值 | 说明 | 获取时间 |
|----|------|---------|
| `d` | 日 K 线 | 每日更新 |
| `w` | 周 K 线 | 每周五收盘后 |
| `m` | 月 K 线 | 每月最后一个交易日 |
| `5/15/30/60` | 分钟线 | ❌ 指数不支持 |

### adjustflag 参数

**指数数据固定使用 `adjustflag="3"`（不复权）**

原因：
- 指数是价格指数，不需要复权
- 指数成分股调整时，基期和基点会相应调整
- 指数本身已经保持了连续性

---

## 使用示例

### 示例 1：获取上证指数日线数据

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()
print('login respond error_code:'+lg.error_code)
print('login respond  error_msg:'+lg.error_msg)

# 获取上证指数 K 线数据
rs = bs.query_history_k_data_plus(
    "sh.000001",  # 上证指数
    "date,code,open,high,low,close,preclose,volume,amount,pctChg",
    start_date='2023-01-01',
    end_date='2023-12-31',
    frequency="d"
)
print('query_history_k_data_plus respond error_code:'+rs.error_code)
print('query_history_k_data_plus respond  error_msg:'+rs.error_msg)

# 转换为 DataFrame
data_list = []
while (rs.error_code == '0') & rs.next():
    data_list.append(rs.get_row_data())

result = pd.DataFrame(data_list, columns=rs.fields)

# 保存到 CSV
result.to_csv("shanghai_index_2023.csv", index=False, encoding='utf-8-sig')
print(f"共获取 {len(result)} 条数据")

# 登出
bs.logout()
```

### 示例 2：获取多个规模指数数据

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()

# 规模指数列表
indices = [
    ("sh.000016", "上证 50"),
    ("sh.000300", "沪深 300"),
    ("sh.000905", "中证 500"),
    ("sz.399001", "深证成指")
]

# 获取每个指数的数据
for code, name in indices:
    rs = bs.query_history_k_data_plus(
        code,
        "date,code,open,high,low,close,volume,amount,pctChg",
        start_date='2024-01-01',
        end_date='2024-12-31',
        frequency="d"
    )
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    df = pd.DataFrame(data_list, columns=rs.fields)
    df.to_csv(f"index_{name}.csv", index=False, encoding='utf-8-sig')
    print(f"{name}: {len(df)} 条数据")

bs.logout()
```

### 示例 3：获取行业指数周线数据

```python
import baostock as bs
import pandas as pd

lg = bs.login()

# 获取上证医药指数周线数据
rs = bs.query_history_k_data_plus(
    "sh.000037",  # 上证医药
    "date,code,open,high,low,close,volume,amount,pctChg",
    start_date='2023-01-01',
    end_date='2024-12-31',
    frequency="w"  # 周线
)

data_list = []
while (rs.error_code == '0') & rs.next():
    data_list.append(rs.get_row_data())

df = pd.DataFrame(data_list, columns=rs.fields)
print(f"上证医药周线数据：{len(df)} 条")
print(df.tail())

bs.logout()
```

### 示例 4：对比多个指数走势

```python
import baostock as bs
import pandas as pd
import matplotlib.pyplot as plt

lg = bs.login()

# 获取多个指数数据
indices_data = {}

for code, name in [("sh.000001", "上证指数"), 
                    ("sh.000300", "沪深 300"),
                    ("sh.000905", "中证 500")]:
    rs = bs.query_history_k_data_plus(
        code,
        "date,close",
        start_date='2023-01-01',
        end_date='2024-12-31',
        frequency="d"
    )
    
    data_list = []
    while (rs.error_code == '0') & rs.next():
        data_list.append(rs.get_row_data())
    
    df = pd.DataFrame(data_list, columns=rs.fields)
    df['close'] = df['close'].astype(float)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    # 归一化（以第一个交易日为基准）
    df['close'] = df['close'] / df['close'].iloc[0] * 1000
    indices_data[name] = df['close']

# 绘制对比图
plt.figure(figsize=(14, 7))
for name, series in indices_data.items():
    plt.plot(series.index, series.values, label=name, linewidth=2)

plt.title('主要指数走势对比（2023-2024）')
plt.xlabel('日期')
plt.ylabel('指数点位（归一化）')
plt.legend()
plt.grid(True)
plt.show()

bs.logout()
```

### 示例 5：计算指数收益率

```python
import baostock as bs
import pandas as pd

lg = bs.login()

# 获取沪深 300 数据
rs = bs.query_history_k_data_plus(
    "sh.000300",
    "date,close,pctChg",
    start_date='2023-01-01',
    end_date='2024-12-31',
    frequency="d"
)

data_list = []
while (rs.error_code == '0') & rs.next():
    data_list.append(rs.get_row_data())

df = pd.DataFrame(data_list, columns=rs.fields)
df['close'] = df['close'].astype(float)
df['pctChg'] = df['pctChg'].astype(float)

# 计算收益率
start_price = df['close'].iloc[0]
end_price = df['close'].iloc[-1]
total_return = (end_price / start_price - 1) * 100

print(f"沪深 300 区间收益率：{total_return:.2f}%")
print(f"最大单日涨幅：{df['pctChg'].max():.2f}%")
print(f"最大单日跌幅：{df['pctChg'].min():.2f}%")
print(f"上涨天数：{len(df[df['pctChg'] > 0])}天")
print(f"下跌天数：{len(df[df['pctChg'] < 0])}天")

bs.logout()
```

---

## 在 Quant 项目中的使用

### 通过 BaoStock 适配器

```python
from app.adapters.baostock_adapter import BaostockAdapter

# 初始化适配器
adapter = BaostockAdapter()
await adapter.initialize()

# 获取上证指数 K 线数据
index_klines = await adapter.get_index_kline(
    index_code="000001",  # 或 "sh.000001"
    start_date="2023-01-01",
    end_date="2024-12-31",
    frequency="d"
)

# 获取沪深 300 周线数据
index_klines = await adapter.get_index_kline(
    index_code="000300",
    frequency="w"
)

# 关闭连接
await adapter.close()
```

### 通过数据源管理器

```python
from app.adapters import data_source_manager

# 获取指数数据（如果适配器支持）
index_klines = await data_source_manager.get_index_kline(
    index_code="000001",
    source_type="baostock"  # 指定使用 BaoStock
)
```

### 在策略中的应用

```python
# 策略回测中使用指数作为基准
from app.services.backtest_service import BacktestService

service = BacktestService()

# 获取策略收益和基准收益
strategy_return = await service.calculate_strategy_return(...)
benchmark_return = await data_source_manager.get_index_kline(
    index_code="000300",  # 沪深 300 作为基准
    start_date="2023-01-01",
    end_date="2024-12-31"
)

# 计算超额收益
alpha = strategy_return - benchmark_return
```

---

## 注意事项

### ⚠️ 重要提示

#### 1. 指数没有分钟线数据

```python
# ❌ 错误：尝试获取指数分钟线
rs = bs.query_history_k_data_plus(
    "sh.000001",
    fields="...",
    frequency="5"  # 指数不支持！
)

# ✅ 正确：使用日线、周线或月线
rs = bs.query_history_k_data_plus(
    "sh.000001",
    fields="...",
    frequency="d"  # 日线
)
```

#### 2. 指数不需要复权

```python
# ✅ 正确：指数固定使用 adjustflag="3"
rs = bs.query_history_k_data_plus(
    "sh.000001",
    fields="...",
    adjustflag="3"  # 不复权
)

# ❌ 错误：指数不需要前复权或后复权
rs = bs.query_history_k_data_plus(
    "sh.000001",
    fields="...",
    adjustflag="2"  # 不需要！
)
```

#### 3. 指数没有换手率

```python
# ✅ 正确：不查询 turn 字段
rs = bs.query_history_k_data_plus(
    "sh.000001",
    "date,code,open,high,low,close,volume,amount,pctChg"
)

# ❌ 错误：指数没有 turn 字段
rs = bs.query_history_k_data_plus(
    "sh.000001",
    "date,code,open,high,low,close,turn"  # 会报错！
)
```

#### 4. 代码格式

```python
# ✅ 正确：使用完整代码格式
code = "sh.000001"  # 上证指数
code = "sz.399001"  # 深证成指

# ✅ 也可以：适配器会自动添加前缀
code = "000001"  # 自动转为 sh.000001
code = "399001"  # 自动转为 sz.399001
```

#### 5. 数据更新时间

| 数据类型 | 更新时间 |
|---------|---------|
| 日 K 线 | 交易日 17:30 |
| 周 K 线 | 周六 17:30 |
| 月 K 线 | 每月 1 号 17:30 |

**建议**: 在交易日晚间获取最新数据

#### 6. 数据范围

- **开始日期**: 2006-01-01
- **结束日期**: 最近一个交易日
- **默认开始**: 2015-01-01（如果不指定）

```python
# ✅ 正确：2006 年之后的数据
rs = bs.query_history_k_data_plus(
    "sh.000001",
    start_date="2006-01-01"
)

# ❌ 错误：2006 年之前无数据
rs = bs.query_history_k_data_plus(
    "sh.000001",
    start_date="2000-01-01"  # 会返回空结果
)
```

---

## 总结

### 指数数据特点

| 特点 | 说明 |
|------|------|
| **数据完整** | 2006 年至今完整历史数据 |
| **免费开放** | 无需注册，完全免费 |
| **类型丰富** | 10 大类指数，覆盖全面 |
| **更新及时** | 交易日当晚更新 |
| **无分钟线** | ❌ 不支持分钟级数据 |
| **无需复权** | 固定使用 adjustflag="3" |

### 推荐使用场景

| 场景 | 推荐指数 | 说明 |
|------|---------|------|
| **大盘分析** | sh.000001 上证指数 | 反映上海市场整体走势 |
| **基准对比** | sh.000300 沪深 300 | 市场基准，机构常用 |
| **风格分析** | sh.000016/000905 | 大盘/中小盘风格 |
| **行业研究** | 一级/二级行业指数 | 行业板块分析 |
| **策略回测** | sh.000300 沪深 300 | 作为业绩基准 |

### 最佳实践

```python
# 1. 使用前登录
lg = bs.login()
if lg.error_code != "0":
    print(f"登录失败：{lg.error_msg}")
    exit()

# 2. 明确指定字段
fields = "date,code,open,high,low,close,preclose,volume,amount,pctChg"

# 3. 指数固定使用 adjustflag="3"
rs = bs.query_history_k_data_plus(
    "sh.000001",
    fields=fields,
    adjustflag="3"
)

# 4. 使用完毕后登出
bs.logout()
```

---

## 相关资源

### 官方文档
- **BaoStock 官网**: http://www.baostock.com
- **历史行情 API**: http://baostock.com/baostock/index.php/证券历史交易数据
- **指数代码列表**: http://baostock.com/baostock/index.php/证券指数代码

### 项目文档
- [BaoStock 完整使用指南](file://m:\Project\Quant\backend\BAOSTOCK_COMPLETE_GUIDE.md)
- [BaoStock 复权数据详解](file://m:\Project\Quant\backend\BAOSTOCK_ADJUST_GUIDE.md)

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19  
**维护者**: Quant Team

**祝数据获取顺利！** 📊✨
