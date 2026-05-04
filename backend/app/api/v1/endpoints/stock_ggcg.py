"""股东增减持数据 API 端点

提供东方财富股东增减持数据接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockGgcgEM
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/ggcg", response_model=ResponseModel[List[StockGgcgEM]])
async def get_ggcg(
    symbol: str = Query(
        "全部", 
        description="增减持类型",
        enum=["全部", "股东增持", "股东减持"]
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取股东增减持数据
    
    返回所有股东增减持记录（16 个字段）：
    - 股票信息：代码、名称、最新价、涨跌幅
    - 股东信息：股东名称
    - 变动信息：增减类型（增持/减持）、变动数量（万股）、占总股本比例（%）、占流通股比例（%）
    - 变动后持股：持股总数（万股）、占总股本比例（%）、持流通股数（万股）、占流通股比例（%）
    - 日期信息：变动开始日、变动截止日、公告日
    
    增减持类型：
    - 全部：所有增减持记录
    - 股东增持：仅包含增持记录
    - 股东减持：仅包含减持记录
    
    注意：
    - 数据量较大（超过 10 万条），建议使用筛选条件
    - 缓存时间为 5 分钟，以保证数据及时性
    """
    try:
        data = await adapter.get_stock_ggcg_em(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
