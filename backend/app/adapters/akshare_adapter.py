from typing import Optional, List, Dict, Any
import akshare as ak
import pandas as pd
from loguru import logger
from datetime import datetime
import asyncio
import random
import time

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData
)


class AkShareAdapter(BaseDataAdapter):
    """AkShare 数据源适配器
    
    特性：
    - 支持所有 akshare 接口
    - 包含反风控机制（请求延迟、重试、伪装）
    - 异步支持
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        
        # 反风控设置
        self._request_delay_range = (1.0, 2.0)  # 请求间隔（秒）
        self._retry_base_delay = 2.0  # 重试基础延迟（秒）
        self._max_retries = 3  # 最大重试次数
        self._consecutive_failures = 0  # 连续失败次数
        self._adaptive_delay_enabled = True  # 启用自适应延迟
        self._is_initialized = False
        
        # User-Agent 轮换池（伪装成不同浏览器）
        self._user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_2_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1"
        ]
        self._current_user_agent = random.choice(self._user_agents)
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.AKSHARE
    
    async def initialize(self) -> bool:
        try:
            self._is_initialized = True
            logger.info("AkShare 适配器初始化成功")
            return True
        except Exception as e:
            logger.error(f"AkShare 适配器初始化失败：{e}")
            return False
    
    async def close(self) -> None:
        self._is_initialized = False
        logger.info("AkShare 适配器已关闭")
    
    # ========== 反风控方法 ===========
    
    def _get_time_based_delay(self) -> tuple:
        """根据当前时间段获取合适的延迟范围
        
        Returns:
            tuple: (min_delay, max_delay)
        """
        current_hour = datetime.now().hour
        
        # 交易时段（9:30-11:30, 13:00-15:00）使用较长延迟
        if (9 <= current_hour <= 11) or (13 <= current_hour <= 14):
            return (1.5, 3.0)
        # 非交易时段使用较短延迟
        else:
            return (0.5, 1.5)
    
    async def _rate_limit(self):
        """异步请求限流"""
        if self._adaptive_delay_enabled:
            min_delay, max_delay = self._get_time_based_delay()
            
            # 根据连续失败次数增加额外延迟
            if self._consecutive_failures > 0:
                extra_delay = min(self._consecutive_failures, 5)
                min_delay += extra_delay
                max_delay += extra_delay
            
            delay = random.uniform(min_delay, max_delay)
        else:
            delay = random.uniform(*self._request_delay_range)
        
        logger.debug(f"AkShare 请求限流：延迟 {delay:.2f}秒")
        await asyncio.sleep(delay)
    
    def _rate_limit_sync(self):
        """同步请求限流"""
        delay = random.uniform(*self._request_delay_range)
        time.sleep(delay)
    
    def get_anti_wind_config(self) -> Dict[str, Any]:
        """获取反风控配置信息"""
        return {
            "request_delay_range": self._request_delay_range,
            "current_delay_range": self._get_time_based_delay() if self._adaptive_delay_enabled else self._request_delay_range,
            "adaptive_delay_enabled": self._adaptive_delay_enabled,
            "max_retries": self._max_retries,
            "consecutive_failures": self._consecutive_failures,
            "user_agent_pool_size": len(self._user_agents),
            "current_user_agent": self._current_user_agent[:50] + "...",
            "user_agent_rotation": "已启用"
        }
    
    def enable_adaptive_delay(self, enabled: bool = True):
        """启用/禁用自适应延迟
        
        Args:
            enabled: 是否启用自适应延迟
        """
        self._adaptive_delay_enabled = enabled
        status = "已启用" if enabled else "已禁用"
        logger.info(f"AkShare 自适应延迟：{status}")
    
    def set_custom_delay(self, min_delay: float, max_delay: float):
        """设置自定义延迟范围
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
        """
        self._request_delay_range = (min_delay, max_delay)
        self._adaptive_delay_enabled = False  # 禁用自适应延迟
        logger.info(f"AkShare 自定义延迟范围：{min_delay}-{max_delay}秒（已禁用自适应延迟）")
    
    def _rotate_user_agent(self):
        """轮换 User-Agent"""
        old_ua = self._current_user_agent
        self._current_user_agent = random.choice(self._user_agents)
        logger.debug(f"User-Agent 已轮换：{old_ua[:50]}... -> {self._current_user_agent[:50]}...")
    
    def get_current_user_agent(self) -> str:
        """获取当前 User-Agent"""
        return self._current_user_agent
    
    @staticmethod
    def rate_limit_decorator(min_delay: float = 1.0, max_delay: float = 2.0, retries: int = 3):
        """限流装饰器（用于同步方法）
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            retries: 重试次数
        
        Example:
            @rate_limit_decorator(min_delay=1.5, max_delay=2.5, retries=3)
            def fetch_data():
                pass
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                self = args[0] if args else None
                for attempt in range(retries):
                    try:
                        # 请求前延迟
                        if hasattr(self, '_rate_limit_sync'):
                            self._rate_limit_sync()
                        
                        result = func(*args, **kwargs)
                        
                        # 成功后重置失败计数
                        if hasattr(self, '_consecutive_failures'):
                            self._consecutive_failures = 0
                        
                        return result
                    except Exception as e:
                        if hasattr(self, '_consecutive_failures'):
                            self._consecutive_failures += 1
                        
                        if attempt < retries - 1:
                            # 指数退避
                            delay = (2 ** attempt) * min_delay + random.uniform(0, 1)
                            logger.debug(f"{func.__name__} 请求失败，{delay:.1f}秒后重试（{attempt+1}/{retries}）: {e}")
                            time.sleep(delay)
                        else:
                            logger.error(f"{func.__name__} 失败，已达最大重试次数：{e}")
                            raise
                return None
            return wrapper
        return decorator
    
    @staticmethod
    def async_rate_limit_decorator(min_delay: float = 1.0, max_delay: float = 2.0, retries: int = 3):
        """异步限流装饰器
        
        Args:
            min_delay: 最小延迟（秒）
            max_delay: 最大延迟（秒）
            retries: 重试次数
        
        Example:
            @async_rate_limit_decorator(min_delay=1.5, max_delay=2.5, retries=3)
            async def fetch_data():
                pass
        """
        def decorator(func):
            async def wrapper(*args, **kwargs):
                self = args[0] if args else None
                for attempt in range(retries):
                    try:
                        # 请求前延迟
                        if hasattr(self, '_rate_limit'):
                            await self._rate_limit()
                        
                        result = await func(*args, **kwargs)
                        
                        # 成功后重置失败计数
                        if hasattr(self, '_consecutive_failures'):
                            self._consecutive_failures = 0
                        
                        return result
                    except Exception as e:
                        if hasattr(self, '_consecutive_failures'):
                            self._consecutive_failures += 1
                        
                        if attempt < retries - 1:
                            # 指数退避
                            delay = (2 ** attempt) * min_delay + random.uniform(0, 1)
                            logger.debug(f"{func.__name__} 请求失败，{delay:.1f}秒后重试（{attempt+1}/{retries}）: {e}")
                            await asyncio.sleep(delay)
                        else:
                            logger.error(f"{func.__name__} 失败，已达最大重试次数：{e}")
                            raise
                return None
            return wrapper
        return decorator
    
    async def initialize(self) -> bool:
        try:
            self._is_initialized = True
            logger.info("AkShare 适配器初始化成功（含反风控设置）")
            return True
        except Exception as e:
            logger.error(f"AkShare 适配器初始化失败：{e}")
            return False
    
    async def close(self) -> None:
        self._is_initialized = False
        logger.info("AkShare 适配器已关闭")
    
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
            logger.error(f"获取股票列表失败：{e}")
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
            logger.error(f"获取 K 线数据失败 {code}: {e}")
            return []
    
    async def get_market_index_kline(
        self,
        index_code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[KLineData]:
        """获取大盘指数 K 线数据
        
        Args:
            index_code: 指数代码，如 000001（上证指数）、399001（深证成指）
            start_date: 开始日期 YYYY-MM-DD
            end_date: 结束日期 YYYY-MM-DD
            
        Returns:
            K 线数据列表
        """
        try:
            await self._rate_limit()
            
            # 使用 akshare 获取指数历史行情
            df = ak.stock_zh_index_hist(
                symbol=index_code,
                period="daily",
                start_date=start_date.replace("-", "") if start_date else "19900101",
                end_date=end_date.replace("-", "") if end_date else "20991231"
            )
            
            klines = []
            for _, row in df.iterrows():
                klines.append(KLineData(
                    code=index_code,
                    date=self.format_date(str(row["date"])),
                    open=float(row["open"]),
                    high=float(row["high"]),
                    low=float(row["low"]),
                    close=float(row["close"]),
                    volume=float(row["volume"]) if "volume" in row else 0,
                    amount=0  # 指数通常没有成交额数据
                ))
            
            return klines
            
        except Exception as e:
            logger.error(f"获取指数 K 线失败 {index_code}: {e}")
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
                    code=str(row["板块代码"]),
                    name=str(row["板块名称"]),
                    sector_type=sector_type,
                    change_pct=float(row["涨跌幅"]) if "涨跌幅" in row else None,
                    volume=float(row["成交量"]) if "成交量" in row else None
                ))
            return sectors
        except Exception as e:
            logger.error(f"获取板块列表失败：{e}")
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
            
            sort_col = "涨跌幅" if sort_by == "change_pct" else "成交量"
            df = df.sort_values(by=sort_col, ascending=False)
            df = df.head(limit)
            
            sectors = []
            for _, row in df.iterrows():
                sectors.append(SectorInfo(
                    code=str(row["板块代码"]),
                    name=str(row["板块名称"]),
                    sector_type=sector_type,
                    change_pct=float(row["涨跌幅"]) if "涨跌幅" in row else None
                ))
            return sectors
        except Exception as e:
            logger.error(f"获取板块排名失败：{e}")
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
            
            # 查找日期列
            date_column = None
            for col in ['报告日期', '股东人数', '股东人数', '日期']:
                if col in df.columns:
                    date_column = col
                    break
            
            if not date_column:
                logger.warning(f"未找到日期列，可用列：{df.columns.tolist()}")
                return []
            
            chip_data = []
            for _, row in df.iterrows():
                date = str(row[date_column])
                if start_date and date < start_date:
                    continue
                if end_date and date > end_date:
                    continue
                
                # 查找股东人数列
                count_column = None
                for col in ['股东人数', '股东总人数']:
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
            df = ak.stock_financial_abstract_ths(symbol=code, indicator="全部") 
            return df.to_dict("records")
        except Exception as e:
            logger.error(f"获取财务数据失败 {code}: {e}")
            return {}
    
    # ========== 东方财富特色数据接口（从 EastMoneyAdapter 合并）==========
    
    async def get_stock_changes(self, change_type: str = "big_buy") -> List[Any]:
        """获取盘口异动数据
        
        Args:
            change_type: 异动类型，可选：
                - rocket: 火箭发射
                - rebound: 快速反弹
                - big_buy: 大笔买入
                - limit_up: 封涨停板
                - limit_down: 封跌停板
                等
        
        Returns:
            盘口异动数据列表
        """
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_change_em(symbol=change_type))
            
            if df is None or df.empty:
                return []
            
            changes = []
            for _, row in df.iterrows():
                changes.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'change': float(row.get('涨跌额', 0)) if pd.notna(row.get('涨跌额')) else None,
                    'volume': float(row.get('成交量', 0)) if pd.notna(row.get('成交量')) else None,
                    'amount': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    'change_reason': str(row.get('异动类型', ''))
                })
            
            logger.info(f"获取盘口异动数据成功，共{len(changes)}条")
            return changes
        except Exception as e:
            logger.error(f"获取盘口异动数据失败：{e}")
            return []
    
    async def get_zt_pool(self, date: Optional[str] = None) -> List[Any]:
        """获取涨停股池数据
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为今日
        
        Returns:
            涨停股池数据列表
        """
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_zt_pool_em(date=date))
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'latest_price': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'turnover': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    'float_mv': float(row.get('流通市值', 0)) if pd.notna(row.get('流通市值')) else None,
                    'total_mv': float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None,
                    'turnover_rate': float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else None,
                    'seal_fund': float(row.get('封板资金', 0)) if pd.notna(row.get('封板资金')) else None,
                    'first_seal_time': str(row.get('首次封板时间', '')),
                    'last_seal_time': str(row.get('最后封板时间', '')),
                    'open_count': int(row.get('炸板次数', 0)) if pd.notna(row.get('炸板次数')) else None,
                    'zt_stats': str(row.get('涨停统计', '')),
                    'continuous_count': int(row.get('连板数', 1)) if pd.notna(row.get('连板数')) else None,
                    'industry': str(row.get('所属行业', ''))
                })
            
            logger.info(f"获取涨停股池数据成功：{date}, 共{len(zt_stocks)}条")
            return zt_stocks
        except Exception as e:
            logger.error(f"获取涨停股池数据失败：{e}")
            return []
    
    async def get_zt_pool_previous(self, date: Optional[str] = None) -> List[Any]:
        """获取昨日涨停股池数据
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为昨日
        
        Returns:
            昨日涨停股池数据列表
        """
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_zt_pool_previous_em(date=date))
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'latest_price': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'limit_up_price': float(row.get('涨停价', 0)) if pd.notna(row.get('涨停价')) else None,
                    'turnover': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    'float_mv': float(row.get('流通市值', 0)) if pd.notna(row.get('流通市值')) else None,
                    'total_mv': float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None,
                    'turnover_rate': float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else None,
                    'speed_pct': float(row.get('涨速', 0)) if pd.notna(row.get('涨速')) else None,
                    'amplitude': float(row.get('振幅', 0)) if pd.notna(row.get('振幅')) else None
                })
            
            logger.info(f"获取昨日涨停股池数据成功：{date}, 共{len(zt_stocks)}条")
            return zt_stocks
        except Exception as e:
            logger.error(f"获取昨日涨停股池数据失败：{e}")
            return []
    
    async def get_zt_strong(self, date: Optional[str] = None) -> List[Any]:
        """获取强势股池数据（连续涨停股）
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为今日
        
        Returns:
            强势股池数据列表
        """
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_zt_strong_em(date=date))
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'latest_price': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'continuous_count': int(row.get('连板数', 1)) if pd.notna(row.get('连板数')) else None,
                    'industry': str(row.get('所属行业', '')),
                    'reason': str(row.get('涨停理由', ''))
                })
            
            logger.info(f"获取强势股池数据成功：{date}, 共{len(zt_stocks)}条")
            return zt_stocks
        except Exception as e:
            logger.error(f"获取强势股池数据失败：{e}")
            return []
    
    async def get_zt_sub_new(self, date: Optional[str] = None) -> List[Any]:
        """获取次新股涨停池数据
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为今日
        
        Returns:
            次新股涨停池数据列表
        """
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_zt_sub_new_em(date=date))
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'latest_price': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'turnover': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    'float_mv': float(row.get('流通市值', 0)) if pd.notna(row.get('流通市值')) else None,
                    'total_mv': float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None,
                    'turnover_rate': float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else None,
                    'open_count': int(row.get('炸板次数', 0)) if pd.notna(row.get('炸板次数')) else None,
                    'industry': str(row.get('所属行业', '')),
                    'list_date': str(row.get('上市日期', ''))
                })
            
            logger.info(f"获取次新股涨停池数据成功：{date}, 共{len(zt_stocks)}条")
            return zt_stocks
        except Exception as e:
            logger.error(f"获取次新股涨停池数据失败：{e}")
            return []
    
    async def get_board_changes(self) -> List[Any]:
        """获取板块异动数据
        
        Returns:
            板块异动数据列表
        """
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_board_change_em())
            
            if df is None or df.empty:
                return []
            
            changes = []
            for _, row in df.iterrows():
                changes.append({
                    'board_name': str(row.get('板块名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'net_inflow': float(row.get('主力净流入', 0)) if pd.notna(row.get('主力净流入')) else None,
                    'change_count': int(row.get('板块异动总次数', 0)) if pd.notna(row.get('板块异动总次数')) else None,
                    'top_stock_code': str(row.get('板块异动最频繁个股及所属类型 - 股票代码', '')),
                    'top_stock_name': str(row.get('板块异动最频繁个股及所属类型 - 股票名称', '')),
                    'top_stock_type': str(row.get('板块异动最频繁个股及所属类型 - 买卖方向', '')),
                    'change_types': row.get('板块具体异动类型列表及出现次数', [])
                })
            
            logger.info(f"获取板块异动数据成功，共{len(changes)}条")
            return changes
        except Exception as e:
            logger.error(f"获取板块异动数据失败：{e}")
            return []
    
    async def get_stock_info_sh_name_code(self, symbol: str = "主板 A 股") -> List[Any]:
        """获取上海证券交易所股票列表
        
        Args:
            symbol: 板块类型，可选值："主板 A 股"、"主板 B 股"、"科创板"
        
        Returns:
            股票信息列表
        """
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_info_sh_name_code(symbol=symbol))
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': str(row.get('证券代码', '')),
                    'name': str(row.get('证券简称', ''))
                })
            
            logger.info(f"获取上交所股票列表成功 ({symbol}), 共{len(stocks)}条")
            return stocks
        except Exception as e:
            logger.error(f"获取上交所股票列表失败：{e}")
            return []
    
    async def get_stock_info_sz_name_code(self, symbol: str = "主板 A 股") -> List[Any]:
        """获取深圳证券交易所股票列表
        
        Args:
            symbol: 板块类型，可选值："主板 A 股"、"主板 B 股"、"创业板"
        
        Returns:
            股票信息列表
        """
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_info_sz_name_code(symbol=symbol))
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': str(row.get('证券代码', '')),
                    'name': str(row.get('证券简称', ''))
                })
            
            logger.info(f"获取深交所股票列表成功 ({symbol}), 共{len(stocks)}条")
            return stocks
        except Exception as e:
            logger.error(f"获取深交所股票列表失败：{e}")
            return []
    
    async def get_stock_info_bj_name_code(self) -> List[Any]:
        """获取北京证券交易所股票列表
        
        Returns:
            股票信息列表
        """
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_info_bj_name_code())
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stocks.append({
                    'code': str(row.get('证券代码', '')),
                    'name': str(row.get('证券简称', ''))
                })
            
            logger.info(f"获取北交所股票列表成功，共{len(stocks)}条")
            return stocks
        except Exception as e:
            logger.error(f"获取北交所股票列表失败：{e}")
            return []
    
    async def get_board_industry_name_em(self) -> List[Any]:
        """获取东方财富行业板块列表
        
        Returns:
            行业板块列表
        """
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_board_industry_name_em())
            
            if df is None or df.empty:
                return []
            
            boards = []
            for _, row in df.iterrows():
                boards.append({
                    'code': str(row.get('板块代码', '')),
                    'name': str(row.get('板块名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'change': float(row.get('涨跌额', 0)) if pd.notna(row.get('涨跌额')) else None,
                    'total_mv': float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None,
                    'turnover': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None
                })
            
            logger.info(f"获取东方财富行业板块列表成功，共{len(boards)}条")
            return boards
        except Exception as e:
            logger.error(f"获取东方财富行业板块列表失败：{e}")
            return []
    
    async def get_board_industry_cons_em(self, symbol: str) -> List[Any]:
        """获取东方财富行业板块成份股
        
        Args:
            symbol: 板块代码或板块名称
        
        Returns:
            板块成份股列表
        """
        try:
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_board_industry_cons_em(symbol=symbol))
            
            if df is None or df.empty:
                return []
            
            cons_data = []
            for _, row in df.iterrows():
                cons_data.append({
                    'code': str(row.get('代码', '')),
                    'name': str(row.get('名称', '')),
                    'change_pct': float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    'latest_price': float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    'change': float(row.get('涨跌额', 0)) if pd.notna(row.get('涨跌额')) else None,
                    'volume': float(row.get('成交量', 0)) if pd.notna(row.get('成交量')) else None,
                    'amount': float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    'turnover_rate': float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else None,
                    'pe_ratio': float(row.get('市盈率 - 动态', 0)) if pd.notna(row.get('市盈率 - 动态')) else None,
                    'pb_ratio': float(row.get('市净率', 0)) if pd.notna(row.get('市净率')) else None
                })
            
            logger.info(f"获取东方财富行业板块成份股成功 ({symbol}), 共{len(cons_data)}条")
            return cons_data
        except Exception as e:
            logger.error(f"获取东方财富行业板块成份股失败：{e}")
            return []
