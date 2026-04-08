# AntiWindFacade 反风控策略优化方案

## 一、策略分类与层级

### 1.1 策略分层架构

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
│  ┌─────────────────────────────────┐   │
│  │  L1: 认证策略 (Authentication)  │   │
│  │  - CookieInjectStrategy         │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  L2: 伪装策略 (Disguise)        │   │
│  │  - TLSFingerprintStrategy       │   │
│  │  - UARotatorStrategy            │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  L3: 限流策略 (Rate Limiting)   │   │
│  │  - RateLimitStrategy            │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  L4: 重试策略 (Retry)           │   │
│  │  - SmartRetryStrategy           │   │
│  └─────────────────────────────────┘   │
│  ┌─────────────────────────────────┐   │
│  │  L5: 扩展策略 (Extension)       │   │
│  │  - ProxyPoolStrategy            │   │
│  │  - CaptchaHandlerStrategy       │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

### 1.2 策略执行顺序

```
请求开始
    ↓
[Before Request 阶段]
    ↓
L1 → CookieInjectStrategy (注入凭证)
    ↓
L2 → TLSFingerprintStrategy (准备 TLS 客户端)
    ↓
L2 → UARotatorStrategy (轮换 User-Agent)
    ↓
L3 → RateLimitStrategy (限流延迟)
    ↓
L5 → ProxyPoolStrategy (选择代理，可选)
    ↓
[执行实际请求] ← SmartRetryStrategy 包装
    ↓
[After Request 阶段]
    ↓
L5 → CaptchaHandlerStrategy (检测验证码，可选)
    ↓
L3 → RateLimitStrategy (更新失败计数)
    ↓
L5 → ProxyPoolStrategy (报告成功/失败)
    ↓
响应返回
```

## 二、标准化配置模板

### 2.1 配置层级

```python
# 配置示例
config = {
    # ========== L1: 认证策略 ==========
    'enable_cookie_inject': True,
    'cookie_storage_dir': 'data/cookies',
    'cookie_file_name': 'eastmoney_com_manual.json',
    
    # ========== L2: 伪装策略 ==========
    'enable_tls_fingerprint': True,
    'tls_patch_mode': 'curl_cffi',
    'impersonate': 'chrome120',
    
    'enable_ua_rotation': True,
    'rotation_interval': 10,  # 每 10 次请求轮换
    
    # ========== L3: 限流策略 ==========
    'enable_rate_limit': True,
    'min_delay': 1.0,  # 最小延迟（秒）
    'max_delay': 3.0,  # 最大延迟（秒）
    
    # ========== L4: 重试策略 ==========
    'enable_smart_retry': True,
    'max_retries': 3,
    
    # ========== L5: 扩展策略（可选）==========
    'enable_proxy_pool': False,
    'proxies': [],
    'min_success_rate': 0.3,
    'block_duration_minutes': 30,
    
    'enable_captcha_handler': False,
    'captcha_timeout': 60,
    'captcha_check_interval': 1,
}
```

### 2.2 预设配置模板

