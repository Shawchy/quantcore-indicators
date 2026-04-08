# 数据时效性检查工具使用指南

## 概述

`DataFreshnessChecker` 提供统一的数据时效性检查机制，根据不同数据类型的更新频率要求，智能判断是否需要从数据源重新获取数据。

## 核心特性

1. **智能时效性判断**: 基于数据最后更新时间自动判断是否过期
2. **可配置策略**: 支持 12 种预定义数据类型，每种类型有不同的有效期
3. **灵活使用**: 支持类、函数、装饰器三种使用方式
4. **自动降级**: 数据过期时可自动获取新数据或使用旧数据

## 数据有效期策略

### 高频数据（交易时段内实时变化）
**交易时段特点**: 数据变化快，需要频繁更新
**非交易时段**: 使用最新数据，不强制更新

- `realtime_quote`: 实时行情 - **15 分钟**（交易时段）
- `tick_data`: 分时数据 - **15 分钟**（交易时段）

### 日频数据（每个交易日更新）
**交易时段特点**: 数据较快变化，需要较短有效期
**非交易时段/已收盘**: 使用最新数据

- `kline_daily`: 日 K 线 - **30 分钟**（交易时段）
- `market_turnover`: 市场成交额 - **15 分钟**（交易时段）
- `moneyflow`: 资金流向 - **15 分钟**（交易时段）
- `billboard`: 龙虎榜 - **30 分钟**（交易时段，盘后公布）

### 周频数据（每周更新）
- `kline_weekly`: 周 K 线 - **7 天**

### 月频数据（每月更新）
- `kline_monthly`: 月 K 线 - **30 天**

### 低频数据（季度/年度更新）
- `financial_report`: 财报 - **90 天**
- `stock_info`: 股票基本信息 - **30 天**

### 静态数据（很少变化）
- `stock_list`: 股票列表 - **90 天**
- `sector_info`: 板块信息 - **90 天**

## 使用方式

### 方式一：直接使用 DataFreshnessChecker 类

```python
from app.utils.data_freshness_checker import DataFreshnessChecker
from app.storage.sqlite import StockInfo, MarketTurnover

async def get_stock_data(session):
    checker = DataFreshnessChecker(session)
    
    # 检查股票信息（30 天有效期）
    data, is_stale = await checker.check_freshness(
        StockInfo, 
        'stock_info',
        filter_conditions={'code': '000001'}
    )
    
    if is_stale:
        # 数据过期，从数据源获取
        new_data = await fetch_from_api()
        await save_to_db(new_data)
        return new_data
    else:
        # 使用缓存数据
        return data
```

### 方式二：使用便捷函数

```python
from app.utils.data_freshness_checker import check_data_freshness

async def get_market_turnover(session):
    # 检查成交额数据（15 分钟有效期）
    data, is_stale = await check_data_freshness(
        session, 
        MarketTurnover, 
        'market_turnover'
    )
    
    if is_stale:
        # 获取新数据
        return await fetch_turnover_data()
    else:
        return data
```

### 方式三：使用装饰器

```python
from app.utils.data_freshness_checker import auto_refresh_data
from app.storage.sqlite import StockInfo

class StockService:
    @auto_refresh_data(StockInfo, 'stock_info', max_age_hours=24)
    async def get_stock_info(self, code: str, session=None):
        """
        获取股票信息，自动检查时效性
        数据过期时自动调用 get_stock_info_refresh
        """
        # 正常查询逻辑
        result = await session.execute(...)
        return result.scalar_one_or_none()
    
    async def get_stock_info_refresh(self, code: str, session=None):
        """刷新函数：从数据源获取最新数据"""
        # 从 API 获取最新数据
        data = await fetch_from_api(code)
        # 保存到数据库
        await save_to_db(data)
        return data
```

### 方式四：按日期检查（适用于日频数据）

```python
from app.utils.data_freshness_checker import DataFreshnessChecker
from app.storage.sqlite import DailyKline

async def get_daily_kline(session, trade_date: str):
    checker = DataFreshnessChecker(session)
    
    # 检查指定日期的 K 线数据
    data, is_stale = await checker.check_freshness_by_date(
        DailyKline,
        'kline_daily',
        date_field='trade_date',
        target_date=trade_date,
        custom_max_age_hours=24
    )
    
    if is_stale:
        # 获取新数据
        return await fetch_kline_from_api(trade_date)
    else:
        return data
```

## 自定义策略

### 临时覆盖有效期

```python
# 使用自定义有效期（覆盖默认策略）
data, is_stale = await checker.check_freshness(
    StockInfo,
    'stock_info',
    custom_max_age_hours=12  # 使用 12 小时而非默认的 30 天
)
```

### 添加新的数据类型

```python
from app.utils.data_freshness_checker import DataFreshnessPolicy

# 添加新的数据类型策略
DataFreshnessPolicy.POLICIES['custom_data'] = 48  # 48 小时有效期

# 使用新策略
data, is_stale = await checker.check_freshness(
    CustomTable,
    'custom_data'
)
```

## 返回值说明

### check_freshness 返回值

```python
data, is_stale = await checker.check_freshness(...)
```

- `data` (Dict | None): 最新的数据库记录
  - 包含所有字段数据
  - 包含 `_freshness` 元信息（时效性检查结果）
- `is_stale` (bool): 是否需要更新
  - `True`: 数据过期或不存在，需要获取新数据
  - `False`: 数据有效，可以使用缓存

