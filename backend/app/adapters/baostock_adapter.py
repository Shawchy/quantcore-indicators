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
    ChipData
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
        """
        获取股票列表（包含所有基本信息）
        
        Returns:
            List[StockBasicInfo]: 股票列表，包含 code, name, market, type, status, 
                                 list_date, delist_date 等完整字段
        """
        try:
            rs = bs.query_stock_basic()
            stocks = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                code_full = row[0]  # sh.600000
                name = row[1]
                
                # 转换代码格式
                if '.' in code_full:
                    market_code, stock_code = code_full.split('.')
                    code = stock_code
                    market_tag = market_code.upper()
                else:
                    code = code_full
                    market_tag = 'UNKNOWN'
                
                # 解析其他字段
                list_date = row[2] if len(row) > 2 and row[2] else None
                delist_date = row[3] if len(row) > 3 and row[3] else None
                stock_type = int(row[4]) if len(row) > 4 and row[4] else 1
                status = int(row[5]) if len(row) > 5 and row[5] else 1
                
                stocks.append(StockBasicInfo(
                    code=code,
                    name=name,
                    market=market_tag,
                    type=stock_type,
                    status=status,
                    list_date=list_date,
                    delist_date=delist_date,
                    industry=None,  # Baostock 不提供行业信息
                    sector=None,
                    area=None,
                    total_shares=None,
                    float_shares=None
                ))
            
            logger.info(f"成功获取 {len(stocks)} 只股票信息")
            return stocks
        except Exception as e:
            logger.error(f"获取股票列表失败：{e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        """
        获取单只股票详细信息
        
        Args:
            code: 股票代码
            
        Returns:
            Optional[StockBasicInfo]: 股票详细信息，包含完整字段
        """
        try:
            bs_code = self._get_bs_code(code)
            rs = bs.query_stock_basic(code=bs_code)
            if rs.error_code != "0":
                logger.warning(f"获取股票信息失败 {code}: {rs.error_msg}")
                return None
            
            row = rs.get_row_data()
            code_full = row[0]
            name = row[1]
            
            # 转换代码格式
            if '.' in code_full:
                market_code, _ = code_full.split('.')
                market_tag = market_code.upper()
            else:
                market_tag = 'SH' if code.startswith('6') else 'SZ'
            
            # 解析其他字段
            list_date = row[2] if len(row) > 2 and row[2] else None
            delist_date = row[3] if len(row) > 3 and row[3] else None
            stock_type = int(row[4]) if len(row) > 4 and row[4] else 1
            status = int(row[5]) if len(row) > 5 and row[5] else 1
            
            return StockBasicInfo(
                code=code,
                name=name,
                market=market_tag,
                type=stock_type,
                status=status,
                list_date=list_date,
                delist_date=delist_date,
                industry=None,
                sector=None,
                area=None,
                total_shares=None,
                float_shares=None
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
