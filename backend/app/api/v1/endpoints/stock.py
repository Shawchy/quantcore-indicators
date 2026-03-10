from fastapi import APIRouter, Query, Depends
from app.models.schemas import ResponseModel, KLineData, StockBasic, TechnicalIndicator
from app.services import stock_service
from app.api.deps import CurrentUser
from typing import Optional

router = APIRouter()


@router.get("/basic/{code}", response_model=ResponseModel[dict])
async def get_stock_basic(code: str, current_user: CurrentUser):
    data = await stock_service.get_stock_basic(code)
    return ResponseModel(data=data)


@router.get("/kline/{code}", response_model=ResponseModel[dict])
async def get_kline(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    adjust: str = Query("qfq", description="复权类型：qfq 前复权，hfq 后复权，none 不复权"),
    priority_load: bool = Query(True, description="是否启用优先加载模式"),
    current_user: CurrentUser = Depends
):
    data = await stock_service.get_kline(code, start_date, end_date, adjust, priority_load=priority_load)
    return ResponseModel(data=data)


@router.get("/indicators/{code}", response_model=ResponseModel[list])
async def get_technical_indicators(
    code: str,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    current_user: CurrentUser = Depends
):
    data = await stock_service.get_technical_indicators(code, start_date, end_date)
    return ResponseModel(data=data)


@router.get("/realtime/{code}", response_model=ResponseModel[dict])
async def get_realtime_quote(code: str, current_user: CurrentUser):
    data = await stock_service.get_realtime_quote(code)
    return ResponseModel(data=data)


@router.get("/search", response_model=ResponseModel[list])
async def search_stocks(
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, description="返回数量限制"),
    current_user: CurrentUser = Depends
):
    data = await stock_service.search_stocks(keyword, limit)
    return ResponseModel(data=data)
