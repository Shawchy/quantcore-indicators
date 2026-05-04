"""东方财富板块资金流排名数据 API 端点

提供东方财富板块资金流向排名数据接口
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockSectorFundFlowRank
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/sector-fund-flow-rank", response_model=ResponseModel[List[StockSectorFundFlowRank]])
async def get_sector_fund_flow_rank(
    indicator: str = Query(
        "今日", 
        description="时间周期",
        enum=["今日", "5 日", "10 日"]
    ),
    sector_type: str = Query(
        "行业资金流", 
        description="板块类型",
        enum=["行业资金流", "概念资金流", "地域资金流"]
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 板块资金流排名数据
    
    返回指定板块类型的资金流向排名数据（14 个字段）：
    - 基本信息：序号、名称
    - 涨跌幅：涨跌幅（%）（根据 indicator 不同返回对应周期）
    - 主力流入：主力净流入净额、主力净流入净占比（%）
    - 超大单：超大单净流入净额、超大单净流入净占比（%）
    - 大单：大单净流入净额、大单净流入净占比（%）
    - 中单：中单净流入净额、中单净流入净占比（%）
    - 小单：小单净流入净额、小单净流入净占比（%）
    - 最大股：主力净流入最大股
    
    时间周期：
    - 今日：当日资金流向排名
    - 5 日：近 5 日资金流向排名
    - 10 日：近 10 日资金流向排名
    
    板块类型：
    - 行业资金流：按行业分类的板块
    - 概念资金流：按概念分类的板块
    - 地域资金流：按地域分类的板块
    
    注意：
    - 数据量根据板块类型不同（约 80-100 个板块）
    - 缓存时间 5 分钟
    """
    try:
        data = await adapter.get_stock_sector_fund_flow_rank(
            indicator=indicator,
            sector_type=sector_type
        )
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
