"""东方财富基金持股数据 API 端点

提供东方财富基金持仓汇总和明细数据接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockReportFundHold, StockReportFundHoldDetail
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/report-fund-hold", response_model=ResponseModel[List[StockReportFundHold]])
async def get_report_fund_hold(
    symbol: str = Query(
        "基金持仓", 
        description="持仓类型",
        enum=["基金持仓", "QFII 持仓", "社保持仓", "券商持仓", "保险持仓", "信托持仓"]
    ),
    date: str = Query(..., description="财报发布日期（格式：YYYYMMDD，如 20200630）"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 基金持仓汇总数据
    
    返回指定报告期的基金持仓汇总数据（9 个字段）：
    - 基本信息：序号、股票代码、股票简称
    - 持仓统计：持有基金家数（家）、持股总数（股）、持股市值（元）
    - 持仓变化：持股变化（新进/增持/减持/退出）、持股变动数值（股）、持股变动比例（%）
    
    持仓类型：
    - 基金持仓：公募基金持仓统计
    - QFII 持仓：合格境外机构投资者持仓
    - 社保持仓：全国社保基金持仓
    - 券商持仓：证券公司持仓
    - 保险持仓：保险公司持仓
    - 信托持仓：信托公司持仓
    
    财报日期：
    - 一季报：xxxx0331
    - 中报：xxxx0630
    - 三季报：xxxx0930
    - 年报：xxxx1231
    
    注意：
    - 数据量较大（数千条），建议使用筛选
    - 缓存时间 1 小时
    """
    try:
        data = await adapter.get_stock_report_fund_hold(
            symbol=symbol,
            date=date
        )
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/report-fund-hold-detail", response_model=ResponseModel[List[StockReportFundHoldDetail]])
async def get_report_fund_hold_detail(
    symbol: str = Query(..., description="基金代码（如 005827）"),
    date: str = Query(..., description="财报发布日期（格式：YYYYMMDD，如 20201231）"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 基金持仓明细数据
    
    返回指定基金在指定报告期的持仓明细数据（7 个字段）：
    - 基本信息：序号、股票代码、股票简称
    - 持仓数据：持股数（股）、持股市值（元）
    - 持仓比例：占总股本比例（%）、占流通股本比例（%）
    
    财报日期：
    - 一季报：xxxx0331
    - 中报：xxxx0630
    - 三季报：xxxx0930
    - 年报：xxxx1231
    
    注意：
    - 基金在一、三季报不披露全部持仓，中报/年报统计更为准确
    - 缓存时间 1 小时
    """
    try:
        data = await adapter.get_stock_report_fund_hold_detail(
            symbol=symbol,
            date=date
        )
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
