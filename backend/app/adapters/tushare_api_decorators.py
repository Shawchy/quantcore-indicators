"""
Tushare API 装饰器注册

为现有 API 方法添加装饰器注册，支持权限检查和自动降级
"""

from functools import wraps
from typing import Optional
from loguru import logger

from app.utils.tushare_api_registry import api_registry, APIGroup


def register_tushare_api(api_name: str, group: APIGroup, description: str, 
                         min_points: int = None, cache_ttl: int = 300):
    """
    装饰器：注册 Tushare API 方法
    
    Usage:
        @register_tushare_api("get_stock_list", APIGroup.BASIC, "股票列表")
        async def get_stock_list(self, ...):
            pass
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(self, *args, **kwargs):
            # 检查权限
            if not api_registry.check_permission(api_name):
                logger.warning(f"Tushare 无权限调用 {api_name}，使用备选数据源")
                return [] if 'List' in str(func.__annotations__.get('return', '')) else None
            
            # 调用原函数
            return await func(self, *args, **kwargs)
        
        # 注册到 API 注册表
        api_registry.register(
            api_name=api_name,
            group=group,
            min_points=min_points or group.value[1],
            description=description,
            cache_ttl=cache_ttl
        )
        
        return wrapper
    return decorator


# 定义所有 API 的注册装饰器

# === 基础数据（120 分）===
register_stock_list = lambda f: register_tushare_api("get_stock_list", APIGroup.BASIC, "股票列表", cache_ttl=600)(f)
register_stock_info = lambda f: register_tushare_api("get_stock_info", APIGroup.BASIC, "股票信息")(f)
register_trade_cal = lambda f: register_tushare_api("get_trade_cal", APIGroup.BASIC, "交易日历")(f)

# K 线数据
register_get_kline = lambda f: register_tushare_api("get_kline", APIGroup.KLINE, "日线 K 线")(f)
register_adj_factor = lambda f: register_tushare_api("get_adj_factor", APIGroup.KLINE, "复权因子")(f)

# 指数数据
register_index_daily = lambda f: register_tushare_api("get_index_daily", APIGroup.INDEX, "指数日线")(f)
register_index_weight = lambda f: register_tushare_api("get_index_weight", APIGroup.INDEX, "指数成分股")(f)

# 基金数据
register_fund_basic = lambda f: register_tushare_api("get_fund_basic", APIGroup.FUND, "基金列表")(f)
register_fund_nav = lambda f: register_tushare_api("get_fund_nav", APIGroup.FUND, "基金净值")(f)

# 宏观数据
register_shibor = lambda f: register_tushare_api("get_shibor", APIGroup.MACRO, "Shibor 利率")(f)
register_cn_gdp = lambda f: register_tushare_api("get_cn_gdp", APIGroup.MACRO, "GDP 数据")(f)
register_cn_cpi = lambda f: register_tushare_api("get_cn_cpi", APIGroup.MACRO, "CPI 数据")(f)
register_cn_ppi = lambda f: register_tushare_api("get_cn_ppi", APIGroup.MACRO, "PPI 数据")(f)

# === 进阶数据（200-800 分）===
# 交易异动
register_top_list = lambda f: register_tushare_api("get_top_list", APIGroup.TRADING, "龙虎榜", 200)(f)
register_block_trade = lambda f: register_tushare_api("get_block_trade", APIGroup.TRADING, "大宗交易", 200)(f)
register_margin_detail = lambda f: register_tushare_api("get_margin_detail", APIGroup.TRADING, "融资融券", 200)(f)

# 财务数据
register_forecast = lambda f: register_tushare_api("get_forecast", APIGroup.FINANCE, "业绩预告", 800)(f)
register_express = lambda f: register_tushare_api("get_express", APIGroup.FINANCE, "业绩快报", 800)(f)
register_finance = lambda f: register_tushare_api("get_finance", APIGroup.FINANCE, "财务指标", 800)(f)

# === 高级数据（2000-5000 分）===
# 周月线
register_weekly = lambda f: register_tushare_api("get_weekly", APIGroup.WEEKLY, "周线行情", 2000)(f)
register_monthly = lambda f: register_tushare_api("get_monthly", APIGroup.WEEKLY, "月线行情", 2000)(f)

# 分钟数据
register_intraday = lambda f: register_tushare_api("get_intraday", APIGroup.INTRADAY, "分时数据", 5000)(f)
register_bar = lambda f: register_tushare_api("get_bar", APIGroup.INTRADAY, "分钟 K 线", 5000)(f)
register_moneyflow = lambda f: register_tushare_api("get_moneyflow", APIGroup.MONEYFLOW, "资金流向", 5000)(f)

# === 专业数据（10000+ 分）===
# 筹码分布
register_chip_distribution = lambda f: register_tushare_api("get_chip_distribution", APIGroup.CHIP, "筹码分布", 10000)(f)
register_stk_holdernumber = lambda f: register_tushare_api("get_stk_holdernumber", APIGroup.CHIP, "股东人数", 10000)(f)

# Level-2 数据
register_level2_tick = lambda f: register_tushare_api("get_level2_tick", APIGroup.LEVEL2, "Level-2 逐笔", 10000)(f)

# 盈利预测
register_profit_forecast = lambda f: register_tushare_api("get_profit_forecast", APIGroup.FORECAST, "盈利预测", 10000)(f)
