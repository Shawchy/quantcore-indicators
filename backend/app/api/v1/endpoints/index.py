from fastapi import APIRouter, HTTPException, Path
from typing import List
from loguru import logger

from app.models.schemas import ResponseModel, IndexComponent
from app.adapters.factory import data_source_manager

router = APIRouter()


@router.get("/index/{code}/components", response_model=ResponseModel[List[IndexComponent]])
async def get_index_components(
    code: str = Path(..., description="指数代码")
):
    """
    获取指数成分股
    
    返回指定指数的所有成分股，包括：
    - 股票代码、名称
    - 权重
    - 所属行业
    
    数据来源：东方财富网
    
    示例指数代码：
    - 000001: 上证指数
    - 000300: 沪深 300
    - 000016: 上证 50
    - 399001: 深证成指
    """
    try:
        components = await data_source_manager.get_members(
            index_code=code,
            source_type="efinance"
        )
        
        if not components:
            logger.warning(f"未获取到指数 {code} 的成分股")
        
        return ResponseModel(
            success=True,
            code="SUCCESS",
            message="获取成功",
            data=components
        )
        
    except Exception as e:
        logger.error(f"获取指数成分股失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
