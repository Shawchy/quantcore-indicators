"""响应模式模块

为了向后兼容，从 app.models.schemas 重新导出 ResponseModel
"""
from app.models.schemas import ResponseModel

__all__ = ["ResponseModel"]
