"""财务深度分析 API 端点

提供财务分析指标、历史分红、分红详情、财务摘要等接口
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import FinancialIndicator, HistoricalDividend
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/financial-indicator/{code}", response_model=ResponseModel[List[FinancialIndicator]])
async def get_financial_indicator(
    code: str,
    start_date: Optional[str] = Query(
        None,
        description="开始日期，格式 YYYY-MM-DD"
    ),
    end_date: Optional[str] = Query(
        None,
        description="结束日期，格式 YYYY-MM-DD"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取财务分析主要指标
    
    - **code**: 股票代码
    - **report_date**: 报告期
    - **eps**: 每股收益
    - **roe**: 净资产收益率
    - **roa**: 总资产收益率
    - **gross_margin**: 销售毛利率
    - **net_margin**: 销售净利率
    - **debt_ratio**: 资产负债率
    - **current_ratio**: 流动比率
    - **quick_ratio**: 速动比率
    - **inventory_turnover**: 存货周转率
    - **receivables_turnover**: 应收账款周转率
    
    使用场景：
    - 财务健康状况分析
    - 盈利能力评估
    - 运营效率分析
    - 偿债能力分析
    """
    try:
        data = await adapter.get_financial_analysis_indicator(code, start_date, end_date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取财务分析指标失败：{str(e)}",
            "data": []
        }


@router.get("/history-dividend/{code}", response_model=ResponseModel[List[HistoricalDividend]])
async def get_history_dividend(
    code: str,
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取历史分红数据
    
    - **code**: 股票代码
    - **announce_date**: 公告日期
    - **record_date**: 股权登记日
    - **ex_dividend_date**: 除权除息日
    - **cash_dividend**: 每股派现（税前）
    - **bonus_shares**: 每股送股
    - **capital_reserve_transfer**: 每股转增
    - **total_dividend**: 分红总额（万元）
    
    使用场景：
    - 分红历史查询
    - 股息率计算
    - 价值投资分析
    """
    try:
        data = await adapter.get_history_dividend(code)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取历史分红数据失败：{str(e)}",
            "data": []
        }


@router.get("/dividend-detail/{code}", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_dividend_detail(
    code: str,
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取分红详情
    
    返回数据字段：
    - **announce_date**: 公告日期
    - **record_date**: 股权登记日
    - **ex_dividend_date**: 除权除息日
    - **plan**: 分配方案
    - **cash_dividend**: 每股派现
    - **bonus_shares**: 每股送股
    - **capital_reserve_transfer**: 每股转增
    
    使用场景：
    - 详细分红方案查询
    - 送转股分析
    """
    try:
        data = await adapter.get_dividend_detail(code)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取分红详情失败：{str(e)}",
            "data": []
        }


@router.get("/financial-abstract/{code}", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_financial_abstract(
    code: str,
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取财务摘要数据
    
    返回数据字段：
    - **report_date**: 报告期
    - **revenue**: 营业收入
    - **revenue_growth**: 营收增长率
    - **net_profit**: 净利润
    - **net_profit_growth**: 净利润增长率
    - **eps**: 每股收益
    - **roe**: 净资产收益率
    - **bvps**: 每股净资产
    - **cfps**: 每股现金流
    
    使用场景：
    - 快速财务概览
    - 业绩趋势分析
    - 财务数据对比
    """
    try:
        data = await adapter.get_financial_abstract(code)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取财务摘要失败：{str(e)}",
            "data": []
        }
