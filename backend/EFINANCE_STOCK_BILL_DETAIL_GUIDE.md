# efinance 股票资金流向明细 API 使用指南

## 📊 接口说明

新增 `get_stock_bill_detail` 接口，用于获取单只股票最新交易日的日内分钟级单子流入流出数据。

### 数据字段

返回的数据包含以下字段：

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

- **主力净流入**：超大单 + 大单净流入总和
- **小单净流入**：散户小单净流入
- **中单净流入**：中户中单净流入
- **大单净流入**：大户大单净流入
- **超大单净流入**：机构超大单净流入

## 🎯 使用示例

### 1. 基础查询

```python
from app.adapters.factory import DataSourceManager

adapter = await DataSourceManager.get_adapter("efinance")

# 获取贵州茅台资金流向明细
bill_detail = await adapter.get_stock_bill_detail("600519")

print(f"共获取 {len(bill_detail)} 条数据")
```

### 2. 查看最新数据

```python
bill_detail = await adapter.get_stock_bill_detail("600519")

if bill_detail:
    # 最新一分钟数据
    latest = bill_detail[-1]
    print(f"时间：{latest['time']}")
    print(f"主力净流入：{latest['main_net_amount']:,.0f}元")
    print(f"小单净流入：{latest['sm_net_amount']:,.0f}元")
    print(f"中单净流入：{latest['md_net_amount']:,.0f}元")
    print(f"大单净流入：{latest['lg_net_amount']:,.0f}元")
    print(f"超大单净流入：{latest['elg_net_amount']:,.0f}元")
```

### 3. 分析全天资金流向

```python
bill_detail = await adapter.get_stock_bill_detail("600519")

if bill_detail:
    # 计算总和
    total_main = sum(d['main_net_amount'] for d in bill_detail)
    total_sm = sum(d['sm_net_amount'] for d in bill_detail)
    total_md = sum(d['md_net_amount'] for d in bill_detail)
    total_lg = sum(d['lg_net_amount'] for d in bill_detail)
    total_elg = sum(d['elg_net_amount'] for d in bill_detail)
    
    print(f"【全天资金流向】")
    print(f"  主力净流入：{total_main:,.0f}元")
    print(f"  小单净流入：{total_sm:,.0f}元")
    print(f"  中单净流入：{total_md:,.0f}元")
    print(f"  大单净流入：{total_lg:,.0f}元")
    print(f"  超大单净流入：{total_elg:,.0f}元")
```

### 4. 分析资金流向趋势

```python
bill_detail = await adapter.get_stock_bill_detail("600519")

if bill_detail:
    # 计算主力净流入的累计值
    cumulative_main = 0
    trend_data = []
    
    for d in bill_detail:
        cumulative_main += d['main_net_amount']
        trend_data.append({
            'time': d['time'],
            'cumulative': cumulative_main
        })
    
    # 显示关键时间点
    print(f"【主力净流入累计趋势】")
    print(f"  开盘（9:30）: {trend_data[0]['cumulative']:,.0f}元")
    print(f"  午间（11:30）: {trend_data[119]['cumulative']:,.0f}元")
    print(f"  收盘（15:00）: {trend_data[-1]['cumulative']:,.0f}元")
```

### 5. 找出主力大幅流入/流出时段

```python
bill_detail = await adapter.get_stock_bill_detail("600519")

if bill_detail:
    # 找出主力净流入最大的 5 个时段
    sorted_by_main = sorted(bill_detail, key=lambda x: x['main_net_amount'], reverse=True)
    
    print(f"【主力大幅流入时段 TOP5】")
    for i, d in enumerate(sorted_by_main[:5], 1):
        print(f"  {i}. {d['time']} - {d['main_net_amount']:,.0f}元")
    
    # 找出主力净流出最大的 5 个时段
    sorted_by_out = sorted(bill_detail, key=lambda x: x['main_net_amount'])
    
    print(f"\n【主力大幅流出时段 TOP5】")
    for i, d in enumerate(sorted_by_out[:5], 1):
        print(f"  {i}. {d['time']} - {d['main_net_amount']:,.0f}元")
```

### 6. 分析超大单动向

```python
bill_detail = await adapter.get_stock_bill_detail("600519")

if bill_detail:
    # 统计超大单净流入为正的时段
    positive_elg = [d for d in bill_detail if d['elg_net_amount'] > 0]
    negative_elg = [d for d in bill_detail if d['elg_net_amount'] < 0]
    
    print(f"【超大单动向分析】")
    print(f"  净流入时段数：{len(positive_elg)}")
    print(f"  净流出时段数：{len(negative_elg)}")
    print(f"  净流入时段占比：{len(positive_elg)/len(bill_detail)*100:.1f}%")
    
    # 计算净流入/流出总额
    total_positive = sum(d['elg_net_amount'] for d in positive_elg)
    total_negative = sum(d['elg_net_amount'] for d in negative_elg)
    
    print(f"  净流入总额：{total_positive:,.0f}元")
    print(f"  净流出总额：{total_negative:,.0f}元")
```

