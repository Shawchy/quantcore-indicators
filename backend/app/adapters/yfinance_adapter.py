from typing import Optional, List, Dict, Any
import yfinance as yf
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


class YFinanceAdapter(BaseDataAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.YFINANCE
    
    async def initialize(self) -> bool:
        try:
            self._is_initialized = True
            logger.info("YFinance适配器初始化成功")
            return True
        except Exception as e:
            logger.error(f"YFinance适配器初始化失败: {e}")
            return False
    
    async def close(self) -> None:
        self._is_initialized = False
        logger.info("YFinance适配器已关闭")
    
    def _get_yf_symbol(self, code: str) -> str:
        if code.startswith("6"):
            return f"{code}.SS"
        else:
            return f"{code}.SZ"
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        logger.warning("YFinance不支持获取A股列表")
        return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        try:
            symbol = self._get_yf_symbol(code)
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return StockBasicInfo(
                code=code,
                name=info.get("longName", info.get("shortName", "")),
                market="SH" if code.startswith("6") else "SZ",
                industry=info.get("industry"),
                sector=info.get("sector"),
                total_shares=info.get("sharesOutstanding")
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
            symbol = self._get_yf_symbol(code)
            ticker = yf.Ticker(symbol)
            
            auto_adjust = adjust in ["qfq", "hfq"]
            df = ticker.history(
                start=start_date,
                end=end_date,
                auto_adjust=auto_adjust
            )
            
            klines = []
            for index, row in df.iterrows():
                klines.append(KLineData(
                    code=code,
                    date=index.strftime("%Y-%m-%d"),
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]),
                    amount=None
                ))
            return klines
        except Exception as e:
            logger.error(f"获取K线数据失败 {code}: {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        try:
            symbol = self._get_yf_symbol(code)
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "code": code,
                "name": info.get("longName", ""),
                "price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
                "change": info.get("regularMarketChange", 0),
                "change_pct": info.get("regularMarketChangePercent", 0),
                "volume": info.get("regularMarketVolume", 0),
                "high": info.get("dayHigh", 0),
                "low": info.get("dayLow", 0),
                "open": info.get("regularMarketOpen", 0),
                "prev_close": info.get("previousClose", 0)
            }
        except Exception as e:
            logger.error(f"获取实时行情失败 {code}: {e}")
            return {}
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        logger.warning("YFinance不支持获取A股板块列表")
        return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        logger.warning("YFinance不支持获取板块成分股")
        return []
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        try:
            symbol = self._get_yf_symbol(code)
            ticker = yf.Ticker(symbol)
            
            major_holders = ticker.major_holders
            institutional_holders = ticker.institutional_holders
            
            return [ChipData(
                code=code,
                date=pd.Timestamp.now().strftime("%Y-%m-%d"),
                top10_holders_ratio=major_holders.iloc[0, 0] if not major_holders.empty else None
            )]
        except Exception as e:
            logger.error(f"获取筹码数据失败 {code}: {e}")
            return []
