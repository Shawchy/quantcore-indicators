from typing import Optional, List, Dict, Any
import baostock as bs
import pandas as pd
from loguru import logger
from datetime import datetime

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
    MarketQuote,
    FinancialPerformance
)


class BaostockAdapter(BaseDataAdapter):
    """
    BaoStock 证券宝数据适配器
    
    特点:
    - 完全免费，无需注册
    - 支持日/周/月 K 线及分钟线数据
    - 数据范围：1990-12-19 至今
    - 支持不复权、前复权、后复权
    
    复权说明:
    - BaoStock 使用"涨跌幅复权法"进行复权
    - 优点：可以计算出资金收益率，确保初始投入的资金运用率为 100%
    - 既不会因为分红而导致投资减少，也不会因为配股导致投资增加
    - 与同花顺、通达信等软件可能存在差异
    
    官网：http://www.baostock.com
    文档：http://baostock.com/baostock/index.html
    """
    
    # 复权类型映射
    ADJUST_MAP = {
        "qfq": "2",      # 前复权（推荐）
        "hfq": "1",      # 后复权
        "": "3",         # 不复权
        "none": "3"      # 不复权
    }
    
    # 日期格式映射
    DATE_FORMAT_MAP = {
        "YYYYMMDD": "%Y%m%d",
        "YYYY-MM-DD": "%Y-%m-%d"
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._logged_in = False
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.BAOSTOCK
    
    async def initialize(self) -> bool:
        """
        初始化 BaoStock 适配器
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("正在登录 BaoStock 系统...")
            lg = bs.login()
            
            if lg.error_code != "0":
                logger.error(f"BaoStock 登录失败 - 错误代码：{lg.error_code}, 错误信息：{lg.error_msg}")
                return False
            
            self._logged_in = True
            self._is_initialized = True
            logger.info("BaoStock 适配器初始化成功 ✓")
            return True
            
        except Exception as e:
            logger.error(f"BaoStock 适配器初始化失败：{e}")
            return False
    
    async def close(self) -> None:
        """关闭 BaoStock 连接，释放资源"""
        try:
            if self._logged_in:
                lg = bs.logout()
                if lg.error_code != "0":
                    logger.warning(f"BaoStock 登出失败：{lg.error_msg}")
                else:
                    logger.info("BaoStock 已安全登出")
            self._logged_in = False
            self._is_initialized = False
        except Exception as e:
            logger.error(f"关闭 BaoStock 连接时出错：{e}")
    
    def _get_bs_code(self, code: str) -> str:
        """
        转换股票代码为 BaoStock 格式
        
        Args:
            code: 6 位数字股票代码
            
        Returns:
            str: BaoStock 格式的代码 (sh.xxxxxx 或 sz.xxxxxx)
        """
        if not code:
            raise ValueError("股票代码不能为空")
        
        # 如果已经是 BaoStock 格式，直接返回
        if "." in code:
            return code
        
        # 根据股票代码前缀判断市场
        if code.startswith("6"):
            return f"sh.{code}"
        elif code.startswith("0") or code.startswith("3"):
            return f"sz.{code}"
        else:
            # 默认按深圳市场处理
            return f"sz.{code}"
    
    def _parse_date(self, date_str: str) -> str:
        """
        解析日期字符串为标准格式
        
        Args:
            date_str: 日期字符串 (YYYYMMDD 或 YYYY-MM-DD)
            
        Returns:
            str: YYYY-MM-DD 格式的日期
        """
        if not date_str:
            return ""
        
        # 如果已经是 YYYY-MM-DD 格式，直接返回
        if "-" in date_str:
            return date_str
        
        # 转换 YYYYMMDD 为 YYYY-MM-DD
        try:
            if len(date_str) == 8:
                return f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            else:
                return date_str
        except Exception:
            return date_str
    
    def _format_date_for_bs(self, date_str: str) -> str:
        """
        格式化日期为 BaoStock 要求的格式 (YYYYMMDD)
        
        Args:
            date_str: 日期字符串 (YYYY-MM-DD 或 YYYYMMDD)
            
        Returns:
            str: YYYYMMDD 格式的日期
        """
        if not date_str:
            return ""
        
        # 如果已经是 YYYYMMDD 格式，直接返回
        if len(date_str) == 8 and date_str.isdigit():
            return date_str
        
        # 转换 YYYY-MM-DD 为 YYYYMMDD
        try:
            if "-" in date_str:
                return date_str.replace("-", "")
            else:
                return date_str
        except Exception:
            return date_str
    
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        """
        获取 A 股股票列表
        
        Args:
            market: 市场代码 (可选)
            
        Returns:
            List[StockBasicInfo]: 股票列表
        """
        try:
            logger.debug("正在获取股票列表...")
            rs = bs.query_stock_basic()
            
            if rs.error_code != "0":
                logger.error(f"获取股票列表失败：{rs.error_msg}")
                return []
            
            stocks = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                code = row[0]  # 证券代码 (sh.xxxxxx 或 sz.xxxxxx)
                
                # 筛选 A 股
                if code.startswith(("sh.6", "sz.0", "sz.3")):
                    stocks.append(StockBasicInfo(
                        code=code.split(".")[1],  # 提取 6 位数字代码
                        name=row[1],  # 证券名称
                        market=code.split(".")[0].upper(),  # SH 或 SZ
                        industry=row[7] if len(row) > 7 else None,  # 所属行业
                        list_date=row[4] if len(row) > 4 else None  # 上市日期
                    ))
            
            logger.info(f"成功获取 {len(stocks)} 只股票信息")
            return stocks
            
        except Exception as e:
            logger.error(f"获取股票列表失败：{e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        """
        获取股票基本信息
        
        Args:
            code: 股票代码
            
        Returns:
            Optional[StockBasicInfo]: 股票信息，获取失败返回 None
        """
        try:
            bs_code = self._get_bs_code(code)
            logger.debug(f"正在获取股票信息：{code} -> {bs_code}")
            
            rs = bs.query_stock_basic(code=bs_code)
            
            if rs.error_code != "0":
                logger.warning(f"获取股票信息失败 {code}: {rs.error_msg}")
                return None
            
            row = rs.get_row_data()
            if not row:
                logger.warning(f"未找到股票信息：{code}")
                return None
            
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
        """
        获取日 K 线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD 或 YYYYMMDD)
            end_date: 结束日期 (YYYY-MM-DD 或 YYYYMMDD)
            adjust: 复权类型 (qfq=前复权，hfq=后复权，""=不复权)
            
        Returns:
            List[KLineData]: K 线数据列表
        """
        return await self._get_kline_data(
            code=code,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
            frequency="d"
        )
    
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """
        获取周 K 线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            
        Returns:
            List[KLineData]: 周 K 线数据列表
        """
        return await self._get_kline_data(
            code=code,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
            frequency="w"
        )
    
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """
        获取月 K 线数据
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            
        Returns:
            List[KLineData]: 月 K 线数据列表
        """
        return await self._get_kline_data(
            code=code,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust,
            frequency="m"
        )
    
    async def _get_kline_data(
        self,
        code: str,
        start_date: Optional[str],
        end_date: Optional[str],
        adjust: str,
        frequency: str
    ) -> List[KLineData]:
        """
        获取 K 线数据的通用方法
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
            frequency: 频率 (d=日，w=周，m=月)
            
        Returns:
            List[KLineData]: K 线数据列表
        """
        try:
            bs_code = self._get_bs_code(code)
            adjust_flag = self.ADJUST_MAP.get(adjust, "2")
            
            # 格式化日期
            start = self._format_date_for_bs(start_date) if start_date else "19900101"
            end = self._format_date_for_bs(end_date) if end_date else datetime.now().strftime("%Y%m%d")
            
            # 根据频率选择不同的字段
            if frequency in ["d", "w", "m"]:
                fields = "date,code,open,high,low,close,volume,amount,turn"
            else:
                fields = "date,time,code,open,high,low,close,volume,amount,adjustflag"
            
            logger.debug(f"获取 K 线数据：{code}, 频率：{frequency}, 范围：{start} ~ {end}, 复权：{adjust}")
            
            rs = bs.query_history_k_data_plus(
                security_code=bs_code,
                fields=fields,
                start_date=start,
                end_date=end,
                frequency=frequency,
                adjustflag=adjust_flag
            )
            
            if rs.error_code != "0":
                logger.error(f"获取 K 线数据失败 {code}: {rs.error_msg}")
                return []
            
            klines = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 处理换手率（空字符串转为 0）
                turnover_rate = None
                if len(row) > 8 and row[8]:
                    try:
                        turnover_rate = float(row[8]) if row[8] else None
                    except ValueError:
                        turnover_rate = None
                
                klines.append(KLineData(
                    code=code,
                    date=self._parse_date(row[0]),
                    open=float(row[2]) if row[2] else 0.0,
                    high=float(row[3]) if row[3] else 0.0,
                    low=float(row[4]) if row[4] else 0.0,
                    close=float(row[5]) if row[5] else 0.0,
                    volume=float(row[6]) if row[6] else 0.0,
                    amount=float(row[7]) if row[7] else None,
                    turnover_rate=turnover_rate
                ))
            
            logger.info(f"成功获取 {code} 的 K 线数据 {len(klines)} 条 (频率：{frequency})")
            return klines
            
        except Exception as e:
            logger.error(f"获取 K 线数据失败 {code}: {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        """
        获取实时行情（BaoStock 暂不支持）
        
        Args:
            code: 股票代码
            
        Returns:
            Dict[str, Any]: 空字典
        """
        logger.debug(f"BaoStock 不支持实时行情查询：{code}")
        return {}
    
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        """
        获取行业板块列表
        
        Args:
            sector_type: 板块类型
            
        Returns:
            List[SectorInfo]: 板块列表
        """
        try:
            logger.debug(f"正在获取行业板块列表...")
            rs = bs.query_stock_industry()
            
            if rs.error_code != "0":
                logger.error(f"获取板块列表失败：{rs.error_msg}")
                return []
            
            sectors = {}
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                industry = row[1]
                
                if industry and industry not in sectors:
                    sectors[industry] = SectorInfo(
                        code=industry,
                        name=industry,
                        sector_type="industry"
                    )
            
            logger.info(f"成功获取 {len(sectors)} 个行业板块")
            return list(sectors.values())
            
        except Exception as e:
            logger.error(f"获取板块列表失败：{e}")
            return []
    
    async def get_sector_components(self, sector_code: str) -> List[str]:
        """
        获取板块成分股
        
        Args:
            sector_code: 板块代码
            
        Returns:
            List[str]: 成分股代码列表
        """
        try:
            logger.debug(f"正在获取板块成分股：{sector_code}")
            rs = bs.query_stock_industry(industry=sector_code)
            
            if rs.error_code != "0":
                logger.error(f"获取板块成分股失败 {sector_code}: {rs.error_msg}")
                return []
            
            codes = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                bs_code = row[0]
                # 提取 6 位数字代码
                code = bs_code.split(".")[1] if "." in bs_code else bs_code
                codes.append(code)
            
            logger.info(f"板块 {sector_code} 包含 {len(codes)} 只成分股")
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
        """
        获取筹码数据（BaoStock 暂不支持）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[ChipData]: 空列表
        """
        logger.debug(f"BaoStock 不支持筹码数据查询：{code}")
        return []
    
    async def get_daily_billboard(self, trade_date: Optional[str] = None) -> List[BillboardEntry]:
        """
        获取龙虎榜单数据（BaoStock 暂不支持）
        
        Args:
            trade_date: 交易日期
            
        Returns:
            List[BillboardEntry]: 空列表
        """
        logger.debug(f"BaoStock 不支持龙虎榜数据查询：{trade_date}")
        return []
    
    async def get_belong_board(self, code: str) -> List[BoardInfo]:
        """
        获取股票所属板块（BaoStock 暂不支持）
        
        Args:
            code: 股票代码
            
        Returns:
            List[BoardInfo]: 空列表
        """
        logger.debug(f"BaoStock 不支持查询股票所属板块：{code}")
        return []
    
    async def get_members(self, index_code: str) -> List[IndexComponent]:
        """
        获取指数成分股（BaoStock 暂不支持）
        
        Args:
            index_code: 指数代码
            
        Returns:
            List[IndexComponent]: 空列表
        """
        logger.debug(f"BaoStock 不支持查询指数成分股：{index_code}")
        return []
    
    async def get_today_bill(self, trade_date: Optional[str] = None) -> List[CapitalFlowItem]:
        """
        获取当日资金流向（BaoStock 暂不支持）
        
        Args:
            trade_date: 交易日期
            
        Returns:
            List[CapitalFlowItem]: 空列表
        """
        logger.debug(f"BaoStock 不支持当日资金流向查询：{trade_date}")
        return []
    
    async def get_history_bill(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[CapitalFlowItem]:
        """
        获取历史资金流向（BaoStock 暂不支持）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            List[CapitalFlowItem]: 空列表
        """
        logger.debug(f"BaoStock 不支持历史资金流向查询：{code}")
        return []
    
    async def get_top10_stock_holder_info(self, code: str) -> List[ShareholderInfo]:
        """
        获取前十大股东信息（BaoStock 暂不支持）
        
        Args:
            code: 股票代码
            
        Returns:
            List[ShareholderInfo]: 空列表
        """
        logger.debug(f"BaoStock 不支持查询前十大股东信息：{code}")
        return []
    
    async def get_market_realtime_quotes(self, market_types: Optional[List[str]] = None) -> List[MarketQuote]:
        """
        获取市场实时行情（BaoStock 暂不支持）
        
        Args:
            market_types: 市场类型列表
            
        Returns:
            List[MarketQuote]: 空列表
        """
        logger.debug(f"BaoStock 不支持市场实时行情查询")
        return []
    
    async def get_financial_performance(
        self,
        code: str,
        report_date: Optional[str] = None,
        report_type: str = "quarterly"
    ) -> List[FinancialPerformance]:
        """
        获取财务业绩数据（BaoStock 暂不支持）
        
        Args:
            code: 股票代码
            report_date: 报告日期
            report_type: 报告类型
            
        Returns:
            List[FinancialPerformance]: 空列表
        """
        logger.debug(f"BaoStock 不支持财务业绩数据查询：{code}")
        return []
    
    async def get_index_kline(
        self,
        index_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        frequency: str = "d"
    ) -> List[KLineData]:
        """
        获取指数 K 线数据
        
        支持的指数类型:
        1. 综合指数 - sh.000001 上证指数，sz.399106 深证综指
        2. 规模指数 - sh.000016 上证 50，sh.000300 沪深 300，sh.000905 中证 500
        3. 一级行业指数 - sh.000037 上证医药，sz.399433 国证交运
        4. 二级行业指数 - sh.000952 300 地产，sz.399951 300 银行
        5. 策略指数 - sh.000050 50 等权，sh.000982 500 等权
        6. 成长指数 - sz.399376 小盘成长
        7. 价值指数 - sh.000029 180 价值
        8. 主题指数 - sh.000015 红利指数，sh.000063 上证周期
        9. 基金指数 - sh.000011 上证基金指数
        10. 债券指数 - sh.000012 上证国债指数
        
        Args:
            index_code: 指数代码（格式：sh.xxxxxx 或 sz.xxxxxx）
            start_date: 开始日期 (YYYY-MM-DD 或 YYYYMMDD)
            end_date: 结束日期 (YYYY-MM-DD 或 YYYYMMDD)
            frequency: 频率 (d=日，w=周，m=月，指数不支持分钟线)
            
        Returns:
            List[KLineData]: 指数 K 线数据列表
            
        注意:
        - 指数没有分钟线数据
        - 指数数据从 2006-01-01 开始
        - 指数不需要复权（adjustflag 固定为 3）
        """
        try:
            # 格式化指数代码（确保是 BaoStock 格式）
            if "." not in index_code:
                # 尝试自动添加市场前缀
                if index_code.startswith("6") or index_code.startswith("000"):
                    bs_code = f"sh.{index_code}"
                elif index_code.startswith("399") or index_code.startswith("0"):
                    bs_code = f"sz.{index_code}"
                else:
                    bs_code = f"sh.{index_code}"  # 默认上海
            else:
                bs_code = index_code
            
            # 格式化日期
            start = self._format_date_for_bs(start_date) if start_date else "20060101"
            end = self._format_date_for_bs(end_date) if end_date else datetime.now().strftime("%Y%m%d")
            
            # 指数日线指标字段（不包含 turn 换手率）
            if frequency in ["d", "w", "m"]:
                fields = "date,code,open,high,low,close,preclose,volume,amount,pctChg"
            else:
                logger.warning(f"指数不支持 {frequency} 分钟线数据，使用日线")
                frequency = "d"
                fields = "date,code,open,high,low,close,preclose,volume,amount,pctChg"
            
            logger.debug(f"获取指数 K 线数据：{bs_code}, 频率：{frequency}, 范围：{start} ~ {end}")
            
            # 查询指数 K 线数据（指数不需要复权）
            rs = bs.query_history_k_data_plus(
                security_code=bs_code,
                fields=fields,
                start_date=start,
                end_date=end,
                frequency=frequency,
                adjustflag="3"  # 指数不复权
            )
            
            if rs.error_code != "0":
                logger.error(f"获取指数 K 线数据失败 {bs_code}: {rs.error_msg}")
                return []
            
            klines = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 提取股票代码（去掉市场前缀）
                code = bs_code.split(".")[1] if "." in bs_code else bs_code
                
                klines.append(KLineData(
                    code=code,
                    date=self._parse_date(row[0]),
                    open=float(row[2]) if row[2] else 0.0,
                    high=float(row[3]) if row[3] else 0.0,
                    low=float(row[4]) if row[4] else 0.0,
                    close=float(row[5]) if row[5] else 0.0,
                    volume=float(row[7]) if row[7] else 0.0,
                    amount=float(row[8]) if row[8] else None,
                    turnover_rate=None  # 指数没有换手率
                ))
            
            logger.info(f"成功获取指数 {bs_code} 的 K 线数据 {len(klines)} 条 (频率：{frequency})")
            return klines
            
        except Exception as e:
            logger.error(f"获取指数 K 线数据失败 {index_code}: {e}")
            return []
    
    async def get_valuation_indicators(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取沪深 A 股估值指标（日频）
        
        支持的估值指标:
        - peTTM: 滚动市盈率 = (收盘价/每股盈余 TTM)
        - psTTM: 滚动市销率 = (收盘价/每股销售额 TTM)
        - pcfNcfTTM: 滚动市现率 = (收盘价/每股现金流 TTM)
        - pbMRQ: 市净率 = (收盘价/每股净资产)
        
        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD 或 YYYYMMDD)
            end_date: 结束日期 (YYYY-MM-DD 或 YYYYMMDD)
            
        Returns:
            List[Dict[str, Any]]: 估值指标数据列表
            
        注意:
        - 仅支持日线，不支持周线、月线
        - 指数未提供估值数据
        - 数据从 2006-01-01 开始
        """
        try:
            bs_code = self._get_bs_code(code)
            
            # 格式化日期
            start = self._format_date_for_bs(start_date) if start_date else "20060101"
            end = self._format_date_for_bs(end_date) if end_date else datetime.now().strftime("%Y%m%d")
            
            # 估值指标字段（必须包含 close 收盘价）
            fields = "date,code,close,peTTM,pbMRQ,psTTM,pcfNcfTTM"
            
            logger.debug(f"获取估值指标：{bs_code}, 范围：{start} ~ {end}")
            
            # 查询估值指标数据（使用不复权）
            rs = bs.query_history_k_data_plus(
                security_code=bs_code,
                fields=fields,
                start_date=start,
                end_date=end,
                frequency="d",
                adjustflag="3"
            )
            
            if rs.error_code != "0":
                logger.error(f"获取估值指标失败 {bs_code}: {rs.error_msg}")
                return []
            
            indicators = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析估值指标
                indicator = {
                    "code": code,
                    "date": self._parse_date(row[0]),
                    "close": float(row[2]) if row[2] else None,
                    "pe_ttm": float(row[3]) if row[3] else None,      # 滚动市盈率
                    "pb_mrq": float(row[4]) if row[4] else None,      # 市净率
                    "ps_ttm": float(row[5]) if row[5] else None,      # 滚动市销率
                    "pcf_ncf_ttm": float(row[6]) if row[6] else None  # 滚动市现率
                }
                indicators.append(indicator)
            
            logger.info(f"成功获取 {bs_code} 的估值指标 {len(indicators)} 条")
            return indicators
            
        except Exception as e:
            logger.error(f"获取估值指标失败 {code}: {e}")
            return []
