"""个股详细信息 API 端点"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from loguru import logger

from app.adapters.factory import DataSourceManager
from app.adapters.base import (
    StockIndividualInfo,
    DividendInfo,
    FinancialStatement,
    PerformanceExpress,
    FundFlowItem,
    BoardDetail,
    IndustryValuation,
    StockRepurchase,
    RestrictedShareUnlock,
)
from app.api.deps import get_current_user
from app.storage.sqlite import User

router = APIRouter()


@router.get("/stock/{code}/individual-info", summary="获取个股详细资料", description="获取个股的基本面数据，包括估值、财务、股本等信息")
async def get_individual_info(code: str, current_user: User = Depends(get_current_user)):
    """获取个股详细资料
    
    **数据字段:**
    - latest_price: 最新价
    - total_shares: 总股本（亿股）
    - float_shares: 流通股本（亿股）
    - total_market_cap: 总市值（亿元）
    - float_market_cap: 流通市值（亿元）
    - pe_ratio: 市盈率（动态）
    - pb_ratio: 市净率
    - roe: ROE（加权）
    - eps: 每股收益
    - bps: 每股净资产
    - net_profit: 净利润（亿元）
    - revenue: 营业收入（亿元）
    - gross_margin: 毛利率
    
    **示例:**
    ```
    GET /api/v1/stock/000001/individual-info
    ```
    """
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_individual_info(code)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"未找到股票 {code} 的详细信息")
        
        return {
            "code": code,
            "data": result.__dict__
        }
        
    except Exception as e:
        logger.error(f"获取个股详情失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/all-a-shares-spot", summary="获取全 A 股实时行情", description="获取所有 A 股的实时行情数据，包括涨跌幅、成交量、换手率等")
async def get_all_a_shares_spot(current_user: User = Depends(get_current_user)):
    """获取全 A 股实时行情
    
    **返回:** 包含所有 A 股实时行情的列表
    
    **数据字段:**
    - code: 代码
    - name: 名称
    - latest_price: 最新价
    - change_pct: 涨跌幅
    - change: 涨跌额
    - volume: 成交量
    - amount: 成交额
    - amplitude: 振幅
    - turnover_rate: 换手率
    - volume_ratio: 量比
    - pe_ratio: 市盈率
    - total_market_cap: 总市值
    - float_market_cap: 流通市值
    """
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_all_a_shares_spot()
        
        return {
            "count": len(result),
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取全 A 股行情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/dividend", summary="获取分红送转数据", description="获取个股历史分红送转记录")
async def get_dividend_info(code: str, current_user: User = Depends(get_current_user)):
    """获取分红送转数据
    
    **数据字段:**
    - announce_date: 公告日期
    - record_date: 股权登记日
    - ex_dividend_date: 除权除息日
    - plan: 分配方案
    - cash_dividend: 每股派现（元）
    - bonus_shares: 每股送股
    - capital_reserve_transfer: 每股转增
    """
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_dividend_info(code)
        
        return {
            "code": code,
            "count": len(result),
            "data": [item.__dict__ for item in result]
        }
        
    except Exception as e:
        logger.error(f"获取分红数据失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/balance-sheet", summary="获取资产负债表", description="获取个股历史资产负债表数据")
async def get_balance_sheet(code: str, current_user: User = Depends(get_current_user)):
    """获取资产负债表"""
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_balance_sheet(code)
        
        return {
            "code": code,
            "count": len(result),
            "data": [
                {
                    "report_date": item.report_date,
                    "statement_type": item.statement_type,
                    "data": item.data
                }
                for item in result
            ]
        }
        
    except Exception as e:
        logger.error(f"获取资产负债表失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/income-statement", summary="获取利润表", description="获取个股历史利润表数据")
async def get_income_statement(code: str, current_user: User = Depends(get_current_user)):
    """获取利润表"""
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_income_statement(code)
        
        return {
            "code": code,
            "count": len(result),
            "data": [
                {
                    "report_date": item.report_date,
                    "statement_type": item.statement_type,
                    "data": item.data
                }
                for item in result
            ]
        }
        
    except Exception as e:
        logger.error(f"获取利润表失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/cashflow-statement", summary="获取现金流量表", description="获取个股历史现金流量表数据")
async def get_cashflow_statement(code: str, current_user: User = Depends(get_current_user)):
    """获取现金流量表"""
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_cashflow_statement(code)
        
        return {
            "code": code,
            "count": len(result),
            "data": [
                {
                    "report_date": item.report_date,
                    "statement_type": item.statement_type,
                    "data": item.data
                }
                for item in result
            ]
        }
        
    except Exception as e:
        logger.error(f"获取现金流量表失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/performance-express", summary="获取业绩快报", description="获取个股业绩快报/业绩预告数据")
async def get_performance_express(code: str, current_user: User = Depends(get_current_user)):
    """获取业绩快报
    
    **数据字段:**
    - announce_date: 公告日期
    - report_date: 报告期
    - net_profit: 净利润（亿元）
    - net_profit_yoy: 净利润同比增长率（%）
    - eps: 每股收益
    - roe: 净资产收益率
    - revenue: 营业收入（亿元）
    - revenue_yoy: 营收同比增长率（%）
    - reason: 业绩变动原因
    """
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_performance_express(code)
        
        return {
            "code": code,
            "count": len(result),
            "data": [item.__dict__ for item in result]
        }
        
    except Exception as e:
        logger.error(f"获取业绩快报失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/fund-flow", summary="获取资金流向", description="获取个股近期资金流向数据")
async def get_fund_flow(code: str, current_user: User = Depends(get_current_user)):
    """获取资金流向
    
    **数据字段:**
    - trade_date: 交易日
    - main_net_amount: 主力净流入（万元）
    - main_net_ratio: 主力净流入占比（%）
    - super_large_net: 超大单净流入（万元）
    - large_net: 大单净流入（万元）
    - medium_net: 中单净流入（万元）
    - small_net: 小单净流入（万元）
    """
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_individual_fund_flow(code)
        
        return {
            "code": code,
            "count": len(result),
            "data": [item.__dict__ for item in result]
        }
        
    except Exception as e:
        logger.error(f"获取资金流向失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/board/concept/{code}/detail", summary="获取概念板块详情", description="获取概念板块的成分股及领涨股信息")
async def get_concept_board_detail(code: str, current_user: User = Depends(get_current_user)):
    """获取概念板块详情
    
    **数据字段:**
    - code: 板块代码
    - name: 板块名称
    - board_type: 板块类型
    - leader_code: 领涨股代码
    - leader_name: 领涨股名称
    - leader_change_pct: 领涨股涨跌幅
    - components: 成分股列表
    """
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_concept_board_detail(code)
        
        if result is None:
            raise HTTPException(status_code=404, detail=f"未找到板块 {code}")
        
        return {
            "code": code,
            "data": result.__dict__
        }
        
    except Exception as e:
        logger.error(f"获取概念板块详情失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/board/industry-valuation", summary="获取行业估值", description="获取所有行业板块的估值数据")
async def get_industry_valuation(current_user: User = Depends(get_current_user)):
    """获取行业估值数据
    
    **数据字段:**
    - code: 行业代码
    - name: 行业名称
    - index_value: 行业指数
    - change_pct: 涨跌幅
    - pe_ttm: 市盈率（TTM）
    - pb_ratio: 市净率
    - total_market_cap: 总市值（亿元）
    """
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_industry_valuation()
        
        return {
            "count": len(result),
            "data": [item.__dict__ for item in result]
        }
        
    except Exception as e:
        logger.error(f"获取行业估值数据失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/repurchase", summary="获取股票回购", description="获取个股历史回购数据")
async def get_stock_repurchase(code: str, current_user: User = Depends(get_current_user)):
    """获取股票回购数据
    
    **数据字段:**
    - announce_date: 公告日期
    - repurchase_amount: 回购金额（万元）
    - repurchase_quantity: 回购数量（万股）
    - repurchase_ratio: 回购比例（%）
    - purpose: 回购目的
    - progress: 实施进度
    - price_range: 价格区间
    """
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_stock_repurchase(code)
        
        return {
            "code": code,
            "count": len(result),
            "data": [item.__dict__ for item in result]
        }
        
    except Exception as e:
        logger.error(f"获取股票回购数据失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{code}/restricted-unlock", summary="获取限售股解禁", description="获取个股限售股解禁数据")
async def get_restricted_unlock(code: str, current_user: User = Depends(get_current_user)):
    """获取限售股解禁数据
    
    **数据字段:**
    - unlock_date: 解禁日期
    - unlock_quantity: 解禁数量（万股）
    - unlock_ratio: 解禁比例（%）
    - unlock_type: 解禁类型
    - unlock_shares_holder: 解禁股东
    """
    try:
        manager = DataSourceManager()
        adapter = manager.get_adapter("akshare")
        
        result = await adapter.get_restricted_share_unlock(code)
        
        return {
            "code": code,
            "count": len(result),
            "data": [item.__dict__ for item in result]
        }
        
    except Exception as e:
        logger.error(f"获取限售股解禁数据失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
