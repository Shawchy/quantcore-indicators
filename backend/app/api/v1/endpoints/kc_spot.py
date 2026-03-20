"""科创板实时行情 API 端点

提供科创板实时行情数据接口
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


@router.get("/kc-a-spot", response_model=ResponseModel[List[StockZhASpot]])
async def get_kc_a_spot(
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取科创板实时行情数据
    
    返回所有科创板（688 开头）上市公司的实时行情数据（约 600 只股票，23 个字段）：
    
    **基本信息**:
    - **serial_number**: 序号
    - **code**: 股票代码（688 开头）
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
    - 科创板市场行情监控
    - 科创板股票筛选和排序
    - 科创板涨跌幅排行分析
    - 科创板成交量/额排行
    - 科创板估值水平分析
    - 科创板市场活跃度监控
    - 硬科技企业投资分析
    - 量化策略数据源
    
    注意：
    - 数据来源：东方财富网
    - 实时更新（交易时间内）
    - 仅包含科创板股票（688 开头）
    - 缓存时间：3 分钟
    
    数据量：
    - 约 600+ 只股票
    - 每只股票 23 个字段
    
    科创板特点：
    - 股票代码：688 开头
    - 涨跌幅限制：20%（新股前 5 日无限制）
    - 定位：面向世界科技前沿、面向经济主战场、面向国家重大需求
    - 重点支持：新一代信息技术、高端装备、新材料、新能源、节能环保、生物医药
    - 代表企业：中芯国际、金山办公、中微公司、传音控股等
    
    示例应用：
    - 获取涨停股票：筛选 change_pct >= 19.8
    - 获取跌停股票：筛选 change_pct <= -19.8
    - 获取高换手股票：筛选 turnover_rate > 15
    - 获取硬科技企业：按行业分类筛选
    - 获取次新股：按上市时间筛选
    
    科创板与创业板区别：
    - 科创板：688 开头，约 600 只，硬科技企业
    - 创业板：300/301 开头，约 1400 只，成长型创新创业企业
    - 两者涨跌幅限制均为 20%
    """
    try:
        data = await adapter.get_stock_kc_a_spot()
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取科创板实时行情失败：{str(e)}",
            "data": []
        }
