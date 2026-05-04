"""股票市场总貌 API 端点

提供上海证券交易所和深圳证券交易所的市场总貌数据接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from datetime import datetime

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import SSESummary, SZSESummary
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/sse-summary", response_model=ResponseModel[List[SSESummary]])
async def get_sse_summary(
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取上海证券交易所股票数据总貌
    
    返回数据项目：
    - **流通股本**: 流通股本总计（百万股）
    - **总市值**: 总市值（亿元）
    - **平均市盈率**: 平均市盈率
    - **上市公司**: 上市公司数量
    - **上市股票**: 上市股票数量
    - **流通市值**: 流通市值（亿元）
    - **报告时间**: 统计报告时间
    - **总股本**: 总股本（百万股）
    
    数据分类：
    - **股票**: 总计
    - **科创板**: 科创板数据
    - **主板**: 主板数据
    
    使用场景：
    - 分析上交所整体市场规模
    - 对比科创板和主板发展情况
    - 监控市场估值水平（平均市盈率）
    - 追踪 IPO 节奏（上市公司数量）
    
    注意：
    - 当前交易日的数据需要交易所收盘后统计
    - 返回最近交易日的统计数据
    """
    try:
        data = await adapter.get_sse_summary()
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")


@router.get("/szse-summary", response_model=ResponseModel[List[SZSESummary]])
async def get_szse_summary(
    date: Optional[str] = Query(
        None,
        description="日期，格式 YYYYMMDD，默认为最近交易日"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取深圳证券交易所市场总貌-证券类别统计
    
    证券类别：
    - **股票**: 股票总计
    - **主板 A 股**: 主板 A 股
    - **主板 B 股**: 主板 B 股
    - **中小板**: 中小板股票
    - **创业板 A 股**: 创业板股票
    - **基金**: 基金总计
    - **ETF**: 交易型开放式指数基金
    - **LOF**: 上市型开放式基金
    - **封闭式基金**: 封闭式基金
    - **分级基金**: 分级基金
    - **债券**: 债券总计
    - **债券现券**: 债券现券
    - **债券回购**: 债券回购
    - **ABS**: 资产支持证券
    - **期权**: 期权
    
    返回字段：
    - **category**: 证券类别
    - **count**: 数量（只）
    - **turnover_amount**: 成交金额（元）
    - **total_market_cap**: 总市值
    - **float_market_cap**: 流通市值
    
    使用场景：
    - 分析深交所各类证券市场规模
    - 对比不同板块发展情况
    - 监控市场活跃度（成交金额）
    - 追踪市场扩容（证券数量）
    
    注意：
    - 当前交易日的数据需要交易所收盘后统计
    - 日期格式：YYYYMMDD（如：20240119）
    """
    try:
        # 如果没有提供日期，使用最近交易日（AKShare 会自动处理）
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        data = await adapter.get_szse_summary(date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
