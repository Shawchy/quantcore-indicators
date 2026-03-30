from fastapi import APIRouter, Query, Depends
from app.models.schemas import ResponseModel, KLineData, StockBasic, TechnicalIndicator
from app.services import stock_service
from app.services.smart_loader import smart_loader
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


@router.get("/list", response_model=ResponseModel[list[StockBasic]])
async def get_stock_list(
    source: str = Query("auto", description="指定数据源：auto/efinance/akshare/baostock"),
    source_priority: str = Query("", description="临时优先级列表（逗号分隔），如：efinance,akshare"),
    source_exclude: str = Query("", description="排除的数据源（逗号分隔）"),
    fallback: bool = Query(True, description="是否允许故障转移"),
):
    """
    获取股票列表（支持多数据源优先级控制）
    
    Args:
        source: 指定数据源（auto=自动选择）
        source_priority: 临时优先级列表（逗号分隔）
        source_exclude: 排除的数据源
        fallback: 是否允许故障转移
    
    Examples:
        - 默认自动：/api/v1/stock/list
        - 指定优先级：/api/v1/stock/list?source_priority=efinance,akshare
        - 排除数据源：/api/v1/stock/list?source_exclude=yfinance
        - 强制使用：/api/v1/stock/list?source=efinance&fallback=false
    """
    from app.adapters.factory import data_source_manager
    
    if source == "auto" and not source_priority and not source_exclude:
        stocks = await data_source_manager.get_stock_list(
            source_type=None,
            source_priority=None,
            source_exclude=None,
            fallback=fallback
        )
    else:
        stocks = await data_source_manager.get_stock_list(
            source_type=None if source == "auto" else source,
            source_priority=source_priority if source_priority else None,
            source_exclude=source_exclude if source_exclude else None,
            fallback=fallback
        )
    
    return ResponseModel(data=stocks)


@router.get("/{identifier}/kline", response_model=ResponseModel[dict])
async def get_kline(
    identifier: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    adjust: str = Query("qfq", description="复权类型：qfq 前复权，hfq 后复权，none 不复权"),
    period: str = Query("daily", description="K 线周期：1m/5m/15m/30m/60m/daily/weekly/monthly"),
    priority_load: bool = Query(True, description="是否启用优先加载模式"),
    source: str = Query("auto", description="指定数据源：auto/efinance/tushare/akshare"),
    source_priority: str = Query("", description="临时优先级列表（逗号分隔）"),
    source_exclude: str = Query("", description="排除的数据源（逗号分隔）"),
    fallback: bool = Query(True, description="是否允许故障转移"),
    current_user: OptionalCurrentUser = None
):
    """
    获取股票历史 K 线数据（支持多数据源优先级控制）
    
    Args:
        identifier: 股票代码或股票名称
        start_date: 开始日期 YYYY-MM-DD
        end_date: 结束日期 YYYY-MM-DD
        adjust: 复权类型
        period: K 线周期
        priority_load: 是否启用优先加载模式
        source: 指定数据源
        source_priority: 临时优先级列表
        source_exclude: 排除的数据源
        fallback: 是否允许故障转移
    
    Examples:
        - 默认自动：/api/v1/stock/600519/kline
        - 指定数据源：/api/v1/stock/600519/kline?source=efinance
        - 优先 akshare：/api/v1/stock/600519/kline?source_priority=akshare,efinance
    """
    
    # 判断是代码还是名称
    # 股票代码通常是 6 位数字（A 股）或字母（美股/港股）
    is_code = identifier.isdigit() or (len(identifier) >= 6 and identifier.replace('.', '').replace('$', '').isalnum())
    
    if is_code:
        code = identifier
        # 通过代码获取 K 线 - 使用智能加载器
        kline_data = await smart_loader.get_kline(
            code=code,
            period=period,
            start_date=start_date,
            end_date=end_date,
            use_cache=True
        )
        
        if kline_data:
            data = {
                "code": code,
                "klines": kline_data,
                "total": len(kline_data)
            }
        else:
            data = {
                "code": code,
                "klines": [],
                "total": 0
            }
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
    
    # 获取指数 K 线 - 暂时直接使用数据源管理器（指数数据量小，缓存需求低）
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
            # 获取实时行情 - 使用智能加载器（缓存 30 秒）
            quote = await smart_loader.get_quote(code, use_cache=True)
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
