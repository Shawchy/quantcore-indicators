"""
Tushare API 分组管理方案分析

根据积分权限对 API 进行分组管理的可行性分析
"""

from typing import Dict, List, Any

# 可行性分析

## 1. 技术可行性 ✅

### 优势：
1. **已有积分管理器基础**
   - TusharePointsManager 已实现
   - 权限检查机制已工作
   - 单例模式，性能优秀

2. **代码结构清晰**
   - 适配器模式
   - 工厂模式
   - 易于扩展

3. **Python 动态特性**
   - 可以动态注册 API
   - 支持装饰器模式
   - 灵活的元编程能力

## 2. 架构设计

### 方案一：基于装饰器的 API 分组

```python
from app.utils.tushare_points_manager import get_points_manager

def require_points(min_points: int, api_group: str):
    """
    API 权限装饰器
    
    Args:
        min_points: 所需最低积分
        api_group: API 分组名称
    """
    def decorator(func):
        async def wrapper(self, *args, **kwargs):
            points_mgr = get_points_manager()
            
            # 检查积分权限
            if not points_mgr.has_permission(api_group):
                logger.warning(f"{api_group} 需要{min_points}积分，当前{points_mgr.get_points()}分")
                # 自动降级到备选数据源
                return await self._fallback_to_akshare(func.__name__, *args, **kwargs)
            
            return await func(self, *args, **kwargs)
        return wrapper
    return decorator

# 使用示例
class TushareAdapter(BaseDataAdapter):
    
    @require_points(120, "daily")
    async def get_kline(self, code: str, ...) -> List[KLineData]:
        # 实现代码
        pass
    
    @require_points(5000, "intraday")
    async def get_stock_zh_a_minute(self, symbol: str, ...) -> List[Dict]:
        # 实现代码
        pass
    
    @require_points(2000, "finance")
    async def get_financial_report(self, code: str, ...) -> Dict:
        # 实现代码
        pass
```

### 方案二：基于配置文件的 API 分组

```python
# config.py
TUSHARE_API_GROUPS = {
    "basic": {
        "points": 120,
        "apis": ["stock_basic", "trade_cal", "dividend"],
        "description": "基础股票信息"
    },
    "kline": {
        "points": 120,
        "apis": ["daily", "adj_factor", "index_daily"],
        "description": "K 线数据"
    },
    "intraday": {
        "points": 5000,
        "apis": ["intraday", "bar"],
        "description": "分钟级数据"
    },
    "finance": {
        "points": 800,
        "apis": ["forecast", "express", "finance_report"],
        "description": "财务数据"
    },
    "advanced": {
        "points": 10000,
        "apis": ["chip_distribution", "level2", "moneyflow"],
        "description": "高级数据"
    }
}

# 使用示例
class TushareAdapter(BaseDataAdapter):
    
    async def get_kline(self, code: str, ...):
        # 检查 API 分组权限
        if not self._check_group_permission("kline"):
            return await self._fallback("akshare")
        # 实现代码
        pass
```

### 方案三：基于注册表的 API 分组（推荐）

