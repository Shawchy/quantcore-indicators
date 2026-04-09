"""
监控与统计模块（v5.0）

提供完整的指标收集、监控、告警和统计功能。

功能:
- 策略执行统计
- Cookie 有效性监控
- 成功率统计
- 性能分析
- 异常告警
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from collections import deque
from loguru import logger
from enum import Enum


class AlertLevel(Enum):
    """告警级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class StrategyMetrics:
    """策略指标"""
    strategy_name: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    total_execution_time_ms: float = 0.0
    last_execution_time: Optional[datetime] = None
    last_error: Optional[str] = None
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.total_requests == 0:
            return 1.0
        return self.successful_requests / self.total_requests
    
    @property
    def avg_execution_time_ms(self) -> float:
        """平均执行时间"""
        if self.total_requests == 0:
            return 0.0
        return self.total_execution_time_ms / self.total_requests
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'strategy_name': self.strategy_name,
            'total_requests': self.total_requests,
            'successful_requests': self.successful_requests,
            'failed_requests': self.failed_requests,
            'success_rate': f"{self.success_rate:.2%}",
            'avg_execution_time_ms': f"{self.avg_execution_time_ms:.2f}",
            'last_execution_time': self.last_execution_time.isoformat() if self.last_execution_time else None,
            'last_error': self.last_error,
        }


@dataclass
class APIMetrics:
    """API 指标（滑动窗口统计）"""
    api_key: str
    window_size: int = 100  # 滑动窗口大小
    results: deque = field(default_factory=lambda: deque(maxlen=100))
    response_times: deque = field(default_factory=lambda: deque(maxlen=100))
    last_request_time: Optional[datetime] = None
    
    def record(self, success: bool, response_time_ms: float = 0.0):
        """记录请求结果"""
        self.results.append(success)
        self.response_times.append(response_time_ms)
        self.last_request_time = datetime.now()
    
    @property
    def success_rate(self) -> float:
        """成功率（滑动窗口）"""
        if not self.results:
            return 1.0
        return sum(self.results) / len(self.results)
    
    @property
    def avg_response_time_ms(self) -> float:
        """平均响应时间"""
        if not self.response_times:
            return 0.0
        return sum(self.response_times) / len(self.response_times)
    
    @property
    def total_requests(self) -> int:
        """总请求数"""
        return len(self.results)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'api_key': self.api_key,
            'total_requests': self.total_requests,
            'success_rate': f"{self.success_rate:.2%}",
            'avg_response_time_ms': f"{self.avg_response_time_ms:.2f}",
            'last_request_time': self.last_request_time.isoformat() if self.last_request_time else None,
        }


@dataclass
class CookieMetrics:
    """Cookie 指标"""
    domain: str
    is_valid: bool = False
    is_expired: bool = False
    last_verified_time: Optional[datetime] = None
    last_refresh_time: Optional[datetime] = None
    refresh_count: int = 0
    refresh_success_count: int = 0
    refresh_fail_count: int = 0
    consecutive_failures: int = 0
    
    @property
    def refresh_success_rate(self) -> float:
        """续期成功率"""
        if self.refresh_count == 0:
            return 0.0
        return self.refresh_success_count / self.refresh_count
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'domain': self.domain,
            'is_valid': self.is_valid,
            'is_expired': self.is_expired,
            'last_verified_time': self.last_verified_time.isoformat() if self.last_verified_time else None,
            'last_refresh_time': self.last_refresh_time.isoformat() if self.last_refresh_time else None,
            'refresh_count': self.refresh_count,
            'refresh_success_rate': f"{self.refresh_success_rate:.2%}",
            'consecutive_failures': self.consecutive_failures,
        }


@dataclass
class Alert:
    """告警"""
    level: AlertLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    category: Optional[str] = None  # 告警类别（cookie/rate_limit/strategy）
    details: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'level': self.level.value,
            'message': self.message,
            'timestamp': self.timestamp.isoformat(),
            'category': self.category,
            'details': self.details,
        }


