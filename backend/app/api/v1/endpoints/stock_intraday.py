"""沪深京 A 股日内分时数据 API 端点

提供东方财富和新浪财经的日内分时数据接口（逐笔成交数据）
"""
from typing import List
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockIntradayEM, StockIntradaySina
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/em-intraday", response_model=ResponseModel[List[StockIntradayEM]])
async def get_em_intraday(
    symbol: str = Query(..., description="股票代码（如 '000001'）- 不带市场前缀"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富日内分时数据
    
    返回指定股票最近一个交易日的日内分时数据（4 个字段），包含盘前数据：
    
    **数据字段**:
    - **time**: 时间（从 09:15 开始，包含集合竞价）
    - **price**: 成交价
    - **volume**: 手数
    - **type**: 买卖盘性质（买盘/卖盘/中性盘）
    
    **数据特点**:
    - 包含盘前集合竞价数据（09:15-09:25）
    - 包含连续竞价数据（09:30-15:00）
    - 最近一个交易日数据
    - 数据量：约 4000-5000 条/日
    
    **使用场景**:
    - 日内交易分析
    - 逐笔成交分析
    - 盘口买卖力量分析
    - 主力行为分析
    - 集合竞价分析
    - 大单追踪
    
    **注意**:
    - 数据来源：东方财富网
    - 仅返回最近一个交易日数据
    - 缓存时间：5 分钟
    - 包含盘前集合竞价数据
    
    **买卖盘性质说明**:
    - **买盘**: 主动性买入成交
    - **卖盘**: 主动性卖出成交
    - **中性盘**: 无法明确判断买卖方向的成交
    
    **示例应用**:
    
    1. **获取最近交易日数据**:
       ```
       GET /api/v1/stock-intraday/em-intraday?symbol=000001
       ```
    
    2. **分析集合竞价** (09:15-09:25):
       - 筛选 time 在 09:15-09:25 之间的数据
       - 观察竞价期间的成交量和价格变化
    
    3. **分析主力大单**:
       - 筛选 volume >= 100 手的数据
       - 统计买盘/卖盘大单比例
    
    4. **计算主动买入比例**:
       - 统计 type='买盘' 的成交量
       - 计算买盘成交量 / 总成交量
    
    **典型数据分布**:
    - 集合竞价阶段（09:15-09:25）：约 100-200 条
    - 连续竞价阶段（09:30-15:00）：约 4000 条
    - 总计：约 4400 条左右
    """
    try:
        data = await adapter.get_stock_intraday_em(symbol=symbol)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取东方财富日内分时数据失败：{str(e)}",
            "data": []
        }


@router.get("/sina-intraday", response_model=ResponseModel[List[StockIntradaySina]])
async def get_sina_intraday(
    symbol: str = Query(..., description="股票代码（如 'sz000001'）- 需要带市场前缀"),
    date: str = Query(..., description="交易日（格式 YYYYMMDD，如 '20240321'）"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取新浪财经日内分时数据
    
    返回指定股票指定交易日的日内大单分时数据（7 个字段）：
    
    **数据字段**:
    - **symbol**: 股票代码
    - **name**: 股票名称
    - **ticktime**: 时间
    - **price**: 成交价
    - **volume**: 成交量（股）⚠️ 注意单位
    - **prev_price**: 前一笔价格
    - **kind**: 买卖盘性质
    
    **数据特点**:
    - 仅返回大单数据（成交量≥400 手）
    - 可以获取历史交易日数据
    - 数据量：约 800-1000 条/日（大单）
    - 成交量单位：股（非手）
    
    **买卖盘性质 (kind)**:
    - **U** (Up): 买盘 - 主动性买入
    - **D** (Down): 卖盘 - 主动性卖出
    - **E** (Equal): 集合竞价
    - 空值：中性盘
    
    **使用场景**:
    - 大单追踪分析
    - 主力行为分析
    - 历史交易日分析
    - 买卖盘力量对比
    - 资金流向分析
    - 龙虎榜研究
    
    **注意**:
    - 数据来源：新浪财经
    - 仅返回大单数据（≥400 手）
    - 只能获取近期数据
    - 缓存时间：1 小时
    - 成交量单位：股（非手）
    - 需要带市场前缀（sz/sh）
    
    **示例应用**:
    
    1. **获取今日大单数据**:
       ```
       GET /api/v1/stock-intraday/sina-intraday?symbol=sz000001&date=20240321
       ```
    
    2. **统计大单买卖比例**:
       - 统计 kind='U' 的大单成交量
       - 统计 kind='D' 的大单成交量
       - 计算买盘/卖盘比例
    
    3. **分析集合竞价大单**:
       - 筛选 kind='E' 的数据
       - 观察集合竞价期间的大单情况
    
    4. **追踪主力大单**:
       - 筛选 volume >= 1000000 股的数据
       - 分析大单的买卖方向和价格影响
    
    5. **对比历史大单**:
       - 获取多个交易日的大单数据
       - 分析主力行为模式
    
    **东方财富 vs 新浪财经**:
    - **东财**: 全部成交数据（含小单），仅最近 1 日，单位是手
    - **新浪**: 仅大单数据（≥400 手），可获取历史，单位是股
    - **东财**: 包含盘前数据，有买卖盘性质分类
    - **新浪**: 有股票代码和名称，有前一笔价格
    """
    try:
        data = await adapter.get_stock_intraday_sina(symbol=symbol, date=date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取新浪财经日内分时数据失败：{str(e)}",
            "data": []
        }