```python
# app/utils/tushare_api_registry.py

from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Callable

class APIGroup(Enum):
    """API 分组枚举"""
    BASIC = "basic"           # 基础数据（120 分）
    KLINE = "kline"           # K 线数据（120 分）
    FINANCE = "finance"       # 财务数据（800 分）
    INTRADAY = "intraday"     # 分钟数据（5000 分）
    ADVANCED = "advanced"     # 高级数据（10000 分）

@dataclass
class APIMetadata:
    """API 元数据"""
    name: str
    group: APIGroup
    min_points: int
    description: str
    func: Callable
    fallback: str = "akshare"  # 降级数据源

class TushareAPIRegistry:
    """API 注册表（单例）"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._apis: Dict[str, APIMetadata] = {}
        self._groups: Dict[APIGroup, List[str]] = {}
        self._register_all_apis()
        self._initialized = True
    
    def register(self, name: str, group: APIGroup, min_points: int, 
                 description: str, fallback: str = "akshare"):
        """注册 API 的装饰器"""
        def decorator(func: Callable):
            metadata = APIMetadata(
                name=name,
                group=group,
                min_points=min_points,
                description=description,
                func=func,
                fallback=fallback
            )
            self._apis[name] = metadata
            
            # 添加到分组
            if group not in self._groups:
                self._groups[group] = []
            self._groups[group].append(name)
            
            return func
        return decorator
    
    def _register_all_apis(self):
        """注册所有 API"""
        
        # 基础数据（120 分）
        @self.register("stock_basic", APIGroup.BASIC, 120, "股票列表")
        async def get_stock_basic(...):
            pass
        
        @self.register("trade_cal", APIGroup.BASIC, 120, "交易日历")
        async def get_trade_cal(...):
            pass
        
        # K 线数据（120 分）
        @self.register("daily", APIGroup.KLINE, 120, "日线行情")
        async def get_daily(...):
            pass
        
        @self.register("adj_factor", APIGroup.KLINE, 120, "复权因子")
        async def get_adj_factor(...):
            pass
        
        # 财务数据（800 分）
        @self.register("forecast", APIGroup.FINANCE, 800, "业绩预告")
        async def get_forecast(...):
            pass
        
        # 分钟数据（5000 分）
        @self.register("intraday", APIGroup.INTRADAY, 5000, "分时数据")
        async def get_intraday(...):
            pass
        
        @self.register("bar", APIGroup.INTRADAY, 5000, "分钟 K 线")
        async def get_bar(...):
            pass
        
        # 高级数据（10000 分）
        @self.register("level2", APIGroup.ADVANCED, 10000, "Level-2 数据")
        async def get_level2(...):
            pass
    
    def check_permission(self, api_name: str) -> bool:
        """检查 API 调用权限"""
        from app.utils.tushare_points_manager import get_points_manager
        
        if api_name not in self._apis:
            return False
        
        metadata = self._apis[api_name]
        points_mgr = get_points_manager()
        
        return points_mgr.get_points() >= metadata.min_points
    
    def get_available_apis(self) -> List[str]:
        """获取当前积分可用的 API 列表"""
        from app.utils.tushare_points_manager import get_points_manager
        
        points = points_mgr.get_points()
        available = []
        
        for name, metadata in self._apis.items():
            if points >= metadata.min_points:
                available.append(name)
        
        return available
    
    def get_group_apis(self, group: APIGroup) -> List[str]:
        """获取指定分组的所有 API"""
        return self._groups.get(group, [])
    
    def get_api_metadata(self, api_name: str) -> APIMetadata:
        """获取 API 元数据"""
        return self._apis.get(api_name)

# 全局注册表实例
api_registry = TushareAPIRegistry()
```

## 3. 使用示例

### 在适配器中使用

```python
# app/adapters/tushare_adapter.py

from app.utils.tushare_api_registry import api_registry, APIGroup

class TushareAdapter(BaseDataAdapter):
    
    @api_registry.register("get_kline", APIGroup.KLINE, 120, "日线 K 线")
    async def get_kline(self, code: str, ...) -> List[KLineData]:
        if not api_registry.check_permission("get_kline"):
            logger.warning("积分不足，降级到 AkShare")
            return await self._fallback_akshare("get_kline", code, ...)
        
        # 正常实现
        ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
        df = self._pro.daily(ts_code=ts_code, ...)
        ...
    
    @api_registry.register("get_intraday", APIGroup.INTRADAY, 5000, "分时数据")
    async def get_stock_intraday_em(self, symbol: str) -> List[Dict]:
        if not api_registry.check_permission("get_intraday"):
            logger.warning("分时数据需要 5000 积分，降级到 AkShare")
            return await self._fallback_akshare("get_intraday", symbol)
        
        # 正常实现
        df = self._pro.intraday(ts_code=ts_code)
        ...
```

## 4. 优势分析

### ✅ 优点

1. **清晰的权限管理**
   - 每个 API 都有明确的积分要求
   - 自动检查权限
   - 详细的日志记录

2. **自动降级**
   - 积分不足时自动切换到备选数据源
   - 用户无感知
   - 业务代码无需修改

3. **易于扩展**
   - 新增 API 只需注册
   - 自动继承权限管理
   - 统一的错误处理

4. **文档自动生成**
   - 可以从注册表生成 API 文档
   - 显示每个 API 的积分要求
   - 分组展示

5. **性能监控**
   - 可以统计每个 API 的调用次数
   - 监控降级情况
   - 优化数据源选择

### ⚠️ 挑战

1. **代码重构工作量**
   - 需要为现有 API 添加注册
   - 需要统一接口签名
   - 需要处理边界情况

