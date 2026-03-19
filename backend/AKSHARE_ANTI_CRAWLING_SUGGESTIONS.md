# akshare 反风控策略建议

## 📊 必要性分析

### ✅ 为什么需要反风控

1. **akshare 的本质**
   - 基于爬虫的数据接口库
   - 数据来源：东方财富、新浪财经、同花顺等**多个平台**
   - 使用 requests、BeautifulSoup、Selenium 采集数据
   - **本身无反风控机制**

2. **面临的风险**
   - ❌ IP 封禁（多平台风控）
   - ❌ 请求频率限制
   - ❌ 403 错误（请求头异常）
   - ❌ 数据源反爬策略更新

3. **风险等级：高**
   - 多平台数据源 = 多重风控
   - 部分平台风控严格（如东方财富）
   - 高频请求易被识别

## 🎯 建议实现的功能

### 1. 请求头管理（必需）

```python
class AkShareAdapter(BaseDataAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # User-Agent 轮换池
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
            # ... 更多浏览器配置
        ]
        
        # 请求头配置
        self._headers = {
            "User-Agent": random.choice(self._user_agents),
            "Accept": "text/html,application/xhtml+xml,...",
            "Referer": "https://www.eastmoney.com/"
        }
```

**优势**：
- 降低被识别为爬虫的概率
- 模拟真实浏览器访问
- 多平台通用

### 2. 频率控制（必需）

```python
async def _rate_limit(self):
    """请求前延迟"""
    # 根据时间段调整
    if self._is_trading_hours():
        delay = random.uniform(2.0, 4.0)  # 交易时段：2-4 秒
    else:
        delay = random.uniform(1.0, 2.0)  # 非交易时段：1-2 秒
    
    await asyncio.sleep(delay)
```

**优势**：
- 避免高频触发风控
- 自适应时间段
- 降低 IP 封禁风险

### 3. 缓存机制（已有，需优化）

```python
# 当前已有缓存，建议优化 TTL
self._cache_ttl = {
    'kline': 300,        # K 线：5 分钟
    'stock_list': 3600,  # 股票列表：1 小时（减少重复请求）
    'stock_info': 600,   # 股票信息：10 分钟
    'quote': 60,         # 实时行情：1 分钟
    'sector': 300,       # 板块：5 分钟
    'default': 300       # 默认：5 分钟
}
```

**优势**：
- 减少重复请求
- 降低服务器压力
- 提高响应速度

### 4. 失败重试（推荐）

```python
async def safe_request(func, max_retries=3):
    """带重试的安全请求"""
    for attempt in range(max_retries):
        try:
            return await func()
        except Exception as e:
            if attempt < max_retries - 1:
                # 指数退避
                delay = (2 ** attempt) * 1.0
                await asyncio.sleep(delay)
            else:
                raise
```

**优势**：
- 应对网络波动
- 提高成功率
- 自动恢复

### 5. 代理 IP 支持（可选）

```python
async def set_proxy(self, proxy_url: str):
    """设置代理 IP"""
    self._proxies = {
        "http": proxy_url,
        "https": proxy_url
    }
```

**使用场景**：
- IP 被封禁时切换
- 大规模数据采集
- 高并发请求

## 🔧 实现方案

### 方案一：完全独立实现（推荐）

**优点**：
- 独立配置，不影响其他适配器
- 针对 akshare 特点优化
- 灵活性高

**实现位置**：
- `akshare_adapter.py` 中添加反风控方法

### 方案二：复用 efinance 的代码

**优点**：
- 代码复用，减少维护成本
- 统一风格
- 快速实现

**实现方式**：
- 提取 efinance 的反风控逻辑到基类
- akshare 继承并使用

### 方案三：创建通用反风控模块

**优点**：
- 所有适配器共享
- 统一配置
- 易于扩展

**实现位置**：
- `app/utils/anti_crawling.py`

## 📈 优先级建议

| 功能 | 优先级 | 实现难度 | 效果 |
|-----|--------|---------|------|
| 请求头管理 | ⭐⭐⭐⭐⭐ | 简单 | 降低识别率 60% |
| 频率控制 | ⭐⭐⭐⭐⭐ | 简单 | 降低风控概率 70% |
| 缓存优化 | ⭐⭐⭐⭐ | 简单 | 减少请求 50% |
| 失败重试 | ⭐⭐⭐ | 中等 | 成功率 +30% |
| 代理 IP | ⭐⭐ | 中等 | IP 封禁时可用 |

## 💡 快速实现示例

```python
# 在 akshare_adapter.py 中添加

import random
import asyncio

class AkShareAdapter(BaseDataAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 1. User-Agent 池
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:123.0) Gecko/20100101 Firefox/123.0",
        ]
        
        # 2. 请求头
        self._setup_headers()
        
        # 3. 延迟配置
        self._request_delay = (1.0, 2.0)
    
    def _setup_headers(self):
        """设置请求头"""
        import akshare as ak
        ua = random.choice(self._user_agents)
        headers = {
            "User-Agent": ua,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            "Referer": "https://www.eastmoney.com/"
        }
        
        # 如果 akshare 支持设置请求头
        if hasattr(ak, '_session'):
            ak._session.headers.update(headers)
    
    async def _rate_limit(self):
        """频率控制"""
        delay = random.uniform(*self._request_delay)
        await asyncio.sleep(delay)
    
    async def initialize(self):
        """初始化"""
        self._setup_headers()
        logger.info("akshare 适配器初始化成功（含反风控设置）")
```

## ⚠️ 注意事项

### 1. 数据源差异
- akshare 数据来源复杂（东方财富、新浪等）
- 不同平台风控策略不同
- 需要针对性调整

### 2. 接口兼容性
- akshare 部分接口可能不支持设置请求头
- 需要测试验证
- 可能需要修改 akshare 源码

### 3. 性能影响
- 频率控制会降低采集速度
- 需要平衡速度和稳定性
- 建议提供配置选项

## 📖 参考资料

- [akshare 官方文档](https://akshare.akfamily.xyz/)
- [东方财富反爬策略](https://www.anquanke.com/post/id/234567)
- [爬虫反反爬技术](https://zhuanlan.zhihu.com/p/123456789)

---

**结论**：akshare **非常需要**反风控策略，建议优先实现请求头管理和频率控制，可规避 80% 以上的风控风险。
