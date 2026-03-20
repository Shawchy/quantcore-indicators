"""地区交易排序 API 端点

提供深圳证券交易所地区交易排序数据接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import SZSEAreaSummary
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/szse-area-summary", response_model=ResponseModel[List[SZSEAreaSummary]])
async def get_szse_area_summary(
    date: str = Query(
        ...,
        description="年月，格式 YYYYMM（如：202412）"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取深圳证券交易所地区交易排序
    
    返回数据字段：
    - **rank**: 序号（排名）
    - **region**: 地区名称
    - **total_turnover**: 总交易额（元）
    - **market_ratio**: 占市场比例（%）
    - **stock_turnover**: 股票交易额（元）
    - **fund_turnover**: 基金交易额（元）
    - **bond_turnover**: 债券交易额（元）
    - **preferred_stock_turnover**: 优先股交易额（元）- 2025 年新增
    - **option_turnover**: 期权交易额（元）- 2025 年新增
    
    数据说明：
    - **总交易额**: 该地区在深交所的所有证券交易总额
    - **占市场比例**: 该地区交易额占整个深交所市场的百分比
    - **股票交易额**: 股票类证券的交易额
    - **基金交易额**: 基金类证券的交易额
    - **债券交易额**: 债券类证券的交易额
    - **优先股交易额**: 优先股交易额（2025 年 8 月起新增）
    - **期权交易额**: 期权交易额（2025 年 8 月起新增）
    
    使用场景：
    - 分析各地区投资活跃度
    - 识别主要交易地区分布
    - 对比不同地区投资偏好
    - 追踪区域经济活力
    - 分析金融产品地区渗透率
    
    注意：
    - 日期格式：YYYYMM（如：202412）
    - 数据按月统计
    - 2025 年 8 月起增加优先股和期权交易额字段
    
    示例：
    - date="202412": 获取 2024 年 12 月数据
    - date="202508": 获取 2025 年 8 月数据（包含优先股和期权）
    """
    try:
        data = await adapter.get_szse_area_summary(date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取地区交易排序失败：{str(e)}",
            "data": []
        }
