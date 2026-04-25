import logging
from typing import Dict, List, Callable, Optional
from datetime import datetime
from .models import RiskLevel, RiskAssessment, Adjustment

logger = logging.getLogger(__name__)


class RiskDecisionEngine:
    """Risk decision engine (based on Seadex DecisionEngine)"""

    DEFAULT_INDICATORS = {
        "failure_rate": {
            "threshold": 0.3,
            "weight": 0.25,
            "description": "Request failure rate",
        },
        "avg_latency": {
            "threshold": 5000,
            "weight": 0.20,
            "description": "Average response latency (ms)",
        },
        "consecutive_failures": {
            "threshold": 5,
            "weight": 0.20,
            "description": "Consecutive failure count",
        },
        "request_rate": {
            "threshold": 100,
            "weight": 0.15,
            "description": "Request rate (per minute)",
        },
        "error_response_rate": {
            "threshold": 0.2,
            "weight": 0.20,
            "description": "Error response code ratio",
        },
    }

    def __init__(self, indicators: Optional[Dict] = None):
        self.indicators = indicators or self.DEFAULT_INDICATORS
        self.history: List[RiskAssessment] = []
        self.alert_callbacks: List[Callable] = []
        self.auto_adjust_enabled = True

    def assess_risk(
        self,
        data_source: str,
        metrics: Dict[str, float],
    ) -> RiskAssessment:
        """Assess risk based on metrics"""
        assessment = RiskAssessment(
            score=0.0,
            level=RiskLevel.LOW,
            factors=[],
            timestamp=datetime.now(),
            data_source=data_source,
        )

        total_weight = 0.0
        weighted_score = 0.0

        for name, indicator in self.indicators.items():
            value = metrics.get(name)
            if value is None:
                continue

            risk_score = self._calculate_indicator_risk(value, indicator)

            if risk_score > 0:
                assessment.factors.append(
                    f"{name}={value} (threshold={indicator['threshold']})"
                )

            weighted_score += risk_score * indicator["weight"]
            total_weight += indicator["weight"]

        if total_weight > 0:
            assessment.score = min(100, weighted_score / total_weight * 100)

        assessment.level = self._determine_risk_level(assessment.score)
        assessment.recommendation = self._generate_recommendation(assessment)

        self.history.append(assessment)
        if len(self.history) > 1000:
            self.history.pop(0)

        if assessment.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            self._trigger_alert(assessment)

        if self.auto_adjust_enabled:
            adjustment = self._generate_adjustment(assessment)
            self._apply_adjustment(data_source, adjustment)

        return assessment

    def register_alert_callback(self, callback: Callable):
        """Register alert callback"""
        self.alert_callbacks.append(callback)

    def _calculate_indicator_risk(
        self, value: float, indicator: Dict
    ) -> float:
        """Calculate single indicator risk score"""
        if value <= indicator["threshold"]:
            return 0.0

        ratio = value / indicator["threshold"]
        risk_score = min(100, (ratio - 1) * 50)

        return risk_score

    def _determine_risk_level(self, score: float) -> RiskLevel:
        """Determine risk level"""
        if score >= 80:
            return RiskLevel.CRITICAL
        elif score >= 60:
            return RiskLevel.HIGH
        elif score >= 40:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_recommendation(self, assessment: RiskAssessment) -> str:
        """Generate recommendation"""
        if assessment.level == RiskLevel.CRITICAL:
            return "Stop immediately, check anti-detection strategy, switch proxy pool, refresh all cookies"
        elif assessment.level == RiskLevel.HIGH:
            return "Reduce request rate, upgrade anti-detection strategy, consider using browser for cookies"
        elif assessment.level == RiskLevel.MEDIUM:
            return "Moderately reduce request rate, monitor success rate, prepare fallback plan"
        else:
            return "Maintain current strategy, continue monitoring"

    def _generate_adjustment(self, assessment: RiskAssessment) -> Adjustment:
        """Generate strategy adjustment"""
        adjustment = Adjustment(reason=assessment.recommendation)

        if assessment.level == RiskLevel.CRITICAL:
            adjustment.change_interval = True
            adjustment.new_min_interval = 5.0
            adjustment.new_max_interval = 15.0
            adjustment.enable_extra_check = True
            adjustment.extra_checks = [
                "cookie_validation",
                "proxy_check",
                "fingerprint_check",
            ]

        elif assessment.level == RiskLevel.HIGH:
            adjustment.change_interval = True
            adjustment.new_min_interval = 3.0
            adjustment.new_max_interval = 10.0
            adjustment.enable_extra_check = True
            adjustment.extra_checks = ["cookie_validation", "proxy_check"]

        elif assessment.level == RiskLevel.MEDIUM:
            adjustment.change_interval = True
            adjustment.new_min_interval = 2.0
            adjustment.new_max_interval = 5.0

        return adjustment

    def _trigger_alert(self, assessment: RiskAssessment):
        """Trigger alert callbacks"""
        for callback in self.alert_callbacks:
            try:
                callback(assessment)
            except Exception as e:
                logger.error(f"Alert callback error: {e}")

    def _apply_adjustment(self, data_source: str, adjustment: Adjustment):
        """Apply strategy adjustment (placeholder for future implementation)"""
        if adjustment.change_interval:
            logger.info(
                f"Adjusted rate limit for {data_source}: "
                f"{adjustment.new_min_interval}s - {adjustment.new_max_interval}s"
            )

    def get_risk_trend(self, window_size: int = 100) -> str:
        """Get risk trend"""
        if len(self.history) < 2:
            return "stable"

        recent = self.history[-1].score
        previous = self.history[-2].score

        if recent > previous + 5:
            return "increasing"
        elif recent < previous - 5:
            return "decreasing"
        else:
            return "stable"

    def get_recent_average_risk(self, window_size: int = 100) -> float:
        """Get recent average risk"""
        if not self.history:
            return 0.0

        window = self.history[-window_size:]
        return sum(a.score for a in window) / len(window)
