"""东方财富 - 历史行情数据 API 端点

提供沪深京 A 股历史行情数据接口（支持日/周/月频率，不复权/前复权/后复权）
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


@router.get("/zh-a-hist", response_model=ResponseModel[List[StockZhAHist]])
async def get_zh_a_hist(
    symbol: str = Query(..., description="股票代码（如 '000001'）"),
    period: str = Query("daily", description="周期：daily/weekly/monthly"),
    start_date: Optional[str] = Query(None, description="开始日期（YYYYMMDD 格式）"),
    end_date: Optional[str] = Query(None, description="结束日期（YYYYMMDD 格式）"),
    adjust: str = Query("", description="复权类型：''=不复权，'qfq'=前复权，'hfq'=后复权"),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取沪深京 A 股历史行情数据
    
    返回指定沪深京 A 股上市公司的历史行情数据（12 个字段）：
    
    **基本信息**:
    - **date**: 交易日
    - **code**: 股票代码
    
    **价格信息**:
    - **open**: 开盘价
    - **close**: 收盘价
    - **high**: 最高价
    - **low**: 最低价
    
    **成交信息**:
    - **volume**: 成交量（手）
    - **turnover**: 成交额（元）
    - **amplitude**: 振幅（%）
    - **turnover_rate**: 换手率（%）
    
    **涨跌统计**:
    - **change_pct**: 涨跌幅（%）
    - **change_amount**: 涨跌额（元）
    
    **参数说明**:
    
    **period** - 周期选择:
    - `daily`: 日线数据（默认）
    - `weekly`: 周线数据
    - `monthly`: 月线数据
    
    **adjust** - 复权类型:
    - `""` (空字符串): 不复权（默认）
    - `"qfq"`: 前复权 - 保持当前价格不变，调整历史价格
    - `"hfq"`: 后复权 - 保持历史价格不变，调整当前价格（**量化研究推荐**）
    
    **为何要复权**:
    由于股票存在配股、分拆、合并和发放股息等事件，会导致股价出现较大的缺口。
    若使用不复权的价格处理数据、计算各种指标，将会导致它们失去连续性。
    
    **前复权 vs 后复权**:
    - **前复权**: 用来看盘方便，能一眼看出股价的历史走势，是行情软件默认的复权方式
      - 缺点 1: 历史价格时变（每次除权除息需重新调整）
      - 缺点 2: 对于有持续分红的公司，前复权价可能出现负值
    - **后复权**: 保证历史价格不变，在权益事件发生后调整当前价格
      - 优点：可被看作投资者的长期财富增长曲线，反映真实收益率
      - **量化投资研究普遍采用后复权数据**
    
    **使用场景**:
    - 股票历史走势分析
    - 技术指标计算（MA、MACD、KDJ 等）
    - 量化策略回测
    - 收益率计算
    - 波动率分析
    - 量价关系研究
    - 趋势分析
    
    **注意**:
    - 数据来源：东方财富网
    - 历史数据按日频率更新
    - 当日收盘价请在收盘后获取
    - 缓存时间：1 小时（历史数据变化少）
    - 股票代码可在 `/api/v1/stock-spot/zh-a-spot` 接口获取
    
    **数据量**:
    - 单只股票全部历史数据（或指定日期范围）
    - 每只股票 12 个字段
    - 日线数据：通常 2000-3000 条（取决于上市时间）
    
    **示例应用**:
    
    1. **获取不复权日线数据**:
       ```
       GET /api/v1/stock-hist/zh-a-hist?symbol=000001
       ```
    
    2. **获取前复权日线数据**:
       ```
       GET /api/v1/stock-hist/zh-a-hist?symbol=000001&adjust=qfq
       ```
    
    3. **获取后复权日线数据（量化推荐）**:
       ```
       GET /api/v1/stock-hist/zh-a-hist?symbol=000001&adjust=hfq
       ```
    
    4. **获取指定日期范围**:
       ```
       GET /api/v1/stock-hist/zh-a-hist?symbol=000001&start_date=20230101&end_date=20231231
       ```
    
    5. **获取周线数据**:
       ```
       GET /api/v1/stock-hist/zh-a-hist?symbol=000001&period=weekly&adjust=hfq
       ```
    
    6. **获取月线数据**:
       ```
       GET /api/v1/stock-hist/zh-a-hist?symbol=000001&period=monthly&adjust=hfq
       ```
    
    **量化策略建议**:
    - 回测使用：后复权数据（hfq）
    - 技术分析：前复权数据（qfq）或不复权
    - 长期投资分析：后复权数据（真实收益率曲线）
    - 短线交易：不复权数据（真实交易价格）
    """
    try:
        data = await adapter.get_stock_zh_a_hist(
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
        raise HTTPException(status_code=500, detail="服务器内部错误")
