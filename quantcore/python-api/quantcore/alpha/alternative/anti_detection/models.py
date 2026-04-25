from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any


@dataclass
class ProxyInfo:
    ip: str
    port: int
    proxy_type: str
    username: Optional[str] = None
    password: Optional[str] = None
    status: str = "active"
    use_count: int = 0
    last_check: Optional[datetime] = None

    def is_available(self) -> bool:
        return self.status == "active" and (
            self.last_check is None
            or (datetime.now() - self.last_check).total_seconds() < 600
        )


@dataclass
class ProxyStats:
    success_rate: float = 100.0
    quality_score: float = 50.0
    avg_latency: float = 0.0
    consecutive_fail: int = 0
    success_count: int = 0
    failure_count: int = 0
    anonymity_level: str = "anonymous"
    last_success: Optional[datetime] = None
    last_failure: Optional[datetime] = None


@dataclass
class CookieInfo:
    value: Dict[str, str]
    created_at: datetime
    account: str
    use_count: int = 0
    expires_at: Optional[datetime] = None

    def is_valid(self) -> bool:
        if self.expires_at:
            return datetime.now() < self.expires_at
        return (datetime.now() - self.created_at).total_seconds() < 3600


@dataclass
class AccountInfo:
    username: str
    password: str
    user_agent: str


@dataclass
class SessionContext:
    site_name: str = ""
    proxy: Optional[ProxyInfo] = None
    headers: Dict[str, str] = field(default_factory=dict)
    cookies: Optional[Dict[str, str]] = None
    browser_config: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None


@dataclass
class SiteAntiDetectionStats:
    success_count: int = 0
    failure_count: int = 0
    ban_count: int = 0
    last_ban_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "ban_count": self.ban_count,
            "success_rate": self.success_count
            / max(1, self.success_count + self.failure_count),
        }


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskAssessment:
    score: float
    level: RiskLevel
    factors: List[str]
    timestamp: datetime
    data_source: str
    recommendation: str = ""


@dataclass
class Adjustment:
    reason: str
    change_interval: bool = False
    new_min_interval: float = 0.0
    new_max_interval: float = 0.0
    enable_extra_check: bool = False
    extra_checks: List[str] = field(default_factory=list)


@dataclass
class Credentials:
    domain: str
    cookies: Dict[str, str]
    tokens: Dict[str, str]
    user_agent: str
    obtained_at: datetime
    expires_at: datetime

    def is_valid(self) -> bool:
        return datetime.now() < self.expires_at


@dataclass
class TokenExtractorConfig:
    name: str
    type: str
    selector: str


@dataclass
class DomainConfig:
    init_url: str
    refresh_interval: int
    required_tokens: List[TokenExtractorConfig] = field(default_factory=list)


class BrowserSession:
    def __init__(
        self,
        browser: Any,
        context: Any,
        page: Any,
        domain: str,
        created_at: float,
        last_used: float,
    ):
        self.browser = browser
        self.context = context
        self.page = page
        self.domain = domain
        self.created_at = created_at
        self.last_used = last_used


@dataclass
class BrowserStats:
    total_launches: int = 0
    total_closures: int = 0
    active_sessions: int = 0
    credentials_issued: int = 0


class FailurePhase(Enum):
    IP_BAN = "ip_ban"
    RATE_LIMIT = "rate_limit"
    COOKIE_EXPIRED = "cookie_expired"
    FINGERPRINT_DETECTED = "fingerprint_detected"


@dataclass
class FailureRecord:
    status: int
    timestamp: datetime


@dataclass
class RecoveryResult:
    success: bool
    action: str
    message: str
