# akshare 反风控 - 快速参考

## 🎯 核心功能速查

### 1. User-Agent 轮换
```python
# 自动轮换（每次请求）
ua = adapter._rotate_user_agent()

# 获取本地 UA
local_ua = adapter._get_local_user_agent()

# 配置池：12 种浏览器（Chrome/Edge/Firefox/Safari）
```

### 2. 自适应延迟
```python
# 时间段自动调整
- 交易时段：2-4 秒
- 盘后时段：1-2 秒
- 夜间：0.5-1.5 秒

# 失败时自动增加延迟（最多 +5 秒）
```

### 3. 失败统计
```python
# 记录请求
adapter.record_request_success()
adapter.record_request_failure()

# 获取统计
stats = adapter.get_stats()
# {success_rate, consecutive_failures, ...}
```

### 4. 自定义设置
```python
# 启用/禁用自适应延迟
adapter.enable_adaptive_delay(True/False)

# 设置自定义延迟
adapter.set_custom_delay(min, max)
```

## 📊 时间段与延迟

| 时间段 | 时间范围 | 延迟 | 说明 |
|-------|---------|------|------|
| 交易时段 | 9:30-11:30, 13:00-15:00 | 2-4 秒 | 风控严格 |
| 盘后时段 | 15:00-22:00 | 1-2 秒 | 中等 |
| 夜间 | 22:00-9:30 | 0.5-1.5 秒 | 风控宽松 |

## 🔧 常用配置

### 保守模式（高频请求）
```python
adapter.set_custom_delay(3.0, 5.0)
adapter._max_retries = 5
```

### 平衡模式（推荐）
```python
adapter.enable_adaptive_delay(True)
adapter._max_retries = 3
```

### 激进模式（非交易时段）
```python
adapter.set_custom_delay(0.5, 1.0)
adapter._max_retries = 2
```

## 📈 监控指标

### 关键指标
```python
stats = adapter.get_stats()
print(f"成功率：{stats['success_rate']}")
print(f"连续失败：{stats['consecutive_failures']}")
print(f"当前延迟：{stats['current_delay_range']}")
```

### 告警阈值
| 指标 | 警告 | 处理方案 |
|-----|------|---------|
| 成功率 < 90% | 增加延迟 | `adapter.set_custom_delay(3.0, 5.0)` |
| 连续失败 ≥ 3 次 | 切换 IP | 暂停请求或切换代理 |
| 延迟 > 5 秒 | 降低频率 | 暂停请求 |

## 🚨 故障处理

### 返回空数据
```python
# 1. 增加延迟
adapter.set_custom_delay(3.0, 5.0)

# 2. 暂停请求
await asyncio.sleep(1800)  # 30 分钟
```

### 连续失败
```python
# 1. 查看统计
stats = adapter.get_stats()
print(stats)

# 2. 增加重试
adapter._max_retries = 5

# 3. 降低频率
adapter.enable_adaptive_delay(True)
```

## 💡 最佳实践

### ✅ 推荐
```python
# 1. 批量获取（减少请求次数）
stocks = await adapter.get_stock_list()

# 2. 利用缓存
stocks = await adapter.get_stock_list()  # 30 分钟内缓存

# 3. 监控统计
stats = adapter.get_stats()
if float(stats['success_rate'].rstrip('%')) < 90:
    logger.warning("调整策略")
```

### ❌ 避免
```python
# 1. 交易时段高频请求
for code in codes:  # ❌
    await adapter.get_stock_info(code)

# 2. 固定间隔请求
time.sleep(1)  # ❌ 固定 1 秒

# 3. 无缓存重复查询
while True:
    await adapter.get_stock_list()  # ❌
```

## 🧪 测试命令

```bash
# 运行反风控测试
python test_akshare_anti_crawling.py
```

## 📖 完整文档

- [优化建议](./AKSHARE_ANTI_CRAWLING_SUGGESTIONS.md)
- [实现总结](./AKSHARE_IMPLEMENTATION_COMPLETE.md)
- [efinance 参考](./EFINANCE_QUICK_REFERENCE.md)

## 🎯 快速示例

```python
from app.adapters.akshare_adapter import AkShareAdapter

# 初始化
adapter = AkShareAdapter()
await adapter.initialize()

# 获取股票列表（带缓存和频率控制）
stocks = await adapter.get_stock_list()

# 查看统计
stats = adapter.get_stats()
print(f"成功率：{stats['success_rate']}")

# 自定义延迟
adapter.set_custom_delay(2.0, 3.0)

# 启用自适应延迟
adapter.enable_adaptive_delay(True)
```

---

**提示**：建议保存此文件作为日常开发参考！
