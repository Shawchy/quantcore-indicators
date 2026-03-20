"""沪深京 A 股实时行情 API 端点

提供沪深京 A 股全市场实时行情数据接口
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


@router.get("/zh-a-spot", response_model=ResponseModel[List[StockZhASpot]])
async def get_zh_a_spot(
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取沪深京 A 股实时行情数据
    
    返回所有沪深京 A 股上市公司的实时行情数据（5600+ 只股票，23 个字段）：
    
    **基本信息**:
    - **serial_number**: 序号
    - **code**: 股票代码
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
    - 全市场行情监控
    - 股票筛选和排序
    - 涨跌幅排行分析
    - 成交量/额排行
    - 估值水平分析
    - 市场活跃度监控
    - 量化策略数据源
    
    注意：
    - 数据来源：东方财富网
    - 实时更新（交易时间内）
    - 包含沪深京三个交易所的所有 A 股
    - 缓存时间：3 分钟
    
    数据量：
    - 约 5600+ 只股票
    - 每只股票 23 个字段
    
    示例应用：
    - 获取涨停股票：筛选 change_pct >= 9.8
    - 获取跌停股票：筛选 change_pct <= -9.8
    - 获取高换手股票：筛选 turnover_rate > 10
    - 获取低市盈率股票：按 pe_ratio_dynamic 升序排序
    - 获取放量股票：筛选 volume_ratio > 3
    """
    try:
        data = await adapter.get_stock_zh_a_spot()
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取沪深京 A 股实时行情失败：{str(e)}",
            "data": []
        }
