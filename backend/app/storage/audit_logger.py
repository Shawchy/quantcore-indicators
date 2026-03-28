"""
审计日志模块

记录用户操作、数据访问和系统事件
"""
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path
from loguru import logger
from enum import Enum
from dataclasses import dataclass, asdict


class AuditEventType(str, Enum):
    """审计事件类型"""
    LOGIN = "login"
    LOGOUT = "logout"
    DATA_ACCESS = "data_access"
    DATA_MODIFY = "data_modify"
    DATA_DELETE = "data_delete"
    DATA_EXPORT = "data_export"
    CONFIG_CHANGE = "config_change"
    SYSTEM_START = "system_start"
    SYSTEM_STOP = "system_stop"
    BACKUP_CREATE = "backup_create"
    BACKUP_RESTORE = "backup_restore"
    ERROR = "error"
    SECURITY = "security"


class AuditSeverity(str, Enum):
    """审计严重级别"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """审计事件"""
    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: str
    user_id: Optional[str]
    username: Optional[str]
    ip_address: Optional[str]
    resource: Optional[str]
    action: str
    details: Dict[str, Any]
    result: str
    duration_ms: Optional[float] = None


class AuditLogger:
    """审计日志记录器"""
    
    def __init__(self, log_dir: str = "./logs/audit"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        self.current_log_file = None
        self.events: List[AuditEvent] = []
        self.max_events = 10000
        self.retention_days = 90
        
        self.stats = {
            "total_events": 0,
            "events_by_type": {},
            "events_by_severity": {},
            "last_event_time": None
        }
    
    def _generate_event_id(self) -> str:
        """生成事件 ID"""
        import uuid
        return f"audit_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def _get_log_file_path(self) -> Path:
        """获取当前日志文件路径"""
        date_str = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"audit_{date_str}.jsonl"
    
    async def log_event(
        self,
        event_type: AuditEventType,
        severity: AuditSeverity,
        action: str,
        result: str = "success",
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        resource: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None
    ):
        """记录审计事件"""
        event = AuditEvent(
            event_id=self._generate_event_id(),
            event_type=event_type,
            severity=severity,
            timestamp=datetime.now().isoformat(),
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            resource=resource,
            action=action,
            details=details or {},
            result=result,
            duration_ms=duration_ms
        )
        
        self.events.append(event)
        
        if len(self.events) > self.max_events:
            self.events = self.events[-self.max_events:]
        
        self._update_stats(event)
        
        await self._write_to_file(event)
        
        logger.info(
            f"审计事件: {event_type.value} | {severity.value} | "
            f"用户: {username or 'anonymous'} | "
            f"操作: {action} | "
            f"结果: {result}"
        )
    
    def _update_stats(self, event: AuditEvent):
        """更新统计信息"""
        self.stats["total_events"] += 1
        self.stats["last_event_time"] = event.timestamp
        
        event_type = event.event_type.value
        if event_type not in self.stats["events_by_type"]:
            self.stats["events_by_type"][event_type] = 0
        self.stats["events_by_type"][event_type] += 1
        
        severity = event.severity.value
        if severity not in self.stats["events_by_severity"]:
            self.stats["events_by_severity"][severity] = 0
        self.stats["events_by_severity"][severity] += 1
    
    async def _write_to_file(self, event: AuditEvent):
        """写入日志文件"""
        log_file = self._get_log_file_path()
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(asdict(event), ensure_ascii=False) + "\n")
    
    async def query_events(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        event_type: Optional[str] = None,
        severity: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """查询审计事件"""
        filtered_events = []
        
        for event in reversed(self.events):
            if start_time and event.timestamp < start_time:
                continue
            if end_time and event.timestamp > end_time:
                continue
            if event_type and event.event_type.value != event_type:
                continue
            if severity and event.severity.value != severity:
                continue
            if user_id and event.user_id != user_id:
                continue
            
            filtered_events.append(asdict(event))
            
            if len(filtered_events) >= limit:
                break
        
        return filtered_events
    
    async def get_user_activity(
        self,
        user_id: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """获取用户活动报告"""
        start_time = (datetime.now() - timedelta(days=days)).isoformat()
        
        user_events = [
            event for event in self.events
            if event.user_id == user_id and event.timestamp >= start_time
        ]
        
        activity_by_type = {}
        for event in user_events:
            event_type = event.event_type.value
            if event_type not in activity_by_type:
                activity_by_type[event_type] = 0
            activity_by_type[event_type] += 1
        
        return {
            "user_id": user_id,
            "period_days": days,
            "total_events": len(user_events),
            "activity_by_type": activity_by_type,
            "last_activity": user_events[-1].timestamp if user_events else None
        }
    
    async def cleanup_old_logs(self):
        """清理过期日志"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        deleted_count = 0
        
        for log_file in self.log_dir.glob("audit_*.jsonl"):
            try:
                date_str = log_file.stem.replace("audit_", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")
                
                if file_date < cutoff_date:
                    log_file.unlink()
                    deleted_count += 1
                    logger.info(f"删除过期审计日志: {log_file.name}")
            
            except ValueError:
                continue
        
        return {"deleted_count": deleted_count}
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.stats
    
    def get_events_in_memory(self) -> List[Dict[str, Any]]:
        """获取内存中的事件"""
        return [asdict(event) for event in self.events]


audit_logger = AuditLogger()
