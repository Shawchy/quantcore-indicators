# 反风控策略 v5.0 优化方案

**版本**: v5.0 (持续优化版)  
**制定日期**: 2026-04-09  
**状态**: 📋 待实施

---

## 📊 当前状态分析

### ✅ v4.0 已完成

1. **策略注册制** - 动态加载策略
2. **配置分离** - 减少内存占用
3. **统一初始化** - 优化初始化流程
4. **接口精简** - 提升可维护性
5. **执行优化** - 缓存启用策略列表

### ⚠️ 存在的问题

#### 1. Cookie 管理不够智能
- ❌ 需要手动获取 Cookie（用户体验差）
- ❌ Cookie 过期检测不精确（只检查天数）
- ❌ 缺少自动续期机制
- ❌ 不支持多域名 Cookie

#### 2. 限流策略过于简单
- ❌ 固定时间段策略（不够灵活）
- ❌ 缺少请求优先级支持
- ❌ 失败计数全局化（应该按 API 分类）
- ❌ 缺少并发控制

#### 3. UA 轮换策略可优化
- ❌ UA 池静态硬编码（11 个固定 UA）
- ❌ 轮换策略简单（固定每 10 次）
- ❌ 缺少 UA 成功率统计
- ❌ 没有考虑浏览器指纹匹配

#### 4. 缺少监控与统计
- ❌ 无策略执行统计
- ❌ 无成功率监控
- ❌ 无性能瓶颈分析
- ❌ 无异常告警机制

#### 5. TLS 指纹策略可增强
- ❌ 指纹选择依赖配置（不智能）
- ❌ 缺少指纹成功率追踪
- ❌ 指纹切换不够平滑

---

## 🎯 优化目标

### 高优先级（v5.0 核心）

1. **智能 Cookie 管理** - 自动获取 + 自动续期
2. **自适应限流** - 基于成功率的动态限流
3. **UA 池动态管理** - 自动更新 + 成功率统计
4. **监控与统计** - 完整的指标收集

### 中优先级（v5.1 增强）

5. **TLS 指纹智能选择** - 基于成功率自动选择
6. **请求优先级** - 支持高优先级请求插队
7. **并发控制** - 限制同时请求数

### 低优先级（v5.2 扩展）

8. **行为伪装** - 模拟真实用户行为
9. **验证码自动处理** - 对接打码平台
10. **分布式 Cookie 共享** - 多实例共享 Cookie

---

## ✅ 优化方案详情

### 优化 1: 智能 Cookie 管理 ⭐⭐⭐⭐⭐

#### 1.1 自动 Cookie 获取

**新增模块**: `cookie_auto_fetcher.py`

```python
class CookieAutoFetcher:
    """自动 Cookie 获取器"""
    
    async def fetch_cookie(self, domain: str) -> bool:
        """
        自动获取 Cookie
        使用 Playwright/DrissionPage 访问网站获取
        """
        # 1. 尝试使用 DrissionPage（最优）
        # 2. 降级到 Playwright
        # 3. 降级到 undetected-chromedriver
        
    async def is_cookie_valid(self, domain: str) -> bool:
        """检查 Cookie 是否有效（精确到秒）"""
        # 检查过期时间
        # 检查是否被封禁
        # 发送测试请求验证
        
    async def auto_refresh(self, domain: str) -> bool:
        """自动续期 Cookie（过期前 1 小时）"""
        # 后台监听
        # 提前续期
```

**收益**:
- ✅ 用户体验提升 90%（无需手动获取）
- ✅ Cookie 可用性提升至 99%
- ✅ 减少人工维护成本

---

#### 1.2 Cookie 持久化增强

**修改文件**: `cookie_injector.py`

```python
class CookieInjectStrategy(BaseStrategy):
    def __init__(self, config):
        # ... 现有配置
        self._cookie_expiry: Dict[str, datetime] = {}  # 精确过期时间
        self._cookie_domain: Dict[str, str] = {}  # 多域名支持
    
    async def _load_manual_cookies(self):
        """加载 Cookie（支持多域名）"""
        domains = self.config.get('domains', ['eastmoney.com'])
        for domain in domains:
            await self._load_domain_cookie(domain)
    
    def _check_cookie_expiry(self) -> bool:
        """检查 Cookie 是否过期（精确到秒）"""
        now = datetime.now()
        for domain, expiry in self._cookie_expiry.items():
            if now >= expiry:
                logger.warning(f"{domain} Cookie 已过期")
                return False
        return True
```

**收益**:
- ✅ 支持多域名 Cookie
- ✅ 过期检测精确到秒
- ✅ 自动提醒续期

---

### 优化 2: 自适应限流 ⭐⭐⭐⭐⭐

#### 2.1 基于成功率的动态限流

