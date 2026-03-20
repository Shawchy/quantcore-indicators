"""财务报表数据 API 端点

提供东方财富财务报表数据接口（资产负债表、利润表、现金流量表）
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockZcfzEM, StockLrbEM, StockXjllEM
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/zcfz", response_model=ResponseModel[List[StockZcfzEM]])
async def get_zcfz(
    date: str = Query(..., description="报告期（YYYYMMDD 格式），如 20240331、20240630、20240930、20241231"),
    market: str = Query("hs", description="市场：'hs'=沪深 A 股，'bj'=北交所"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取资产负债表数据
    
    返回指定报告期的资产负债表数据（15 个字段）：
    - 基本信息：序号、股票代码、股票简称、公告日期
    - 资产项目：货币资金、应收账款、存货、总资产、总资产同比
    - 负债项目：应付账款、总负债、预收账款、总负债同比
    - 财务指标：资产负债率、股东权益合计
    
    支持市场：
    - 沪深 A 股：数据范围从 20081231 开始
    - 北交所：数据范围从 20081231 开始
    
    单位说明：金额单位为元，比率为%
    """
    try:
        if market == "bj":
            data = await adapter.get_stock_zcfz_bj_em(date=date)
        else:
            data = await adapter.get_stock_zcfz_em(date=date)
        
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取资产负债表失败：{str(e)}",
            "data": []
        }


@router.get("/lrb", response_model=ResponseModel[List[StockLrbEM]])
async def get_lrb(
    date: str = Query(..., description="报告期（YYYYMMDD 格式），如 20240331、20240630、20240930、20241231"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取利润表数据
    
    返回指定报告期的利润表数据（15 个字段）：
    - 基本信息：序号、股票代码、股票简称、公告日期
    - 盈利指标：净利润、净利润同比、营业利润、利润总额
    - 营收指标：营业总收入、营业总收入同比
    - 支出指标：营业支出、销售费用、管理费用、财务费用、营业总支出
    
    数据范围：从 20120331 开始
    
    单位说明：金额单位为元，比率为%
    """
    try:
        data = await adapter.get_stock_lrb_em(date=date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取利润表失败：{str(e)}",
            "data": []
        }


@router.get("/xjll", response_model=ResponseModel[List[StockXjllEM]])
async def get_xjll(
    date: str = Query(..., description="报告期（YYYYMMDD 格式），如 20240331、20240630、20240930、20241231"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取现金流量表数据
    
    返回指定报告期的现金流量表数据（11 个字段）：
    - 基本信息：序号、股票代码、股票简称、公告日期
    - 净现金流：净现金流、净现金流同比增长
    - 经营性现金流：现金流量净额、净现金流占比
    - 投资性现金流：现金流量净额、净现金流占比
    - 融资性现金流：现金流量净额、净现金流占比
    
    数据范围：从 20081231 开始
    
    单位说明：金额单位为元，比率为%
    """
    try:
        data = await adapter.get_stock_xjll_em(date=date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取现金流量表失败：{str(e)}",
            "data": []
        }
