# A 股日线行情接口集成报告

**完成时间**: 2026-03-12 20:00  
**接口**: daily  
**状态**: ✅ **测试成功，可以使用**

---

## 📊 **接口信息**

### 基本信息

- **接口名称**: daily
- **描述**: 获取股票日线行情数据（未复权）
- **所需积分**: **120 分**（基础权限）✅
- **更新频率**: 交易日每天 15-16 点
- **数据范围**: 全部 A 股（主板、创业板、科创板）

### 调用限制

- **频次**: 500 次/分钟
- **数据量**: 6000 条/次
- **说明**: 一次请求可提取单只股票 23 年历史数据

---

## ✅ **测试结果**

### 测试 1: 单只股票日线数据

**测试股票**: 平安银行 (000001.SZ)  
**日期范围**: 最近 30 天  
**结果**: ✅ 成功获取 17 条数据

**数据样例**:
```
ts_code   trade_date   open   high    low  close  pre_close  change  pct_chg    vol       amount
000001.SZ 20260312    10.87  10.96  10.85  10.94    10.89     0.05   0.4591  754905.58  824171.954
000001.SZ 20260311    10.79  10.90  10.77  10.89    10.81     0.08   0.7401  720534.64  781041.009
```

**统计信息**:
- 最高价：11.10 元
- 最低价：10.67 元
- 平均成交量：735,671 手
- 平均成交额：799,178 千元

---

### 测试 2: 多只股票同时获取

**测试股票**: 000001.SZ, 600000.SH, 000002.SZ  
**日期范围**: 2024-03-01 到 2024-03-12  
**结果**: ✅ 成功获取 24 条数据（每只股票 8 条）

**数据样例**:
```
ts_code   trade_date   open   high    low  close  ...
600000.SH 20240312     7.11   7.15   7.08   7.10  ...
000001.SZ 20240312    10.48  10.59  10.41  10.56  ...
000002.SZ 20240312     9.40  10.20   9.36  10.00  ...
```

---

### 测试 3: 获取某一天全部股票

**测试日期**: 2024-03-11  
**结果**: ✅ 成功获取 5346 只股票数据

**市场表现**:
- 上涨：4484 只 (83.9%)
- 下跌：781 只 (14.6%)
- 平盘：81 只 (1.5%)

---

### 测试 4: query 方法

**方法**: `pro.query('daily', ...)`  
**结果**: ✅ 成功获取 8 条数据

**说明**: query 方法与 daily 方法功能相同，可按习惯选择使用

---

## 📁 **输出字段说明**

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| **ts_code** | str | 股票代码 | 000001.SZ |
| **trade_date** | str | 交易日期 (YYYYMMDD) | 20240312 |
| **open** | float | 开盘价 | 10.87 |
| **high** | float | 最高价 | 10.96 |
| **low** | float | 最低价 | 10.85 |
| **close** | float | 收盘价 | 10.94 |
| **pre_close** | float | 昨收价（除权价） | 10.89 |
| **change** | float | 涨跌额 | 0.05 |
| **pct_chg** | float | 涨跌幅 (%) | 0.4591 |
| **vol** | float | 成交量（手） | 754905.58 |
| **amount** | float | 成交额（千元） | 824171.954 |

---

## 🎯 **使用示例**

### 示例 1: 获取单只股票历史数据

```python
import tushare as ts

# 初始化
ts.set_token('your_token')
pro = ts.pro_api()

# 获取平安银行 2024 年 3 月数据
df = pro.daily(
    ts_code='000001.SZ',
    start_date='20240301',
    end_date='20240331'
)

print(df)
```

### 示例 2: 获取多只股票数据

```python
# 同时获取多只股票（逗号分隔）
df = pro.daily(
    ts_code='000001.SZ,600000.SH,000002.SZ',
    start_date='20240301',
    end_date='20240312'
)

# 按股票代码分组
for code in df['ts_code'].unique():
    stock_data = df[df['ts_code'] == code]
    print(f"{code}: {len(stock_data)} 条数据")
```

### 示例 3: 获取某一天全部股票

```python
# 获取 2024 年 3 月 11 日所有股票数据
df = pro.daily(trade_date='20240311')

print(f"共{len(df)}只股票")

# 统计涨跌
up = len(df[df['pct_chg'] > 0])
down = len(df[df['pct_chg'] < 0])
print(f"上涨：{up}只，下跌：{down}只")
```

### 示例 4: 使用 query 方法

```python
# query 方法与 daily 方法等价
df = pro.query('daily',
               ts_code='000001.SZ',
               start_date='20240301',
               end_date='20240312')
```

---

## 💾 **数据导入数据库**

### 批量导入脚本

**文件**: `batch_import_kline.py`

**功能**:
- ✅ 自动从 stock_info 表读取股票列表
- ✅ 批量获取最近 3 个月的 K 线数据
- ✅ 保存到 kline 表（adjust_type='none'）
- ✅ 自动去重和更新
- ✅ 显示进度和统计信息

**使用方法**:
```bash
cd D:\Project\Quant
python batch_import_kline.py
```

**导入字段映射**:
```python
trade_date → date
vol → volume
pct_chg → change_pct
```

---

## 📊 **数据字段映射**

### Tushare → 数据库