2. **测试复杂度**
   - 需要测试每个分组
   - 需要测试降级逻辑
   - 需要测试不同积分场景

3. **维护成本**
   - 需要维护注册表
   - 需要更新文档
   - 需要同步 Tushare API 变化

## 5. 推荐实施方案

### 阶段一：基础框架（1-2 天）

1. 创建 API 注册表
2. 实现装饰器模式
3. 集成积分管理器
4. 实现自动降级

### 阶段二：API 迁移（2-3 天）

1. 迁移现有 API 到注册表
2. 添加分组标签
3. 测试降级逻辑
4. 完善错误处理

### 阶段三：新增 API（持续）

1. 根据需求新增 API
2. 自动注册到分组
3. 配置积分要求
4. 测试验证

### 阶段四：文档和监控（1 天）

1. 生成 API 文档
2. 添加性能监控
3. 添加使用统计
4. 优化建议

## 6. 代码示例

### 完整的 API 分组实现

```python
# app/utils/tushare_api_groups.py

from enum import Enum
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from loguru import logger

class APIGroup(Enum):
    """API 分组"""
    # 基础数据（120 分）
    BASIC = ("basic", 120, "基础股票信息")
    KLINE = ("kline", 120, "K 线数据")
    INDEX = ("index", 120, "指数数据")
    FUND = ("fund", 120, "基金数据")
    
    # 进阶数据（200-800 分）
    TRADING = ("trading", 200, "交易异动数据")
    FINANCE = ("finance", 800, "财务数据")
    
    # 高级数据（2000-5000 分）
    WEEKLY = ("weekly", 2000, "周月线数据")
    INTRADAY = ("intraday", 5000, "分钟级数据")
    MONEYFLOW = ("moneyflow", 5000, "资金流向")
    
    # 专业数据（10000+ 分）
    CHIP = ("chip", 10000, "筹码分布")
    LEVEL2 = ("level2", 10000, "Level-2 数据")
    FORECAST = ("forecast", 10000, "盈利预测")

@dataclass
class APIInfo:
    """API 信息"""
    name: str
    group: APIGroup
    description: str
    params: Dict[str, Any] = field(default_factory=dict)
    fallback: str = "akshare"
    cache_ttl: int = 300  # 缓存时间（秒）

class TushareAPIGroups:
    """Tushare API 分组管理"""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._apis: Dict[str, APIInfo] = {}
        self._init_all_apis()
        self._initialized = True
    
    def _init_all_apis(self):
        """初始化所有 API"""
        
        # === 基础数据（120 分）===
        self._register_api("stock_basic", APIGroup.BASIC, "股票列表")
        self._register_api("trade_cal", APIGroup.BASIC, "交易日历")
        self._register_api("dividend", APIGroup.BASIC, "分红送股")
        
        # === K 线数据（120 分）===
        self._register_api("daily", APIGroup.KLINE, "日线行情")
        self._register_api("adj_factor", APIGroup.KLINE, "复权因子")
        self._register_api("index_daily", APIGroup.INDEX, "指数日线")
        
        # === 基金数据（120 分）===
        self._register_api("fund_basic", APIGroup.FUND, "基金列表")
        self._register_api("fund_nav", APIGroup.FUND, "基金净值")
        
        # === 交易异动（200 分）===
        self._register_api("top_list", APIGroup.TRADING, "龙虎榜")
        self._register_api("block_trade", APIGroup.TRADING, "大宗交易")
        self._register_api("margin_detail", APIGroup.TRADING, "融资融券")
        
        # === 财务数据（800 分）===
        self._register_api("forecast", APIGroup.FINANCE, "业绩预告")
        self._register_api("express", APIGroup.FINANCE, "业绩快报")
        self._register_api("finance_report", APIGroup.FINANCE, "财务报表")
        
        # === 周月线（2000 分）===
        self._register_api("weekly", APIGroup.WEEKLY, "周线行情")
        self._register_api("monthly", APIGroup.WEEKLY, "月线行情")
        
        # === 分钟数据（5000 分）===
        self._register_api("intraday", APIGroup.INTRADAY, "分时数据")
        self._register_api("bar", APIGroup.INTRADAY, "分钟 K 线")
        self._register_api("moneyflow", APIGroup.MONEYFLOW, "资金流向")
        
        # === 高级数据（10000 分）===
        self._register_api("chip_distribution", APIGroup.CHIP, "筹码分布")
        self._register_api("level2", APIGroup.LEVEL2, "Level-2 数据")
        self._register_api("profit_forecast", APIGroup.FORECAST, "盈利预测")
    
    def _register_api(self, name: str, group: APIGroup, description: str, 
                      params: Dict = None, fallback: str = "akshare", 
                      cache_ttl: int = 300):
        """注册 API"""
        self._apis[name] = APIInfo(
            name=name,
            group=group,
            description=description,
            params=params or {},
            fallback=fallback,
            cache_ttl=cache_ttl
        )
    
    def check_permission(self, api_name: str) -> bool:
        """检查 API 调用权限"""
        from app.utils.tushare_points_manager import get_points_manager
        
        if api_name not in self._apis:
            logger.error(f"未知 API: {api_name}")
            return False
        
        api_info = self._apis[api_name]
        points_mgr = get_points_manager()
        current_points = points_mgr.get_points()
        
        if current_points >= api_info.group.value[1]:
            logger.debug(f"✅ {api_name} 权限检查通过 "
                        f"({current_points} >= {api_info.group.value[1]}分)")
            return True
        else:
            logger.warning(f"❌ {api_name} 权限不足 "
                          f"({current_points} < {api_info.group.value[1]}分)")
            return False
    
    def get_available_apis(self) -> List[str]:
        """获取当前可用的 API 列表"""
        from app.utils.tushare_points_manager import get_points_manager
        
        points = points_mgr.get_points()
        available = []
        
        for name, api_info in self._apis.items():
            if points >= api_info.group.value[1]:
                available.append(name)
        
        return sorted(available)
    
    def get_unavailable_apis(self) -> List[str]:
        """获取当前不可用的 API 列表"""
        from app.utils.tushare_points_manager import get_points_manager
        
        points = points_mgr.get_points()
        unavailable = []
        
        for name, api_info in self._apis.items():
            if points < api_info.group.value[1]:
                unavailable.append({
                    "name": name,
                    "description": api_info.description,
                    "group": api_info.group.value[0],
                    "required_points": api_info.group.value[1],
                    "lack_points": api_info.group.value[1] - points
                })
        
        return sorted(unavailable, key=lambda x: x["required_points"])
    
    def get_apis_by_group(self, group: APIGroup) -> List[str]:
        """获取指定分组的所有 API"""
        return [name for name, info in self._apis.items() 
                if info.group == group]
    
    def get_api_info(self, api_name: str) -> Optional[APIInfo]:
        """获取 API 详细信息"""
        return self._apis.get(api_name)
    
    def get_permission_summary(self) -> Dict:
        """获取权限摘要"""
        from app.utils.tushare_points_manager import get_points_manager
        
        points_mgr = get_points_manager()
        points = points_mgr.get_points()
        
        summary = {
            "current_points": points,
            "available_count": len(self.get_available_apis()),
            "total_count": len(self._apis),
            "groups": {}
        }
        
        for group in APIGroup:
            group_apis = self.get_apis_by_group(group)
            available_in_group = [api for api in group_apis 
                                 if points >= group.value[1]]
            
            summary["groups"][group.value[0]] = {
                "name": group.value[2],
                "required_points": group.value[1],
                "total": len(group_apis),
                "available": len(available_in_group),
                "apis": available_in_group if points >= group.value[1] else []
            }
        
        return summary

# 全局实例
api_groups = TushareAPIGroups()
```

## 7. 结论

### ✅ 可行性评估：**完全可行**

**技术层面**:
- ✅ 已有积分管理器基础
- ✅ Python 支持动态注册
- ✅ 装饰器模式成熟
- ✅ 性能影响可忽略

**业务层面**:
- ✅ 清晰的权限管理
- ✅ 自动降级机制
- ✅ 易于扩展维护
- ✅ 文档自动生成

**实施难度**:
- 🟡 中等（需要重构现有代码）
- 🟡 工作量：3-5 天
- 🟢 风险低（可逐步迁移）

### 🎯 推荐方案

**采用方案三：基于注册表的 API 分组**

理由：
1. 最灵活，支持动态扩展
2. 代码最清晰，易于维护
3. 可以自动生成文档
4. 支持性能监控
5. 便于测试

### 📋 下一步

1. 创建 API 注册表
2. 实现装饰器模式
3. 迁移现有 API
4. 测试验证
5. 生成文档
