# 数据源场景化优化方案

> 基于各数据源 API 实现特点和性能表现的深度优化

---

## 📊 数据源 API 能力矩阵

### 已实现 API 接口统计

| 数据源 | 接口数量 | 核心接口 | 特色接口 | 性能评级 |
|--------|---------|---------|---------|---------|
| **EFinance** | 37 个 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **TickFlow** | 26 个 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **AkShare** | 28 个 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Baostock** | 9 个 | ⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐ |

### 核心 API 对比

| API 功能 | EFinance | AkShare | Baostock | TickFlow | 最优数据源 |
|---------|----------|---------|----------|----------|-----------|
| **股票列表** | ✅ | ✅ | ✅ | ✅ | EFinance |
| **股票信息** | ✅ | ✅ | ✅ | ✅ | EFinance |
| **日 K 线** | ✅ | ✅ | ✅ | ✅ | EFinance |
| **周/月 K 线** | ✅ | ❌ | ❌ | ✅ | EFinance |
| **分钟 K 线** | ❌ | ❌ | ❌ | ✅ | TickFlow |
| **实时行情** | ✅ | ✅ | ⚠️ | ✅ | EFinance |
| **指数 K 线** | ⚠️(转 AkShare) | ✅ | ❌ | ✅ | AkShare |
| **板块列表** | ✅ | ✅ | ✅ | ✅ | EFinance |
| **板块成分** | ✅ | ✅ | ✅ | ✅ | EFinance |
| **资金流向** | ✅ | ⚠️ | ❌ | ✅ | EFinance |
| **龙虎榜** | ✅ | ⚠️ | ❌ | ✅ | EFinance |
| **股东人数** | ✅ | ✅ | ✅ | ✅ | EFinance |
| **前十大股东** | ✅ | ❌ | ❌ | ✅ | EFinance |
| **财务业绩** | ✅ | ⚠️ | ❌ | ✅ | EFinance |
| **基金数据** | ✅ | ✅ | ❌ | ❌ | EFinance |

**注**: 
- ✅ = 完整支持且性能好
- ⚠️ = 支持但性能一般
- ❌ = 不支持

---

## 🎯 场景化数据源优先级

### 场景 1：实时行情监控

**需求特点**：
- 高频查询（每秒多次）
- 低延迟要求（<1 秒）
- 数据准确性高
- 持续连接

**数据源优先级**：
```
1. EFinance     ⭐⭐⭐⭐⭐ (1-2 秒，实时性强，无限制)
2. TickFlow     ⭐⭐⭐⭐⭐ (0.5-1 秒，需 API Key)
3. AkShare      ⭐⭐⭐   (5-10 秒，限流)
4. Baostock     ⭐      (不支持实时)
```

**推荐配置**：
```python
# 实时行情场景
REALTIME_SCENARIO_CONFIG = {
    "default_source": "efinance",
    "priority": ["efinance", "tickflow", "akshare"],
    "exclude": ["baostock"],
    "cache_ttl": 10,  # 10 秒缓存
    "rate_limit": 5   # 每秒 5 次
}
```

---

### 场景 2：历史 K 线回测

**需求特点**：
- 大批量数据（数年历史）
- 数据完整性要求高
- 复权数据准确
- 可接受较慢速度

**数据源优先级**：
```
日线/周线/月线：
1. EFinance     ⭐⭐⭐⭐⭐ (支持前/后复权，速度快)
2. AkShare      ⭐⭐⭐⭐  (历史数据全，速度慢)
3. Baostock     ⭐⭐⭐⭐  (数据准确，仅日线)
4. TickFlow     ⭐⭐⭐⭐  (质量好，需 API Key)

分钟线：
1. TickFlow     ⭐⭐⭐⭐⭐ (唯一支持分钟线)
2. AkShare      ⭐⭐⭐   (部分支持)
3. EFinance     ❌      (不支持)
```

