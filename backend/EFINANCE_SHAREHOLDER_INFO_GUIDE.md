# efinance 前十大股东信息接口使用指南

## 接口说明

优化后的 `get_top10_stock_holder_info` 接口用于获取沪深市场指定股票的前十大流通股东信息，支持灵活指定获取前 N 大股东（1-10）。

## 接口签名

```python
async def get_top10_stock_holder_info(
    self, 
    code: str, 
    top: int = 4
) -> List[ShareholderInfo]:
    """获取前十大股东信息（支持指定获取前 top 个股东）
    
    Args:
        code: 股票代码
        top: 获取前 top 个股东，默认 4，可选 1-10
            - 4: 获取前 4 大流通股东（默认）
            - 10: 获取前 10 大流通股东
            - 1-10: 获取指定数量的股东
    
    Returns:
        前十大股东信息列表，包含：
        - code: 股票代码
        - report_date: 报告期（更新日期）
        - holder_code: 股东代码
        - holder_name: 股东名称
        - hold_amount: 持股数（股）
        - hold_ratio: 持股比例（%）
        - change: 增减描述（不变/新进/数值）
        - change_rate: 变动率（%）
    """
```

## 数据模型

```python
class ShareholderInfo(BaseModel):
    """股东信息"""
    code: str                    # 股票代码
    report_date: str             # 报告期/更新日期
    holder_code: str             # 股东代码
    holder_name: str             # 股东名称
    hold_amount: Optional[float] = None    # 持股数（股）
    hold_ratio: Optional[float] = None     # 持股比例（%）
    change: Optional[str] = None           # 增减描述（不变/新进/数值）
    change_rate: Optional[float] = None    # 变动率（%）
```

## 使用示例

### 1. 获取前 4 大流通股东（默认）

```python
import asyncio
from app.adapters.efinance_adapter import EFinanceAdapter

async def main():
    adapter = EFinanceAdapter()
    await adapter.initialize()
    
    # 获取贵州茅台前 4 大流通股东
    shareholders = await adapter.get_top10_stock_holder_info("600519")
    
    for shareholder in shareholders:
        print(f"股东名称：{shareholder.holder_name}")
        print(f"持股数：{shareholder.hold_amount}")
        print(f"持股比例：{shareholder.hold_ratio}%")
        print(f"增减：{shareholder.change}")
        print(f"变动率：{shareholder.change_rate}%")
        print("---")

asyncio.run(main())
```

### 2. 获取前 10 大流通股东

```python
# 获取全部前 10 大流通股东
shareholders = await adapter.get_top10_stock_holder_info("600519", top=10)
```

### 3. 获取前 1 大股东（控股股东）

```python
# 只获取第一大股东
shareholders = await adapter.get_top10_stock_holder_info("600519", top=1)
if shareholders:
    top_holder = shareholders[0]
    print(f"第一大股东：{top_holder.holder_name}")
    print(f"持股数：{top_holder.hold_amount} 股")
    print(f"持股比例：{top_holder.hold_ratio}%")
```

### 4. 获取前 5 大股东

```python
# 获取前 5 大股东
shareholders = await adapter.get_top10_stock_holder_info("300274", top=5)
```

## 输出示例

以贵州茅台（600519）为例：

```
股票代码：600519
报告期：2021-03-31

1. 中国贵州茅台酒厂 (集团) 有限责任公司
   股东代码：80010298
   持股数：6.783 亿股
   持股比例：54.00%
   增减：不变
   变动率：--

2. 香港中央结算有限公司
   股东代码：80637337
   持股数：9594 万股
   持股比例：7.64%
   增减：-841.1 万股
   变动率：-8.06%

3. 贵州省国有资本运营有限责任公司
   股东代码：80732941
   持股数：5700 万股
   持股比例：4.54%
   增减：-182.7 万股
   变动率：-3.11%

4. 贵州茅台酒厂集团技术开发公司
   股东代码：80010302
   持股数：2781 万股
   持股比例：2.21%
   增减：不变
   变动率：--
```

## 数据解析特性

### 1. 持股数解析

支持多种单位格式：
- **亿**：`6.783 亿` → `678300000` 股
- **万**：`9594 万` → `95940000` 股
- **纯数字**：`1234567` → `1234567.0` 股

### 2. 增减解析

支持多种情况：
- **不变**：持股数未变化
- **新进**：新进入前十大股东
- **数值**：`+1000000` 或 `-500000`（股）
- **带单位**：`-841.1 万` 或 `+1.2 亿`

