from fastapi import APIRouter, Query, Depends
from app.models.schemas import ResponseModel, KLineData, StockBasic, TechnicalIndicator
from app.services import stock_service
from app.api.deps import CurrentUser, OptionalCurrentUser
from typing import Optional
from loguru import logger

router = APIRouter()


@router.get("/{code}", response_model=ResponseModel[dict])
async def get_stock_basic(code: str, current_user: OptionalCurrentUser):
    data = await stock_service.get_stock_basic(code)
    return ResponseModel(data=data)


@router.get("/{code}/kline", response_model=ResponseModel[dict])
async def get_kline(
    code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    adjust: str = Query("qfq", description="复权类型：qfq 前复权，hfq 后复权，none 不复权"),
    priority_load: bool = Query(True, description="是否启用优先加载模式"),
    current_user: OptionalCurrentUser = None
):
    data = await stock_service.get_kline(code, start_date, end_date, adjust, priority_load=priority_load)
    return ResponseModel(data=data)


@router.get("/market/index", response_model=ResponseModel[dict])
async def get_market_index(
    index_code: str = Query("000001", description="指数代码：000001=上证指数，399001=深证成指，399006=创业板指"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    current_user: OptionalCurrentUser = None
):
    """获取大盘指数 K 线数据"""
    from app.adapters.factory import data_source_manager
    
    # 获取指数 K 线
    klines = await data_source_manager.get_market_index_kline(index_code, start_date, end_date)
    
    # 格式化返回
    return ResponseModel(data={
        "index_code": index_code,
        "klines": [
            {
                "date": k.date,
                "open": k.open,
                "high": k.high,
                "low": k.low,
                "close": k.close,
                "volume": k.volume,
                "amount": k.amount,
            }
            for k in klines
        ]
    })


@router.get("/market/realtime", response_model=ResponseModel[list])
async def get_market_realtime(
    index_codes: str = Query("000001,399001,399006", description="指数代码列表，逗号分隔"),
    current_user: OptionalCurrentUser = None
):
    """获取多个大盘指数的实时行情"""
    from app.adapters.factory import data_source_manager
    
    codes = [code.strip() for code in index_codes.split(",")]
    realtime_data = []
    
    for code in codes:
        try:
            # 获取实时行情
            quote = await data_source_manager.get_realtime_quote(code)
            if quote:
                realtime_data.append({
                    "code": code,
                    "name": quote.get("name", ""),
                    "price": quote.get("price", 0),
                    "change": quote.get("change", 0),
                    "change_pct": quote.get("change_pct", 0),
                    "volume": quote.get("volume", 0),
                    "amount": quote.get("amount", 0),
                    "high": quote.get("high", 0),
                    "low": quote.get("low", 0),
                    "open": quote.get("open", 0),
                    "prev_close": quote.get("prev_close", 0),
                })
        except Exception as e:
            logger.error(f"获取指数实时行情失败 {code}: {e}")
    
    return ResponseModel(data=realtime_data)


@router.get("/{code}/indicators", response_model=ResponseModel[list])
async def get_technical_indicators(
    code: str,
    current_user: CurrentUser,
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    data = await stock_service.get_technical_indicators(code, start_date, end_date)
    return ResponseModel(data=data)


@router.get("/{code}/realtime", response_model=ResponseModel[dict])
async def get_realtime_quote(code: str, current_user: CurrentUser):
    data = await stock_service.get_realtime_quote(code)
    return ResponseModel(data=data)


@router.get("/search", response_model=ResponseModel[list])
async def search_stocks(
    current_user: CurrentUser,
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(20, description="返回数量限制"),
):
    data = await stock_service.search_stocks(keyword, limit)
    return ResponseModel(data=data)


@router.get("/{code}/kline/weekly", response_model=ResponseModel[list])
async def get_weekly_kline(
    code: str,
    current_user: CurrentUser,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    adjust: str = Query("qfq", description="复权类型"),
):
    data = await stock_service.get_weekly_kline(code, start_date, end_date, adjust)
    return ResponseModel(data=data)


@router.get("/{code}/kline/monthly", response_model=ResponseModel[list])
async def get_monthly_kline(
    code: str,
    current_user: CurrentUser,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    adjust: str = Query("qfq", description="复权类型"),
):
    data = await stock_service.get_monthly_kline(code, start_date, end_date, adjust)
    return ResponseModel(data=data)


@router.get("/top-list", response_model=ResponseModel[list])
async def get_top_list(
    current_user: CurrentUser,
    trade_date: Optional[str] = Query(None, description="交易日期 YYYYMMDD"),
):
    data = await stock_service.get_top_list(trade_date)
    return ResponseModel(data=data)


@router.get("/forecast/{code}", response_model=ResponseModel[list])
async def get_forecast(
    code: str,
    current_user: CurrentUser,
    ann_date: Optional[str] = Query(None, description="公告日期"),
):
    data = await stock_service.get_forecast(code, ann_date)
    return ResponseModel(data=data)


@router.get("/moneyflow/{code}", response_model=ResponseModel[list])
async def get_moneyflow(
    code: str,
    current_user: CurrentUser,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
):
    data = await stock_service.get_moneyflow(code, start_date, end_date)
    return ResponseModel(data=data)
