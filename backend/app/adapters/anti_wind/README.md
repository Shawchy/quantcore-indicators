# 反风控策略门面（优化版）

**版本**: v4.0 (优化版)  
**最后更新**: 2026-04-09  
**状态**: ✅ 已优化重构

---

## 📖 概述

AntiWindFacade 提供统一的反爬虫策略门面，使用**策略注册表**动态加载策略，符合开闭原则。

### 核心特性

- ✅ **策略注册表**: 动态加载策略，添加新策略无需修改 Facade
- ✅ **配置分离**: 每个策略只提取需要的配置，避免内存浪费
- ✅ **统一初始化**: 由 Facade 管理初始化时机，减少重复检查
- ✅ **性能优化**: 缓存启用的策略列表，减少遍历开销

### 策略分层架构

```
┌─────────────────────────────────────────┐
│         应用层 (Application)            │
│  AkShareAdapter, EFinanceAdapter, etc.  │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│      门面层 (Facade - AntiWindFacade)   │
│  统一入口，策略编排，执行控制            │
└─────────────────────────────────────────┘
                  ↓
┌─────────────────────────────────────────┐
│        策略层 (Strategy Layer)          │
├─────────────────────────────────────────┤
│  L1: CookieInjectStrategy    (认证)    │
│  L2: TLSFingerprintStrategy  (伪装)    │
│      UARotatorStrategy                 │
│  L3: RateLimitStrategy       (限流)    │
│  L4: SmartRetryStrategy      (重试)    │
│  L5: ProxyPoolStrategy       (扩展)    │
│      CaptchaHandlerStrategy            │
└─────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 基本使用

```python
from app.adapters.anti_wind import AntiWindFacade, STANDARD_CONFIG

# 创建实例
facade = AntiWindFacade(STANDARD_CONFIG)

# 执行请求
async def fetch(**kwargs):
    # 你的请求逻辑
    response = await session.get(kwargs['url'])
    return response

result = await facade.execute_with_strategies(
    request_func=fetch,
    url="https://www.eastmoney.com",
    method="GET"
)
```

### 2. 在适配器中使用

```python
from app.adapters.anti_wind import AntiWindFacade, STANDARD_CONFIG

class AkShareAdapter:
    def __init__(self):
        self.anti_wind = AntiWindFacade(STANDARD_CONFIG)
    
    async def get_stock_info(self, symbol: str) -> dict:
        """获取股票信息"""
        async def fetch(**kwargs):
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
```

---

## 📋 配置模板

### 预设配置

| 模板 | 适用场景 | 包含策略 |
|------|---------|---------|
| **BASIC_CONFIG** | 快速测试 | Cookie + 限流 + 重试 |
| **STANDARD_CONFIG** ⭐ | 日常使用 | Cookie + TLS + UA + 限流 + 重试 |
| **FULL_CONFIG** | 高危 API | 所有策略 |
| **HEADLESS_CONFIG** | HTTP 请求 | Cookie + TLS + 限流 + 重试 |
| **BROWSER_CONFIG** | Playwright | Cookie + 限流 + 重试 + 验证码 |

### 配置示例

```python
STANDARD_CONFIG = {
    # L1: 认证
    'enable_cookie_inject': True,
    
    # L2: 伪装
    'enable_tls_fingerprint': True,
    'impersonate': 'chrome120',
    'enable_ua_rotation': True,
    'rotation_interval': 10,
    
    # L3: 限流
    'enable_rate_limit': True,
    'min_delay': 1.0,
    'max_delay': 3.0,
    
    # L4: 重试
    'enable_smart_retry': True,
    'max_retries': 3,
}
```

---

## 🎯 核心 API

### Facade 方法

```python
facade = AntiWindFacade(STANDARD_CONFIG)

# 执行请求（带所有策略）
result = await facade.execute_with_strategies(
    request_func=fetch,
    url="https://example.com",
    method="GET"
)

