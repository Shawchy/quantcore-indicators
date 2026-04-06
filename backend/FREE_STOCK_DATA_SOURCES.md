# 免费股票数据源对比

## 主流免费数据源总览

| 数据源 | 稳定性 | 字段完整度 | 是否需要客户端 | 是否需要注册 | 备注 |
|--------|--------|-----------|--------------|------------|------|
| **Baostock** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ | ❌ | 最稳定，推荐 |
| **Tushare** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ❌ | ✅ | 需积分 |
| **Akshare** | ⭐⭐ | ⭐⭐⭐⭐ | ❌ | ❌ | 接口常失效 |
| **Yahoo Finance** | ⭐⭐⭐⭐ | ⭐⭐⭐ | ❌ | ❌ | 适合美股/港股 |
| **Sina** | ⭐⭐⭐ | ⭐⭐ | ❌ | ❌ | 仅实时行情 |
| **腾讯财经** | ⭐⭐⭐ | ⭐⭐ | ❌ | ❌ | 仅实时行情 |
| **东方财富** | ⭐⭐ | ⭐⭐⭐ | ❌ | ❌ | 反爬严重 |

---

## 详细对比

### 1. Baostock（推荐）⭐⭐⭐⭐⭐

**官网**: http://baostock.com/

**优点**：
- ✅ **完全免费**，无需注册
- ✅ **稳定性高**，不反爬
- ✅ **官方数据源**，数据准确
- ✅ **无需客户端**，纯 Python 库
- ✅ 提供证券类型、上市状态、上市/退市日期

**缺点**：
- ❌ 不提供行业、板块、地区信息
- ❌ 不提供实时行情
- ❌ 不提供财务数据
- ❌ 数据更新较慢（T+1）

**可用接口**：
```python
import baostock as bs

bs.login()

# 股票列表（含基本信息）
rs = bs.query_stock_basic()

# 历史 K 线
rs = bs.query_history_kline_plus(
    code="sh.600000",
    fields="date,open,high,low,close,volume",
    start_date="2024-01-01",
    end_date="2024-12-31"
)

# 指数成分股
rs = bs.query_hs300_stocks()  # 沪深 300
rs = bs.query_sz50_stocks()   # 上证 50
rs = bs.query_zz500_stocks()  # 中证 500

bs.logout()
```

**字段覆盖**：
- ✅ code, name, market
- ✅ type（证券类型）
- ✅ status（上市状态）
- ✅ list_date（上市日期）
- ✅ delist_date（退市日期）
- ❌ industry（行业）
- ❌ sector（板块）
- ❌ area（地区）
- ❌ total_shares（总股本）
- ❌ float_shares（流通股本）

**推荐指数**：⭐⭐⭐⭐⭐（基本信息首选）

---

### 2. Tushare（推荐）⭐⭐⭐⭐

**官网**: https://tushare.pro/

**优点**：
- ✅ **字段非常完整**
- ✅ **数据质量高**
- ✅ 提供行业、板块、地区、财务数据
- ✅ 提供实时行情和历史数据
- ✅ 文档完善

**缺点**：
- ❌ **需要注册**（获取 token）
- ❌ **需要积分**（部分接口收费）
- ❌ 免费额度有限（120 积分/天）
- ❌ 高级数据需要付费

**积分规则**：
- 注册送 120 积分
- 每日签到 +10 积分
- 资金门槛：入金 5000 元送 500 积分

**可用接口**：
```python
import tushare as ts

ts.set_token('your_token')
pro = ts.pro_api()

# 股票列表
df = pro.stock_basic(exchange='', list_status='L')

# 历史行情
df = pro.daily(ts_code='000001.SZ', start_date='20240101')

# 公司信息
df = pro.company_info(ts_code='000001.SZ')

# 财务数据
df = pro.fina_indicator(ts_code='000001.SZ')
```

**字段覆盖**：
- ✅ code, name, market
- ✅ type, status
- ✅ list_date, delist_date
- ✅ industry（行业）
- ✅ sector（板块）
- ✅ area（地区）
- ✅ total_shares（总股本）
- ✅ float_shares（流通股本）
- ✅ 财务数据

**推荐指数**：⭐⭐⭐⭐（字段最全，但有门槛）

---

### 3. Akshare ⭐⭐

**官网**: https://akshare.akfamily.xyz/

**优点**：
- ✅ **完全免费**，无需注册
- ✅ **接口丰富**（上千个接口）
- ✅ 支持全球市场
- ✅ 无需客户端

