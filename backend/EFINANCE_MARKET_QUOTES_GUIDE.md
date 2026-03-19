# efinance 市场板块行情 API 优化指南

## 📊 优化内容

优化了 `get_market_realtime_quotes` 接口，完整支持 efinance 的所有市场类型，包括 A 股、港股、美股、ETF、行业板块、概念板块等。

## 🎯 支持的市场类型

### 1. **A 股市场**
- `'沪深 A 股'` - 沪深 A 股（默认）
- `'沪 A'` - 沪市 A 股
- `'深 A'` - 深市 A 股
- `'北 A'` - 北证 A 股

### 2. **板块指数**
- `'创业板'` - 创业板
- `'科创板'` - 科创板

### 3. **基金市场**
- `'ETF'` - ETF 基金
- `'LOF'` - LOF 基金

### 4. **行业概念**
- `'行业板块'` - 行业板块
- `'概念板块'` - 概念板块

### 5. **国际市场**
- `'港股'` - 港股
- `'美股'` - 美股
- `'中概股'` - 中国概念股

### 6. **其他市场**
- `'可转债'` - 沪深可转债
- `'期货'` - 期货

### 7. **指数系列**
- `'沪深系列指数'` - 沪深系列指数
- `'上证系列指数'` - 上证系列指数
- `'深证系列指数'` - 深证系列指数

### 8. **特色板块** ⭐ 新增
- `'沪股通'` - 沪股通
- `'深股通'` - 深股通
- `'新股'` - 沪深新股

## 🔧 使用示例

### 1. 基础查询

```python
from app.adapters.factory import DataSourceManager

adapter = await DataSourceManager.get_adapter("efinance")

# 获取沪深 A 股全部股票（默认）
quotes = await adapter.get_market_realtime_quotes()
print(f"沪深 A 股共 {len(quotes)} 只股票")

# 获取创业板股票
quotes = await adapter.get_market_realtime_quotes(market_types=['创业板'])
print(f"创业板共 {len(quotes)} 只股票")

# 获取 ETF 基金
quotes = await adapter.get_market_realtime_quotes(market_types=['ETF'])
print(f"ETF 基金共 {len(quotes)} 只")
```

### 2. 多市场查询

```python
# 获取创业板 + 科创板股票
quotes = await adapter.get_market_realtime_quotes(
    market_types=['创业板', '科创板']
)

# 获取 ETF + LOF 基金
quotes = await adapter.get_market_realtime_quotes(
    market_types=['ETF', 'LOF']
)

# 获取行业板块 + 概念板块
quotes = await adapter.get_market_realtime_quotes(
    market_types=['行业板块', '概念板块']
)
```

### 3. 使用板块代码查询 ⭐

```python
# 获取光伏板块（板块代码：884723）
quotes = await adapter.get_market_realtime_quotes(fs="884723")

# 获取沪深 300 指数成分股（代码：000300）
quotes = await adapter.get_market_realtime_quotes(fs="000300")

# 获取上证 50 指数成分股（代码：000016）
quotes = await adapter.get_market_realtime_quotes(fs="000016")
```

### 4. 高级筛选 ⭐

```python
# 获取光伏板块中上涨的股票
quotes = await adapter.get_market_realtime_quotes(fs="884723,pctChg:>0")

# 获取市值大于 500 亿的股票
quotes = await adapter.get_market_realtime_quotes(fs="pctChg:>0,totMv:>50000000000")

# 获取北交所股票（市场代码：mkt:2）
quotes = await adapter.get_market_realtime_quotes(fs="mkt:2")

# 获取沪市股票（市场代码：mkt:1）
quotes = await adapter.get_market_realtime_quotes(fs="mkt:1")

# 获取深市股票（市场代码：mkt:0）
quotes = await adapter.get_market_realtime_quotes(fs="mkt:0")
```

### 5. 国际市场查询

