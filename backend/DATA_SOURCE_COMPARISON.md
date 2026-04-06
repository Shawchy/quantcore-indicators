# 数据源选择说明

## 问题描述

之前代码中存在两次同步：
1. 从 akshare 获取股票列表
2. 清空数据库
3. 从 Baostock 获取股票列表

这种逻辑存在问题，需要统一数据源。

## 数据源对比

### Baostock - query_stock_basic()

**返回字段（7 个）：**
| 序号 | 字段 | 说明 | 示例 |
|------|------|------|------|
| 0 | code | 证券代码 | sh.000001 |
| 1 | code_name | 证券名称 | 平安银行 |
| 2 | ipoDate | 上市日期 | 1991-07-15 |
| 3 | outDate | 退市日期 | (空或日期) |
| 4 | type | 证券类型 | 1(股票), 2(指数) |
| 5 | status | 上市状态 | 1(上市), 0(退市) |

**优势：**
- ✅ 字段完整（包含 type, status, list_date, delist_date）
- ✅ 数据稳定（官方数据源，不反爬）
- ✅ 区分证券类型（股票、指数、可转债、ETF 等）
- ✅ 区分上市状态（上市、退市）
- ✅ 包含上市和退市日期

**劣势：**
- ❌ 不提供实时行情
- ❌ 不提供行业、板块、地区信息

### Akshare - stock_zh_a_spot()

**返回字段（2+12 个）：**
| 类别 | 字段 | 说明 |
|------|------|------|
| **基础** | code | 股票代码 |
| | name | 股票名称 |
| **实时行情** | 最新价、涨跌幅、涨跌额 | 价格相关 |
| | 成交量、成交额、振幅 | 成交相关 |
| | 换手率、市盈率、市净率 | 指标相关 |
| | 总市值、流通市值 | 市值相关 |

**缺失字段：**
- ❌ 无上市日期 (list_date)
- ❌ 无退市日期 (delist_date)
- ❌ 无证券类型 (type)
- ❌ 无上市状态 (status)

**优势：**
- ✅ 提供实时行情数据
- ✅ 字段丰富（实时数据）

**劣势：**
- ❌ 基础信息不完整（只有 code 和 name）
- ❌ 接口不稳定（频繁反爬）
- ❌ 数据质量差（第三方聚合）
- ❌ 无法区分证券类型和状态

## 字段对比表

| 字段 | Baostock | Akshare | 重要性 |
|------|----------|---------|--------|
| code | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| name | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| market | ✅ (转换) | ✅ | ⭐⭐⭐⭐⭐ |
| type | ✅ | ❌ | ⭐⭐⭐⭐ |
| status | ✅ | ❌ | ⭐⭐⭐⭐ |
| list_date | ✅ | ❌ | ⭐⭐⭐⭐ |
| delist_date | ✅ | ❌ | ⭐⭐⭐ |
| industry | ❌ | ❌ | ⭐⭐⭐ |
| sector | ❌ | ❌ | ⭐⭐⭐ |
| area | ❌ | ❌ | ⭐⭐⭐ |
| total_shares | ❌ | ❌ | ⭐⭐⭐ |
| float_shares | ❌ | ❌ | ⭐⭐⭐ |
| 实时价格 | ❌ | ✅ | ⭐⭐⭐⭐ |

## 结论

### ✅ 股票基本信息同步：使用 Baostock

**理由：**
1. **字段更完整**：7 个核心字段 vs 2 个基础字段
2. **数据更稳定**：官方数据源，不反爬
3. **数据质量高**：直接来自交易所
4. **包含关键信息**：type, status, list_date, delist_date

**使用场景：**
- 首次同步股票列表
- 定期更新股票信息
- 新增股票上市
- 股票退市更新

### ✅ 实时行情获取：使用 Akshare（如果接口恢复）

**理由：**
1. **实时数据**：提供最新价格、涨跌幅等
2. **字段丰富**：成交量、换手率、市盈率等

**使用场景：**
- 盘中实时行情展示
- 股票筛选和排序
- 技术指标计算

## 实施方案

### 1. 统一使用 Baostock 同步基本信息

```python
# 正确做法
from app.services.stock_info_service import get_stock_info_service

service = get_stock_info_service()
await service.sync_all_stocks(clear_first=True)  # 首次同步
await service.sync_all_stocks(clear_first=False)  # 增量更新
```

### 2. 标记 Akshare get_stock_list 为废弃

已在 `akshare_adapter.py` 中添加废弃警告：
```python
async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
    """
    ⚠️ 注意：此方法已废弃，建议使用 Baostock 适配器获取股票列表
    Akshare 只提供 code 和 name 两个字段，缺少 type, status, list_date, delist_date 等关键字段
    """
    logger.warning("⚠️ akshare 适配器 get_stock_list 方法已废弃，建议使用 Baostock 适配器")
    # ... 保留代码以兼容旧版本
```

### 3. 删除重复同步逻辑

检查以下位置，确保只使用 Baostock：
- ✅ `app/services/stock_info_service.py` - 已使用 Baostock
- ✅ `app/adapters/baostock_adapter.py` - 主要数据源
- ⚠️ `app/adapters/akshare_adapter.py` - 已标记废弃

## 数据流程图

```
【基本信息同步】
Baostock API → BaostockAdapter → StockInfoService → Database
   (7 字段)      (标准化)        (清洗验证)        (持久化)

【实时行情获取】
Akshare API → AkshareAdapter → 实时行情展示
  (实时数据)    (转换处理)
```

## 常见问题

### Q: 为什么不使用 akshare 同步基本信息？

A: 
1. 字段不完整（缺少 type, status, list_date, delist_date）
2. 接口不稳定（频繁反爬）
3. 数据质量差（第三方聚合）
4. 无法区分证券类型（股票、指数、ETF 等）

### Q: Baostock 缺少行业信息怎么办？

A: 
- Baostock 确实不提供行业、板块、地区信息
- 等待 akshare 接口恢复后，可以作为补充数据源
- 或考虑使用 Tushare Pro 等付费数据源

### Q: 如何更新股票信息？

A: 
```bash
# 首次同步（清空数据库）
python -m app.services.stock_info_service --clear

# 增量更新（保留现有数据）
python -m app.services.stock_info_service
```

### Q: 实时行情怎么办？

A: 
- 等待 akshare 接口恢复
- 或使用其他实时数据源（如 Tushare、Wind 等）
- Baostock 不提供实时行情

## 总结

**基本信息同步：只用 Baostock** ✅
**实时行情获取：等待 akshare 恢复** ⏳
**行业信息补充：考虑其他数据源** ⏳

**不要重复同步！** 统一使用 Baostock 一次同步完成。
