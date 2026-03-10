from fastapi import APIRouter, Query
from app.models.schemas import ResponseModel
from app.services import chip_service
from typing import Optional

router = APIRouter()


@router.get("/data/{code}", response_model=ResponseModel[list])
async def get_chip_data(
    code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    data = await chip_service.get_chip_data(code, start_date, end_date)
    return ResponseModel(data=data)


@router.get("/control-degree/{code}", response_model=ResponseModel[dict])
async def get_control_degree(
    code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    data = await chip_service.calculate_control_degree(code, start_date, end_date)
    return ResponseModel(data=data)


@router.get("/screen", response_model=ResponseModel[list])
async def screen_high_control(
    min_control_degree: float = Query(0.5, description="最小控盘度"),
    max_control_degree: float = Query(1.0, description="最大控盘度"),
    limit: int = Query(50)
):
    data = await chip_service.screen_high_control(min_control_degree, max_control_degree, limit)
    return ResponseModel(data=data)


@router.get("/ranking", response_model=ResponseModel[list])
async def get_control_ranking(
    sort_order: str = Query("desc", description="排序方式: desc降序, asc升序"),
    limit: int = Query(50)
):
    data = await chip_service.get_control_ranking(sort_order, limit)
    return ResponseModel(data=data)
