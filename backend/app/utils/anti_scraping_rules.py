"""
反爬安全规则模块 (Anti-Scraping Safety Rules)

核心功能：
- 数据源频率限制配置
- 请求间隔智能计算
- 用户代理管理
- 违规检测与告警
- 安全审计日志

使用场景：
- 保护数据源账号安全
- 避免IP被封禁
- 合规使用爬虫数据
- 延长数据源使用寿命
"""

import asyncio
import random
import time
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from loguru import logger


class RiskLevel(str, Enum):
    """风险等级"""
    SAFE = "safe"           # 安全
    LOW = "low"             # 低风险
    MEDIUM = "medium"       # 中风险
    HIGH = "high"           # 高风险
    CRITICAL = "critical"   # 危险（应立即停止）


@dataclass
class SourceRule:
    """数据源规则配置"""
    source_name: str
    max_requests_per_minute: int = 30
    min_interval_seconds: float = 2.0
    max_requests_per_hour: int = 500
    daily_limit: int = 5000
    user_agent_rotation: bool = True
    business_hours_only: bool = True
    respect_robots_txt: bool = True
    cooldown_on_error: int = 300
    batch_size: int = 10
    warning_threshold: float = 0.8


@dataclass
class RequestRecord:
    """请求记录"""
    timestamp: datetime
    source: str
    endpoint: str
    success: bool
    response_time_ms: float
    user_agent: str = ""


@dataclass
class SafetyStatus:
    """安全状态"""
    is_safe: bool
    risk_level: RiskLevel
    current_rpm: int  # requests per minute
    current_rph: int  # requests per hour
    next_allowed_time: datetime
    cooldown_until: Optional[datetime] = None
    warnings: List[str] = field(default_factory=list)
    violations: List[str] = field(default_factory=list)


