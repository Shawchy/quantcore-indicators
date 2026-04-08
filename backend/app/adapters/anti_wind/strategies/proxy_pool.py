"""
代理池策略

管理多个代理 IP，自动选择最优代理，报告成功/失败状态。
"""

from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger
from .base import BaseStrategy
import random


class ProxyInfo:
    """代理信息类"""
    
    def __init__(
        self,
        host: str,
        port: int,
        protocol: str = "http",
        username: Optional[str] = None,
        password: Optional[str] = None
    ):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.username = username
        self.password = password
        self.status = "available"  # available, busy, blocked
        self.last_used: Optional[datetime] = None
        self.success_count = 0
        self.fail_count = 0
        self.avg_response_time = 0.0
        self.blocked_until: Optional[datetime] = None
        self.consecutive_fails = 0
    
    @property
    def url(self) -> str:
        """获取代理 URL"""
        if self.username and self.password:
            return f"{self.protocol}://{self.username}:{self.password}@{self.host}:{self.port}"
        return f"{self.protocol}://{self.host}:{self.port}"
    
    @property
    def success_rate(self) -> float:
        """计算成功率"""
        total = self.success_count + self.fail_count
        if total == 0:
            return 0.5
        return self.success_count / total
    
    def __repr__(self) -> str:
        return f"ProxyInfo({self.host}:{self.port}, status={self.status}, success_rate={self.success_rate:.1%})"


