"""大单追踪数据 API 端点

提供同花顺大单追踪数据接口
"""
from typing import List
from fastapi import APIRouter, Depends

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockFundFlowBigDeal
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/big-deal", response_model=ResponseModel[List[StockFundFlowBigDeal]])
async def get_big_deal(
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取同花顺 - 大单追踪数据
    
    返回当前时点的所有大单追踪记录（9 个字段）：
    - 交易信息：成交时间、股票代码、股票简称、成交价格、成交量（股）、成交额（万元）
    - 大单性质：大单性质（买盘/卖盘）
    - 涨跌信息：涨跌幅（%）、涨跌额（元）
    
    特点：
    - 实时数据，反映当前市场大单交易情况
    - 数据量约 5000 条
    - 可用于监控主力资金的即时动向
    
    注意：
    - 数据为实时快照，缓存时间仅 1 分钟
    - 建议在交易时段（9:30-15:00）使用
    - 大单性质：买盘表示主动买入，卖盘表示主动卖出
    """
    try:
        data = await adapter.get_stock_fund_flow_big_deal()
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取大单追踪数据失败：{str(e)}",
            "data": []
        }