**推荐配置**：
```python
# 日线回测场景
DAILY_BACKTEST_CONFIG = {
    "default_source": "efinance",
    "priority": ["efinance", "akshare", "baostock", "tickflow"],
    "cache_ttl": 300,  # 5 分钟缓存
    "batch_size": 100  # 批量获取
}

# 分钟线回测场景
MINUTE_BACKTEST_CONFIG = {
    "default_source": "tickflow",
    "priority": ["tickflow", "akshare"],
    "require_api_key": True,
    "cache_ttl": 60
}
```

---

### 场景 3：指数数据分析

**需求特点**：
- 指数 K 线历史
- 成分股数据
- 指数实时行情

**数据源优先级**：
```
指数 K 线：
1. AkShare      ⭐⭐⭐⭐⭐ (指数数据最强项)
2. TickFlow     ⭐⭐⭐⭐  (质量好，需 API Key)
3. EFinance     ⚠️      (自动转 AkShare)
4. Baostock     ❌      (不支持)

指数成分股：
1. EFinance     ⭐⭐⭐⭐⭐ (get_members 接口)
2. TickFlow     ⭐⭐⭐⭐  (完整支持)
3. AkShare      ⭐⭐⭐   (支持)
```

**推荐配置**：
```python
# 指数分析场景
INDEX_ANALYSIS_CONFIG = {
    "kline_source": "akshare",  # K 线强制用 AkShare
    "component_source": "efinance",  # 成分股用 EFinance
    "priority": ["akshare", "efinance", "tickflow"],
    "exclude": ["baostock"]
}
```

---

### 场景 4：财务数据分析

**需求特点**：
- 财务指标完整
- 历史报告期准确
- 数据可比性强

**数据源优先级**：
```
1. EFinance     ⭐⭐⭐⭐⭐ (财务业绩接口完整)
2. TickFlow     ⭐⭐⭐⭐  (专业数据，需 API Key)
3. AkShare      ⭐⭐⭐   (支持但复杂)
4. Baostock     ❌      (不支持)
```

**推荐配置**：
```python
# 财务分析场景
FINANCIAL_ANALYSIS_CONFIG = {
    "default_source": "efinance",
    "priority": ["efinance", "tickflow", "akshare"],
    "exclude": ["baostock"],
    "cache_ttl": 3600  # 1 小时缓存（财务数据变化少）
}
```

---

### 场景 5：资金流向监控

**需求特点**：
- 实时主力净流入
- 历史资金流向
- 龙虎榜数据

**数据源优先级**：
```
1. EFinance     ⭐⭐⭐⭐⭐ (东方财富数据最准确)
2. TickFlow     ⭐⭐⭐⭐  (完整支持，需 API Key)
3. AkShare      ⭐⭐    (支持但限流)
4. Baostock     ❌      (不支持)
```

**推荐配置**：
```python
# 资金流向场景
CAPITAL_FLOW_CONFIG = {
    "default_source": "efinance",
    "priority": ["efinance", "tickflow"],
    "exclude": ["baostock", "akshare"],
    "cache_ttl": 60,  # 1 分钟缓存（实时性强）
    "real_time": True
}
```

---

### 场景 6：板块分析

**需求特点**：
- 行业/概念板块列表
- 板块成分股
- 板块实时行情

**数据源优先级**：
```
1. EFinance     ⭐⭐⭐⭐⭐ (板块数据最丰富)
2. AkShare      ⭐⭐⭐⭐  (支持东方财富板块)
3. TickFlow     ⭐⭐⭐⭐  (完整支持)
4. Baostock     ⭐⭐    (基础支持)
```

**推荐配置**：
```python
# 板块分析场景
SECTOR_ANALYSIS_CONFIG = {
    "default_source": "efinance",
    "priority": ["efinance", "akshare", "tickflow"],
    "cache_ttl": 300  # 5 分钟缓存
}
```

---

### 场景 7：龙虎榜监控

