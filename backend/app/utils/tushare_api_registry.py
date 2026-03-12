"""
Tushare API 注册表和分组管理

基于装饰器模式的 API 权限管理，支持自动降级和文档生成
"""

from enum import Enum
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from loguru import logger


class APIGroup(Enum):
    """
    API 分组枚举
    
    格式：(分组名，所需积分，分组描述)
    """
    # === 基础数据（120 分）===
    BASIC = ("basic", 120, "基础股票信息")
    KLINE = ("kline", 120, "K 线数据")
    INDEX = ("index", 120, "指数数据")
    FUND = ("fund", 120, "基金数据")
    MACRO = ("macro", 120, "宏观数据")
    
    # === 进阶数据（200-800 分）===
    TRADING = ("trading", 200, "交易异动数据")
    FINANCE = ("finance", 800, "财务数据")
    
    # === 高级数据（2000-5000 分）===
    WEEKLY = ("weekly", 2000, "周月线数据")
    INTRADAY = ("intraday", 5000, "分钟级数据")
    MONEYFLOW = ("moneyflow", 5000, "资金流向")
    
    # === 专业数据（10000+ 分）===
    CHIP = ("chip", 10000, "筹码分布")
    LEVEL2 = ("level2", 10000, "Level-2 数据")
    FORECAST = ("forecast", 10000, "盈利预测")


@dataclass
class APIInfo:
    """
    API 元数据信息
    
    Attributes:
        name: API 名称
        group: API 分组
        description: API 描述
        min_points: 所需最低积分
        fallback: 降级数据源
        cache_ttl: 缓存时间（秒）
        enabled: 是否启用
    """
    name: str
    group: APIGroup
    description: str
    min_points: int = 0
    fallback: str = "akshare"
    cache_ttl: int = 300
    enabled: bool = True


