"""认证工具模块

为了向后兼容，从 app.api.deps 重新导出认证相关函数
"""
from app.api.deps import (
    get_current_user,
    get_current_active_user,
    get_current_admin_user,
    get_optional_current_user,
    CurrentUser,
    CurrentActiveUser,
    CurrentAdminUser,
    OptionalCurrentUser,
)

__all__ = [
    "get_current_user",
    "get_current_active_user",
    "get_current_admin_user",
    "get_optional_current_user",
    "CurrentUser",
    "CurrentActiveUser",
    "CurrentAdminUser",
    "OptionalCurrentUser",
]
