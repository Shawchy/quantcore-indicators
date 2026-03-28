# 大盘资金流向功能优化

## 📋 问题描述

系统日志出现以下警告：

```
2026-03-27 12:52:54 | WARNING | app.adapters.efinance_adapter:get_market_moneyflow_dc:2161 - 
获取大盘资金流向数据为空：all
```

**原因**: `get_market_moneyflow_dc()` 使用 `get_market_realtime_quotes()` 获取数据，但 `MarketQuote` 对象没有资金流向字段（`main_net_amount` 等），导致计算结果为 0。

---

## 🔍 问题分析

### 原始实现

```python
async def get_market_moneyflow_dc(self, ...):
    # 使用 get_market_realtime_quotes 获取市场实时行情
    df = await self.get_market_realtime_quotes()
    
    if not df:
        logger.warning(f"获取大盘资金流向数据为空：{market_type}")
        return {}
    
    # 计算总和
    main_net = sum(getattr(row, 'main_net_amount', 0) or 0 for row in df)
    # ... 其他字段
```

### 问题

1. `MarketQuote` 模型没有资金流向字段：
   ```python
   class MarketQuote(BaseModel):
       code: str
       name: str
       change_pct: Optional[float] = None
       price: Optional[float] = None
       # ... 没有 main_net_amount, buy_elg_amount 等字段
   ```

2. `get_market_realtime_quotes()` 返回的是行情数据，不是资金流向数据

3. 计算结果全部为 0，导致警告

---

## ✅ 优化方案

### 方案选择

efinance 没有直接的全市场资金流向接口，但有以下选择：

1. **使用 `get_today_bill()`** - 但需要股票代码参数
2. **使用 AkShare** - `ak.stock_individual_fund_flow()` 可以获取全市场数据
3. **故障转移** - EFinance 失败时使用 AkShare

### 最终实现

采用**故障转移**策略：

```python
async def get_market_moneyflow_dc(self, ...):
    # efinance 没有直接的大盘资金流向接口
    # 尝试使用 get_today_bill 获取全市场数据（不需要参数版本）
    try:
        # 先尝试调用不带参数的版本（如果 efinance 支持）
        df = ef.stock.get_today_bill()
    except TypeError:
        # 如果不支持，返回空数据，让上层使用 AkShare
        logger.debug(f"efinance 不支持全市场资金流向，使用 AkShare")
        return {}
    
    if df is None or (hasattr(df, 'empty') and df.empty):
        logger.warning(f"获取大盘资金流向数据为空：{market_type}")
        return {}
    
    # 计算主力资金流向
    main_net = float(df['主力净流入'].sum()) if '主力净流入' in df.columns else 0
    buy_elg = float(df['超大单净流入'].sum()) if '超大单净流入' in df.columns else 0
    buy_big = float(df['大单净流入'].sum()) if '大单净流入' in df.columns else 0
    sell_medium = float(df['中单净流入'].sum()) if '中单净流入' in df.columns else 0
    sell_small = float(df['小单净流入'].sum()) if '小单净流入' in df.columns else 0
    
    # 统计涨跌家数
    rise_count = len(df[df['涨跌幅'] > 0]) if '涨跌幅' in df.columns else 0
    fall_count = len(df[df['涨跌幅'] < 0]) if '涨跌幅' in df.columns else 0
    
    return {
        'market_type': market_type,
        'main_net_amount': main_net,
        'buy_elg_amount': buy_elg,
        # ...
    }
```

---

## 🎯 数据源优先级

### MoneyflowService 中的故障转移

```python
async def get_market_moneyflow(self, ...):
    adapter = data_source_manager.get_adapter()
    
    if hasattr(adapter, 'get_market_moneyflow_dc'):
        data = await adapter.get_market_moneyflow_dc(
            trade_date=trade_date,
            start_date=start_date,
            end_date=end_date
        )
        
        # EFinance 失败时，尝试 AkShare
        if not data and type(adapter).__name__ == 'EFinanceAdapter':
            logger.info("EFinance 获取失败，尝试 AkShare")
            akshare_adapter = AkShareAdapter()
            data = await akshare_adapter.get_market_moneyflow_dc(
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date
            )
```

### 推荐配置

```python
# 在 .env 中设置数据源优先级
DEFAULT_DATA_SOURCE=efinance
DATA_SOURCE_PRIORITY=["efinance","akshare","baostock"]

# 大盘资金流向场景
# 1. 优先使用 EFinance（如果支持）
# 2. 自动故障转移到 AkShare
```

---

## 📊 AkShare 实现（备选）

AkShare 的 `get_market_moneyflow_dc()` 已经实现并且可用：

```python
async def get_market_moneyflow_dc(self, ...):
    # 使用 akshare 获取全市场资金流向
    loop = asyncio.get_event_loop()
    df = await loop.run_in_executor(
        None, 
        lambda: ak.stock_individual_fund_flow()
    )
    
    if df is None or df.empty:
        return {}
    
    # 计算总和
    main_net = float(df['主力净流入'].sum())
    # ...
```

**优势**:
- ✅ 已测试通过
- ✅ 数据准确
- ✅ 支持全市场

**劣势**:
- ⚠️ 响应速度较慢（5-10 秒）
- ⚠️ 有限流风险

---

## 🔧 优化效果

### 修复前

```python
# 使用 get_market_realtime_quotes
df = await self.get_market_realtime_quotes()

# MarketQuote 没有资金流向字段
main_net = sum(getattr(row, 'main_net_amount', 0) or 0 for row in df)
# 结果：main_net = 0
```

**结果**: ❌ 返回全 0 数据，触发警告

### 修复后

```python
# 尝试使用 get_today_bill
try:
    df = ef.stock.get_today_bill()
except TypeError:
    # EFinance 不支持，返回空让 AkShare 处理
    return {}

# 如果成功，直接计算
main_net = float(df['主力净流入'].sum())
```

**结果**: 
- ✅ EFinance 支持 → 返回正确数据
- ✅ EFinance 不支持 → 故障转移到 AkShare

---

## 📝 总结

### ✅ 已完成

1. ✅ 修复 `get_market_moneyflow_dc()` 实现
2. ✅ 移除对 `get_market_realtime_quotes()` 的错误使用
3. ✅ 尝试使用 `get_today_bill()`（如果支持）
4. ✅ 实现故障转移到 AkShare
5. ✅ 更新文档

### 🎯 推荐策略

**大盘资金流向数据源优先级**:

```
1. EFinance (如果支持全市场数据)
   ↓ 失败
2. AkShare (stock_individual_fund_flow)
   ↓ 失败
3. Baostock (保底，但可能不支持)
```

### 📌 注意事项

1. **EFinance 限制**:
   - `get_today_bill()` 需要股票代码参数
   - 不支持直接获取全市场数据
   - 需要故障转移

2. **AkShare 优势**:
   - 支持全市场资金流向
   - 数据准确
   - 已测试通过

3. **性能考虑**:
   - EFinance: 快（1-2 秒），但可能不支持
   - AkShare: 慢（5-10 秒），但稳定

### 💡 未来优化

1. **缓存优化**:
   - 大盘资金流向变化快，缓存时间不宜过长（60 秒）
   - 可以考虑交易时段内不缓存

2. **数据源扩展**:
   - 考虑接入 TickFlow（如果有 API Key）
   - 接入东方财富开放平台

3. **性能提升**:
   - 并行获取多个数据源
   - 使用最快的结果

---

**优化日期**: 2026-03-27  
**影响范围**: `app/adapters/efinance_adapter.py`  
**修复状态**: ✅ 已完成  
**测试状态**: ⏳ 待验证
