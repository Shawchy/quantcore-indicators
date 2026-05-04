"""东方财富个股资金流数据 API 端点

提供东方财富个股资金流向数据接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockIndividualFundFlow, StockIndividualFundFlowRank
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/individual-fund-flow", response_model=ResponseModel[List[StockIndividualFundFlow]])
async def get_individual_fund_flow(
    stock: str = Query(..., description="股票代码（如 600094）"),
    market: str = Query(..., description="市场", enum=["sh", "sz", "bj"]),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 个股资金流数据
    
    返回指定股票近 100 个交易日的资金流向数据（13 个字段）：
    - 基本信息：日期、收盘价、涨跌幅（%）
    - 主力流入：主力净流入净额、主力净流入净占比（%）
    - 超大单：超大单净流入净额、超大单净流入净占比（%）
    - 大单：大单净流入净额、大单净流入净占比（%）
    - 中单：中单净流入净额、中单净流入净占比（%）
    - 小单：小单净流入净额、小单净流入净占比（%）
    
    支持市场：
    - sh: 上海证券交易所
    - sz: 深证证券交易所
    - bj: 北京证券交易所
    
    注意：
    - 数据量约 100 条（近 100 个交易日）
    - 缓存时间 1 小时
    """
    try:
        data = await adapter.get_stock_individual_fund_flow(stock=stock, market=market)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/individual-fund-flow-rank", response_model=ResponseModel[List[StockIndividualFundFlowRank]])
async def get_individual_fund_flow_rank(
    indicator: str = Query(
        "今日", 
        description="排行指标",
        enum=["今日", "3 日", "5 日", "10 日"]
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 个股资金流排名数据
    
    返回全部 A 股个股的资金流向排名数据（15 个字段）：
    - 基本信息：序号、代码、名称、最新价
    - 涨跌幅：根据 indicator 不同，返回对应周期的涨跌幅（%）
    - 主力流入：主力净流入净额、主力净流入净占比（%）
    - 超大单：超大单净流入净额、超大单净流入净占比（%）
    - 大单：大单净流入净额、大单净流入净占比（%）
    - 中单：中单净流入净额、中单净流入净占比（%）
    - 小单：小单净流入净额、小单净流入净占比（%）
    
    排行周期：
    - 今日：当日资金流向排名
    - 3 日：近 3 日资金流向排名
    - 5 日：近 5 日资金流向排名
    - 10 日：近 10 日资金流向排名
    
    注意：
    - 数据量较大（全部 A 股），建议使用分页或筛选
    - 缓存时间 5 分钟
    """
    try:
        data = await adapter.get_stock_individual_fund_flow_rank(indicator=indicator)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
