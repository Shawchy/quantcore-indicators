"""东方财富大盘资金流数据 API 端点

提供东方财富大盘资金流向数据接口
"""
from typing import List
from fastapi import APIRouter, Depends

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockMarketFundFlow
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/market-fund-flow", response_model=ResponseModel[List[StockMarketFundFlow]])
async def get_market_fund_flow(
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 大盘资金流向历史数据
    
    返回大盘资金流向历史数据（15 个字段）：
    - 基本信息：日期
    - 上证指数：上证 - 收盘价、上证 - 涨跌幅（%）
    - 深证指数：深证 - 收盘价、深证 - 涨跌幅（%）
    - 主力流入：主力净流入净额、主力净流入净占比（%）
    - 超大单：超大单净流入净额、超大单净流入净占比（%）
    - 大单：大单净流入净额、大单净流入净占比（%）
    - 中单：中单净流入净额、中单净流入净占比（%）
    - 小单：小单净流入净额、小单净流入净占比（%）
    
    注意：
    - 数据量约 121 条（历史数据）
    - 缓存时间 1 小时
    """
    try:
        data = await adapter.get_stock_market_fund_flow()
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