| Tushare 字段 | 数据库字段 | 说明 |
|-------------|-----------|------|
| ts_code | code | 股票代码 |
| trade_date | date | 交易日期 |
| open | open | 开盘价 |
| high | high | 最高价 |
| low | low | 最低价 |
| close | close | 收盘价 |
| vol | volume | 成交量 |
| amount | amount | 成交额 |
| pct_chg | change_pct | 涨跌幅 |

### 复权类型

- **none**: 未复权（daily 接口数据）
- **qfq**: 前复权（需要 pro_bar 接口 + 复权因子）
- **hfq**: 后复权（需要 pro_bar 接口 + 复权因子）

---

## 🔧 **集成到后端服务**

### 在 stock_service.py 中调用

```python
from app.adapters.factory import data_source_manager

async def get_daily_kline(code: str, start_date: str, end_date: str):
    """
    获取日线行情
    
    Args:
        code: 股票代码（如：000001）
        start_date: 开始日期（YYYYMMDD）
        end_date: 结束日期（YYYYMMDD）
    
    Returns:
        list: K 线数据列表
    """
    # 添加市场后缀
    if code.startswith('6'):
        ts_code = f"{code}.SH"
    else:
        ts_code = f"{code}.SZ"
    
    # 从数据源获取
    klines = await data_source_manager.get_kline(
        code=ts_code,
        start_date=start_date,
        end_date=end_date,
        adjust='none'
    )
    
    return klines
```

---

## 🎓 **最佳实践**

### 1. 批量获取优化

```python
# ✅ 推荐：一次获取多只股票
codes = '000001.SZ,600000.SH,000002.SZ'
df = pro.daily(ts_code=codes, start_date='20240301', end_date='20240312')

# ❌ 不推荐：逐只获取（慢）
for code in codes.split(','):
    df = pro.daily(ts_code=code, ...)
```

### 2. 日期范围控制

```python
# ✅ 推荐：控制数据量
df = pro.daily(ts_code='000001.SZ', start_date='20240101', end_date='20240312')

# ⚠️ 注意：数据量过大可能超时
# df = pro.daily(ts_code='000001.SZ', start_date='20000101', end_date='20240312')
```

### 3. 错误处理

```python
try:
    df = pro.daily(ts_code='000001.SZ', start_date='20240301', end_date='20240312')
    if df.empty:
        print("无数据")
    else:
        print(f"获取到{len(df)}条数据")
except Exception as e:
    print(f"获取失败：{e}")
```

### 4. 缓存策略

```python
# 使用内存缓存（TTL: 300 秒）
cache_key = f"daily_{ts_code}_{start_date}_{end_date}"
cached_data = cache.get(cache_key)

if cached_data:
    return cached_data
else:
    df = pro.daily(...)
    cache.set(cache_key, df, ttl=300)
    return df
```

---

## 📋 **验证清单**

### 数据验证

- [x] 单只股票数据获取成功
- [x] 多只股票数据获取成功
- [x] 全市场数据获取成功
- [x] query 方法测试成功
- [ ] 批量导入数据库
- [ ] 后端 API 集成
- [ ] 前端数据展示

### 字段验证

- [x] ts_code - 股票代码
- [x] trade_date - 交易日期
- [x] open/high/low/close - OHLC 价格
- [x] pre_close - 昨收价
- [x] change/pct_chg - 涨跌额和涨跌幅
- [x] vol/amount - 成交量和成交额

---

## 💡 **注意事项**

### 1. 数据更新频率

- **更新时间**: 交易日每天 15-16 点
- **休市日**: 不提供数据
- **停牌**: 停牌期间无数据

### 2. 复权说明

- **daily 接口**: 未复权行情
- **前复权**: 需要使用 `pro_bar` 接口 + 复权因子
- **后复权**: 需要使用 `pro_bar` 接口 + 复权因子

### 3. 涨跌幅计算

```
涨跌幅 = (今收 - 除权昨收) / 除权昨收 × 100%
```

基于除权后的昨收价计算，已考虑分红送股影响

### 4. 数据单位

- **价格**: 元
- **成交量**: 手（1 手=100 股）
- **成交额**: 千元

---

## 📞 **故障排查**

### 问题 1: 无数据返回

**可能原因**:
- 该股票已退市
- 日期范围内无交易（停牌）
- 日期不是交易日

**解决方法**:
- 检查股票代码是否正确
- 使用交易日历确认日期
- 尝试其他日期范围

### 问题 2: 请求失败

**可能原因**:
- Token 积分不足
- 超过频次限制
- 网络连接问题

**解决方法**:
- 检查 Token 和积分
- 降低请求频率
- 添加重试机制

---

## 🎉 **总结**

### 已完成

✅ **接口测试**: 4 个测试全部通过  
✅ **数据验证**: 字段完整，数据准确  
✅ **脚本创建**: 批量导入脚本已就绪  
✅ **文档完善**: 详细使用说明已提供

### 优势

- ✅ **积分要求低**: 只需 120 分（基础权限）
- ✅ **数据完整**: 包含所有必要字段
- ✅ **调用频次高**: 500 次/分钟
- ✅ **数据量大**: 6000 条/次
- ✅ **支持批量**: 可同时获取多只股票

### 下一步

1. **批量导入历史数据**: 运行 `batch_import_kline.py`
2. **集成后端 API**: 在 stock_service.py 中调用
3. **前端数据展示**: 测试 K 线图显示

---

**完成时间**: 2026-03-12 20:00  
**状态**: ✅ 完成  
**积分要求**: 120 分  
**测试状态**: 全部通过
