"""用户模型模块

为了向后兼容，从 app.core.security 重新导出 User 模型
"""
from app.core.security import User

__all__ = ["User"]