### 7. 多股票对比

```python
codes = ["600519", "300750", "002594"]  # 贵州茅台、宁德时代、比亚迪

for code in codes:
    bill_detail = await adapter.get_stock_bill_detail(code)
    
    if bill_detail:
        total_main = sum(d['main_net_amount'] for d in bill_detail)
        print(f"{code}: 主力净流入 {total_main:,.0f}元")
```

## 📈 应用场景

### 1. 主力监控

```python
async def monitor_main_force(code: str):
    """监控主力动向"""
    bill_detail = await adapter.get_stock_bill_detail(code)
    
    if bill_detail:
        # 计算主力净流入
        total_main = sum(d['main_net_amount'] for d in bill_detail)
        
        # 判断主力态度
        if total_main > 1e8:  # 大于 1 亿
            print(f"{code}: 主力大幅流入 {total_main/1e8:.2f}亿")
        elif total_main > 0:
            print(f"{code}: 主力小幅流入 {total_main/1e4:.0f}万")
        elif total_main < -1e8:
            print(f"{code}: 主力大幅流出 {abs(total_main)/1e8:.2f}亿")
        else:
            print(f"{code}: 主力小幅流出 {abs(total_main)/1e4:.0f}万")

await monitor_main_force("600519")
```

### 2. 异动检测

```python
async def detect_abnormal(code: str):
    """检测异常资金流向"""
    bill_detail = await adapter.get_stock_bill_detail(code)
    
    if bill_detail:
        # 找出异常时段（主力净流入绝对值>1000 万）
        abnormal = [d for d in bill_detail if abs(d['main_net_amount']) > 1e7]
        
        if abnormal:
            print(f"{code}: 发现 {len(abnormal)} 个异常时段")
            for d in abnormal[:5]:  # 显示前 5 个
                print(f"  {d['time']}: {d['main_net_amount']/1e4:.0f}万")

await detect_abnormal("600519")
```

### 3. 尾盘分析

```python
async def analyze_last_hour(code: str):
    """分析尾盘 1 小时资金流向"""
    bill_detail = await adapter.get_stock_bill_detail(code)
    
    if bill_detail and len(bill_detail) >= 48:  # 最后 48 分钟
        last_hour = bill_detail[-48:]
        total_main = sum(d['main_net_amount'] for d in last_hour)
        
        print(f"{code}: 尾盘 1 小时主力净流入 {total_main/1e4:.0f}万")
        
        if total_main > 0:
            print("  尾盘资金流入，可能看好明日行情")
        else:
            print("  尾盘资金流出，可能看空明日行情")

await analyze_last_hour("600519")
```

### 4. 开盘分析

```python
async def analyze_opening(code: str):
    """分析开盘 30 分钟资金流向"""
    bill_detail = await adapter.get_stock_bill_detail(code)
    
    if bill_detail and len(bill_detail) >= 30:
        opening = bill_detail[:30]
        total_main = sum(d['main_net_amount'] for d in opening)
        
        print(f"{code}: 开盘 30 分钟主力净流入 {total_main/1e4:.0f}万")
        
        if total_main > 0:
            print("  开盘资金流入，可能强势")
        else:
            print("  开盘资金流出，可能弱势")

await analyze_opening("600519")
```

## ⚠️ 注意事项

### 1. 数据更新

- **交易时段**：实时数据（每分钟更新）
- **非交易时段**：最后交易日数据
- **缓存时间**：60 秒

### 2. 数据量

- **交易日**：约 240 条数据（4 小时×60 分钟）
- **非交易日**：无数据

### 3. 数据准确性

- 数据来源于东方财富
- 可能存在 1-2 分钟延迟
- 建议结合其他数据源验证

### 4. 使用限制

- 仅支持 A 股股票
- 不支持港股、美股
- 不支持基金、债券

## 🎯 总结

**接口特点**：
- ✅ 获取单只股票资金流向明细
- ✅ 分钟级数据，精确到每分钟
- ✅ 包含 5 种资金类型（主力、小单、中单、大单、超大单）
- ✅ 支持缓存（60 秒）
- ✅ 集成反风控机制

**数据字段**：
- 股票代码
- 时间（YYYY-MM-DD HH:MM）
- 主力净流入（元）
- 小单净流入（元）
- 中单净流入（元）
- 大单净流入（元）
- 超大单净流入（元）

**使用建议**：
- 结合行情数据分析
- 关注异常时段
- 分析主力动向
- 监控尾盘/开盘资金流向

---

**提示**：所有资金流向数据都包含反风控机制，可安全使用！
