from typing import Optional, List, Dict, Any
import baostock as bs
import pandas as pd
from loguru import logger

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData,
    BillboardEntry,
    BoardInfo,
    ShareholderInfo,
    IndexComponent,
    CapitalFlowItem,
    MarketQuote
)


class BaostockAdapter(BaseDataAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._logged_in = False
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.BAOSTOCK
    
    async def initialize(self) -> bool:
        try:
            lg = bs.login()
            if lg.error_code != "0":
                logger.error(f"Baostock登录失败: {lg.error_msg}")
                return False
            self._logged_in = True
            self._is_initialized = True
            logger.info("Baostock适配器初始化成功")
            return True
        except Exception as e:
            logger.error(f"Baostock适配器初始化失败: {e}")
            return False
    
    async def close(self) -> None:
        if self._logged_in:
            bs.logout()
            self._logged_in = False
        self._is_initialized = False
        logger.info("Baostock适配器已关闭")
    
    def _get_bs_code(self, code: str) -> str:
        if code.startswith("6"):
            return f"sh.{code}"
        else:
            return f"sz.{code}"
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        try:
            rs = bs.query_stock_basic()
            stocks = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                code = row[0]
                if code.startswith(("sh.6", "sz.0", "sz.3")):
                    stocks.append(StockBasicInfo(
                        code=code.split(".")[1],
                        name=row[1],
                        market=code.split(".")[0].upper(),
                        industry=row[7] if len(row) > 7 else None,
                        list_date=row[4] if len(row) > 4 else None
                    ))
            return stocks
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        try:
            bs_code = self._get_bs_code(code)
            rs = bs.query_stock_basic(code=bs_code)
            if rs.error_code != "0":
                return None
            
            row = rs.get_row_data()
            return StockBasicInfo(
                code=code,
                name=row[1],
                market=code.split(".")[0].upper() if "." in code else ("SH" if code.startswith("6") else "SZ"),
                industry=row[7] if len(row) > 7 else None,
                list_date=row[4] if len(row) > 4 else None
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
            bs_code = self._get_bs_code(code)
            
            adjust_map = {
                "qfq": "2",
                "hfq": "1",
                "": "3"
            }
            adjust_flag = adjust_map.get(adjust, "2")
            
            start = start_date.replace("-", "") if start_date else "19900101"
            end = end_date.replace("-", "") if end_date else "20991231"
            
            rs = bs.query_history_k_data_plus(
                bs_code,
                "date,code,open,high,low,close,volume,amount,turn",
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag=adjust_flag
            )
            
            klines = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(row[0]),
                    open=float(row[2]) if row[2] else 0,
                    high=float(row[3]) if row[3] else 0,
                    low=float(row[4]) if row[4] else 0,
                    close=float(row[5]) if row[5] else 0,
                    volume=float(row[6]) if row[6] else 0,
                    amount=float(row[7]) if row[7] else None,
                    turnover_rate=float(row[8]) if len(row) > 8 and row[8] else None
                ))
            return klines
        except Exception as e:
            logger.error(f"获取K线数据失败 {code}: {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        return {}
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        try:
            rs = bs.query_stock_industry()
            sectors = {}
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                industry = row[1]
                if industry not in sectors:
                    sectors[industry] = SectorInfo(
                        code=industry,
                        name=industry,
                        sector_type="industry"
                    )
            return list(sectors.values())
        except Exception as e:
            logger.error(f"获取板块列表失败: {e}")
            return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        try:
            rs = bs.query_stock_industry(industry=sector_code)
            codes = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                code = row[0].split(".")[1] if "." in row[0] else row[0]
                codes.append(code)
            return codes
        except Exception as e:
            logger.error(f"获取板块成分股失败 {sector_code}: {e}")
            return []
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        return []
    
    async def get_daily_billboard(self, trade_date: Optional[str] = None) -> List[BillboardEntry]:
        """获取龙虎榜单数据（暂不支持）"""
        logger.warning(f"Baostock 暂不支持获取龙虎榜数据 {trade_date}")
        return []
    
    async def get_belong_board(self, code: str) -> List[BoardInfo]:
        """获取股票所属板块（暂不支持）"""
        logger.warning(f"Baostock 暂不支持获取股票所属板块 {code}")
        return []
    
    async def get_members(self, index_code: str) -> List[IndexComponent]:
        """获取指数成分股（暂不支持）"""
        logger.warning(f"Baostock 暂不支持获取指数成分股 {index_code}")
        return []
    
    async def get_today_bill(self, trade_date: Optional[str] = None) -> List[CapitalFlowItem]:
        """获取当日资金流向（暂不支持）"""
        logger.warning(f"Baostock 暂不支持获取当日资金流向 {trade_date}")
        return []
    
    async def get_history_bill(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[CapitalFlowItem]:
        """获取历史资金流向（暂不支持）"""
        logger.warning(f"Baostock 暂不支持获取历史资金流向 {code}")
        return []
    
    async def get_top10_stock_holder_info(self, code: str) -> List[ShareholderInfo]:
        """获取前十大股东信息（暂不支持）"""
        logger.warning(f"Baostock 暂不支持获取前十大股东信息 {code}")
        return []
    
    async def get_market_realtime_quotes(self, market_types: Optional[List[str]] = None) -> List[MarketQuote]:
        """获取市场实时行情（暂不支持）"""
        logger.warning(f"Baostock 暂不支持获取市场实时行情")
        return []