class AntiScrapingRules:
    """
    反爬安全规则管理器
    
    确保应用在使用爬虫数据源时遵守最佳实践，
    避免触发反爬机制导致封禁。
    
    内置规则库：
    - EFinance: 东方财富（主力数据源）
    - AkShare: 开源接口
    - Baostock: 证券宝
    - YFinance: Yahoo Finance
    
    使用示例：
        >>> safety = AntiScrapingRules()
        >>> status = safety.check_before_request("efinance")
        >>> if status.is_safe:
        ...     await make_request()
        ...     safety.record_request("efinance", "/api/quote", success=True)
    """
    
    DEFAULT_RULES = {
        "efinance": SourceRule(
            source_name="EFinance",
            max_requests_per_minute=25,
            min_interval_seconds=2.5,
            max_requests_per_hour=400,
            daily_limit=4000,
            user_agent_rotation=True,
            business_hours_only=True,
            cooldown_on_error=300,
            batch_size=8,
            warning_threshold=0.75
        ),
        "akshare": SourceRule(
            source_name="AkShare",
            max_requests_per_minute=50,
            min_interval_seconds=1.2,
            max_requests_per_hour=800,
            daily_limit=8000,
            user_agent_rotation=False,
            business_hours_only=False,
            cooldown_on_error=180,
            batch_size=20,
            warning_threshold=0.85
        ),
        "baostock": SourceRule(
            source_name="BaoStock",
            max_requests_per_minute=100,
            min_interval_seconds=0.6,
            max_requests_per_hour=1500,
            daily_limit=15000,
            user_agent_rotation=False,
            business_hours_only=False,
            cooldown_on_error=120,
            batch_size=30,
            warning_threshold=0.9
        ),
        "yfinance": SourceRule(
            source_name="YFinance",
            max_requests_per_minute=20,
            min_interval_seconds=3.0,
            max_requests_per_hour=300,
            daily_limit=3000,
            user_agent_rotation=True,
            business_hours_only=False,
            cooldown_on_error=600,
            batch_size=5,
            warning_threshold=0.7
        ),
        "tickflow": SourceRule(
            source_name="TickFlow",
            max_requests_per_minute=60,
            min_interval_seconds=1.0,
            max_requests_per_hour=1000,
            daily_limit=10000,
            user_agent_rotation=True,
            business_hours_only=False,
            cooldown_on_error=120,
            batch_size=15,
            warning_threshold=0.8
        ),
    }
    
    USER_AGENTS = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) "
        "Gecko/20100101 Firefox/121.0",
        
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 "
        "Safari/605.1.15",
        
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 "
        "Safari/537.36 Edg/120.0.0.0",
    ]
    
    def __init__(self):
        self._rules: Dict[str, SourceRule] = dict(self.DEFAULT_RULES)
        self._request_history: List[RequestRecord] = []
        self._source_counters: Dict[str, Dict] = {}
        self._cooldowns: Dict[str, datetime] = {}
        self._violations: List[Dict] = []
        
        self._last_request_times: Dict[str, datetime] = {}
        self._current_user_agents: Dict[str, str] = {}
        
        logger.info("AntiScrapingRules 初始化完成（反爬安全保护已启用）")
    
    def check_before_request(self, source: str) -> SafetyStatus:
        """
        发起请求前检查是否安全
        
        Args:
            source: 数据源名称
            
        Returns:
            SafetyStatus: 安全状态
        """
        now = datetime.now()
        rule = self._rules.get(source)
        
        if not rule:
            return SafetyStatus(
                is_safe=False,
                risk_level=RiskLevel.HIGH,
                current_rpm=0,
                current_rph=0,
                next_allowed_time=now,
                warnings=[f"未知数据源: {source}"]
            )
        
        if source in self._cooldowns:
            if now < self._cooldowns[source]:
                return SafetyStatus(
                    is_safe=False,
                    risk_level=RiskLevel.CRITICAL,
                    current_rpm=self._get_current_rpm(source),
                    current_rph=self._get_current_rph(source),
                    next_allowed_time=self._cooldowns[source],
                    cooldown_until=self._cooldowns[source],
                    warnings=[f"冷却中，请在 {self._cooldowns[source].strftime('%H:%M:%S')} 后重试"],
                    violations=["频繁错误触发冷却"]
                )
            else:
                del self._cooldowns[source]
        
        rpm = self._get_current_rpm(source)
        rph = self._get_current_rph(source)
        
        warnings = []
        violations = []
        
        if rpm >= rule.max_requests_per_minute:
            violations.append(f"超过每分钟限制 ({rpm}/{rule.max_requests_per_minute})")
        
        if rph >= rule.max_requests_per_hour:
            violations.append(f"超过每小时限制 ({rph}/{rule.max_requests_per_hour})")
        
        rpm_ratio = rpm / rule.max_requests_per_minute if rule.max_requests_per_minute > 0 else 0
        
        if rpm_ratio >= rule.warning_threshold and rpm_ratio < 1.0:
            warnings.append(f"接近频率限制 ({rpm_ratio*100:.0f}%)")
        
        if rule.business_hours_only and not self._is_trading_hours():
            warnings.append("非交易时间，建议减少请求")
        
        last_request = self._last_request_times.get(source)
        if last_request:
            elapsed = (now - last_request).total_seconds()
            if elapsed < rule.min_interval_seconds:
                wait_time = rule.min_interval_seconds - elapsed
                return SafetyStatus(
                    is_safe=False,
                    risk_level=RiskLevel.MEDIUM,
                    current_rpm=rpm,
                    current_rph=rph,
                    next_allowed_time=now + timedelta(seconds=wait_time),
                    warnings=[f"请求过于频繁，需等待 {wait_time:.1f}秒"],
                    violations=[]
                )
        
        risk_level = self._calculate_risk_level(rpm_ratio, len(violations))
        
        is_safe = len(violations) == 0 and risk_level != RiskLevel.CRITICAL
        
        return SafetyStatus(
            is_safe=is_safe,
            risk_level=risk_level,
            current_rpm=rpm,
            current_rph=rph,
            next_allowed_time=now + timedelta(seconds=rule.min_interval_seconds),
            cooldown_until=self._cooldowns.get(source),
            warnings=warnings,
            violations=violations
        )
    
    def record_request(
        self,
        source: str,
        endpoint: str,
        success: bool,
        response_time_ms: float = 0.0
    ):
        """
        记录请求（每次API调用后必须调用）
        
        Args:
            source: 数据源
            endpoint: API端点
            success: 是否成功
            response_time_ms: 响应时间
        """
        now = datetime.now()
        
        record = RequestRecord(
            timestamp=now,
            source=source,
            endpoint=endpoint,
            success=success,
            response_time_ms=response_time_ms,
            user_agent=self.get_user_agent(source)
        )
        
        self._request_history.append(record)
        self._last_request_times[source] = now
        
        if not success:
            rule = self._rules.get(source)
            if rule:
                recent_failures = sum(
                    1 for r in self._request_history[-20:]
                    if r.source == source and not r.success
                )
                
                if recent_failures >= 3:
                    cooldown_end = now + timedelta(seconds=rule.cooldown_on_error)
                    self._cooldowns[source] = cooldown_end
                    
                    violation = {
                        "timestamp": now.isoformat(),
                        "source": source,
                        "type": "consecutive_failures",
                        "count": recent_failures,
                        "cooldown_seconds": rule.cooldown_on_error
                    }
                    self._violations.append(violation)
                    
                    logger.warning(
                        f"⚠️ {source} 连续失败{recent_failures}次，"
                        f"触发冷却 {rule.cooldown_on_error}秒"
                    )
        
        if len(self._request_history) > 10000:
            self._request_history = self._request_history[-5000:]
        
        if len(self._violations) > 1000:
            self._violations = self._violations[-500:]
    
    def get_optimal_interval(self, source: str) -> float:
        """
        获取最优请求间隔
        
        根据历史请求模式和安全规则，
        计算下一次请求应该等待的时间。
        
        Args:
            source: 数据源名称
            
        Returns:
            float: 推荐的等待时间（秒）
        """
        rule = self._rules.get(source)
        if not rule:
            return 2.0
        
        base_interval = rule.min_interval_seconds
        
        status = self.check_before_request(source)
        
        if status.risk_level == RiskLevel.LOW:
            jitter = random.uniform(0.8, 1.2)
        elif status.risk_level == RiskLevel.MEDIUM:
            jitter = random.uniform(1.2, 1.8)
        elif status.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]:
            jitter = random.uniform(2.0, 3.0)
        else:
            jitter = random.uniform(0.9, 1.1)
        
        final_interval = base_interval * jitter
        
        if not self._is_trading_hours() and rule.business_hours_only:
            final_interval *= 2.0
        
        return round(final_interval, 2)
    
    def get_user_agent(self, source: str) -> str:
        """
        获取User-Agent（支持轮换）
        
        Args:
            source: 数据源名称
            
        Returns:
            str: User-Agent字符串
        """
        rule = self._rules.get(source)
        
        if rule and rule.user_agent_rotation:
            if source not in self._current_user_agents or random.random() < 0.1:
                self._current_user_agents[source] = random.choice(self.USER_AGENTS)
            
            return self._current_user_agents[source]
        
        return self.USER_AGENTS[0]
    
    async def safe_request_delay(self, source: str):
        """
        安全延迟（在请求前调用）
        
        自动计算并等待合适的间隔时间。
        
        Args:
            source: 数据源名称
        """
        interval = self.get_optimal_interval(source)
        
        last_request = self._last_request_times.get(source)
        if last_request:
            elapsed = (datetime.now() - last_request).total_seconds()
            
            if elapsed < interval:
                wait_time = interval - elapsed
                logger.debug(f"{source} 安全延迟: {wait_time:.2f}秒")
                await asyncio.sleep(wait_time)
        else:
            initial_delay = random.uniform(0.5, 1.5)
            await asyncio.sleep(initial_delay)
    
    def _get_current_rpm(self, source: str) -> int:
        """获取当前每分钟请求数"""
        now = datetime.now()
        one_min_ago = now - timedelta(minutes=1)
        
        return sum(
            1 for r in self._request_history
            if r.source == source and r.timestamp > one_min_ago
        )
    
    def _get_current_rph(self, source: str) -> int:
        """获取当前每小时请求数"""
        now = datetime.now()
        one_hour_ago = now - timedelta(hours=1)
        
        return sum(
            1 for r in self._request_history
            if r.source == source and r.timestamp > one_hour_ago
        )
    
    def _calculate_risk_level(
        self,
        rpm_ratio: float,
        violation_count: int
    ) -> RiskLevel:
        """计算风险等级"""
        if violation_count > 0:
            return RiskLevel.HIGH if violation_count <= 2 else RiskLevel.CRITICAL
        
        if rpm_ratio >= 1.0:
            return RiskLevel.CRITICAL
        elif rpm_ratio >= 0.9:
            return RiskLevel.HIGH
        elif rpm_ratio >= 0.75:
            return RiskLevel.MEDIUM
        elif rpm_ratio >= 0.5:
            return RiskLevel.LOW
        else:
            return RiskLevel.SAFE
    
    def _is_trading_hours(self) -> bool:
        """判断是否在交易时间"""
        now = datetime.now()
        
        if now.weekday() >= 5:
            return False
        
        current_time = (now.hour, now.minute)
        
        morning = (9, 30) <= current_time <= (11, 30)
        afternoon = (13, 0) <= current_time <= (15, 0)
        
        return morning or afternoon
    
    def add_custom_rule(self, source: str, rule: SourceRule):
        """添加自定义规则"""
        self._rules[source] = rule
        logger.info(f"添加自定义规则: {source}")
    
    def update_rule(self, source: str, **kwargs):
        """更新现有规则参数"""
        if source in self._rules:
            rule = self._rules[source]
            for key, value in kwargs.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            logger.info(f"更新规则: {source}, 参数: {kwargs}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取安全统计信息"""
        now = datetime.now()
        
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)
        
        recent_requests = [
            r for r in self._request_history
            if r.timestamp > hour_ago
        ]
        
        today_requests = [
            r for r in self._request_history
            if r.timestamp > day_ago
        ]
        
        success_rate = (
            sum(1 for r in recent_requests if r.success) / len(recent_requests) * 100
            if recent_requests else 100.0
        )
        
        avg_response_time = (
            sum(r.response_time_ms for r in recent_requests) / len(recent_requests)
            if recent_requests else 0.0
        )
        
        active_sources = set(r.source for r in recent_requests)
        
        source_stats = {}
        for source in active_sources:
            source_requests = [r for r in recent_requests if r.source == source]
            source_stats[source] = {
                "requests": len(source_requests),
                "success_rate": f"{sum(1 for r in source_requests if r.success)/len(source_requests)*100:.1f}%",
                "avg_response_ms": f"{sum(r.response_time_ms for r in source_requests)/len(source_requests):.0f}",
                "rpm": self._get_current_rpm(source),
                "in_cooldown": source in self._cooldowns
            }
        
        return {
            "total_requests_today": len(today_requests),
            "requests_last_hour": len(recent_requests),
            "overall_success_rate": f"{success_rate:.1f}%",
            "avg_response_time_ms": f"{avg_response_time:.0f}",
            "active_sources": list(active_sources),
            "source_details": source_stats,
            "active_cooldowns": len(self._cooldowns),
            "total_violations": len(self._violations),
            "recent_violations": len([
                v for v in self._violations
                if datetime.fromisoformat(v["timestamp"]) > hour_ago
            ]),
            "is_trading_hours": self._is_trading_hours(),
            "current_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        }


# 全局单例
anti_scraping_rules = AntiScrapingRules()


async def demo():
    """演示用法"""
    print("=" * 70)
    print("🛡️  AntiScrapingRules 反爬安全演示")
    print("=" * 70)
    
    safety = AntiScrapingRules()
    
    print("\n📋 内置数据源规则:")
    for name, rule in safety.DEFAULT_RULES.items():
        print(f"\n   🔌 {name}:")
        print(f"      - 每分钟限制: {rule.max_requests_per_minute} 次")
        print(f"      - 最小间隔: {rule.min_interval_seconds}s")
        print(f"      - 每小时限制: {rule.max_requests_per_hour} 次")
        print(f"      - 日限制: {rule.daily_limit} 次")
    
    print("\n✅ 安全检查示例:")
    sources_to_test = ["efinance", "akshare", "baostock"]
    
    for source in sources_to_test:
        status = safety.check_before_request(source)
        
        risk_icon = {
            RiskLevel.SAFE: "🟢",
            RiskLevel.LOW: "🟡",
            RiskLevel.MEDIUM: "🟠",
            RiskLevel.HIGH: "🔴",
            RiskLevel.CRITICAL: "⛔"
        }.get(status.risk_level, "❓")
        
        print(f"\n   {risk_icon} {source.upper()}:")
        print(f"      安全: {'是' if status.is_safe else '否'}")
        print(f"      当前RPM: {status.current_rpm}")
        print(f"      风险等级: {status.risk_level.value}")
        
        if status.warnings:
            print(f"      ⚠️  警告: {status.warnings}")
        if status.violations:
            print(f"      ❌ 违规: {status.violations}")
    
    print("\n📊 模拟请求记录:")
    test_source = "efinance"
    
    for i in range(5):
        status = safety.check_before_request(test_source)
        if status.is_safe:
            safety.record_request(
                test_source,
                "/api/quote",
                success=True,
                response_time_ms=random.randint(50, 200)
            )
            print(f"   ✅ 第{i+1}次请求成功")
            
            await asyncio.sleep(0.5)
        else:
            print(f"   ❌ 第{i+1}次请求被拦截: {status.warnings}")
            break
    
    print("\n⏱️  推荐请求间隔:")
    for source in ["efinance", "akshare"]:
        interval = safety.get_optimal_interval(source)
        print(f"   {source}: {interval}秒")
    
    stats = safety.get_statistics()
    print(f"\n📈 安全统计:")
    for key, value in stats.items():
        if key != "source_details":
            print(f"   {key}: {value}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(demo())
