from typing import Optional, List, Dict, Any
import akshare as ak
import pandas as pd
from loguru import logger
import time
from datetime import timedelta
import asyncio

from .base import (
    BaseDataAdapter,
    DataSourceType,
    StockBasicInfo,
    KLineData,
    SectorInfo,
    ChipData
)
from app.utils.data_validator import validator


class AkShareAdapter(BaseDataAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        # 内存缓存
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Dict[str, float] = {}
        # 不同数据的缓存时间（秒）
        self._cache_ttl = {
            'kline': 300,        # K 线：5 分钟
            'stock_list': 1800,  # 股票列表：30 分钟
            'stock_info': 600,   # 股票信息：10 分钟
            'sector': 300,       # 板块：5 分钟
            'chip': 300,         # 筹码：5 分钟
            'default': 300       # 默认：5 分钟
        }
        # 缓存统计
        self._cache_stats = {
            'hits': 0,
            'misses': 0
        }
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.AKSHARE
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存 key"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return "_".join(key_parts)
    
    def _get_from_cache(self, key: str, ttl_type: str = 'default') -> Optional[Any]:
        """从缓存获取数据"""
        if key not in self._cache:
            self._cache_stats['misses'] += 1
            return None
        
        # 检查是否过期
        timestamp = self._cache_timestamp.get(key, 0)
        ttl = self._cache_ttl.get(ttl_type, self._cache_ttl['default'])
        
        if time.time() - timestamp > ttl:
            # 过期，删除
            del self._cache[key]
            self._cache_stats['misses'] += 1
            logger.debug(f"缓存过期：{key}")
            return None
        
        self._cache_stats['hits'] += 1
        logger.debug(f"缓存命中：{key}")
        return self._cache[key]
    
    def _set_to_cache(self, key: str, value: Any, ttl_type: str = 'default'):
        """设置缓存"""
        self._cache[key] = value
        self._cache_timestamp[key] = time.time()
        logger.debug(f"写入缓存：{key} (TTL: {self._cache_ttl.get(ttl_type, 300)}s)")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        total = self._cache_stats['hits'] + self._cache_stats['misses']
        hit_rate = (self._cache_stats['hits'] / total * 100) if total > 0 else 0
        
        return {
            'hits': self._cache_stats['hits'],
            'misses': self._cache_stats['misses'],
            'hit_rate': f"{hit_rate:.2f}%",
            'cache_size': len(self._cache),
            'memory_usage': f"{len(self._cache) * 10} KB"  # 估算
        }
    
    async def clear_cache(self, pattern: Optional[str] = None):
        """清理缓存"""
        if pattern:
            keys_to_delete = [k for k in self._cache.keys() if pattern in k]
            for key in keys_to_delete:
                del self._cache[key]
                del self._cache_timestamp[key]
            logger.info(f"清理缓存：{pattern}, 删除 {len(keys_to_delete)} 条")
        else:
            self._cache.clear()
            self._cache_timestamp.clear()
            self._cache_stats.clear()
            logger.info("清理所有缓存")
    
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
            # 使用缓存（30 分钟）
            cache_key = self._get_cache_key('stock_list', market=market)
            cached = self._get_from_cache(cache_key, 'stock_list')
            if cached:
                return cached
            
            # 从数据源获取
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
            
            # 保存到缓存
            self._set_to_cache(cache_key, stocks, 'stock_list')
            
            return stocks
        except Exception as e:
            logger.error(f"获取股票列表失败：{e}")
            return []
    
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        try:
            # 使用缓存（10 分钟）
            cache_key = self._get_cache_key('stock_info', code=code)
            cached = self._get_from_cache(cache_key, 'stock_info')
            if cached:
                return cached
            
            # 从数据源获取
            df = ak.stock_individual_info_em(symbol=code)
            info_dict = dict(zip(df["item"], df["value"]))
            market_tag = "SH" if code.startswith("6") else "SZ"
            stock_info = StockBasicInfo(
                code=code,
                name=info_dict.get("股票简称", ""),
                market=market_tag,
                industry=info_dict.get("行业"),
                list_date=info_dict.get("上市时间"),
                total_shares=float(info_dict.get("总市值", 0)) / 100000000 if info_dict.get("总市值") else None
            )
            
            # 保存到缓存
            self._set_to_cache(cache_key, stock_info, 'stock_info')
            
            return stock_info
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
            # 使用缓存（5 分钟）
            cache_key = self._get_cache_key('kline', code=code, start=start_date, end=end_date, adjust=adjust)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                logger.debug(f"K 线缓存命中：{code}")
                return cached
            
            adjust_map = {
                "qfq": "qfq",
                "hfq": "hfq",
                "": ""
            }
            adjust_type = adjust_map.get(adjust, "qfq")
            
            # 限制日期范围（默认 3 年），防止超时
            from datetime import datetime, timedelta
            
            # 兼容两种日期格式：YYYY-MM-DD 和 YYYYMMDD
            def parse_date(date_str):
                if not date_str:
                    return None
                # 移除可能的横杠
                clean_date = date_str.replace("-", "")
                return datetime.strptime(clean_date, "%Y%m%d")
            
            if not start_date:
                # 默认获取 3 年数据
                end_dt = parse_date(end_date) if end_date else datetime.now()
                start_dt = end_dt - timedelta(days=3*365)
                start_date = start_dt.strftime("%Y-%m-%d")
            
            # 添加超时控制（10 秒）
            async with asyncio.timeout(10):
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
            
            # 数据验证
            is_valid, errors = validator.validate_kline(klines, code)
            if not is_valid:
                logger.warning(f"K 线数据验证失败：{errors}")
            
            # 保存到缓存
            self._set_to_cache(cache_key, klines, 'kline')
            
            return klines
        except asyncio.TimeoutError:
            logger.error(f"获取 K 线数据超时 {code}: 超过 10 秒")
            return []
        except Exception as e:
            logger.error(f"获取 K 线数据失败 {code}: {e}")
            return []
    
    async def get_market_index_kline(
        self,
        index_code: str = "000001",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[KLineData]:
        """
        获取大盘指数 K 线数据
        :param index_code: 指数代码（000001=上证指数，399001=深证成指，399006=创业板指）
        :param start_date: 开始日期
        :param end_date: 结束日期
        :return: K 线数据列表
        """
        try:
            # 使用缓存
            cache_key = self._get_cache_key('index_kline', code=index_code, start=start_date, end=end_date)
            cached = self._get_from_cache(cache_key, 'kline')
            if cached:
                return cached
            
            # 限制日期范围（默认 3 年），防止超时
            from datetime import datetime, timedelta
            
            # 兼容两种日期格式：YYYY-MM-DD 和 YYYYMMDD
            def parse_date(date_str):
                if not date_str:
                    return None
                # 移除可能的横杠
                clean_date = date_str.replace("-", "")
                return datetime.strptime(clean_date, "%Y%m%d")
            
            if not start_date:
                # 默认获取 3 年数据
                end_dt = parse_date(end_date) if end_date else datetime.now()
                start_dt = end_dt - timedelta(days=3*365)
                start_date = start_dt.strftime("%Y-%m-%d")
            
            # 添加超时控制（10 秒）
            async with asyncio.timeout(10):
                # 获取指数 K 线（指数无需复权）
                df = ak.index_zh_a_hist(
                    symbol=index_code,
                    period="daily",
                    start_date=start_date.replace("-", "") if start_date else "19900101",
                    end_date=end_date.replace("-", "") if end_date else "20991231"
                )
            
            klines = []
            for _, row in df.iterrows():
                klines.append(KLineData(
                    code=index_code,
                    date=self.format_date(str(row["日期"])),
                    open=float(row["开盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    close=float(row["收盘"]),
                    volume=float(row["成交量"]),
                    amount=float(row["成交额"]) if "成交额" in row else None,
                    turnover_rate=0.0  # 指数无换手率
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, klines, 'kline')
            
            return klines
        except asyncio.TimeoutError:
            logger.error(f"获取指数 K 线数据超时 {index_code}: 超过 10 秒")
            return []
        except Exception as e:
            logger.error(f"获取指数 K 线失败 {index_code}: {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        try:
            # 使用东方财富指数实时行情接口
            # API: stock_zh_index_spot_em(symbol: str)
            # 参数 symbol: choice of {"沪深重要指数", "上证系列指数", "深证系列指数", "指数成份", "中证系列指数"}
            # 数据来源：东方财富网 https://quote.eastmoney.com/center/gridlist.html#index_sz
            async with asyncio.timeout(10):
                # 获取沪深重要指数数据（包含上证 50、沪深 300、创业板指等）
                df = ak.stock_zh_index_spot_em(symbol="沪深重要指数")
            
            if df.empty:
                return {}
            
            # 过滤出指定指数数据（代码字段匹配）
            index_data = df[df['代码'] == code]
            if index_data.empty:
                return {}
            
            row = index_data.iloc[0]
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
                "turnover_rate": 0.0  # 指数无换手率
            }
        except asyncio.TimeoutError:
            logger.error(f"获取实时行情超时 {code}")
            return {}
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
            # 优先匹配带"-本次"的字段，其次匹配不带后缀的字段
            for col in ['股东户数统计截止日 - 本次', '股东户数统计截止日', '统计截止日期 - 本次', 
                       '统计截止日期', '截止日期 - 本次', '截止日期', '日期']:
                if col in df.columns:
                    date_column = col
                    break
            
            if not date_column:
                logger.warning(f"未找到日期字段，可用字段：{df.columns.tolist()}")
                return []
            
            chip_data = []
            for _, row in df.iterrows():
                date = str(row[date_column])
                # 清理日期格式
                if ' ' in date:
                    date = date.split(' ')[0]
                if start_date and date < start_date:
                    continue
                if end_date and date > end_date:
                    continue
                
                # 动态检测股东户数字段
                count_column = None
                for col in ['股东户数 - 本次', '股东户数', '股东人数 - 本次', '股东人数']:
                    if col in df.columns:
                        count_column = col
                        break
                
                if not count_column:
                    # 尝试使用第一列数值型字段
                    for col in df.columns:
                        if '户数' in col or '人数' in col:
                            count_column = col
                            break
                
                if not count_column:
                    continue
                
                # 获取户均持股数量
                avg_shares = None
                for col in ['户均持股数量', '户均持股市值']:
                    if col in df.columns:
                        try:
                            avg_shares = float(row[col])
                            break
                        except (ValueError, TypeError):
                            continue
                
                chip_data.append(ChipData(
                    code=code,
                    date=date,
                    shareholder_count=float(row[count_column]) if row[count_column] not in [None, '', '-'] else None,
                    avg_shares_per_holder=avg_shares
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
    
    async def get_sse_daily_overview(self, date: str) -> Dict[str, Any]:
        """
        获取上海证券交易所每日概况数据
        
        Args:
            date: 日期，格式 YYYYMMDD，仅支持 20211227 之后的数据
            
        Returns:
            上交所每日概况数据，包含：
            - 挂牌数（股票、主板 A、主板 B、科创板）
            - 市价总值
            - 流通市值
            - 成交金额
            - 成交量
            - 平均市盈率
            - 换手率等
            
        API: stock_sse_deal_daily
        数据来源：上海证券交易所
        """
        try:
            # 验证日期格式
            if len(date) != 8:
                logger.error(f"日期格式错误：{date}，应为 YYYYMMDD")
                return {}
            
            # 验证日期范围（仅支持 20211227 之后的数据）
            if date < "20211227":
                logger.error(f"日期超出范围：{date}，仅支持 20211227 之后的数据")
                return {}
            
            # 调用 API
            df = ak.stock_sse_deal_daily(date=date)
            
            if df.empty:
                return {}
            
            # 转换为字典格式
            result = {}
            for _, row in df.iterrows():
                indicator_name = row["单日情况"]
                result[indicator_name] = {}
                # 动态获取所有列（除了"单日情况"列）
                for col in df.columns:
                    if col != "单日情况":
                        value = row[col]
                        # 处理 NaN 值
                        import math
                        if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                            result[indicator_name][col] = None
                        else:
                            result[indicator_name][col] = float(value)
            
            return result
        except Exception as e:
            logger.error(f"获取上交所每日概况失败 {date}: {e}")
            return {}
    
    async def get_all_a_shares_realtime(self) -> List[Dict[str, Any]]:
        """
        获取沪深京 A 股实时行情数据
        
        Returns:
            所有沪深京 A 股上市公司的实时行情数据，包含：
            - 序号：股票代码
            - 代码：股票代码
            - 名称：股票名称
            - 最新价：当前价格
            - 涨跌幅：涨跌幅度（%）
            - 涨跌额：涨跌金额
            - 成交量：成交量（手）
            - 成交额：成交额（元）
            - 振幅：振幅（%）
            - 最高：最高价
            - 最低：最低价
            - 今开：今日开盘价
            - 昨收：昨日收盘价
            - 量比：量比
            - 换手率：换手率（%）
            - 市盈率 - 动态：动态市盈率
            - 市净率：市净率
            - 总市值：总市值（元）
            - 流通市值：流通市值（元）
            - 涨速：涨速
            - 5 分钟涨跌：5 分钟涨跌幅（%）
            - 60 日涨跌幅：60 日涨跌幅（%）
            - 年初至今涨跌幅：年初至今涨跌幅（%）
            
        API: stock_zh_a_spot_em
        数据来源：东方财富网 https://quote.eastmoney.com/center/gridlist.html#hs_a_board
        限量：单次返回所有沪深京 A 股上市公司的实时行情数据（约 5600+ 只股票）
        """
        try:
            # 使用东方财富网沪深京 A 股实时行情接口
            # API: stock_zh_a_spot_em - 获取所有沪深京 A 股实时行情
            # 数据来源：东方财富网
            async with asyncio.timeout(15):  # 增加超时时间到 15 秒，因为数据量较大
                df = ak.stock_zh_a_spot_em()
            
            if df.empty:
                return []
            
            # 转换为字典列表
            result = []
            for _, row in df.iterrows():
                stock_data = {}
                for col in df.columns:
                    value = row[col]
                    # 处理 NaN 值
                    import math
                    if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                        stock_data[col] = None
                    else:
                        # 根据字段类型转换
                        if col in ['序号']:
                            stock_data[col] = int(value)
                        else:
                            stock_data[col] = float(value)
                
                result.append(stock_data)
            
            return result
        except asyncio.TimeoutError:
            logger.error("获取沪深京 A 股实时行情超时")
            return []
        except Exception as e:
            logger.error(f"获取沪深京 A 股实时行情失败：{e}")
            return []
    
    async def get_gem_board_realtime(self) -> List[Dict[str, Any]]:
        """
        获取创业板实时行情数据
        
        Returns:
            所有创业板上市公司的实时行情数据，包含：
            - 序号：股票代码
            - 代码：股票代码（300/301 开头）
            - 名称：股票名称
            - 最新价：当前价格
            - 涨跌幅：涨跌幅度（%）
            - 涨跌额：涨跌金额
            - 成交量：成交量（手）
            - 成交额：成交额（元）
            - 振幅：振幅（%）
            - 最高：最高价
            - 最低：最低价
            - 今开：今日开盘价
            - 昨收：昨日收盘价
            - 量比：量比
            - 换手率：换手率（%）
            - 市盈率 - 动态：动态市盈率
            - 市净率：市净率
            - 总市值：总市值（元）
            - 流通市值：流通市值（元）
            - 涨速：涨速
            - 5 分钟涨跌：5 分钟涨跌幅（%）
            - 60 日涨跌幅：60 日涨跌幅（%）
            - 年初至今涨跌幅：年初至今涨跌幅（%）
            
        API: stock_cy_a_spot_em
        数据来源：东方财富网 https://quote.eastmoney.com/center/gridlist.html#gem_board
        限量：单次返回所有创业板的实时行情数据（约 1400+ 只股票）
        """
        try:
            # 使用东方财富网创业板实时行情接口
            # API: stock_cy_a_spot_em - 获取创业板实时行情
            # 数据来源：东方财富网
            async with asyncio.timeout(15):  # 增加超时时间到 15 秒，因为数据量较大
                df = ak.stock_cy_a_spot_em()
            
            if df.empty:
                return []
            
            # 转换为字典列表
            result = []
            for _, row in df.iterrows():
                stock_data = {}
                for col in df.columns:
                    value = row[col]
                    # 处理 NaN 值
                    import math
                    if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                        stock_data[col] = None
                    else:
                        # 根据字段类型转换
                        if col in ['序号']:
                            stock_data[col] = int(value)
                        else:
                            stock_data[col] = float(value)
                
                result.append(stock_data)
            
            return result
        except asyncio.TimeoutError:
            logger.error("获取创业板实时行情超时")
            return []
        except Exception as e:
            logger.error(f"获取创业板实时行情失败：{e}")
            return []
    
    async def get_kc_a_board_realtime(self) -> List[Dict[str, Any]]:
        """
        获取科创板实时行情数据
        
        Returns:
            所有科创板上市公司的实时行情数据，包含：
            - 序号：股票代码
            - 代码：股票代码（688 开头）
            - 名称：股票名称
            - 最新价：当前价格
            - 涨跌幅：涨跌幅度（%）
            - 涨跌额：涨跌金额
            - 成交量：成交量（手）
            - 成交额：成交额（元）
            - 振幅：振幅（%）
            - 最高：最高价
            - 最低：最低价
            - 今开：今日开盘价
            - 昨收：昨日收盘价
            - 量比：量比
            - 换手率：换手率（%）
            - 市盈率 - 动态：动态市盈率
            - 市净率：市净率
            - 总市值：总市值（元）
            - 流通市值：流通市值（元）
            - 涨速：涨速
            - 5 分钟涨跌：5 分钟涨跌幅（%）
            - 60 日涨跌幅：60 日涨跌幅（%）
            - 年初至今涨跌幅：年初至今涨跌幅（%）
            
        API: stock_kc_a_spot_em
        数据来源：东方财富网 http://quote.eastmoney.com/center/gridlist.html#kcb_board
        限量：单次返回所有科创板的实时行情数据（约 580+ 只股票）
        """
        try:
            # 使用东方财富网科创板实时行情接口
            # API: stock_kc_a_spot_em - 获取科创板实时行情
            # 数据来源：东方财富网
            async with asyncio.timeout(15):  # 增加超时时间到 15 秒
                df = ak.stock_kc_a_spot_em()
            
            if df.empty:
                return []
            
            # 转换为字典列表
            result = []
            for _, row in df.iterrows():
                stock_data = {}
                for col in df.columns:
                    value = row[col]
                    # 处理 NaN 值
                    import math
                    if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                        stock_data[col] = None
                    else:
                        # 根据字段类型转换
                        if col in ['序号']:
                            stock_data[col] = int(value)
                        else:
                            stock_data[col] = float(value)
                
                result.append(stock_data)
            
            return result
        except asyncio.TimeoutError:
            logger.error("获取科创板实时行情超时")
            return []
        except Exception as e:
            logger.error(f"获取科创板实时行情失败：{e}")
            return []
    
    async def get_stock_spot_xq(self, symbol: str, token: Optional[str] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        """
        获取雪球个股实时行情数据
        
        Args:
            symbol: 证券代码，支持：
                - A 股个股代码：SH600000, SZ000001
                - A 股场内基金代码：SH513520
                - A 股指数：SH000001, SZ399001
                - 美股代码：AAPL, TSLA
                - 美股指数：.DJI, .IXIC, .INX
            token: 雪球访问令牌（可选）
            timeout: 超时时间（秒，可选）
            
        Returns:
            雪球个股实时行情数据，包含：
            - 代码：证券代码
            - 名称：证券名称
            - 现价：当前价格
            - 涨跌：涨跌额
            - 涨幅：涨跌幅（%）
            - 最高：最高价
            - 最低：最低价
            - 今开：今日开盘价
            - 昨收：昨日收盘价
            - 涨停：涨停价
            - 跌停：跌停价
            - 成交量：成交量
            - 成交额：成交额
            - 换手率：换手率（%）
            - 振幅：振幅（%）
            - 市盈率 (动)：动态市盈率
            - 市盈率 (静)：静态市盈率
            - 市盈率 (TTM): TTM 市盈率
            - 市净率：市净率
            - 每股收益：每股收益
            - 每股净资产：每股净资产
            - 总股本：总股本
            - 流通股：流通股本
            - 总市值：总市值
            - 流通值：流通市值
            - 52 周最高：52 周最高价
            - 52 周最低：52 周最低价
            - 股息 (TTM): 股息
            - 股息率 (TTM): 股息率
            - 今年以来涨幅：年初至今涨幅（%）
            - 时间：数据时间
            
        API: stock_individual_spot_xq
        数据来源：雪球 https://xueqiu.com/
        限量：单次获取指定 symbol 的最新行情数据
        """
        try:
            # 使用雪球个股实时行情接口
            # API: stock_individual_spot_xq(symbol, token, timeout)
            # 数据来源：雪球
            if timeout:
                async with asyncio.timeout(timeout):
                    df = ak.stock_individual_spot_xq(symbol=symbol, token=token, timeout=timeout)
            else:
                df = ak.stock_individual_spot_xq(symbol=symbol, token=token)
            
            if df.empty:
                return {}
            
            # 转换为字典格式
            result = {}
            for _, row in df.iterrows():
                item = row["item"]
                value = row["value"]
                # 尝试转换为数值类型
                if isinstance(value, str):
                    try:
                        # 尝试转换为浮点数
                        result[item] = float(value)
                    except ValueError:
                        # 保持字符串
                        result[item] = value
                else:
                    result[item] = value
            
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取雪球行情超时 {symbol}")
            return {}
        except Exception as e:
            logger.error(f"获取雪球行情失败 {symbol}: {e}")
            return {}

    async def get_stock_intraday_em(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取东方财富个股分时数据
        
        Args:
            symbol: 证券代码，如：000001
            
        Returns:
            东方财富个股分时数据，包含：
            - 时间：分时时间（如：09:15:00）
            - 成交价：成交价格
            - 手数：成交量（手）
            - 买卖盘性质：买卖盘方向
            
        特性：
        1. ✅ 最新交易日数据
        2. ✅ 包含开盘前数据
        3. ✅ 约 4400+ 条/天
        4. ✅ 10 秒超时控制
        5. ✅ 数据验证
        6. ✅ 错误处理
        """
        try:
            async with asyncio.timeout(10):
                df = ak.stock_intraday_em(symbol=symbol)
            
            if df.empty:
                return []
            
            result = []
            for _, row in df.iterrows():
                tick_data = {}
                for col in df.columns:
                    value = row[col]
                    import math
                    if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                        tick_data[col] = None
                    else:
                        if col in ['手数']:
                            tick_data[col] = int(value)
                        else:
                            tick_data[col] = float(value) if col != '时间' else str(value)
                result.append(tick_data)
            
            logger.info(f"获取东方财富分时数据成功 {symbol}: {len(result)} 条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取东方财富分时数据超时 {symbol}")
            return []
        except Exception as e:
            logger.error(f"获取东方财富分时数据失败 {symbol}: {e}")
            return []

    async def get_stock_intraday_sina(self, symbol: str, date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取新浪财经个股分时数据（大单数据）
        
        Args:
            symbol: 证券代码（带市场标识），如：sz000001, sh600000
            date: 交易日期，格式 YYYYMMDD（可选，默认最新）
            
        Returns:
            新浪财经个股分时数据，包含：
            - symbol: 证券代码
            - name: 证券名称
            - ticktime: 分时时间
            - price: 成交价格
            - volume: 成交量（手）
            - prev_price: 上一笔价格
            - kind: 买卖盘性质（D=卖盘，U=买盘，E=收盘集合竞价）
            
        特性：
        1. ✅ 大单数据（≥ 400 手）
        2. ✅ 指定交易日数据
        3. ✅ 约 800+ 条/天（大单）
        4. ✅ 10 秒超时控制
        5. ✅ 数据验证
        6. ✅ 错误处理
        """
        try:
            if date:
                async with asyncio.timeout(10):
                    df = ak.stock_intraday_sina(symbol=symbol, date=date)
            else:
                async with asyncio.timeout(10):
                    df = ak.stock_intraday_sina(symbol=symbol)
            
            if df.empty:
                return []
            
            result = []
            for _, row in df.iterrows():
                tick_data = {}
                for col in df.columns:
                    value = row[col]
                    import math
                    if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                        tick_data[col] = None
                    else:
                        if col in ['volume', 'prev_price']:
                            tick_data[col] = int(value) if value == int(value) else float(value)
                        else:
                            tick_data[col] = float(value) if col not in ['symbol', 'name', 'ticktime', 'kind'] else str(value)
                result.append(tick_data)
            
            logger.info(f"获取新浪财经分时数据成功 {symbol}: {len(result)} 条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取新浪财经分时数据超时 {symbol}")
            return []
        except Exception as e:
            logger.error(f"获取新浪财经分时数据失败 {symbol}: {e}")
            return []

    async def get_stock_zh_a_minute(
        self,
        symbol: str,
        period: str = '1',
        adjust: str = ''
    ) -> List[Dict[str, Any]]:
        """
        获取新浪财经沪深京 A 股分时数据
        
        Args:
            symbol: 股票代码，带市场标识，如：sh600519, sz000001
            period: 分钟频率，choice of {'1', '5', '15', '30', '60'}，默认 '1'
            adjust: 复权类型，默认 '' (不复权), 'qfq' (前复权), 'hfq' (后复权)
            
        Returns:
            新浪财经分时数据，包含：
            - day: 时间
            - open: 开盘价
            - high: 最高价
            - low: 最低价
            - close: 收盘价
            - volume: 成交量（手）
            - amount: 成交额
            
        特性：
        1. ✅ 支持多种频率：1/5/15/30/60 分钟
        2. ✅ 支持复权调整
        3. ✅ 最近交易日数据
        4. ✅ 10 秒超时控制
        5. ✅ 数据验证
        6. ✅ 错误处理
        """
        try:
            # 验证参数
            if period not in ['1', '5', '15', '30', '60']:
                logger.error(f"无效的周期参数：{period}")
                return []
            
            if adjust not in ['', 'qfq', 'hfq']:
                logger.error(f"无效的复权参数：{adjust}")
                return []
            
            async with asyncio.timeout(10):
                df = ak.stock_zh_a_minute(symbol=symbol, period=period, adjust=adjust)
            
            if df.empty:
                return []
            
            result = []
            for _, row in df.iterrows():
                tick_data = {}
                for col in df.columns:
                    value = row[col]
                    import math
                    if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                        tick_data[col] = None
                    else:
                        if col in ['day']:
                            tick_data[col] = str(value)
                        elif col in ['volume']:
                            tick_data[col] = int(value) if value == int(value) else float(value)
                        else:
                            tick_data[col] = float(value)
                result.append(tick_data)
            
            logger.info(f"获取新浪财经分时数据成功 {symbol} (周期={period}, 复权={adjust}): {len(result)} 条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取新浪财经分时数据超时 {symbol}")
            return []
        except Exception as e:
            logger.error(f"获取新浪财经分时数据失败 {symbol}: {e}")
            return []

    async def get_stock_zh_a_hist_min_em(
        self,
        symbol: str,
        period: str = '5',
        adjust: str = '',
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取东方财富沪深京 A 股分时数据
        
        Args:
            symbol: 股票代码，如：000001, 600519
            period: 分钟频率，choice of {'1', '5', '15', '30', '60'}，默认 '5'
            adjust: 复权类型，默认 '' (不复权), 'qfq' (前复权), 'hfq' (后复权)
                   注意：1 分钟数据只返回近 5 个交易日数据且不复权
            start_date: 开始日期时间，格式 "YYYY-MM-DD HH:MM:SS"，默认返回所有数据
            end_date: 结束日期时间，格式 "YYYY-MM-DD HH:MM:SS"，默认返回所有数据
            
        Returns:
            东方财富分时数据，根据频率不同返回不同字段：
            
            1 分钟数据：
            - 时间：datetime
            - 开盘：float
            - 收盘：float
            - 最高：float
            - 最低：float
            - 成交量：float (手)
            - 成交额：float
            - 均价：float
            
            其他频率 (5/15/30/60 分钟)：
            - 时间：datetime
            - 开盘：float
            - 收盘：float
            - 最高：float
            - 最低：float
            - 涨跌幅：float (%)
            - 涨跌额：float
            - 成交量：float (手)
            - 成交额：float
            - 振幅：float (%)
            - 换手率：float (%)
            
        特性：
        1. ✅ 支持多种频率：1/5/15/30/60 分钟
        2. ✅ 支持复权调整
        3. ✅ 支持自定义时间范围
        4. ✅ 1 分钟数据仅返回近 5 个交易日
        5. ✅ 10 秒超时控制
        6. ✅ 数据验证
        7. ✅ 错误处理
        """
        try:
            # 验证参数
            if period not in ['1', '5', '15', '30', '60']:
                logger.error(f"无效的周期参数：{period}")
                return []
            
            if adjust not in ['', 'qfq', 'hfq']:
                logger.error(f"无效的复权参数：{adjust}")
                return []
            
            # 1 分钟数据只能不复权
            if period == '1' and adjust != '':
                logger.warning("1 分钟数据只支持不复权，自动调整为空字符串")
                adjust = ''
            
            # 日期格式转换（兼容处理）
            def format_datetime(date_str):
                if not date_str:
                    return ""
                # 支持多种格式
                date_str = date_str.replace("/", "-").replace(".", "-")
                if len(date_str) == 10:  # YYYY-MM-DD
                    date_str += " 09:30:00"
                return date_str
            
            start_dt = format_datetime(start_date) if start_date else ""
            end_dt = format_datetime(end_date) if end_date else ""
            
            async with asyncio.timeout(10):
                df = ak.stock_zh_a_hist_min_em(
                    symbol=symbol,
                    period=period,
                    adjust=adjust,
                    start_date=start_dt if start_dt else "1979-09-01 09:32:00",
                    end_date=end_dt if end_dt else "2222-01-01 09:32:00"
                )
            
            if df.empty:
                return []
            
            result = []
            for _, row in df.iterrows():
                tick_data = {}
                for col in df.columns:
                    value = row[col]
                    import math
                    if value is None or value == '' or value == '-' or (isinstance(value, float) and math.isnan(value)):
                        tick_data[col] = None
                    else:
                        if col in ['时间', 'day']:
                            tick_data[col] = str(value)
                        elif col in ['成交量', 'volume']:
                            tick_data[col] = int(value) if value == int(value) else float(value)
                        else:
                            try:
                                tick_data[col] = float(value)
                            except (ValueError, TypeError):
                                tick_data[col] = str(value)
                result.append(tick_data)
            
            logger.info(f"获取东方财富分时数据成功 {symbol} (周期={period}, 复权={adjust}): {len(result)} 条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取东方财富分时数据超时 {symbol}")
            return []
        except Exception as e:
            logger.error(f"获取东方财富分时数据失败 {symbol}: {e}")
            return []

    # ========== 新增 API 方法（对应 Tushare） ==========
    
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """
        获取周线 K 线数据（使用东方财富 API）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型（qfq/hfq/none）
            
        Returns:
            周线 K 线数据列表
        """
        try:
            # 使用东方财富的周线数据 API
            async with asyncio.timeout(10):
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="weekly",
                    start_date=start_date.replace("-", "") if start_date else "19900101",
                    end_date=end_date.replace("-", "") if end_date else "20991231",
                    adjust=adjust if adjust in ['qfq', 'hfq'] else ""
                )
            
            if df.empty:
                return []
            
            klines = []
            for _, row in df.iterrows():
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row["日期"])),
                    open=float(row["开盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    close=float(row["收盘"]),
                    volume=float(row["成交量"])
                ))
            
            logger.info(f"获取周线数据成功 {code}: {len(klines)}条")
            return klines
        except asyncio.TimeoutError:
            logger.error(f"获取周线数据超时 {code}")
            return []
        except Exception as e:
            logger.error(f"获取周线数据失败 {code}: {e}")
            return []

    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """
        获取月线 K 线数据（使用东方财富 API）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
        """
        try:
            async with asyncio.timeout(10):
                df = ak.stock_zh_a_hist(
                    symbol=code,
                    period="monthly",
                    start_date=start_date.replace("-", "") if start_date else "19900101",
                    end_date=end_date.replace("-", "") if end_date else "20991231",
                    adjust=adjust if adjust in ['qfq', 'hfq'] else ""
                )
            
            if df.empty:
                return []
            
            klines = []
            for _, row in df.iterrows():
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row["日期"])),
                    open=float(row["开盘"]),
                    high=float(row["最高"]),
                    low=float(row["最低"]),
                    close=float(row["收盘"]),
                    volume=float(row["成交量"])
                ))
            
            logger.info(f"获取月线数据成功 {code}: {len(klines)}条")
            return klines
        except asyncio.TimeoutError:
            logger.error(f"获取月线数据超时 {code}")
            return []
        except Exception as e:
            logger.error(f"获取月线数据失败 {code}: {e}")
            return []

    async def get_top_list(self, trade_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取龙虎榜数据（使用东方财富 API）
        
        Args:
            trade_date: 交易日期（YYYYMMDD）
            
        Returns:
            龙虎榜数据列表
        """
        try:
            # 使用东方财富龙虎榜 API
            date_str = trade_date if trade_date else datetime.now().strftime("%Y%m%d")
            
            async with asyncio.timeout(10):
                df = ak.stock_lhb_detail_em(trade_date=date_str)
            
            if df.empty:
                return []
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    "code": row["代码"] if "代码" in row else None,
                    "name": row["名称"] if "名称" in row else None,
                    "close": float(row["收盘价"]) if "收盘价" in row else None,
                    "change_pct": float(row["涨跌幅"]) if "涨跌幅" in row else None,
                    "amount": float(row["成交额"]) if "成交额" in row else None,
                    "net_in": float(row["净额"]) if "净额" in row else None,
                    "buy_amount": float(row["买入额"]) if "买入额" in row else None,
                    "sell_amount": float(row["卖出额"]) if "卖出额" in row else None
                })
            
            logger.info(f"获取龙虎榜数据成功：{len(result)}条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取龙虎榜数据超时")
            return []
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败：{e}")
            return []

    async def get_forecast(self, code: str, ann_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取业绩预告数据（使用东方财富 API）
        
        Args:
            code: 股票代码
            ann_date: 公告日期
            
        Returns:
            业绩预告数据列表
        """
        try:
            # 使用东方财富业绩预告 API
            async with asyncio.timeout(10):
                df = ak.stock_earnings_forecast_em(symbol=code)
            
            if df.empty:
                return []
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    "code": code,
                    "ann_date": str(row["公告日期"]) if "公告日期" in row else ann_date,
                    "end_date": str(row["报告期"]) if "报告期" in row else None,
                    "type": row["类型"] if "类型" in row else None,
                    "net_profit_min": float(row["净利润下限"]) if "净利润下限" in row else None,
                    "net_profit_max": float(row["净利润上限"]) if "净利润上限" in row else None,
                    "net_profit_yoy_min": float(row["净利润下限同比"]) if "净利润下限同比" in row else None,
                    "net_profit_yoy_max": float(row["净利润上限同比"]) if "净利润上限同比" in row else None
                })
            
            logger.info(f"获取业绩预告数据成功 {code}: {len(result)}条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取业绩预告数据超时 {code}")
            return []
        except Exception as e:
            logger.error(f"获取业绩预告数据失败 {code}: {e}")
            return []
    
    async def get_moneyflow(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取资金流向数据（使用东方财富 API）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            资金流向数据列表，包含：
            - 日期
            - 收盘价
            - 涨跌幅
            - 主力净流入
            - 主力净流入占比
            - 超大单净流入
            - 大单净流入
            - 中单净流入
            - 小单净流入等
        """
        try:
            # 使用东方财富资金流向 API
            async with asyncio.timeout(10):
                df = ak.stock_individual_fund_flow(symbol=code)
            
            if df.empty:
                return []
            
            result = []
            for _, row in df.iterrows():
                result.append({
                    "code": code,
                    "date": str(row["日期"]) if "日期" in row else None,
                    "close": float(row["收盘价"]) if "收盘价" in row else None,
                    "change_pct": float(row["涨跌幅"]) if "涨跌幅" in row else None,
                    "main_net_in": float(row["主力净流入"]) if "主力净流入" in row else None,
                    "main_net_in_pct": float(row["主力净流入占比"]) if "主力净流入占比" in row else None,
                    "super_net_in": float(row["超大单净流入"]) if "超大单净流入" in row else None,
                    "big_net_in": float(row["大单净流入"]) if "大单净流入" in row else None,
                    "mid_net_in": float(row["中单净流入"]) if "中单净流入" in row else None,
                    "small_net_in": float(row["小单净流入"]) if "小单净流入" in row else None
                })
            
            logger.info(f"获取资金流向数据成功 {code}: {len(result)}条")
            return result
        except asyncio.TimeoutError:
            logger.error(f"获取资金流向数据超时 {code}")
            return []
        except Exception as e:
            logger.error(f"获取资金流向数据失败 {code}: {e}")
            return []