### _freshness 元信息

```python
{
    'is_stale': True,           # 是否过期
    'age_hours': 25.5,          # 数据年龄（小时）
    'max_age_hours': 24,        # 最大允许年龄
    'update_time': '2024-01-01T12:00:00'  # 更新时间
}
```

## 实际应用示例

### 示例 1：市场统计数据 API

```python
@router.get("/market-stats")
async def get_market_statistics(session: AsyncSession = Depends(get_session)):
    from app.utils.data_freshness_checker import DataFreshnessChecker
    from app.storage.sqlite import MarketTurnover
    
    checker = DataFreshnessChecker(session)
    
    # 检查成交额数据（15 分钟有效期）
    turnover_data, is_stale = await checker.check_freshness(
        MarketTurnover,
        'market_turnover',
        custom_max_age_hours=0.25
    )
    
    if is_stale:
        # 从 akshare 获取新数据
        turnover_data = await fetch_from_akshare()
        await save_to_db(turnover_data)
    
    return {"turnover": turnover_data}
```

### 示例 2：实时行情服务

```python
class RealtimeQuoteService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.checker = DataFreshnessChecker(session)
    
    async def get_quote(self, code: str):
        from app.storage.sqlite import RealtimeQuote
        
        # 实时行情只有 15 分钟有效期（交易时段内）
        data, is_stale = await self.checker.check_freshness(
            RealtimeQuote,
            'realtime_quote',
            filter_conditions={'code': code}
        )
        
        if is_stale:
            # 从数据源获取最新行情
            quote = await self.fetch_quote_from_api(code)
            await self.save_quote(quote)
            return quote
        else:
            return data
```

### 示例 3：K 线数据服务

```python
class KlineService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.checker = DataFreshnessChecker(session)
    
    async def get_daily_kline(self, code: str, trade_date: str):
        from app.storage.sqlite import DailyKline
        
        # 按日期检查（日 K 线 30 分钟有效期，交易时段）
        data, is_stale = await self.checker.check_freshness_by_date(
            DailyKline,
            'kline_daily',
            date_field='trade_date',
            target_date=trade_date
        )
        
        if is_stale:
            # 获取新 K 线数据
            kline = await self.fetch_kline_from_api(code, trade_date)
            await self.save_kline(kline)
            return kline
        else:
            return data
```

## 最佳实践

### 最佳实践

### 1. 合理选择数据类型

根据数据的实际更新频率选择合适的类型：
- 实时行情 → `realtime_quote` (15 分钟，交易时段内)
- 日 K 线 → `kline_daily` (30 分钟，交易时段)
- 股票基本信息 → `stock_info` (30 天)

### 2. 优雅降级

数据获取失败时使用旧数据：

```python
data, is_stale = await checker.check_freshness(...)

if is_stale:
    try:
        new_data = await fetch_from_api()
        await save_to_db(new_data)
        return new_data
    except Exception as e:
        logger.warning(f"获取新数据失败，使用旧数据：{e}")
        if data:
            return data  # 使用旧数据
        raise
```

### 3. 日志记录

检查器会自动记录日志：
- `INFO`: 数据过期、获取新数据
- `DEBUG`: 数据有效
- `WARNING`: 数据无时间字段
- `ERROR`: 检查失败

### 4. 性能优化

- 使用装饰器自动检查，减少重复代码
- 批量检查多个数据时复用 checker 实例
- 合理设置有效期，避免频繁请求 API

## 策略配置查询

```python
from app.utils.data_freshness_checker import DataFreshnessPolicy

# 获取所有策略配置
policies = DataFreshnessPolicy.get_all_policies()

# 获取特定数据类型的有效期
max_age = DataFreshnessPolicy.get_max_age('market_turnover')  # 0.25 (15 分钟)

# 查看所有策略描述
info = DataFreshnessPolicy.get_policy_info()
print(info['descriptions'])
```

## 注意事项

1. **数据库表需要时间字段**: 表应该有 `created_at` 或 `updated_at` 字段
2. **时区处理**: 所有时间使用 UTC 或统一时区
3. **并发安全**: 多个请求同时检查时可能重复获取数据，可考虑加锁
4. **缓存配合**: 可与 Redis 等缓存配合，进一步减少数据库查询

## 故障排除

### 问题 1: 总是返回 is_stale=True

**原因**: 
- 数据表没有时间字段
- 数据年龄超过设置的有效期

**解决**:
```python
# 检查表结构，确保有 updated_at 或 created_at 字段

# 或者临时使用更长的有效期
data, is_stale = await checker.check_freshness(
    ..., custom_max_age_hours=720  # 30 天
)
```

### 问题 2: 装饰器不生效

**原因**:
- session 参数名称不匹配
- 刷新函数命名不正确

**解决**:
```python
# 确保 session 参数名为 'session'
@auto_refresh_data(StockInfo, 'stock_info')
async def get_stock_info(code: str, session=None):  # ✓
    pass

# 刷新函数命名：get_{data_type}_refresh
async def get_stock_info_refresh(self, code: str, session=None):
    pass
```

## 总结

数据时效性检查工具提供了：
- ✅ 统一的时效性检查机制
- ✅ 灵活的配置策略
- ✅ 多种使用方式
- ✅ 自动降级处理
- ✅ 详细的日志记录

在开发新 API 或服务时，优先使用此工具检查数据时效性，避免重复请求数据源，提高系统性能和响应速度。
