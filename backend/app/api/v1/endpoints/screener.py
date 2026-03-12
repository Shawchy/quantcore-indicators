from fastapi import APIRouter, Query, Body, Depends
from app.models.schemas import ResponseModel, PagedResponseModel
from app.services import stock_service, sector_service, chip_service
from app.services.trading_calendar import trading_calendar
from app.api.deps import CurrentUser, OptionalCurrentUser
from typing import Optional

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
    
    return ResponseModel(data={
        "total_stocks": total_count or 0,
        "industry_distribution": industries,
        "top_industries": sorted(industries.items(), key=lambda x: x[1], reverse=True)[:10],
        "trade_date": trade_date or (await trading_calendar.get_latest_trading_day())
    })


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
    effective_info = await trading_calendar.get_effective_date()
    return ResponseModel(data=effective_info)


@router.get("/trading-days", response_model=ResponseModel[list])
async def get_trading_days(
    limit: int = Query(60, description="最多返回的交易日数量"),
    current_user: OptionalCurrentUser = None
):
    """获取交易日列表"""
    trading_days = await trading_calendar.get_recent_trading_days(limit)
    return ResponseModel(data=trading_days)
