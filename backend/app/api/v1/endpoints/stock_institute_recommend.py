"""机构推荐数据 API 端点

提供新浪财经机构推荐池、股票评级记录和巨潮资讯投资评级数据接口
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockInstituteRecommend, StockInstituteRecommendDetail, StockRankForecastCninfo
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/institute-recommend", response_model=ResponseModel[List[StockInstituteRecommend]])
async def get_institute_recommend(
    symbol: str = Query(
        "最新投资评级", 
        description="推荐类型",
        enum=["最新投资评级", "上调评级股票", "下调评级股票", "股票综合评级", "首次评级股票", 
              "目标涨幅排名", "机构关注度", "行业关注度", "投资评级选股"]
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取新浪财经 - 机构推荐池数据
    
    返回机构推荐池数据（7 个字段）：
    - 基本信息：股票代码、股票名称
    - 评级信息：最新评级、目标价、评级日期
    - 统计信息：综合评级、平均涨幅（%）、行业
    
    推荐类型：
    - 最新投资评级：最新的机构投资评级
    - 上调评级股票：被机构上调评级的股票
    - 下调评级股票：被机构下调评级的股票
    - 股票综合评级：综合评级排名
    - 首次评级股票：首次被评级的股票
    - 目标涨幅排名：目标涨幅排名
    - 机构关注度：机构关注度排名
    - 行业关注度：行业关注度排名
    - 投资评级选股：根据投资评级选股
    
    注意：
    - 数据量较大（上千条），建议使用筛选
    - 缓存时间 1 小时
    """
    try:
        data = await adapter.get_stock_institute_recommend(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/institute-recommend-detail", response_model=ResponseModel[List[StockInstituteRecommendDetail]])
async def get_institute_recommend_detail(
    symbol: str = Query(..., description="股票代码（如 000001）"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取新浪财经 - 股票评级记录数据
    
    返回指定股票的历史评级记录（8 个字段）：
    - 基本信息：股票代码、股票名称
    - 评级信息：目标价、最新评级、评级机构、分析师
    - 其他信息：行业、评级日期
    
    参数说明：
    - symbol：股票代码，如 "000001"（平安银行）、"002709"（天赐材料）
    
    注意：
    - 返回该股票所有历史评级记录
    - 缓存时间 1 小时
    """
    try:
        data = await adapter.get_stock_institute_recommend_detail(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/rank-forecast-cninfo", response_model=ResponseModel[List[StockRankForecastCninfo]])
async def get_rank_forecast_cninfo(
    date: str = Query(..., description="交易日（格式：YYYYMMDD，如 20230817）"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取巨潮资讯 - 投资评级数据
    
    返回指定交易日的投资评级数据（11 个字段）：
    - 基本信息：证券代码、证券简称
    - 发布信息：发布日期、研究机构简称、研究员名称
    - 评级信息：投资评级、是否首次评级、评级变化、前一次投资评级
    - 目标价：目标价格 - 下限、目标价格 - 上限
    
    参数说明：
    - date：交易日，格式 YYYYMMDD，如 "20230817"
    
    注意：
    - 数据量根据交易日而定（数百条）
    - 缓存时间 1 小时
    """
    try:
        data = await adapter.get_stock_rank_forecast_cninfo(date=date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
