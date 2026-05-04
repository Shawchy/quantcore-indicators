"""
图表数据服务
提供 K 线图表所需的数据处理和指标计算
"""
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np
from datetime import datetime
from loguru import logger
import time

from app.processing.indicators_manager import get_indicators_manager, IndicatorsManager
from app.services.stock_service import stock_service


class ChartDataService:
    """图表数据服务"""
    
    def __init__(self, prefer_talib: bool = True):
        """
        Args:
            prefer_talib: 是否优先使用 TA-Lib
        """
        self.indicators_manager = get_indicators_manager(prefer_talib=prefer_talib)
    
    async def get_kline_with_indicators(
        self,
        code: str,
        k_type: str = 'daily',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        indicators: Optional[List[str]] = None,
        adjust: str = 'qfq'
    ) -> Dict[str, Any]:
        """
        获取 K 线数据并计算指标
        
        Args:
            code: 股票代码
            k_type: K 线类型 (daily/weekly/monthly)
            start_date: 开始日期
            end_date: 结束日期
            indicators: 指标列表 ['MA', 'MACD', 'RSI', 'KDJ', ...]
            adjust: 复权类型 (qfq/hfq/no)
        
        Returns:
            {
                "code": "000001",
                "k_type": "daily",
                "data": [...],  # K 线数据
                "indicators": {...},  # 指标数据
                "performance": {
                    "fetch_time_ms": 50,
                    "calc_time_ms": 30
                }
            }
        """
        start_time = time.time()
        
        # 1. 获取 K 线数据
        # 构建方法名，处理分钟线特殊情况
        if k_type in ['1m', '5m', '15m', '30m', '60m']:
            # 分钟线使用通用的 get_kline 方法，传入 freq 参数
            kline_result = await stock_service.get_kline(
                code=code,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust,
                freq=k_type
            )
        else:
            safe_methods = {
                'daily': stock_service.get_kline,
                'weekly': stock_service.get_weekly_kline,
                'monthly': stock_service.get_monthly_kline,
            }
            kline_method = safe_methods.get(k_type, stock_service.get_kline)
            kline_result = await kline_method(
                code=code,
                start_date=start_date,
                end_date=end_date,
                adjust=adjust
            )
        
        fetch_time = (time.time() - start_time) * 1000
        logger.debug(f"获取 K 线数据耗时：{fetch_time:.2f}ms")
        
        # 2. 转换为 DataFrame
        if isinstance(kline_result, dict):
            kline_data = kline_result.get('data', [])
        else:
            kline_data = kline_result
        
        if not kline_data:
            return {
                "code": code,
                "k_type": k_type,
                "data": [],
                "indicators": {},
                "performance": {
                    "fetch_time_ms": fetch_time,
                    "calc_time_ms": 0
                }
            }
        
        df = pd.DataFrame(kline_data)
        
        # 3. 计算指标
        calc_start = time.time()
        indicators_data = {}
        
        if indicators:
            indicators_data = await self._calculate_indicators(df, indicators)
        
        calc_time = (time.time() - calc_start) * 1000
        logger.debug(f"计算指标耗时：{calc_time:.2f}ms")
        
        # 4. 格式化返回
        return {
            "code": code,
            "k_type": k_type,
            "data": self._format_kline_data(kline_data),
            "indicators": indicators_data,
            "performance": {
                "fetch_time_ms": fetch_time,
                "calc_time_ms": calc_time,
                "total_ms": fetch_time + calc_time
            }
        }
    
    async def _calculate_indicators(
        self,
        df: pd.DataFrame,
        indicators: List[str]
    ) -> Dict[str, Any]:
        """
        计算技术指标
        
        Args:
            df: K 线数据 DataFrame
            indicators: 指标列表
        
        Returns:
            指标数据字典
        """
        result = {}
        
        # 确保有必要的列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            logger.warning("K 线数据缺少必要列")
            return result
        
        # 计算各指标
        if 'MA' in indicators:
            result['MA'] = await self._calculate_ma(df)
        
        if 'MACD' in indicators:
            result['MACD'] = await self._calculate_macd(df)
        
        if 'RSI' in indicators:
            result['RSI'] = await self._calculate_rsi(df)
        
        if 'KDJ' in indicators:
            result['KDJ'] = await self._calculate_kdj(df)
        
        if 'BOLL' in indicators:
            result['BOLL'] = await self._calculate_boll(df)
        
        if 'ATR' in indicators:
            result['ATR'] = await self._calculate_atr(df)
        
        return result
    
    async def _calculate_ma(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """计算移动平均线"""
        try:
            result_df = self.indicators_manager.calculate_ma(
                df, periods=[5, 10, 20, 60], price_column='close'
            )
            
            return [
                {
                    "date": str(row.get('date', '')),
                    "ma5": float(row['ma5']) if pd.notna(row.get('ma5')) else None,
                    "ma10": float(row['ma10']) if pd.notna(row.get('ma10')) else None,
                    "ma20": float(row['ma20']) if pd.notna(row.get('ma20')) else None,
                    "ma60": float(row['ma60']) if pd.notna(row.get('ma60')) else None
                }
                for _, row in result_df.iterrows()
            ]
        except Exception as e:
            logger.error(f"计算 MA 失败：{e}")
            return []
    
    async def _calculate_macd(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """计算 MACD"""
        try:
            result_df = self.indicators_manager.calculate_macd(df)
            
            return [
                {
                    "date": str(row.get('date', '')),
                    "macd": float(row['macd']) if pd.notna(row.get('macd')) else None,
                    "macd_signal": float(row['macd_signal']) if pd.notna(row.get('macd_signal')) else None,
                    "macd_hist": float(row['macd_hist']) if pd.notna(row.get('macd_hist')) else None
                }
                for _, row in result_df.iterrows()
            ]
        except Exception as e:
            logger.error(f"计算 MACD 失败：{e}")
            return []
    
    async def _calculate_rsi(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """计算 RSI"""
        try:
            result_df = self.indicators_manager.calculate_rsi(
                df, periods=[6, 12, 24], price_column='close'
            )
            
            return [
                {
                    "date": str(row.get('date', '')),
                    "rsi6": float(row['rsi6']) if pd.notna(row.get('rsi6')) else None,
                    "rsi12": float(row['rsi12']) if pd.notna(row.get('rsi12')) else None,
                    "rsi24": float(row['rsi24']) if pd.notna(row.get('rsi24')) else None
                }
                for _, row in result_df.iterrows()
            ]
        except Exception as e:
            logger.error(f"计算 RSI 失败：{e}")
            return []
    
    async def _calculate_kdj(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """计算 KDJ"""
        try:
            result_df = self.indicators_manager.calculate_kdj(df)
            
            return [
                {
                    "date": str(row.get('date', '')),
                    "kdj_k": float(row['kdj_k']) if pd.notna(row.get('kdj_k')) else None,
                    "kdj_d": float(row['kdj_d']) if pd.notna(row.get('kdj_d')) else None,
                    "kdj_j": float(row['kdj_j']) if pd.notna(row.get('kdj_j')) else None
                }
                for _, row in result_df.iterrows()
            ]
        except Exception as e:
            logger.error(f"计算 KDJ 失败：{e}")
            return []
    
    async def _calculate_boll(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """计算布林带"""
        try:
            result_df = self.indicators_manager.calculate_bollinger_bands(df)
            
            return [
                {
                    "date": str(row.get('date', '')),
                    "boll_upper": float(row['bb_upper']) if pd.notna(row.get('bb_upper')) else None,
                    "boll_middle": float(row['bb_middle']) if pd.notna(row.get('bb_middle')) else None,
                    "boll_lower": float(row['bb_lower']) if pd.notna(row.get('bb_lower')) else None
                }
                for _, row in result_df.iterrows()
            ]
        except Exception as e:
            logger.error(f"计算 BOLL 失败：{e}")
            return []
    
    async def _calculate_atr(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """计算 ATR"""
        try:
            result_df = self.indicators_manager.calculate_atr(df, period=14)
            
            return [
                {
                    "date": str(row.get('date', '')),
                    "atr": float(row['atr']) if pd.notna(row.get('atr')) else None
                }
                for _, row in result_df.iterrows()
            ]
        except Exception as e:
            logger.error(f"计算 ATR 失败：{e}")
            return []
    
    def _format_kline_data(self, kline_data: List[Any]) -> List[Dict[str, Any]]:
        """格式化 K 线数据"""
        formatted = []
        
        for item in kline_data:
            if isinstance(item, dict):
                formatted.append({
                    "date": item.get('date', ''),
                    "open": float(item.get('open', 0)),
                    "high": float(item.get('high', 0)),
                    "low": float(item.get('low', 0)),
                    "close": float(item.get('close', 0)),
                    "volume": float(item.get('volume', 0)),
                    "amount": float(item.get('amount', 0)) if item.get('amount') else None,
                    "turnover_rate": float(item.get('turnover_rate', 0)) if item.get('turnover_rate') else None
                })
        
        return formatted


# 全局服务实例
chart_data_service = ChartDataService(prefer_talib=False)
