from fastapi import APIRouter, Query, Body, Depends
from app.models.schemas import ResponseModel, PagedResponseModel
from app.services import stock_service, sector_service, chip_service
from app.services.trading_calendar import trading_calendar
from app.api.deps import CurrentUser, OptionalCurrentUser
from typing import Optional
from loguru import logger
from datetime import datetime, timedelta
import asyncio
import random

router = APIRouter()


@router.post("/query", response_model=ResponseModel[list])
async def screen_stocks(
    conditions: dict = Body(..., description="选股条件"),
    current_user: CurrentUser = Depends
):
    results = []
    
    market_cap_min = conditions.get("market_cap_min")
    market_cap_max = conditions.get("market_cap_max")
    pe_min = conditions.get("pe_min")
    pe_max = conditions.get("pe_max")
    industry = conditions.get("industry")
    control_degree_min = conditions.get("control_degree_min")
    
    stocks = await stock_service.search_stocks("", limit=1000)
    
    for stock in stocks:
        match = True
        
        if industry and stock.get("industry") != industry:
            match = False
        
        if match and control_degree_min:
            try:
                control_info = await chip_service.calculate_control_degree(stock["code"])
                if control_info.get("control_degree", 0) < control_degree_min:
                    match = False
            except:
                match = False
        
        if match:
            results.append(stock)
    
    return ResponseModel(data=results[:100])


@router.get("/market-stats", response_model=ResponseModel[dict])
async def get_market_statistics(
    trade_date: Optional[str] = Query(None, description="交易日期，格式 YYYYMMDD"),
    current_user: OptionalCurrentUser = None
):
    """获取市场统计数据"""
    from sqlalchemy import select, func
    from app.storage.sqlite import get_session, StockInfo
    from app.services.market_turnover_service import market_turnover_service
    from app.utils.api_cache_stats import api_cache
    
    # 使用缓存，避免每次都调用 akshare（太慢了）
    cache_key = {'date': trade_date}
    cached_data = await api_cache.get('api_stats', cache_key)
    if cached_data:
        return ResponseModel(data=cached_data)
    
    # 直接从数据库查询，而不是从数据源获取
    async with get_session() as session:
        # 查询总数
        result = await session.execute(select(func.count()).select_from(StockInfo))
        total_count = result.scalar()
        
        # 查询行业分布
        result = await session.execute(
            select(StockInfo.industry, func.count()).group_by(StockInfo.industry)
        )
        industries = {ind: cnt for ind, cnt in result.all() if ind}
        
        # 计算市场总成交额：优先从数据库获取历史数据
        total_turnover = 0.0  # 默认值
        
        try:
            # 尝试从数据库获取（带超时保护）
            turnover_data = await asyncio.wait_for(
                market_turnover_service.fetch_and_save_latest(session),
                timeout=10.0  # 10 秒超时
            )
            
            if turnover_data:
                total_turnover = turnover_data.get('total_turnover', 0.0)
                logger.info(f"从数据库获取成交额：{total_turnover/100000000:.2f}亿")
            else:
                logger.info("数据库无成交额数据，使用默认值 0")
                
        except asyncio.TimeoutError:
            logger.warning("获取成交额超时，使用默认值 0")
        except Exception as e:
            logger.error(f"获取成交额失败：{e}")
    
    # 获取交易日期（带超时保护）
    try:
        effective_trade_date = await asyncio.wait_for(
            trading_calendar.get_latest_trading_day(),
            timeout=5.0  # 5 秒超时
        )
    except asyncio.TimeoutError:
        logger.warning("获取交易日期超时，使用今天日期")
        effective_trade_date = datetime.now().strftime("%Y%m%d")
    except Exception as e:
        logger.warning(f"获取交易日期失败：{e}，使用今天日期")
        effective_trade_date = datetime.now().strftime("%Y%m%d")
    
    result_data = {
        "total_stocks": total_count or 0,
        "industry_distribution": industries,
        "top_industries": sorted(industries.items(), key=lambda x: x[1], reverse=True)[:10] if industries else [],
        "turnover": total_turnover,  # 市场总成交额（元）
        "trade_date": trade_date or effective_trade_date
    }
    
    logger.info(f"市场统计数据：total_stocks={total_count}, industries={len(industries)}")
    
    # 缓存 5 分钟（300 秒）
    await api_cache.set('api_stats', cache_key, result_data, ttl=300)
    
    return ResponseModel(data=result_data)


