from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from loguru import logger

from app.adapters import data_source_manager
from app.services.cache_service import cache_service
from app.models.schemas import MarketMoneyflowData


class MoneyflowService:
    def __init__(self):
        self._cache_ttl = 300
    
    async def get_market_moneyflow(
        self,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        use_cache: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取大盘资金流向数据（使用 cache_service 统一管理）
        
        Args:
            trade_date: 交易日期（YYYYMMDD 格式）
            start_date: 开始日期（YYYYMMDD 格式）
            end_date: 结束日期（YYYYMMDD 格式）
            use_cache: 是否使用缓存
            
        Returns:
            大盘资金流向数据列表
        """
        cache_key = f"market_moneyflow_{trade_date}_{start_date}_{end_date}"
        
        if use_cache:
            # 使用 cache_service 统一管理
            cached = await cache_service.get("moneyflow", cache_key)
            if cached:
                logger.debug(f"从缓存获取大盘资金流向数据")
                return cached
        
        try:
            adapter = data_source_manager.get_adapter()
            
            if hasattr(adapter, 'get_market_moneyflow_dc'):
                data = await adapter.get_market_moneyflow_dc(
                    trade_date=trade_date,
                    start_date=start_date,
                    end_date=end_date
                )
            else:
                logger.warning(f"当前数据源 {type(adapter).__name__} 不支持大盘资金流向")
                data = []
            
            if data:
                # 使用 cache_service 保存
                await cache_service.set("moneyflow", cache_key, data, ttl=self._cache_ttl)
            
            return data
            
        except Exception as e:
            logger.error(f"获取大盘资金流向数据失败：{e}")
            return []
    
    async def get_latest_market_moneyflow(self, days: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近N天的大盘资金流向数据
        
        Args:
            days: 天数，默认5天
            
        Returns:
            大盘资金流向数据列表
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days * 2)
        
        data = await self.get_market_moneyflow(
            start_date=start_date.strftime("%Y%m%d"),
            end_date=end_date.strftime("%Y%m%d")
        )
        
        if data:
            data = sorted(data, key=lambda x: x.get("trade_date", ""), reverse=True)[:days]
        
        return data
    
    async def get_moneyflow_summary(self) -> Dict[str, Any]:
        """
        获取资金流向摘要（用于首页展示）
        
        Returns:
            包含最新资金流向数据的摘要
        """
        try:
            latest_data = await self.get_latest_market_moneyflow(days=1)
            
            if not latest_data:
                return {
                    "success": False,
                    "message": "暂无资金流向数据",
                    "data": None
                }
            
            latest = latest_data[0]
            
            def format_amount(amount: Optional[float]) -> str:
                if amount is None:
                    return "--"
                if abs(amount) >= 1e8:
                    return f"{amount / 1e8:.2f}亿"
                elif abs(amount) >= 1e4:
                    return f"{amount / 1e4:.2f}万"
                else:
                    return f"{amount:.2f}"
            
            summary = {
                "trade_date": latest.get("trade_date"),
                "close_sh": latest.get("close_sh"),
                "pct_change_sh": latest.get("pct_change_sh"),
                "close_sz": latest.get("close_sz"),
                "pct_change_sz": latest.get("pct_change_sz"),
                "main_net_in": {
                    "amount": latest.get("net_amount"),
                    "amount_str": format_amount(latest.get("net_amount")),
                    "rate": latest.get("net_amount_rate")
                },
                "super_large": {
                    "amount": latest.get("buy_elg_amount"),
                    "amount_str": format_amount(latest.get("buy_elg_amount")),
                    "rate": latest.get("buy_elg_amount_rate")
                },
                "large": {
                    "amount": latest.get("buy_lg_amount"),
                    "amount_str": format_amount(latest.get("buy_lg_amount")),
                    "rate": latest.get("buy_lg_amount_rate")
                },
                "medium": {
                    "amount": latest.get("buy_md_amount"),
                    "amount_str": format_amount(latest.get("buy_md_amount")),
                    "rate": latest.get("buy_md_amount_rate")
                },
                "small": {
                    "amount": latest.get("buy_sm_amount"),
                    "amount_str": format_amount(latest.get("buy_sm_amount")),
                    "rate": latest.get("buy_sm_amount_rate")
                }
            }
            
            return {
                "success": True,
                "message": "获取成功",
                "data": summary
            }
            
        except Exception as e:
            logger.error(f"获取资金流向摘要失败：{e}")
            return {
                "success": False,
                "message": str(e),
                "data": None
            }
    
    async def get_moneyflow_trend(self, days: int = 10) -> Dict[str, Any]:
        """
        获取资金流向趋势数据（用于图表展示）
        
        Args:
            days: 天数，默认10天
            
        Returns:
            包含日期和资金流向数据的趋势数据
        """
        try:
            data = await self.get_latest_market_moneyflow(days=days)
            
            if not data:
                return {
                    "success": False,
                    "message": "暂无资金流向数据",
                    "dates": [],
                    "main_net_in": [],
                    "super_large": [],
                    "large": [],
                    "medium": [],
                    "small": []
                }
            
            data = sorted(data, key=lambda x: x.get("trade_date", ""))
            
            return {
                "success": True,
                "message": "获取成功",
                "dates": [d.get("trade_date", "") for d in data],
                "main_net_in": [d.get("net_amount") for d in data],
                "super_large": [d.get("buy_elg_amount") for d in data],
                "large": [d.get("buy_lg_amount") for d in data],
                "medium": [d.get("buy_md_amount") for d in data],
                "small": [d.get("buy_sm_amount") for d in data]
            }
            
        except Exception as e:
            logger.error(f"获取资金流向趋势失败：{e}")
            return {
                "success": False,
                "message": str(e),
                "dates": [],
                "main_net_in": [],
                "super_large": [],
                "large": [],
                "medium": [],
                "small": []
            }


moneyflow_service = MoneyflowService()