class MetricsCollector:
    """指标收集器"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化指标收集器
        
        Args:
            config: 配置字典
                - alert_thresholds: 告警阈值配置
        """
        self.config = config or {}
        
        # 策略指标
        self._strategy_metrics: Dict[str, StrategyMetrics] = {}
        
        # API 指标
        self._api_metrics: Dict[str, APIMetrics] = {}
        
        # Cookie 指标
        self._cookie_metrics: Dict[str, CookieMetrics] = {}
        
        # 告警列表
        self._alerts: deque = deque(maxlen=1000)  # 最多保留 1000 条告警
        
        # 告警回调
        self._alert_callbacks: List[Callable[[Alert], None]] = []
        
        # 告警阈值
        self._alert_thresholds = {
            'success_rate_min': 0.8,  # 成功率低于 80% 告警
            'execution_time_max': 1000,  # 执行时间超过 1000ms 告警
            'consecutive_failures': 5,  # 连续失败 5 次告警
            'cookie_expiry_hours': 2,  # Cookie 过期前 2 小时告警
        }
        
        if 'alert_thresholds' in self.config:
            self._alert_thresholds.update(self.config['alert_thresholds'])
        
        logger.info("✅ 指标收集器已初始化")
    
    # ========== 策略指标 ==========
    
    def record_strategy_request(
        self,
        strategy_name: str,
        success: bool,
        execution_time_ms: float = 0.0,
        error: Optional[str] = None
    ):
        """记录策略执行"""
        if strategy_name not in self._strategy_metrics:
            self._strategy_metrics[strategy_name] = StrategyMetrics(strategy_name)
        
        metrics = self._strategy_metrics[strategy_name]
        metrics.total_requests += 1
        metrics.total_execution_time_ms += execution_time_ms
        metrics.last_execution_time = datetime.now()
        
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
            metrics.last_error = error
            
            # 检查连续失败
            if metrics.failed_requests >= self._alert_thresholds['consecutive_failures']:
                self._send_alert(
                    level=AlertLevel.WARNING,
                    message=f"策略 {strategy_name} 连续失败 {metrics.failed_requests} 次",
                    category="strategy",
                    details={'strategy_name': strategy_name, 'failed_count': metrics.failed_requests}
                )
        
        # 检查成功率
        if metrics.total_requests >= 10:  # 至少 10 次请求后才检查
            if metrics.success_rate < self._alert_thresholds['success_rate_min']:
                self._send_alert(
                    level=AlertLevel.WARNING,
                    message=f"策略 {strategy_name} 成功率过低：{metrics.success_rate:.2%}",
                    category="strategy",
                    details={'strategy_name': strategy_name, 'success_rate': metrics.success_rate}
                )
        
        # 检查执行时间
        if execution_time_ms > self._alert_thresholds['execution_time_max']:
            self._send_alert(
                level=AlertLevel.INFO,
                message=f"策略 {strategy_name} 执行时间过长：{execution_time_ms:.2f}ms",
                category="strategy",
                details={'strategy_name': strategy_name, 'execution_time_ms': execution_time_ms}
            )
    
    def get_strategy_metrics(self, strategy_name: str) -> Optional[StrategyMetrics]:
        """获取策略指标"""
        return self._strategy_metrics.get(strategy_name)
    
    def get_all_strategy_metrics(self) -> Dict[str, StrategyMetrics]:
        """获取所有策略指标"""
        return self._strategy_metrics.copy()
    
    # ========== API 指标 ==========
    
    def record_api_request(self, api_key: str, success: bool, response_time_ms: float = 0.0):
        """记录 API 请求"""
        if api_key not in self._api_metrics:
            self._api_metrics[api_key] = APIMetrics(api_key)
        
        self._api_metrics[api_key].record(success, response_time_ms)
    
    def get_api_metrics(self, api_key: str) -> Optional[APIMetrics]:
        """获取 API 指标"""
        return self._api_metrics.get(api_key)
    
    def get_all_api_metrics(self) -> Dict[str, APIMetrics]:
        """获取所有 API 指标"""
        return self._api_metrics.copy()
    
    # ========== Cookie 指标 ==========
    
    def record_cookie_verification(self, domain: str, is_valid: bool):
        """记录 Cookie 验证"""
        if domain not in self._cookie_metrics:
            self._cookie_metrics[domain] = CookieMetrics(domain)
        
        metrics = self._cookie_metrics[domain]
        metrics.is_valid = is_valid
        metrics.last_verified_time = datetime.now()
        
        if not is_valid:
            metrics.is_expired = True
            self._send_alert(
                level=AlertLevel.WARNING,
                message=f"Cookie 已过期或无效：{domain}",
                category="cookie",
                details={'domain': domain}
            )
    
    def record_cookie_refresh(self, domain: str, success: bool):
        """记录 Cookie 续期"""
        if domain not in self._cookie_metrics:
            self._cookie_metrics[domain] = CookieMetrics(domain)
        
        metrics = self._cookie_metrics[domain]
        metrics.refresh_count += 1
        metrics.last_refresh_time = datetime.now()
        
        if success:
            metrics.refresh_success_count += 1
            metrics.is_valid = True
            metrics.is_expired = False
            metrics.consecutive_failures = 0
        else:
            metrics.refresh_fail_count += 1
            metrics.consecutive_failures += 1
            
            # 检查连续失败
            if metrics.consecutive_failures >= self._alert_thresholds['consecutive_failures']:
                self._send_alert(
                    level=AlertLevel.ERROR,
                    message=f"Cookie 续期连续失败 {metrics.consecutive_failures} 次：{domain}",
                    category="cookie",
                    details={'domain': domain, 'consecutive_failures': metrics.consecutive_failures}
                )
    
    def get_cookie_metrics(self, domain: str) -> Optional[CookieMetrics]:
        """获取 Cookie 指标"""
        return self._cookie_metrics.get(domain)
    
    def get_all_cookie_metrics(self) -> Dict[str, CookieMetrics]:
        """获取所有 Cookie 指标"""
        return self._cookie_metrics.copy()
    
    # ========== 告警管理 ==========
    
    def _send_alert(
        self,
        level: AlertLevel,
        message: str,
        category: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """发送告警"""
        alert = Alert(
            level=level,
            message=message,
            category=category,
            details=details
        )
        
        self._alerts.append(alert)
        
        # 记录日志
        log_message = f"🔔 [{level.value.upper()}] {message}"
        if level == AlertLevel.CRITICAL:
            logger.critical(log_message)
        elif level == AlertLevel.ERROR:
            logger.error(log_message)
        elif level == AlertLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # 调用回调
        for callback in self._alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"❌ 告警回调失败：{e}")
    
    def register_alert_callback(self, callback: Callable[[Alert], None]):
        """注册告警回调"""
        self._alert_callbacks.append(callback)
    
    def get_alerts(
        self,
        level: Optional[AlertLevel] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Alert]:
        """获取告警列表"""
        alerts = list(self._alerts)
        
        if level:
            alerts = [a for a in alerts if a.level == level]
        
        if category:
            alerts = [a for a in alerts if a.category == category]
        
        return alerts[-limit:]
    
    def clear_alerts(self):
        """清空告警"""
        self._alerts.clear()
        logger.info("✅ 告警已清空")
    
    # ========== 报告生成 ==========
    
    def generate_report(self) -> Dict[str, Any]:
        """生成完整报告"""
        return {
            'timestamp': datetime.now().isoformat(),
            'strategy_metrics': {
                name: metrics.to_dict()
                for name, metrics in self._strategy_metrics.items()
            },
            'api_metrics': {
                name: metrics.to_dict()
                for name, metrics in self._api_metrics.items()
            },
            'cookie_metrics': {
                name: metrics.to_dict()
                for name, metrics in self._cookie_metrics.items()
            },
            'alerts': {
                'total': len(self._alerts),
                'recent': [a.to_dict() for a in self.get_alerts(limit=10)]
            }
        }
    
    def print_report(self):
        """打印报告"""
        report = self.generate_report()
        
        logger.info("\n" + "="*80)
        logger.info("📊 监控统计报告")
        logger.info(f"生成时间：{report['timestamp']}")
        logger.info("="*80)
        
        # 策略指标
        if report['strategy_metrics']:
            logger.info("\n📈 策略执行统计:")
            for name, metrics in report['strategy_metrics'].items():
                logger.info(f"  {name}:")
                logger.info(f"    总请求：{metrics['total_requests']}")
                logger.info(f"    成功率：{metrics['success_rate']}")
                logger.info(f"    平均耗时：{metrics['avg_execution_time_ms']}ms")
        
        # API 指标
        if report['api_metrics']:
            logger.info("\n🌐 API 统计:")
            for name, metrics in report['api_metrics'].items():
                logger.info(f"  {name}:")
                logger.info(f"    总请求：{metrics['total_requests']}")
                logger.info(f"    成功率：{metrics['success_rate']}")
                logger.info(f"    平均响应：{metrics['avg_response_time_ms']}ms")
        
        # Cookie 指标
        if report['cookie_metrics']:
            logger.info("\n🍪 Cookie 状态:")
            for name, metrics in report['cookie_metrics'].items():
                status = "✅ 有效" if metrics['is_valid'] else "❌ 无效"
                logger.info(f"  {name}: {status}")
                logger.info(f"    续期次数：{metrics['refresh_count']}")
                logger.info(f"    续期成功率：{metrics['refresh_success_rate']}")
                if metrics['consecutive_failures'] > 0:
                    logger.info(f"    ⚠️  连续失败：{metrics['consecutive_failures']}")
        
        # 告警
        if report['alerts']['total'] > 0:
            logger.info(f"\n🔔 告警信息（共 {report['alerts']['total']} 条）:")
            for alert in report['alerts']['recent']:
                logger.info(f"  [{alert['level'].upper()}] {alert['message']}")
                if alert.get('details'):
                    logger.info(f"    详情：{alert['details']}")
        
        logger.info("\n" + "="*80)


# 全局单例
_global_collector: Optional[MetricsCollector] = None


def get_metrics_collector(config: Optional[Dict[str, Any]] = None) -> MetricsCollector:
    """获取全局指标收集器"""
    global _global_collector
    
    if _global_collector is None:
        _global_collector = MetricsCollector(config)
    
    return _global_collector
