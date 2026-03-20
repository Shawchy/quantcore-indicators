"""东方财富行业个股资金流数据 API 端点

提供东方财富行业个股资金流向数据接口
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockSectorFundFlowSummary
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/sector-fund-flow-summary", response_model=ResponseModel[List[StockSectorFundFlowSummary]])
async def get_sector_fund_flow_summary(
    symbol: str = Query(..., description="行业名称（如 电源设备）"),
    indicator: str = Query(
        "今日", 
        description="时间周期",
        enum=["今日", "5 日", "10 日"]
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 行业个股资金流数据
    
    返回指定行业的所有个股资金流向数据（15 个字段）：
    - 基本信息：序号、代码、名称、最新价
    - 涨跌幅：涨跌幅（%）（根据 indicator 不同返回对应周期）
    - 主力流入：主力净流入净额、主力净流入净占比（%）
    - 超大单：超大单净流入净额、超大单净流入净占比（%）
    - 大单：大单净流入净额、大单净流入净占比（%）
    - 中单：中单净流入净额、中单净流入净占比（%）
    - 小单：小单净流入净额、小单净流入净占比（%）
    
    时间周期：
    - 今日：当日资金流向
    - 5 日：近 5 日资金流向
    - 10 日：近 10 日资金流向
    
    行业示例：
    - 电源设备、小金属、有色金属、贵金属、交运设备、钢铁行业等
    
    注意：
    - 数据量根据行业不同（一般几十到几百只股票）
    - 缓存时间 5 分钟
    """
    try:
        data = await adapter.get_stock_sector_fund_flow_summary(
            symbol=symbol,
            indicator=indicator
        )
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取行业个股资金流失败：{str(e)}",
            "data": []
        }
