import random
from typing import Dict, List
from datetime import datetime
from .models import ProxyInfo, ProxyStats


class ProxyQualityScorer:
    """Proxy quality scorer (based on Seadex ProxyPool)"""

    ANONYMITY_BONUS = {
        "elite": 10.0,
        "anonymous": 7.0,
        "transparent": 3.0,
    }

    def __init__(self):
        self.proxy_stats: Dict[str, ProxyStats] = {}

    def calculate_quality_score(self, stats: ProxyStats) -> float:
        """Calculate proxy quality score (0-100)"""
        score = 0.0

        score += stats.success_rate * 0.4

        latency_score = 100.0
        if stats.avg_latency > 0:
            latency_ms = stats.avg_latency * 1000
            latency_score = max(0, 100.0 - (latency_ms / 100) * 10)
        score += latency_score * 0.3

        stability_score = max(0, 100.0 - stats.consecutive_fail * 10)
        score += stability_score * 0.2

        score += self.ANONYMITY_BONUS.get(stats.anonymity_level, 5.0)

        return max(0.0, min(100.0, score))

    def get_weighted_proxy(self, available_proxies: List[ProxyInfo]) -> ProxyInfo:
        """Select proxy based on weighted score"""
        if not available_proxies:
            raise ValueError("No available proxies")

        total_weight = 0.0
        for proxy in available_proxies:
            stats = self.proxy_stats.get(proxy.ip)
            if stats:
                stats.quality_score = self.calculate_quality_score(stats)
                total_weight += stats.quality_score
            else:
                total_weight += 50.0

        r = random.uniform(0, total_weight)
        cumulative = 0.0

        for proxy in available_proxies:
            stats = self.proxy_stats.get(proxy.ip)
            weight = stats.quality_score if stats else 50.0
            cumulative += weight
            if r < cumulative:
                return proxy

        return available_proxies[0]

    def get_top_proxies(self, proxies: List[ProxyInfo], n: int) -> List[ProxyInfo]:
        """Get top N proxies by score"""
        scored = []
        for proxy in proxies:
            stats = self.proxy_stats.get(proxy.ip)
            score = stats.quality_score if stats else 50.0
            scored.append((proxy, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        return [p for p, s in scored[:n]]

    def report_result(self, proxy_ip: str, success: bool, latency: float) -> None:
        """Report proxy usage result"""
        if proxy_ip not in self.proxy_stats:
            self.proxy_stats[proxy_ip] = ProxyStats(
                success_rate=100.0,
                quality_score=50.0,
            )

        stats = self.proxy_stats[proxy_ip]

        if success:
            stats.success_count += 1
            stats.last_success = datetime.now()
            stats.consecutive_fail = 0

            if latency > 0 and stats.success_count > 0:
                total_latency = stats.avg_latency * (stats.success_count - 1) + latency
                stats.avg_latency = total_latency / stats.success_count
        else:
            stats.failure_count += 1
            stats.last_failure = datetime.now()
            stats.consecutive_fail += 1

        total = stats.success_count + stats.failure_count
        if total > 0:
            stats.success_rate = (stats.success_count / total) * 100

        stats.quality_score = self.calculate_quality_score(stats)