# 策略管理
facade.enable_strategy('UARotatorStrategy')
facade.disable_strategy('TLSFingerprintStrategy')
strategy = facade.get_strategy('CookieInjectStrategy')

# 查看状态
facade.print_status()
enabled = facade.get_enabled_strategies()
status = facade.get_strategy_status()

# 配置管理
facade.update_config({'min_delay': 2.0, 'max_delay': 5.0})
facade.reset()
```

---

## 🔧 高级功能

### 1. 注册自定义策略

```python
from app.adapters.anti_wind import register_strategy
from app.adapters.anti_wind.strategies.base import BaseStrategy

class MyCustomStrategy(BaseStrategy):
    """自定义策略"""
    
    async def before_request(self, url, method, headers):
        # 请求前处理
        headers['X-Custom'] = 'value'
        return headers
    
    async def after_request(self, response):
        # 请求后处理
        return response

# 注册策略（默认禁用）
register_strategy('my_custom', MyCustomStrategy, default_enabled=False)

# 使用
facade = AntiWindFacade({
    **STANDARD_CONFIG,
    'enable_my_custom': True,  # 启用自定义策略
})
```

### 2. 动态调整策略

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

### 3. 策略状态监控

```python
# 打印所有策略状态
facade.print_status()

# 获取启用的策略
enabled = facade.get_enabled_strategies()
print(f"启用的策略：{enabled}")

# 获取策略实例
cookie_strategy = facade.get_strategy('CookieInjectStrategy')
if cookie_strategy:
    # 访问策略内部状态
    print(f"Cookie 数量：{len(cookie_strategy._cookies)}")
```

---

## 📊 策略说明

### L1: CookieInjectStrategy (认证)

**功能**: 注入真实用户 Cookie 绕过反爬检测

**配置项**:
```python
{
    'enable_cookie_inject': True,
    'cookie_storage_dir': 'data/cookies',
    'cookie_file_name': 'eastmoney_com_manual.json',
    'cookie_max_age_hours': 24,
}
```

**Cookie 文件位置**: `backend/data/cookies/eastmoney_com_manual.json`

---

### L2: TLSFingerprintStrategy (伪装)

**功能**: 模拟真实浏览器的 TLS 握手特征

**配置项**:
```python
{
    'enable_tls_fingerprint': True,
    'tls_patch_mode': 'curl_cffi',
    'impersonate': 'chrome120',
    'timeout': 30,
}
```

**指纹库**:
- `chrome120`, `chrome119`, `chrome118`
- `firefox120`, `firefox117`
- `safari15_5`, `safari15_3`

---

### L3: RateLimitStrategy (限流)

**功能**: 自适应延迟，防止频率过高

**配置项**:
```python
{
    'enable_rate_limit': True,
    'min_delay': 1.0,  # 最小延迟（秒）
    'max_delay': 3.0,  # 最大延迟（秒）
}
```

**时间段策略**:
- **交易时段 (9:30-15:00)**: 2-4 秒
- **非交易时段**: 1-2 秒
- **连续失败后**: 5-10 秒

---

### L4: UARotatorStrategy (伪装)

**功能**: 轮换 User-Agent，降低被识别风险

**配置项**:
```python
{
    'enable_ua_rotation': True,
    'rotation_interval': 10,  # 每 10 次请求轮换
}
```

**UA 池**: 11 个真实浏览器 UA（带概率权重）

---

### L5: SmartRetryStrategy (重试)

**功能**: 智能重试，错误分类与自动降级

**配置项**:
```python
{
    'enable_smart_retry': True,
    'max_retries': 3,
}
```

**错误分类策略**:
| 错误类型 | 重试次数 | 说明 |
|---------|---------|------|
| TLS 指纹错误 | 0 | 直接降级 |
| HTTP 429 | 1 | 等待后重试 |
| 网络错误 | 2 | 指数退避 |
| 服务器错误 | 2 | 指数退避 |

---

## 🔍 测试验证

### 运行测试

```bash
cd backend
python test_anti_wind_quick_test.py
```

### 测试覆盖

- ✅ 基本功能验证
- ✅ 策略注册表
- ✅ 配置分离
- ✅ 懒加载初始化
- ✅ 性能优化

**性能指标**: 平均每次请求 < 20ms

---

## 📈 优化说明（v4.0）

### 优化内容

1. **策略注册制** - 动态加载策略，符合开闭原则
2. **统一初始化** - Facade 管理初始化时机
3. **配置分离** - 每个策略只提取需要的配置
4. **接口精简** - 移除冗余方法
5. **执行优化** - 缓存启用的策略列表

### 优化效果

| 指标 | 优化前 | 优化后 | 改进 |
|------|--------|--------|------|
| Facade 代码行数 | 356 行 | 306 行 | -14% |
| 策略初始化开销 | 每次检查 | 一次性 | -90% |
| 配置内存占用 | 完整 config | 精简 config | -50% |
| 性能表现 | - | 15.6ms/请求 | 优秀 |

### 迁移指南

**v3.x → v4.0** (向后兼容，无需修改)

```python
# 老代码（仍然可用）
facade = AntiWindFacade(STANDARD_CONFIG)