```python
# 获取港股
quotes = await adapter.get_market_realtime_quotes(market_types=['港股'])
print(f"港股共 {len(quotes)} 只")

# 获取美股
quotes = await adapter.get_market_realtime_quotes(market_types=['美股'])
print(f"美股共 {len(quotes)} 只")

# 获取中概股
quotes = await adapter.get_market_realtime_quotes(market_types=['中概股'])
```

### 6. 基金市场查询

```python
# 获取 ETF 基金
quotes = await adapter.get_market_realtime_quotes(market_types=['ETF'])

# 获取 LOF 基金
quotes = await adapter.get_market_realtime_quotes(market_types=['LOF'])

# 获取可转债
quotes = await adapter.get_market_realtime_quotes(market_types=['可转债'])
```

### 7. 行业概念查询

```python
# 获取行业板块
quotes = await adapter.get_market_realtime_quotes(market_types=['行业板块'])
print(f"行业板块共 {len(quotes)} 个")

# 获取概念板块
quotes = await adapter.get_market_realtime_quotes(market_types=['概念板块'])
print(f"概念板块共 {len(quotes)} 个")
```

### 8. 指数系列查询

```python
# 获取沪深系列指数
quotes = await adapter.get_market_realtime_quotes(market_types=['沪深系列指数'])

# 获取上证系列指数
quotes = await adapter.get_market_realtime_quotes(market_types=['上证系列指数'])

# 获取深证系列指数
quotes = await adapter.get_market_realtime_quotes(market_types=['深证系列指数'])
```

### 9. 特色板块查询 ⭐

```python
# 获取沪股通股票
quotes = await adapter.get_market_realtime_quotes(market_types=['沪股通'])

# 获取深股通股票
quotes = await adapter.get_market_realtime_quotes(market_types=['深股通'])

# 获取新股
quotes = await adapter.get_market_realtime_quotes(market_types=['新股'])
```

### 10. 自定义返回字段

```python
# 只获取股票代码、名称、最新价、涨跌幅
quotes = await adapter.get_market_realtime_quotes(
    market_types=['创业板'],
    fields=['股票代码', '股票名称', '最新价', '涨跌幅']
)

# 只获取市值相关字段
quotes = await adapter.get_market_realtime_quotes(
    fs="884723",
    fields=['股票代码', '股票名称', '总市值', '流通市值']
)
```

## 📊 数据字段说明

### 完整字段列表

```python
quote = {
    '股票代码': '300750',           # 股票代码
    '股票名称': '宁德时代',         # 股票名称
    '涨跌幅': 2.5,                 # 涨跌幅（%）
    '最新价': 180.5,               # 最新价（元）
    '最高': 185.0,                 # 最高价（元）
    '最低': 178.0,                 # 最低价（元）
    '今开': 182.0,                 # 今开（元）
    '涨跌额': 4.5,                 # 涨跌额（元）
    '换手率': 1.5,                 # 换手率（%）
    '量比': 1.2,                   # 量比
    '动态市盈率': 25.5,            # 动态市盈率
    '成交量': 150000,              # 成交量（手）
    '成交额': 27000000000,         # 成交额（元）
    '昨日收盘': 176.0,             # 昨日收盘价（元）
    '总市值': 4200000000000,       # 总市值（元）
    '流通市值': 3500000000000,     # 流通市值（元）
    '行情 ID': '0.300750',         # 行情 ID
    '市场类型': '深 A'             # 市场类型
}
```

### 可用字段列表

```python
fields = [
    '股票代码',    # 股票代码
    '股票名称',    # 股票名称
    '涨跌幅',      # 涨跌幅（%）
    '最新价',      # 最新价（元）
    '最高',        # 最高价（元）
    '最低',        # 最低价（元）
    '今开',        # 今开（元）
    '涨跌额',      # 涨跌额（元）
    '换手率',      # 换手率（%）
    '量比',        # 量比
    '动态市盈率',  # 动态市盈率
    '成交量',      # 成交量（手）
    '成交额',      # 成交额（元）
    '昨日收盘',    # 昨日收盘价（元）
    '总市值',      # 总市值（元）
    '流通市值',    # 流通市值（元）
    '行情 ID',     # 行情 ID
    '市场类型'     # 市场类型
]
```

