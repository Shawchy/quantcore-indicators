import re
import random
from typing import Optional, Dict, List


class RequestHeaderManager:
    """Request header spoofing manager"""

    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
    ]

    PLATFORM_HEADERS = {
        "Windows": {
            "Sec-CH-UA-Platform": '"Windows"',
            "Sec-CH-UA-Platform-Version": '"15.0.0"',
        },
        "macOS": {
            "Sec-CH-UA-Platform": '"macOS"',
            "Sec-CH-UA-Platform-Version": '"14.1.1"',
        },
        "Linux": {
            "Sec-CH-UA-Platform": '"Linux"',
            "Sec-CH-UA-Platform-Version": '"5.15.0"',
        },
    }

    COMMON_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
    }

    def __init__(self):
        self._last_ua: Optional[str] = None
        self._rotation_count: int = 0

    def generate_headers(self, referer: Optional[str] = None) -> Dict[str, str]:
        """Generate complete request headers"""
        ua = random.choice(self.USER_AGENTS)
        platform = self._detect_platform(ua)

        headers = {
            "User-Agent": ua,
            **self.COMMON_HEADERS,
            **self.PLATFORM_HEADERS.get(platform, {}),
        }

        if referer:
            headers["Referer"] = referer

        headers["Sec-CH-UA"] = self._extract_sec_ch_ua(ua)
        headers["Sec-CH-UA-Mobile"] = "?0"

        self._last_ua = ua
        self._rotation_count += 1

        return headers

    def rotate_user_agent(self) -> str:
        """Rotate to a different user agent"""
        available = [ua for ua in self.USER_AGENTS if ua != self._last_ua]
        new_ua = random.choice(available)
        self._last_ua = new_ua
        return new_ua

    def _detect_platform(self, ua: str) -> str:
        """Detect platform from User-Agent"""
        if "Windows" in ua:
            return "Windows"
        elif "Macintosh" in ua or "Mac OS X" in ua:
            return "macOS"
        elif "Linux" in ua:
            return "Linux"
        return "Windows"

    def _extract_sec_ch_ua(self, ua: str) -> str:
        """Extract Sec-CH-UA information"""
        if "Chrome" in ua:
            version = re.search(r"Chrome/(\d+)", ua)
            if version:
                major = version.group(1)
                return f'"Not_A Brand";v="8", "Chromium";v="{major}", "Google Chrome";v="{major}"'
        return '"Not_A Brand";v="99", "Chromium";v="120"'

    @property
    def rotation_count(self) -> int:
        return self._rotation_count
