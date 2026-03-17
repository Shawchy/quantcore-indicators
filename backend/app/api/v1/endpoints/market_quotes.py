from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from loguru import logger

from app.models.schemas import ResponseModel, MarketQuote
from app.adapters.factory import data_source_manager

router = APIRouter()


@router.get("/market-quotes", response_model=ResponseModel[List[MarketQuote]])
async def get_market_realtime_quotes(
    market_types: Optional[str] = Query(
        None, 
        description="市场类型，多个类型用逗号分隔。可选值：沪深 A 股，沪 A，深 A，北 A，可转债，期货，创业板，美股，港股，中概股，新股，科创板，沪股通，深股通，行业板块，概念板块，沪深系列指数，上证系列指数，深证系列指数，ETF, LOF"
    )
):
    """
    获取市场实时行情数据
    
    支持获取多个市场板块的实时行情，包括：
    - A 股（沪深、沪市、深市、北证）
    - 创业板、科创板
    - 行业板块、概念板块
    - 指数（沪深、上证、深证系列）
    - 基金（ETF、LOF）
    - 可转债、期货
    - 港股、美股、中概股
    
    数据来源：东方财富网
    
    示例：
    - /api/v1/market-quotes/market-quotes - 获取沪深京 A 股
    - /api/v1/market-quotes/market-quotes?market_types=创业板 - 获取创业板
    - /api/v1/market-quotes/market-quotes?market_types=ETF，LOF - 获取 ETF 和 LOF 基金
    - /api/v1/market-quotes/market-quotes?market_types=行业板块，概念板块 - 获取板块行情
    """
    try:
        # 解析市场类型
        types = None
        if market_types:
            types = [t.strip() for t in market_types.split(',')]
        
        # 使用 efinance 数据源获取市场实时行情
        data = await data_source_manager.get_market_realtime_quotes(
            market_types=types,
            source_type="efinance"
        )
        
        if not data:
            logger.warning(f"未获取到市场实时行情数据，市场类型：{market_types}")
        
        return ResponseModel(
            success=True,
            code="SUCCESS",
            message="获取成功",
            data=data
        )
        
    except Exception as e:
        logger.error(f"获取市场实时行情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-quotes/{market_type}", response_model=ResponseModel[List[MarketQuote]])
async def get_specific_market_quotes(
    market_type: str,
    limit: Optional[int] = Query(
        None, 
        description="返回数据条数限制，默认返回全部"
    )
):
    """
    获取特定市场类型的实时行情
    
    Args:
        market_type: 市场类型，如：创业板，科创板，ETF, 行业板块等
        limit: 返回数据条数限制
    
    支持的 market_type：
    - 沪深 A 股，沪 A，深 A，北 A
    - 创业板，科创板
    - ETF, LOF
    - 行业板块，概念板块
    - 沪深系列指数，上证系列指数，深证系列指数
    - 可转债，期货
    - 港股，美股，中概股
    """
    try:
        # 使用 efinance 数据源获取特定市场类型行情
        data = await data_source_manager.get_market_realtime_quotes(
            market_types=[market_type],
            source_type="efinance"
        )
        
        # 应用数量限制
        if limit and limit > 0:
            data = data[:limit]
        
        if not data:
            logger.warning(f"未获取到 {market_type} 市场实时行情数据")
        
        return ResponseModel(
            success=True,
            code="SUCCESS",
            message="获取成功",
            data=data
        )
        
    except Exception as e:
        logger.error(f"获取 {market_type} 市场实时行情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))
