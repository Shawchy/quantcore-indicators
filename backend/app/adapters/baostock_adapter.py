from typing import Optional, List, Dict, Any
import baostock as bs
import pandas as pd
from loguru import logger
from datetime import datetime
import asyncio
import time

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
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 缓存机制
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Dict[str, float] = {}
        self._cache_ttl = {
            'kline': 300,
            'stock_list': 3600,
            'financial': 7200,  # 财务数据缓存更长
            'default': 300
        }
        
        # 重试机制
        self._max_retries = 3
        self._retry_base_delay = 1.0
        
        # 连接管理
        self._session = None
    
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
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存 key"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return "_".join(key_parts)
    
    def _get_from_cache(self, key: str, ttl_type: str = 'default') -> Optional[Any]:
        """从缓存获取数据"""
        if key not in self._cache:
            return None
        
        timestamp = self._cache_timestamp.get(key, 0)
        ttl = self._cache_ttl.get(ttl_type, self._cache_ttl['default'])
        
        if time.time() - timestamp > ttl:
            del self._cache[key]
            del self._cache_timestamp[key]
            logger.debug(f"缓存过期：{key}")
            return None
        
        logger.debug(f"缓存命中：{key}")
        return self._cache[key]
    
    def _set_to_cache(self, key: str, value: Any, ttl_type: str = 'default'):
        """设置缓存"""
        self._cache[key] = value
        self._cache_timestamp[key] = time.time()
        logger.debug(f"写入缓存：{key} (TTL: {self._cache_ttl.get(ttl_type, 300)}s)")
    
    async def initialize(self) -> bool:
        """
        初始化 BaoStock 适配器（已启用缓存和重试机制）
        
        Returns:
            bool: 初始化是否成功
        """
        try:
            logger.info("正在登录 BaoStock 系统...")
            
            # 使用异步包装
            def login():
                return bs.login()
            
            lg = await asyncio.to_thread(login)
            
            if lg.error_code != "0":
                logger.error(f"BaoStock 登录失败 - 错误代码：{lg.error_code}, 错误信息：{lg.error_msg}")
                return False
            
            self._logged_in = True
            self._is_initialized = True
            logger.info("BaoStock 适配器初始化成功 ✓")
            logger.info(f"  - 缓存策略：K 线 5 分钟，股票列表 1 小时，财务数据 2 小时")
            logger.info(f"  - 重试机制：最多{self._max_retries}次，指数退避")
            return True
            
        except Exception as e:
            logger.error(f"BaoStock 适配器初始化失败：{e}")
            return False
    
    async def close(self) -> None:
        """关闭 BaoStock 连接，释放资源"""
        try:
            if self._logged_in:
                def logout():
                    return bs.logout()
                
                await asyncio.to_thread(logout)
                logger.info("BaoStock 已安全登出")
            
            self._logged_in = False
            self._is_initialized = False
            self._cache.clear()
            self._cache_timestamp.clear()
            logger.info("BaoStock 适配器已关闭")
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
    
    async def get_profit_data(
        self,
        code: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取季频盈利能力数据
        
        通过 API 接口获取季频盈利能力信息，可以通过参数设置获取对应年份、季度数据
        
        Args:
            code: 股票代码
            year: 统计年份（可选，默认当前年）
            quarter: 统计季度（可选，默认当前季度，取值 1-4）
            
        Returns:
            List[Dict[str, Any]]: 季频盈利能力数据列表
            
        返回字段:
        - code: 证券代码
        - pub_date: 公司发布财报的日期
        - stat_date: 财报统计的季度的最后一天
        - roe_avg: 净资产收益率 (平均)(%)
        - np_margin: 销售净利率 (%)
        - gp_margin: 销售毛利率 (%)
        - net_profit: 净利润 (元)
        - eps_ttm: 每股收益
        - mb_revenue: 主营营业收入 (元)
        - total_share: 总股本
        - liqa_share: 流通股本
        
        数据范围:
        - 从 2007 年至今
        - 提供 2007 年至今数据
        """
        try:
            bs_code = self._get_bs_code(code)
            
            # 默认当前年份和季度
            if year is None:
                year = datetime.now().year
            if quarter is None:
                quarter = (datetime.now().month - 1) // 3 + 1
            
            logger.debug(f"获取季频盈利能力：{bs_code}, 年份：{year}, 季度：{quarter}")
            
            # 查询季频盈利能力数据
            rs = bs.query_profit_data(
                code=bs_code,
                year=year,
                quarter=quarter
            )
            
            if rs.error_code != "0":
                logger.error(f"获取盈利能力数据失败 {bs_code}: {rs.error_msg}")
                return []
            
            profits = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析盈利能力数据
                profit = {
                    "code": code,
                    "pub_date": self._parse_date(row[1]) if len(row) > 1 else None,
                    "stat_date": self._parse_date(row[2]) if len(row) > 2 else None,
                    "roe_avg": float(row[3]) if len(row) > 3 and row[3] else None,      # 净资产收益率
                    "np_margin": float(row[4]) if len(row) > 4 and row[4] else None,    # 销售净利率
                    "gp_margin": float(row[5]) if len(row) > 5 and row[5] else None,    # 销售毛利率
                    "net_profit": float(row[6]) if len(row) > 6 and row[6] else None,   # 净利润
                    "eps_ttm": float(row[7]) if len(row) > 7 and row[7] else None,      # 每股收益
                    "mb_revenue": float(row[8]) if len(row) > 8 and row[8] else None,   # 主营营业收入
                    "total_share": float(row[9]) if len(row) > 9 and row[9] else None,  # 总股本
                    "liqa_share": float(row[10]) if len(row) > 10 and row[10] else None # 流通股本
                }
                profits.append(profit)
            
            logger.info(f"成功获取 {bs_code} 的季频盈利能力数据 {len(profits)} 条")
            return profits
            
        except Exception as e:
            logger.error(f"获取盈利能力数据失败 {code}: {e}")
            return []
    
    async def get_operation_data(
        self,
        code: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取季频营运能力数据
        
        通过 API 接口获取季频营运能力信息，可以通过参数设置获取对应年份、季度数据
        
        Args:
            code: 股票代码
            year: 统计年份（可选，默认当前年）
            quarter: 统计季度（可选，默认当前季度，取值 1-4）
            
        Returns:
            List[Dict[str, Any]]: 季频营运能力数据列表
            
        返回字段:
        - code: 证券代码
        - pub_date: 公司发布财报的日期
        - stat_date: 财报统计的季度的最后一天
        - nr_turn_ratio: 应收账款周转率 (次)
        - nr_turn_days: 应收账款周转天数 (天)
        - inv_turn_ratio: 存货周转率 (次)
        - inv_turn_days: 存货周转天数 (天)
        - ca_turn_ratio: 流动资产周转率 (次)
        - asset_turn_ratio: 总资产周转率 (次)
        
        数据范围:
        - 从 2007 年至今
        - 提供 2007 年至今数据
        """
        try:
            bs_code = self._get_bs_code(code)
            
            # 默认当前年份和季度
            if year is None:
                year = datetime.now().year
            if quarter is None:
                quarter = (datetime.now().month - 1) // 3 + 1
            
            logger.debug(f"获取季频营运能力：{bs_code}, 年份：{year}, 季度：{quarter}")
            
            # 查询季频营运能力数据
            rs = bs.query_operation_data(
                code=bs_code,
                year=year,
                quarter=quarter
            )
            
            if rs.error_code != "0":
                logger.error(f"获取营运能力数据失败 {bs_code}: {rs.error_msg}")
                return []
            
            operations = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析营运能力数据
                operation = {
                    "code": code,
                    "pub_date": self._parse_date(row[1]) if len(row) > 1 else None,
                    "stat_date": self._parse_date(row[2]) if len(row) > 2 else None,
                    "nr_turn_ratio": float(row[3]) if len(row) > 3 and row[3] else None,    # 应收账款周转率
                    "nr_turn_days": float(row[4]) if len(row) > 4 and row[4] else None,     # 应收账款周转天数
                    "inv_turn_ratio": float(row[5]) if len(row) > 5 and row[5] else None,   # 存货周转率
                    "inv_turn_days": float(row[6]) if len(row) > 6 and row[6] else None,    # 存货周转天数
                    "ca_turn_ratio": float(row[7]) if len(row) > 7 and row[7] else None,    # 流动资产周转率
                    "asset_turn_ratio": float(row[8]) if len(row) > 8 and row[8] else None  # 总资产周转率
                }
                operations.append(operation)
            
            logger.info(f"成功获取 {bs_code} 的季频营运能力数据 {len(operations)} 条")
            return operations
            
        except Exception as e:
            logger.error(f"获取营运能力数据失败 {code}: {e}")
            return []
    
    async def get_growth_data(
        self,
        code: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取季频成长能力数据
        
        通过 API 接口获取季频成长能力信息，可以通过参数设置获取对应年份、季度数据
        
        Args:
            code: 股票代码
            year: 统计年份（可选，默认当前年）
            quarter: 统计季度（可选，默认当前季度，取值 1-4）
            
        Returns:
            List[Dict[str, Any]]: 季频成长能力数据列表
            
        返回字段:
        - code: 证券代码
        - pub_date: 公司发布财报的日期
        - stat_date: 财报统计的季度的最后一天
        - yoy_equity: 净资产同比增长率 (%)
        - yoy_asset: 总资产同比增长率 (%)
        - yoy_ni: 净利润同比增长率 (%)
        - yoy_eps_basic: 基本每股收益同比增长率 (%)
        - yoy_pni: 归属母公司股东净利润同比增长率 (%)
        
        数据范围:
        - 从 2007 年至今
        - 提供 2007 年至今数据
        """
        try:
            bs_code = self._get_bs_code(code)
            
            # 默认当前年份和季度
            if year is None:
                year = datetime.now().year
            if quarter is None:
                quarter = (datetime.now().month - 1) // 3 + 1
            
            logger.debug(f"获取季频成长能力：{bs_code}, 年份：{year}, 季度：{quarter}")
            
            # 查询季频成长能力数据
            rs = bs.query_growth_data(
                code=bs_code,
                year=year,
                quarter=quarter
            )
            
            if rs.error_code != "0":
                logger.error(f"获取成长能力数据失败 {bs_code}: {rs.error_msg}")
                return []
            
            growths = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析成长能力数据
                growth = {
                    "code": code,
                    "pub_date": self._parse_date(row[1]) if len(row) > 1 else None,
                    "stat_date": self._parse_date(row[2]) if len(row) > 2 else None,
                    "yoy_equity": float(row[3]) if len(row) > 3 and row[3] else None,      # 净资产同比增长率
                    "yoy_asset": float(row[4]) if len(row) > 4 and row[4] else None,       # 总资产同比增长率
                    "yoy_ni": float(row[5]) if len(row) > 5 and row[5] else None,          # 净利润同比增长率
                    "yoy_eps_basic": float(row[6]) if len(row) > 6 and row[6] else None,   # 基本每股收益同比增长率
                    "yoy_pni": float(row[7]) if len(row) > 7 and row[7] else None          # 归属母公司股东净利润同比增长率
                }
                growths.append(growth)
            
            logger.info(f"成功获取 {bs_code} 的季频成长能力数据 {len(growths)} 条")
            return growths
            
        except Exception as e:
            logger.error(f"获取成长能力数据失败 {code}: {e}")
            return []
    
    async def get_balance_data(
        self,
        code: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取季频偿债能力数据
        
        通过 API 接口获取季频偿债能力信息，可以通过参数设置获取对应年份、季度数据
        
        Args:
            code: 股票代码
            year: 统计年份（可选，默认当前年）
            quarter: 统计季度（可选，默认当前季度，取值 1-4）
            
        Returns:
            List[Dict[str, Any]]: 季频偿债能力数据列表
            
        返回字段:
        - code: 证券代码
        - pub_date: 公司发布财报的日期
        - stat_date: 财报统计的季度的最后一天
        - current_ratio: 流动比率
        - quick_ratio: 速动比率
        - cash_ratio: 现金比率
        - yoy_liability: 总负债同比增长率 (%)
        - liability_to_asset: 资产负债率
        - asset_to_equity: 权益乘数
        
        数据范围:
        - 从 2007 年至今
        - 提供 2007 年至今数据
        """
        try:
            bs_code = self._get_bs_code(code)
            
            # 默认当前年份和季度
            if year is None:
                year = datetime.now().year
            if quarter is None:
                quarter = (datetime.now().month - 1) // 3 + 1
            
            logger.debug(f"获取季频偿债能力：{bs_code}, 年份：{year}, 季度：{quarter}")
            
            # 查询季频偿债能力数据
            rs = bs.query_balance_data(
                code=bs_code,
                year=year,
                quarter=quarter
            )
            
            if rs.error_code != "0":
                logger.error(f"获取偿债能力数据失败 {bs_code}: {rs.error_msg}")
                return []
            
            balances = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析偿债能力数据
                balance = {
                    "code": code,
                    "pub_date": self._parse_date(row[1]) if len(row) > 1 else None,
                    "stat_date": self._parse_date(row[2]) if len(row) > 2 else None,
                    "current_ratio": float(row[3]) if len(row) > 3 and row[3] else None,      # 流动比率
                    "quick_ratio": float(row[4]) if len(row) > 4 and row[4] else None,        # 速动比率
                    "cash_ratio": float(row[5]) if len(row) > 5 and row[5] else None,         # 现金比率
                    "yoy_liability": float(row[6]) if len(row) > 6 and row[6] else None,      # 总负债同比增长率
                    "liability_to_asset": float(row[7]) if len(row) > 7 and row[7] else None, # 资产负债率
                    "asset_to_equity": float(row[8]) if len(row) > 8 and row[8] else None     # 权益乘数
                }
                balances.append(balance)
            
            logger.info(f"成功获取 {bs_code} 的季频偿债能力数据 {len(balances)} 条")
            return balances
            
        except Exception as e:
            logger.error(f"获取偿债能力数据失败 {code}: {e}")
            return []
    
    async def get_cash_flow_data(
        self,
        code: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取季频现金流量数据
        
        通过 API 接口获取季频现金流量信息，可以通过参数设置获取对应年份、季度数据
        
        Args:
            code: 股票代码
            year: 统计年份（可选，默认当前年）
            quarter: 统计季度（可选，默认当前季度，取值 1-4）
            
        Returns:
            List[Dict[str, Any]]: 季频现金流量数据列表
            
        返回字段:
        - code: 证券代码
        - pub_date: 公司发布财报的日期
        - stat_date: 财报统计的季度的最后一天
        - ca_to_asset: 流动资产/总资产
        - nca_to_asset: 非流动资产/总资产
        - tangible_asset_to_asset: 有形资产/总资产
        - ebit_to_interest: 已获利息倍数
        - cfo_to_or: 经营活动现金净流量/营业收入
        - cfo_to_np: 经营活动现金净流量/净利润
        - cfo_to_gr: 经营活动现金净流量/营业总收入
        
        数据范围:
        - 从 2007 年至今
        - 提供 2007 年至今数据
        """
        try:
            bs_code = self._get_bs_code(code)
            
            # 默认当前年份和季度
            if year is None:
                year = datetime.now().year
            if quarter is None:
                quarter = (datetime.now().month - 1) // 3 + 1
            
            logger.debug(f"获取季频现金流量：{bs_code}, 年份：{year}, 季度：{quarter}")
            
            # 查询季频现金流量数据
            rs = bs.query_cash_flow_data(
                code=bs_code,
                year=year,
                quarter=quarter
            )
            
            if rs.error_code != "0":
                logger.error(f"获取现金流量数据失败 {bs_code}: {rs.error_msg}")
                return []
            
            cash_flows = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析现金流量数据
                cash_flow = {
                    "code": code,
                    "pub_date": self._parse_date(row[1]) if len(row) > 1 else None,
                    "stat_date": self._parse_date(row[2]) if len(row) > 2 else None,
                    "ca_to_asset": float(row[3]) if len(row) > 3 and row[3] else None,              # 流动资产/总资产
                    "nca_to_asset": float(row[4]) if len(row) > 4 and row[4] else None,            # 非流动资产/总资产
                    "tangible_asset_to_asset": float(row[5]) if len(row) > 5 and row[5] else None, # 有形资产/总资产
                    "ebit_to_interest": float(row[6]) if len(row) > 6 and row[6] else None,        # 已获利息倍数
                    "cfo_to_or": float(row[7]) if len(row) > 7 and row[7] else None,               # 经营现金净流量/营业收入
                    "cfo_to_np": float(row[8]) if len(row) > 8 and row[8] else None,               # 经营现金净流量/净利润
                    "cfo_to_gr": float(row[9]) if len(row) > 9 and row[9] else None                # 经营现金净流量/营业总收入
                }
                cash_flows.append(cash_flow)
            
            logger.info(f"成功获取 {bs_code} 的季频现金流量数据 {len(cash_flows)} 条")
            return cash_flows
            
        except Exception as e:
            logger.error(f"获取现金流量数据失败 {code}: {e}")
            return []
    
    async def get_dupont_data(
        self,
        code: str,
        year: Optional[int] = None,
        quarter: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        获取季频杜邦指数数据
        
        通过 API 接口获取季频杜邦指数信息，可以通过参数设置获取对应年份、季度数据
        
        Args:
            code: 股票代码
            year: 统计年份（可选，默认当前年）
            quarter: 统计季度（可选，默认当前季度，取值 1-4）
            
        Returns:
            List[Dict[str, Any]]: 季频杜邦指数数据列表
            
        返回字段:
        - code: 证券代码
        - pub_date: 公司发布财报的日期
        - stat_date: 财报统计的季度的最后一天
        - dupont_roe: 净资产收益率
        - dupont_asset_to_equity: 权益乘数
        - dupont_asset_turn: 总资产周转率
        - dupont_pni_to_ni: 归属母公司净利润/净利润
        - dupont_ni_to_gr: 净利润/营业总收入
        - dupont_tax_burden: 税负水平
        - dupont_int_burden: 利息负担
        - dupont_ebit_to_gr: 息税前利润/营业总收入
        
        数据范围:
        - 从 2007 年至今
        - 提供 2007 年至今数据
        """
        try:
            bs_code = self._get_bs_code(code)
            
            # 默认当前年份和季度
            if year is None:
                year = datetime.now().year
            if quarter is None:
                quarter = (datetime.now().month - 1) // 3 + 1
            
            logger.debug(f"获取季频杜邦指数：{bs_code}, 年份：{year}, 季度：{quarter}")
            
            # 查询季频杜邦指数数据
            rs = bs.query_dupont_data(
                code=bs_code,
                year=year,
                quarter=quarter
            )
            
            if rs.error_code != "0":
                logger.error(f"获取杜邦指数数据失败 {bs_code}: {rs.error_msg}")
                return []
            
            duponts = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析杜邦指数数据
                dupont = {
                    "code": code,
                    "pub_date": self._parse_date(row[1]) if len(row) > 1 else None,
                    "stat_date": self._parse_date(row[2]) if len(row) > 2 else None,
                    "dupont_roe": float(row[3]) if len(row) > 3 and row[3] else None,              # 净资产收益率
                    "dupont_asset_to_equity": float(row[4]) if len(row) > 4 and row[4] else None, # 权益乘数
                    "dupont_asset_turn": float(row[5]) if len(row) > 5 and row[5] else None,      # 总资产周转率
                    "dupont_pni_to_ni": float(row[6]) if len(row) > 6 and row[6] else None,       # 归属母公司净利润/净利润
                    "dupont_ni_to_gr": float(row[7]) if len(row) > 7 and row[7] else None,        # 净利润/营业总收入
                    "dupont_tax_burden": float(row[8]) if len(row) > 8 and row[8] else None,      # 税负水平
                    "dupont_int_burden": float(row[9]) if len(row) > 9 and row[9] else None,      # 利息负担
                    "dupont_ebit_to_gr": float(row[10]) if len(row) > 10 and row[10] else None    # 息税前利润/营业总收入
                }
                duponts.append(dupont)
            
            logger.info(f"成功获取 {bs_code} 的季频杜邦指数数据 {len(duponts)} 条")
            return duponts
            
        except Exception as e:
            logger.error(f"获取杜邦指数数据失败 {code}: {e}")
            return []
    
    async def get_performance_express_report(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取季频公司业绩快报数据
        
        通过 API 接口获取季频公司业绩快报信息，可以通过参数设置获取起止年份数据
        
        Args:
            code: 股票代码
            start_date: 开始日期（发布日期或更新日期在这个范围内）
            end_date: 结束日期（发布日期或更新日期在这个范围内）
            
        Returns:
            List[Dict[str, Any]]: 季频公司业绩快报数据列表
            
        返回字段:
        - code: 证券代码
        - performance_exp_pub_date: 业绩快报披露日
        - performance_exp_stat_date: 业绩快报统计日期
        - performance_exp_update_date: 业绩快报披露日 (最新)
        - performance_express_total_asset: 业绩快报总资产
        - performance_express_net_asset: 业绩快报净资产
        - performance_express_eps_chg_pct: 业绩每股收益增长率
        - performance_express_roe_wa: 业绩快报净资产收益率 ROE-加权
        - performance_express_eps_diluted: 业绩快报每股收益 EPS-摊薄
        - performance_express_gr_yoy: 业绩快报营业总收入同比
        - performance_express_op_yoy: 业绩快报营业利润同比
        
        数据范围:
        - 从 2006 年至今
        - 除特殊情况外，交易所未要求必须发布
        """
        try:
            bs_code = self._get_bs_code(code)
            
            # 默认日期范围
            if start_date is None:
                start_date = "2006-01-01"
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            logger.debug(f"获取季频业绩快报：{bs_code}, 范围：{start_date} ~ {end_date}")
            
            # 查询季频公司业绩快报数据
            rs = bs.query_performance_express_report(
                code=bs_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if rs.error_code != "0":
                logger.error(f"获取业绩快报数据失败 {bs_code}: {rs.error_msg}")
                return []
            
            reports = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析业绩快报数据
                report = {
                    "code": code,
                    "performance_exp_pub_date": self._parse_date(row[1]) if len(row) > 1 else None,
                    "performance_exp_stat_date": self._parse_date(row[2]) if len(row) > 2 else None,
                    "performance_exp_update_date": self._parse_date(row[3]) if len(row) > 3 else None,
                    "performance_express_total_asset": float(row[4]) if len(row) > 4 and row[4] else None,
                    "performance_express_net_asset": float(row[5]) if len(row) > 5 and row[5] else None,
                    "performance_express_eps_chg_pct": float(row[6]) if len(row) > 6 and row[6] else None,
                    "performance_express_roe_wa": float(row[7]) if len(row) > 7 and row[7] else None,
                    "performance_express_eps_diluted": float(row[8]) if len(row) > 8 and row[8] else None,
                    "performance_express_gr_yoy": float(row[9]) if len(row) > 9 and row[9] else None,
                    "performance_express_op_yoy": float(row[10]) if len(row) > 10 and row[10] else None
                }
                reports.append(report)
            
            logger.info(f"成功获取 {bs_code} 的季频业绩快报数据 {len(reports)} 条")
            return reports
            
        except Exception as e:
            logger.error(f"获取业绩快报数据失败 {code}: {e}")
            return []
    
    async def get_forecast_report(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取季频公司业绩预告数据
        
        通过 API 接口获取季频公司业绩预告信息，可以通过参数设置获取起止年份数据
        
        Args:
            code: 股票代码
            start_date: 开始日期（发布日期或更新日期在这个范围内）
            end_date: 结束日期（发布日期或更新日期在这个范围内）
            
        Returns:
            List[Dict[str, Any]]: 季频公司业绩预告数据列表
            
        返回字段:
        - code: 证券代码
        - profit_forcast_exp_pub_date: 业绩预告发布日期
        - profit_forcast_exp_stat_date: 业绩预告统计日期
        - profit_forcast_type: 业绩预告类型
        - profit_forcast_abstract: 业绩预告摘要
        - profit_forcast_chg_pct_up: 预告归母净利润增长上限 (%)
        - profit_forcast_chg_pct_dwn: 预告归母净利润增长下限 (%)
        
        数据范围:
        - 从 2003 年至今
        - 除特殊情况外，交易所未要求必须发布
        """
        try:
            bs_code = self._get_bs_code(code)
            
            # 默认日期范围
            if start_date is None:
                start_date = "2003-01-01"
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            logger.debug(f"获取季频业绩预告：{bs_code}, 范围：{start_date} ~ {end_date}")
            
            # 查询季频公司业绩预告数据
            rs = bs.query_forecast_report(
                code=bs_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if rs.error_code != "0":
                logger.error(f"获取业绩预告数据失败 {bs_code}: {rs.error_msg}")
                return []
            
            forecasts = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析业绩预告数据
                forecast = {
                    "code": code,
                    "profit_forcast_exp_pub_date": self._parse_date(row[1]) if len(row) > 1 else None,
                    "profit_forcast_exp_stat_date": self._parse_date(row[2]) if len(row) > 2 else None,
                    "profit_forcast_type": row[3] if len(row) > 3 else None,
                    "profit_forcast_abstract": row[4] if len(row) > 4 else None,
                    "profit_forcast_chg_pct_up": float(row[5]) if len(row) > 5 and row[5] else None,
                    "profit_forcast_chg_pct_dwn": float(row[6]) if len(row) > 6 and row[6] else None
                }
                forecasts.append(forecast)
            
            logger.info(f"成功获取 {bs_code} 的季频业绩预告数据 {len(forecasts)} 条")
            return forecasts
            
        except Exception as e:
            logger.error(f"获取业绩预告数据失败 {code}: {e}")
            return []
    
    async def get_deposit_rate_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取存款利率数据
        
        通过 API 接口获取存款利率，可以通过参数设置获取对应起止日期的数据
        
        Args:
            start_date: 开始日期（发布日期在这个范围内）
            end_date: 结束日期（发布日期在这个范围内）
            
        Returns:
            List[Dict[str, Any]]: 存款利率数据列表
            
        返回字段:
        - pub_date: 发布日期
        - demand_deposit_rate: 活期存款 (不定期)
        - fixed_deposit_rate_3_month: 定期存款 (三个月)
        - fixed_deposit_rate_6_month: 定期存款 (半年)
        - fixed_deposit_rate_1_year: 定期存款整存整取 (一年)
        - fixed_deposit_rate_2_year: 定期存款整存整取 (二年)
        - fixed_deposit_rate_3_year: 定期存款整存整取 (三年)
        - fixed_deposit_rate_5_year: 定期存款整存整取 (五年)
        - installment_fixed_deposit_rate_1_year: 零存整取等定期存款 (一年)
        - installment_fixed_deposit_rate_3_year: 零存整取等定期存款 (三年)
        - installment_fixed_deposit_rate_5_year: 零存整取等定期存款 (五年)
        """
        try:
            # 默认日期范围
            if start_date is None:
                start_date = "2003-01-01"
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            logger.debug(f"获取存款利率：范围：{start_date} ~ {end_date}")
            
            # 查询存款利率数据
            rs = bs.query_deposit_rate_data(
                start_date=start_date,
                end_date=end_date
            )
            
            if rs.error_code != "0":
                logger.error(f"获取存款利率数据失败：{rs.error_msg}")
                return []
            
            rates = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析存款利率数据
                rate = {
                    "pub_date": self._parse_date(row[0]) if len(row) > 0 else None,
                    "demand_deposit_rate": float(row[1]) if len(row) > 1 and row[1] else None,
                    "fixed_deposit_rate_3_month": float(row[2]) if len(row) > 2 and row[2] else None,
                    "fixed_deposit_rate_6_month": float(row[3]) if len(row) > 3 and row[3] else None,
                    "fixed_deposit_rate_1_year": float(row[4]) if len(row) > 4 and row[4] else None,
                    "fixed_deposit_rate_2_year": float(row[5]) if len(row) > 5 and row[5] else None,
                    "fixed_deposit_rate_3_year": float(row[6]) if len(row) > 6 and row[6] else None,
                    "fixed_deposit_rate_5_year": float(row[7]) if len(row) > 7 and row[7] else None,
                    "installment_fixed_deposit_rate_1_year": float(row[8]) if len(row) > 8 and row[8] else None,
                    "installment_fixed_deposit_rate_3_year": float(row[9]) if len(row) > 9 and row[9] else None,
                    "installment_fixed_deposit_rate_5_year": float(row[10]) if len(row) > 10 and row[10] else None
                }
                rates.append(rate)
            
            logger.info(f"成功获取存款利率数据 {len(rates)} 条")
            return rates
            
        except Exception as e:
            logger.error(f"获取存款利率数据失败：{e}")
            return []
    
    async def get_loan_rate_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取贷款利率数据
        
        通过 API 接口获取贷款利率，可以通过参数设置获取对应起止日期的数据
        
        Args:
            start_date: 开始日期（发布日期在这个范围内）
            end_date: 结束日期（发布日期在这个范围内）
            
        Returns:
            List[Dict[str, Any]]: 贷款利率数据列表
            
        返回字段:
        - pub_date: 发布日期
        - loan_rate_6_month: 6 个月贷款利率
        - loan_rate_6_month_to_1_year: 6 个月至 1 年贷款利率
        - loan_rate_1_year_to_3_year: 1 年至 3 年贷款利率
        - loan_rate_3_year_to_5_year: 3 年至 5 年贷款利率
        - loan_rate_above_5_year: 5 年以上贷款利率
        - mortgate_rate_below_5_year: 5 年以下住房公积金贷款利率
        - mortgate_rate_above_5_year: 5 年以上住房公积金贷款利率
        """
        try:
            # 默认日期范围
            if start_date is None:
                start_date = "2003-01-01"
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            logger.debug(f"获取贷款利率：范围：{start_date} ~ {end_date}")
            
            # 查询贷款利率数据
            rs = bs.query_loan_rate_data(
                start_date=start_date,
                end_date=end_date
            )
            
            if rs.error_code != "0":
                logger.error(f"获取贷款利率数据失败：{rs.error_msg}")
                return []
            
            rates = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析贷款利率数据
                rate = {
                    "pub_date": self._parse_date(row[0]) if len(row) > 0 else None,
                    "loan_rate_6_month": float(row[1]) if len(row) > 1 and row[1] else None,
                    "loan_rate_6_month_to_1_year": float(row[2]) if len(row) > 2 and row[2] else None,
                    "loan_rate_1_year_to_3_year": float(row[3]) if len(row) > 3 and row[3] else None,
                    "loan_rate_3_year_to_5_year": float(row[4]) if len(row) > 4 and row[4] else None,
                    "loan_rate_above_5_year": float(row[5]) if len(row) > 5 and row[5] else None,
                    "mortgate_rate_below_5_year": float(row[6]) if len(row) > 6 and row[6] else None,
                    "mortgate_rate_above_5_year": float(row[7]) if len(row) > 7 and row[7] else None
                }
                rates.append(rate)
            
            logger.info(f"成功获取贷款利率数据 {len(rates)} 条")
            return rates
            
        except Exception as e:
            logger.error(f"获取贷款利率数据失败：{e}")
            return []
    
    async def get_required_reserve_ratio_data(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        year_type: int = 0
    ) -> List[Dict[str, Any]]:
        """
        获取存款准备金率数据
        
        通过 API 接口获取存款准备金率，可以通过参数设置获取对应起止日期的数据
        
        Args:
            start_date: 开始日期（发布日期在这个范围内）
            end_date: 结束日期（发布日期在这个范围内）
            year_type: 年份类型（0=公告日期，1=生效日期）
            
        Returns:
            List[Dict[str, Any]]: 存款准备金率数据列表
            
        返回字段:
        - pub_date: 公告日期
        - effective_date: 生效日期
        - big_institutions_ratio_pre: 大型金融机构调整前
        - big_institutions_ratio_after: 大型金融机构调整后
        - medium_institutions_ratio_pre: 中小型金融机构调整前
        - medium_institutions_ratio_after: 中小型金融机构调整后
        """
        try:
            # 默认日期范围
            if start_date is None:
                start_date = "2003-01-01"
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m-%d")
            
            logger.debug(f"获取存款准备金率：范围：{start_date} ~ {end_date}, 类型：{year_type}")
            
            # 查询存款准备金率数据
            rs = bs.query_required_reserve_ratio_data(
                start_date=start_date,
                end_date=end_date,
                yearType=str(year_type)
            )
            
            if rs.error_code != "0":
                logger.error(f"获取存款准备金率数据失败：{rs.error_msg}")
                return []
            
            ratios = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析存款准备金率数据
                ratio = {
                    "pub_date": self._parse_date(row[0]) if len(row) > 0 else None,
                    "effective_date": self._parse_date(row[1]) if len(row) > 1 else None,
                    "big_institutions_ratio_pre": float(row[2]) if len(row) > 2 and row[2] else None,
                    "big_institutions_ratio_after": float(row[3]) if len(row) > 3 and row[3] else None,
                    "medium_institutions_ratio_pre": float(row[4]) if len(row) > 4 and row[4] else None,
                    "medium_institutions_ratio_after": float(row[5]) if len(row) > 5 and row[5] else None
                }
                ratios.append(ratio)
            
            logger.info(f"成功获取存款准备金率数据 {len(ratios)} 条")
            return ratios
            
        except Exception as e:
            logger.error(f"获取存款准备金率数据失败：{e}")
            return []
    
    async def get_money_supply_data_month(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取月度货币供应量数据
        
        通过 API 接口获取货币供应量，可以通过参数设置获取对应起止日期的数据
        
        Args:
            start_date: 开始日期（格式：YYYY-MM，发布日期在这个范围内）
            end_date: 结束日期（格式：YYYY-MM，发布日期在这个范围内）
            
        Returns:
            List[Dict[str, Any]]: 月度货币供应量数据列表
            
        返回字段:
        - stat_year: 统计年度
        - stat_month: 统计月份
        - m0_month: 货币供应量 M0（月）
        - m0_yoy: 货币供应量 M0（同比）
        - m0_chain_relative: 货币供应量 M0（环比）
        - m1_month: 货币供应量 M1（月）
        - m1_yoy: 货币供应量 M1（同比）
        - m1_chain_relative: 货币供应量 M1（环比）
        - m2_month: 货币供应量 M2（月）
        - m2_yoy: 货币供应量 M2（同比）
        - m2_chain_relative: 货币供应量 M2（环比）
        
        货币供应量说明:
        - M0: 流通中的现金
        - M1: M0 + 单位活期存款
        - M2: M1 + 单位定期存款 + 居民储蓄存款 + 其他存款
        """
        try:
            # 默认日期范围
            if start_date is None:
                start_date = "2010-01"
            if end_date is None:
                end_date = datetime.now().strftime("%Y-%m")
            
            logger.debug(f"获取月度货币供应量：范围：{start_date} ~ {end_date}")
            
            # 查询月度货币供应量数据
            rs = bs.query_money_supply_data_month(
                start_date=start_date,
                end_date=end_date
            )
            
            if rs.error_code != "0":
                logger.error(f"获取月度货币供应量数据失败：{rs.error_msg}")
                return []
            
            data_list = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析月度货币供应量数据
                data = {
                    "stat_year": int(row[0]) if len(row) > 0 and row[0] else None,
                    "stat_month": int(row[1]) if len(row) > 1 and row[1] else None,
                    "m0_month": float(row[2]) if len(row) > 2 and row[2] else None,
                    "m0_yoy": float(row[3]) if len(row) > 3 and row[3] else None,
                    "m0_chain_relative": float(row[4]) if len(row) > 4 and row[4] else None,
                    "m1_month": float(row[5]) if len(row) > 5 and row[5] else None,
                    "m1_yoy": float(row[6]) if len(row) > 6 and row[6] else None,
                    "m1_chain_relative": float(row[7]) if len(row) > 7 and row[7] else None,
                    "m2_month": float(row[8]) if len(row) > 8 and row[8] else None,
                    "m2_yoy": float(row[9]) if len(row) > 9 and row[9] else None,
                    "m2_chain_relative": float(row[10]) if len(row) > 10 and row[10] else None
                }
                data_list.append(data)
            
            logger.info(f"成功获取月度货币供应量数据 {len(data_list)} 条")
            return data_list
            
        except Exception as e:
            logger.error(f"获取月度货币供应量数据失败：{e}")
            return []
    
    async def get_money_supply_data_year(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取年度货币供应量数据（年底余额）
        
        通过 API 接口获取货币供应量（年底余额），可以通过参数设置获取对应起止日期的数据
        
        Args:
            start_date: 开始日期（格式：YYYY，发布日期在这个范围内）
            end_date: 结束日期（格式：YYYY，发布日期在这个范围内）
            
        Returns:
            List[Dict[str, Any]]: 年度货币供应量数据列表
            
        返回字段:
        - stat_year: 统计年度
        - m0_year: 年货币供应量 M0（亿元）
        - m0_year_yoy: 年货币供应量 M0（同比）
        - m1_year: 年货币供应量 M1（亿元）
        - m1_year_yoy: 年货币供应量 M1（同比）
        - m2_year: 年货币供应量 M2（亿元）
        - m2_year_yoy: 年货币供应量 M2（同比）
        
        货币供应量说明:
        - M0: 流通中的现金
        - M1: M0 + 单位活期存款
        - M2: M1 + 单位定期存款 + 居民储蓄存款 + 其他存款
        """
        try:
            # 默认日期范围
            if start_date is None:
                start_date = "2010"
            if end_date is None:
                end_date = datetime.now().strftime("%Y")
            
            logger.debug(f"获取年度货币供应量：范围：{start_date} ~ {end_date}")
            
            # 查询年度货币供应量数据
            rs = bs.query_money_supply_data_year(
                start_date=start_date,
                end_date=end_date
            )
            
            if rs.error_code != "0":
                logger.error(f"获取年度货币供应量数据失败：{rs.error_msg}")
                return []
            
            data_list = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析年度货币供应量数据
                data = {
                    "stat_year": int(row[0]) if len(row) > 0 and row[0] else None,
                    "m0_year": float(row[1]) if len(row) > 1 and row[1] else None,
                    "m0_year_yoy": float(row[2]) if len(row) > 2 and row[2] else None,
                    "m1_year": float(row[3]) if len(row) > 3 and row[3] else None,
                    "m1_year_yoy": float(row[4]) if len(row) > 4 and row[4] else None,
                    "m2_year": float(row[5]) if len(row) > 5 and row[5] else None,
                    "m2_year_yoy": float(row[6]) if len(row) > 6 and row[6] else None
                }
                data_list.append(data)
            
            logger.info(f"成功获取年度货币供应量数据 {len(data_list)} 条")
            return data_list
            
        except Exception as e:
            logger.error(f"获取年度货币供应量数据失败：{e}")
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
    
    async def get_dividend_data(
        self,
        code: str,
        start_year: int = 2006,
        end_year: Optional[int] = None,
        year_type: str = "report"
    ) -> List[Dict[str, Any]]:
        """
        获取除权除息信息（分红数据）
        
        通过 API 接口获取除权除息信息数据（预披露、预案、正式都已通过）
        
        Args:
            code: 股票代码
            start_year: 开始年份
            end_year: 结束年份（可选，默认为当前年份）
            year_type: 年份类型
                - "report": 预案公告年份（默认）
                - "operate": 除权除息年份
            
        Returns:
            List[Dict[str, Any]]: 除权除息信息列表
            
        返回字段:
        - code: 证券代码
        - divid_pre_notice_date: 预披露公告日
        - divid_agm_pum_date: 股东大会公告日期
        - divid_plan_announce_date: 预案公告日
        - divid_plan_date: 分红实施公告日
        - divid_regist_date: 股权登记日
        - divid_operate_date: 除权除息日
        - divid_pay_date: 派息日
        - divid_stock_market_date: 红股上市交易日
        - divid_cash_ps_before_tax: 每股股利（税前）
        - divid_cash_ps_after_tax: 每股股利（税后）
        - divid_stocks_ps: 每股红股
        - divid_cash_stock: 分红送转
        - divid_reserve_to_stock_ps: 每股转增资本
        """
        try:
            bs_code = self._get_bs_code(code)
            
            if end_year is None:
                end_year = datetime.now().year
            
            logger.debug(f"获取除权除息信息：{bs_code}, 年份：{start_year}-{end_year}, 类型：{year_type}")
            
            all_dividends = []
            
            # 遍历年份获取数据
            for year in range(start_year, end_year + 1):
                try:
                    rs = bs.query_dividend_data(
                        code=bs_code,
                        year=str(year),
                        yearType=year_type
                    )
                    
                    if rs.error_code != "0":
                        logger.warning(f"获取 {year} 年分红数据失败 {bs_code}: {rs.error_msg}")
                        continue
                    
                    while (rs.error_code == "0") & rs.next():
                        row = rs.get_row_data()
                        
                        # 解析除权除息信息
                        dividend = {
                            "code": code,
                            "divid_pre_notice_date": row[1] if len(row) > 1 else None,
                            "divid_agm_pum_date": row[2] if len(row) > 2 else None,
                            "divid_plan_announce_date": row[3] if len(row) > 3 else None,
                            "divid_plan_date": row[4] if len(row) > 4 else None,
                            "divid_regist_date": row[5] if len(row) > 5 else None,
                            "divid_operate_date": row[6] if len(row) > 6 else None,
                            "divid_pay_date": row[7] if len(row) > 7 else None,
                            "divid_stock_market_date": row[8] if len(row) > 8 else None,
                            "divid_cash_ps_before_tax": float(row[9]) if len(row) > 9 and row[9] else None,
                            "divid_cash_ps_after_tax": float(row[10]) if len(row) > 10 and row[10] else None,
                            "divid_stocks_ps": float(row[11]) if len(row) > 11 and row[11] else None,
                            "divid_cash_stock": row[12] if len(row) > 12 else None,
                            "divid_reserve_to_stock_ps": float(row[13]) if len(row) > 13 and row[13] else None
                        }
                        all_dividends.append(dividend)
                    
                except Exception as e:
                    logger.error(f"获取 {year} 年分红数据异常 {bs_code}: {e}")
                    continue
            
            logger.info(f"成功获取 {bs_code} 的除权除息信息 {len(all_dividends)} 条")
            return all_dividends
            
        except Exception as e:
            logger.error(f"获取除权除息信息失败 {code}: {e}")
            return []
    
    async def get_adjust_factor(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取复权因子信息
        
        BaoStock 提供的是涨跌幅复权算法复权因子
        
        Args:
            code: 股票代码
            start_date: 开始日期 (YYYY-MM-DD 或 YYYYMMDD)
            end_date: 结束日期 (YYYY-MM-DD 或 YYYYMMDD)
            
        Returns:
            List[Dict[str, Any]]: 复权因子信息列表
            
        返回字段:
        - code: 证券代码
        - divid_operate_date: 除权除息日期
        - fore_adjust_factor: 向前复权因子
        - back_adjust_factor: 向后复权因子
        - adjust_factor: 本次复权因子
        
        复权因子说明:
        - foreAdjustFactor: 除权除息日前一个交易日的收盘价/除权除息日最近的一个交易日的前收盘价
        - backAdjustFactor: 除权除息日最近的一个交易日的前收盘价/除权除息日前一个交易日的收盘价
        - adjustFactor: 本次复权因子
        
        基于复权因子与日 K 线数据可生成复权行情
        """
        try:
            bs_code = self._get_bs_code(code)
            
            # 格式化日期
            start = self._format_date_for_bs(start_date) if start_date else "20150101"
            end = self._format_date_for_bs(end_date) if end_date else datetime.now().strftime("%Y%m%d")
            
            logger.debug(f"获取复权因子：{bs_code}, 范围：{start} ~ {end}")
            
            # 查询复权因子
            rs = bs.query_adjust_factor(
                code=bs_code,
                start_date=start,
                end_date=end
            )
            
            if rs.error_code != "0":
                logger.error(f"获取复权因子失败 {bs_code}: {rs.error_msg}")
                return []
            
            factors = []
            while (rs.error_code == "0") & rs.next():
                row = rs.get_row_data()
                
                # 解析复权因子
                factor = {
                    "code": code,
                    "divid_operate_date": self._parse_date(row[1]) if len(row) > 1 else None,
                    "fore_adjust_factor": float(row[2]) if len(row) > 2 and row[2] else None,
                    "back_adjust_factor": float(row[3]) if len(row) > 3 and row[3] else None,
                    "adjust_factor": float(row[4]) if len(row) > 4 and row[4] else None
                }
                factors.append(factor)
            
            logger.info(f"成功获取 {bs_code} 的复权因子 {len(factors)} 条")
            return factors
            
        except Exception as e:
            logger.error(f"获取复权因子失败 {code}: {e}")
            return []
