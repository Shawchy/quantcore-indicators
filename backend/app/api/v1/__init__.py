from fastapi import APIRouter
from app.api.v1.endpoints import (
    stock, sector, chip, screener, strategy, backtest, watchlist, auth
)

api_router = APIRouter()

# 认证端点 (不需要认证)
api_router.include_router(auth.router, tags=["认证"])

# 业务端点 (需要认证)
api_router.include_router(stock.router, tags=["个股信息"])
api_router.include_router(sector.router, tags=["板块分析"])
api_router.include_router(chip.router, tags=["筹码选股"])
api_router.include_router(screener.router, tags=["选股筛选"])
api_router.include_router(strategy.router, tags=["策略管理"])
api_router.include_router(backtest.router, tags=["回测系统"])
api_router.include_router(watchlist.router, tags=["自选股"])