### 3. 持股比例

统一解析为百分比数值（不带%符号）：
- `54.00%` → `54.00`
- `7.64%` → `7.64`

### 4. 变动率

统一解析为百分比数值：
- `-8.06%` → `-8.06`
- `11.48%` → `11.48`
- `--` 或 `不变` → `0.0`

## 反风控机制

### 1. 请求频率控制

- **自适应延迟**：根据时间段自动调整
  - 交易时段（9:30-15:00）：2-4 秒
  - 盘后时段（15:00-22:00）：1-2 秒
  - 夜间（22:00-9:30）：0.5-1.5 秒

- **失败重试**：根据连续失败次数增加延迟
  - 每失败一次，延迟增加 1 秒
  - 最多增加 5 秒

### 2. 请求头伪装

- **User-Agent 轮换**：12 种浏览器配置池
  - Chrome（Windows/macOS）
  - Edge（Windows）
  - Firefox（Windows/macOS）
  - Safari（macOS）

- **完整请求头**：模拟真实浏览器行为
  - Accept、Accept-Language
  - Referer（东方财富网）
  - Sec-Fetch 系列字段

### 3. 缓存机制

- **缓存时间**：10 分钟
- **缓存 Key**：包含股票代码和 top 参数
- **自动失效**：超时自动清除

### 4. 失败统计

- **连续失败计数**：自动跟踪
- **自动告警**：连续失败≥3 次时记录警告
- **自动调整**：失败时自动轮换 User-Agent

## 参数验证

```python
# 无效参数会自动使用默认值
await adapter.get_top10_stock_holder_info("600519", top=0)    # 警告，使用默认 4
await adapter.get_top10_stock_holder_info("600519", top=15)   # 警告，使用默认 4
await adapter.get_top10_stock_holder_info("600519", top="5")  # 警告，使用默认 4
```

## 错误处理

```python
try:
    shareholders = await adapter.get_top10_stock_holder_info("600519", top=10)
    if not shareholders:
        print("未获取到股东信息")
    else:
        print(f"成功获取 {len(shareholders)} 条股东信息")
except Exception as e:
    print(f"获取失败：{e}")
```

## 统计信息

```python
# 查看请求统计
stats = adapter.get_stats()
print(f"总请求数：{stats['total_requests']}")
print(f"失败次数：{stats['failed_requests']}")
print(f"成功率：{stats['success_rate']}")
print(f"连续失败：{stats['consecutive_failures']}")
```

## 与其他接口对比

| 接口 | 数据源 | 特点 | 用途 |
|------|--------|------|------|
| `get_top10_stock_holder_info` | efinance | 免费、实时、支持 top 参数 | 日常查询前十大股东 |
| Tushare 股东接口 | Tushare | 需要积分、数据质量高 | 专业研究、历史数据分析 |
| Wind/Choice | 付费终端 | 数据最全、最准确 | 机构级应用 |

## 注意事项

1. **数据更新频率**：
   - 仅在季报/年报披露后更新
   - 非定期报告期间数据不变

2. **流通股东 vs 总股本股东**：
   - 本接口返回的是**前十大流通股东**
   - 非前十大总股本股东

3. **数据完整性**：
   - 部分股东可能缺少持股数或比例
   - 返回 `None` 表示数据缺失

4. **单位转换**：
   - 所有持股数统一转换为**股**
   - 所有比例统一转换为**百分比数值**（不带%）

## 性能优化

### 1. 批量查询

```python
# 推荐：并发查询多只股票
tasks = [
    adapter.get_top10_stock_holder_info("600519", top=4),
    adapter.get_top10_stock_holder_info("300274", top=4),
    adapter.get_top10_stock_holder_info("002594", top=4),
]
results = await asyncio.gather(*tasks)
```

### 2. 利用缓存

```python
# 10 分钟内重复查询会命中缓存
result1 = await adapter.get_top10_stock_holder_info("600519", top=4)
result2 = await adapter.get_top10_stock_holder_info("600519", top=4)  # 缓存命中
```

## 总结

优化后的 `get_top10_stock_holder_info` 接口具有以下特点：

✅ **灵活参数**：支持获取前 1-10 大股东  
✅ **完整字段**：包含股东代码、名称、持股数、比例、增减、变动率  
✅ **智能解析**：自动处理'亿'、'万'、'%'等单位  
✅ **反风控保护**：频率控制、请求头伪装、缓存机制  
✅ **错误处理**：参数验证、失败重试、统计跟踪  
✅ **性能优化**：异步并发、本地缓存