**缺点**：
- ❌ **稳定性差**（频繁反爬）
- ❌ **接口常失效**
- ❌ 数据质量参差不齐（第三方聚合）
- ❌ 文档混乱

**当前状态**（2026-04-05）：
- ❌ `stock_zh_a_spot_em()` - 失效（连接断开）
- ❌ `stock_individual_info_em()` - 失效（连接断开）
- ✅ `stock_zh_a_hist()` - 可用（历史 K 线）
- ✅ `stock_info_a_code_name()` - 可用（股票列表）

**可用接口**：
```python
import akshare as ak

# 股票列表（仅代码和名称）
df = ak.stock_info_a_code_name()

# 历史 K 线
df = ak.stock_zh_a_hist(symbol="000001", period="daily")

# 实时行情（已失效）
# df = ak.stock_zh_a_spot_em()  # ❌ 不可用
```

**字段覆盖**：
- ✅ code, name
- ❌ type, status
- ❌ list_date, delist_date
- ❌ industry, sector, area
- ❌ total_shares, float_shares

**推荐指数**：⭐⭐（不稳定，不推荐作为主力）

---

### 4. Yahoo Finance ⭐⭐⭐⭐

**官网**: https://finance.yahoo.com/

**优点**：
- ✅ **完全免费**，无需注册
- ✅ **稳定性高**
- ✅ 适合美股、港股数据
- ✅ Python 库成熟（yfinance）

**缺点**：
- ❌ A 股数据不完整
- ❌ 中文文档少
- ❌ 部分 A 股数据延迟

**可用接口**：
```python
import yfinance as yf

# 下载历史数据
stock = yf.Ticker("AAPL")
hist = stock.history(period="1y")

# 获取公司信息
info = stock.info

# A 股（数据有限）
stock_cn = yf.Ticker("600000.SS")  # 浦发银行
```

**字段覆盖**：
- ✅ code, name
- ✅ 历史 K 线
- ✅ 财务数据（美股）
- ❌ A 股基本信息不完整

**推荐指数**：⭐⭐⭐⭐（美股首选，A 股不适合）

---

### 5. Sina（新浪） ⭐⭐⭐

**数据源**：http://vip.stock.finance.sina.com.cn/

**优点**：
- ✅ **完全免费**
- ✅ **实时行情**
- ✅ 无需注册

**缺点**：
- ❌ 仅提供实时行情
- ❌ 无基本信息
- ❌ 接口老旧
- ❌ 数据格式混乱

**可用接口**：
```python
# 通过 akshare 调用
import akshare as ak

# 新浪实时行情
df = ak.stock_zh_a_spot()  # 批量获取

# 单个股票
df = ak.stock_sina_a_spot(symbol="sh600000")
```

**字段覆盖**：
- ✅ code, name
- ✅ 实时价格、涨跌幅
- ✅ 成交量、成交额
- ❌ 基本信息（type, status, list_date 等）
- ❌ 行业、板块

**推荐指数**：⭐⭐⭐（仅适合实时行情）

---

### 6. 腾讯财经 ⭐⭐⭐

**数据源**：http://qt.gtimg.cn/

**优点**：
- ✅ **完全免费**
- ✅ **实时行情**
- ✅ 无需注册

**缺点**：
- ❌ 仅提供实时行情
- ❌ 无基本信息
- ❌ 接口不正式

**可用接口**：
```python
# 通过 akshare 调用
import akshare as ak

# 腾讯实时行情
df = ak.stock_sina_a_spot(symbol="sh600000")
```

**推荐指数**：⭐⭐⭐（仅适合实时行情）

---

### 7. 东方财富 ⭐⭐

**数据源**：https://www.eastmoney.com/

**优点**：
- ✅ **完全免费**
- ✅ 字段较丰富
- ✅ 提供行业、板块信息

**缺点**：
- ❌ **反爬严重**
- ❌ **接口常失效**
- ❌ 数据质量一般

**当前状态**（2026-04-05）：
- ❌ `stock_zh_a_spot_em()` - 失效
- ❌ `stock_individual_info_em()` - 失效

**推荐指数**：⭐⭐（不稳定，不推荐）

---

## 综合对比表

