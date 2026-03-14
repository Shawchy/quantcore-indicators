"""
实时涨跌幅排名接口
提供全市场股票实时涨跌幅排行、市场情绪分析等功能
"""
from fastapi import APIRouter, Depends, Query
from typing import Optional, Dict, Any, List
import pandas as pd
import time
from app.api.deps import OptionalCurrentUser
from app.models.schemas import ResponseModel
from app.storage.cache import cache_manager
from app.config import settings
import tushare as ts

router = APIRouter()

if settings.TUSHARE_TOKEN:
    ts.set_token(settings.TUSHARE_TOKEN)


@router.get("/market-ranking", response_model=ResponseModel[Dict[str, Any]])
async def get_market_ranking(
    top_n: int = Query(50, description="返回前 N 只股票", ge=10, le=100),
    src: str = Query("sina", description="数据源：sina-新浪，dc-东方财富"),
    current_user: OptionalCurrentUser = None
):
    """
    获取市场实时涨跌幅排名
    
    ## 参数说明:
    - top_n: 返回前 N 只股票（默认 50，范围 10-100）
    - src: 数据源选择（sina-推荐，dc-备用）
    
    ## 返回数据:
    - 涨幅榜前 N
    - 跌幅榜前 N
    - 成交额前 N
    - 换手率前 N
    - 市场情绪统计
    """
    try:
        # 检查缓存（1 分钟有效期）
        cache_key = f"market_ranking_{src}_{top_n}"
        cached_data = await cache_manager.get("realtime", cache_key)
        
        if cached_data:
            return ResponseModel(
                data=cached_data,
                message="从缓存获取数据"
            )
        
        # 获取全市场数据
        start_time = time.time()
        df = ts.realtime_list(src=src)
        elapsed = time.time() - start_time
        
        if df is None or len(df) == 0:
            return ResponseModel(
                success=False,
                code="NO_DATA",
                message="未获取到数据"
            )
        
        # 数据清洗和格式化
        # 统一字段名（新浪数据字段是大写的）
        df.columns = df.columns.str.upper()
        
        # 确保有必要的字段
        required_columns = ['TS_CODE', 'NAME', 'PRICE', 'PCT_CHANGE', 'VOLUME', 'AMOUNT']
        for col in required_columns:
            if col not in df.columns:
                df[col] = 0
        
        # 计算统计指标
        total_count = len(df)
        up_count = len(df[df['PCT_CHANGE'] > 0])
        down_count = len(df[df['PCT_CHANGE'] < 0])
        flat_count = len(df[df['PCT_CHANGE'] == 0])
        limit_up = len(df[df['PCT_CHANGE'] >= 9.9])
        limit_down = len(df[df['PCT_CHANGE'] <= -9.9])
        
        # 市场情绪判断
        up_down_ratio = up_count / down_count if down_count > 0 else float('inf')
        if up_down_ratio > 2 and limit_up > limit_down * 3:
            sentiment = "强势上涨"
            sentiment_score = 5
        elif up_down_ratio > 1.5:
            sentiment = "震荡上涨"
            sentiment_score = 4
        elif up_down_ratio < 0.5:
            sentiment = "震荡下跌"
            sentiment_score = 2
        elif up_down_ratio < 0.3 and limit_up < limit_down * 0.3:
            sentiment = "强势下跌"
            sentiment_score = 1
        else:
            sentiment = "震荡整理"
            sentiment_score = 3
        
        # 涨幅榜
        top_gainers = df.nlargest(top_n, 'PCT_CHANGE')[[
            'TS_CODE', 'NAME', 'PRICE', 'PCT_CHANGE', 'CHANGE', 
            'VOLUME', 'AMOUNT', 'OPEN', 'HIGH', 'LOW', 'CLOSE'
        ]].to_dict('records')
        
        # 跌幅榜
        top_losers = df.nsmallest(top_n, 'PCT_CHANGE')[[
            'TS_CODE', 'NAME', 'PRICE', 'PCT_CHANGE', 'CHANGE',
            'VOLUME', 'AMOUNT', 'OPEN', 'HIGH', 'LOW', 'CLOSE'
        ]].to_dict('records')
        
        # 成交额榜
        top_amount = df.nlargest(top_n, 'AMOUNT')[[
            'TS_CODE', 'NAME', 'PRICE', 'PCT_CHANGE', 'AMOUNT', 'VOLUME'
        ]].to_dict('records')
        
        # 换手率榜（如果有该字段）
        if 'TURNOVER_RATE' in df.columns:
            top_turnover = df.nlargest(top_n, 'TURNOVER_RATE')[[
                'TS_CODE', 'NAME', 'PRICE', 'PCT_CHANGE', 'TURNOVER_RATE'
            ]].to_dict('records')
        else:
            top_turnover = []
        
        # 构建返回数据
        result = {
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fetch_time": round(elapsed, 2),
            "data_source": src,
            "total_stocks": total_count,
            "market_stats": {
                "up_count": up_count,
                "down_count": down_count,
                "flat_count": flat_count,
                "limit_up_count": limit_up,
                "limit_down_count": limit_down,
                "up_ratio": round(up_count / total_count * 100, 2) if total_count > 0 else 0,
                "down_ratio": round(down_count / total_count * 100, 2) if total_count > 0 else 0
            },
            "sentiment": {
                "text": sentiment,
                "score": sentiment_score,
                "up_down_ratio": round(up_down_ratio, 2)
            },
            "rankings": {
                "gainers": top_gainers,
                "losers": top_losers,
                "amount": top_amount,
                "turnover": top_turnover
            }
        }
        
        # 缓存 1 分钟
        await cache_manager.set("realtime", cache_key, result, ttl=60)
        
        return ResponseModel(data=result)
        
    except Exception as e:
        return ResponseModel(
            success=False,
            code="ERROR",
            message=f"获取数据失败：{str(e)}"
        )


