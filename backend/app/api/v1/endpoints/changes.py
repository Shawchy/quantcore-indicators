"""盘口异动 API 端点

提供个股盘口异动、板块异动详情等接口
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockChanges
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/stock-changes", response_model=ResponseModel[List[StockChanges]])
async def get_stock_changes(
    trade_date: Optional[str] = Query(
        None,
        description="交易日期，格式 YYYYMMDD，默认为今日"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取盘口异动数据
    
    - **code**: 股票代码
    - **name**: 股票名称
    - **change_type**: 异动类型（快速拉升、大幅下跌等）
    - **change_time**: 异动时间
    - **price**: 当前价
    - **change_pct**: 涨跌幅
    - **volume_ratio**: 量比
    - **turnover_rate**: 换手率
    - **reason**: 异动原因
    
    使用场景：
    - 实时监控个股异动
    - 捕捉快速拉升机会
    - 识别异常波动风险
    - 追踪资金动向
    """
    try:
        data = await adapter.get_stock_changes(trade_date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/board-changes", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_board_changes(
    trade_date: Optional[str] = Query(
        None,
        description="交易日期，格式 YYYYMMDD，默认为今日"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取板块异动详情
    
    返回数据字段：
    - **board_name**: 板块名称
    - **board_code**: 板块代码
    - **change_type**: 异动类型
    - **change_time**: 异动时间
    - **change_pct**: 涨跌幅
    - **volume_ratio**: 量比
    - **leader_stock**: 领涨股
    - **reason**: 异动原因
    
    使用场景：
    - 监控板块轮动
    - 识别热点板块
    - 追踪板块资金流向
    - 发现板块联动机会
    """
    try:
        data = await adapter.get_board_changes(trade_date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
