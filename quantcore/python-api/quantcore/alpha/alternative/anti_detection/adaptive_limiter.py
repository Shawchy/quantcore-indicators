import asyncio
import random
import time
from typing import Dict


class AdaptiveRateLimiter:
    """Adaptive rate limiter (based on Seadex AdaptiveRateLimiter)"""

    def __init__(
        self,
        min_interval: float = 1.0,
        max_interval: float = 10.0,
        burst_protection: bool = True,
        max_burst: int = 5,
    ):
        self.base_min_interval = min_interval
        self.base_max_interval = max_interval
        self.current_interval = min_interval
        self.last_request = time.time()

        self.success_count = 0
        self.failure_count = 0
        self.block_count = 0

        self.jitter_enabled = True
        self.burst_protection = burst_protection
        self.max_burst = max_burst
        self.burst_counter = 0

    def calculate_interval(self) -> float:
        """Calculate request interval based on success rate"""
        base = self.base_min_interval
        range_val = self.base_max_interval - self.base_min_interval

        total = self.success_count + self.failure_count
        if total > 10:
            success_rate = self.success_count / total

            if success_rate < 0.5:
                base *= 3
            elif success_rate < 0.7:
                base *= 1.5
            elif success_rate > 0.95 and total > 50:
                base /= 1.5
                base = max(base, self.base_min_interval)

        if self.block_count > 5:
            base *= 4
        elif self.block_count > 2:
            base *= 2

        base = max(self.base_min_interval, base)
        base = min(self.base_max_interval * 5, base)

        self.current_interval = base

        if self.jitter_enabled:
            jitter = random.uniform(0, range_val * 0.5)
            base += jitter

        return base

    async def wait(self) -> None:
        """Wait until can send request (async version)"""
        interval = self.calculate_interval()
        elapsed = time.time() - self.last_request

        if elapsed < interval:
            sleep_time = interval - elapsed
            await asyncio.sleep(sleep_time)

        self.last_request = time.time()

        if self.burst_protection:
            self.burst_counter += 1
            if self.burst_counter >= self.max_burst:
                extra_delay = self.current_interval * 2
                await asyncio.sleep(extra_delay)
                self.burst_counter = 0

    def report_success(self) -> None:
        self.success_count += 1

    def report_failure(self) -> None:
        self.failure_count += 1

    def report_block(self) -> None:
        self.block_count += 1

    def get_stats(self) -> Dict:
        total = self.success_count + self.failure_count
        success_rate = self.success_count / total if total > 0 else 0

        return {
            "current_interval": self.current_interval,
            "success_rate": success_rate,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "block_count": self.block_count,
            "burst_counter": self.burst_counter,
        }

    def reset_stats(self) -> None:
        self.success_count = 0
        self.failure_count = 0
        self.block_count = 0
        self.burst_counter = 0
        self.current_interval = self.base_min_interval
