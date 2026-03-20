"""行业分类数据 API 端点

提供巨潮资讯行业分类数据和上市公司行业归属变动数据接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockIndustryCategoryCNINFO, StockIndustryChangeCNINFO
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/industry-category", response_model=ResponseModel[List[StockIndustryCategoryCNINFO]])
async def get_industry_category(
    symbol: str = Query(
        ..., 
        description="行业分类标准",
        examples=["巨潮行业分类标准"],
        enum=[
            "证监会行业分类标准",
            "巨潮行业分类标准",
            "申银万国行业分类标准",
            "新财富行业分类标准",
            "国资委行业分类标准",
            "巨潮产业细分标准",
            "天相行业分类标准",
            "全球行业分类标准"
        ]
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取行业分类数据
    
    返回指定行业分类标准的完整行业分类体系（8 个字段）：
    - 类目信息：类目编码、类目名称、类目名称英文
    - 行业信息：行业类型、行业类型编码
    - 层级信息：父类编码、分级（0-4 级）
    - 其他：终止日期
    
    支持的分类标准：
    - 证监会行业分类标准：证监会发布的行业分类
    - 巨潮行业分类标准：巨潮资讯自有的行业分类
    - 申银万国行业分类标准：申万行业分类
    - 新财富行业分类标准：新财富行业分类
    - 国资委行业分类标准：国资委行业分类
    - 巨潮产业细分标准：更细分的产业分类
    - 天相行业分类标准：天相投顾行业分类
    - 全球行业分类标准：GICS 全球行业分类
    """
    try:
        data = await adapter.get_stock_industry_category_cninfo(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取行业分类数据失败：{str(e)}",
            "data": []
        }


@router.get("/industry-change", response_model=ResponseModel[List[StockIndustryChangeCNINFO]])
async def get_industry_change(
    symbol: str = Query(..., description="股票代码（如 002594）"),
    start_date: str = Query(..., description="开始日期（YYYYMMDD 格式）"),
    end_date: str = Query(..., description="结束日期（YYYYMMDD 格式）"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取上市公司行业归属的变动情况
    
    返回指定股票在指定时间范围内的行业归属变动记录（11 个字段）：
    - 公司信息：新证券简称、证券代码、机构名称
    - 行业分类：行业门类、行业大类、行业中类、行业次类
    - 分类标准：分类标准、分类标准编码、行业编码
    - 变更信息：变更日期
    
    可用于追踪上市公司行业分类的历史变化，适用于：
    - 行业分类调整分析
    - 公司业务转型追踪
    - 历史数据回测校正
    """
    try:
        data = await adapter.get_stock_industry_change_cninfo(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date
        )
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取行业归属变动数据失败：{str(e)}",
            "data": []
        }
