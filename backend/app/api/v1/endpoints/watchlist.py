from fastapi import APIRouter, Query, Body
from app.models.schemas import ResponseModel
from app.services import watchlist_service

router = APIRouter()


@router.get("/list", response_model=ResponseModel[list])
async def get_watchlist():
    data = await watchlist_service.get_watchlist()
    return ResponseModel(data=data)


@router.post("/add", response_model=ResponseModel[dict])
async def add_to_watchlist(
    code: str = Body(..., embed=True),
    note: str = Body(None, embed=True)
):
    data = await watchlist_service.add_to_watchlist(code, note)
    return ResponseModel(data=data)


@router.delete("/remove/{code}", response_model=ResponseModel[dict])
async def remove_from_watchlist(code: str):
    data = await watchlist_service.remove_from_watchlist(code)
    return ResponseModel(data=data)


@router.put("/update/{code}", response_model=ResponseModel[dict])
async def update_watchlist_note(
    code: str,
    note: str = Body(..., embed=True)
):
    data = await watchlist_service.update_watchlist_note(code, note)
    return ResponseModel(data=data)


@router.get("/quotes", response_model=ResponseModel[list])
async def get_watchlist_quotes():
    data = await watchlist_service.get_watchlist_quotes()
    return ResponseModel(data=data)
