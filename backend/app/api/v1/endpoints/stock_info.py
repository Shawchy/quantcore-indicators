"""个股详细信息 API 端点"""

from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional
from loguru import logger

from app.adapters.factory import data_source_manager
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


def _get_akshare_adapter():
    """获取 akshare 适配器（使用全局单例）"""
    return data_source_manager.get_adapter("akshare")


@router.get("/stock/{code}/individual-info", summary="获取个股详细资料", description="获取个股的基本面数据，包括估值、财务、股本等信息")
async def get_individual_info(code: str, current_user: User = Depends(get_current_user)):
    """获取个股详细资料"""
    try:
        adapter = _get_akshare_adapter()
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
    """获取全 A 股实时行情"""
    try:
        adapter = _get_akshare_adapter()
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
    """获取分红送转数据"""
    try:
        adapter = _get_akshare_adapter()
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
        adapter = _get_akshare_adapter()
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
        adapter = _get_akshare_adapter()
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
        adapter = _get_akshare_adapter()
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
    """获取业绩快报"""
    try:
        adapter = _get_akshare_adapter()
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
    """获取资金流向"""
    try:
        adapter = _get_akshare_adapter()
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
    """获取概念板块详情"""
    try:
        adapter = _get_akshare_adapter()
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
    """获取行业估值数据"""
    try:
        adapter = _get_akshare_adapter()
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
    """获取股票回购数据"""
    try:
        adapter = _get_akshare_adapter()
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
    """获取限售股解禁数据"""
    try:
        adapter = _get_akshare_adapter()
        result = await adapter.get_restricted_share_unlock(code)
        
        return {
            "code": code,
            "count": len(result),
            "data": [item.__dict__ for item in result]
        }
        
    except Exception as e:
        logger.error(f"获取限售股解禁数据失败 {code}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
