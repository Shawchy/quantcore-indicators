"""筹码分布 API 端点

提供筹码分布数据接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import ChipDistribution
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/chip-distribution/{code}", response_model=ResponseModel[List[ChipDistribution]])
async def get_chip_distribution(
    code: str,
    adjust: Optional[str] = Query(
        "",
        description="复权类型，choice of {'qfq': '前复权', 'hfq': '后复权', '': '不复权'}"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取筹码分布数据
    
    - **code**: 股票代码
    - **date**: 日期
    - **profit_ratio**: 获利比例（%）
    - **avg_cost**: 平均成本
    - **cost_90_low**: 90 成本 - 低
    - **cost_90_high**: 90 成本 - 高
    - **concentration_90**: 90 集中度
    - **cost_70_low**: 70 成本 - 低
    - **cost_70_high**: 70 成本 - 高
    - **concentration_70**: 70 集中度
    
    使用场景：
    - 分析筹码集中度，判断主力控盘程度
    - 通过获利比例判断市场情绪
    - 识别筹码峰，判断支撑位和压力位
    - 配合 K 线进行技术分析
    
    数据说明：
    - 获利比例：当前股价下，获利筹码所占的比例
    - 平均成本：所有持仓筹码的平均成本价
    - 90 集中度：90% 筹码的成本集中程度，数值越小越集中
    - 70 集中度：70% 筹码的成本集中程度，数值越小越集中
    
    示例：
    - 获利比例 > 90%：大部分筹码获利，可能存在抛压
    - 获利比例 < 10%：大部分筹码被套，可能存在反弹
    - 集中度 < 10%：筹码高度集中，主力控盘度高
    """
    try:
        data = await adapter.get_chip_distribution(code, adjust)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取筹码分布数据失败：{str(e)}",
            "data": []
        }
