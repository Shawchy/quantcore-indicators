"""龙虎榜 API 端点

提供龙虎榜详情、机构买卖统计、营业部排行等接口
"""
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, Query

from app.adapters.akshare_adapter import AkShareAdapter
from app.adapters.base import LHBEntry, InstitutionalTrading
from app.dependencies import get_akshare_adapter
from app.schemas.response import ResponseModel
from app.utils.auth import get_current_user
from app.models.user import User


router = APIRouter()


@router.get("/detail/{code}", response_model=ResponseModel[List[LHBEntry]])
async def get_lhb_detail(
    code: str,
    start_date: Optional[str] = Query(
        None,
        description="开始日期，格式 YYYYMMDD"
    ),
    end_date: Optional[str] = Query(
        None,
        description="结束日期，格式 YYYYMMDD"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取龙虎榜详情数据
    
    - **code**: 股票代码
    - **name**: 股票名称
    - **trade_date**: 交易日期
    - **close_price**: 收盘价
    - **change_pct**: 涨跌幅
    - **turnover_rate**: 换手率
    - **total_turnover**: 总成交额（万元）
    - **net_buy**: 净买入（万元）
    - **buy_amount**: 买入总额（万元）
    - **sell_amount**: 卖出总额（万元）
    - **reason**: 上榜原因
    - **buyer_seats**: 买方席位数
    - **seller_seats**: 卖方席位数
    
    使用场景：
    - 查询个股历史龙虎榜记录
    - 分析龙虎榜资金流向
    - 识别游资和机构动向
    """
    try:
        data = await adapter.get_lhb_detail(code, start_date, end_date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取龙虎榜详情失败：{str(e)}",
            "data": []
        }


@router.get("/institutional-stats", response_model=ResponseModel[List[InstitutionalTrading]])
async def get_institutional_stats(
    trade_date: Optional[str] = Query(
        None,
        description="交易日期，格式 YYYYMMDD，默认为今日"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取机构买卖统计
    
    - **code**: 股票代码
    - **name**: 股票名称
    - **trade_date**: 交易日期
    - **institutional_buy**: 机构买入（万元）
    - **institutional_sell**: 机构卖出（万元）
    - **institutional_net**: 机构净买（万元）
    - **institutional_buy_seats**: 机构买入席位数
    - **institutional_sell_seats**: 机构卖出席位数
    
    使用场景：
    - 监控机构资金流向
    - 识别机构重仓股
    - 分析机构买卖力度
    """
    try:
        data = await adapter.get_lhb_institutional_stats(trade_date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取机构买卖统计失败：{str(e)}",
            "data": []
        }


@router.get("/broker-ranking", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_broker_ranking(
    trade_date: Optional[str] = Query(
        None,
        description="交易日期，格式 YYYYMMDD，默认为今日"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取营业部排行
    
    返回数据字段：
    - **broker_name**: 营业部名称
    - **total_buy**: 总买入（万元）
    - **total_sell**: 总卖出（万元）
    - **net_buy**: 净买入（万元）
    - **buy_count**: 买入次数
    - **sell_count**: 卖出次数
    - **total_count**: 总上榜次数
    
    使用场景：
    - 识别活跃营业部
    - 追踪游资席位
    - 分析营业部操作风格
    """
    try:
        data = await adapter.get_lhb_broker_ranking(trade_date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取营业部排行失败：{str(e)}",
            "data": []
        }


@router.get("/sina-detail/{symbol}", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_lhb_detail_sina(
    symbol: str,
    date: Optional[str] = Query(
        None,
        description="日期，格式 YYYY-MM-DD，默认为最新"
    ),
    adapter: AkShareAdapter = Depends(get_akshare_adapter),
    current_user: User = Depends(get_current_user)
):
    """获取龙虎榜详情（新浪数据源）
    
    返回数据字段：
    - **trade_date**: 交易日期
    - **code**: 股票代码
    - **name**: 股票名称
    - **close_price**: 收盘价
    - **change_ratio**: 涨跌幅
    - **turnover_rate**: 换手率
    - **reason**: 上榜原因
    - **buy_total**: 买入总额
    - **sell_total**: 卖出总额
    - **net_amount**: 净买入额
    - **detail**: 买卖明细
    
    使用场景：
    - 多数据源对比验证
    - 获取新浪特色数据
    - 补充东方财富数据
    """
    try:
        data = await adapter.get_lhb_detail_sina(symbol, date)
        return {
            "code": 200,
            "message": "success",
            "data": data
        }
    except Exception as e:
        return {
            "code": 500,
            "message": f"获取新浪龙虎榜详情失败：{str(e)}",
            "data": []
        }