**需求特点**：
- 每日龙虎榜名单
- 上榜原因
- 买卖金额

**数据源优先级**：
```
1. EFinance     ⭐⭐⭐⭐⭐ (数据完整、实时)
2. TickFlow     ⭐⭐⭐⭐  (完整支持)
3. AkShare      ⭐⭐    (支持但限流)
4. Baostock     ❌      (不支持)
```

**推荐配置**：
```python
# 龙虎榜场景
BILLBOARD_CONFIG = {
    "default_source": "efinance",
    "priority": ["efinance", "tickflow"],
    "exclude": ["baostock"],
    "cache_ttl": 300,  # 5 分钟缓存
    "update_time": "16:00"  # 盘后更新
}
```

---

### 场景 8：股东筹码分析

**需求特点**：
- 股东人数变化
- 前十大股东
- 持仓变化

**数据源优先级**：
```
1. EFinance     ⭐⭐⭐⭐⭐ (股东数据最完整)
2. TickFlow     ⭐⭐⭐⭐  (完整支持)
3. AkShare      ⭐⭐⭐   (支持)
4. Baostock     ⭐⭐    (基础支持)
```

**推荐配置**：
```python
# 股东筹码场景
CHIP_ANALYSIS_CONFIG = {
    "default_source": "efinance",
    "priority": ["efinance", "tickflow", "akshare"],
    "cache_ttl": 600  # 10 分钟缓存
}
```

---

### 场景 9：基金数据分析

**需求特点**：
- 基金基本信息
- 基金净值
- 基金持仓

**数据源优先级**：
```
1. EFinance     ⭐⭐⭐⭐⭐ (基金接口最完整)
2. AkShare      ⭐⭐⭐⭐  (支持多种基金)
3. TickFlow     ❌      (不支持基金)
4. Baostock     ❌      (不支持)
```

**推荐配置**：
```python
# 基金分析场景
FUND_ANALYSIS_CONFIG = {
    "default_source": "efinance",
    "priority": ["efinance", "akshare"],
    "exclude": ["tickflow", "baostock"],
    "cache_ttl": 300
}
```

---

### 场景 10：港股/美股数据

**需求特点**：
- 全球市场覆盖
- 实时行情
- 历史数据

**数据源优先级**：
```
1. TickFlow     ⭐⭐⭐⭐⭐ (支持全球市场)
2. EFinance     ⭐⭐⭐   (支持部分)
3. AkShare      ⭐⭐⭐   (支持但慢)
4. Baostock     ❌      (仅 A 股)
```

**推荐配置**：
```python
# 港股/美股场景
GLOBAL_MARKET_CONFIG = {
    "default_source": "tickflow",
    "priority": ["tickflow", "efinance", "akshare"],
    "require_api_key": True,
    "exclude": ["baostock"]
}
```

---

### 场景 11：批量数据获取

**需求特点**：
- 多只股票同时查询
- 高效率
- 避免限流

**数据源优先级**：
```
批量 K 线：
1. EFinance     ⭐⭐⭐⭐⭐ (get_multi_kline 接口)
2. TickFlow     ⭐⭐⭐⭐  (批量接口)
3. AkShare      ⭐⭐    (限流)
4. Baostock     ⭐⭐    (循环查询慢)

批量实时行情：
1. EFinance     ⭐⭐⭐⭐⭐ (get_latest_quote 接口)
2. TickFlow     ⭐⭐⭐⭐  (批量接口)
3. AkShare      ⭐⭐    (限流)
```

**推荐配置**：
```python
# 批量查询场景
BATCH_QUERY_CONFIG = {
    "default_source": "efinance",
    "priority": ["efinance", "tickflow"],
    "batch_size": 50,  # 每批 50 只
    "concurrent_limit": 5,  # 最多 5 个并发
    "cache_ttl": 60
}
```

---

### 场景 12：开发调试

