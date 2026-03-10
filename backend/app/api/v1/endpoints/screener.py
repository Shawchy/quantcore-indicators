from fastapi import APIRouter, Query, Body
from app.models.schemas import ResponseModel, PagedResponseModel
from app.services import stock_service, sector_service, chip_service
from typing import Optional

router = APIRouter()


@router.post("/query", response_model=ResponseModel[list])
async def screen_stocks(
    conditions: dict = Body(..., description="选股条件")
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
async def get_market_statistics():
    stocks = await stock_service.search_stocks("", limit=5000)
    
    total_count = len(stocks)
    industries = {}
    
    for stock in stocks:
        ind = stock.get("industry", "未知")
        if ind not in industries:
            industries[ind] = 0
        industries[ind] += 1
    
    return ResponseModel(data={
        "total_stocks": total_count,
        "industry_distribution": industries,
        "top_industries": sorted(industries.items(), key=lambda x: x[1], reverse=True)[:10]
    })


@router.get("/sector-stats/{sector_code}", response_model=ResponseModel[dict])
async def get_sector_statistics(sector_code: str):
    components = await sector_service.get_sector_components(sector_code)
    leaders = await sector_service.get_sector_leaders(sector_code, 10)
    
    return ResponseModel(data={
        "sector_code": sector_code,
        "component_count": len(components),
        "leaders": leaders
    })


@router.get("/preset-conditions", response_model=ResponseModel[list])
async def get_preset_conditions():
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
            "description": "市值 < 50亿",
            "conditions": {"market_cap_max": 50}
        }
    ])
