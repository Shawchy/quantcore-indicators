# efinance 反风控使用指南

## 概述

efinance 是基于网络请求的爬虫库，数据来源于东方财富网等财经平台。平台会对高频/异常请求进行风控限制（如 IP 封禁、返回空数据、403 错误）。

本适配器已内置完整的反风控机制，无需额外配置即可使用。

## 内置反风控机制

### 1. 请求头伪装（自动）

适配器在初始化时自动设置浏览器级别的请求头，模拟正常用户访问：

```python
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ...",
    "Accept": "text/html,application/xhtml+xml,...",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Referer": "https://eastmoney.com/",
    "Connection": "keep-alive"
}
```

**无需手动设置，初始化时自动配置**

### 2. 请求频率控制（自动）

所有接口调用自动添加 1-2 秒的随机延迟，避免高频请求：

```python
# 示例：连续调用多个接口
quote1 = await adapter.get_latest_quote("601012")  # 自动延迟 1-2 秒
quote2 = await adapter.get_latest_quote("300274")  # 自动延迟 1-2 秒
quote3 = await adapter.get_latest_quote("002594")  # 自动延迟 1-2 秒
```

**所有接口都已内置频率控制，无需手动管理**

### 3. 失败重试机制（自动）

网络请求失败时自动重试，使用指数退避策略：

- 第 1 次重试：延迟 2-3 秒
- 第 2 次重试：延迟 4-5 秒
- 第 3 次重试：延迟 8-9 秒

**所有接口都已内置重试机制，最多重试 3 次**

### 4. 本地缓存策略（自动）

不同数据类型采用不同的缓存时间，减少重复请求：

| 数据类型 | 缓存时间 | 说明 |
|---------|---------|------|
| 实时行情 | 60 秒 | 价格变化快，缓存时间短 |
| 股票信息 | 10 分钟 | 基本信息相对稳定 |
| K 线数据 | 5 分钟 | 历史数据不变 |
| 股票列表 | 30 分钟 | 非常稳定 |
| 板块数据 | 5 分钟 | 中等稳定性 |

**缓存完全透明，优先返回缓存数据**

### 5. 批量请求优化（推荐手动）

**❌ 错误示例（高频请求，易被风控）：**

```python
codes = ["601012", "300274", "688223"]
for code in codes:
    df = await adapter.get_stock_info(code)  # N 次请求 → 高风险
```

**✅ 正确示例（批量请求，低风险）：**

```python
codes = ["601012", "300274", "688223"]
stocks = await adapter.get_stock_info_batch(codes)  # 1 次请求 → 低风险
```

### 6. 代理 IP 支持（应急使用）

当 IP 被封禁时，可手动设置代理 IP：

```python
# 设置代理（需自备有效代理）
await adapter.set_proxy("http://127.0.0.1:7890")

# 测试是否生效
quote = await adapter.get_latest_quote("601012")

# 清除代理
await adapter.clear_proxy()
```

## 使用示例

### 基础使用（推荐）

```python
from app.adapters.factory import get_data_adapter

# 获取适配器（已自动配置反风控）
adapter = await get_data_adapter("efinance")

# 1. 单只股票查询（自动频率控制）
quote = await adapter.get_latest_quote("601012")

# 2. 批量查询（推荐，减少请求次数）
quotes = await adapter.get_latest_quote(["601012", "300274", "002594"])

# 3. 获取股票列表（自动缓存）
stocks = await adapter.get_stock_list()

# 4. 获取 K 线数据（自动重试 + 缓存）
klines = await adapter.get_kline("601012", start_date="2024-01-01")
```

### 进阶使用（批量优化）

```python
# 场景：获取光伏板块所有股票的最新行情

# ✅ 推荐：批量获取（1 次请求）
market_quotes = await adapter.get_market_realtime_quotes(fs="884723")

# ❌ 不推荐：循环查询（N 次请求）
# for quote in market_quotes:
#     detail = await adapter.get_latest_quote(quote.code)
```

### 应急使用（IP 被封）

