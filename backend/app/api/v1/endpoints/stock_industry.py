"""行业分类数据 API 端点

提供巨潮资讯行业分类数据和上市公司行业归属变动数据接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockIndustryCategoryCNINFO, StockIndustryChangeCNINFO
from app.models.schemas import SWIndexFirst, SWIndexSecond, SWIndexThird, SWIndexThirdCons
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


# ========== 申万行业信息 ==========

@router.get("/sw-index-first", response_model=ResponseModel[List[SWIndexFirst]])
async def get_sw_index_first(
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取申万一级行业信息
    
    返回申万一级行业的估值指标（7 个字段）：
    - 行业信息：行业代码、行业名称
    - 估值指标：成份个数、静态市盈率、TTM 市盈率、市净率、静态股息率
    
    适用于：
    - 行业估值分析
    - 行业横向对比
    - 投资策略制定
    """
    try:
        data = await adapter.get_sw_index_first_info()
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取申万一级行业信息失败：{str(e)}",
            "data": []
        }


@router.get("/sw-index-second", response_model=ResponseModel[List[SWIndexSecond]])
async def get_sw_index_second(
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取申万二级行业信息
    
    返回申万二级行业的估值指标（8 个字段）：
    - 行业信息：行业代码、行业名称、上级行业
    - 估值指标：成份个数、静态市盈率、TTM 市盈率、市净率、静态股息率
    
    适用于：
    - 行业细分领域分析
    - 产业链研究
    - 行业轮动策略
    """
    try:
        data = await adapter.get_sw_index_second_info()
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取申万二级行业信息失败：{str(e)}",
            "data": []
        }


@router.get("/sw-index-third", response_model=ResponseModel[List[SWIndexThird]])
async def get_sw_index_third(
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取申万三级行业信息
    
    返回申万三级行业的估值指标（8 个字段）：
    - 行业信息：行业代码、行业名称、上级行业
    - 估值指标：成份个数、静态市盈率、TTM 市盈率、市净率、静态股息率
    
    适用于：
    - 最细分行业分析
    - 精准投资定位
    - 行业深度研究
    """
    try:
        data = await adapter.get_sw_index_third_info()
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取申万三级行业信息失败：{str(e)}",
            "data": []
        }


@router.get("/sw-index-third-cons/{symbol}", response_model=ResponseModel[List[SWIndexThirdCons]])
async def get_sw_index_third_cons(
    symbol: str,
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取申万三级行业成份数据
    
    返回指定申万三级行业的所有成份股数据（18 个字段）：
    - 基本信息：序号、股票代码、股票简称、纳入时间
    - 行业分类：申万 1 级、申万 2 级、申万 3 级
    - 估值指标：价格、市盈率、市盈率 TTM、市净率、股息率、市值（亿元）
    - 业绩增长：归母净利润同比增长 (09-30/06-30)、营业收入同比增长 (09-30/06-30)
    
    Args:
        symbol: 行业代码（如 "850111.SI"），可通过 /sw-index-third 接口获取
        
    适用于：
    - 行业成份股分析
    - 产业链上下游研究
    - 行业 ETF 成分股追踪
    """
    try:
        data = await adapter.get_sw_index_third_cons(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取申万三级行业成份失败：{str(e)}",
            "data": []
        }
