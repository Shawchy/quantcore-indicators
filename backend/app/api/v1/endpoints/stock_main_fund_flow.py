"""东方财富主力净流入排名数据 API 端点

提供东方财富主力净流入排名数据接口
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockMainFundFlow
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/main-fund-flow", response_model=ResponseModel[List[StockMainFundFlow]])
async def get_main_fund_flow(
    symbol: str = Query(
        "全部股票", 
        description="市场类型",
        enum=["全部股票", "沪深 A 股", "沪市 A 股", "科创板", "深市 A 股", "创业板", "沪市 B 股", "深市 B 股"]
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 主力净流入排名数据
    
    返回指定市场类型的主力净流入排名数据（14 个字段）：
    - 基本信息：序号、代码、名称、最新价
    - 今日排行：主力净占比（%）、今日排名、今日涨跌（%）
    - 5 日排行：主力净占比（%）、5 日排名、5 日涨跌（%）
    - 10 日排行：主力净占比（%）、10 日排名、10 日涨跌（%）
    - 板块：所属板块
    
    市场类型：
    - 全部股票：所有 A 股和 B 股
    - 沪深 A 股：上海和深圳 A 股
    - 沪市 A 股：上海证券交易所 A 股
    - 科创板：上海证券交易所科创板
    - 深市 A 股：深圳证券交易所 A 股
    - 创业板：深圳证券交易所创业板
    - 沪市 B 股：上海证券交易所 B 股
    - 深市 B 股：深圳证券交易所 B 股
    
    注意：
    - 数据量根据市场类型不同（全部股票约 5200+ 只）
    - 缓存时间 5 分钟
    """
    try:
        data = await adapter.get_stock_main_fund_flow(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取主力净流入排名失败：{str(e)}",
            "data": []
        }
