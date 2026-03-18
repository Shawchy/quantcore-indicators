# efinance 实时行情快照 API 优化指南

## 📊 优化内容

已优化 `get_realtime_quote` 接口，使用 `efinance.stock.get_quote_snapshot` 获取更详细的股票行情快照数据。

### 新增字段

优化后的接口返回包含以下完整字段：

#### 1. **基本信息**
- `code` - 股票代码
- `name` - 股票名称

#### 2. **价格信息**
- `price` - 最新价
- `change` - 涨跌额
- `change_pct` - 涨跌幅
- `high` - 最高价
- `low` - 最低价
- `open` - 今开
- `prev_close` - 昨收
- `avg_price` - 均价

#### 3. **成交信息**
- `volume` - 成交量（手）
- `amount` - 成交额（元）
- `turnover_rate` - 换手率（%）

#### 4. **估值指标**
- `pe_ratio` - 市盈率
- `pb_ratio` - 市净率

#### 5. **市值信息**
- `total_market_cap` - 总市值（元）
- `float_market_cap` - 流通市值（元）

#### 6. **涨跌停价格** ⭐ 新增
- `limit_up` - 涨停价
- `limit_down` - 跌停价

#### 7. **时间信息**
- `quote_time` - 报价时间

#### 8. **五档买卖盘** ⭐ 新增
- `bid_prices` - 买盘价格列表 [买 1, 买 2, 买 3, 买 4, 买 5]
- `ask_prices` - 卖盘价格列表 [卖 1, 卖 2, 卖 3, 卖 4, 卖 5]
- `bid_volumes` - 买盘数量列表 [买 1, 买 2, 买 3, 买 4, 买 5]
- `ask_volumes` - 卖盘数量列表 [卖 1, 卖 2, 卖 3, 卖 4, 卖 5]

## 🎯 使用示例

### 1. 基础查询

```python
from app.adapters.factory import DataSourceManager

adapter = await DataSourceManager.get_adapter("efinance")

# 获取单只股票实时行情
quote = await adapter.get_realtime_quote("600519")

print(f"股票：{quote['name']} ({quote['code']})")
print(f"最新价：{quote['price']}")
print(f"涨跌幅：{quote['change_pct']}%")
print(f"成交量：{quote['volume']}手")
print(f"成交额：{quote['amount']}元")
```

### 2. 查看五档买卖盘

```python
quote = await adapter.get_realtime_quote("600519")

# 买盘
print("买盘：")
for i in range(5):
    price = quote['bid_prices'][i]
    volume = quote['bid_volumes'][i]
    if price > 0:
        print(f"  买{i+1}: {price}元 x {volume}手")

# 卖盘
print("卖盘：")
for i in range(5):
    price = quote['ask_prices'][i]
    volume = quote['ask_volumes'][i]
    if price > 0:
        print(f"  卖{i+1}: {price}元 x {volume}手")
```

### 3. 查看涨跌停价格

```python
quote = await adapter.get_realtime_quote("600519")

print(f"涨停价：{quote['limit_up']}")
print(f"跌停价：{quote['limit_down']}")
print(f"当前价：{quote['price']}")

# 计算距离涨跌停的幅度
up_percent = (quote['limit_up'] - quote['price']) / quote['price'] * 100
down_percent = (quote['price'] - quote['limit_down']) / quote['price'] * 100
print(f"距离涨停：{up_percent:.2f}%")
print(f"距离跌停：{down_percent:.2f}%")
```

### 4. 查看市值和估值

```python
quote = await adapter.get_realtime_quote("600519")

print(f"总市值：{quote['total_market_cap']/1e8:.2f}亿")
print(f"流通市值：{quote['float_market_cap']/1e8:.2f}亿")
print(f"市盈率：{quote['pe_ratio']:.2f}")
print(f"市净率：{quote['pb_ratio']:.2f}")
```

### 5. 查看成交明细

```python
quote = await adapter.get_realtime_quote("600519")

print(f"今开：{quote['open']}")
print(f"最高：{quote['high']}")
print(f"最低：{quote['low']}")
print(f"昨收：{quote['prev_close']}")
print(f"均价：{quote['avg_price']}")
print(f"成交量：{quote['volume']}手")
print(f"成交额：{quote['amount']/1e6:.2f}万元")
print(f"换手率：{quote['turnover_rate']:.2f}%")
```

