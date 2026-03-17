from fastapi import APIRouter, HTTPException, Path
from typing import List
from loguru import logger

from app.models.schemas import ResponseModel, BoardInfo
from app.adapters.factory import data_source_manager

router = APIRouter()


@router.get("/stock/{code}/boards", response_model=ResponseModel[List[BoardInfo]])
async def get_stock_boards(
    code: str = Path(..., description="股票代码")
):
    """
    获取股票所属板块
    
    返回股票所属的所有板块，包括：
    - 行业板块
    - 概念板块
    - 地域板块
    
    数据来源：东方财富网
    """
    try:
        boards = await data_source_manager.get_belong_board(
            code=code,
            source_type="efinance"
        )
        
        if not boards:
            logger.warning(f"未获取到 {code} 的所属板块信息")
        
        return ResponseModel(
            success=True,
            code="SUCCESS",
            message="获取成功",
            data=boards
        )
        
    except Exception as e:
        logger.error(f"获取股票所属板块失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