@router.get("/sector-stats/{sector_code}", response_model=ResponseModel[dict])
async def get_sector_statistics(sector_code: str, current_user: CurrentUser = Depends):
    components = await sector_service.get_sector_components(sector_code)
    leaders = await sector_service.get_sector_leaders(sector_code, 10)
    
    return ResponseModel(data={
        "sector_code": sector_code,
        "component_count": len(components),
        "leaders": leaders
    })


@router.get("/preset-conditions", response_model=ResponseModel[list])
async def get_preset_conditions(current_user: CurrentUser = Depends):
    return ResponseModel(data=[
        {
            "id": "low_pe",
            "name": "低市盈率",
            "description": "PE < 15",
            "conditions": {"pe_max": 15}
        },
        {
            "id": "high_control",
            "name": "高控盘",
            "description": "控盘度 > 0.7",
            "conditions": {"control_degree_min": 0.7}
        },
        {
            "id": "small_cap",
            "name": "小市值",
            "description": "市值 < 50 亿",
            "conditions": {"market_cap_max": 50}
        }
    ])


@router.get("/effective-date", response_model=ResponseModel[dict])
async def get_effective_date(current_user: OptionalCurrentUser = None):
    """获取智能判断的有效日期"""
    from app.utils.api_cache_stats import api_cache
    import asyncio
    
    # 检查缓存
    cache_key = {'type': 'effective_date'}
    cached_data = await api_cache.get('trading_calendar', cache_key)
    if cached_data:
        return ResponseModel(data=cached_data)
    
    # 获取有效日期（带超时保护）
    try:
        effective_info = await asyncio.wait_for(
            trading_calendar.get_effective_date(),
            timeout=5.0  # 5 秒超时
        )
    except asyncio.TimeoutError:
        logger.warning("获取有效日期超时，使用默认值")
        today = datetime.now().strftime("%Y%m%d")
        effective_info = {
            "effective_date": today,
            "is_today": True,
            "is_market_open": False,
            "latest_trading_day": today,
            "previous_trading_day": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"),
            "current_time": datetime.now().strftime("%H:%M:%S")
        }
    except Exception as e:
        logger.error(f"获取有效日期失败：{e}")
        today = datetime.now().strftime("%Y%m%d")
        effective_info = {
            "effective_date": today,
            "is_today": True,
            "is_market_open": False,
            "latest_trading_day": today,
            "previous_trading_day": (datetime.now() - timedelta(days=1)).strftime("%Y%m%d"),
            "current_time": datetime.now().strftime("%H:%M:%S")
        }
    
    # 缓存 5 分钟
    await api_cache.set('trading_calendar', cache_key, effective_info, ttl=300)
    
    return ResponseModel(data=effective_info)


@router.get("/trading-days", response_model=ResponseModel[list])
async def get_trading_days(
    limit: int = Query(60, description="最多返回的交易日数量"),
    current_user: OptionalCurrentUser = None
):
    """获取交易日列表"""
    from app.utils.api_cache_stats import api_cache
    import asyncio
    
    # 检查缓存
    cache_key = {'type': 'trading_days', 'limit': limit}
    cached_data = await api_cache.get('trading_calendar', cache_key)
    if cached_data:
        return ResponseModel(data=cached_data)
    
    # 获取交易日列表（带超时保护）
    try:
        trading_days = await asyncio.wait_for(
            trading_calendar.get_recent_trading_days(limit),
            timeout=5.0  # 5 秒超时
        )
    except asyncio.TimeoutError:
        logger.warning("获取交易日列表超时，使用估算值")
        # 使用估算方法
        trading_days = []
        current = datetime.now()
        while len(trading_days) < limit:
            if current.weekday() < 5:  # 排除周末
                trading_days.append({
                    "date": current.strftime("%Y%m%d"),
                    "display": f"{current.month}月{current.day}日",
                    "is_today": len(trading_days) == 0,
                    "is_latest": len(trading_days) == 0,
                    "is_selected": len(trading_days) == 0
                })
            current -= timedelta(days=1)
    except Exception as e:
        logger.error(f"获取交易日列表失败：{e}")
        trading_days = []
    
    # 缓存 5 分钟
    await api_cache.set('trading_calendar', cache_key, trading_days, ttl=300)
    
    return ResponseModel(data=trading_days)
