# AntiWindFacade 快速参考

## 一、快速开始

### 1.1 导入

```python
from app.adapters.anti_wind import (
    AntiWindFacade,
    BASIC_CONFIG,      # 基础配置
    STANDARD_CONFIG,   # 标准配置（推荐）
    FULL_CONFIG,       # 完整配置
    HEADLESS_CONFIG,   # 无浏览器模式
    BROWSER_CONFIG,    # 浏览器模式
)
```

### 1.2 基本使用

```python
# 创建实例
facade = AntiWindFacade(STANDARD_CONFIG)

# 执行请求
async def fetch():
    # 你的请求逻辑
    return response

result = await facade.execute_with_strategies(
    request_func=fetch,
    url="https://www.eastmoney.com",
    method="GET"
)
```

## 二、配置模板选择

| 模板 | 适用场景 | 包含策略 |
|------|---------|---------|
| **BASIC_CONFIG** | 快速测试 | Cookie + 限流 + 重试 |
| **STANDARD_CONFIG** ⭐ | 日常使用 | Cookie + TLS + UA + 限流 + 重试 |
| **FULL_CONFIG** | 高危 API | 所有策略 |
| **HEADLESS_CONFIG** | HTTP 请求 | Cookie + TLS + 限流 + 重试 |
| **BROWSER_CONFIG** | Playwright | Cookie + 限流 + 重试 + 验证码 |

## 三、策略分层

```
L1: CookieInjectStrategy    (认证)
L2: TLSFingerprintStrategy  (伪装)
    UARotatorStrategy
L3: RateLimitStrategy       (限流)
L4: SmartRetryStrategy      (重试)
L5: ProxyPoolStrategy       (扩展)
    CaptchaHandlerStrategy
```

## 四、常用 API

### 4.1 策略管理

```python
# 启用/禁用策略
facade.enable_strategy('UARotatorStrategy')
facade.disable_strategy('TLSFingerprintStrategy')

# 获取策略实例
strategy = facade.get_strategy('CookieInjectStrategy')

# 查看状态
facade.print_status()
status = facade.get_strategy_status()
```

### 4.2 配置管理

```python
# 更新配置
facade.update_config({
    'min_delay': 2.0,
    'max_delay': 5.0,
})

# 重置状态
facade.reset()
```

### 4.3 层级管理

```python
# 获取某层策略
l2_strategies = facade.get_layer_strategies(2)

# 查看分层结构
layers = facade.get_strategy_by_layer()
```

## 五、典型场景

### 5.1 适配器中使用

```python
class MyAdapter:
    def __init__(self):
        self.anti_wind = AntiWindFacade(STANDARD_CONFIG)
    
    async def get_data(self, symbol: str):
        async def fetch():
            # 请求逻辑
            pass
        
        return await self.anti_wind.execute_with_strategies(
            request_func=fetch,
            url=f"https://example.com/{symbol}"
        )
```

### 5.2 服务层中使用

```python
class MyService:
    def __init__(self):
        config = {
            **STANDARD_CONFIG,
            'min_delay': 2.0,  # 更保守
            'max_delay': 5.0,
        }
        self.anti_wind = AntiWindFacade(config)
```

### 5.3 动态调整

```python
# 触发限流时
facade.disable_strategy('UARotatorStrategy')
facade.update_config({
    'min_delay': 5.0,
    'max_delay': 10.0,
})

# 恢复正常
facade.enable_strategy('UARotatorStrategy')
facade.update_config({
    'min_delay': 1.0,
    'max_delay': 3.0,
})
```

### 5.4 Cookie 管理

```python
cookie_strategy = facade.get_strategy('CookieInjectStrategy')

# 设置 Cookie
cookie_strategy.set_cookie('key', 'value')

# 获取 Cookie
value = cookie_strategy.get_cookie('key')

# 清空 Cookie
cookie_strategy.clear_cookies()
```

## 六、错误处理

```python
try:
    result = await facade.execute_with_strategies(...)
except Exception as e:
    # 降级策略
    facade.disable_strategy('TLSFingerprintStrategy')
    
    # 重试
    result = await facade.execute_with_strategies(...)
```

## 七、最佳实践

### 7.1 配置选择

- ✅ **日常使用**: STANDARD_CONFIG
- ✅ **高危 API**: FULL_CONFIG
- ✅ **浏览器自动化**: BROWSER_CONFIG
- ⚠️ **生产环境**: 根据实际情况调整延迟参数

### 7.2 策略调优

```python
# 交易时段（9:30-15:00）
config = {
    **STANDARD_CONFIG,
    'min_delay': 2.0,
    'max_delay': 5.0,
}

# 非交易时段
config = {
    **STANDARD_CONFIG,
    'min_delay': 1.0,
    'max_delay': 3.0,
}
```

### 7.3 Cookie 更新

```python
# 检查 Cookie 过期
from datetime import datetime

cookie_strategy = facade.get_strategy('CookieInjectStrategy')
if cookie_strategy._cookies_updated_at:
    age = (datetime.now() - cookie_strategy._cookies_updated_at).days
    if age > 5:
        logger.warning("Cookie 即将过期，请更新")
```

## 八、调试技巧

```python
# 1. 查看策略状态
facade.print_status()

# 2. 查看分层
layers = facade.get_strategy_by_layer()
print(layers)

# 3. 禁用所有策略（排查问题）
for strategy in facade.strategies:
    strategy.disable()

# 4. 逐个启用策略
facade.enable_strategy('CookieInjectStrategy')
# 测试...
facade.enable_strategy('TLSFingerprintStrategy')
# 测试...
```

## 九、完整示例

```python
from app.adapters.anti_wind import AntiWindFacade, STANDARD_CONFIG

class StockAdapter:
    def __init__(self):
        self.anti_wind = AntiWindFacade(STANDARD_CONFIG)
    
    async def get_stock_info(self, symbol: str) -> dict:
        """获取股票信息"""
        async def fetch():
            # 实际请求逻辑
            response = await session.get(
                f"https://quote.eastmoney.com/{symbol}.html"
            )
            return response.json()
        
        return await self.anti_wind.execute_with_strategies(
            request_func=fetch,
            url=f"https://quote.eastmoney.com/{symbol}.html",
            method="GET"
        )

# 使用
adapter = StockAdapter()
info = await adapter.get_stock_info("sz000001")
```

## 十、常见问题

### Q1: 如何选择配置模板？
**A**: 从 STANDARD_CONFIG 开始，根据反爬强度调整。

### Q2: 如何禁用某个策略？
**A**: `facade.disable_strategy('策略名')`

### Q3: 如何调整请求频率？
**A**: `facade.update_config({'min_delay': 2.0, 'max_delay': 5.0})`

### Q4: Cookie 过期了怎么办？
**A**: 重新抓取 Cookie 并保存到 `data/cookies/eastmoney_com_manual.json`

### Q5: 如何查看日志？
**A**: 策略执行会自动记录日志，级别：DEBUG → INFO → WARNING → ERROR

---

**版本**: v2.0  
**更新**: 2026-04-09  
**文档**: [OPTIMIZATION_PLAN.md](OPTIMIZATION_PLAN.md) - 完整优化方案
