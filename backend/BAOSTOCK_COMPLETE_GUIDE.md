# BaoStock 证券宝 - 完整使用指南

**文档版本**: v1.0  
**更新日期**: 2026-03-19  
**数据源类型**: 免费、开源证券数据平台（无需注册）

---

## 📋 目录

1. [平台简介](#平台简介)
2. [安装与配置](#安装与配置)
3. [数据范围](#数据范围)
4. [数据更新时间](#数据更新时间)
5. [在 Quant 项目中的使用](#在 quant-项目中的使用)
6. [API 参考](#api-参考)
7. [数据格式说明](#数据格式说明)
8. [使用示例](#使用示例)
9. [注意事项](#注意事项)
10. [与其他数据源对比](#与其他数据源对比)

---

## 平台简介

### 什么是 BaoStock？

**证券宝（www.baostock.com）** 是一个**免费、开源**的证券数据平台，具有以下特点：

- ✅ **无需注册** - 直接使用，无门槛
- ✅ **完全免费** - 所有数据免费开放
- ✅ **开源项目** - 代码开源，社区维护
- ✅ **数据完整** - 提供大量准确、完整的证券数据
- ✅ **Python API** - 通过 Python 获取数据，适合量化交易

### 适用人群

- 📊 量化交易投资者
- 📈 数量金融爱好者
- 📉 计量经济从业者
- 💻 数据分析师

### 官方资源

- **官网**: [www.baostock.com](http://www.baostock.com)
- **PyPI**: [https://pypi.python.org/pypi/baostock](https://pypi.python.org/pypi/baostock)
- **GitHub**: 开源项目

---

## 安装与配置

### 方式 1：pip 安装（推荐）

```bash
# 使用默认源安装
pip install baostock

# 使用指定源安装（推荐，速度更快）
pip install baostock -i https://pypi.org/simple
```

### 方式 2：下载安装

```bash
# 访问 PyPI 下载安装包
# https://pypi.python.org/pypi/baostock

# 解压后安装
python setup.py install

# 或使用 wheel 安装
pip install xxx.whl
```

### 版本升级

```bash
# 升级到最新版本
pip install --upgrade baostock -i https://pypi.org/simple
```

### 环境要求

**必须安装**:
- ✅ Python 3.x
- ✅ pandas: `pip install pandas`

**推荐安装**:
- ✅ **Anaconda** - 包含 pandas、NumPy、Matplotlib 等 180+ 科学包
  - 下载地址：[https://www.anaconda.com/download/](https://www.anaconda.com/download/)
  - 避免依赖问题，推荐使用 Anaconda

### ⚠️ 重要注意事项

```
❌ 程序运行时，文件名、文件夹名不能是 baostock
   否则可能导致导入错误！
```

**正确示例**:
```python
✅ import baostock as bs  # 正确
```

**错误示例**:
```python
❌ # 文件名：baostock.py  # 错误！会与包名冲突
❌ # 文件夹名：baostock/  # 错误！
```

---

## 数据范围

### 📈 股票数据

| 数据类型 | 频率 | 时间范围 | 说明 |
|---------|------|---------|------|
| K 线数据 | 日 K | 1990-12-19 至今 | 包含开高低收、成交量、成交额 |
| K 线数据 | 周 K | 1990-12-19 至今 | 周线数据 |
| K 线数据 | 月 K | 1990-12-19 至今 | 月线数据 |
| K 线数据 | 5 分钟 | 2019-01-02 至今 | 近 5 年分钟数据 |
| K 线数据 | 15 分钟 | 2019-01-02 至今 | 近 5 年分钟数据 |
| K 线数据 | 30 分钟 | 2019-01-02 至今 | 近 5 年分钟数据 |
| K 线数据 | 60 分钟 | 2019-01-02 至今 | 近 5 年分钟数据 |

### 📊 ETF 数据

| 数据类型 | 频率 | 时间范围 | 说明 |
|---------|------|---------|------|
| ETF K 线 | 日 K | 2026-01-05 至今 | ETF 日线数据 |
| ETF K 线 | 周 K | 2026-01-05 至今 | ETF 周线数据 |
| ETF K 线 | 月 K | 2026-01-05 至今 | ETF 月线数据 |
| ETF K 线 | 5 分钟 | 2026-01-05 至今 | ETF 分钟数据 |
| ETF K 线 | 15 分钟 | 2026-01-05 至今 | ETF 分钟数据 |
| ETF K 线 | 30 分钟 | 2026-01-05 至今 | ETF 分钟数据 |
| ETF K 线 | 60 分钟 | 2026-01-05 至今 | ETF 分钟数据 |

### 📉 指数数据

**包含指数类型**:
- 综合指数
- 规模指数
- 一级行业指数
- 二级行业指数
- 策略指数
- 成长指数
- 价值指数
- 主题指数
- 基金指数
- 债券指数

| 数据类型 | 频率 | 时间范围 | 说明 |
|---------|------|---------|------|
| 指数 K 线 | 日 K | 2006-01-01 至今 | ❌ 不提供分钟 K 线 |
| 指数 K 线 | 周 K | 2006-01-01 至今 | ❌ 不提供分钟 K 线 |
| 指数 K 线 | 月 K | 2006-01-01 至今 | ❌ 不提供分钟 K 线 |

### 💰 财务数据（季频）

**已包含的财务数据**:
- ✅ 部分上市公司资产负债信息
- ✅ 上市公司现金流量信息
- ✅ 上市公司利润信息
- ✅ 上市公司杜邦指标信息

| 数据类型 | 时间范围 | 说明 |
|---------|---------|------|
| 财务数据 | 2007 年至今 | 季度报告 |

### 📄 公司报告（季频）

| 数据类型 | 时间范围 | 说明 |
|---------|---------|------|
| 业绩预告 | 2003 年至今 | 上市公司业绩预告 |
| 业绩快报 | 2006 年至今 | 上市公司业绩快报 |

---

## 数据更新时间

### 每日最新数据更新

| 数据类型 | 更新时间 | 说明 |
|---------|---------|------|
| 日 K 线数据 | 当前交易日 17:30 | 完成日 K 线数据入库 |
| 复权因子数据 | 当前交易日 18:00 | 完成复权因子数据入库 |
| 分钟 K 线数据 | 当前交易日 20:00 | 完成分钟 K 线数据入库 |
| 财务报告数据 | 第二自然日 1:30 | 前交易日"其它财务报告数据"入库 |
| 周 K 线数据 | 周六 17:30 | 完成周 K 线数据入库 |
| 月 K 线数据 | 每月 1 号 17:30 | 完成上月月 K 线数据入库 |

### 每周数据更新

| 数据类型 | 更新时间 | 说明 |
|---------|---------|------|
| 上证 50 成份股 | 每周一下午 | 完成上证 50 成份股信息数据入库 |
| 沪深 300 成份股 | 每周一下午 | 完成沪深 300 成份股信息数据入库 |
| 中证 500 成份股 | 每周一下午 | 完成中证 500 成份股信息数据入库 |

---

## 在 Quant 项目中的使用

### 项目中的实现

BaoStock 已作为**备用数据源**集成到 Quant 项目中，位于：

```
backend/app/adapters/baostock_adapter.py
```

### 数据源优先级

在项目中，BaoStock 的优先级配置：

```python
# backend/app/config.py
DATA_SOURCE_PRIORITY = ["tushare", "efinance", "akshare", "baostock"]
```

**优先级说明**:
1. **Tushare** - 主要数据源（需 Token）
2. **EFinance** - 第二数据源（免费）
3. **AkShare** - 第三数据源（免费）
4. **BaoStock** - 备用数据源（免费）

### 已实现的功能

✅ **已支持**:
- 获取股票列表 (`get_stock_list`)
- 获取股票信息 (`get_stock_info`)
- 获取日 K 线数据 (`get_kline`)
- 获取周 K 线数据 (`get_weekly_kline`)
- 获取月 K 线数据 (`get_monthly_kline`)
- 获取行业板块列表 (`get_sector_list`)
- 获取板块成分股 (`get_sector_components`)

❌ **暂不支持**:
- 实时行情数据
- 龙虎榜数据
- 资金流向数据
- 股东持股信息
- 财务业绩数据
- 指数成分股

### 使用示例

#### 1. 直接使用 BaoStock API

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()
if lg.error_code != "0":
    print(f"登录失败：{lg.error_msg}")

# 查询股票信息
rs = bs.query_stock_basic(code="sh.601398")
while (rs.error_code == "0") & rs.next():
    print(rs.get_row_data())

# 查询历史 K 线数据
rs = bs.query_history_k_data_plus(
    "sh.601398",
    "date,code,open,high,low,close,volume,amount,turn",
    start_date="2023-01-01",
    end_date="2023-12-31",
    frequency="d",
    adjustflag="2"  # 2=前复权
)

# 转换为 DataFrame
data_list = []
while (rs.error_code == "0") & rs.next():
    data_list.append(rs.get_row_data())

df = pd.DataFrame(data_list, columns=rs.fields)
print(df)

# 登出
bs.logout()
```

#### 2. 在项目中通过数据源管理器使用

```python
from app.adapters import data_source_manager

# 指定使用 BaoStock
adapter = data_source_manager.get_adapter("baostock")

# 获取股票信息
stock_info = await adapter.get_stock_info("601398")

# 获取 K 线数据
klines = await adapter.get_kline(
    code="601398",
    start_date="2023-01-01",
    end_date="2023-12-31",
    adjust="qfq"  # 前复权
)

# 自动故障转移：如果 BaoStock 失败，会自动尝试其他数据源
klines = await data_source_manager.get_kline(
    code="601398",
    source_type="baostock"  # 优先使用 BaoStock，失败则转移
)
```

#### 3. 临时切换数据源到 BaoStock

```python
# 通过 API 参数指定
from app.services.stock_service import StockService

service = StockService()

# 使用 BaoStock 获取数据（其他数据源失败时）
klines = await service.get_kline(
    code="601398",
    source_priority="baostock,akshare"  # 临时优先级
)
```

---

## API 参考

### 核心 API 函数

#### 1. 登录与登出

**login() - 登录系统**

```python
import baostock as bs

# 登录（无需账号密码）
lg = bs.login()

# 返回信息
print(f"错误代码：{lg.error_code}")  # "0" 表示成功，非 0 表示失败
print(f"错误信息：{lg.error_msg}")   # 详细的错误描述
```

**方法说明**:
- **功能**: 登录 BaoStock 系统
- **参数**: 无需参数（无需账号密码）
- **返回**: 包含 `error_code` 和 `error_msg` 的对象
- **error_code**: 
  - `"0"` - 登录成功
  - 非 `"0"` - 登录失败
- **error_msg**: 详细的错误信息

**logout() - 登出系统**

```python
# 登出
lg = bs.logout()

# 返回信息
print(f"错误代码：{lg.error_code}")  # "0" 表示成功，非 0 表示失败
print(f"错误信息：{lg.error_msg}")   # 详细的错误描述
```

**方法说明**:
- **功能**: 登出 BaoStock 系统，释放资源
- **参数**: 无需参数
- **返回**: 包含 `error_code` 和 `error_msg` 的对象
- **error_code**: 
  - `"0"` - 登出成功
  - 非 `"0"` - 登出失败
- **error_msg**: 详细的错误信息

**完整使用示例**:

```python
import baostock as bs

# 登录
lg = bs.login()
if lg.error_code != "0":
    print(f"登录失败：{lg.error_msg}")
    exit()
else:
    print("登录成功！")

# ... 执行数据查询操作 ...

# 登出（重要：使用完毕后必须登出）
lg = bs.logout()
if lg.error_code != "0":
    print(f"登出失败：{lg.error_msg}")
else:
    print("登出成功！")
```

**⚠️ 注意事项**:
1. **必须登录**: 所有数据查询操作前必须先登录
2. **必须登出**: 使用完毕后必须调用 `logout()` 释放资源
3. **无需账号**: BaoStock 无需注册，直接登录即可使用
4. **错误处理**: 建议检查 `error_code` 判断操作是否成功

#### 2. 股票基本信息查询

```python
# 查询股票基本信息
rs = bs.query_stock_basic(code="sh.601398")

# 查询所有股票
rs = bs.query_stock_basic()

# 查询行业板块
rs = bs.query_stock_industry()

# 查询板块成分股
rs = bs.query_stock_industry(industry="银行业")
```

#### 3. K 线数据查询

**query_history_k_data_plus() - 获取 A 股历史 K 线数据**

**方法说明**:
- **功能**: 通过 API 接口获取 A 股历史交易数据
- **支持**: 日 K 线、周 K 线、月 K 线，以及 5/15/30/60 分钟 K 线
- **用途**: 适合搭配均线数据进行选股和分析
- **返回类型**: pandas 的 DataFrame 类型
- **时间范围**: 1990-12-19 至当前时间
- **复权类型**: 支持不复权、前复权、后复权

**函数签名**:
```python
rs = bs.query_history_k_data_plus(
    code,              # 股票代码
    fields,            # 指标字段
    start_date='',     # 开始日期
    end_date='',       # 结束日期
    frequency='d',     # 频率
    adjustflag='3'     # 复权类型
)
```

**参数详解**:

| 参数 | 说明 | 是否必填 | 示例 |
|------|------|---------|------|
| **code** | 股票代码，sh 或 sz.+6 位数字代码，或指数代码 | 是 | `sh.601398`、`sz.000001` |
| **fields** | 指标字段，支持多指标，半角逗号分隔 | 是 | `date,code,open,high,low,close` |
| **start_date** | 开始日期（包含），格式"YYYY-MM-DD" | 否 | `2024-01-01` |
| **end_date** | 结束日期（包含），格式"YYYY-MM-DD" | 否 | `2024-12-31` |
| **frequency** | 数据类型 | 否 | `d`=日，`w`=周，`m`=月，`5/15/30/60`=分钟 |
| **adjustflag** | 复权类型 | 否 | `3`=不复权，`1`=后复权，`2`=前复权 |

**frequency 参数说明**:
- `d` - 日 K 线（默认）
- `w` - 周 K 线（每周最后一个交易日获取）
- `m` - 月 K 线（每月最后一个交易日获取）
- `5` - 5 分钟 K 线
- `15` - 15 分钟 K 线
- `30` - 30 分钟 K 线
- `60` - 60 分钟 K 线

**adjustflag 参数说明**:
- `3` - 不复权（默认）
- `1` - 后复权
- `2` - 前复权

**日线指标字段**:
```
date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST
```

**分钟线指标字段**:
```
date,time,code,open,high,low,close,volume,amount,adjustflag
```

**周月线指标字段**:
```
date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg
```

**日线使用示例**:

```python
import baostock as bs
import pandas as pd

#### 登陆系统 ####
lg = bs.login()
# 显示登陆返回信息
print('login respond error_code:'+lg.error_code)
print('login respond  error_msg:'+lg.error_msg)

#### 获取沪深 A 股历史 K 线数据 ####
# 详细指标参数，参见"历史行情指标参数"章节
# "分钟线"参数与"日线"参数不同。"分钟线"不包含指数。
# 分钟线指标：date,time,code,open,high,low,close,volume,amount,adjustflag
# 周月线指标：date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg
rs = bs.query_history_k_data_plus("sh.600000", 
    "date,code,open,high,low,close,preclose,volume,amount,adjustflag,turn,tradestatus,pctChg,isST", 
    start_date='2024-07-01', end_date='2024-12-31', 
    frequency="d", adjustflag="3")
print('query_history_k_data_plus respond error_code:'+rs.error_code)
print('query_history_k_data_plus respond  error_msg:'+rs.error_msg)

#### 打印结果集 ####
data_list = []
while (rs.error_code == '0') & rs.next():
    # 获取一条记录，将记录合并在一起
    data_list.append(rs.get_row_data())
result = pd.DataFrame(data_list, columns=rs.fields)

#### 结果集输出到 csv 文件 ####   
result.to_csv("D:\\history_A_stock_k_data.csv", index=False)
print(result)

#### 登出系统 ####
bs.logout()
```

**分钟线使用示例**:

```python
import baostock as bs
import pandas as pd

#### 登陆系统 ####
lg = bs.login()
# 显示登陆返回信息
print('login respond error_code:'+lg.error_code)
print('login respond  error_msg:'+lg.error_msg)

#### 获取沪深 A 股历史 K 线数据 ####
# 详细指标参数，参见"历史行情指标参数"章节
# "分钟线"参数与"日线"参数不同。"分钟线"不包含指数。
# 分钟线指标：date,time,code,open,high,low,close,volume,amount,adjustflag
# 周月线指标：date,code,open,high,low,close,volume,amount,adjustflag,turn,pctChg
rs = bs.query_history_k_data_plus("sh.600000", 
    "date,time,code,open,high,low,close,volume,amount,adjustflag", 
    start_date='2024-07-01', end_date='2024-12-31', 
    frequency="5", adjustflag="3")
print('query_history_k_data_plus respond error_code:'+rs.error_code)
print('query_history_k_data_plus respond  error_msg:'+rs.error_msg)

#### 打印结果集 ####
data_list = []
while (rs.error_code == '0') & rs.next():
    # 获取一条记录，将记录合并在一起
    data_list.append(rs.get_row_data())
result = pd.DataFrame(data_list, columns=rs.fields)

#### 结果集输出到 csv 文件 ####   
result.to_csv("D:\\history_A_stock_k_data.csv", index=False)
print(result)

#### 登出系统 ####
bs.logout()
```

**⚠️ 注意事项**:

1. **停牌股票处理**:
   - 股票停牌时，对于日线，开、高、低、收价都相同
   - 都都为前一交易日的收盘价
   - 成交量、成交额为 0
   - 换手率为空

2. **换手率类型转换**:
   ```python
   # 如果需要将换手率转为 float 类型，可使用如下方法转换：
   result["turn"] = [0 if x == "" else float(x) for x in result["turn"]]
   ```

3. **分钟线限制**:
   - 分钟线不包含指数数据
   - 分钟线时间范围：近 5 年（2019-01-02 至今）

4. **周月线获取时间**:
   - 周线：每周最后一个交易日才可以获取
   - 月线：每月最后一个交易日才可以获取

#### 4. 指数数据查询

**query_history_k_data_plus() - 获取指数 K 线数据**

**支持的指数类型**:

| 类型 | 示例代码 | 名称 |
|------|---------|------|
| **综合指数** | sh.000001 | 上证指数 |
| | sz.399106 | 深证综指 |
| **规模指数** | sh.000016 | 上证 50 |
| | sh.000300 | 沪深 300 |
| | sh.000905 | 中证 500 |
| | sz.399001 | 深证成指 |
| **一级行业指数** | sh.000037 | 上证医药 |
| | sz.399433 | 国证交运 |
| **二级行业指数** | sh.000952 | 300 地产 |
| | sz.399951 | 300 银行 |
| **策略指数** | sh.000050 | 50 等权 |
| | sh.000982 | 500 等权 |
| **成长指数** | sz.399376 | 小盘成长 |
| **价值指数** | sh.000029 | 180 价值 |
| **主题指数** | sh.000015 | 红利指数 |
| | sh.000063 | 上证周期 |
| **基金指数** | sh.000011 | 上证基金指数 |
| **债券指数** | sh.000012 | 上证国债指数 |

**特点**:
- ❌ **指数没有分钟线数据**
- ✅ **时间范围**: 2006-01-01 至今
- ✅ **不需要复权** (adjustflag 固定为 3)
- ✅ **日线指标**: date,code,open,high,low,close,preclose,volume,amount,pctChg

**使用示例**:

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
    start_date='2017-01-01',
    end_date='2017-06-30',
    frequency="d"  # 日线
)
print('query_history_k_data_plus respond error_code:'+rs.error_code)
print('query_history_k_data_plus respond  error_msg:'+rs.error_msg)

# 转换为 DataFrame
data_list = []
while (rs.error_code == '0') & rs.next():
    data_list.append(rs.get_row_data())

result = pd.DataFrame(data_list, columns=rs.fields)

# 保存到 CSV
result.to_csv("D:\\history_Index_k_data.csv", index=False)
print(result)

# 登出
bs.logout()
```

**返回数据说明**:

| 字段 | 说明 | 精度 |
|------|------|------|
| date | 交易所日期 | YYYY-MM-DD |
| code | 证券代码 | sh.xxxxxx |
| open | 开盘价 | 小数点后 4 位 |
| high | 最高价 | 小数点后 4 位 |
| low | 最低价 | 小数点后 4 位 |
| close | 收盘价 | 小数点后 4 位 |
| preclose | 前收盘价 | 小数点后 4 位 |
| volume | 成交量 | 股 |
| amount | 成交额 | 元 |
| pctChg | 涨跌幅 | 小数点后 6 位 |

**注意**: 指数数据**没有换手率 **(turn)字段

#### 5. 估值指标查询（日频）

**query_history_k_data_plus() - 获取沪深 A 股估值指标**

**支持的估值指标**:

| 指标 | 名称 | 计算公式 | 说明 |
|------|------|---------|------|
| **peTTM** | 滚动市盈率 | 收盘价/每股盈余 TTM | 最常用的估值指标 |
| **psTTM** | 滚动市销率 | 收盘价/每股销售额 TTM | 适合未盈利企业 |
| **pcfNcfTTM** | 滚动市现率 | 收盘价/每股现金流 TTM | 现金流估值 |
| **pbMRQ** | 市净率 | 收盘价/每股净资产 | 适合重资产企业 |

**特点**:
- ✅ **日频数据** - 每日更新
- ❌ **不支持周/月线** - 仅有日线数据
- ❌ **指数无估值** - 仅支持个股
- ✅ **数据范围**: 2006-01-01 至今

**使用示例**:

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
    start_date='2015-01-01',
    end_date='2017-12-31',
    frequency="d",
    adjustflag="3"  # 不复权
)
print('query_history_k_data_plus respond error_code:'+rs.error_code)
print('query_history_k_data_plus respond  error_msg:'+rs.error_msg)

# 转换为 DataFrame
result_list = []
while (rs.error_code == '0') & rs.next():
    result_list.append(rs.get_row_data())

result = pd.DataFrame(result_list, columns=rs.fields)

# 保存到 CSV
result.to_csv("valuation_indicators.csv", encoding="gbk", index=False)
print(result)

# 登出
bs.logout()
```

**返回数据说明**:

| 字段 | 说明 | 精度 |
|------|------|------|
| date | 交易所日期 | YYYY-MM-DD |
| code | 证券代码 | sh.xxxxxx |
| close | 收盘价 | 小数点后 4 位 |
| peTTM | 滚动市盈率 | 小数点后 4 位 |
| psTTM | 滚动市销率 | 小数点后 4 位 |
| pcfNcfTTM | 滚动市现率 | 小数点后 4 位 |
| pbMRQ | 市净率 | 小数点后 4 位 |

**估值指标解读**:

| 指标 | 低估值 | 合理估值 | 高估值 |
|------|-------|---------|-------|
| **peTTM** | < 15 | 15-25 | > 25 |
| **pbMRQ** | < 1.5 | 1.5-3 | > 3 |
| **psTTM** | < 3 | 3-8 | > 8 |
| **pcfNcfTTM** | < 10 | 10-20 | > 20 |

**注意**: 
- 不同行业估值水平差异较大，应横向对比
- 周期股、成长股、价值股适用不同指标
- 负值表示企业亏损或现金流为负

```python
# 查询 ETF K 线
rs = bs.query_history_k_data_plus(
    security_code="sh.510050",  # 上证 50ETF
    fields="date,code,open,high,low,close,volume,amount",
    start_date="2023-01-01",
    end_date="2023-12-31",
    frequency="d",
    adjustflag="2"
)
```

---

## 数据格式说明

### K 线数据字段

| 字段名 | 类型 | 说明 |
|-------|------|------|
| date | String | 日期 YYYYMMDD |
| code | String | 证券代码 |
| open | Double | 开盘价 |
| high | Double | 最高价 |
| low | Double | 最低价 |
| close | Double | 收盘价 |
| volume | Long | 成交量（手） |
| amount | Double | 成交额（元） |
| turn | Double | 换手率（%） |

### 股票基本信息字段

| 字段名 | 类型 | 说明 |
|-------|------|------|
| code | String | 证券代码 |
| code_name | String | 证券名称 |
| ipoDate | String | 上市日期 |
| outDate | String | 退市日期 |
| status | String | 状态 |
| maxNonHRStock | Long | 最大非流通股份 |
| totalShares | Long | 总股本 |
| industry | String | 所属行业 |

### 返回值格式

所有 API 返回都是 **pandas DataFrame** 类型：

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()

# 查询数据
rs = bs.query_history_k_data_plus("sh.601398", "date,code,open,high,low,close", 
                                   start_date="20230101", end_date="20231231", 
                                   frequency="d", adjustflag="2")

# 转换为 DataFrame
data_list = []
while (rs.error_code == "0") & rs.next():
    data_list.append(rs.get_row_data())

df = pd.DataFrame(data_list, columns=rs.fields)

# 使用 pandas 进行分析
print(df.describe())
print(df.tail())

# 使用 matplotlib 可视化
import matplotlib.pyplot as plt
plt.figure(figsize=(12, 6))
plt.plot(df['date'], df['close'])
plt.title('601398 收盘价走势')
plt.xlabel('日期')
plt.ylabel('收盘价')
plt.grid(True)
plt.show()

# 登出
bs.logout()
```

---

## 使用示例

### 示例 1：获取股票列表并保存

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()

# 查询股票信息
rs = bs.query_stock_basic()
print(f"响应错误码：{rs.error_code}")

# 获取数据
data_list = []
while (rs.error_code == "0") & rs.next():
    data_list.append(rs.get_row_data())

# 转换为 DataFrame
df = pd.DataFrame(data_list, columns=rs.fields)

# 筛选 A 股
a_shares = df[df['code'].str.startswith('sh.') | df['code'].str.startswith('sz.')]

# 保存到 CSV
a_shares.to_csv("stock_list.csv", index=False, encoding='utf-8-sig')
print(f"共获取 {len(a_shares)} 只股票信息")

# 登出
bs.logout()
```

### 示例 2：获取多只股票的 K 线数据

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()

# 股票列表
stock_codes = ["sh.601398", "sz.000001", "sh.600519"]

# 获取每只股票的 K 线数据
for code in stock_codes:
    rs = bs.query_history_k_data_plus(
        code,
        "date,code,open,high,low,close,volume",
        start_date="2023-01-01",
        end_date="2023-12-31",
        frequency="d",
        adjustflag="2"
    )
    
    # 转换为 DataFrame
    data_list = []
    while (rs.error_code == "0") & rs.next():
        data_list.append(rs.get_row_data())
    
    df = pd.DataFrame(data_list, columns=rs.fields)
    
    # 保存
    short_code = code.split(".")[1]
    df.to_csv(f"kline_{short_code}_2023.csv", index=False, encoding='utf-8-sig')
    print(f"{short_code} 共获取 {len(df)} 条数据")

# 登出
bs.logout()
```

### 示例 3：获取行业板块数据

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()

# 查询行业板块
rs = bs.query_stock_industry()
industries = set()

while (rs.error_code == "0") & rs.next():
    industry = rs.get_data("industry")
    industries.add(industry)

print(f"共 {len(industries)} 个行业:")
for ind in sorted(industries):
    print(f"  - {ind}")

# 查询某个行业的成分股
rs = bs.query_stock_industry(industry="银行业")
banks = []

while (rs.error_code == "0") & rs.next():
    code = rs.get_data("code")
    code_name = rs.get_data("code_name")
    banks.append((code, code_name))

print(f"\n银行业共 {len(banks)} 家上市公司:")
for code, name in banks[:10]:  # 显示前 10 个
    print(f"  {code}: {name}")

# 登出
bs.logout()
```

### 示例 4：获取 ETF 数据

```python
import baostock as bs
import pandas as pd

# 登录
lg = bs.login()

# ETF 代码列表
etf_codes = [
    "sh.510050",  # 上证 50ETF
    "sh.510300",  # 沪深 300ETF
    "sz.159915"   # 创业板 ETF
]

for code in etf_codes:
    rs = bs.query_history_k_data_plus(
        code,
        "date,code,open,high,low,close,volume,amount",
        start_date="2023-01-01",
        end_date="2023-12-31",
        frequency="d",
        adjustflag="2"
    )
    
    data_list = []
    while (rs.error_code == "0") & rs.next():
        data_list.append(rs.get_row_data())
    
    df = pd.DataFrame(data_list, columns=rs.fields)
    short_code = code.split(".")[1]
    
    print(f"{short_code}: {len(df)} 条数据")
    print(f"最新收盘价：{df.iloc[-1]['close']}")

# 登出
bs.logout()
```

---

## 注意事项

### ⚠️ 常见错误与解决方案

#### 1. 导入错误

```python
# ❌ 错误：文件名或文件夹名为 baostock
# 解决方案：重命名文件或文件夹
```

#### 2. 登录失败

```python
lg = bs.login()
if lg.error_code != "0":
    print(f"错误：{lg.error_msg}")
    
# 可能原因：
# - 网络连接问题
# - BaoStock 服务器维护
# - 解决方案：检查网络，稍后重试
```

#### 3. 数据为空

```python
rs = bs.query_history_k_data_plus(...)
if rs.rowcount == 0:
    print("未查询到数据")
    
# 可能原因：
# - 股票代码错误
# - 日期范围无数据
# - 解决方案：检查代码和日期范围
```

#### 4. 分钟 K 线数据限制

```python
# 分钟 K 线只有近 5 年数据（2019-01-02 至今）
# 查询更早数据会返回空
rs = bs.query_history_k_data_plus(
    "sh.601398",
    fields="...",
    start_date="2015-01-01",  # ❌ 太早，无数据
    frequency="5"
)
```

### 📝 最佳实践

#### 1. 错误处理

```python
import baostock as bs
from loguru import logger

def safe_query(func, *args, **kwargs):
    """安全的查询函数"""
    try:
        result = func(*args, **kwargs)
        if result.error_code == "0":
            return result
        else:
            logger.error(f"BaoStock 错误：{result.error_msg}")
            return None
    except Exception as e:
        logger.error(f"查询异常：{e}")
        return None
```

#### 2. 数据缓存

```python
import pickle
from datetime import datetime, timedelta

def get_cached_data(code, days=1):
    """获取缓存数据"""
    cache_file = f"cache_{code}.pkl"
    
    try:
        with open(cache_file, 'rb') as f:
            data, timestamp = pickle.load(f)
            if datetime.now() - timestamp < timedelta(days=days):
                return data
    except:
        pass
    
    # 从 BaoStock 获取新数据
    data = query_from_baostock(code)
    
    # 保存缓存
    with open(cache_file, 'wb') as f:
        pickle.dump((data, datetime.now()), f)
    
    return data
```

#### 3. 批量查询限流

```python
import time

def batch_query_codes(codes, delay=0.5):
    """批量查询，避免过快"""
    results = []
    for code in codes:
        result = query_code(code)
        results.append(result)
        time.sleep(delay)  # 避免请求过快
    return results
```

---

## 与其他数据源对比

### 数据源特性对比

| 特性 | BaoStock | Tushare | EFinance | AkShare |
|------|----------|---------|----------|---------|
| **费用** | 完全免费 | 积分制 | 完全免费 | 完全免费 |
| **注册** | 无需注册 | 需要注册 | 无需注册 | 无需注册 |
| **开源** | ✅ 开源 | ❌ 闭源 | ❌ 闭源 | ✅ 开源 |
| **数据完整性** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **更新速度** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **API 友好度** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **分钟 K 线** | ✅ 近 5 年 | ✅ 需积分 | ✅ | ✅ |
| **财务数据** | ✅ 季频 | ✅ 需积分 | ✅ | ✅ |
| **实时行情** | ❌ | ✅ 需积分 | ✅ | ✅ |
| **资金流向** | ❌ | ✅ 需积分 | ✅ | ✅ |

### 在项目中作为数据源的定位

#### BaoStock 的优势
- ✅ **完全免费** - 无任何费用，无需积分
- ✅ **无需注册** - 直接使用，无门槛
- ✅ **数据稳定** - 历史悠久，数据完整
- ✅ **适合离线分析** - 可批量下载历史数据

#### BaoStock 的劣势
- ❌ **无实时数据** - 不支持实时行情
- ❌ **无资金流向** - 不支持资金流数据
- ❌ **无龙虎榜** - 不支持特色数据
- ❌ **更新较慢** - 相比 Tushare 更新稍慢

#### 推荐使用场景

**使用 BaoStock**:
- 📊 历史 K 线数据分析
- 📈 回测策略（需要大量历史数据）
- 💰 财务数据分析
- 📉 行业板块分析
- 🎯 作为备用数据源

**使用其他数据源**:
- ⚡ 需要实时行情
- 💹 需要资金流向数据
- 🐉 需要龙虎榜数据
- 📊 需要更全面的财务数据

### 项目中的数据源配置建议

```python
# backend/app/config.py

# 推荐配置（兼顾速度和稳定性）
DATA_SOURCE_PRIORITY = [
    "tushare",      # 主要数据源（如果有 Token）
    "efinance",     # 第二数据源（免费，数据全）
    "akshare",      # 第三数据源（免费，开源）
    "baostock"      # 备用数据源（免费，稳定）
]

# 如果无 Tushare Token，推荐配置
DATA_SOURCE_PRIORITY = [
    "efinance",     # 主要数据源
    "akshare",      # 第二数据源
    "baostock"      # 备用数据源
]
```

---

## 总结

### BaoStock 核心价值

1. **🆓 完全免费** - 无任何使用门槛
2. **📚 数据完整** - 覆盖股票、ETF、指数、财务数据
3. **🐍 Python 友好** - pandas DataFrame 格式，易于分析
4. **🔧 易于集成** - 简单 API，快速上手
5. **💾 适合离线** - 可批量下载历史数据

### 在 Quant 项目中的定位

- **主要用途**: 备用数据源，提供历史 K 线数据
- **优先级**: 第 4 优先级（在 Tushare/EFinance/AkShare 之后）
- **适用场景**: 其他数据源失败时的保底选择

### 推荐使用策略

```python
# 日常使用：优先使用 EFinance 或 Tushare
klines = await service.get_kline(code="601398")

# 历史数据回测：可以使用 BaoStock（免费、完整）
klines = await service.get_kline(
    code="601398",
    source_priority="baostock"  # 指定使用 BaoStock
)

# 其他数据源失败：自动故障转移到 BaoStock
klines = await service.get_kline(
    code="601398",
    fallback=True  # 允许故障转移
)
```

---

## 相关资源

### 官方链接
- **官网**: http://www.baostock.com
- **PyPI**: https://pypi.python.org/pypi/baostock
- **文档**: http://baostock.com/baostock/index.html

### 项目文档
- [多数据源智能路由](file://m:\Project\Quant\backend\MULTI_DATA_SOURCE_SMART_ROUTING.md)
- [数据获取策略](file://m:\Project\Quant\backend\DATA_FETCHING_STRATEGIES.md)
- [Tushare 使用指南](file://m:\Project\Quant\backend\TUSHARE_SETUP.md)
- [EFinance 集成文档](file://m:\Project\Quant\backend\EFINANCE_IMPLEMENTATION_SUMMARY.md)

---

**文档版本**: v1.0  
**最后更新**: 2026-03-19  
**维护者**: Quant Team

**祝数据获取顺利！** 📊🚀
