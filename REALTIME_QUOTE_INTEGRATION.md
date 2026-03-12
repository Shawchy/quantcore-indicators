# 实时盘口 TICK 快照接口集成报告

**完成时间**: 2026-03-12 20:30  
**接口**: realtime_quote  
**状态**: ✅ **测试成功，可以使用**

---

## 📊 **接口信息**

### 基本信息

- **接口名称**: realtime_quote
- **描述**: A 股实时行情数据（爬虫版）
- **所需权限**: **0 积分**（需要 Tushare 账号）✅
- **数据源**: 新浪财经 / 东方财富
- **更新频率**: 实时（交易时间内）
- **数据性质**: 爬虫数据，非官方

### 重要说明

⚠️ **免责声明**:
- 数据来自网络爬虫，不进入 Tushare 服务器
- Tushare 不对数据内容和质量负责
- 主要用于研究和学习使用
- 商业用途请自行解决合规问题

---

## ✅ **测试结果**

### 测试 1: 单只股票（新浪数据源）✅

**测试股票**: 平安银行 (000001.SZ)  
**结果**: 成功获取实时行情

**实时数据**:
```
股票：平安银行 (000001.SZ)
现价：¥10.94
涨跌：+0.05 (+0.46%) 📈
开盘：¥10.87
最高：¥10.96
最低：¥10.85
昨收：¥10.89
成交量：75,490,558 股
成交额：¥824,171,953.50 元
买一：¥10.94 × 4,784 手
卖一：¥10.95 × 998 手
时间：2026-03-12 15:00:00
```

---

### 测试 2: 多只股票批量获取（新浪）✅

**测试股票**: 浦发银行、平安银行、万科 A、中国平安、贵州茅台  
**结果**: 成功获取 5 只股票实时行情

**行情概览**:
```
📈 浦发银行 (600000.SH): ¥10.18 +1.09%
📈 平安银行 (000001.SZ): ¥10.94 +0.46%
📉 万 科 A (000002.SZ): ¥4.65 -0.43%
📉 中国平安 (601318.SH): ¥61.60 -1.52%
📉 贵州茅台 (600519.SH): ¥1392.00 -0.57%
```

**五档盘口数据**:
```
股票        价格     买一 (量)    卖一 (量)
浦发银行    10.18   ¥10.17×413   ¥10.18×1372
平安银行    10.94   ¥10.94×4784  ¥10.95×998
万 科 A     4.65    ¥4.65×19881  ¥4.66×23856
中国平安    61.60   ¥61.60×265   ¥61.61×5
贵州茅台    1392.00 ¥1392.00×53  ¥1392.48×2
```

---

### 测试 3: 东方财富数据源 ✅

**测试股票**: 浦发银行 (600000.SH)  
**结果**: 成功获取东财数据源实时行情

**五档盘口详情**:
```
卖五：¥10.22 × 5,112 手
卖四：¥10.21 × 5,631 手
卖三：¥10.20 × 22,808 手
卖二：¥10.19 × 9,081 手
卖一：¥10.18 × 1,372 手
-----
买一：¥10.17 × 413 手
买二：¥10.16 × 12,743 手
买三：¥10.15 × 2,006 手
买四：¥10.14 × 1,277 手
买五：¥10.13 × 938 手
```

---

### 测试 4: 上证指数 ✅

**指数代码**: 000001.SH  
**结果**: 成功获取上证指数实时行情

**指数数据**:
```
上证指数：4129.10 点
涨跌：-4.33 (-0.10%) 📉
今开：4133.20 点
最高：4141.65 点
最低：4103.16 点
昨收：4133.43 点
成交量：786,151,182 股
成交额：¥1,078,215,329,773.00 元
时间：2026-03-12 15:30:39
```

---

## 📁 **输出字段说明**

### 基础行情字段

| 字段 | 类型 | 描述 | 示例 |
|------|------|------|------|
| **name** | str | 股票名称 | 平安银行 |
| **ts_code** | str | 股票代码 | 000001.SZ |
| **date** | str | 交易日期 | 20260312 |
| **time** | str | 交易时间 | 15:00:00 |
| **open** | float | 开盘价 | 10.87 |
| **pre_close** | float | 昨收价 | 10.89 |
| **price** | float | 现价 | 10.94 |
| **high** | float | 最高价 | 10.96 |
| **low** | float | 最低价 | 10.85 |

### 涨跌字段

| 字段 | 类型 | 描述 | 计算方式 |
|------|------|------|---------|
| **bid** | float | 竞买价（买一） | - |
| **ask** | float | 竞卖价（卖一） | - |
| **volume** | int | 成交量 | 股（sina）/ 手（dc） |
| **amount** | float | 成交金额 | 元（CNY） |

### 五档盘口字段

