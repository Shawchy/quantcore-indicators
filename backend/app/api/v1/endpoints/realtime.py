"""
实时盘口 TICK 快照接口
提供个股实时盘口数据（买一卖一等）
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
# import tushare as ts  # Tushare 已移除，使用其他数据源替代

router = APIRouter()


# 超时时间（秒）
REALTIME_TIMEOUT = 5  # 实时数据超时 5 秒
TICK_TIMEOUT = 10     # 分笔成交超时 10 秒


@router.get("/quote/{code}", response_model=ResponseModel[Dict[str, Any]])
async def get_realtime_quote(
    code: str,
    src: str = Query("sina", description="数据源：sina-新浪，dc-东方财富"),
    current_user: OptionalCurrentUser = None
):
    """
    获取个股实时盘口 TICK 快照
    
    ## 参数说明:
    - code: 股票代码（如：000001）
    - src: 数据源选择（sina-推荐，dc-备用）
    
    ## 返回数据:
    - 实时价格、涨跌幅
    - 买一至买五、卖一至卖五
    - 成交量、成交额
    - 开盘价、最高价、最低价
    """
    try:
        # 检查缓存（30 秒有效期）
        cache_key = f"realtime_quote_{code}_{src}"
        cached_data = await cache_manager.get("realtime", cache_key)
        
        if cached_data:
            return ResponseModel(
                data=cached_data,
                message="从缓存获取数据"
            )
        
        # 获取实时数据（添加超时控制）
        start_time = time.time()
        try:
            # 使用 akshare 新浪接口获取实时行情（东方财富接口已失效）
            import akshare as ak
            # 使用 asyncio.wait_for 添加超时控制
            df = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, lambda: ak.stock_zh_a_spot()
                ),
                timeout=REALTIME_TIMEOUT
            )
            # 过滤出指定股票（新浪接口字段是 code）
            df = df[df['code'] == code]
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail=f"获取实时数据超时（{REALTIME_TIMEOUT}秒），请重试或切换数据源"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取数据失败：{str(e)}"
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
        
        # 提取最新数据
        if len(df) > 0:
            latest = df.iloc[-1]
        else:
            return ResponseModel(
                success=False,
                code="NO_DATA",
                message="数据为空"
            )
        
        # 构建返回数据
        result = {
            "ts_code": code,
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fetch_time": round(elapsed, 2),
            "data_source": src,
            "quote": {
                "price": float(latest.get('PRICE', 0)),
                "change": float(latest.get('CHANGE', 0)),
                "change_pct": float(latest.get('PCT_CHANGE', 0)),
                "open": float(latest.get('OPEN', 0)),
                "high": float(latest.get('HIGH', 0)),
                "low": float(latest.get('LOW', 0)),
                "close": float(latest.get('CLOSE', 0)),
                "volume": float(latest.get('VOLUME', 0)),
                "amount": float(latest.get('AMOUNT', 0)) if 'AMOUNT' in latest else 0,
            },
            "bid_ask": {}
        }
        
        # 提取买卖盘数据（新浪数据源有这些字段）
        if 'B1' in df.columns:
            result["bid_ask"] = {
                "bid": [
                    {"price": float(latest.get(f'B{i}', 0)), "volume": float(latest.get(f'BV{i}', 0))}
                    for i in range(1, 6)
                ],
                "ask": [
                    {"price": float(latest.get(f'A{i}', 0)), "volume": float(latest.get(f'AV{i}', 0))}
                    for i in range(1, 6)
                ]
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


@router.get("/tick/{code}", response_model=ResponseModel[Dict[str, Any]])
async def get_realtime_tick_data(
    code: str,
    src: str = Query("dc", description="数据源：sina-新浪，dc-东方财富"),
    limit: int = Query(100, description="返回最近 N 条成交记录", ge=10, le=1000),
    current_user: OptionalCurrentUser = None
):
    """
    获取个股实时成交明细（分笔成交）
    
    ## 参数说明:
    - code: 股票代码（如：000001）
    - src: 数据源选择
    - limit: 返回最近 N 条记录（默认 100）
    
    ## 返回数据:
    - 时间、价格、成交量
    - 买卖类型（买盘/卖盘/中性）
    """
    try:
        # 检查缓存（60 秒有效期）
        cache_key = f"realtime_tick_{code}_{src}_{limit}"
        cached_data = await cache_manager.get("realtime", cache_key)
        
        if cached_data:
            return ResponseModel(
                data=cached_data,
                message="从缓存获取数据"
            )
        
        # 获取实时成交数据（添加超时控制）
        start_time = time.time()
        try:
            # 使用 akshare 获取分笔成交
            import akshare as ak
            df = await asyncio.wait_for(
                asyncio.get_event_loop().run_in_executor(
                    None, lambda: ak.stock_zh_a_tick_tx(symbol=code)
                ),
                timeout=TICK_TIMEOUT
            )
        except asyncio.TimeoutError:
            raise HTTPException(
                status_code=504,
                detail=f"获取成交数据超时（{TICK_TIMEOUT}秒），请重试或切换数据源"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"获取数据失败：{str(e)}"
            )
        
        elapsed = time.time() - start_time
        
        if df is None or len(df) == 0:
            return ResponseModel(
                success=False,
                code="NO_DATA",
                message="未获取到数据"
            )
        
        # 统一字段名
        df.columns = df.columns.str.upper()
        
        # 取最近 N 条
        recent = df.tail(limit).reset_index(drop=True)
        
        # 格式化数据
        tick_data = []
        for idx, row in recent.iterrows():
            tick = {
                "time": row.get('TIME', ''),
                "price": float(row.get('PRICE', 0)),
                "volume": float(row.get('VOLUME', 0)),
                "type": row.get('TYPE', ''),
            }
            if 'AMOUNT' in row:
                tick['amount'] = float(row.get('AMOUNT', 0))
            tick_data.append(tick)
        
        # 统计信息
        buy_count = len(recent[recent['TYPE'] == '买盘'])
        sell_count = len(recent[recent['TYPE'] == '卖盘'])
        neutral_count = len(recent[recent['TYPE'] == '中性'])
        
        result = {
            "ts_code": code,
            "update_time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "fetch_time": round(elapsed, 2),
            "data_source": src,
            "total_records": len(recent),
            "tick_data": tick_data,
            "stats": {
                "buy_count": buy_count,
                "sell_count": sell_count,
                "neutral_count": neutral_count,
                "buy_ratio": round(buy_count / len(recent) * 100, 2) if len(recent) > 0 else 0,
                "sell_ratio": round(sell_count / len(recent) * 100, 2) if len(recent) > 0 else 0,
            }
        }
        
        # 缓存 60 秒
        await cache_manager.set("realtime", cache_key, result, ttl=60)
        
        return ResponseModel(data=result)
        
    except Exception as e:
        return ResponseModel(
            success=False,
            code="ERROR",
            message=f"获取数据失败：{str(e)}"
        )
