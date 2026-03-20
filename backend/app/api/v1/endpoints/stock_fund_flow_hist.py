"""东方财富行业/概念历史资金流数据 API 端点

提供东方财富行业和概念历史资金流向数据接口
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockSectorFundFlowHist
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/sector-fund-flow-hist", response_model=ResponseModel[List[StockSectorFundFlowHist]])
async def get_sector_fund_flow_hist(
    symbol: str = Query(..., description="行业名称（如 汽车服务）"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 行业历史资金流数据
    
    返回指定行业的历史资金流数据（11 个字段，约 121 条）：
    - 基本信息：日期
    - 主力流入：主力净流入净额、主力净流入净占比（%）
    - 超大单：超大单净流入净额、超大单净流入净占比（%）
    - 大单：大单净流入净额、大单净流入净占比（%）
    - 中单：中单净流入净额、中单净流入净占比（%）
    - 小单：小单净流入净额、小单净流入净占比（%）
    
    行业示例：
    - 汽车服务、电源设备、小金属、有色金属、钢铁行业等
    
    注意：
    - 数据量约 121 条（历史数据）
    - 缓存时间 1 小时
    """
    try:
        data = await adapter.get_stock_sector_fund_flow_hist(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取行业历史资金流失败：{str(e)}",
            "data": []
        }


@router.get("/concept-fund-flow-hist", response_model=ResponseModel[List[StockSectorFundFlowHist]])
async def get_concept_fund_flow_hist(
    symbol: str = Query(..., description="概念名称（如 数据要素）"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 概念历史资金流数据
    
    返回指定概念的历史资金流数据（11 个字段，约 121 条）：
    - 基本信息：日期
    - 主力流入：主力净流入净额、主力净流入净占比（%）
    - 超大单：超大单净流入净额、超大单净流入净占比（%）
    - 大单：大单净流入净额、大单净流入净占比（%）
    - 中单：中单净流入净额、中单净流入净占比（%）
    - 小单：小单净流入净额、小单净流入净占比（%）
    
    概念示例：
    - 数据要素、锂电池、人工智能、芯片、5G 等
    
    注意：
    - 数据量约 121 条（历史数据）
    - 缓存时间 1 小时
    """
    try:
        data = await adapter.get_stock_concept_fund_flow_hist(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取概念历史资金流失败：{str(e)}",
            "data": []
        }
