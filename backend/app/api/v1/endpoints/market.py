"""
实时涨跌幅排名接口
提供全市场股票实时涨跌幅排行、市场情绪分析等功能
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional, Dict, Any, List
import pandas as pd
import time
import asyncio
from app.api.deps import OptionalCurrentUser
from app.models.schemas import ResponseModel
from app.storage.cache import cache_manager
from app.config import settings
import tushare as ts
from app.services.data_persistence import data_persistence

router = APIRouter()

if settings.TUSHARE_TOKEN:
    ts.set_token(settings.TUSHARE_TOKEN)

# 超时时间配置
MARKET_RANKING_TIMEOUT = 15  # 市场排行超时 15 秒（数据量大）
MARKET_OVERVIEW_TIMEOUT = 10  # 市场概览超时 10 秒


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
        # 检查缓存（5 分钟有效期，优化后）
        cache_key = f"market_ranking_{src}_{top_n}"
        cached_data = await cache_manager.get("realtime", cache_key)
        
        if cached_data:
            return ResponseModel(
                data=cached_data,
                message="从缓存获取数据"
            )
        
        # 获取全市场数据（添加超时控制）
        start_time = time.time()
        try:
            # 使用 asyncio.wait_for 添加超时控制
            df = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, lambda: ts.realtime_list(src=src)
                ),
                timeout=MARKET_RANKING_TIMEOUT
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail=f"获取市场数据超时（{MARKET_RANKING_TIMEOUT}秒），请重试或切换数据源"
            )
        except Exception as e:
            return ResponseModel(
                success=False,
                code="ERROR",
                message=f"获取数据失败：{str(e)}"
            )
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
        
        # 缓存 5 分钟（优化后）
        await cache_manager.set("realtime", cache_key, result, ttl=300)
        
        # 异步保存到数据库（不阻塞返回）
        asyncio.create_task(_save_ranking_to_db(result, src))
        
        return ResponseModel(data=result)
        
    except Exception as e:
        return ResponseModel(
            success=False,
            code="ERROR",
            message=f"获取数据失败：{str(e)}"
        )


async def _save_ranking_to_db(result: Dict[str, Any], data_source: str):
    """异步保存市场排行数据到数据库"""
    try:
        # 保存 4 种类型的排行数据
        ranking_types = ["gainers", "losers", "amount", "turnover"]
        total_saved = 0
        
        for ranking_type in ranking_types:
            saved = await data_persistence.save_market_ranking(result, ranking_type, data_source)
            total_saved += saved
        
        if total_saved > 0:
            logger.info(f"市场排行数据持久化完成：共保存 {total_saved} 条记录")
    except Exception as e:
        logger.error(f"保存市场排行数据到数据库失败：{e}")


@router.get("/market-overview", response_model=ResponseModel[Dict[str, Any]])
async def get_market_overview(
    current_user: OptionalCurrentUser = None
):
    """
    获取市场概览（快速版本，只返回统计信息）
    """
    try:
        # 检查缓存（5 分钟有效期，优化后）
        cache_key = "market_overview"
        cached_data = await cache_manager.get("realtime", cache_key)
        
        if cached_data:
            return ResponseModel(data=cached_data)
        
        # 获取全市场数据（添加超时控制）
        try:
            df = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, lambda: ts.realtime_list(src='sina')
                ),
                timeout=MARKET_OVERVIEW_TIMEOUT
            )
        except asyncio.TimeoutError:
            return ResponseModel(
                success=False,
                code="TIMEOUT",
                message=f"获取数据超时（{MARKET_OVERVIEW_TIMEOUT}秒），请重试"
            )
        except Exception as e:
            return ResponseModel(
                success=False,
                code="ERROR",
                message=f"获取数据失败：{str(e)}"
            )
        
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
        
        # 缓存 5 分钟（优化后）
        await cache_manager.set("realtime", cache_key, result, ttl=300)
        
        return ResponseModel(data=result)
        
    except Exception as e:
        return ResponseModel(
            success=False,
            code="ERROR",
            message=f"获取数据失败：{str(e)}"
        )


@router.get("/market-ranking/history", response_model=ResponseModel[List[Dict[str, Any]]])
async def get_market_ranking_history(
    ranking_type: str = Query(..., description="排行类型：gainers/losers/amount/turnover"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    limit: int = Query(100, description="返回记录数限制", ge=1, le=1000),
    current_user: OptionalCurrentUser = None
):
    """
    获取市场排行历史数据
    
    ## 参数说明:
    - ranking_type: 排行类型（gainers-涨幅榜，losers-跌幅榜，amount-成交额榜，turnover-换手率榜）
    - start_date: 开始日期（YYYY-MM-DD），不传则查询当天
    - end_date: 结束日期（YYYY-MM-DD），不传则查询当天
    - limit: 返回记录数限制（默认 100，最大 1000）
    
    ## 返回数据:
    - 历史排行数据列表（按日期倒序、排名正序排列）
    """
    try:
        # 验证 ranking_type
        valid_types = ["gainers", "losers", "amount", "turnover"]
        if ranking_type not in valid_types:
            return ResponseModel(
                success=False,
                code="INVALID_PARAM",
                message=f"无效的排行类型，必须是：{', '.join(valid_types)}"
            )
        
        # 从数据库查询历史数据
        history_data = await data_persistence.get_market_ranking_history(
            ranking_type=ranking_type,
            start_date=start_date,
            end_date=end_date,
            limit=limit
        )
        
        if not history_data:
            return ResponseModel(
                data=[],
                message="未找到历史数据"
            )
        
        return ResponseModel(data=history_data)
        
    except Exception as e:
        return ResponseModel(
            success=False,
            code="ERROR",
            message=f"获取历史数据失败：{str(e)}"
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