| 字段 | 类型 | 描述 | 单位 |
|------|------|------|------|
| **b1_v/b1_p** | float | 买一（量/价） | 手 / 元 |
| **b2_v/b2_p** | float | 买二（量/价） | 手 / 元 |
| **b3_v/b3_p** | float | 买三（量/价） | 手 / 元 |
| **b4_v/b4_p** | float | 买四（量/价） | 手 / 元 |
| **b5_v/b5_p** | float | 买五（量/价） | 手 / 元 |
| **a1_v/a1_p** | float | 卖一（量/价） | 手 / 元 |
| **a2_v/a2_p** | float | 卖二（量/价） | 手 / 元 |
| **a3_v/a3_p** | float | 卖三（量/价） | 手 / 元 |
| **a4_v/a4_p** | float | 卖四（量/价） | 手 / 元 |
| **a5_v/a5_p** | float | 卖五（量/价） | 手 / 元 |

---

## 🎯 **使用示例**

### 示例 1: 获取单只股票实时行情

```python
import tushare as ts

# 设置 Token
ts.set_token('your_token')

# 获取平安银行实时行情（新浪数据源）
df = ts.realtime_quote(ts_code='000001.SZ', src='sina')

# 显示数据
print(df[['NAME', 'TS_CODE', 'PRICE', 'VOLUME', 'AMOUNT']])
```

### 示例 2: 批量获取多只股票

```python
# 同时获取最多 50 只股票（逗号分隔）
codes = '600000.SH,000001.SZ,000002.SZ,601318.SH,600519.SH'
df = ts.realtime_quote(ts_code=codes, src='sina')

# 计算涨跌幅
for idx, row in df.iterrows():
    change = row['PRICE'] - row['PRE_CLOSE']
    change_pct = change / row['PRE_CLOSE'] * 100
    print(f"{row['NAME']}: ¥{row['PRICE']:.2f} "
          f"{'+' if change > 0 else ''}{change:.2f} ({change_pct:.2f}%)")
```

### 示例 3: 使用东方财富数据源

```python
# 东财数据源只支持单只股票
df = ts.realtime_quote(ts_code='600000.SH', src='dc')

# 显示五档盘口
row = df.iloc[0]
print("五档卖盘:")
for i in range(5, 0, -1):
    print(f"  卖{i}: ¥{row[f'A{i}_P']:.2f} × {row[f'A{i}_V']:,.0f} 手")

print("五档买盘:")
for i in range(1, 6):
    print(f"  买{i}: ¥{row[f'B{i}_P']:.2f} × {row[f'B{i}_V']:,.0f} 手")
```

### 示例 4: 获取指数行情

```python
# 获取上证指数
df = ts.realtime_quote(ts_code='000001.SH', src='sina')

row = df.iloc[0]
print(f"上证指数：{row['PRICE']:.2f} 点")
print(f"涨跌：{row['PRICE'] - row['PRE_CLOSE']:.2f} "
      f"({(row['PRICE'] - row['PRE_CLOSE'])/row['PRE_CLOSE']*100:.2f}%)")
```

---

## 💡 **数据源对比**

| 特性 | 新浪 (sina) | 东方财富 (dc) |
|------|------------|-------------|
| **支持股票数** | 最多 50 只 | 仅 1 只 |
| **成交量单位** | 股 | 手 |
| **数据更新** | 实时 | 实时 |
| **盘口深度** | 五档 | 五档 |
| **适用场景** | 批量监控 | 个股深度分析 |

---

## 🔧 **集成到后端服务**

### 在 stock_service.py 中调用

```python
from app.adapters.factory import data_source_manager

async def get_realtime_quote(code: str):
    """
    获取实时行情
    
    Args:
        code: 股票代码（如：000001）
    
    Returns:
        dict: 实时行情数据
    """
    # 添加市场后缀
    if code.startswith('6'):
        ts_code = f"{code}.SH"
    else:
        ts_code = f"{code}.SZ"
    
    # 从数据源获取
    quote = await data_source_manager.get_realtime_quote(ts_code)
    
    return quote
```

### 在前端 Watchlist 中使用

```typescript
// 每 3 秒刷新一次自选股行情
useEffect(() => {
  const fetchQuotes = async () => {
    const codes = watchlist.map(stock => stock.code).join(',');
    const response = await fetch(`/api/v1/market/realtime?index_codes=${codes}`);
    const data = await response.json();
    setQuotes(data);
  };
  
  fetchQuotes();
  const interval = setInterval(fetchQuotes, 3000);
  return () => clearInterval(interval);
}, [watchlist]);
```

---

## 📊 **实战应用**

### 1. 实时行情监控

```python
import time

# 监控股票池
watchlist = '600000.SH,000001.SZ,000002.SZ'

while True:
    df = ts.realtime_quote(ts_code=watchlist, src='sina')
    
    print(f"\n{df['DATE'].iloc[0]} {df['TIME'].iloc[0]}")
    print("=" * 60)
    
    for idx, row in df.iterrows():
        change = row['PRICE'] - row['PRE_CLOSE']
        change_pct = change / row['PRE_CLOSE'] * 100
        print(f"{row['NAME']}: ¥{row['PRICE']:.2f} "
              f"{'+' if change > 0 else ''}{change:.2f} ({change_pct:.2f}%)")
    
    time.sleep(3)  # 3 秒刷新一次
```

