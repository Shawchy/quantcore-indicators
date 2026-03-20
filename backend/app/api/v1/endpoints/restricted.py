"""限售解禁 API 端点

提供限售解禁详情、解禁批次、解禁股东等接口
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import RestrictedReleaseDetail
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/restricted-detail/{code}", response_model=ResponseModel[List[RestrictedReleaseDetail]])
async def get_restricted_detail(
    code: str,
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取限售解禁详情
    
    - **code**: 股票代码
    - **unlock_date**: 解禁日期
    - **unlock_quantity**: 解禁数量（万股）
    - **unlock_ratio**: 解禁比例（%）
    - **unlock_value**: 解禁市值（万元）
    - **holder_name**: 解禁股东
    - **unlock_type**: 解禁类型
    - **sale_restriction_date**: 减持起始日
    
    使用场景：
    - 查询个股限售解禁明细
    - 分析解禁压力
    - 评估减持风险
    """
    try:
        data = await adapter.get_restricted_release_detail(code)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取限售解禁详情失败：{str(e)}",
            "data": []
        }


@router.get("/restricted-queue", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_restricted_queue(
    start_date: Optional[str] = Query(
        None,
        description="开始日期，格式 YYYY-MM-DD"
    ),
    end_date: Optional[str] = Query(
        None,
        description="结束日期，格式 YYYY-MM-DD"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取限售解禁批次
    
    返回数据字段：
    - **code**: 股票代码
    - **name**: 股票名称
    - **unlock_date**: 解禁日期
    - **unlock_quantity**: 解禁数量（万股）
    - **unlock_ratio**: 解禁比例（%）
    - **unlock_value**: 解禁市值（万元）
    - **holder_count**: 解禁股东数量
    
    使用场景：
    - 查询特定时间段的解禁批次
    - 识别解禁高峰期
    - 市场流动性压力分析
    """
    try:
        data = await adapter.get_restricted_release_queue(start_date, end_date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取限售解禁批次失败：{str(e)}",
            "data": []
        }


@router.get("/restricted-stockholder/{code}", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_restricted_stockholder(
    code: str,
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取解禁股东
    
    返回数据字段：
    - **holder_name**: 股东名称
    - **unlock_date**: 解禁日期
    - **unlock_quantity**: 解禁数量（万股）
    - **unlock_ratio**: 占总股本比例（%）
    - **hold_ratio**: 持股比例（%）
    - **holder_type**: 股东类型
    
    使用场景：
    - 分析解禁股东结构
    - 识别重要股东减持风险
    - 评估解禁对市场的影响
    """
    try:
        data = await adapter.get_restricted_release_stockholder(code)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取解禁股东失败：{str(e)}",
            "data": []
        }