```python
# ========== 模板 1: 基础配置（快速开始）==========
BASIC_CONFIG = {
    'enable_cookie_inject': True,
    'enable_rate_limit': True,
    'enable_smart_retry': True,
    'max_retries': 3,
}

# ========== 模板 2: 标准配置（推荐）==========
STANDARD_CONFIG = {
    # L1
    'enable_cookie_inject': True,
    'cookie_storage_dir': 'data/cookies',
    
    # L2
    'enable_tls_fingerprint': True,
    'impersonate': 'chrome120',
    
    'enable_ua_rotation': True,
    'rotation_interval': 10,
    
    # L3
    'enable_rate_limit': True,
    'min_delay': 1.0,
    'max_delay': 3.0,
    
    # L4
    'enable_smart_retry': True,
    'max_retries': 3,
}

# ========== 模板 3: 完整配置（高危 API）==========
FULL_CONFIG = {
    # L1
    'enable_cookie_inject': True,
    'cookie_storage_dir': 'data/cookies',
    
    # L2
    'enable_tls_fingerprint': True,
    'impersonate': 'chrome120',
    
    'enable_ua_rotation': True,
    'rotation_interval': 5,  # 更频繁的轮换
    
    # L3
    'enable_rate_limit': True,
    'min_delay': 2.0,  # 更保守的延迟
    'max_delay': 5.0,
    
    # L4
    'enable_smart_retry': True,
    'max_retries': 3,
    
    # L5
    'enable_proxy_pool': True,
    'proxies': [
        {'host': '1.2.3.4', 'port': 8080},
        # ... 更多代理
    ],
    'min_success_rate': 0.5,
    
    'enable_captcha_handler': True,
    'captcha_timeout': 120,
}

# ========== 模板 4: 无浏览器模式（纯 HTTP）==========
HEADLESS_CONFIG = {
    'enable_cookie_inject': True,
    'enable_tls_fingerprint': True,
    'impersonate': 'chrome120',
    'enable_rate_limit': True,
    'enable_smart_retry': True,
    'max_retries': 3,
}

# ========== 模板 5: 浏览器模式（Playwright）==========
BROWSER_CONFIG = {
    'enable_cookie_inject': True,
    'enable_rate_limit': True,
    'enable_smart_retry': True,
    'max_retries': 3,
    'enable_captcha_handler': True,
    'captcha_timeout': 120,
}
```

## 三、优化后的 Facade 接口

### 3.1 核心接口

```python
class AntiWindFacade:
    """反爬策略统一门面"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """初始化"""
        pass
    
    async def execute_with_strategies(
        self,
        request_func: Callable,
        url: str,
        method: str = "GET",
        headers: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> Any:
        """使用策略执行请求"""
        pass
    
    # ========== 策略管理 ==========
    def enable_strategy(self, strategy_name: str) -> bool:
        """启用策略"""
        pass
    
    def disable_strategy(self, strategy_name: str) -> bool:
        """禁用策略"""
        pass
    
    def get_strategy(self, strategy_name: str) -> Optional[BaseStrategy]:
        """获取策略实例"""
        pass
    
    def get_enabled_strategies(self) -> List[str]:
        """获取启用的策略列表"""
        pass
    
    def get_strategy_status(self) -> Dict[str, bool]:
        """获取所有策略状态"""
        pass
    
    def print_status(self) -> None:
        """打印策略状态"""
        pass
    
    # ========== 便捷方法 ==========
    def update_config(self, config: Dict[str, Any]) -> None:
        """更新配置"""
        pass
    
    def reset(self) -> None:
        """重置所有策略状态"""
        pass
```

### 3.2 使用示例

```python
# ========== 示例 1: 适配器中使用 ==========
class AkShareAdapter:
    def __init__(self):
        self.anti_wind = AntiWindFacade(STANDARD_CONFIG)
    
    async def stock_individual_info_em(self, symbol: str) -> Dict:
        """获取股票基本信息"""
        url = f"https://quote.eastmoney.com/sz{symbol}.html"
        
        async def fetch():
            # 实际请求逻辑
            pass
        
        return await self.anti_wind.execute_with_strategies(
            request_func=fetch,
            url=url,
            method="GET"
        )

# ========== 示例 2: 服务层中使用 ==========
class MarketTurnoverService:
    def __init__(self):
        self.anti_wind = AntiWindFacade({
            **STANDARD_CONFIG,
            'min_delay': 2.0,
            'max_delay': 5.0,
        })
    
    async def get_market_turnover(self, date: str) -> Dict:
        """获取成交额数据"""
        async def fetch():
            # 实际请求逻辑
            pass
        
        return await self.anti_wind.execute_with_strategies(
            request_func=fetch,
            url="https://data.eastmoney.com/...",
            method="GET"
        )

# ========== 示例 3: 动态调整策略 ==========
async def adaptive_request():
    facade = AntiWindFacade(BASIC_CONFIG)
    
    # 根据响应动态调整
    try:
        result = await facade.execute_with_strategies(...)
    except Exception as e:
        if "429" in str(e):
            # 触发限流，增强限流策略
            facade.disable_strategy('UARotatorStrategy')
            facade.update_config({'min_delay': 5.0, 'max_delay': 10.0})
        elif "TLS" in str(e):
            # TLS 指纹错误，切换指纹
            tls_strategy = facade.get_strategy('TLSFingerprintStrategy')
            tls_strategy.switch_fingerprint('firefox120')
        
        # 重试
        result = await facade.execute_with_strategies(...)
```