### 6. 完整的行情展示

```python
async def show_full_quote(code: str):
    """展示完整的股票行情"""
    quote = await adapter.get_realtime_quote(code)
    
    if not quote:
        print(f"未获取到 {code} 的行情数据")
        return
    
    print("="*60)
    print(f"{quote['name']} ({quote['code']}) - 实时行情")
    print("="*60)
    
    # 价格信息
    print(f"\n【价格信息】")
    print(f"  最新价：  {quote['price']:.2f}")
    print(f"  涨跌额：  {quote['change']:+.2f}")
    print(f"  涨跌幅：  {quote['change_pct']:+.2f}%")
    print(f"  昨收：    {quote['prev_close']:.2f}")
    print(f"  今开：    {quote['open']:.2f}")
    print(f"  最高：    {quote['high']:.2f}")
    print(f"  最低：    {quote['low']:.2f}")
    print(f"  均价：    {quote['avg_price']:.2f}")
    
    # 涨跌停
    print(f"\n【涨跌停】")
    print(f"  涨停价：  {quote['limit_up']:.2f} (+10%)")
    print(f"  跌停价：  {quote['limit_down']:.2f} (-10%)")
    
    # 成交信息
    print(f"\n【成交信息】")
    print(f"  成交量：  {quote['volume']:,.0f}手")
    print(f"  成交额：  {quote['amount']/1e6:,.2f}万元")
    print(f"  换手率：  {quote['turnover_rate']:.2f}%")
    
    # 市值和估值
    print(f"\n【市值和估值】")
    print(f"  总市值：  {quote['total_market_cap']/1e8:,.2f}亿")
    print(f"  流通市值：{quote['float_market_cap']/1e8:,.2f}亿")
    print(f"  市盈率：  {quote['pe_ratio']:.2f}")
    print(f"  市净率：  {quote['pb_ratio']:.2f}")
    
    # 五档买卖盘
    print(f"\n【五档买卖盘】")
    print("  卖盘:")
    for i in range(4, -1, -1):
        price = quote['ask_prices'][i]
        volume = quote['ask_volumes'][i]
        if price > 0:
            print(f"    卖{i+1}: {price:7.2f}元 x {volume:6.0f}手")
    
    print("  买盘:")
    for i in range(5):
        price = quote['bid_prices'][i]
        volume = quote['bid_volumes'][i]
        if price > 0:
            print(f"    买{i+1}: {price:7.2f}元 x {volume:6.0f}手")
    
    # 时间
    print(f"\n【报价时间】{quote['quote_time']}")
    print("="*60)

# 使用
await show_full_quote("600519")
```

## 📈 数据字段详解

### 五档买卖盘

五档买卖盘显示了当前市场上买卖双方的报价和数量：

```python
# 买盘（Bid）- 买方愿意支付的价格
bid_prices = [1707.0, 1706.99, 1706.88, 1706.87, 1706.86]
bid_volumes = [17.0, 8.0, 10.0, 8.0, 21.0]

# 卖盘（Ask）- 卖方愿意出售的价格
ask_prices = [1708.0, 1708.75, 1709.0, 1709.6, 1709.63]
ask_volumes = [3.0, 2.0, 5.0, 3.0, 1.0]

# 买一价 > 卖一价 = 买方市场（看涨）
# 卖一价 > 买一价 = 卖方市场（看跌）
spread = ask_prices[0] - bid_prices[0]  # 买卖价差
print(f"买卖价差：{spread}")
```

### 涨跌停价格

```python
# 涨停价 = 昨收 × 1.1
# 跌停价 = 昨收 × 0.9
limit_up = quote['limit_up']
limit_down = quote['limit_down']

# 判断是否涨停/跌停
if quote['price'] >= limit_up:
    print("涨停！")
elif quote['price'] <= limit_down:
    print("跌停！")
```

### 均价

```python
# 均价 = 成交额 / 成交量
avg_price = quote['avg_price']

# 均价反映市场平均成本
if quote['price'] > avg_price:
    print("当前价高于均价，市场偏强")
else:
    print("当前价低于均价，市场偏弱")
```

## 🔧 缓存机制

实时行情快照使用 60 秒缓存：

