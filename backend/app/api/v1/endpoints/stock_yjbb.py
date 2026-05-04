"""业绩报表数据 API 端点

提供东方财富业绩报表、业绩快报、业绩预告数据接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockYjbbEM, StockYjkbEM, StockYjygEM
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/yjbb", response_model=ResponseModel[List[StockYjbbEM]])
async def get_yjbb(
    date: str = Query(..., description="报告期（YYYYMMDD 格式），如 20240331、20240630、20240930、20241231"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取业绩报表数据
    
    返回指定报告期的业绩报表数据（16 个字段）：
    - 基本信息：序号、股票代码、股票简称
    - 盈利指标：每股收益、净利润、净利润同比增长、净利润季度环比增长
    - 营收指标：营业总收入、营收同比增长、营收季度环比增长
    - 财务指标：每股净资产、净资产收益率、每股经营现金流量、销售毛利率
    - 其他：所处行业、最新公告日期
    
    数据范围：从 20100331 开始
    """
    try:
        data = await adapter.get_stock_yjbb_em(date=date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/yjkb", response_model=ResponseModel[List[StockYjkbEM]])
async def get_yjkb(
    date: str = Query(..., description="报告期（YYYYMMDD 格式），如 20240331、20240630、20240930、20241231"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取业绩快报数据
    
    返回指定报告期的业绩快报数据（18 个字段）：
    - 基本信息：序号、股票代码、股票简称
    - 盈利指标：每股收益、净利润、去年同期净利润、净利润同比增长、净利润季度环比增长
    - 营收指标：营业收入、去年同期营收、营收同比增长、营收季度环比增长
    - 财务指标：每股净资产、净资产收益率
    - 其他：所处行业、公告日期、市场板块、证券类型
    
    数据范围：从 20100331 开始
    """
    try:
        data = await adapter.get_stock_yjkb_em(date=date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/yjyg", response_model=ResponseModel[List[StockYjygEM]])
async def get_yjyg(
    date: str = Query(..., description="报告期（YYYYMMDD 格式），如 20240331、20240630、20240930、20241231"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取业绩预告数据
    
    返回指定报告期的业绩预告数据（11 个字段）：
    - 基本信息：序号、股票代码、股票简称
    - 预测信息：预测指标、业绩变动、预测数值、业绩变动幅度
    - 预告类型：预增、预减、首亏、续亏、略增、略减、续盈、扭亏等
    - 其他：业绩变动原因、上年同期值、公告日期
    
    数据范围：从 20081231 开始
    """
    try:
        data = await adapter.get_stock_yjyg_em(date=date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
