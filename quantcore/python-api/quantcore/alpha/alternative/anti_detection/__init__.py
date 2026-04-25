from .models import (
    ProxyInfo, ProxyStats, CookieInfo, AccountInfo,
    SessionContext, SiteAntiDetectionStats,
    RiskLevel, RiskAssessment, Adjustment,
    Credentials, TokenExtractorConfig, DomainConfig,
    BrowserSession, BrowserStats,
    FailurePhase, FailureRecord, RecoveryResult,
)
from .header_manager import RequestHeaderManager
from .proxy_pool import ProxyPoolManager
from .rate_limiter import IntelligentRateLimiter
from .tls_fingerprinter import TLSFingerprintManager
from .adaptive_limiter import AdaptiveRateLimiter
from .quality_scorer import ProxyQualityScorer
from .decision_engine import RiskDecisionEngine
from .coordinator import AntiDetectionCoordinator

__version__ = "1.0.0"
__all__ = [
    # Models
    "ProxyInfo", "ProxyStats", "CookieInfo", "AccountInfo",
    "SessionContext", "SiteAntiDetectionStats",
    "RiskLevel", "RiskAssessment", "Adjustment",
    "Credentials", "TokenExtractorConfig", "DomainConfig",
    "BrowserSession", "BrowserStats",
    "FailurePhase", "FailureRecord", "RecoveryResult",
    # Components
    "RequestHeaderManager",
    "ProxyPoolManager",
    "IntelligentRateLimiter",
    "TLSFingerprintManager",
    "AdaptiveRateLimiter",
    "ProxyQualityScorer",
    "RiskDecisionEngine",
    "AntiDetectionCoordinator",
]
