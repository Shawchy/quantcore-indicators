from fastapi import APIRouter, Query
from app.models.schemas import ResponseModel
from app.services import sector_service
from typing import Optional

router = APIRouter()


@router.get("/list", response_model=ResponseModel[list])
async def get_sector_list(
    sector_type: str = Query("industry", description="板块类型: industry行业, concept概念, area地域")
):
    data = await sector_service.get_sector_list(sector_type)
    return ResponseModel(data=data)


@router.get("/ranking", response_model=ResponseModel[list])
async def get_sector_ranking(
    sector_type: str = Query("industry"),
    sort_by: str = Query("change_pct", description="排序字段: change_pct, volume, amount"),
    limit: int = Query(20)
):
    data = await sector_service.get_sector_ranking(sector_type, sort_by, limit)
    return ResponseModel(data=data)


@router.get("/components/{sector_code}", response_model=ResponseModel[list])
async def get_sector_components(sector_code: str):
    data = await sector_service.get_sector_components(sector_code)
    return ResponseModel(data=data)


@router.get("/leaders/{sector_code}", response_model=ResponseModel[list])
async def get_sector_leaders(sector_code: str, top_n: int = Query(5)):
    data = await sector_service.get_sector_leaders(sector_code, top_n)
    return ResponseModel(data=data)