## 四、最佳实践

### 4.1 策略选择指南

| 场景 | 推荐策略组合 | 配置要点 |
|------|------------|---------|
| **低频请求** (< 100 次/天) | L1 + L3 + L4 | Cookie + 限流 + 重试 |
| **中频请求** (100-1000 次/天) | L1 + L2 + L3 + L4 | + TLS 指纹 + UA 轮换 |
| **高频请求** (> 1000 次/天) | L1 + L2 + L3 + L4 + L5 | + 代理池 |
| **高危 API** | FULL_CONFIG | 所有策略，保守延迟 |
| **浏览器自动化** | L1 + L3 + L4 + L5(Captcha) | Playwright + 验证码处理 |
| **纯 HTTP 请求** | L1 + L2 + L3 + L4 | curl_cffi + TLS 指纹 |

### 4.2 Cookie 管理最佳实践

```python
# 1. Cookie 存储位置
# 推荐：data/cookies/{domain}_manual.json

# 2. Cookie 更新周期
# - 东方财富网：7 天
# - 其他网站：根据实际过期时间

# 3. Cookie 自动监控
async def monitor_cookie_expiry(facade: AntiWindFacade):
    """监控 Cookie 过期时间"""
    cookie_strategy = facade.get_strategy('CookieInjectStrategy')
    
    if cookie_strategy._cookies_updated_at:
        age_days = (datetime.now() - cookie_strategy._cookies_updated_at).days
        if age_days > 5:
            logger.warning(f"Cookie 已使用{age_days}天，建议更新")
```

### 4.3 限流策略调优

```python
# 根据不同时间段调整
def get_time_based_config():
    now = datetime.now()
    hour = now.hour
    
    # 交易时段 (9:30-15:00)
    if (hour == 9 and now.minute >= 30) or (10 <= hour <= 14) or (hour == 15 and now.minute == 0):
        return {
            'min_delay': 2.0,
            'max_delay': 5.0,
            'max_retries': 2,
        }
    
    # 非交易时段
    return {
        'min_delay': 1.0,
        'max_delay': 3.0,
        'max_retries': 3,
    }

# 动态应用配置
facade.update_config(get_time_based_config())
```

### 4.4 错误处理与降级

```python
async def robust_request(facade: AntiWindFacade, url: str):
    """健壮的请求处理"""
    
    # 第 1 次尝试：完整策略
    try:
        return await facade.execute_with_strategies(...)
    except Exception as e:
        logger.warning(f"完整策略失败：{e}")
    
    # 第 2 次尝试：降级策略（禁用 TLS 指纹）
    try:
        facade.disable_strategy('TLSFingerprintStrategy')
        return await facade.execute_with_strategies(...)
    except Exception as e:
        logger.warning(f"降级策略失败：{e}")
    
    # 第 3 次尝试：最小策略（仅 Cookie + 重试）
    try:
        facade.disable_strategy('UARotatorStrategy')
        facade.disable_strategy('RateLimitStrategy')
        return await facade.execute_with_strategies(...)
    except Exception as e:
        logger.error(f"所有尝试失败")
        raise
```

### 4.5 性能优化建议

