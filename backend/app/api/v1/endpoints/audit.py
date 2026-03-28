"""
审计日志 API 端点

提供审计日志查询、统计和用户活动报告接口
"""
from fastapi import APIRouter, Query, BackgroundTasks
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from app.storage.audit_logger import audit_logger, AuditEventType, AuditSeverity


router = APIRouter(prefix="/audit", tags=["审计日志"])


class AuditEventRequest(BaseModel):
    event_type: str
    severity: str
    action: str
    result: str = "success"
    user_id: Optional[str] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    resource: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    duration_ms: Optional[float] = None


@router.post("/log")
async def log_audit_event(request: AuditEventRequest):
    """记录审计事件"""
    try:
        event_type = AuditEventType(request.event_type)
        severity = AuditSeverity(request.severity)
    except ValueError as e:
        return {
            "success": False,
            "error": f"无效的事件类型或严重级别: {e}"
        }
    
    await audit_logger.log_event(
        event_type=event_type,
        severity=severity,
        action=request.action,
        result=request.result,
        user_id=request.user_id,
        username=request.username,
        ip_address=request.ip_address,
        resource=request.resource,
        details=request.details,
        duration_ms=request.duration_ms
    )
    
    return {
        "success": True,
        "message": "审计事件已记录"
    }


@router.get("/events")
async def query_events(
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    event_type: Optional[str] = None,
    severity: Optional[str] = None,
    user_id: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000)
):
    """查询审计事件"""
    events = await audit_logger.query_events(
        start_time=start_time,
        end_time=end_time,
        event_type=event_type,
        severity=severity,
        user_id=user_id,
        limit=limit
    )
    
    return {
        "success": True,
        "count": len(events),
        "events": events
    }


@router.get("/stats")
async def get_audit_stats():
    """获取审计统计信息"""
    stats = audit_logger.get_stats()
    
    return {
        "success": True,
        "data": stats
    }


@router.get("/user-activity/{user_id}")
async def get_user_activity(
    user_id: str,
    days: int = Query(7, ge=1, le=30)
):
    """获取用户活动报告"""
    activity = await audit_logger.get_user_activity(user_id, days)
    
    return {
        "success": True,
        "data": activity
    }


@router.post("/cleanup")
async def cleanup_old_logs(background_tasks: BackgroundTasks):
    """清理过期审计日志"""
    background_tasks.add_task(audit_logger.cleanup_old_logs)
    
    return {
        "success": True,
        "message": "已提交清理任务"
    }


@router.get("/event-types")
async def get_event_types():
    """获取所有事件类型"""
    return {
        "success": True,
        "event_types": [e.value for e in AuditEventType]
    }


@router.get("/severity-levels")
async def get_severity_levels():
    """获取所有严重级别"""
    return {
        "success": True,
        "severity_levels": [s.value for s in AuditSeverity]
    }


@router.get("/report/daily")
async def get_daily_report(date: Optional[str] = None):
    """获取每日审计报告"""
    target_date = date or datetime.now().strftime("%Y-%m-%d")
    
    start_time = f"{target_date}T00:00:00"
    end_time = f"{target_date}T23:59:59"
    
    events = await audit_logger.query_events(
        start_time=start_time,
        end_time=end_time,
        limit=10000
    )
    
    events_by_type = {}
    events_by_severity = {}
    events_by_user = {}
    
    for event in events:
        event_type = event["event_type"]
        severity = event["severity"]
        user_id = event.get("user_id") or "anonymous"
        
        if event_type not in events_by_type:
            events_by_type[event_type] = 0
        events_by_type[event_type] += 1
        
        if severity not in events_by_severity:
            events_by_severity[severity] = 0
        events_by_severity[severity] += 1
        
        if user_id not in events_by_user:
            events_by_user[user_id] = 0
        events_by_user[user_id] += 1
    
    return {
        "success": True,
        "date": target_date,
        "total_events": len(events),
        "events_by_type": events_by_type,
        "events_by_severity": events_by_severity,
        "events_by_user": events_by_user,
        "top_users": sorted(events_by_user.items(), key=lambda x: x[1], reverse=True)[:10]
    }
