from fastapi import APIRouter
from app.api.v1.endpoints import (
    stock, sector, chip, screener, strategy, backtest, watchlist, auth, market, realtime, moneyflow, 
    data_source_control, loading_progress, billboard, capital_flow, board, index, shareholder, market_quotes,
    data_source, fund, stock_info, market_sentiment, lhb, financial, restricted, changes, chip_distribution,
    market_overview, area_summary, sector_deal, stock_spot, cy_spot, kc_spot, sina_spot, stock_hist, stock_minute, stock_intraday, stock_pre_min, stock_comparison, stock_us_hist, stock_hk_hist, stock_yjbb, stock_industry, stock_financial_report, stock_ggcg, stock_fund_flow, stock_big_deal, stock_individual_fund_flow, stock_market_fund_flow, stock_sector_fund_flow_rank, stock_main_fund_flow, stock_sector_fund_flow_summary, stock_fund_flow_hist, stock_report_fund_hold, stock_lhb, stock_institute_recommend, indicators, kline, monitoring, lifecycle, backup, performance, audit
)
from app.websocket import routes as websocket_router

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
api_router.include_router(stock_info.router, prefix="/stock", tags=["个股详细信息"])
api_router.include_router(market_sentiment.router, prefix="/market-sentiment", tags=["市场情绪监控"])
api_router.include_router(lhb.router, prefix="/lhb", tags=["龙虎榜"])
api_router.include_router(financial.router, prefix="/financial", tags=["财务深度分析"])
api_router.include_router(restricted.router, prefix="/restricted", tags=["限售解禁"])
api_router.include_router(changes.router, prefix="/changes", tags=["盘口异动"])
api_router.include_router(chip_distribution.router, prefix="/chip", tags=["筹码分布"])
api_router.include_router(market_overview.router, prefix="/market-overview", tags=["股票市场总貌"])
api_router.include_router(area_summary.router, prefix="/area", tags=["地区交易排序"])
api_router.include_router(sector_deal.router, prefix="/sector-deal", tags=["行业成交与概况"])
api_router.include_router(stock_spot.router, prefix="/stock-spot", tags=["沪深京 A 股实时行情"])
api_router.include_router(cy_spot.router, prefix="/cy-spot", tags=["创业板实时行情"])
api_router.include_router(kc_spot.router, prefix="/kc-spot", tags=["科创板实时行情"])
api_router.include_router(sina_spot.router, prefix="/sina-spot", tags=["新浪财经实时行情"])
api_router.include_router(stock_hist.router, prefix="/stock-hist", tags=["历史行情数据"])
api_router.include_router(stock_minute.router, prefix="/stock-minute", tags=["分时数据"])
api_router.include_router(stock_intraday.router, prefix="/stock-intraday", tags=["日内分时数据"])
api_router.include_router(stock_pre_min.router, prefix="/stock-pre-min", tags=["盘前分钟数据"])
api_router.include_router(stock_comparison.router, prefix="/stock-comparison", tags=["同行比较"])
api_router.include_router(stock_us_hist.router, prefix="/stock-global", tags=["美股历史行情"])
api_router.include_router(stock_hk_hist.router, prefix="/stock-global", tags=["港股历史行情"])
api_router.include_router(stock_yjbb.router, prefix="/stock-yjbb", tags=["业绩报表"])
api_router.include_router(stock_industry.router, prefix="/stock-industry", tags=["行业分类数据"])
api_router.include_router(stock_financial_report.router, prefix="/stock-financial-report", tags=["财务报表"])
api_router.include_router(stock_ggcg.router, prefix="/stock-ggcg", tags=["股东增减持"])
api_router.include_router(stock_fund_flow.router, prefix="/stock-fund-flow", tags=["资金流向"])
api_router.include_router(stock_big_deal.router, prefix="/stock-big-deal", tags=["大单追踪"])
api_router.include_router(stock_individual_fund_flow.router, prefix="/stock-individual-fund-flow", tags=["东方财富个股资金流"])
api_router.include_router(stock_market_fund_flow.router, prefix="/stock-market-fund-flow", tags=["东方财富大盘资金流"])
api_router.include_router(stock_sector_fund_flow_rank.router, prefix="/stock-sector-fund-flow-rank", tags=["东方财富板块资金流"])
api_router.include_router(stock_main_fund_flow.router, prefix="/stock-main-fund-flow", tags=["东方财富主力净流入"])
api_router.include_router(stock_sector_fund_flow_summary.router, prefix="/stock-sector-fund-flow-summary", tags=["东方财富行业个股资金流"])
api_router.include_router(stock_fund_flow_hist.router, prefix="/stock-fund-flow-hist", tags=["东方财富行业/概念历史资金流"])
api_router.include_router(stock_report_fund_hold.router, prefix="/stock-report-fund-hold", tags=["东方财富基金持股"])
api_router.include_router(stock_lhb.router, prefix="/stock-lhb", tags=["东方财富龙虎榜"])
api_router.include_router(stock_institute_recommend.router, prefix="/stock-institute-recommend", tags=["机构推荐"])

# 技术指标相关（不需要认证）
api_router.include_router(indicators.router, prefix="/indicators", tags=["技术指标"])
api_router.include_router(kline.router, prefix="/kline", tags=["K 线图表"])

# 监控相关（不需要认证）
api_router.include_router(monitoring.router, tags=["监控"])

# 生命周期管理相关（不需要认证）
api_router.include_router(lifecycle.router, tags=["生命周期管理"])

# 备份和恢复相关（不需要认证）
api_router.include_router(backup.router, tags=["备份和恢复"])

# 性能优化相关（不需要认证）
api_router.include_router(performance.router, tags=["性能优化"])

# 审计日志相关（不需要认证）
api_router.include_router(audit.router, tags=["审计日志"])

# WebSocket 端点（不需要认证）
api_router.include_router(websocket_router.router, tags=["WebSocket"])