class TushareAPIRegistry:
    """
    Tushare API 注册表（单例模式）
    
    功能：
    1. 注册所有 Tushare API
    2. 管理 API 分组
    3. 检查调用权限
    4. 自动降级处理
    5. 生成 API 文档
    """
    
    _instance: Optional['TushareAPIRegistry'] = None
    _initialized: bool = False
    
    def __new__(cls) -> 'TushareAPIRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._apis: Dict[str, APIInfo] = {}
        self._groups: Dict[APIGroup, List[str]] = {}
        self._func_map: Dict[str, Callable] = {}  # API 名称到函数的映射
        
        # 初始化所有 API
        self._init_all_apis()
        self._initialized = True
        
        logger.info(f"Tushare API 注册表初始化完成，共注册 {len(self._apis)} 个 API")
    
    def _init_all_apis(self):
        """初始化所有 API 注册信息"""
        
        # === 基础数据（120 分）===
        self._register_api("stock_basic", APIGroup.BASIC, "股票列表")
        self._register_api("trade_cal", APIGroup.BASIC, "交易日历")
        self._register_api("dividend", APIGroup.BASIC, "分红送股")
        self._register_api("name_change", APIGroup.BASIC, "股票更名")
        
        # K 线数据
        self._register_api("daily", APIGroup.KLINE, "日线行情")
        self._register_api("adj_factor", APIGroup.KLINE, "复权因子")
        self._register_api("index_daily", APIGroup.INDEX, "指数日线")
        self._register_api("index_weight", APIGroup.INDEX, "指数成分股")
        
        # 基金数据
        self._register_api("fund_basic", APIGroup.FUND, "基金列表")
        self._register_api("fund_nav", APIGroup.FUND, "基金净值")
        self._register_api("fund_div", APIGroup.FUND, "基金分红")
        
        # 宏观数据
        self._register_api("shibor", APIGroup.MACRO, "Shibor 利率")
        self._register_api("cn_gdp", APIGroup.MACRO, "GDP 数据")
        self._register_api("cn_cpi", APIGroup.MACRO, "CPI 数据")
        self._register_api("cn_ppi", APIGroup.MACRO, "PPI 数据")
        
        # === 进阶数据（200-800 分）===
        # 交易异动
        self._register_api("top_list", APIGroup.TRADING, "龙虎榜")
        self._register_api("top_inst", APIGroup.TRADING, "龙虎榜机构明细")
        self._register_api("block_trade", APIGroup.TRADING, "大宗交易")
        self._register_api("margin_detail", APIGroup.TRADING, "融资融券")
        
        # 财务数据
        self._register_api("forecast", APIGroup.FINANCE, "业绩预告")
        self._register_api("express", APIGroup.FINANCE, "业绩快报")
        self._register_api("finance", APIGroup.FINANCE, "财务指标")
        self._register_api("income", APIGroup.FINANCE, "利润表")
        self._register_api("balance", APIGroup.FINANCE, "资产负债表")
        self._register_api("cashflow", APIGroup.FINANCE, "现金流量表")
        
        # === 高级数据（2000-5000 分）===
        # 周月线
        self._register_api("weekly", APIGroup.WEEKLY, "周线行情")
        self._register_api("monthly", APIGroup.WEEKLY, "月线行情")
        
        # 分钟数据
        self._register_api("intraday", APIGroup.INTRADAY, "分时数据")
        self._register_api("bar", APIGroup.INTRADAY, "分钟 K 线")
        self._register_api("moneyflow", APIGroup.MONEYFLOW, "资金流向")
        self._register_api("moneyflow_cnt", APIGroup.MONEYFLOW, "资金流向统计")
        
        # === 专业数据（10000+ 分）===
        # 筹码分布
        self._register_api("chip_distribution", APIGroup.CHIP, "筹码分布")
        self._register_api("stk_holdernumber", APIGroup.CHIP, "股东人数")
        self._register_api("stk_holdertrade", APIGroup.CHIP, "股东增减持")
        
        # Level-2 数据
        self._register_api("level2_tick", APIGroup.LEVEL2, "Level-2 逐笔")
        
        # 盈利预测
        self._register_api("profit_forecast", APIGroup.FORECAST, "盈利预测")
        self._register_api("broker_recommend", APIGroup.FORECAST, "券商金股")
    
    def _register_api(self, name: str, group: APIGroup, description: str,
                      fallback: str = "akshare", cache_ttl: int = 300):
        """
        注册 API
        
        Args:
            name: API 名称
            group: API 分组
            description: API 描述
            fallback: 降级数据源
            cache_ttl: 缓存时间（秒）
        """
        min_points = group.value[1]
        
        self._apis[name] = APIInfo(
            name=name,
            group=group,
            description=description,
            min_points=min_points,
            fallback=fallback,
            cache_ttl=cache_ttl,
            enabled=True
        )
        
        # 添加到分组
        if group not in self._groups:
            self._groups[group] = []
        self._groups[group].append(name)
    
    def register(self, api_name: str = None, group: APIGroup = None, 
                 min_points: int = None, description: str = None,
                 fallback: str = "akshare", cache_ttl: int = 300):
        """
        装饰器：注册 API 函数
        
        Usage:
            @registry.register(group=APIGroup.KLINE, description="日线行情")
            async def get_daily(...):
                pass
        """
        def decorator(func: Callable):
            # 从参数或函数名获取 API 名称
            name = api_name or func.__name__
            
            # 获取积分要求
            points = min_points or (group.value[1] if group else 120)
            
            # 获取分组
            api_group = group or APIGroup.BASIC
            
            # 获取描述
            desc = description or func.__doc__ or name
            
            # 注册 API
            self._apis[name] = APIInfo(
                name=name,
                group=api_group,
                description=desc,
                min_points=points,
                fallback=fallback,
                cache_ttl=cache_ttl,
                enabled=True
            )
            
            # 添加到分组
            if api_group not in self._groups:
                self._groups[api_group] = []
            self._groups[api_group].append(name)
            
            # 保存函数映射
            self._func_map[name] = func
            
            logger.debug(f"注册 API: {name} ({api_group.value[0]}, {points}分)")
            
            return func
        return decorator
    
    def check_permission(self, api_name: str) -> bool:
        """
        检查 API 调用权限
        
        Args:
            api_name: API 名称
            
        Returns:
            bool: 是否有权限调用
        """
        from app.utils.tushare_points_manager import get_points_manager
        
        if api_name not in self._apis:
            logger.error(f"未知 API: {api_name}")
            return False
        
        api_info = self._apis[api_name]
        
        if not api_info.enabled:
            logger.warning(f"API 已禁用：{api_name}")
            return False
        
        points_mgr = get_points_manager()
        current_points = points_mgr.get_points()
        
        if current_points >= api_info.min_points:
            logger.debug(f"✅ {api_name} 权限检查通过 "
                        f"({current_points} >= {api_info.min_points}分)")
            return True
        else:
            logger.warning(f"❌ {api_name} 权限不足 "
                          f"({current_points} < {api_info.min_points}分，"
                          f"需要{api_info.min_points - current_points}分)")
            return False
    
    def get_api_info(self, api_name: str) -> Optional[APIInfo]:
        """获取 API 详细信息"""
        return self._apis.get(api_name)
    
    def get_function(self, api_name: str) -> Optional[Callable]:
        """获取 API 函数"""
        return self._func_map.get(api_name)
    
    def get_available_apis(self) -> List[str]:
        """获取当前积分可用的 API 列表"""
        from app.utils.tushare_points_manager import get_points_manager
        
        points_mgr = get_points_manager()
        points = points_mgr.get_points()
        
        available = []
        for name, api_info in self._apis.items():
            if points >= api_info.min_points and api_info.enabled:
                available.append(name)
        
        return sorted(available)
    
    def get_unavailable_apis(self) -> List[Dict]:
        """获取当前不可用的 API 列表"""
        from app.utils.tushare_points_manager import get_points_manager
        
        points_mgr = get_points_manager()
        points = points_mgr.get_points()
        
        unavailable = []
        for name, api_info in self._apis.items():
            if points < api_info.min_points and api_info.enabled:
                unavailable.append({
                    "name": name,
                    "description": api_info.description,
                    "group": api_info.group.value[0],
                    "required_points": api_info.min_points,
                    "lack_points": api_info.min_points - points
                })
        
        return sorted(unavailable, key=lambda x: x["required_points"])
    
    def get_apis_by_group(self, group: APIGroup) -> List[str]:
        """获取指定分组的所有 API"""
        return self._groups.get(group, [])
    
    def get_group_info(self, group: APIGroup) -> Dict:
        """获取分组信息"""
        apis = self.get_apis_by_group(group)
        available = [api for api in apis if self.check_permission(api)]
        
        return {
            "name": group.value[0],
            "description": group.value[2],
            "required_points": group.value[1],
            "total_apis": len(apis),
            "available_apis": len(available),
            "api_list": available
        }
    
    def get_permission_summary(self) -> Dict:
        """获取权限摘要信息"""
        from app.utils.tushare_points_manager import get_points_manager
        
        points_mgr = get_points_manager()
        points = points_mgr.get_points()
        
        available = self.get_available_apis()
        unavailable = self.get_unavailable_apis()
        
        # 按分组统计
        groups_info = {}
        for group in APIGroup:
            groups_info[group.value[0]] = self.get_group_info(group)
        
        # 计算下一等级
        next_level = None
        for group in sorted(APIGroup, key=lambda x: x.value[1]):
            if group.value[1] > points:
                next_level = group
                break
        
        summary = {
            "current_points": points,
            "available_count": len(available),
            "unavailable_count": len(unavailable),
            "total_count": len(self._apis),
            "groups": groups_info,
            "next_level": {
                "name": next_level.value[0] if next_level else None,
                "description": next_level.value[2] if next_level else None,
                "required_points": next_level.value[1] if next_level else None,
                "lack_points": (next_level.value[1] - points) if next_level else 0
            } if next_level else None
        }
        
        return summary
    
    def generate_api_documentation(self) -> str:
        """生成 API 文档"""
        from app.utils.tushare_points_manager import get_points_manager
        
        points_mgr = get_points_manager()
        points = points_mgr.get_points()
        
        doc_lines = [
            "=" * 80,
            "Tushare API 分组文档",
            "=" * 80,
            f"\n当前积分：{points}分",
            f"可用 API：{len(self.get_available_apis())}/{len(self._apis)}",
            "\n" + "-" * 80
        ]
        
        for group in sorted(APIGroup, key=lambda x: x.value[1]):
            group_info = self.get_group_info(group)
            status = "✅" if points >= group.value[1] else "🔒"
            
            doc_lines.append(
                f"\n{status} {group_info['name'].upper()} ({group_info['required_points']}分)"
            )
            doc_lines.append(f"   {group_info['description']}")
            doc_lines.append(f"   可用：{group_info['available_apis']}/{group_info['total_apis']}")
            
            if group_info['api_list']:
                doc_lines.append("   接口列表:")
                for api_name in group_info['api_list']:
                    api_info = self._apis[api_name]
                    doc_lines.append(f"     - {api_name}: {api_info.description}")
        
        doc_lines.append("\n" + "=" * 80)
        
        return "\n".join(doc_lines)


# 全局单例
api_registry = TushareAPIRegistry()


def get_api_registry() -> TushareAPIRegistry:
    """获取 API 注册表单例"""
    return api_registry
