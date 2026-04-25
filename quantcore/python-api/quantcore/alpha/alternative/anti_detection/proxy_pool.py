import random
import logging
from typing import Optional, Dict, List, Set
from datetime import datetime
from .models import ProxyInfo

logger = logging.getLogger(__name__)


class ProxyPoolManager:
    """Proxy pool manager"""

    PROXY_TYPES = {
        "residential": {
            "priority": "high",
            "sites": ["xueqiu", "eastmoney_guba", "taoguba"],
            "cost": "high",
            "success_rate": 0.95,
        },
        "datacenter": {
            "priority": "medium",
            "sites": ["sina", "eastmoney_news", "cls"],
            "cost": "low",
            "success_rate": 0.85,
        },
        "mobile": {
            "priority": "critical",
            "sites": ["juchao", "sse", "szse"],
            "cost": "very_high",
            "success_rate": 0.98,
        },
    }

    DEFAULT_TEST_ENDPOINTS = [
        "https://httpbin.org/ip",
        "https://api.ipify.org?format=json",
        "https://ifconfig.me/ip",
    ]

    def __init__(
        self,
        max_pool_size: int = 100,
        health_check_interval: int = 300,
        ban_threshold: int = 3,
        test_endpoints: Optional[List[str]] = None,
    ):
        self.max_pool_size = max_pool_size
        self.health_check_interval = health_check_interval
        self.ban_threshold = ban_threshold
        self.test_endpoints = test_endpoints or self.DEFAULT_TEST_ENDPOINTS
        self._endpoint_index = 0

        self._pool: List[ProxyInfo] = []
        self._failed_proxies: Dict[str, int] = {}
        self._healthy_proxies: Set[str] = set()

    def add_proxy(self, proxy: ProxyInfo):
        """Add proxy to pool"""
        if len(self._pool) < self.max_pool_size:
            self._pool.append(proxy)
            self._healthy_proxies.add(proxy.ip)
            logger.info(f"Added proxy {proxy.ip}:{proxy.port} ({proxy.proxy_type})")

    def remove_proxy(self, ip: str):
        """Remove proxy from pool"""
        self._pool = [p for p in self._pool if p.ip != ip]
        self._healthy_proxies.discard(ip)
        self._failed_proxies.pop(ip, None)
        logger.info(f"Removed proxy {ip}")

    def get_proxy(self, site_name: str) -> Optional[ProxyInfo]:
        """Get proxy suitable for specified site"""
        proxy_type = self._get_proxy_type_for_site(site_name)

        healthy = [
            p
            for p in self._pool
            if p.proxy_type == proxy_type
            and p.ip in self._healthy_proxies
            and p.is_available()
        ]

        if healthy:
            proxy = random.choice(healthy)
            proxy.use_count += 1
            return proxy

        available = [
            p
            for p in self._pool
            if p.proxy_type == proxy_type and p.is_available()
        ]

        if available:
            proxy = random.choice(available)
            proxy.use_count += 1
            return proxy

        return None

    def record_success(self, proxy_ip: str):
        """Record proxy success request"""
        if proxy_ip in self._failed_proxies:
            self._failed_proxies[proxy_ip] = max(
                0, self._failed_proxies[proxy_ip] - 1
            )
            if self._failed_proxies[proxy_ip] == 0:
                self._healthy_proxies.add(proxy_ip)

    def record_failure(self, proxy_ip: str, error_type: str):
        """Record proxy failure request"""
        self._failed_proxies[proxy_ip] = (
            self._failed_proxies.get(proxy_ip, 0) + 1
        )

        if self._failed_proxies[proxy_ip] >= self.ban_threshold:
            self._healthy_proxies.discard(proxy_ip)

            if "ban" in error_type.lower() or "403" in error_type:
                self._mark_proxy_banned(proxy_ip)

    def _get_proxy_type_for_site(self, site_name: str) -> str:
        """Get proxy type for site"""
        for proxy_type, config in self.PROXY_TYPES.items():
            if site_name in config["sites"]:
                return proxy_type
        return "datacenter"

    def _mark_proxy_banned(self, proxy_ip: str):
        """Mark proxy as banned"""
        for proxy in self._pool:
            if proxy.ip == proxy_ip:
                proxy.status = "banned"
                break

    async def health_check(self):
        """Proxy health check"""
        for proxy in self._pool:
            if proxy.status == "banned":
                continue

            try:
                await self._test_proxy(proxy)
                proxy.last_check = datetime.now()
                self._healthy_proxies.add(proxy.ip)
            except Exception:
                self._healthy_proxies.discard(proxy.ip)

    def _get_test_url(self) -> str:
        """Get next test endpoint (round-robin)"""
        url = self.test_endpoints[self._endpoint_index % len(self.test_endpoints)]
        self._endpoint_index += 1
        return url

    async def _test_proxy(self, proxy: ProxyInfo) -> bool:
        """Test single proxy"""
        import aiohttp

        test_url = self._get_test_url()

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    test_url,
                    proxy=f"http://{proxy.ip}:{proxy.port}",
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response:
                    return response.status == 200
            except Exception:
                return False

    @property
    def pool_size(self) -> int:
        return len(self._pool)

    @property
    def healthy_count(self) -> int:
        return len(self._healthy_proxies)
