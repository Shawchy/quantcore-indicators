from fastapi import APIRouter
from app.api.v1.endpoints import (
    stock, sector, chip, screener, strategy, backtest, watchlist, auth, market, realtime, moneyflow, 
    data_source_control, loading_progress, billboard, capital_flow, board, index, shareholder, market_quotes,
    data_source, fund
)

api_router = APIRouter()

# 认证端点 (不需要认证)
api_router.include_router(auth.router, tags=["认证"])

# 业务端点 (需要认证)
api_router.include_router(stock.router, prefix="/stock", tags=["个股信息"])
api_router.include_router(sector.router, prefix="/sector", tags=["板块分析"])
api_router.include_router(chip.router, prefix="/chip", tags=["筹码选股"])
api_router.include_router(screener.router, prefix="/screener", tags=["选股筛选"])
api_router.include_router(strategy.router, prefix="/strategy", tags=["策略管理"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["回测系统"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["自选股"])
api_router.include_router(market.router, prefix="/market", tags=["市场行情"])
api_router.include_router(realtime.router, prefix="/realtime", tags=["实时盘口"])
api_router.include_router(moneyflow.router, prefix="/moneyflow", tags=["资金流向"])
api_router.include_router(data_source_control.router, prefix="/data-source-control", tags=["数据源控制"])
api_router.include_router(data_source.router, prefix="/data-source", tags=["数据源管理"])
api_router.include_router(loading_progress.router, prefix="/loading", tags=["加载进度"])
api_router.include_router(billboard.router, prefix="/billboard", tags=["龙虎榜"])
api_router.include_router(capital_flow.router, prefix="/capital-flow", tags=["资金流向"])
api_router.include_router(board.router, prefix="/board", tags=["板块信息"])
api_router.include_router(index.router, prefix="/index", tags=["指数成分"])
api_router.include_router(shareholder.router, prefix="/shareholder", tags=["股东信息"])
api_router.include_router(market_quotes.router, prefix="/market-quotes", tags=["市场实时行情"])
api_router.include_router(fund.router, prefix="/fund", tags=["基金信息"])
