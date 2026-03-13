from fastapi import APIRouter, Query, Depends
from typing import Optional
from loguru import logger

from app.models.schemas import ResponseModel
from app.services.moneyflow_service import moneyflow_service
from app.api.deps import CurrentUser, OptionalCurrentUser

router = APIRouter()


@router.get("/market", response_model=ResponseModel[dict])
async def get_market_moneyflow(
    current_user: OptionalCurrentUser,
    trade_date: Optional[str] = Query(None, description="交易日期（YYYYMMDD格式）"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYYMMDD格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYYMMDD格式）"),
    days: int = Query(5, description="最近N天数据（当未指定日期范围时生效）"),
):
    """
    获取大盘资金流向数据
    
    返回包含以下字段的数据：
    - trade_date: 交易日期
    - close_sh: 上证收盘价
    - pct_change_sh: 上证涨跌幅(%)
    - close_sz: 深证收盘价
    - pct_change_sz: 深证涨跌幅(%)
    - net_amount: 主力净流入净额
    - net_amount_rate: 主力净流入净占比(%)
    - buy_elg_amount: 超大单净流入净额
    - buy_elg_amount_rate: 超大单净流入净占比(%)
    - buy_lg_amount: 大单净流入净额
    - buy_lg_amount_rate: 大单净流入净占比(%)
    - buy_md_amount: 中单净流入净额
    - buy_md_amount_rate: 中单净流入净占比(%)
    - buy_sm_amount: 小单净流入净额
    - buy_sm_amount_rate: 小单净流入净占比(%)
    """
    try:
        if trade_date or start_date or end_date:
            data = await moneyflow_service.get_market_moneyflow(
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date
            )
        else:
            data = await moneyflow_service.get_latest_market_moneyflow(days=days)
        
        return ResponseModel(data={"items": data, "total": len(data)})
    except Exception as e:
        logger.error(f"获取大盘资金流向失败：{e}")
        return ResponseModel(data={"items": [], "total": 0, "error": str(e)})


@router.get("/market/summary", response_model=ResponseModel[dict])
async def get_market_moneyflow_summary(
    current_user: OptionalCurrentUser,
):
    """
    获取大盘资金流向摘要（用于首页展示）
    
    返回格式化后的资金流向摘要数据，适合在首页卡片中展示
    """
    try:
        summary = await moneyflow_service.get_moneyflow_summary()
        return ResponseModel(data=summary)
    except Exception as e:
        logger.error(f"获取资金流向摘要失败：{e}")
        return ResponseModel(data={"success": False, "message": str(e), "data": None})


@router.get("/market/trend", response_model=ResponseModel[dict])
async def get_market_moneyflow_trend(
    current_user: OptionalCurrentUser,
    days: int = Query(10, description="天数", ge=1, le=60),
):
    """
    获取大盘资金流向趋势数据（用于图表展示）
    
    返回指定天数内的资金流向趋势数据，适合绘制趋势图表
    """
    try:
        trend = await moneyflow_service.get_moneyflow_trend(days=days)
        return ResponseModel(data=trend)
    except Exception as e:
        logger.error(f"获取资金流向趋势失败：{e}")
        return ResponseModel(data={"success": False, "message": str(e)})