**需求特点**：
- 免费使用
- 快速响应
- 无限制

**数据源优先级**：
```
1. EFinance     ⭐⭐⭐⭐⭐ (完全免费，快速)
2. AkShare      ⭐⭐⭐   (免费但慢)
3. Baostock     ⭐⭐⭐   (免费稳定)
4. TickFlow     ⭐⭐    (需 API Key，有额度限制)
```

**推荐配置**：
```python
# 开发调试场景
DEVELOPMENT_CONFIG = {
    "default_source": "efinance",
    "priority": ["efinance", "akshare", "baostock"],
    "exclude": ["tickflow"],  # 开发环境不依赖付费服务
    "cache_ttl": 60  # 短缓存，快速看到变化
}
```

---

## 🔄 动态数据源切换策略

### 基于时间的切换

```python
# 交易时段 vs 非交易时段
TRADING_HOUR_CONFIG = {
    "trading_hours": {
        "priority": ["efinance", "tickflow", "akshare"],
        "cache_ttl": 30,  # 交易时段短缓存
    },
    "after_hours": {
        "priority": ["efinance", "baostock", "akshare"],
        "cache_ttl": 300,  # 非交易时段长缓存
    }
}

# 交易时段：9:30-11:30, 13:00-15:00
```

### 基于负载的切换

```python
# 根据数据源响应时间动态调整
ADAPTIVE_CONFIG = {
    "response_time_threshold": 3.0,  # 3 秒阈值
    "success_rate_threshold": 0.95,  # 95% 成功率
    "auto_switch": True,  # 自动切换
    "health_check_interval": 60  # 60 秒健康检查
}
```

### 基于数据类型的切换

```python
# 不同数据类型使用不同数据源
DATA_TYPE_CONFIG = {
    "kline_daily": "efinance",
    "kline_minute": "tickflow",
    "kline_index": "akshare",
    "realtime_quote": "efinance",
    "financial_data": "efinance",
    "fund_data": "efinance",
    "global_market": "tickflow"
}
```

---

## 📈 推荐的默认配置

### 通用场景（推荐）

```python
# .env 配置
DEFAULT_DATA_SOURCE=efinance
DATA_SOURCE_PRIORITY=["efinance","akshare","baostock","tickflow"]

# 适用场景：
# - 日常开发
# - 一般查询
# - 混合数据类型
```

**优势**：
- ✅ 完全免费（EFinance + AkShare + Baostock）
- ✅ 覆盖全面（95%+ 需求）
- ✅ 响应快速
- ✅ 稳定性好

### 专业场景（有 TickFlow API Key）

```python
# .env 配置
DEFAULT_DATA_SOURCE=tickflow
DATA_SOURCE_PRIORITY=["tickflow","efinance","akshare","baostock"]
TICKFLOW_API_KEY=your_api_key

# 适用场景：
# - 专业研究
# - 港股美股
# - 分钟线回测
# - 高质量数据需求
```

**优势**：
- ✅ 数据质量最高
- ✅ 全球市场覆盖
- ✅ 分钟线支持
- ⚠️ 成本可控（付费）

---

## 🎯 场景化 API 路由优化

### 按场景路由

```python
# 在 API 层根据场景自动选择数据源

# 1. 实时行情接口
@router.get("/realtime/{code}")
async def get_realtime(code: str):
    # 自动使用 EFinance（最快）
    return await data_source_manager.get_realtime_quote(
        code=code,
        source_type="efinance"
    )

# 2. 指数 K 线接口
@router.get("/index/{code}/kline")
async def get_index_kline(code: str):
    # 自动使用 AkShare（指数数据最强）
    return await data_source_manager.get_market_index_kline(
        index_code=code,
        source_type="akshare"
    )

# 3. 财务数据接口
@router.get("/stock/{code}/financial")
async def get_financial(code: str):
    # 自动使用 EFinance（财务数据完整）
    return await data_source_manager.get_financial_performance(
        code=code,
        source_type="efinance"
    )

# 4. 分钟线接口
@router.get("/stock/{code}/kline/minute")
async def get_minute_kline(code: str):
    # 自动使用 TickFlow（唯一支持分钟线）
    return await data_source_manager.get_kline(
        code=code,
        source_type="tickflow",
        period="minute"
    )
```