## 🔍 高级筛选条件

### 1. 市场类型筛选

```python
# 沪市（mkt:1）
quotes = await adapter.get_market_realtime_quotes(fs="mkt:1")

# 深市（mkt:0）
quotes = await adapter.get_market_realtime_quotes(fs="mkt:0")

# 北交所（mkt:2）
quotes = await adapter.get_market_realtime_quotes(fs="mkt:2")
```

### 2. 涨跌幅筛选

```python
# 上涨股票（pctChg:>0）
quotes = await adapter.get_market_realtime_quotes(fs="pctChg:>0")

# 下跌股票（pctChg:<0）
quotes = await adapter.get_market_realtime_quotes(fs="pctChg:<0")

# 涨停股票（pctChg:>=9.8）
quotes = await adapter.get_market_realtime_quotes(fs="pctChg:>=9.8")

# 跌幅>5%（pctChg:>-5）
quotes = await adapter.get_market_realtime_quotes(fs="pctChg:>-5")
```

### 3. 市值筛选

```python
# 市值>500 亿（totMv:>50000000000）
quotes = await adapter.get_market_realtime_quotes(fs="totMv:>50000000000")

# 市值<100 亿（totMv:<10000000000）
quotes = await adapter.get_market_realtime_quotes(fs="totMv:<10000000000")

# 市值 100 亿 -500 亿
quotes = await adapter.get_market_realtime_quotes(fs="totMv:>10000000000,totMv:<50000000000")
```

### 4. 换手率筛选

```python
# 换手率>5%（tRt:>5）
quotes = await adapter.get_market_realtime_quotes(fs="tRt:>5")

# 换手率>10%（活跃）
quotes = await adapter.get_market_realtime_quotes(fs="tRt:>10")
```

### 5. 成交量筛选

```python
# 成交量>100 万手（vol:>1000000）
quotes = await adapter.get_market_realtime_quotes(fs="vol:>1000000")

# 成交额>10 亿（amt:>1000000000）
quotes = await adapter.get_market_realtime_quotes(fs="amt:>1000000000")
```

### 6. 组合筛选

```python
# 光伏板块 + 上涨 + 市值>200 亿
quotes = await adapter.get_market_realtime_quotes(
    fs="884723,pctChg:>0,totMv:>20000000000"
)

# 创业板 + 上涨 + 换手率>5%
quotes = await adapter.get_market_realtime_quotes(
    fs="创业板，pctChg:>0,tRt:>5"
)

# 沪市 + 市值>1000 亿 + 上涨
quotes = await adapter.get_market_realtime_quotes(
    fs="mkt:1,pctChg:>0,totMv:>100000000000"
)
```

## 📈 应用场景

### 1. 板块监控

```python
# 监控光伏板块
async def monitor_pv_sector():
    quotes = await adapter.get_market_realtime_quotes(fs="884723")
    
    # 计算板块涨跌幅
    total_change = sum(q['涨跌幅'] for q in quotes)
    avg_change = total_change / len(quotes) if quotes else 0
    
    print(f"光伏板块平均涨跌幅：{avg_change:.2f}%")
    print(f"板块股票数：{len(quotes)}")
    
    # 找出领涨股票
    top_stocks = sorted(quotes, key=lambda x: x['涨跌幅'], reverse=True)[:5]
    for stock in top_stocks:
        print(f"{stock['股票名称']}: {stock['涨跌幅']}%")

await monitor_pv_sector()
```

### 2. 选股策略

