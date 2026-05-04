"""东方财富 - 盘前分钟数据 API 端点

提供包含盘前数据的股票分钟行情数据接口
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockZhAHistPreMinEM
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/pre-min", response_model=ResponseModel[List[StockZhAHistPreMinEM]])
async def get_pre_min(
    symbol: str = Query(..., description="股票代码（如 '000001'）- 不带市场前缀"),
    start_time: str = Query("09:00:00", description="开始时间（HH:MM:SS），默认 09:00:00"),
    end_time: str = Query("15:40:00", description="结束时间（HH:MM:SS），默认 15:40:00"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富盘前分钟数据
    
    返回指定股票最近一个交易日的分钟数据（8 个字段），包含盘前和盘中数据：
    
    **数据字段**:
    - **time**: 时间（精确到分钟）
    - **open**: 开盘价
    - **close**: 收盘价
    - **high**: 最高价
    - **low**: 最低价
    - **volume**: 成交量（手）
    - **turnover**: 成交额
    - **latest_price**: 最新价
    
    **数据范围**:
    - **盘前数据**：09:15-09:25（集合竞价）
    - **盘中数据**：09:30-15:00（连续竞价）
    - 默认返回 09:00:00 - 15:40:00 的所有数据
    
    **时间参数**:
    - **start_time**: 开始时间（格式 HH:MM:SS）
      - 默认：`09:00:00`
      - 建议：`09:15:00`（包含集合竞价）
    - **end_time**: 结束时间（格式 HH:MM:SS）
      - 默认：`15:40:00`
      - 建议：`15:00:00`（收盘时间）
    
    **使用场景**:
    - 集合竞价分析（09:15-09:25）
    - 盘前走势监控
    - 开盘价格发现
    - 盘中分钟级走势分析
    - 量价关系研究
    - 日内交易策略
    
    **注意**:
    - 数据来源：东方财富网
    - 仅返回最近一个交易日数据
    - 缓存时间：5 分钟
    - 成交量单位：手
    - 股票代码不带市场前缀
    
    **数据量**:
    - 盘前（09:15-09:25）：约 10 条
    - 盘中（09:30-15:00）：约 240 条
    - 总计：约 250-260 条
    
    **集合竞价时间段说明**:
    - **09:15-09:20**：可撤单集合竞价
    - **09:20-09:25**：不可撤单集合竞价
    - **09:25-09:30**：集合竞价撮合期（不显示）
    - **09:30**：连续竞价开始
    
    **示例应用**:
    
    1. **获取全部数据**（默认）:
       ```
       GET /api/v1/stock-pre-min/pre-min?symbol=000001
       ```
    
    2. **仅获取集合竞价数据**:
       ```
       GET /api/v1/stock-pre-min/pre-min?symbol=000001&start_time=09:15:00&end_time=09:25:00
       ```
    
    3. **获取盘前 + 开盘数据**:
       ```
       GET /api/v1/stock-pre-min/pre-min?symbol=000001&start_time=09:15:00&end_time=09:35:00
       ```
    
    4. **仅获取盘中数据**:
       ```
       GET /api/v1/stock-pre-min/pre-min?symbol=000001&start_time=09:30:00&end_time=15:00:00
       ```
    
    5. **获取尾盘数据**:
       ```
       GET /api/v1/stock-pre-min/pre-min?symbol=000001&start_time=14:30:00&end_time=15:00:00
       ```
    
    **分析应用**:
    
    1. **集合竞价分析**:
       - 观察 09:15-09:25 的价格变化
       - 分析集合竞价成交量
       - 判断开盘强弱
    
    2. **盘前走势分析**:
       - 对比前一日收盘价
       - 分析盘前价格趋势
       - 预测开盘走势
    
    3. **开盘分析**:
       - 观察 09:30 开盘后的价格变化
       - 分析开盘成交量
       - 判断主力意图
    
    4. **分钟级技术分析**:
       - 计算分钟级均线
       - 分析分钟级量价关系
       - 构建分钟级技术指标
    
    **与相关接口区别**:
    - **stock_intraday_em**: 逐笔成交数据，约 4400 条/日
    - **stock_minute/em-minute**: 分时数据（1/5/15/30/60 分钟），可获取历史
    - **pre-min**: 1 分钟数据，含盘前，仅最近 1 日，约 250 条
    """
    try:
        data = await adapter.get_stock_zh_a_hist_pre_min_em(
            symbol=symbol,
            start_time=start_time,
            end_time=end_time
        )
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail="服务器内部错误")
