"""市场情绪监控 API 端点

提供涨停股池、跌停股池、炸板股池、创新高/新低统计等接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from datetime import datetime

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import (
    LimitUpPool,
    LimitDownStock,
    BrokenLimitStock,
    HighLowStatistics
)
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/limit-up-pool", response_model=ResponseModel[List[LimitUpPool]])
async def get_limit_up_pool(
    trade_date: Optional[str] = Query(
        None,
        description="交易日期，格式 YYYYMMDD，默认为今日"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取涨停股池数据
    
    - **code**: 股票代码
    - **name**: 股票名称
    - **change_pct**: 涨跌幅
    - **latest_price**: 最新价
    - **turnover_rate**: 换手率
    - **limit_up_count**: 连板数
    - **first_limit_time**: 首次涨停时间
    - **last_limit_time**: 最后涨停时间
    - **seal_amount**: 封板资金（万元）
    - **industry**: 所属行业
    - **open_count**: 开板次数
    - **seal_ratio**: 封成比
    
    使用场景：
    - 监控市场涨停情绪
    - 识别连板龙头股
    - 分析涨停封板质量
    """
    try:
        data = await adapter.get_limit_up_pool(trade_date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取涨停股池失败：{str(e)}",
            "data": []
        }


@router.get("/limit-down-pool", response_model=ResponseModel[List[LimitDownStock]])
async def get_limit_down_pool(
    trade_date: Optional[str] = Query(
        None,
        description="交易日期，格式 YYYYMMDD，默认为今日"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取跌停股池数据
    
    - **code**: 股票代码
    - **name**: 股票名称
    - **change_pct**: 涨跌幅
    - **latest_price**: 最新价
    - **continuous_limit_down**: 连续跌停天数
    - **open_count**: 开板次数
    - **turnover_rate**: 换手率
    - **seal_amount**: 封单金额（万元）
    - **industry**: 所属行业
    
    使用场景：
    - 监控市场跌停情绪
    - 识别连续跌停风险股
    - 分析市场恐慌程度
    """
    try:
        data = await adapter.get_limit_down_pool(trade_date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取跌停股池失败：{str(e)}",
            "data": []
        }


@router.get("/broken-limit-pool", response_model=ResponseModel[List[BrokenLimitStock]])
async def get_broken_limit_pool(
    trade_date: Optional[str] = Query(
        None,
        description="交易日期，格式 YYYYMMDD，默认为今日"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取炸板股池数据
    
    - **code**: 股票代码
    - **name**: 股票名称
    - **change_pct**: 涨跌幅
    - **latest_price**: 最新价
    - **highest_price**: 最高价（涨停价）
    - **turnover_rate**: 换手率
    - **industry**: 所属行业
    - **limit_time**: 涨停时间
    
    使用场景：
    - 监控炸板风险
    - 识别弱势涨停股
    - 分析市场分歧程度
    """
    try:
        data = await adapter.get_broken_limit_pool(trade_date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取炸板股池失败：{str(e)}",
            "data": []
        }


@router.get("/high-low-statistics", response_model=ResponseModel[List[HighLowStatistics]])
async def get_high_low_statistics(
    trade_date: Optional[str] = Query(
        None,
        description="交易日期，格式 YYYYMMDD，默认为今日"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取创新高/新低统计
    
    - **date**: 统计日期
    - **index_close**: 大盘收盘点位
    - **high_20**: 创 20 日新高数量
    - **low_20**: 创 20 日新低数量
    - **high_60**: 创 60 日新高数量
    - **low_60**: 创 60 日新低数量
    - **high_120**: 创 120 日新高数量
    - **low_120**: 创 120 日新低数量
    
    使用场景：
    - 判断市场趋势强弱
    - 识别市场拐点
    - 配合大盘点位分析市场结构
    """
    try:
        data = await adapter.get_high_low_statistics(trade_date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取创新高/新低统计失败：{str(e)}",
            "data": []
        }