**修改文件**: `rate_limiter.py`

```python
class RateLimitStrategy(BaseStrategy):
    def __init__(self, config):
        # ... 现有配置
        self._api_stats: Dict[str, APIStats] = {}  # 按 API 统计
        self._success_window = 100  # 滑动窗口大小
    
    async def _calculate_delay(self, url: str) -> float:
        """基于成功率计算延迟"""
        api_key = self._extract_api_key(url)
        stats = self._get_api_stats(api_key)
        
        # 计算成功率
        success_rate = stats.get_success_rate()
        
        # 动态调整延迟
        if success_rate < 0.5:
            # 成功率低，大幅增加延迟
            delay_multiplier = 3.0
        elif success_rate < 0.8:
            # 成功率中等，增加延迟
            delay_multiplier = 2.0
        elif success_rate < 0.95:
            # 成功率良好，正常延迟
            delay_multiplier = 1.0
        else:
            # 成功率优秀，可以减少延迟
            delay_multiplier = 0.8
        
        base_delay = random.uniform(self._base_min_delay, self._base_max_delay)
        return base_delay * delay_multiplier
    
    def _get_api_stats(self, api_key: str) -> APIStats:
        """获取 API 统计信息（滑动窗口）"""
        if api_key not in self._api_stats:
            self._api_stats[api_key] = APIStats(window_size=self._success_window)
        return self._api_stats[api_key]
```

**新增辅助类**:

```python
class APIStats:
    """API 统计信息（滑动窗口）"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.results: deque = deque(maxlen=window_size)  # True=成功，False=失败
    
    def record(self, success: bool):
        """记录请求结果"""
        self.results.append(success)
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        if not self.results:
            return 1.0
        return sum(self.results) / len(self.results)
```

**收益**:
- ✅ 限流更智能（基于实际成功率）
- ✅ 按 API 分类统计（更精确）
- ✅ 自动适应反爬策略变化

---

#### 2.2 请求优先级支持

**新增功能**:

```python
class RequestPriority(Enum):
    HIGH = 1
    NORMAL = 2
    LOW = 3

class RateLimitStrategy(BaseStrategy):
    async def before_request(self, url, method, headers, priority=RequestPriority.NORMAL):
        if priority == RequestPriority.HIGH:
            # 高优先级请求，减少延迟
            delay *= 0.5
        elif priority == RequestPriority.LOW:
            # 低优先级请求，增加延迟
            delay *= 2.0
```

**收益**:
- ✅ 关键业务优先保障
- ✅ 非关键业务可降级

---

### 优化 3: UA 池动态管理 ⭐⭐⭐⭐

#### 3.1 动态 UA 池

**修改文件**: `ua_rotator.py`

```python
class UARotatorStrategy(BaseStrategy):
    def __init__(self, config):
        # ... 现有配置
        self._ua_stats: Dict[str, UAStats] = {}  # UA 成功率统计
        self._ua_pool_file = config.get('ua_pool_file', 'data/ua_pool.json')
        self._load_dynamic_ua_pool()
    
    def _load_dynamic_ua_pool(self):
        """加载动态 UA 池"""
        # 1. 从文件加载（可手动更新）
        # 2. 从在线 UA 库加载（定期更新）
        # 3. 从成功请求中提取 UA
        
    async def before_request(self, url, method, headers):
        # 基于成功率选择 UA
        best_ua = self._select_best_ua()
        headers['User-Agent'] = best_ua
    
    def _select_best_ua(self) -> str:
        """选择成功率最高的 UA"""
        # 过滤成功率 > 80% 的 UA
        qualified_uas = [
            ua for ua, stats in self._ua_stats.items()
            if stats.get_success_rate() > 0.8
        ]
        
        if qualified_uas:
            # 从合格的 UA 中随机选择
            return random.choice(qualified_uas)
        else:
            # 没有合格的，使用默认 UA
            return self._user_agents[0]
    
    def record_ua_result(self, ua: str, success: bool):
        """记录 UA 使用结果"""
        if ua not in self._ua_stats:
            self._ua_stats[ua] = UAStats()
        self._ua_stats[ua].record(success)
```

**收益**:
- ✅ UA 池可动态更新
- ✅ 自动选择高成功率 UA
- ✅ 淘汰低成功率 UA

---

#### 3.2 UA 与浏览器指纹匹配

**增强功能**:

```python
class UARotatorStrategy(BaseStrategy):
    def _match_ua_with_fingerprint(self, ua: str, fingerprint: str) -> bool:
        """确保 UA 与 TLS 指纹匹配"""
        # Chrome UA 应该匹配 chrome120/119/118 指纹
        # Firefox UA 应该匹配 firefox120/117 指纹
        if 'Chrome' in ua and 'chrome' in fingerprint:
            return True
        if 'Firefox' in ua and 'firefox' in fingerprint:
            return True
        return False
```

