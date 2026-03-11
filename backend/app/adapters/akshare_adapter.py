from typing import Optional, List, Dict, Any
import akshare as ak
import pandas as pd
from loguru import logger
import time
from datetime import timedelta

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
            
            # 保存到缓存
            self._set_to_cache(cache_key, klines, 'kline')
            
            return klines
        except Exception as e:
            logger.error(f"获取 K 线数据失败 {code}: {e}")
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
