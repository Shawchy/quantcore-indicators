"""
Tushare API 自动注册器

自动为 TushareAdapter 的所有方法添加装饰器注册
"""

from typing import Dict, Any, Optional
from loguru import logger

from app.utils.tushare_api_registry import api_registry, APIGroup


# API 方法到分组的映射
API_METHOD_MAPPING = {
    # 基础数据（120 分）
    "get_stock_list": (APIGroup.BASIC, "股票列表", 600),
    "get_stock_info": (APIGroup.BASIC, "股票信息", 600),
    "get_kline": (APIGroup.KLINE, "日线 K 线", 300),
    "get_realtime_quote": (APIGroup.KLINE, "实时行情", 60),
    "get_market_index_kline": (APIGroup.INDEX, "指数 K 线", 300),
    "get_sector_list": (APIGroup.INDEX, "板块列表", 600),
    "get_sector_components": (APIGroup.INDEX, "板块成分股", 600),
    
    # 筹码数据（需要 10000 分）
    "get_chip_data": (APIGroup.CHIP, "筹码数据", 300),
}


def auto_register_tushare_apis(adapter_instance):
    """
    自动注册 TushareAdapter 的所有 API 方法
    
    Usage:
        adapter = TushareAdapter()
        auto_register_tushare_apis(adapter)
    """
    registered_count = 0
    
    for method_name, (group, description, cache_ttl) in API_METHOD_MAPPING.items():
        # 检查方法是否存在
        if hasattr(adapter_instance, method_name):
            method = getattr(adapter_instance, method_name)
            
            # 注册到 API 注册表
            api_registry.register(
                api_name=method_name,
                group=group,
                min_points=group.value[1],
                description=description,
                cache_ttl=cache_ttl
            )
            
            registered_count += 1
            logger.debug(f"注册 API: {method_name} ({group.value[0]}, {group.value[1]}分)")
    
    logger.info(f"自动注册完成：{registered_count}/{len(API_METHOD_MAPPING)} 个 API")
    return registered_count


def create_api_wrapper(adapter_class):
    """
    为 adapter class 创建包装器，自动添加权限检查
    
    Usage:
        WrappedAdapter = create_api_wrapper(TushareAdapter)
        adapter = WrappedAdapter()
    """
    from functools import wraps
    
    class WrappedAdapter(adapter_class):
        async def initialize(self) -> bool:
            # 先初始化父类
            result = await super().initialize()
            
            if result:
                # 初始化完成后自动注册所有 API
                auto_register_tushare_apis(self)
            
            return result
    
    return WrappedAdapter
