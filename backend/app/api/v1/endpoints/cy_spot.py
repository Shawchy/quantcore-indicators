"""创业板实时行情 API 端点

提供创业板实时行情数据接口
"""
from typing import List
from fastapi import APIRouter, Depends

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockZhASpot
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/cy-a-spot", response_model=ResponseModel[List[StockZhASpot]])
async def get_cy_a_spot(
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取创业板实时行情数据
    
    返回所有创业板（300/301 开头）上市公司的实时行情数据（约 1400 只股票，23 个字段）：
    
    **基本信息**:
    - **serial_number**: 序号
    - **code**: 股票代码（300/301 开头）
    - **name**: 股票名称
    
    **价格信息**:
    - **latest_price**: 最新价
    - **change_pct**: 涨跌幅（%）
    - **change_amount**: 涨跌额
    - **high**: 最高价
    - **low**: 最低价
    - **open**: 今开
    - **prev_close**: 昨收
    - **amplitude**: 振幅（%）
    
    **成交信息**:
    - **volume**: 成交量（手）
    - **turnover**: 成交额（元）
    - **volume_ratio**: 量比
    - **turnover_rate**: 换手率（%）
    
    **估值指标**:
    - **pe_ratio_dynamic**: 市盈率 - 动态
    - **pb_ratio**: 市净率
    - **total_market_cap**: 总市值（元）
    - **float_market_cap**: 流通市值（元）
    
    **涨跌统计**:
    - **speed**: 涨速
    - **change_5min**: 5 分钟涨跌（%）
    - **change_60d**: 60 日涨跌幅（%）
    - **change_ytd**: 年初至今涨跌幅（%）
    
    使用场景：
    - 创业板市场行情监控
    - 创业板股票筛选和排序
    - 创业板涨跌幅排行分析
    - 创业板成交量/额排行
    - 创业板估值水平分析
    - 创业板市场活跃度监控
    - 量化策略数据源
    
    注意：
    - 数据来源：东方财富网
    - 实时更新（交易时间内）
    - 仅包含创业板股票（300/301 开头）
    - 缓存时间：3 分钟
    
    数据量：
    - 约 1400+ 只股票
    - 每只股票 23 个字段
    
    创业板特点：
    - 股票代码：300 或 301 开头
    - 涨跌幅限制：20%（新股前 5 日无限制）
    - 定位：服务成长型创新创业企业
    - 代表企业：宁德时代、迈瑞医疗、东方财富等
    
    示例应用：
    - 获取涨停股票：筛选 change_pct >= 19.8
    - 获取跌停股票：筛选 change_pct <= -19.8
    - 获取高换手股票：筛选 turnover_rate > 15
    - 获取成长股：按 change_ytd 降序排序
    """
    try:
        data = await adapter.get_stock_cy_a_spot()
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
