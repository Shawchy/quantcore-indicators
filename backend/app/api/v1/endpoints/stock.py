from fastapi import APIRouter, Query, Depends
from app.models.schemas import ResponseModel, KLineData, StockBasic, TechnicalIndicator
from app.services import stock_service
from app.api.deps import CurrentUser, OptionalCurrentUser
from typing import Optional
from loguru import logger
import asyncio
import efinance as ef

router = APIRouter()


@router.get("/{code}", response_model=ResponseModel[dict])
async def get_stock_basic(code: str, current_user: OptionalCurrentUser):
    data = await stock_service.get_stock_basic(code)
    return ResponseModel(data=data)


@router.get("/{identifier}/kline", response_model=ResponseModel[dict])
async def get_kline(
    identifier: str,  # 支持股票代码或股票名称
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    adjust: str = Query("qfq", description="复权类型：qfq 前复权，hfq 后复权，none 不复权"),
    priority_load: bool = Query(True, description="是否启用优先加载模式"),
    current_user: OptionalCurrentUser = None
):
    """
    获取股票历史日 K 线数据（支持股票代码和股票名称两种模式）
    
    Args:
        identifier: 股票代码（如：600519）或股票名称（如：贵州茅台、微软）
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        adjust: 复权类型
        priority_load: 是否启用优先加载模式
    
    Returns:
        K 线数据，包含股票基本信息和历史 K 线
        
    Examples:
        - 通过股票代码获取：/api/v1/stock/600519/kline
        - 通过股票名称获取：/api/v1/stock/贵州茅台/kline
        - 通过美股名称获取：/api/v1/stock/微软/kline
    """
    from app.services.stock_service import stock_service
    
    # 判断是代码还是名称
    # 股票代码通常是 6 位数字（A 股）或字母（美股/港股）
    is_code = identifier.isdigit() or (len(identifier) >= 6 and identifier.replace('.', '').replace('$', '').isalnum())
    
    if is_code:
        code = identifier
        # 通过代码获取 K 线
        data = await stock_service.get_kline(code, start_date, end_date, adjust, priority_load=priority_load)
    else:
        # 通过名称获取 K 线（efinance 支持直接传入股票名称）
        from app.adapters import efinance_adapter
        adapter = efinance_adapter.EFinanceAdapter()
        
        # 先通过名称获取股票代码
        try:
            # efinance 支持直接传入股票名称获取历史数据
            df = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: ef.stock.get_quote_history(identifier)
            )
            
            if df is None or df.empty:
                return ResponseModel(
                    success=False,
                    code="NOT_FOUND",
                    message=f"未找到股票：{identifier}"
                )
            
            # 从 DataFrame 中提取股票代码
            stock_code = df.iloc[0]['股票代码'] if '股票代码' in df.columns else None
            stock_name = df.iloc[0]['股票名称'] if '股票名称' in df.columns else identifier
            
            # 转换为标准 K 线格式
            klines = []
            for _, row in df.iterrows():
                klines.append({
                    "date": row.get('日期', ''),
                    "open": float(row.get('开盘', 0)),
                    "close": float(row.get('收盘', 0)),
                    "high": float(row.get('最高', 0)),
                    "low": float(row.get('最低', 0)),
                    "volume": float(row.get('成交量', 0)),
                    "amount": float(row.get('成交额', 0)),
                    "change_pct": float(row.get('涨跌幅', 0)),
                    "change": float(row.get('涨跌额', 0)),
                    "amplitude": float(row.get('振幅', 0)),
                    "turnover_rate": float(row.get('换手率', 0)),
                })
            
            data = {
                "code": stock_code,
                "name": stock_name,
                "klines": klines,
                "total": len(klines)
            }
            
            return ResponseModel(data=data)
            
        except Exception as e:
            logger.error(f"通过股票名称获取 K 线失败 {identifier}: {e}")
            return ResponseModel(
                success=False,
                code="ERROR",
                message=f"获取股票数据失败：{str(e)}"
            )
    
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
    current_user: OptionalCurrentUser,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    adjust: str = Query("qfq", description="复权类型"),
):
    data = await stock_service.get_weekly_kline(code, start_date, end_date, adjust)
    return ResponseModel(data=data)


@router.get("/{code}/kline/monthly", response_model=ResponseModel[list])
async def get_monthly_kline(
    code: str,
    current_user: OptionalCurrentUser,
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
