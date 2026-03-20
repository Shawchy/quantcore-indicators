"""美股历史行情数据 API 端点

提供美股历史行情数据接口（支持日/周/月频率，不复权/前复权/后复权）
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import StockZhAHist
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/us-hist", response_model=ResponseModel[List[StockZhAHist]])
async def get_us_hist(
    symbol: str = Query(..., description="美股代码（如 '106.TTE'）"),
    period: str = Query("daily", description="周期：daily/weekly/monthly"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYYMMDD 格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYYMMDD 格式）"),
    adjust: str = Query("", description="复权类型：''=不复权，'qfq'=前复权，'hfq'=后复权"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取美股历史行情数据
    
    返回指定美股上市公司的历史行情数据（11 个字段）：
    
    **基本信息**:
    - **date**: 交易日
    - **code**: 股票代码
    
    **价格信息** (美元):
    - **open**: 开盘价
    - **close**: 收盘价
    - **high**: 最高价
    - **low**: 最低价
    
    **成交信息**:
    - **volume**: 成交量（股）
    - **turnover**: 成交额（美元）
    - **amplitude**: 振幅（%）
    - **turnover_rate**: 换手率（%）
    
    **涨跌统计** (美元):
    - **change_pct**: 涨跌幅（%）
    - **change_amount**: 涨跌额
    
    **参数说明**:
    
    **symbol** - 美股代码格式:
    - 通过 `ak.stock_us_spot_em()` 获取所有美股代码
    - 格式示例：`106.TTE`、`AAPL`、`TSLA`
    
    **period** - 周期选择:
    - `daily`: 日线数据（默认）
    - `weekly`: 周线数据
    - `monthly`: 月线数据
    
    **adjust** - 复权类型:
    - `""` (空字符串): 不复权（默认）
    - `"qfq"`: 前复权
    - `"hfq"`: 后复权（**量化研究推荐**）
    
    **使用场景**:
    - 美股历史走势分析
    - 技术指标计算
    - 量化策略回测
    - 收益率计算
    - 波动率分析
    - 中概股研究
    
    **注意**:
    - 数据来源：东方财富网
    - 成交量单位：股（非手）
    - 货币单位：美元
    - 缓存时间：1 小时
    - 复权参数对部分美股可能不生效
    
    **示例应用**:
    
    1. **获取美股日线数据**:
       ```
       GET /api/v1/stock-global/us-hist?symbol=AAPL&period=daily
       ```
    
    2. **获取特斯拉后复权数据**:
       ```
       GET /api/v1/stock-global/us-hist?symbol=TSLA&adjust=hfq
       ```
    
    3. **获取中概股数据**:
       ```
       GET /api/v1/stock-global/us-hist?symbol=BABA&start_date=20230101
       ```
    
    4. **获取周线数据**:
       ```
       GET /api/v1/stock-global/us-hist?symbol=NVDA&period=weekly
       ```
    """
    try:
        data = await adapter.get_stock_us_hist(
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
            "message": f"获取美股历史行情失败：{str(e)}",
            "data": []
        }
