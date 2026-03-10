from typing import Optional, List, Dict, Any
import akshare as ak
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


class AkShareAdapter(BaseDataAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.AKSHARE
    
    async def initialize(self) -> bool:
        try:
            self._is_initialized = True
            logger.info("AkShare适配器初始化成功")
            return True
        except Exception as e:
            logger.error(f"AkShare适配器初始化失败: {e}")
            return False
    
    async def close(self) -> None:
        self._is_initialized = False
        logger.info("AkShare适配器已关闭")
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        try:
            df = ak.stock_zh_a_spot_em()
            stocks = []
            for _, row in df.iterrows():
                code = str(row["代码"])
                name = str(row["名称"])
                market_tag = "SH" if code.startswith("6") else "SZ"
                stocks.append(StockBasicInfo(
                    code=code,
                    name=name,
                    market=market_tag
                ))
            return stocks
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        try:
            df = ak.stock_individual_info_em(symbol=code)
            info_dict = dict(zip(df["item"], df["value"]))
            market_tag = "SH" if code.startswith("6") else "SZ"
            return StockBasicInfo(
                code=code,
                name=info_dict.get("股票简称", ""),
                market=market_tag,
                industry=info_dict.get("行业"),
                list_date=info_dict.get("上市时间"),
                total_shares=float(info_dict.get("总市值", 0)) / 100000000 if info_dict.get("总市值") else None
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
            adjust_map = {
                "qfq": "qfq",
                "hfq": "hfq",
                "": ""
            }
            adjust_type = adjust_map.get(adjust, "qfq")
            
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.replace("-", "") if start_date else "19900101",
                end_date=end_date.replace("-", "") if end_date else "20991231",
                adjust=adjust_type
            )
            
            klines = []
            for _, row in df.iterrows():
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row["日期"])),
                    open=float(row["开盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    close=float(row["收盘"]),
                    volume=float(row["成交量"]),
                    amount=float(row["成交额"]) if "成交额" in row else None,
                    turnover_rate=float(row["换手率"]) if "换手率" in row else None
                ))
            return klines
        except Exception as e:
            logger.error(f"获取K线数据失败 {code}: {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        try:
            df = ak.stock_zh_a_spot_em()
            row = df[df["代码"] == code]
            if row.empty:
                return {}
            
            row = row.iloc[0]
            return {
                "code": code,
                "name": row["名称"],
                "price": float(row["最新价"]),
                "change": float(row["涨跌额"]),
                "change_pct": float(row["涨跌幅"]),
                "volume": float(row["成交量"]),
                "amount": float(row["成交额"]),
                "high": float(row["最高"]),
                "low": float(row["最低"]),
                "open": float(row["今开"]),
                "prev_close": float(row["昨收"]),
                "turnover_rate": float(row["换手率"]) if "换手率" in row else None
            }
        except Exception as e:
            logger.error(f"获取实时行情失败 {code}: {e}")
            return {}
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        try:
            if sector_type == "industry":
                df = ak.stock_board_industry_name_em()
            elif sector_type == "concept":
                df = ak.stock_board_concept_name_em()
            else:
                df = ak.stock_board_industry_name_em()
            
            sectors = []
            for _, row in df.iterrows():
                sectors.append(SectorInfo(
                    code=str(row["板块名称"]),
                    name=str(row["板块名称"]),
                    sector_type=sector_type,
                    change_pct=float(row["涨跌幅"]) if "涨跌幅" in row else None,
                    volume=float(row["总市值"]) if "总市值" in row else None
                ))
            return sectors
        except Exception as e:
            logger.error(f"获取板块列表失败: {e}")
            return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        try:
            df = ak.stock_board_industry_cons_em(symbol=sector_code)
            return df["代码"].tolist()
        except Exception as e:
            logger.error(f"获取板块成分股失败 {sector_code}: {e}")
            return []
    
    async def get_sector_ranking(
        self,
        sector_type: str = "industry",
        sort_by: str = "change_pct",
        limit: int = 20
    ) -> List[SectorInfo]:
        try:
            if sector_type == "industry":
                df = ak.stock_board_industry_name_em()
            else:
                df = ak.stock_board_concept_name_em()
            
            sort_col = "涨跌幅" if sort_by == "change_pct" else "总市值"
            df = df.sort_values(by=sort_col, ascending=False)
            df = df.head(limit)
            
            sectors = []
            for _, row in df.iterrows():
                sectors.append(SectorInfo(
                    code=str(row["板块名称"]),
                    name=str(row["板块名称"]),
                    sector_type=sector_type,
                    change_pct=float(row["涨跌幅"]) if "涨跌幅" in row else None
                ))
            return sectors
        except Exception as e:
            logger.error(f"获取板块排行失败: {e}")
            return []
    
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        try:
            df = ak.stock_zh_a_gdhs(symbol=code)
            if df.empty:
                return []
            
            # 动态检测字段名
            date_column = None
            for col in ['股东户数统计截止日', '统计截止日期', '截止日期', '日期']:
                if col in df.columns:
                    date_column = col
                    break
            
            if not date_column:
                logger.warning(f"未找到日期字段，可用字段：{df.columns.tolist()}")
                return []
            
            chip_data = []
            for _, row in df.iterrows():
                date = str(row[date_column])
                if start_date and date < start_date:
                    continue
                if end_date and date > end_date:
                    continue
                
                # 动态检测股东户数字段
                count_column = None
                for col in ['股东户数', '股东人数']:
                    if col in df.columns:
                        count_column = col
                        break
                
                if not count_column:
                    continue
                
                chip_data.append(ChipData(
                    code=code,
                    date=date,
                    shareholder_count=float(row[count_column]),
                    avg_shares_per_holder=float(row["户均持股数量"]) if "户均持股数量" in row else None
                ))
            return chip_data
        except Exception as e:
            logger.error(f"获取筹码数据失败 {code}: {e}")
            return []
    
    async def get_stock_financial(self, code: str) -> Dict[str, Any]:
        try:
            df = ak.stock_financial_abstract_ths(symbol=code, indicator="按报告期")
            return df.to_dict("records")
        except Exception as e:
            logger.error(f"获取财务数据失败 {code}: {e}")
            return {}
