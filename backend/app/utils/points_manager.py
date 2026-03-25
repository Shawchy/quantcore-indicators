"""
Tushare 积分权限管理器

根据用户积分控制 API 接口调用权限，实现智能数据源切换。
"""

from typing import Dict, Set, Optional
from loguru import logger
from app.config import settings


class TusharePointsManager:
    """Tushare 积分权限管理器"""
    
    _instance: Optional['TusharePointsManager'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'TusharePointsManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.points: int = settings.TUSHARE_POINTS
        self.permission_config: Dict[int, Dict[str, bool]] = settings.TUSHARE_PERMISSION_CONFIG
        self.available_permissions: Set[str] = set()
        
        self._calculate_permissions()
        self._initialized = True
        
        logger.info(f"Tushare 积分管理器初始化完成：{self.points}分")
        logger.info(f"可用权限：{len(self.available_permissions)} 个接口")
    
    def _calculate_permissions(self):
        """根据积分计算可用权限"""
        self.available_permissions.clear()
        
        # 累加所有低于等于当前积分的权限
        for points_threshold, permissions in self.permission_config.items():
            if self.points >= points_threshold:
                for api_name, enabled in permissions.items():
                    if enabled:
                        self.available_permissions.add(api_name)
                logger.debug(f"积分达到 {points_threshold} 分，解锁 {len(permissions)} 个接口")
    
    def has_permission(self, api_name: str) -> bool:
        """
        检查是否有权限调用指定 API
        
        Args:
            api_name: API 名称，如 'daily', 'intraday', 'top_list' 等
            
        Returns:
            bool: 是否有权限调用
        """
        has_perm = api_name in self.available_permissions
        
        if not has_perm:
            logger.warning(f"积分不足，无法调用 {api_name} 接口（当前积分：{self.points}）")
        
        return has_perm
    
    def get_points(self) -> int:
        """获取当前积分"""
        return self.points
    
    def get_available_permissions(self) -> Set[str]:
        """获取所有可用权限"""
        return self.available_permissions.copy()
    
    def get_unavailable_permissions(self) -> Set[str]:
        """获取不可用权限"""
        all_permissions = set()
        for permissions in self.permission_config.values():
            all_permissions.update(permissions.keys())
        
        return all_permissions - self.available_permissions
    
    def get_points_needed(self, api_name: str) -> Optional[int]:
        """
        获取调用指定 API 所需的积分
        
        Args:
            api_name: API 名称
            
        Returns:
            int: 所需积分，如果当前已有权限则返回 None
        """
        if self.has_permission(api_name):
            return None
        
        # 查找所需积分
        for points_threshold in sorted(self.permission_config.keys()):
            if api_name in self.permission_config[points_threshold]:
                return points_threshold
        
        return None
    
    def get_permission_summary(self) -> Dict[str, any]:
        """
        获取权限摘要信息
        
        Returns:
            dict: 权限摘要
        """
        summary = {
            "points": self.points,
            "available_count": len(self.available_permissions),
            "unavailable_count": len(self.get_unavailable_permissions()),
            "available_apis": sorted(list(self.available_permissions)),
            "unavailable_apis": sorted(list(self.get_unavailable_permissions())),
        }
        
        # 计算下一个等级
        next_level = None
        for points_threshold in sorted(self.permission_config.keys()):
            if points_threshold > self.points:
                next_level = points_threshold
                break
        
        if next_level:
            summary["next_level"] = next_level
            summary["points_to_next"] = next_level - self.points
        
        return summary
    
    def check_and_log_permission(self, api_name: str, fallback_source: str = "akshare") -> bool:
        """
        检查权限并记录日志，如果无权限则建议使用备选数据源
        
        Args:
            api_name: API 名称
            fallback_source: 备选数据源名称
            
        Returns:
            bool: 是否有权限
        """
        if self.has_permission(api_name):
            logger.debug(f"允许调用 {api_name} 接口（积分：{self.points}）")
            return True
        else:
            needed = self.get_points_needed(api_name)
            if needed:
                logger.warning(
                    f"⚠️  积分不足调用 {api_name} 接口\n"
                    f"   当前积分：{self.points}\n"
                    f"   需要积分：{needed}\n"
                    f"   缺少积分：{needed - self.points}\n"
                    f"   自动切换至 {fallback_source}"
                )
            return False


# 全局单例
points_manager = TusharePointsManager()


def get_points_manager() -> TusharePointsManager:
    """获取积分管理器单例"""
    return points_manager
