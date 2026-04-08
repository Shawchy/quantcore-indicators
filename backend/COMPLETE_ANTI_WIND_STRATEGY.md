# 完整反风控策略清单

## 策略分类

### 一、网络层策略

#### 1. 代理 IP 池管理
- **位置**: `app/adapters/anti_wind_control.py` - `ProxyPool`
- **功能**: 
  - 自动轮换代理 IP
  - IP 成功率统计
  - IP 健康检查
  - 失败自动屏蔽
- **状态**: ❌ **成交额服务未使用**

```python
# 使用示例
proxy_pool = ProxyPool()
proxy_pool.add_proxy(host="127.0.0.1", port=7890)
proxy = proxy_pool.get_best_proxy()
```

#### 2. TLS 指纹伪装
- **位置**: `app/adapters/tls_fingerprint.py` - `TLSFingerprintClient`
- **功能**:
  - curl_cffi - 模拟 Chrome/Firefox/Safari TLS 指纹
  - tls-client - 专门的 TLS 指纹模拟库
  - httpx - HTTP/2 支持
- **状态**: ⚠️ **成交额服务未显式使用**

```python
# 使用示例
tls_client = TLSFingerprintClient(backend="curl_cffi", impersonate="chrome120")
tls_client.initialize()
response = tls_client.get(url)
```

#### 3. 智能 TLS 指纹选择
- **位置**: `app/adapters/hybrid_tls_client.py` - `HybridTLSClient`
- **功能**:
  - 多层 TLS 指纹伪装
  - 指纹成功率统计
  - 动态更新最优指纹
  - 自动故障切换
- **状态**: ❌ **成交额服务未使用**

```python
# 使用示例
tls_client = HybridTLSClient()
await tls_client.initialize()
response = await tls_client.get(url)
```

### 二、浏览器层策略

#### 4. 凭证注入（Cookie 认证）
- **位置**: `app/adapters/credential_injector.py` - `CredentialInjector`
- **功能**:
  - Playwright 访问获取 Cookie
  - 注入 Cookie 到请求
  - Cookie 持久化
  - 自动刷新 Cookie
- **状态**: ✅ **已集成**

```python
# 使用示例
injector = CredentialInjector()
await injector.initialize()
result = await injector.execute_request(fetch_func)
```

#### 5. 智能路由器
- **位置**: `app/adapters/smart_router.py` - `SmartDataRouter`
- **功能**:
  - 根据 API 敏感度自动选择客户端
  - curl_cffi（低敏感）
  - Playwright（高敏感）
  - 自动故障转移
- **状态**: ✅ **已集成**

```python
# 使用示例
router = SmartDataRouter()
await router.initialize()
result = await router.execute_request(fetch_func)
```

#### 6. Playwright 浏览器增强
- **位置**: `app/adapters/enhanced_playwright_adapter.py` - `EnhancedPlaywrightAdapter`
- **功能**:
  - 浏览器指纹增强
  - 防检测参数配置
  - 验证码检测与处理
  - Cookie 持久化
- **状态**: ⚠️ **成交额服务未直接使用**

```python
# 使用示例
adapter = EnhancedPlaywrightAdapter()
await adapter.initialize()
result = await adapter.fetch_data()
```

### 三、请求调度策略

#### 7. 智能请求调度
- **位置**: `app/adapters/anti_wind_control.py` - `AntiWindControlManager`
- **功能**:
  - 请求去重与缓存
  - 请求频率控制
  - 请求优先级调度
- **状态**: ❌ **成交额服务未使用**

#### 8. 请求限流
- **位置**: `app/services/market_turnover_service.py`
- **功能**:
  - 请求前延迟（3-5 秒）
  - 时间段差异化延迟
  - 限流时延迟惩罚（3 倍）
  - 交易时段额外延迟（1.5 倍）
- **状态**: ✅ **已实现**

```python
await self._rate_limit()
```

### 四、重试与容错策略

#### 9. 指数退避重试
- **位置**: `app/services/market_turnover_service.py`
- **功能**:
  - 指数退避延迟（2^attempt）
  - 限流时延迟惩罚（3 倍）
  - 交易时段额外延迟（1.5 倍）
  - 最大重试次数限制
- **状态**: ✅ **已实现**

```python
base_delay = (2 ** attempt) * self._retry_base_delay
if self._rate_limit_detected:
    base_delay *= 3
```

#### 10. 熔断器保护
- **位置**: `app/services/market_turnover_service.py`
- **功能**:
  - 连续失败 3 次触发熔断
  - 熔断持续时间 5 分钟
  - 熔断超时自动恢复
- **状态**: ✅ **已实现**

```python
if self._consecutive_failures >= 3:
    self._open_circuit_breaker()
```

#### 11. 限流检测
- **位置**: `app/services/market_turnover_service.py`
- **功能**:
  - 检测连接异常
  - 检测限流关键词
  - 5 分钟内多次触发确认