**收益**:
- ✅ 避免 UA 与指纹不匹配
- ✅ 提升伪装真实性

---

### 优化 4: 监控与统计 ⭐⭐⭐⭐⭐

#### 4.1 策略执行统计

**新增模块**: `metrics.py`

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List

@dataclass
class StrategyMetrics:
    """策略指标"""
    strategy_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_execution_time_ms: float = 0.0
    last_execution_time: Optional[datetime] = None
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests

class MetricsCollector:
    """指标收集器"""
    
    def __init__(self):
        self._metrics: Dict[str, StrategyMetrics] = {}
        self._execution_times: Dict[str, List[float]] = {}
    
    def record_request(self, strategy_name: str, success: bool, execution_time_ms: float):
        """记录请求"""
        if strategy_name not in self._metrics:
            self._metrics[strategy_name] = StrategyMetrics(strategy_name)
        
        metrics = self._metrics[strategy_name]
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # 记录执行时间
        if strategy_name not in self._execution_times:
            self._execution_times[strategy_name] = []
        self._execution_times[strategy_name].append(execution_time_ms)
        
        # 计算平均执行时间
        metrics.avg_execution_time_ms = (
            sum(self._execution_times[strategy_name]) / 
            len(self._execution_times[strategy_name])
        )
        
        metrics.last_execution_time = datetime.now()
    
    def get_metrics(self, strategy_name: str) -> StrategyMetrics:
        """获取策略指标"""
        return self._metrics.get(strategy_name)
    
    def get_all_metrics(self) -> Dict[str, StrategyMetrics]:
        """获取所有指标"""
        return self._metrics.copy()
    
    def print_report(self):
        """打印指标报告"""
        print("\n" + "="*60)
        print("反风控策略执行报告")
        print("="*60)
        
        for name, metrics in self._metrics.items():
            print(f"\n{name}:")
            print(f"  总请求数：{metrics.total_requests}")
            print(f"  成功率：{metrics.success_rate:.2%}")
            print(f"  平均执行时间：{metrics.avg_execution_time_ms:.2f}ms")
```

**集成到 Facade**:

```python
class AntiWindFacade:
    def __init__(self, config):
        # ... 现有初始化
        self._metrics_collector = MetricsCollector()
    
    async def execute_with_strategies(self, ...):
        start_time = time.time()
        
        try:
            result = await super().execute_with_strategies(...)
            
            # 记录成功
            for strategy in self._enabled_strategies:
                execution_time = (time.time() - start_time) * 1000
                self._metrics_collector.record_request(
                    strategy.name, 
                    success=True, 
                    execution_time_ms=execution_time
                )
            
            return result
            
        except Exception as e:
            # 记录失败
            for strategy in self._enabled_strategies:
                self._metrics_collector.record_request(
                    strategy.name, 
                    success=False, 
                    execution_time_ms=0
                )
            raise
```

**收益**:
- ✅ 完整的执行统计
- ✅ 性能瓶颈分析
- ✅ 成功率监控

---

#### 4.2 异常告警

**新增功能**:

```python
class MetricsCollector:
    def __init__(self, config=None):
        # ... 现有初始化
        self._alert_thresholds = {
            'success_rate_min': 0.8,  # 成功率低于 80% 告警
            'execution_time_max': 1000,  # 执行时间超过 1000ms 告警
            'consecutive_failures': 5,  # 连续失败 5 次告警
        }
        
        if config:
            self._alert_thresholds.update(config.get('alert_thresholds', {}))
    
    def check_alerts(self, strategy_name: str):
        """检查是否需要告警"""
        metrics = self.get_metrics(strategy_name)
        
        # 检查成功率
        if metrics.success_rate < self._alert_thresholds['success_rate_min']:
            logger.warning(f"⚠️  告警：{strategy_name} 成功率过低：{metrics.success_rate:.2%}")
        
        # 检查执行时间
        if metrics.avg_execution_time_ms > self._alert_thresholds['execution_time_max']:
            logger.warning(f"⚠️  告警：{strategy_name} 执行时间过长：{metrics.avg_execution_time_ms:.2f}ms")
        
        # 检查连续失败
        if metrics.failed_requests >= self._alert_thresholds['consecutive_failures']:
            logger.error(f"❌ 告警：{strategy_name} 连续失败 {metrics.failed_requests} 次")