---

## 💡 最佳实践建议

### 1. 数据源预热

```python
# 启动时预热常用数据源
async def warmup_data_sources():
    # 预热 EFinance（主力）
    await efinance_adapter.get_stock_list()
    
    # 预热 AkShare（指数备用）
    await akshare_adapter.get_market_index_kline("000001")
    
    # 预热 TickFlow（如果有 API Key）
    if settings.TICKFLOW_API_KEY:
        await tickflow_adapter.get_instruments(["600000.SH"])
```

### 2. 智能缓存策略

```python
# 根据数据变化频率设置缓存
CACHE_STRATEGY = {
    "realtime_quote": 10,      # 实时行情：10 秒
    "kline_daily": 300,        # 日 K 线：5 分钟
    "kline_minute": 30,        # 分钟 K 线：30 秒
    "stock_info": 600,         # 股票信息：10 分钟
    "financial_data": 3600,    # 财务数据：1 小时
    "sector_list": 1800,       # 板块列表：30 分钟
    "fund_data": 300           # 基金数据：5 分钟
}
```

### 3. 故障转移优化

```python
# 智能故障转移（考虑数据类型）
async def get_data_with_smart_fallback(data_type, **kwargs):
    # 根据数据类型选择故障转移链
    if data_type == "index_kline":
        priority = ["akshare", "tickflow", "efinance"]
    elif data_type == "minute_kline":
        priority = ["tickflow", "akshare"]
    elif data_type == "realtime":
        priority = ["efinance", "tickflow", "akshare"]
    else:
        priority = ["efinance", "akshare", "baostock", "tickflow"]
    
    # 按优先级尝试
    for source in priority:
        try:
            return await get_data(source, data_type, **kwargs)
        except Exception as e:
            logger.warning(f"{source} 失败，尝试下一个")
            continue
    
    raise Exception("所有数据源均失败")
```

### 4. 性能监控

```python
# 监控各数据源性能
MONITORING_CONFIG = {
    "metrics": [
        "response_time",
        "success_rate",
        "data_quality",
        "cache_hit_rate"
    ],
    "report_interval": 300,  # 5 分钟报告
    "alert_threshold": {
        "response_time": 5.0,  # 超过 5 秒告警
        "success_rate": 0.90   # 低于 90% 告警
    }
}
```

---

## 📊 总结

### 数据源定位总结

| 数据源 | 主力场景 | 补充场景 | 保底场景 |
|--------|---------|---------|---------|
| **EFinance** | 实时行情、财务分析、资金流向、板块分析 | 批量查询、开发调试 | - |
| **AkShare** | 指数 K 线、长期回测 | 分钟线（部分） | EFinance 失败时 |
| **Baostock** | - | 盘后分析 | 所有场景保底 |
| **TickFlow** | 分钟线、港股美股、专业研究 | 高质量数据需求 | - |

### 核心建议

1. **日常使用 EFinance** ⭐⭐⭐⭐⭐
   - 80% 场景首选
   - 免费、快速、全面

2. **指数数据用 AkShare** ⭐⭐⭐⭐⭐
   - 专业的人做专业的事
   - 指数数据最强

3. **分钟线用 TickFlow** ⭐⭐⭐⭐⭐
   - 唯一选择（需 API Key）

4. **Baostock 做保底** ⭐⭐⭐
   - 确保系统可用性

5. **智能切换** ⭐⭐⭐⭐⭐
   - 根据场景自动选择
   - 用户体验最优

---

**文档更新日期**: 2026-03-27  
**适用版本**: v2.0+
