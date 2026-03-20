"""沪深京 A 股分时数据 API 端点

提供新浪财经和东方财富的分时数据接口（支持 1/5/15/30/60 分钟频率）
"""
from typing import List, Optional, Literal
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockZhAMinuteSina, StockZhAMinuteEM
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/sina-minute", response_model=ResponseModel[List[StockZhAMinuteSina]])
async def get_sina_minute(
    symbol: str = Query(..., description="股票代码（如 'sh600751'）- 需要带市场前缀"),
    period: str = Query("1", description="周期：1/5/15/30/60 分钟"),
    adjust: str = Query("", description="复权类型：''=不复权，'qfq'=前复权，'hfq'=后复权"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取新浪财经分时数据
    
    返回指定沪深京 A 股上市公司或指数的分时数据（7 个字段）：
    
    **基本信息**:
    - **day**: 时间（精确到分钟）
    - **open**: 开盘价
    - **high**: 最高价
    - **low**: 最低价
    - **close**: 收盘价
    - **volume**: 成交量
    - **amount**: 成交额
    
    **参数说明**:
    
    **symbol** - 股票代码格式:
    - 沪市股票：`sh` + 6 位代码（如 `sh600751`）
    - 深市股票：`sz` + 6 位代码（如 `sz000001`）
    - 指数：`sh`/`sz` + 指数代码（如 `sh000300`）
    
    **period** - 周期选择:
    - `1`: 1 分钟线
    - `5`: 5 分钟线
    - `15`: 15 分钟线
    - `30`: 30 分钟线
    - `60`: 60 分钟线
    
    **adjust** - 复权类型:
    - `""` (空字符串): 不复权（默认）
    - `"qfq"`: 前复权
    - `"hfq"`: 后复权
    
    **使用场景**:
    - 日内交易分析
    - 分时走势监控
    - 短期趋势判断
    - 量价关系分析
    - 高频策略研究
    
    **注意**:
    - 数据来源：新浪财经
    - 返回最近交易日的分时数据
    - 缓存时间：5 分钟
    - 注意调用频率
    
    **数据量**:
    - 1 分钟线：约 240 条/交易日
    - 5 分钟线：约 48 条/交易日
    - 15 分钟线：约 16 条/交易日
    - 30 分钟线：约 8 条/交易日
    - 60 分钟线：约 4 条/交易日
    
    **示例应用**:
    
    1. **获取 1 分钟不复权数据**:
       ```
       GET /api/v1/stock-minute/sina-minute?symbol=sh600751&period=1
       ```
    
    2. **获取 5 分钟前复权数据**:
       ```
       GET /api/v1/stock-minute/sina-minute?symbol=sh600751&period=5&adjust=qfq
       ```
    
    3. **获取沪深 300 指数分时数据**:
       ```
       GET /api/v1/stock-minute/sina-minute?symbol=sh000300&period=5
       ```
    
    4. **获取 60 分钟线**:
       ```
       GET /api/v1/stock-minute/sina-minute?symbol=sz000001&period=60&adjust=hfq
       ```
    """
    try:
        data = await adapter.get_stock_zh_a_minute_sina(
            symbol=symbol,
            period=period,
            adjust=adjust
        )
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取新浪财经分时数据失败：{str(e)}",
            "data": []
        }


@router.get("/em-minute", response_model=ResponseModel[List[StockZhAMinuteEM]])
async def get_em_minute(
    symbol: str = Query(..., description="股票代码（如 '000001'）- 不带市场前缀"),
    period: str = Query("5", description="周期：1/5/15/30/60 分钟"),
    start_date: Optional[str] = Query(None, description="开始日期时间（YYYY-MM-DD HH:MM:SS）"),
    end_date: Optional[str] = Query(None, description="结束日期时间（YYYY-MM-DD HH:MM:SS）"),
    adjust: str = Query("", description="复权类型：''=不复权，'qfq'=前复权，'hfq'=后复权"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取东方财富分时数据
    
    返回指定沪深京 A 股上市公司的分时数据：
    
    **1 分钟数据字段** (8 个):
    - **time**: 时间
    - **open**: 开盘价
    - **close**: 收盘价
    - **high**: 最高价
    - **low**: 最低价
    - **volume**: 成交量（手）
    - **turnover**: 成交额
    - **avg_price**: 均价 ⭐
    
    **5/15/30/60 分钟数据字段** (11 个):
    - **time**: 时间
    - **open**: 开盘价
    - **close**: 收盘价
    - **high**: 最高价
    - **low**: 最低价
    - **volume**: 成交量（手）
    - **turnover**: 成交额
    - **change_pct**: 涨跌幅（%）⭐
    - **change_amount**: 涨跌额 ⭐
    - **amplitude**: 振幅（%）⭐
    - **turnover_rate**: 换手率（%）⭐
    
    **参数说明**:
    
    **symbol** - 股票代码格式:
    - 6 位数字代码（如 `000001`）- **不带市场前缀**
    
    **period** - 周期选择:
    - `1`: 1 分钟线（只返回近 5 个交易日数据且不复权）
    - `5`: 5 分钟线（默认）
    - `15`: 15 分钟线
    - `30`: 30 分钟线
    - `60`: 60 分钟线
    
    **adjust** - 复权类型:
    - `""` (空字符串): 不复权（默认）
    - `"qfq"`: 前复权
    - `"hfq"`: 后复权
    - **注意**：1 分钟数据不复权
    
    **start_date / end_date**:
    - 格式：`YYYY-MM-DD HH:MM:SS`
    - 默认：返回所有数据
    - 示例：`2024-03-20 09:30:00`
    
    **使用场景**:
    - 日内交易分析
    - 分时走势监控
    - 短期趋势判断
    - 量价关系分析
    - 高频策略研究
    - 资金流向分析
    
    **注意**:
    - 数据来源：东方财富网
    - 1 分钟数据只返回近 5 个交易日数据且不复权
    - 缓存时间：5 分钟
    - 该接口只能获取近期的分时数据
    
    **数据量**:
    - 1 分钟线：约 240 条/交易日（仅近 5 日）
    - 5 分钟线：约 48 条/交易日
    - 15 分钟线：约 16 条/交易日
    - 30 分钟线：约 8 条/交易日
    - 60 分钟线：约 4 条/交易日
    
    **示例应用**:
    
    1. **获取 5 分钟不复权数据**:
       ```
       GET /api/v1/stock-minute/em-minute?symbol=000001&period=5
       ```
    
    2. **获取 1 分钟数据（近 5 日）**:
       ```
       GET /api/v1/stock-minute/em-minute?symbol=000001&period=1
       ```
    
    3. **获取 15 分钟后复权数据**:
       ```
       GET /api/v1/stock-minute/em-minute?symbol=000001&period=15&adjust=hfq
       ```
    
    4. **获取指定时间段**:
       ```
       GET /api/v1/stock-minute/em-minute?symbol=000001&period=5&start_date=2024-03-20%2009:30:00&end_date=2024-03-20%2015:00:00
       ```
    
    5. **获取 30 分钟前复权数据**:
       ```
       GET /api/v1/stock-minute/em-minute?symbol=000001&period=30&adjust=qfq
       ```
    
    **新浪财经 vs 东方财富**:
    - **新浪**: 需要市场前缀（sh/sz），字段较少（7 个），可获取指数数据
    - **东财**: 不需要市场前缀，字段较多（8-11 个），支持日期范围查询
    - **数据质量**: 两者基本一致，可根据需求选择
    """
    try:
        data = await adapter.get_stock_zh_a_hist_min_em(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取东方财富分时数据失败：{str(e)}",
            "data": []
        }