- **状态**: ✅ **已实现**

```python
is_rate_limit = self._detect_rate_limit(e)
```

### 五、身份伪装策略

#### 12. User-Agent 轮换
- **位置**: `app/services/market_turnover_service.py`
- **功能**:
  - 6 个 UA 随机切换
  - 限流时自动轮换
- **状态**: ✅ **已实现**

```python
self._rotate_user_agent()
```

#### 13. 浏览器指纹伪装
- **位置**: `app/adapters/hybrid_tls_client.py`
- **功能**:
  - 多层 TLS 指纹
  - 指纹成功率统计
  - 动态选择最优指纹
- **状态**: ❌ **成交额服务未使用**

### 六、验证码处理策略

#### 14. 验证码检测与处理
- **位置**: `app/adapters/anti_wind_control.py` - `CaptchaDetector`
- **功能**:
  - 验证码自动检测
  - 验证码处理超时
  - 验证码处理重试
- **状态**: ❌ **成交额服务未使用**

### 七、数据源策略

#### 15. 多数据源故障转移
- **位置**: `app/adapters/strategy_config.py` - `UNIFIED_DATA_STRATEGY`
- **功能**:
  - 数据源优先级配置
  - 自动故障转移
  - 健康检查
- **状态**: ❌ **成交额服务未使用**

```python
# 使用示例
strategy = UNIFIED_DATA_STRATEGY['market_turnover']
```

## 成交额服务当前状态

### 已实现 ✅
1. ✅ 请求限流
2. ✅ 指数退避重试
3. ✅ 熔断器保护
4. ✅ 限流检测
5. ✅ User-Agent 轮换
6. ✅ 凭证注入（新增）
7. ✅ 智能路由（新增）
8. ✅ 串行获取（避免并发）
9. ✅ 超时保护（180 秒）

### 未实现 ❌
1. ❌ 代理 IP 池管理
2. ❌ TLS 指纹伪装（显式使用）
3. ❌ 智能 TLS 指纹选择
4. ❌ Playwright 浏览器增强
5. ❌ 智能请求调度
6. ❌ 请求去重与缓存
7. ❌ 浏览器指纹伪装
8. ❌ 验证码检测与处理
9. ❌ 多数据源故障转移

## 建议优化

### 优先级 1（立即实施）
1. **代理 IP 池管理** - 最重要，防止单 IP 被封
2. **TLS 指纹伪装** - 防止 TLS 指纹识别
3. **智能请求调度** - 优化请求频率

### 优先级 2（短期实施）
1. **浏览器指纹伪装** - 增强反风控能力
2. **验证码检测与处理** - 应对验证码
3. **多数据源故障转移** - 提高可用性

### 优先级 3（长期优化）
1. **请求去重与缓存** - 减少重复请求
2. **指纹成功率统计** - 动态优化指纹选择

## 完整反风控集成示例

```python
class MarketTurnoverService:
    def __init__(self):
        # 现有策略
        self._rate_limit_enabled = True
        self._retry_enabled = True
        self._circuit_breaker_enabled = True
        
        # 新增策略
        self._proxy_pool = ProxyPool()  # 代理 IP 池
        self._tls_client = HybridTLSClient()  # TLS 指纹
        self._captcha_detector = CaptchaDetector()  # 验证码检测
        
        # 懒加载
        self._credential_injector = None
        self._smart_router = None
    
    async def _fetch_with_full_anti_wind(self, fetch_func, *args, **kwargs):
        """完整反风控策略"""
        # 1. 检查熔断器
        if self._is_circuit_breaker_open():
            raise Exception("熔断器保护中")
        
        # 2. 获取代理 IP
        proxy = self._proxy_pool.get_best_proxy()
        
        # 3. 使用 TLS 指纹客户端
        tls_config = await self._tls_client.get_best_fingerprint()
        
        # 4. 请求限流
        await self._rate_limit()
        
        # 5. 执行请求（带凭证注入 + 智能路由）
        result = await self._execute_with_anti_wind(
            fetch_func, *args,
            proxy=proxy,
            tls_config=tls_config,
            **kwargs
        )
        
        # 6. 检测验证码
        if await self._captcha_detector.detect(result):
            logger.warning("检测到验证码，尝试处理...")
            result = await self._captcha_detector.handle(result)
        
        # 7. 成功后重置状态
        self.reset_rate_limit_status()
        return result
```

## 总结

成交额服务目前已集成**9 项基础反风控策略**，但还缺少**6 项高级策略**。

**立即需要添加的**:
1. 代理 IP 池管理（防止单 IP 被封）
2. TLS 指纹伪装（防止 TLS 识别）
3. 智能请求调度（优化请求频率）

添加这些策略后，反风控能力将达到**企业级水平**，可以最大程度避免被限流和封禁。
