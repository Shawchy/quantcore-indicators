"""
K 线图表 API 端点
提供 K 线数据和指标计算接口
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from loguru import logger
import pandas as pd

from app.services.chart_data_service import chart_data_service

router = APIRouter()


@router.get("/kline/{code}")
async def get_kline_data(
    code: str,
    k_type: str = Query("daily", pattern="^(daily|weekly|monthly|1m|5m|15m|30m|60m)$"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
    indicators: Optional[List[str]] = Query(None, description="指标列表：MA,MACD,RSI,KDJ,BOLL,ATR"),
    adjust: str = Query("qfq", pattern="^(qfq|hfq|no)$", description="复权类型"),
    use_cache: bool = Query(True, description="是否使用缓存")
):
    """
    获取 K 线数据（带指标）
    
    Args:
        code: 股票代码
        k_type: K 线类型
            - daily/weekly/monthly: 日/周/月线
            - 1m/5m/15m/30m/60m: 分钟线
        start_date: 开始日期
        end_date: 结束日期
        indicators: 技术指标列表
        adjust: 复权类型 (qfq=前复权，hfq=后复权，no=不复权)
        use_cache: 是否使用缓存
    
    Returns:
        {
            "code": "000001",
            "k_type": "daily",
            "data": [
                {
                    "date": "2024-01-01",
                    "open": 10.5,
                    "high": 11.2,
                    "low": 10.3,
                    "close": 11.0,
                    "volume": 1234567,
                    "amount": 13579246,
                    "turnover_rate": 2.5
                }
            ],
            "indicators": {
                "MA": [
                    {
                        "date": "2024-01-01",
                        "ma5": 10.8,
                        "ma10": 10.5,
                        "ma20": 10.2,
                        "ma60": 9.8
                    }
                ],
                "MACD": [...],
                "RSI": [...],
                "KDJ": [...]
            },
            "performance": {
                "fetch_time_ms": 50,
                "calc_time_ms": 30,
                "total_ms": 80
            }
        }
    """
    try:
        logger.info(f"获取 K 线数据：code={code}, k_type={k_type}, indicators={indicators}")
        
        result = await chart_data_service.get_kline_with_indicators(
            code=code,
            k_type=k_type,
            start_date=start_date,
            end_date=end_date,
            indicators=indicators,
            adjust=adjust
        )
        
        if not result['data']:
            raise HTTPException(status_code=404, detail="未找到 K 线数据")
        
        return {
            "status": "success",
            "data": result['data'],
            "indicators": result.get('indicators', {}),
            "metadata": {
                "code": code,
                "k_type": k_type,
                "count": len(result['data']),
                "adjust": adjust
            },
            "performance": result.get('performance', {})
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取 K 线数据失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取 K 线数据失败：{str(e)}")


@router.get("/kline/{code}/latest")
async def get_latest_kline(
    code: str,
    k_type: str = Query("daily", pattern="^(daily|weekly|monthly)$"),
    limit: int = Query(100, ge=1, le=1000, description="获取最近 N 条数据")
):
    """
    获取最新 K 线数据（用于实时图表）
    
    Args:
        code: 股票代码
        k_type: K 线类型
        limit: 获取最近 N 条数据
    
    Returns:
        最新 K 线数据（带指标）
    """
    try:
        result = await chart_data_service.get_kline_with_indicators(
            code=code,
            k_type=k_type,
            indicators=['MA', 'MACD', 'RSI']
        )
        
        if not result['data']:
            raise HTTPException(status_code=404, detail="未找到 K 线数据")
        
        # 只返回最新的 N 条
        latest_data = result['data'][-limit:]
        latest_indicators = {}
        
        for indicator_name, indicator_data in result.get('indicators', {}).items():
            if indicator_data:
                latest_indicators[indicator_name] = indicator_data[-limit:]
        
        return {
            "status": "success",
            "data": latest_data,
            "indicators": latest_indicators,
            "metadata": {
                "code": code,
                "k_type": k_type,
                "count": len(latest_data),
                "total": len(result['data'])
            }
        }
        
    except Exception as e:
        logger.error(f"获取最新 K 线数据失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取最新 K 线数据失败：{str(e)}")


@router.post("/indicators/calculate")
async def calculate_indicators_batch(
    data: List[dict],
    indicators: List[str] = Query(..., description="指标列表"),
    max_items: int = Query(1000, ge=1, le=5000, description="最大数据条数")
):
    """
    批量计算指标（适合前端 Worker 调用）
    
    Args:
        data: K 线数据列表
        indicators: 指标列表
        max_items: 最大数据条数限制（防止内存溢出）
    
    Returns:
        计算后的指标数据
    """
    try:
        # 数据量限制检查
        if len(data) > max_items:
            raise HTTPException(
                status_code=400,
                detail=f"数据量过大：{len(data)}条，最大允许{max_items}条"
            )
        
        # 转换为 DataFrame
        df = pd.DataFrame(data)
        
        # 验证必要列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            raise HTTPException(
                status_code=400, 
                detail=f"数据缺少必要列，需要：{required_cols}"
            )
        
        # 计算指标
        result = await chart_data_service._calculate_indicators(df, indicators)
        
        return {
            "status": "success",
            "data": result,
            "count": len(data),
            "indicators": indicators
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量计算指标失败：{e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"批量计算指标失败：{str(e)}")


@router.get("/indicators/list")
async def list_available_indicators():
    """
    获取可用的指标列表
    
    Returns:
        支持的指标列表
    """
    return {
        "status": "success",
        "data": {
            "trend": [
                {"name": "MA", "description": "移动平均线", "params": ["periods"]},
                {"name": "EMA", "description": "指数平均线", "params": ["periods"]},
                {"name": "BOLL", "description": "布林带", "params": ["period"]},
                {"name": "SAR", "description": "抛物线转向", "params": ["acceleration", "maximum"]}
            ],
            "momentum": [
                {"name": "MACD", "description": "异同移动平均线", "params": ["fast", "slow", "signal"]},
                {"name": "RSI", "description": "相对强弱指标", "params": ["periods"]},
                {"name": "KDJ", "description": "随机指标", "params": ["n", "m1", "m2"]},
                {"name": "CCI", "description": "顺势指标", "params": ["period"]}
            ],
            "volatility": [
                {"name": "ATR", "description": "平均真实波幅", "params": ["period"]},
                {"name": "BBANDS", "description": "布林带宽度", "params": ["period"]}
            ],
            "volume": [
                {"name": "OBV", "description": "能量潮", "params": []},
                {"name": "VR", "description": "成交量比率", "params": ["period"]}
            ]
        }
    }