| 数据源 | 基本信息 | 实时行情 | 历史 K 线 | 行业板块 | 财务数据 | 稳定性 | 推荐场景 |
|--------|---------|---------|---------|---------|---------|--------|---------|
| **Baostock** | ✅ | ❌ | ✅ | ❌ | ❌ | ⭐⭐⭐⭐⭐ | 基本信息同步 |
| **Tushare** | ✅ | ✅ | ✅ | ✅ | ✅ | ⭐⭐⭐⭐ | 完整数据（需积分） |
| **Akshare** | ⚠️ | ⚠️ | ✅ | ❌ | ❌ | ⭐⭐ | 备用数据源 |
| **Yahoo** | ⚠️ | ✅ | ✅ | ⚠️ | ✅ | ⭐⭐⭐⭐ | 美股/港股 |
| **Sina** | ❌ | ✅ | ❌ | ❌ | ❌ | ⭐⭐⭐ | 实时行情 |
| **腾讯** | ❌ | ✅ | ❌ | ❌ | ❌ | ⭐⭐⭐ | 实时行情 |
| **东方财富** | ⚠️ | ❌ | ✅ | ✅ | ✅ | ⭐⭐ | 备用 |

---

## 最佳实践建议

### 方案 1：完全免费组合（推荐）⭐⭐⭐⭐⭐

```
Baostock（主力） + Sina/腾讯（实时行情）
```

**配置**：
- **基本信息**：Baostock
- **实时行情**：Sina 或腾讯
- **历史 K 线**：Baostock

**优点**：
- ✅ 完全免费
- ✅ 无需注册
- ✅ 稳定性高
- ✅ 部署简单

**缺点**：
- ❌ 缺少行业、板块信息
- ❌ 缺少财务数据

**适用场景**：
- 个人学习/研究
- 量化策略回测
- 小型项目

---

### 方案 2：完整数据组合 ⭐⭐⭐⭐

```
Tushare（主力） + Baostock（备用）
```

**配置**：
- **基本信息**：Tushare（含行业、板块）
- **实时行情**：Tushare
- **历史 K 线**：Tushare + Baostock 备用
- **财务数据**：Tushare

**优点**：
- ✅ 字段最完整
- ✅ 数据质量高
- ✅ 有备用数据源

**缺点**：
- ❌ 需要注册
- ❌ 需要积分（有门槛）

**适用场景**：
- 专业量化研究
- 商业项目
- 需要完整数据的场景

---

### 方案 3：多数据源冗余 ⭐⭐⭐⭐

```
Baostock（主力） + Tushare（补充） + Sina（实时）
```

**配置**：
- **基本信息**：Baostock
- **行业板块**：Tushare（如果有积分）
- **实时行情**：Sina
- **历史 K 线**：Baostock + Tushare 双保险

**优点**：
- ✅ 数据冗余，提高可用性
- ✅ 不依赖单一数据源
- ✅ 字段较完整

**缺点**：
- ❌ 代码复杂度高
- ❌ 需要维护多个数据源

**适用场景**：
- 生产环境
- 对可用性要求高的场景

---

## 最终推荐

### 个人/学习用途

**推荐方案**：方案 1（完全免费）

```
Baostock（基本信息） + Sina（实时行情）
```

**理由**：
- 完全免费，无需注册
- 部署简单，开箱即用
- 稳定性高
- 满足基本需求

### 专业/商业用途

**推荐方案**：方案 2（Tushare 主力）

```
Tushare（完整数据） + Baostock（备用）
```

**理由**：
- 字段最完整
- 数据质量高
- 有官方支持
- 适合商业项目

### 当前项目推荐

**推荐方案**：

```
Baostock（主力） + xtquant（可选补充）
```

**理由**：
- Baostock 提供稳定的基本信息
- xtquant 补充行业、板块、地区信息（如果安装）
- 可选依赖，不强制
- 为未来实盘做准备

---

## 总结

### 最推荐的免费数据源

1. **Baostock** ⭐⭐⭐⭐⭐
   - 基本信息首选
   - 完全免费，稳定可靠

2. **Tushare** ⭐⭐⭐⭐
   - 完整数据首选
   - 需要积分，有门槛

3. **Sina/腾讯** ⭐⭐⭐
   - 实时行情补充
   - 免费，但字段有限

### 不推荐的数据源

1. **Akshare** ⭐⭐
   - 接口常失效
   - 稳定性差

2. **东方财富** ⭐⭐
   - 反爬严重
   - 接口不稳定

### 最佳实践

```
Baostock（主力） + Tushare（可选） + Sina（实时）
```

根据项目需求选择：
- 学习/研究：Baostock + Sina
- 商业项目：Tushare + Baostock
- 生产环境：多数据源冗余
