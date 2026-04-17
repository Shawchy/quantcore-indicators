"""
资金流向数据采集器

从 Backend 数据适配器获取资金流向相关数据，
并转换为 Alpha 因子可用的格式。
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from loguru import logger


@dataclass
class FundFlowData:
    """资金流向数据"""
    symbol: str
    trade_date: date
    
    # 主力资金
    main_net_inflow: float = 0.0  # 主力净流入（万元）
    super_large_net: float = 0.0  # 超大单净流入
    large_order_net: float = 0.0  # 大单净流入
    medium_order_net: float = 0.0  # 中单净流入
    small_order_net: float = 0.0  # 小单净流入
    
    # 北向资金
    northbound_net_inflow: float = 0.0  # 北向净流入
    
    # 龙虎榜
    lhb_net_buy: float = 0.0  # 龙虎榜净买入
    lhb_buy_amount: float = 0.0  # 龙虎榜买入额
    lhb_sell_amount: float = 0.0  # 龙虎榜卖出额
    
    # 融资融券
    margin_balance: float = 0.0  # 融资余额变化
    securities_lending: float = 0.0  # 融券余额变化


class FundFlowCrawler:
    """
    资金流向数据采集器
    
    从 Backend 的数据适配器获取资金流向数据，
    并转换为因子格式。
    
    数据来源：
    - StockIndividualFundFlow (个股资金流)
    - CapitalFlowItem (北向资金)
    - StockLhbDetailEm (龙虎榜)
    
    使用示例：
        crawler = FundFlowCrawler()
        
        # 初始化连接
        await crawler.initialize()
        
        # 获取个股资金流
        flow_data = await crawler.get_stock_fund_flow(
            "000001",
            start_date="2024-01-01"
        )
        
        # 计算资金流向因子
        factors = await crawler.calculate_fund_flow_factors(["000001", "600000"])
    """
    
    def __init__(self):
        self._adapter = None
        self._initialized = False
        
        # 缓存
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = timedelta(minutes=30)
    
    async def initialize(self):
        """初始化数据源连接"""
        if self._initialized:
            return
        
        try:
            from backend.app.adapters import DataSourceFactory
            
            factory = DataSourceFactory()
            self._adapter = factory.create_adapter("efinance")
            
            if hasattr(self._adapter, "initialize"):
                await self._adapter.initialize()
            
            self._initialized = True
            logger.info("FundFlowCrawler 初始化完成")
            
        except Exception as e:
            logger.error(f"FundFlowCrawler 初始化失败: {e}")
            raise
    
    def _get_cache_key(self, symbol: str, data_type: str) -> str:
        return f"{symbol}:{data_type}"
    
    def _is_cache_valid(self, key: str) -> bool:
        if key not in self._cache:
            return False
        cached_time, _ = self._cache[key]
        return datetime.now() - cached_time < self._cache_ttl
    
    async def get_stock_fund_flow(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """
        获取个股资金流向历史数据
        
        Args:
            symbol: 股票代码 (如 "000001" 或 "SH.600000")
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 资金流向明细
        """
        cache_key = self._get_cache_key(symbol, "stock_fund_flow")
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key][0]
        
        if not self._initialized:
            await self.initialize()
        
        try:
            # 尝试使用 Backend 适配器
            if hasattr(self._adapter, "get_history_bill"):
                raw_data = await self._adapter.get_history_bill(
                    symbol, start_date, end_date
                )
                
                records = []
                for item in raw_data:
                    records.append({
                        "date": getattr(item, "trade_date", ""),
                        "main_net_amount": getattr(item, "main_net_amount", 0) or 0,
                        "super_large_net": getattr(item, "super_large_net", 0) or 0,
                        "large_order_net": getattr(item, "large_net", 0) or 0,
                        "medium_order_net": getattr(item, "medium_net", 0) or 0,
                        "small_order_net": getattr(item, "small_net", 0) or 0,
                    })
                
                df = pd.DataFrame(records)
                
                if "date" in df.columns and len(df) > 0:
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.set_index("date").sort_index()
                
                self._cache[cache_key] = (df, datetime.now())
                return df
            
            else:
                logger.warning(f"适配器不支持 get_history_bill，返回空数据")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取 {symbol} 资金流向失败: {e}")
            return pd.DataFrame()
    
    async def get_northbound_flow(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> pd.DataFrame:
        """获取北向资金流向"""
        cache_key = self._get_cache_key("northbound", "flow")
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key][0]
        
        try:
            if hasattr(self._adapter, "get_northbound_data"):
                data = await self._adapter.get_northbound_data(start_date, end_date)
                
                if isinstance(data, list) and len(data) > 0:
                    df = pd.DataFrame([{
                        "date": getattr(d, "trade_date", d.date),
                        "sh_net_buy": getattr(d, "sh_net_buy", 0),
                        "sz_net_buy": getattr(d, "sz_net_buy", 0),
                        "total_net": getattr(d, "total_net", 0)
                    } for d in data])
                    
                    if "date" in df.columns:
                        df["date"] = pd.to_datetime(df["date"])
                        df = df.set_index("date").sort_index()
                    
                    self._cache[cache_key] = (df, datetime.now())
                    return df
                
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取北向资金失败: {e}")
            return pd.DataFrame()
    
    async def get_lhb_data(
        self,
        start_date: Optional[str] = None,
        limit: int = 100
    ) -> pd.DataFrame:
        """获取龙虎榜数据"""
        cache_key = self._get_cache_key("lhb", f"{start_date}_{limit}")
        
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key][0]
        
        try:
            if hasattr(self._adapter, "get_daily_billboard"):
                data = await self._adapter.get_daily_billboard(start_date)
                
                records = []
                for item in data[:limit]:
                    records.append({
                        "date": getattr(item, "trade_date", ""),
                        "code": getattr(item, "code", ""),
                        "name": getattr(item, "name", ""),
                        "net_amount": getattr(item, "net_amount", 0) or 0,
                        "buy_amount": getattr(item, "buy_amount", 0) or 0,
                        "sell_amount": getattr(item, "sell_amount", 0) or 0,
                        "reason": getattr(item, "reason", ""),
                    })
                
                df = pd.DataFrame(records)
                
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                    df = df.set_index("date").sort_index()
                
                self._cache[cache_key] = (df, datetime.now())
                return df
                
            return pd.DataFrame()
            
        except Exception as e:
            logger.error(f"获取龙虎榜失败: {e}")
            return pd.DataFrame()
    
    async def calculate_fund_flow_factors(
        self,
        symbols: List[str],
        end_date: Optional[date] = None,
        lookback_days: int = 20
    ) -> Dict[str, Dict[str, float]]:
        """
        批量计算资金流向因子
        
        Args:
            symbols: 股票代码列表
            end_date: 截止日期
            lookback_days: 回看天数
            
        Returns:
            {symbol: {factor_name: factor_value}}
        """
        if end_date is None:
            end_date = date.today()
        
        all_factors = {}
        
        for symbol in symbols:
            try:
                flow_df = await self.get_stock_fund_flow(symbol)
                
                if flow_df.empty:
                    continue
                
                latest = flow_df.iloc[-1]
                recent = flow_df.tail(lookback_days)
                
                factors = {
                    "symbol": symbol,
                    "date": str(end_date),
                    
                    # 主力净流入因子（标准化）
                    "main_net_inflow_ratio": latest.get("main_net_amount", 0) / (
                        abs(latest.get("main_net_amount", 0)) + 10000
                    ),
                    
                    # 大单占比因子
                    "large_order_ratio": (
                        (latest.get("super_large_net", 0) + 
                         latest.get("large_order_net", 0)) / 
                        abs(latest.get("main_net_amount", 0) + 1)
                    ),
                    
                    # 近5日主力净流入趋势
                    "main_5d_sum": recent["main_net_amount"].sum(),
                    
                    # 近20日主力净流入趋势
                    "main_20d_sum": recent["main_net_amount"].sum(),
                    
                    # 主力净流入波动率
                    "main_volatility": recent["main_net_amount"].std(),
                    
                    # 超大单占比
                    "super_large_ratio": latest.get("super_large_net", 0) / (
                        abs(latest.get("main_net_amount", 0)) + 1
                    ),
                }
                
                all_factors[symbol] = factors
                
            except Exception as e:
                logger.debug(f"计算{symbol}资金因子失败: {e}")
                continue
        
        return all_factors
    
    async def get_fund_flow_summary(
        self,
        symbols: List[str]
    ) -> Dict[str, Any]:
        """获取资金流向摘要统计"""
        summary = {
            "top_inflows": [],  # 净买入最多
            "top_outflows": [],  # 净卖出最多
            "most_active": [],  # 最活跃交易
            "northbound_status": {},  # 北向状态
        }
        
        flows_by_symbol = {}
        
        for symbol in symbols:
            try:
                flow_df = await self.get_stock_fund_flow(symbol)
                
                if flow_df.empty or "main_net_amount" not in flow_df.columns:
                    continue
                
                total_inflow = flow_df["main_net_amount"][flow_df["main_net_amount"] > 0].sum()
                total_outflow = abs(flow_df["main_net_amount"][flow_df["main_net_amount"] < 0].sum())
                
                flows_by_symbol[symbol] = {
                    "net_inflow": flow_df["main_net_amount"].sum(),
                    "total_buy": total_inflow,
                    "total_sell": total_outflow,
                    "n_positive_days": (flow_df["main_net_amount"] > 0).sum(),
                    "n_negative_days": (flow_df["main_net_amount"] < 0).sum(),
                }
                
            except Exception:
                continue
        
        # 排序
        sorted_by_net = sorted(flows_by_symbol.items(), 
                              key=lambda x: x[1]["net_inflow"], reverse=True)
        
        summary["top_inflows"] = sorted_by_net[:10]
        summary["top_outflows"] = sorted_by_net[-10:]
        summary["symbols_analyzed"] = len(flows_by_symbol)
        
        return summary