```

**收益**:
- ✅ 及时发现问题
- ✅ 自动告警通知
- ✅ 快速定位异常

---

### 优化 5: TLS 指纹智能选择 ⭐⭐⭐

#### 5.1 基于成功率的指纹选择

**修改文件**: `tls_fingerprint.py`

```python
class TLSFingerprintStrategy(BaseStrategy):
    def __init__(self, config):
        # ... 现有配置
        self._fingerprint_stats: Dict[str, FingerprintStats] = {}
        self._auto_switch = config.get('auto_switch_fingerprint', True)
    
    def _select_best_fingerprint(self, api_type: str = None) -> str:
        """基于成功率选择最佳指纹"""
        # 获取所有指纹的成功率
        fp_rates = []
        for fp, stats in self._fingerprint_stats.items():
            rate = stats.get_success_rate()
            fp_rates.append((fp, rate))
        
        # 排序
        fp_rates.sort(key=lambda x: x[1], reverse=True)
        
        # 选择成功率最高的
        if fp_rates and fp_rates[0][1] > 0.8:
            return fp_rates[0][0]
        
        # 没有合适的，使用默认
        return self._impersonate
    
    def record_fingerprint_result(self, fingerprint: str, success: bool):
        """记录指纹使用结果"""
        if fingerprint not in self._fingerprint_stats:
            self._fingerprint_stats[fingerprint] = FingerprintStats()
        self._fingerprint_stats[fingerprint].record(success)
```

**收益**:
- ✅ 自动选择最佳指纹
- ✅ 指纹成功率追踪
- ✅ 提升请求成功率

---

### 优化 6: 并发控制 ⭐⭐⭐

#### 6.1 信号量控制

**新增功能**:

```python
class AntiWindFacade:
    def __init__(self, config):
        # ... 现有初始化
        self._max_concurrent = config.get('max_concurrent_requests', 10)
        self._semaphore = asyncio.Semaphore(self._max_concurrent)
    
    async def execute_with_strategies(self, ...):
        async with self._semaphore:
            # 限制并发请求数
            return await super().execute_with_strategies(...)
```

**收益**:
- ✅ 防止并发过高被封禁
- ✅ 保护服务器资源
- ✅ 提升稳定性

---

## 📊 预期效果

### 性能提升

| 指标 | v4.0 | v5.0 | 提升 |
|------|------|------|------|
| Cookie 可用性 | 90% | 99% | +10% |
| 限流精准度 | 70% | 95% | +36% |
| UA 成功率 | 80% | 95% | +19% |
| 问题发现时间 | 小时级 | 分钟级 | -90% |
| 平均执行时间 | 15.6ms | 12ms | -23% |

### 用户体验

- ✅ 无需手动获取 Cookie（自动化）
- ✅ 更少的配置调整（智能化）
- ✅ 更快的故障恢复（自动化）
- ✅ 更清晰的监控报告（可视化）

---

## 📝 实施计划

### Phase 1: v5.0 核心功能（1-2 周）

1. **智能 Cookie 管理** - 3 天
   - Cookie 自动获取器
   - Cookie 持久化增强
   - 多域名支持

2. **自适应限流** - 3 天
   - 基于成功率的动态限流
   - API 分类统计
   - 请求优先级

3. **UA 池动态管理** - 2 天
   - 动态 UA 池
   - UA 成功率统计
   - UA 与指纹匹配

4. **监控与统计** - 4 天
   - 指标收集器
   - 策略执行统计
   - 异常告警

### Phase 2: v5.1 增强功能（1 周）

5. **TLS 指纹智能选择** - 2 天
6. **并发控制** - 2 天
7. **测试与文档** - 3 天

### Phase 3: v5.2 扩展功能（可选）

8. **行为伪装** - 3 天
9. **验证码处理** - 3 天
10. **分布式 Cookie 共享** - 4 天

---

## 🎯 优先级建议

### 立即实施（高优先级）⭐⭐⭐⭐⭐
1. **智能 Cookie 管理** - 用户体验提升最大
2. **监控与统计** - 问题定位必备
3. **自适应限流** - 提升成功率

### 近期实施（中优先级）⭐⭐⭐
4. **UA 池动态管理** - 提升伪装效果
5. **并发控制** - 提升稳定性

### 可选实施（低优先级）⭐⭐
6. **TLS 指纹智能选择** - 锦上添花
7. **行为伪装** - 高级功能

---

## ✅ 总结

**v5.0 优化重点**:
- ✅ **智能化**: 基于成功率自动调整策略
- ✅ **自动化**: Cookie 自动获取 + 续期
- ✅ **可视化**: 完整的监控与统计
- ✅ **精细化**: 按 API 分类统计

**预期收益**:
- ✅ 成功率提升 10-20%
- ✅ 维护成本降低 50%
- ✅ 问题发现时间减少 90%
- ✅ 用户体验提升 90%

**建议**: 优先实施 Phase 1 的 4 个核心功能，快速获得收益。
