from fastapi import APIRouter, HTTPException, Path
from typing import List
from loguru import logger

from app.models.schemas import ResponseModel, ShareholderInfo
from app.adapters.factory import data_source_manager

router = APIRouter()


@router.get("/stock/{code}/shareholders", response_model=ResponseModel[List[ShareholderInfo]])
async def get_stock_shareholders(
    code: str = Path(..., description="股票代码")
):
    """
    获取股票前十大股东信息
    
    返回最新报告期的前十大股东信息，包括：
    - 股东名称
    - 股东类型（机构/个人）
    - 持股数量
    - 持股比例
    - 持股变化
    - 报告期
    
    数据来源：东方财富网
    """
    try:
        shareholders = await data_source_manager.get_top10_stock_holder_info(
            code=code,
            source_type="efinance"
        )
        
        if not shareholders:
            logger.warning(f"未获取到 {code} 的前十大股东信息")
        
        return ResponseModel(
            success=True,
            code="SUCCESS",
            message="获取成功",
            data=shareholders
        )
        
    except Exception as e:
        logger.error(f"获取前十大股东信息失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
