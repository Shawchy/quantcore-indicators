"""
日期格式转换工具

统一处理日期格式转换：
- 输入：支持 YYYY-MM-DD 或 YYYYMMDD
- 输出：根据目标系统要求转换
"""
from typing import Optional
from datetime import datetime


def normalize_date(date_str: Optional[str], target_format: str = "YYYY-MM-DD") -> Optional[str]:
    """
    标准化日期格式
    
    Args:
        date_str: 日期字符串（支持 YYYY-MM-DD 或 YYYYMMDD 格式）
        target_format: 目标格式
            - "YYYY-MM-DD": ISO 格式（数据库存储）
            - "YYYYMMDD": 紧凑格式（数据源参数）
            - "datetime": datetime 对象
    
    Returns:
        标准化后的日期字符串或对象
    
    Examples:
        >>> normalize_date("20260319", "YYYY-MM-DD")
        "2026-03-19"
        
        >>> normalize_date("2026-03-19", "YYYYMMDD")
        "20260319"
        
        >>> normalize_date("20260319", "datetime")
        datetime.datetime(2026, 3, 19)
    """
    if not date_str:
        return None
    
    # 统一解析为 datetime 对象
    try:
        if len(date_str) == 8 and date_str.isdigit():
            # YYYYMMDD 格式
            dt = datetime.strptime(date_str, "%Y%m%d")
        elif len(date_str) == 10 and '-' in date_str:
            # YYYY-MM-DD 格式
            dt = datetime.strptime(date_str, "%Y-%m-%d")
        else:
            # 未知格式，尝试智能解析
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
    except ValueError as e:
        raise ValueError(f"无法解析日期：{date_str}, 错误：{e}")
    
    # 转换为目标格式
    if target_format == "YYYY-MM-DD":
        return dt.strftime("%Y-%m-%d")
    elif target_format == "YYYYMMDD":
        return dt.strftime("%Y%m%d")
    elif target_format == "datetime":
        return dt
    elif target_format == "int":
        return int(dt.strftime("%Y%m%d"))
    else:
        return dt.strftime(target_format)


def to_iso_date(date_str: Optional[str]) -> Optional[str]:
    """转换为 ISO 格式（YYYY-MM-DD），用于数据库存储"""
    return normalize_date(date_str, "YYYY-MM-DD")


def to_compact_date(date_str: Optional[str]) -> Optional[str]:
    """转换为紧凑格式（YYYYMMDD），用于数据源参数"""
    return normalize_date(date_str, "YYYYMMDD")


def to_int_date(date_str: Optional[str]) -> Optional[int]:
    """转换为整数格式（YYYYMMDD），用于 AkShare 等数据源"""
    normalized = normalize_date(date_str, "YYYYMMDD")
    return int(normalized) if normalized else None


def is_valid_date(date_str: str) -> bool:
    """
    检查日期字符串是否有效
    
    Args:
        date_str: 日期字符串
    
    Returns:
        是否有效
    """
    if not date_str:
        return False
    
    try:
        if len(date_str) == 8 and date_str.isdigit():
            datetime.strptime(date_str, "%Y%m%d")
            return True
        elif len(date_str) == 10 and '-' in date_str:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        return False
    except ValueError:
        return False


def format_date_range(
    start_date: Optional[str],
    end_date: Optional[str],
    target_format: str = "YYYY-MM-DD"
) -> tuple:
    """
    格式化日期范围
    
    Args:
        start_date: 开始日期
        end_date: 结束日期
        target_format: 目标格式
    
    Returns:
        (start_date_formatted, end_date_formatted)
    
    Examples:
        >>> format_date_range("20260101", "20260319", "YYYY-MM-DD")
        ("2026-01-01", "2026-03-19")
    """
    start = normalize_date(start_date, target_format) if start_date else None
    end = normalize_date(end_date, target_format) if end_date else None
    return start, end