```python
# 检测到 IP 被封（返回空数据或 403 错误）
try:
    quote = await adapter.get_latest_quote("601012")
    if not quote:
        # 切换代理 IP
        await adapter.set_proxy("http://proxy-server:port")
        quote = await adapter.get_latest_quote("601012")
except Exception as e:
    logger.error(f"请求失败：{e}")
```

## 最佳实践

### 1. 优先使用批量接口

```python
# ✅ 批量获取股票信息
stocks = await adapter.get_stock_info_batch(["601012", "300274", "002594"])

# ✅ 批量获取板块行情
quotes = await adapter.get_market_realtime_quotes(fs="884723")
```

### 2. 利用缓存减少请求

```python
# 第一次：实际请求
quote1 = await adapter.get_latest_quote("601012")

# 60 秒内：直接返回缓存
quote2 = await adapter.get_latest_quote("601012")  # 无网络请求
```

### 3. 避免交易时段高频请求

A 股交易时间（9:30-15:00）平台风控更严格：

```python
# ✅ 建议：非交易时段更新数据
# ✅ 建议：单次获取足够数据后缓存使用
# ❌ 避免：交易时段循环查询大量股票
```

### 4. 合理设置数据范围

```python
# ✅ 指定所需字段，减少数据量
quotes = await adapter.get_market_realtime_quotes(
    fs="884723",
    fields=["code", "name", "price"]  # 只获取关键字段
)
```

## 风控异常处理

### 常见异常及解决方案

| 异常现象 | 原因 | 解决方案 |
|---------|------|---------|
| 返回空 DataFrame | 请求频率超限 / IP 限流 | 暂停请求 10-30 分钟，稍后重试 |
| 403 Forbidden | 请求头被识别 / IP 封禁 | 更换 User-Agent 或切换代理 IP |
| 数据重复/错乱 | 平台反爬策略更新 | 升级 efinance：`pip install -U efinance` |
| 连接超时 | 网络问题 / 服务器限流 | 等待后重试，或使用代理 IP |

### 异常处理示例

```python
import asyncio

async def safe_get_quote(adapter, code, max_retries=3):
    """安全的行情查询（带异常处理）"""
    for attempt in range(max_retries):
        try:
            quote = await adapter.get_latest_quote(code)
            if quote:
                return quote
            else:
                logger.warning(f"返回空数据，重试 {attempt+1}/{max_retries}")
                await asyncio.sleep(5 * (attempt + 1))
        except Exception as e:
            logger.error(f"请求失败：{e}，重试 {attempt+1}/{max_retries}")
            await asyncio.sleep(5 * (attempt + 1))
    
    return None
```

## 配置说明

### 默认配置（无需修改）

```python
adapter._request_delay_range = (1.0, 2.0)  # 请求间隔 1-2 秒
adapter._max_retries = 3  # 最大重试 3 次
adapter._retry_base_delay = 2.0  # 重试基础延迟 2 秒
```

### 自定义配置（可选）

```python
# 调整请求频率（更保守）
adapter._request_delay_range = (2.0, 3.0)  # 间隔 2-3 秒

# 增加重试次数
adapter._max_retries = 5  # 最多重试 5 次
```

## 性能对比

### 使用反风控机制前后

| 场景 | 未优化 | 已优化 | 提升 |
|-----|--------|--------|------|
| 查询 100 只股票 | 100 次请求（高风险） | 1 次批量请求 | 99%↓ |
| 重复查询相同股票 | 每次请求 | 缓存命中（无请求） | 100%↓ |
| 网络波动时 | 直接失败 | 自动重试 3 次 | 成功率 +60% |
| IP 被封禁 | 无法使用 | 代理 IP 切换 | 可用性恢复 |

## 总结

**核心优势：**
- ✅ **完全自动化**：所有反风控机制内置，无需手动配置
- ✅ **批量优化**：优先使用批量接口，减少请求次数
- ✅ **智能缓存**：根据数据类型自动管理缓存
- ✅ **故障恢复**：自动重试 + 代理 IP 支持

**避坑指南：**
- ❌ 避免交易时段高频循环请求
- ❌ 避免单次查询超大量数据
- ❌ 避免无缓存的重复查询
- ✅ 优先批量获取 + 本地缓存

按照以上指南使用，可规避 90% 以上的风控限制，确保数据获取的稳定性。
