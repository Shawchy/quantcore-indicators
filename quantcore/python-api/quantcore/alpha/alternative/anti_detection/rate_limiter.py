import random
import logging
import asyncio
from typing import Dict, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class IntelligentRateLimiter:
    """Intelligent rate limiter"""

    SITE_RATE_LIMITS = {
        "sina_news": {
            "requests_per_minute": 30,
            "requests_per_hour": 500,
            "delay_distribution": "gaussian",
            "mean_delay": 2.0,
            "std_delay": 0.5,
        },
        "eastmoney_news": {
            "requests_per_minute": 20,
            "requests_per_hour": 300,
            "delay_distribution": "gaussian",
            "mean_delay": 3.0,
            "std_delay": 1.0,
        },
        "juchao": {
            "requests_per_minute": 10,
            "requests_per_hour": 100,
            "delay_distribution": "uniform",
            "min_delay": 5.0,
            "max_delay": 15.0,
        },
        "xueqiu": {
            "requests_per_minute": 5,
            "requests_per_hour": 50,
            "delay_distribution": "gaussian",
            "mean_delay": 12.0,
            "std_delay": 3.0,
        },
        "eastmoney_guba": {
            "requests_per_minute": 8,
            "requests_per_hour": 80,
            "delay_distribution": "gaussian",
            "mean_delay": 8.0,
            "std_delay": 2.0,
        },
        "taoguba": {
            "requests_per_minute": 3,
            "requests_per_hour": 30,
            "delay_distribution": "uniform",
            "min_delay": 15.0,
            "max_delay": 30.0,
        },
    }

    def __init__(self):
        self._request_history: Dict[str, List[datetime]] = {}
        self._daily_stats: Dict[str, Dict] = {}

    async def wait_if_needed(self, site_name: str):
        """Wait based on site policy"""
        config = self.SITE_RATE_LIMITS.get(site_name)
        if not config:
            return

        now = datetime.now()

        minute_ago = now - timedelta(minutes=1)
        recent_requests = [
            t
            for t in self._request_history.get(site_name, [])
            if t > minute_ago
        ]

        if len(recent_requests) >= config["requests_per_minute"]:
            wait_seconds = 60 - (now - recent_requests[0]).total_seconds()
            logger.warning(
                f"Triggered {site_name} minute limit, waiting {wait_seconds:.1f}s"
            )
            await asyncio.sleep(wait_seconds)

        hour_ago = now - timedelta(hours=1)
        hour_requests = [
            t
            for t in self._request_history.get(site_name, [])
            if t > hour_ago
        ]

        if len(hour_requests) >= config["requests_per_hour"]:
            wait_seconds = 3600 - (now - hour_requests[0]).total_seconds()
            logger.warning(
                f"Triggered {site_name} hour limit, waiting {wait_seconds:.1f}s"
            )
            await asyncio.sleep(wait_seconds)

        delay = self._generate_delay(config)
        if delay > 0:
            await asyncio.sleep(delay)

        self._request_history.setdefault(site_name, []).append(now)

    def _generate_delay(self, config: Dict) -> float:
        """Generate delay (gaussian or uniform distribution)"""
        dist = config.get("delay_distribution", "gaussian")

        if dist == "gaussian":
            delay = random.gauss(
                config["mean_delay"],
                config["std_delay"],
            )
            return max(0.5, delay)
        elif dist == "uniform":
            return random.uniform(
                config["min_delay"],
                config["max_delay"],
            )

        return 0

    def get_site_stats(self, site_name: str) -> Dict:
        """Get site request statistics"""
        now = datetime.now()
        history = self._request_history.get(site_name, [])

        minute_count = len(
            [t for t in history if t > now - timedelta(minutes=1)]
        )
        hour_count = len(
            [t for t in history if t > now - timedelta(hours=1)]
        )

        config = self.SITE_RATE_LIMITS.get(site_name, {})

        return {
            "requests_per_minute": minute_count,
            "requests_per_hour": hour_count,
            "limit_per_minute": config.get("requests_per_minute", 0),
            "limit_per_hour": config.get("requests_per_hour", 0),
            "minute_usage": minute_count
            / max(1, config.get("requests_per_minute", 1)),
            "hour_usage": hour_count
            / max(1, config.get("requests_per_hour", 1)),
        }