### 2. 盘口分析

```python
def analyze_order_book(row):
    """分析买卖盘力量对比"""
    # 计算买盘总量
    buy_volume = sum([row[f'B{i}_V'] for i in range(1, 6)])
    # 计算卖盘总量
    sell_volume = sum([row[f'A{i}_V'] for i in range(1, 6)])
    
    # 买卖比
    ratio = buy_volume / sell_volume if sell_volume > 0 else 0
    
    if ratio > 1.5:
        return "买盘强势 📈"
    elif ratio < 0.67:
        return "卖盘强势 📉"
    else:
        return "多空平衡 ➖"

# 使用示例
df = ts.realtime_quote(ts_code='000001.SZ', src='sina')
analysis = analyze_order_book(df.iloc[0])
print(f"平安银行：{analysis}")
```

### 3. 异动预警

```python
def check_price_alert(ts_code, threshold=3.0):
    """价格异动检测"""
    df = ts.realtime_quote(ts_code=ts_code, src='sina')
    row = df.iloc[0]
    
    change_pct = abs((row['PRICE'] - row['PRE_CLOSE']) / row['PRE_CLOSE'] * 100)
    
    if change_pct > threshold:
        print(f"⚠️ {row['NAME']} 异动！涨跌幅：{change_pct:.2f}%")
        return True
    return False

# 监控多只股票
stocks = ['600000.SH', '000001.SZ', '000002.SZ']
for code in stocks:
    check_price_alert(code)
```

---

## ⚠️ **注意事项**

### 1. 数据单位

- **新浪数据源**: 成交量单位是"股"
- **东财数据源**: 成交量单位是"手"（1 手=100 股）

### 2. 使用限制

- **批量获取**: 新浪最多支持 50 只股票同时获取
- **东财限制**: 只支持单只股票
- **更新频率**: 建议不低于 3 秒刷新一次

### 3. 交易时间

- **早盘**: 9:30 - 11:30
- **午盘**: 13:00 - 15:00
- **休市时间**: 数据不更新

### 4. 合规说明

⚠️ **重要**:
- 数据仅用于研究和学习
- 不得用于商业用途
- 不得用于高频交易
- 请遵守相关法律法规

---

## 🎓 **最佳实践**

### 1. 错误处理

```python
try:
    df = ts.realtime_quote(ts_code='000001.SZ', src='sina')
    if df.empty:
        print("无数据返回")
    else:
        print(f"获取成功：{len(df)}条")
except Exception as e:
    print(f"获取失败：{e}")
```

### 2. 缓存策略

```python
from functools import lru_cache
import time

@lru_cache(maxsize=100)
def get_cached_quote(ts_code, timestamp):
    """带缓存的实时行情（5 秒有效期）"""
    return ts.realtime_quote(ts_code=ts_code, src='sina')

# 使用（5 秒内相同请求返回缓存）
current_time = int(time.time() / 5) * 5  # 5 秒取整
df = get_cached_quote('000001.SZ', current_time)
```

### 3. 批量优化

```python
# ✅ 推荐：批量获取
codes = '600000.SH,000001.SZ,000002.SZ'
df = ts.realtime_quote(ts_code=codes, src='sina')

# ❌ 不推荐：逐只获取（慢）
for code in codes.split(','):
    df = ts.realtime_quote(ts_code=code, src='sina')
```

---

## 📋 **验证清单**

### 功能测试

- [x] 单只股票实时行情获取
- [x] 多只股票批量获取
- [x] 新浪数据源测试
- [x] 东财数据源测试
- [x] 指数行情获取
- [x] 五档盘口数据获取

### 数据验证

- [x] 基础行情字段完整
- [x] 五档盘口数据准确
- [x] 成交量/成交额正确
- [x] 时间戳实时更新
- [x] 涨跌幅计算正确

---

## 🎉 **总结**

### 已完成

✅ **接口测试**: 4 个测试全部通过  
✅ **数据验证**: 字段完整，数据实时  
✅ **数据源对比**: 新浪和东财都已测试  
✅ **文档完善**: 详细使用说明已提供

### 优势

- ✅ **0 积分**: 无需积分即可使用
- ✅ **实时数据**: 交易时间内实时更新
- ✅ **五档盘口**: 完整的买卖盘数据
- ✅ **批量获取**: 支持最多 50 只股票
- ✅ **多数据源**: 新浪和东财可选

### 应用场景

- 📊 **实时行情监控**
- 📈 **自选股行情刷新**
- 🔔 **价格异动预警**
- 📉 **盘口力量分析**
- 💹 **量化交易信号**

---

**完成时间**: 2026-03-12 20:30  
**状态**: ✅ 完成  
**积分要求**: 0 分（需要账号）  
**测试状态**: 全部通过  
**数据文件**: `realtime_quote.csv`
