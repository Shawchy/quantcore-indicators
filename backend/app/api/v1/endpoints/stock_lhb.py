"""东方财富龙虎榜数据 API 端点

提供东方财富龙虎榜详情和个股上榜统计数据接口
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockLhbDetailEm, StockLhbStockStatisticEm
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/lhb-detail", response_model=ResponseModel[List[StockLhbDetailEm]])
async def get_lhb_detail(
    start_date: str = Query(..., description="开始日期（格式：YYYYMMDD，如 20230403）"),
    end_date: str = Query(..., description="结束日期（格式：YYYYMMDD，如 20230417）"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 龙虎榜详情数据
    
    返回指定日期范围内的龙虎榜详情数据（21 个字段）：
    - 基本信息：序号、代码、名称、上榜日、解读
    - 行情数据：收盘价、涨跌幅（%）
    - 龙虎榜数据：龙虎榜净买额（元）、龙虎榜买入额（元）、龙虎榜卖出额（元）、龙虎榜成交额（元）
    - 成交统计：市场总成交额（元）、净买额占总成交比（%）、成交额占总成交比（%）、换手率（%）、流通市值（元）
    - 上榜原因：上榜原因
    - 上榜后表现：上榜后 1 日（%）、上榜后 2 日（%）、上榜后 5 日（%）、上榜后 10 日（%）
    
    日期范围：
    - start_date：开始日期，格式 YYYYMMDD
    - end_date：结束日期，格式 YYYYMMDD
    
    注意：
    - 数据量根据日期范围而定
    - 缓存时间 1 小时
    """
    try:
        data = await adapter.get_stock_lhb_detail_em(
            start_date=start_date,
            end_date=end_date
        )
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/lhb-stock-statistic", response_model=ResponseModel[List[StockLhbStockStatisticEm]])
async def get_lhb_stock_statistic(
    symbol: str = Query(
        "近一月", 
        description="统计周期",
        enum=["近一月", "近三月", "近六月", "近一年"]
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富 - 个股上榜统计数据
    
    返回指定统计周期内的个股上榜统计数据（20 个字段）：
    - 基本信息：序号、代码、名称、最近上榜日
    - 行情数据：收盘价、涨跌幅
    - 上榜统计：上榜次数、龙虎榜净买额、龙虎榜买入额、龙虎榜卖出额、龙虎榜总成交额
    - 机构统计：买方机构次数、卖方机构次数、机构买入净额、机构买入总额、机构卖出总额
    - 涨跌幅统计：近 1 个月涨跌幅、近 3 个月涨跌幅、近 6 个月涨跌幅、近 1 年涨跌幅
    
    统计周期：
    - 近一月：近一个月的上榜统计
    - 近三月：近三个月的上榜统计
    - 近六月：近六个月的上榜统计
    - 近一年：近一年的上榜统计
    
    注意：
    - 数据量较大（数百条），建议使用筛选
    - 缓存时间 1 小时
    """
    try:
        data = await adapter.get_stock_lhb_stock_statistic_em(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