class ProxyPoolStrategy(BaseStrategy):
    """代理池策略
    
    功能：
    1. 管理多个代理 IP
    2. 自动选择最优代理（基于成功率和响应时间）
    3. 自动屏蔽失败过多的代理
    4. 支持代理轮换
    
    配置参数：
    - min_success_rate: 最小成功率阈值（默认 0.3）
    - block_duration_minutes: 屏蔽时长（分钟，默认 30）
    - max_consecutive_fails: 最大连续失败次数（默认 3）
    - cooldown_seconds: 代理冷却时间（默认 5 秒）
    - proxies: 初始代理列表
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        self._proxies: List[ProxyInfo] = []
        self._current_proxy: Optional[ProxyInfo] = None
        
        # 配置参数
        self._min_success_rate = self.config.get('min_success_rate', 0.3)
        self._block_duration_minutes = self.config.get('block_duration_minutes', 30)
        self._max_consecutive_fails = self.config.get('max_consecutive_fails', 3)
        self._cooldown_seconds = self.config.get('cooldown_seconds', 5)
        
        # 初始化时添加代理
        proxies_config = self.config.get('proxies', [])
        for proxy_cfg in proxies_config:
            self.add_proxy(**proxy_cfg)
        
        logger.info(f"代理池策略已初始化：{len(self._proxies)}个代理")
    
    def add_proxy(
        self,
        host: str,
        port: int,
        protocol: str = "http",
        username: Optional[str] = None,
        password: Optional[str] = None
    ) -> None:
        """添加代理到池中"""
        proxy = ProxyInfo(host, port, protocol, username, password)
        self._proxies.append(proxy)
        logger.debug(f"代理已添加：{host}:{port}")
    
    def add_proxies_from_list(self, proxy_list: List[str]) -> int:
        """从字符串列表批量添加代理
        
        格式：
        - "host:port"
        - "protocol://host:port"
        - "protocol://username:password@host:port"
        """
        count = 0
        for proxy_str in proxy_list:
            try:
                # 解析代理字符串
                if "://" in proxy_str:
                    protocol, rest = proxy_str.split("://", 1)
                else:
                    protocol = "http"
                    rest = proxy_str
                
                if "@" in rest:
                    auth, host_port = rest.split("@", 1)
                    username, password = auth.split(":", 1)
                else:
                    username = password = None
                    host_port = rest
                
                host, port_str = host_port.split(":", 1)
                port = int(port_str)
                
                self.add_proxy(host, port, protocol, username, password)
                count += 1
            except Exception as e:
                logger.warning(f"解析代理失败：{proxy_str}, 错误：{e}")
        
        return count
    
    def _get_available_proxy(self) -> Optional[ProxyInfo]:
        """获取可用代理"""
        if not self._proxies:
            return None
        
        now = datetime.now()
        available_proxies = []
        
        for proxy in self._proxies:
            # 检查是否被屏蔽
            if proxy.status == "blocked":
                if proxy.blocked_until and now < proxy.blocked_until:
                    continue
                else:
                    proxy.status = "available"
                    proxy.blocked_until = None
            
            # 检查是否可用
            if proxy.status == "available":
                # 检查冷却时间
                if proxy.last_used:
                    elapsed = (now - proxy.last_used).total_seconds()
                    if elapsed < self._cooldown_seconds:
                        continue
                
                # 检查成功率
                if proxy.success_rate >= self._min_success_rate:
                    available_proxies.append(proxy)
        
        if not available_proxies:
            logger.debug("没有可用的代理 IP")
            return None
        
        # 按成功率和响应时间排序，选择最优的
        available_proxies.sort(key=lambda p: (-p.success_rate, p.avg_response_time))
        
        # 从前 3 个中随机选择一个（避免总是用同一个）
        top_proxies = available_proxies[:min(3, len(available_proxies))]
        selected = random.choice(top_proxies)
        
        return selected
    
    async def before_request(self, url: str, method: str, headers: Dict[str, str]) -> Dict[str, str]:
        """请求前选择代理"""
        if not self.is_enabled():
            return headers
        
        proxy = self._get_available_proxy()
        if proxy:
            proxy.status = "busy"
            proxy.last_used = datetime.now()
            self._current_proxy = proxy
            
            # 将代理信息添加到 headers（供后续使用）
            headers = headers.copy()
            headers['X-Proxy-Host'] = proxy.host
            headers['X-Proxy-Port'] = str(proxy.port)
            headers['X-Proxy-URL'] = proxy.url
            
            logger.debug(f"使用代理：{proxy.host}:{proxy.port} (成功率：{proxy.success_rate:.1%})")
        else:
            self._current_proxy = None
            logger.debug("未使用代理（无可用代理或策略禁用）")
        
        return headers
    
    async def after_request(self, response: Any) -> Any:
        """请求后报告结果"""
        if not self.is_enabled():
            return response
        
        if self._current_proxy:
            proxy = self._current_proxy
            
            # 判断请求是否成功
            success = False
            response_time = 0.0
            
            if isinstance(response, dict):
                success = response.get('success', False)
                response_time = response.get('response_time', 0.0)
            elif hasattr(response, 'status_code'):
                success = 200 <= response.status_code < 400
                response_time = getattr(response, 'response_time', 0.0)
            
            if success:
                self._report_success(proxy, response_time)
            else:
                error_msg = response.get('error', 'Unknown') if isinstance(response, dict) else 'Unknown'
                self._report_failure(proxy, error_msg)
            
            # 重置当前代理引用
            self._current_proxy = None
        
        return response
    
    def _report_success(self, proxy: ProxyInfo, response_time: float) -> None:
        """报告成功"""
        proxy.success_count += 1
        proxy.status = "available"
        proxy.consecutive_fails = 0
        
        # 更新平均响应时间（加权平均）
        if proxy.avg_response_time == 0:
            proxy.avg_response_time = response_time
        else:
            proxy.avg_response_time = proxy.avg_response_time * 0.8 + response_time * 0.2
        
        logger.debug(f"代理成功：{proxy.host}:{proxy.port}, 成功率：{proxy.success_rate:.1%}")
    
    def _report_failure(self, proxy: ProxyInfo, error: str) -> None:
        """报告失败"""
        proxy.fail_count += 1
        proxy.consecutive_fails += 1
        
        # 连续失败过多，屏蔽代理
        if proxy.consecutive_fails >= self._max_consecutive_fails:
            proxy.status = "blocked"
            proxy.blocked_until = datetime.now() + timedelta(minutes=self._block_duration_minutes)
            logger.warning(f"代理已屏蔽：{proxy.host}:{proxy.port}, 原因：{error}")
        else:
            proxy.status = "available"
    
    def get_status(self) -> Dict[str, Any]:
        """获取代理池状态"""
        available = sum(1 for p in self._proxies if p.status == "available")
        busy = sum(1 for p in self._proxies if p.status == "busy")
        blocked = sum(1 for p in self._proxies if p.status == "blocked")
        
        return {
            'total': len(self._proxies),
            'available': available,
            'busy': busy,
            'blocked': blocked,
            'proxies': [
                {
                    'host': p.host,
                    'port': p.port,
                    'status': p.status,
                    'success_rate': f"{p.success_rate:.1%}",
                    'success_count': p.success_count,
                    'fail_count': p.fail_count,
                }
                for p in self._proxies[:10]  # 只显示前 10 个
            ]
        }
    
    def clear_blocked(self) -> int:
        """清空所有被屏蔽的代理"""
        count = 0
        for proxy in self._proxies:
            if proxy.status == "blocked":
                proxy.status = "available"
                proxy.blocked_until = None
                count += 1
        logger.info(f"已清空 {count} 个被屏蔽的代理")
        return count
