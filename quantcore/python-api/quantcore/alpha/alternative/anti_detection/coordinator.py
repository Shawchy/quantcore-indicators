import logging
import asyncio
from typing import Optional, Dict
from datetime import datetime
from .models import (
    SessionContext, ProxyInfo, SiteAntiDetectionStats, RiskLevel,
    FailurePhase, FailureRecord, RecoveryResult,
)
from .header_manager import RequestHeaderManager
from .proxy_pool import ProxyPoolManager
from .rate_limiter import IntelligentRateLimiter
from .tls_fingerprinter import TLSFingerprintManager
from .adaptive_limiter import AdaptiveRateLimiter
from .quality_scorer import ProxyQualityScorer
from .decision_engine import RiskDecisionEngine

logger = logging.getLogger(__name__)


class AntiDetectionCoordinator:
    """Anti-detection coordinator"""

    def __init__(self, config_path: Optional[str] = None):
        self.config = self._load_config(config_path)

        self.header_manager = RequestHeaderManager()
        self.proxy_pool = ProxyPoolManager(
            max_pool_size=self.config.get("proxy_pool_size", 100)
        )
        self.rate_limiter = IntelligentRateLimiter()
        self.tls_manager = TLSFingerprintManager()
        self.adaptive_limiter = AdaptiveRateLimiter()
        self.quality_scorer = ProxyQualityScorer()
        self.decision_engine = RiskDecisionEngine()

        self._stats: Dict[str, SiteAntiDetectionStats] = {}
        self._failure_tracker: Dict[str, list] = {}
        self._request_count: Dict[str, int] = {}

    def _load_config(self, config_path: Optional[str]) -> dict:
        """Load configuration"""
        import os
        import yaml

        if config_path and os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        return {}

    async def create_session(
        self,
        site_name: str,
        use_browser: bool = False,
    ) -> SessionContext:
        """Create anti-detection session"""
        context = SessionContext()

        proxy = self.proxy_pool.get_proxy(site_name)
        if proxy:
            context.proxy = proxy
        else:
            logger.warning(f"No proxy available for {site_name}")

        context.headers = self.header_manager.generate_headers(
            referer=self._get_site_referer(site_name)
        )

        tls_threshold = self.config.get("tls_rotation_threshold", 50)
        if self.tls_manager.rotation_count % tls_threshold == 0:
            self.tls_manager.rotate_profile()

        context.site_name = site_name
        context.created_at = datetime.now()

        return context

    async def before_request(
        self,
        site_name: str,
        session: SessionContext,
    ) -> None:
        """Pre-request preparation"""
        await self.rate_limiter.wait_if_needed(site_name)

        risk = self.decision_engine.assess_risk(
            data_source=site_name,
            metrics=self._collect_metrics(site_name),
        )

        if risk.level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            logger.warning(
                f"High risk detected for {site_name}: {risk.recommendation}"
            )
            await self._apply_risk_mitigation(site_name, session, risk)

    async def after_request(
        self,
        site_name: str,
        session: SessionContext,
        response_status: int,
        error: Optional[str] = None,
    ) -> None:
        """Post-request processing"""
        self._record_request(site_name)

        if response_status == 200:
            if session.proxy:
                self.proxy_pool.record_success(session.proxy.ip)
            self._record_success(site_name)

        elif response_status == 403 or response_status == 429:
            logger.warning(f"Anti-detection triggered for {site_name}: HTTP {response_status}")

            if session.proxy:
                self.proxy_pool.record_failure(
                    session.proxy.ip, f"HTTP_{response_status}"
                )

            self._record_failure(site_name, f"HTTP_{response_status}")

            await self._handle_ban(site_name, session)

        elif error:
            if session.proxy:
                self.proxy_pool.record_failure(session.proxy.ip, error)
            self._record_failure(site_name, error)

    def _get_site_referer(self, site_name: str) -> Optional[str]:
        """Get site referer"""
        referers = {
            "sina": "https://finance.sina.com.cn",
            "eastmoney": "https://www.eastmoney.com",
            "xueqiu": "https://xueqiu.com",
            "juchao": "http://www.cninfo.com.cn",
        }
        return referers.get(site_name)

    def _record_request(self, site_name: str):
        """Record request"""
        self._request_count[site_name] = self._request_count.get(site_name, 0) + 1

    def _record_success(self, site_name: str):
        """Record success"""
        if site_name not in self._stats:
            self._stats[site_name] = SiteAntiDetectionStats()
        self._stats[site_name].success_count += 1

    def _record_failure(self, site_name: str, error_type: str):
        """Record failure"""
        if site_name not in self._stats:
            self._stats[site_name] = SiteAntiDetectionStats()
        self._stats[site_name].failure_count += 1

        if site_name not in self._failure_tracker:
            self._failure_tracker[site_name] = []
        self._failure_tracker[site_name].append(
            FailureRecord(status=0, timestamp=datetime.now())
        )

    def _collect_metrics(self, site_name: str) -> Dict:
        """Collect metrics for risk assessment"""
        stats = self._stats.get(site_name)
        if not stats:
            return {}

        total = stats.success_count + stats.failure_count
        failure_rate = stats.failure_count / max(1, total)

        request_rate = self._request_count.get(site_name, 0)

        return {
            "failure_rate": failure_rate,
            "request_rate": request_rate,
        }

    async def _apply_risk_mitigation(
        self,
        site_name: str,
        session: SessionContext,
        risk,
    ):
        """Apply risk mitigation"""
        if session.proxy:
            new_proxy = self.proxy_pool.get_proxy(site_name)
            if new_proxy:
                session.proxy = new_proxy
                logger.info(f"Switched proxy for {site_name}")

        if self.tls_manager:
            self.tls_manager.rotate_profile()

        await asyncio.sleep(5)

    async def _handle_ban(
        self,
        site_name: str,
        session: SessionContext,
    ) -> None:
        """Handle ban situation"""
        new_proxy = self.proxy_pool.get_proxy(site_name)
        if new_proxy:
            session.proxy = new_proxy
            logger.info(f"Switched proxy for {site_name} after ban")

        self._stats[site_name].ban_count += 1
        self._stats[site_name].last_ban_time = datetime.now()

        await asyncio.sleep(10)

    def get_overall_stats(self) -> Dict:
        """Get overall anti-detection stats"""
        return {
            site: stats.to_dict()
            for site, stats in self._stats.items()
        }
