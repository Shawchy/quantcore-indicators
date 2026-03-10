from typing import Optional, List, Dict, Any
import tushare as ts
import pandas as pd
from loguru import logger

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData
)
from app.config import settings


class TushareAdapter(BaseDataAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._pro = None
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.TUSHARE
    
    async def initialize(self) -> bool:
        try:
            token = self.config.get("token") or settings.TUSHARE_TOKEN
            if not token:
                logger.warning("Tushare未配置token，跳过初始化")
                return False
            
            ts.set_token(token)
            self._pro = ts.pro_api()
            self._is_initialized = True
            logger.info("Tushare适配器初始化成功")
            return True
        except Exception as e:
            logger.error(f"Tushare适配器初始化失败: {e}")
            return False
    
    async def close(self) -> None:
        self._pro = None
        self._is_initialized = False
        logger.info("Tushare适配器已关闭")
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        try:
            df = self._pro.stock_basic(exchange="", list_status="L", fields="ts_code,symbol,name,area,industry,list_date")
            stocks = []
            for _, row in df.iterrows():
                code = row["symbol"]
                market_tag = row["ts_code"].split(".")[1] if "." in row["ts_code"] else ("SH" if code.startswith("6") else "SZ")
                stocks.append(StockBasicInfo(
                    code=code,
                    name=row["name"],
                    market=market_tag,
                    industry=row.get("industry"),
                    area=row.get("area"),
                    list_date=row.get("list_date")
                ))
            return stocks
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        try:
            ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
            df = self._pro.stock_basic(ts_code=ts_code, fields="ts_code,symbol,name,area,industry,list_date,total_mv,circ_mv")
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            return StockBasicInfo(
                code=code,
                name=row["name"],
                market=row["ts_code"].split(".")[1],
                industry=row.get("industry"),
                area=row.get("area"),
                list_date=row.get("list_date"),
                total_shares=row.get("total_mv"),
                float_shares=row.get("circ_mv")
            )
        except Exception as e:
            logger.error(f"获取股票信息失败 {code}: {e}")
            return None
    
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        try:
            ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
            
            adj_map = {
                "qfq": None,
                "hfq": "hfq",
                "": None
            }
            adj = adj_map.get(adjust)
            
            df = self._pro.daily(
                ts_code=ts_code,
                start_date=start_date.replace("-", "") if start_date else None,
                end_date=end_date.replace("-", "") if end_date else None,
                adj=adj
            )
            
            if adjust == "qfq":
                adj_factor = self._pro.adj_factor(ts_code=ts_code)
                df = df.merge(adj_factor, on="ts_code")
                df["adj_factor"] = df["adj_factor"].fillna(1)
                for col in ["open", "high", "low", "close"]:
                    df[col] = df[col] * df["adj_factor"]
            
            klines = []
            for _, row in df.sort_values("trade_date").iterrows():
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row["trade_date"])),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["vol"]),
                    amount=float(row["amount"]) * 1000 if "amount" in row else None
                ))
            return klines
        except Exception as e:
            logger.error(f"获取K线数据失败 {code}: {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        try:
            ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
            df = self._pro.daily(ts_code=ts_code, limit=1)
            
            if df.empty:
                return {}
            
            row = df.iloc[0]
            return {
                "code": code,
                "date": str(row["trade_date"]),
                "open": float(row["open"]),
                "high": float(row["high"]),
                "low": float(row["low"]),
                "close": float(row["close"]),
                "volume": float(row["vol"]),
                "amount": float(row["amount"]) * 1000
            }
        except Exception as e:
            logger.error(f"获取实时行情失败 {code}: {e}")
            return {}
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        try:
            df = self._pro.index_classify(level="L1", src="SW")
            sectors = []
            for _, row in df.iterrows():
                sectors.append(SectorInfo(
                    code=str(row["index_code"]),
                    name=row["industry_name"],
                    sector_type="industry"
                ))
            return sectors
        except Exception as e:
            logger.error(f"获取板块列表失败: {e}")
            return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        try:
            df = self._pro.index_member(index_code=sector_code)
            return [code.split(".")[0] for code in df["con_code"].tolist()]
        except Exception as e:
            logger.error(f"获取板块成分股失败 {sector_code}: {e}")
            return []
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        try:
            ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
            df = self._pro.stk_holdernumber(ts_code=ts_code)
            
            chip_data = []
            for _, row in df.iterrows():
                date = str(row["ann_date"])
                if start_date and date < start_date.replace("-", ""):
                    continue
                if end_date and date > end_date.replace("-", ""):
                    continue
                chip_data.append(ChipData(
                    code=code,
                    date=self.format_date(date),
                    shareholder_count=float(row["holder_num"])
                ))
            return chip_data
        except Exception as e:
            logger.error(f"获取筹码数据失败 {code}: {e}")
            return []