# 新代码（推荐）
facade = AntiWindFacade(STANDARD_CONFIG)
# 功能完全兼容，性能更优
```

**自定义策略注册** (新功能)

```python
# v4.0 新增
register_strategy('my_custom', MyCustomStrategy)
```

---

## 🐛 故障排查

### 问题 1: 策略未启用

**症状**:
```python
facade.get_enabled_strategies()  # 返回空列表
```

**解决**:
```python
# 检查配置
config = {
    'enable_cookie_inject': True,  # 确保为 True
    'enable_tls_fingerprint': True,
    # ...
}
facade = AntiWindFacade(config)
```

---

### 问题 2: 自定义策略未生效

**症状**:
```python
register_strategy('my_custom', MyCustomStrategy)
facade = AntiWindFacade(STANDARD_CONFIG)
# 自定义策略未启用
```

**解决**:
```python
# 需要在配置中显式启用
facade = AntiWindFacade({
    **STANDARD_CONFIG,
    'enable_my_custom': True,
})
```

---

### 问题 3: 性能下降

**症状**: 请求耗时 > 100ms

**解决**:
```python
# 1. 禁用不必要的策略
config = {
    **STANDARD_CONFIG,
    'enable_ua_rotation': False,  # 禁用 UA 轮换
}

# 2. 调整限流参数
config['min_delay'] = 0.5
config['max_delay'] = 1.0

# 3. 查看策略状态
facade.print_status()
```

---

## 📚 相关文档

- [OPTIMIZATION_RECORD.md](OPTIMIZATION_RECORD.md) - 优化记录与技术细节
- [../test_anti_wind_quick_test.py](../test_anti_wind_quick_test.py) - 快速测试脚本

---

## 🎯 最佳实践

### 1. 配置选择

- **日常使用**: `STANDARD_CONFIG`
- **高危 API**: `FULL_CONFIG`
- **浏览器自动化**: `BROWSER_CONFIG`
- **生产环境**: 根据实际情况调整延迟参数

### 2. Cookie 管理

```python
# 定期检查 Cookie 过期
from datetime import datetime

cookie_strategy = facade.get_strategy('CookieInjectStrategy')
if cookie_strategy._cookies_updated_at:
    age = (datetime.now() - cookie_strategy._cookies_updated_at).days
    if age > 5:
        logger.warning("Cookie 即将过期，请更新")
```

### 3. 性能调优

```python
# 低延迟场景
config = {
    **BASIC_CONFIG,
    'enable_rate_limit': False,  # 禁用限流
    'enable_ua_rotation': False,  # 禁用 UA 轮换
}

# 高可靠性场景
config = {
    **FULL_CONFIG,
    'min_delay': 2.0,
    'max_delay': 5.0,
    'max_retries': 5,
}
```

---

**维护者**: Quant Platform Team  
**文档版本**: v4.0 (优化版)  
**测试状态**: ✅ 全部通过
