"""资金流向数据 API 端点

提供同花顺资金流向数据接口（个股、概念、行业）
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockFundFlowIndividual, StockFundFlowConcept, StockFundFlowIndustry
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/fund-flow-individual", response_model=ResponseModel[List[StockFundFlowIndividual]])
async def get_fund_flow_individual(
    symbol: str = Query(
        "即时", 
        description="排行类型",
        enum=["即时", "3 日排行", "5 日排行", "10 日排行", "20 日排行"]
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取同花顺 - 个股资金流数据
    
    返回全部 A 股个股的资金流向数据：
    
    **即时模式**（10 个字段）：
    - 基本信息：序号、股票代码、股票简称、最新价
    - 涨跌信息：涨跌幅（%）、换手率（%）
    - 资金流向：流入资金（元）、流出资金（元）、净额（元）、成交额（元）
    
    **排行模式**（7 个字段）：
    - 基本信息：序号、股票代码、股票简称、最新价
    - 排行信息：阶段涨跌幅（%）、连续换手率（%）、资金流入净额（元）
    
    排行类型：
    - 即时：实时资金流向数据
    - 3 日排行：近 3 日资金流向排行
    - 5 日排行：近 5 日资金流向排行
    - 10 日排行：近 10 日资金流向排行
    - 20 日排行：近 20 日资金流向排行
    
    注意：数据量较大（约 5000 条），建议使用分页或筛选
    """
    try:
        data = await adapter.get_stock_fund_flow_individual(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/fund-flow-concept", response_model=ResponseModel[List[StockFundFlowConcept]])
async def get_fund_flow_concept(
    symbol: str = Query(
        "即时", 
        description="排行类型",
        enum=["即时", "3 日排行", "5 日排行", "10 日排行", "20 日排行"]
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取同花顺 - 概念资金流数据
    
    返回全部概念板块的资金流向数据：
    
    **即时模式**（11 个字段）：
    - 基本信息：序号、概念名称、行业指数
    - 涨跌信息：行业 - 涨跌幅（%）
    - 资金流向：流入资金（亿）、流出资金（亿）、净额（亿）
    - 板块信息：公司家数、领涨股、领涨股 - 涨跌幅（%）、当前价（元）
    
    **排行模式**（8 个字段）：
    - 基本信息：序号、概念名称、公司家数、行业指数
    - 排行信息：阶段涨跌幅（%）、流入资金（亿）、流出资金（亿）、净额（亿）
    
    注意：数据量约 400 条概念板块
    """
    try:
        data = await adapter.get_stock_fund_flow_concept(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/fund-flow-industry", response_model=ResponseModel[List[StockFundFlowIndustry]])
async def get_fund_flow_industry(
    symbol: str = Query(
        "即时", 
        description="排行类型",
        enum=["即时", "3 日排行", "5 日排行", "10 日排行", "20 日排行"]
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取同花顺 - 行业资金流数据
    
    返回全部行业板块的资金流向数据：
    
    **即时模式**（11 个字段）：
    - 基本信息：序号、行业名称、行业指数
    - 涨跌信息：行业 - 涨跌幅（%）
    - 资金流向：流入资金（亿）、流出资金（亿）、净额（亿）
    - 板块信息：公司家数、领涨股、领涨股 - 涨跌幅（%）、当前价
    
    **排行模式**（8 个字段）：
    - 基本信息：序号、行业名称、公司家数、行业指数
    - 排行信息：阶段涨跌幅（%）、流入资金（亿）、流出资金（亿）、净额（亿）
    
    注意：数据量约几十个行业板块
    """
    try:
        data = await adapter.get_stock_fund_flow_industry(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