```python
# 选股：市值>100 亿 + 上涨 + 换手率>3%
async def select_stocks():
    quotes = await adapter.get_market_realtime_quotes(
        fs="pctChg:>0,totMv:>10000000000,tRt:>3"
    )
    
    print(f"符合条件的股票：{len(quotes)}只")
    
    # 按市值排序
    quotes_sorted = sorted(quotes, key=lambda x: x['总市值'], reverse=True)
    
    for stock in quotes_sorted[:10]:
        print(f"{stock['股票名称']} ({stock['股票代码']})")
        print(f"  市值：{stock['总市值']/1e8:.2f}亿")
        print(f"  涨幅：{stock['涨跌幅']}%")
        print(f"  换手率：{stock['换手率']}%")

await select_stocks()
```

### 3. 市场情绪分析

```python
async def market_sentiment():
    # 获取全部 A 股
    quotes = await adapter.get_market_realtime_quotes()
    
    # 统计上涨/下跌家数
    up_count = sum(1 for q in quotes if q['涨跌幅'] > 0)
    down_count = sum(1 for q in quotes if q['涨跌幅'] < 0)
    
    total = len(quotes)
    up_ratio = up_count / total * 100 if total > 0 else 0
    
    print(f"市场情绪分析:")
    print(f"  上涨家数：{up_count} ({up_ratio:.1f}%)")
    print(f"  下跌家数：{down_count} ({100-up_ratio:.1f}%)")
    
    if up_ratio > 70:
        print("  市场情绪：强势")
    elif up_ratio > 50:
        print("  市场情绪：偏强")
    elif up_ratio > 30:
        print("  市场情绪：偏弱")
    else:
        print("  市场情绪：弱势")

await market_sentiment()
```

### 4. 板块轮动监控

```python
async def sector_rotation():
    sectors = ['行业板块', '概念板块']
    
    for sector in sectors:
        quotes = await adapter.get_market_realtime_quotes(
            market_types=[sector]
        )
        
        # 计算板块平均涨跌幅
        avg_change = sum(q['涨跌幅'] for q in quotes) / len(quotes) if quotes else 0
        
        print(f"{sector}: {avg_change:.2f}% ({len(quotes)}个)")

await sector_rotation()
```

### 5. ETF 套利机会

```python
async def etf_arbitrage():
    # 获取 ETF 基金
    etfs = await adapter.get_market_realtime_quotes(market_types=['ETF'])
    
    # 找出折价/溢价的 ETF
    for etf in etfs[:10]:  # 示例前 10 个
        print(f"{etf['股票名称']}: {etf['涨跌幅']}%")

await etf_arbitrage()
```

## ⚠️ 注意事项

### 1. 数据量

- **沪深 A 股**：约 4500 只股票
- **创业板**：约 1200 只股票
- **科创板**：约 500 只股票
- **ETF**：约 500 只
- **港股**：约 2500 只

**建议**：大数据量时指定 `fields` 参数减少返回字段

### 2. 缓存时间

- 缓存时间：60 秒
- 不同市场类型独立缓存

### 3. 频率控制

- 自动频率控制（1-2 秒）
- 交易时段延迟更长

### 4. 数据更新

- **交易时段**：实时数据（3 秒刷新）
- **非交易时段**：最后收盘价

## 🎯 总结

**优化成果**：
- ✅ 完整支持 8 大类市场类型
- ✅ 新增特色板块（沪股通、深股通、新股）
- ✅ 支持板块代码查询
- ✅ 支持高级筛选条件
- ✅ 支持自定义返回字段
- ✅ 集成反风控机制

**支持的市场**：
- A 股市场：4 个
- 板块指数：2 个
- 基金市场：2 个
- 行业概念：2 个
- 国际市场：3 个
- 其他市场：2 个
- 指数系列：3 个
- 特色板块：3 个

**总计**：21 个市场类型，支持任意组合查询！

---

**提示**：所有市场数据都包含反风控机制，可安全使用！
