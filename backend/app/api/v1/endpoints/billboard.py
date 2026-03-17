from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from loguru import logger

from app.models.schemas import ResponseModel, BillboardEntry
from app.adapters.factory import data_source_manager

router = APIRouter()


@router.get("/billboard", response_model=ResponseModel[List[BillboardEntry]])
async def get_daily_billboard(
    trade_date: Optional[str] = Query(None, description="交易日期，格式：YYYY-MM-DD，默认今日")
):
    """
    获取龙虎榜单数据
    
    龙虎榜是交易所公布的当日异动股票名单，包括：
    - 日涨幅偏离值达到 7% 的前 5 只证券
    - 日跌幅偏离值达到 7% 的前 5 只证券
    - 日振幅值达到 15% 的前 5 只证券
    - 日换手率达到 20% 的前 5 只证券
    - 无价格涨跌幅限制的证券
    
    数据来源：东方财富网
    """
    try:
        # 使用 efinance 数据源获取龙虎榜数据
        data = await data_source_manager.get_daily_billboard(
            trade_date=trade_date,
            source_type="efinance"
        )
        
        if not data:
            logger.warning(f"未获取到龙虎榜数据，日期：{trade_date}")
        
        return ResponseModel(
            success=True,
            code="SUCCESS",
            message="获取成功",
            data=data
        )
        
    except Exception as e:
        logger.error(f"获取龙虎榜数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/billboard/{code}", response_model=ResponseModel[List[BillboardEntry]])
async def get_stock_billboard(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD")
):
    """
    获取个股历史龙虎榜数据
    
    Args:
        code: 股票代码
        start_date: 开始日期
        end_date: 结束日期
    """
    try:
        # 这里可以调用历史龙虎榜 API，目前返回空列表
        # TODO: 实现历史龙虎榜查询
        logger.warning(f"个股历史龙虎榜查询暂未实现，代码：{code}")
        
        return ResponseModel(
            success=True,
            code="SUCCESS",
            message="功能暂未实现",
            data=[]
        )
        
    except Exception as e:
        logger.error(f"获取个股历史龙虎榜数据失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