@router.get("/market-overview", response_model=ResponseModel[Dict[str, Any]])
async def get_market_overview(
    current_user: OptionalCurrentUser = None
):
    """
    获取市场概览（快速版本，只返回统计信息）
    """
    try:
        # 检查缓存（30 秒有效期）
        cache_key = "market_overview"
        cached_data = await cache_manager.get("realtime", cache_key)
        
        if cached_data:
            return ResponseModel(data=cached_data)
        
        # 获取全市场数据
        df = ts.realtime_list(src='sina')
        
        if df is None or len(df) == 0:
            return ResponseModel(
                success=False,
                code="NO_DATA",
                message="未获取到数据"
            )
        
        # 统一字段名
        df.columns = df.columns.str.upper()
        
        # 基本统计
        total = len(df)
        up = len(df[df['PCT_CHANGE'] > 0])
        down = len(df[df['PCT_CHANGE'] < 0])
        flat = len(df[df['PCT_CHANGE'] == 0])
        
        # 涨跌幅分布
        pct_5_plus = len(df[df['PCT_CHANGE'] > 5])
        pct_3_to_5 = len(df[(df['PCT_CHANGE'] > 3) & (df['PCT_CHANGE'] <= 5)])
        pct_minus_3_to_3 = len(df[(df['PCT_CHANGE'] >= -3) & (df['PCT_CHANGE'] <= 3)])
        pct_minus_5_to_minus_3 = len(df[(df['PCT_CHANGE'] >= -5) & (df['PCT_CHANGE'] < -3)])
        pct_minus_5 = len(df[df['PCT_CHANGE'] < -5])
        
        # 平均涨跌幅
        avg_pct = df['PCT_CHANGE'].mean()
        median_pct = df['PCT_CHANGE'].median()
        
        # 成交额统计
        total_amount = df['AMOUNT'].sum() if 'AMOUNT' in df.columns else 0
        avg_amount = df['AMOUNT'].mean() if 'AMOUNT' in df.columns else 0
        
        result = {
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_stocks": total,
            "market_stats": {
                "up": up,
                "down": down,
                "flat": flat,
                "up_ratio": round(up / total * 100, 2),
                "down_ratio": round(down / total * 100, 2)
            },
            "distribution": {
                "pct_5_plus": pct_5_plus,
                "pct_3_to_5": pct_3_to_5,
                "pct_minus_3_to_3": pct_minus_3_to_3,
                "pct_minus_5_to_minus_3": pct_minus_5_to_minus_3,
                "pct_minus_5": pct_minus_5
            },
            "statistics": {
                "avg_pct_change": round(avg_pct, 2),
                "median_pct_change": round(median_pct, 2),
                "total_amount": round(total_amount / 100000000, 2),  # 亿元
                "avg_amount": round(avg_amount / 1000000, 2)  # 百万元
            }
        }
        
        # 缓存 30 秒
        await cache_manager.set("realtime", cache_key, result, ttl=30)
        
        return ResponseModel(data=result)
        
    except Exception as e:
        return ResponseModel(
            success=False,
            code="ERROR",
            message=f"获取数据失败：{str(e)}"
        )


@router.get("/sector-performance", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_sector_performance(
    sector_type: str = Query("industry", description="板块类型：industry-行业，concept-概念，area-地区"),
    current_user: OptionalCurrentUser = None
):
    """
    获取板块涨跌幅排行
    """
    try:
        # 这里可以调用 Tushare 的板块接口
        # 暂时返回示例数据
        sectors = [
            {"code": "BK0001", "name": "半导体", "pct_change": 3.5, "volume": 1000000},
            {"code": "BK0002", "name": "新能源", "pct_change": 2.8, "volume": 800000},
            {"code": "BK0003", "name": "医药生物", "pct_change": -1.2, "volume": 600000},
        ]
        
        return ResponseModel(data=sectors)
        
    except Exception as e:
        return ResponseModel(
            success=False,
            code="ERROR",
            message=f"获取数据失败：{str(e)}"
        )
