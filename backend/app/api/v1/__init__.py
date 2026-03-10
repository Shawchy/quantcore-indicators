from fastapi import APIRouter
from app.api.v1.endpoints import stock, sector, chip, screener, strategy, backtest, watchlist

api_router = APIRouter()

api_router.include_router(stock.router, prefix="/stock", tags=["个股信息"])
api_router.include_router(sector.router, prefix="/sector", tags=["板块分析"])
api_router.include_router(chip.router, prefix="/chip", tags=["筹码选股"])
api_router.include_router(screener.router, prefix="/screener", tags=["选股筛选"])
api_router.include_router(strategy.router, prefix="/strategy", tags=["策略管理"])
api_router.include_router(backtest.router, prefix="/backtest", tags=["回测系统"])
api_router.include_router(watchlist.router, prefix="/watchlist", tags=["自选股"])
