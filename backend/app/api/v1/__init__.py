from fastapi import APIRouter
from app.api.v1.endpoints import (
    stock, sector, chip, screener, strategy, backtest, watchlist, auth, market, realtime, moneyflow, data_source_control
)

api_router = APIRouter()

# 认证端点 (不需要认证)
api_router.include_router(auth.router, tags=["认证"])

# 业务端点 (需要认证)
api_router.include_router(stock.router, prefix="/stock", tags=["个股信息"])
api_router.include_router(sector.router, prefix="/sector", tags=["板块分析"])
api_router.include_router(chip.router, prefix="/chip", tags=["筹码选股"])
api_router.include_router(screener.router, tags=["选股筛选"])
api_router.include_router(strategy.router, tags=["策略管理"])
api_router.include_router(backtest.router, tags=["回测系统"])
api_router.include_router(watchlist.router, tags=["自选股"])
api_router.include_router(market.router, tags=["市场行情"])
api_router.include_router(realtime.router, tags=["实时盘口"])
api_router.include_router(moneyflow.router, prefix="/moneyflow", tags=["资金流向"])
api_router.include_router(data_source_control.router, prefix="/data-source", tags=["数据源控制"])