```python
# 1. 策略懒加载
# - CookieInjectStrategy: 首次请求时加载 Cookie
# - TLSFingerprintStrategy: 首次请求时初始化客户端
# - 避免初始化时创建不必要的对象

# 2. 策略缓存
# - UA 池：类级别缓存，避免重复创建
# - 代理池：单例模式，全局共享

# 3. 异步并发
# - 使用 asyncio.gather 并发执行多个独立请求
# - 注意：共享策略实例时需要加锁

# 4. 资源清理
async def cleanup_resources(facade: AntiWindFacade):
    """清理资源"""
    tls_strategy = facade.get_strategy('TLSFingerprintStrategy')
    if tls_strategy and tls_strategy._client:
        tls_strategy._client.close()
```

## 五、监控与日志

### 5.1 策略状态监控

```python
def monitor_strategy_health(facade: AntiWindFacade) -> Dict:
    """监控策略健康状态"""
    status = facade.get_strategy_status()
    
    health_report = {
        'timestamp': datetime.now().isoformat(),
        'strategies': status,
        'enabled_count': sum(1 for v in status.values() if v),
        'total_count': len(status),
    }
    
    # 检查异常
    if health_report['enabled_count'] == 0:
        logger.error("⚠️  所有策略都被禁用！")
    
    return health_report
```

### 5.2 日志级别建议

```python
# DEBUG: 策略执行细节（每次请求）
# INFO: 策略状态变更（启用/禁用/切换）
# WARNING: 触发限流/验证码/代理屏蔽
# ERROR: 策略初始化失败/所有重试失败
```

## 六、测试验证

### 6.1 单元测试

```python
async def test_strategy_isolation():
    """测试策略隔离性"""
    facade1 = AntiWindFacade({'enable_cookie_inject': True})
    facade2 = AntiWindFacade({'enable_cookie_inject': False})
    
    assert facade1.get_strategy('CookieInjectStrategy').is_enabled()
    assert facade2.get_strategy('CookieInjectStrategy') is None

async def test_strategy_order():
    """测试策略执行顺序"""
    facade = AntiWindFacade(STANDARD_CONFIG)
    
    strategies = facade.strategies
    assert strategies[0].__class__.__name__ == 'CookieInjectStrategy'
    assert strategies[1].__class__.__name__ == 'TLSFingerprintStrategy'
    # ...
```

### 6.2 集成测试

```python
async def test_full_workflow():
    """测试完整工作流程"""
    facade = AntiWindFacade(FULL_CONFIG)
    
    # 模拟真实请求
    result = await facade.execute_with_strategies(
        request_func=mock_request,
        url="https://www.eastmoney.com",
        method="GET"
    )
    
    assert result is not None
    assert facade.get_strategy('CookieInjectStrategy')._cookies
```

## 七、版本兼容性

### 7.1 向后兼容

```python
# 老代码兼容
class AkShareAdapter:
    # 老方法（已废弃，但保持兼容）
    async def _ensure_credentials(self):
        """@deprecated 使用 AntiWindFacade 替代"""
        pass
    
    # 新方法
    async def _fetch_with_anti_wind(self, fetch_func):
        return await self.anti_wind.execute_with_strategies(...)
```

### 7.2 迁移路径

```
老代码 → 保留老方法（@deprecated）→ 调用 AntiWindFacade
         ↓
         逐步替换 → 删除老方法
```

## 八、未来扩展

### 8.1 可扩展点

1. **新策略类型**：继承 `BaseStrategy` 即可
2. **自定义配置**：通过 `update_config` 动态调整
3. **策略组合**：创建预设配置模板
4. **中间件模式**：在 before/after 中插入自定义逻辑

### 8.2 计划中的功能

- [ ] 策略执行统计（成功率、平均耗时）
- [ ] 自动策略调优（基于历史数据）
- [ ] 分布式 Cookie 共享
- [ ] 代理池自动发现
- [ ] 验证码自动识别（对接打码平台）

---

**文档版本**: v2.0  
**最后更新**: 2026-04-09  
**维护者**: AntiWind Team