```python
# 第一次：实际请求
quote1 = await adapter.get_realtime_quote("600519")

# 60 秒内：直接返回缓存
quote2 = await adapter.get_realtime_quote("600519")  # 无网络请求

# 60 秒后：重新请求
quote3 = await adapter.get_realtime_quote("600519")  # 新的请求
```

## ⚠️ 注意事项

### 1. 数据更新频率

- **交易时段**：实时数据（3 秒刷新）
- **非交易时段**：最后收盘价
- **缓存时间**：60 秒

### 2. 五档数据

- 五档买卖盘在集合竞价时段可能为空
- 涨跌停时可能只有买单或卖单

### 3. 数据精度

- 价格：2 位小数
- 成交量：整数（手）
- 成交额：元
- 换手率：百分比

## 📊 应用场景

### 1. 实时监控

```python
# 监控股价变化
last_price = 0
while True:
    quote = await adapter.get_realtime_quote("600519")
    if quote['price'] != last_price:
        print(f"价格变动：{last_price} -> {quote['price']}")
        last_price = quote['price']
    await asyncio.sleep(3)  # 3 秒刷新
```

### 2. 买卖盘分析

```python
# 分析买卖盘力量
quote = await adapter.get_realtime_quote("600519")

# 买盘总量
bid_total = sum(quote['bid_volumes'])
# 卖盘总量
ask_total = sum(quote['ask_volumes'])

# 买卖比
ratio = bid_total / ask_total if ask_total > 0 else 0
print(f"买卖比：{ratio:.2f}")

if ratio > 1:
    print("买方力量较强")
else:
    print("卖方力量较强")
```

### 3. 涨跌停监控

```python
# 监控是否接近涨跌停
quote = await adapter.get_realtime_quote("600519")

distance_up = (quote['limit_up'] - quote['price']) / quote['price'] * 100
distance_down = (quote['price'] - quote['limit_down']) / quote['price'] * 100

if distance_up < 1:
    print(f"接近涨停！距离：{distance_up:.2f}%")
elif distance_down < 1:
    print(f"接近跌停！距离：{distance_down:.2f}%")
```

## 🧪 测试示例

```python
import asyncio
from app.adapters.efinance_adapter import EFinanceAdapter

async def test_realtime_quote():
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 获取实时行情
    quote = await adapter.get_realtime_quote("600519")
    
    if quote:
        print(f"✓ 贵州茅台实时行情")
        print(f"  最新价：{quote['price']}")
        print(f"  涨跌幅：{quote['change_pct']}%")
        print(f"  买一价：{quote['bid_prices'][0]}")
        print(f"  卖一价：{quote['ask_prices'][0]}")
        print(f"  涨停价：{quote['limit_up']}")
        print(f"  跌停价：{quote['limit_down']}")
    else:
        print("✗ 获取失败")

asyncio.run(test_realtime_quote())
```

## 📖 底层实现

### efinance 调用

```python
# 底层调用 efinance.stock.get_quote_snapshot
series = ef.stock.get_quote_snapshot(code.zfill(6))

# 返回 pandas Series 对象
# 包含完整的行情快照数据
```

### 数据处理

```python
# 安全获取数值
def safe_float(key, default=0.0):
    val = series.get(key, default)
    if val is None or str(val) == 'nan':
        return default
    return float(val)

# 构建完整数据
quote = {
    'price': safe_float('最新价'),
    'bid_prices': [safe_float('买 1 价'), ...],
    'ask_prices': [safe_float('卖 1 价'), ...],
    ...
}
```

## 🎯 总结

**优化成果**：
- ✅ 使用 `get_quote_snapshot` 获取完整行情
- ✅ 新增涨跌停价格
- ✅ 新增五档买卖盘
- ✅ 新增均价、市盈率、市净率等指标
- ✅ 更完整的数据字段
- ✅ 集成反风控机制

**数据完整性**：
- 基础价格：8 个字段
- 成交信息：3 个字段
- 估值指标：2 个字段
- 市值信息：2 个字段
- 涨跌停：2 个字段
- 五档买卖：20 个字段
- 时间信息：1 个字段

**总计**：38 个字段（优化前仅 13 个字段）

---

**提示**：所有实时行情数据都包含反风控机制，可安全使用！
