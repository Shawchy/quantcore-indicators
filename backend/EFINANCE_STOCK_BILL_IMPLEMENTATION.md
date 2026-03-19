# efinance 股票资金流向明细 API 实现总结

## ✅ 实现成果

### 新增接口

新增 `get_stock_bill_detail` 方法，用于获取单只股票最新交易日的日内分钟级单子流入流出数据。

### 数据字段（7 个）

```python
{
    'code': '600519',              # 股票代码
    'time': '2021-07-29 09:31',    # 时间（YYYY-MM-DD HH:MM）
    'main_net_amount': -3261705.0, # 主力净流入（元）
    'sm_net_amount': -389320.0,    # 小单净流入（元）
    'md_net_amount': 3651025.0,    # 中单净流入（元）
    'lg_net_amount': -12529658.0,  # 大单净流入（元）
    'elg_net_amount': 9267953.0    # 超大单净流入（元）
}
```

### 资金类型说明

1. **主力净流入**：超大单 + 大单净流入总和
2. **小单净流入**：散户小单净流入
3. **中单净流入**：中户中单净流入
4. **大单净流入**：大户大单净流入
5. **超大单净流入**：机构超大单净流入

## 🔧 技术实现

### 底层调用

```python
# 使用 efinance.stock.get_today_bill
df = ef.stock.get_today_bill(code.zfill(6))

# 返回 DataFrame，包含分钟级数据
```

### 数据处理

```python
# 遍历 DataFrame 每一行
for row in df.itertuples(index=False):
    detail = {
        'code': code,
        'time': getattr(row, '时间', ''),
        'main_net_amount': float(getattr(row, '主力净流入', 0)),
        'sm_net_amount': float(getattr(row, '小单净流入', 0)),
        'md_net_amount': float(getattr(row, '中单净流入', 0)),
        'lg_net_amount': float(getattr(row, '大单净流入', 0)),
        'elg_net_amount': float(getattr(row, '超大单净流入', 0))
    }
```

### 缓存机制

```python
# 缓存键
cache_key = adapter._get_cache_key('bill_detail', code=code)

# 缓存时间：60 秒
```

### 反风控集成

```python
# 频率控制
await self._rate_limit()

# 成功/失败统计
self.record_request_success()
self.record_request_failure()
```

## 📈 使用示例

### 基础查询

```python
# 获取贵州茅台资金流向明细
bill_detail = await adapter.get_stock_bill_detail("600519")
print(f"共获取 {len(bill_detail)} 条数据")
```

### 查看最新数据

```python
if bill_detail:
    latest = bill_detail[-1]
    print(f"主力净流入：{latest['main_net_amount']:,.0f}元")
```

### 分析全天资金流向

```python
total_main = sum(d['main_net_amount'] for d in bill_detail)
print(f"全天主力净流入：{total_main:,.0f}元")
```

### 找出主力大幅流入时段

```python
sorted_by_main = sorted(bill_detail, key=lambda x: x['main_net_amount'], reverse=True)
top5 = sorted_by_main[:5]
```

## 🎯 应用场景

### 1. 主力监控

```python
# 监控主力净流入
total_main = sum(d['main_net_amount'] for d in bill_detail)
if total_main > 1e8:
    print("主力大幅流入")
```

### 2. 异动检测

```python
# 检测异常时段（主力净流入绝对值>1000 万）
abnormal = [d for d in bill_detail if abs(d['main_net_amount']) > 1e7]
```

### 3. 尾盘分析

```python
# 分析尾盘 1 小时资金流向
last_hour = bill_detail[-48:]
total_main = sum(d['main_net_amount'] for d in last_hour)
```

### 4. 开盘分析

```python
# 分析开盘 30 分钟资金流向
opening = bill_detail[:30]
total_main = sum(d['main_net_amount'] for d in opening)
```

### 5. 多股票对比

```python
for code in codes:
    bill_detail = await adapter.get_stock_bill_detail(code)
    total_main = sum(d['main_net_amount'] for d in bill_detail)
    print(f"{code}: 主力净流入 {total_main:,.0f}元")
```

## 📝 已修改文件

### 1. **efinance_adapter.py**
- 新增 `get_stock_bill_detail` 方法
- 完整的文档字符串
- 集成反风控机制
- 缓存支持

### 2. **EFINANCE_STOCK_BILL_DETAIL_GUIDE.md**
- 完整的使用指南
- 详细的数据字段说明
- 丰富的使用示例
- 应用场景说明

## ⚠️ 注意事项

### 1. 数据更新
- **交易时段**：实时数据（每分钟更新）
- **非交易时段**：最后交易日数据
- **缓存时间**：60 秒

### 2. 数据量
- **交易日**：约 240 条数据（4 小时×60 分钟）
- **非交易日**：无数据

### 3. 使用限制
- 仅支持 A 股股票
- 不支持港股、美股
- 不支持基金、债券

### 4. 数据准确性
- 数据来源于东方财富
- 可能存在 1-2 分钟延迟
- 建议结合其他数据源验证

## 📖 相关文档

- [股票资金流向明细使用指南](./EFINANCE_STOCK_BILL_DETAIL_GUIDE.md)
- [市场板块行情优化](./EFINANCE_MARKET_QUOTES_GUIDE.md)
- [实时行情快照优化](./EFINANCE_REALTIME_QUOTE_SNAPSHOT.md)
- [K 线周期优化](./EFINANCE_KLINE_PERIODS.md)
- [反风控机制](./EFINANCE_ANTI_CRAWLING.md)

## 📌 总结

**实现成果**：
- ✅ 新增 `get_stock_bill_detail` 接口
- ✅ 获取单只股票资金流向明细
- ✅ 分钟级数据，精确到每分钟
- ✅ 包含 5 种资金类型
- ✅ 集成反风控机制
- ✅ 支持缓存（60 秒）

**数据完整性**：
- 7 个完整字段
- 5 种资金类型
- 分钟级精度
- 约 240 条数据/交易日

**使用建议**：
- 结合行情数据分析
- 关注异常时段
- 分析主力动向
- 监控尾盘/开盘资金流向

---

**提示**：所有资金流向数据都包含反风控机制，可安全使用！
