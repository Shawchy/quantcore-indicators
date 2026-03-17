from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from loguru import logger

from app.models.schemas import ResponseModel, CapitalFlowItem
from app.adapters.factory import data_source_manager

router = APIRouter()


@router.get("/capital-flow/today", response_model=ResponseModel[List[CapitalFlowItem]])
async def get_today_capital_flow(
    trade_date: Optional[str] = Query(None, description="交易日期，格式：YYYY-MM-DD，默认今日")
):
    """
    获取当日资金流向数据
    
    返回全市场股票的当日资金流向，包括：
    - 主力净流入额及占比
    - 超大单、大单、中单、小单净流入
    - 涨跌幅、收盘价等
    
    数据来源：东方财富网
    """
    try:
        data = await data_source_manager.get_today_bill(
            trade_date=trade_date,
            source_type="efinance"
        )
        
        if not data:
            logger.warning(f"未获取到当日资金流向数据，日期：{trade_date}")
        
        return ResponseModel(
            success=True,
            code="SUCCESS",
            message="获取成功",
            data=data
        )
        
    except Exception as e:
        logger.error(f"获取当日资金流向数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capital-flow/{code}", response_model=ResponseModel[List[CapitalFlowItem]])
async def get_stock_capital_flow(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD")
):
    """
    获取个股历史资金流向数据
    
    Args:
        code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    
    返回：
    - 每日主力净流入额及占比
    - 超大单、大单、中单、小单净流入
    - 收盘价、涨跌幅等
    """
    try:
        data = await data_source_manager.get_history_bill(
            code=code,
            start_date=start_date,
            end_date=end_date,
            source_type="efinance"
        )
        
        if not data:
            logger.warning(f"未获取到 {code} 的历史资金流向数据")
        
        return ResponseModel(
            success=True,
            code="SUCCESS",
            message="获取成功",
            data=data
        )
        
    except Exception as e:
        logger.error(f"获取个股历史资金流向数据失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
