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
from app.utils.tushare_points_manager import get_points_manager
from app.utils.tushare_api_registry import api_registry, APIGroup
from app.utils.tushare_cache_stats import api_call_cache


class TushareAdapter(BaseDataAdapter):
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._pro = None
        self._points_manager = None
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.TUSHARE
    
    async def initialize(self) -> bool:
        try:
            token = self.config.get("token") or settings.TUSHARE_TOKEN
            if not token:
                logger.warning("Tushare 未配置 token，跳过初始化")
                return False
            
            logger.info(f"Tushare Token 已加载：{token[:10]}...{token[-5:]}")
            logger.info(f"Tushare 积分：{settings.TUSHARE_POINTS}分")
            ts.set_token(token)
            self._pro = ts.pro_api()
            
            # 初始化积分管理器
            try:
                self._points_manager = get_points_manager()
                perm_summary = self._points_manager.get_permission_summary()
                logger.info(f"Tushare 可用接口：{perm_summary['available_count']} 个")
                if perm_summary.get('next_level'):
                    logger.info(f"距离下一等级还差：{perm_summary['points_to_next']} 分")
            except Exception as e:
                logger.warning(f"积分管理器初始化失败：{e}")
            
            # 测试连接
            try:
                df = self._pro.trade_cal(exchange='', start_date='20240101', end_date='20240107', fields='pre_cal_flag')
                if not df.empty:
                    self._is_initialized = True
                    logger.info("Tushare 适配器初始化成功")
                    
                    # 自动注册所有 API 方法
                    try:
                        from app.adapters.tushare_api_auto_register import auto_register_tushare_apis
                        auto_register_tushare_apis(self)
                    except Exception as reg_error:
                        logger.warning(f"API 自动注册失败：{reg_error}")
                    
                    return True
                else:
                    logger.warning("Tushare 连接测试失败，无法获取交易日历数据")
                    return False
            except Exception as test_error:
                logger.error(f"Tushare 连接测试失败：{test_error}")
                logger.error("可能原因：Token 无效、积分不足或网络问题")
                return False
                
        except Exception as e:
            logger.error(f"Tushare 适配器初始化失败：{e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    async def close(self) -> None:
        self._pro = None
        self._is_initialized = False
        logger.info("Tushare适配器已关闭")
    
    @api_call_cache(ttl=600)  # 缓存 10 分钟
    async def get_stock_list(self, market: Optional[str] = None) -> List[StockBasicInfo]:
        try:
            df = self._pro.stock_basic(exchange="", list_status="L", fields="ts_code,symbol,name,area,industry,list_date")
            stocks = []
            for row in df.itertuples(index=False):
                code = row.symbol
                market_tag = row.ts_code.split(".")[1] if "." in row.ts_code else ("SH" if code.startswith("6") else "SZ")
                stocks.append(StockBasicInfo(
                    code=code,
                    name=row.name,
                    market=market_tag,
                    industry=getattr(row, 'industry', None),
                    area=getattr(row, 'area', None),
                    list_date=getattr(row, 'list_date', None)
                ))
            return stocks
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return []
    
    @api_call_cache(ttl=600)  # 缓存 10 分钟
    async def get_stock_info(self, code: str) -> Optional[StockBasicInfo]:
        try:
            # 检查权限
            if self._points_manager:
                if not self._points_manager.check_and_log_permission("stock_basic", "akshare"):
                    return None
            
            ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
            df = self._pro.stock_basic(ts_code=ts_code, fields="ts_code,symbol,name,area,industry,list_date,total_mv,circ_mv")
            
            if df.empty:
                return None
            
            row = df.iloc[0]
            logger.info(f"获取股票信息成功 {code}: {row['name']}")
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
    
    @api_call_cache(ttl=300)  # 缓存 5 分钟
    async def get_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        try:
            # 检查积分权限
            if self._points_manager:
                if not self._points_manager.check_and_log_permission("daily", "akshare"):
                    # 无权限，返回空列表，让上层切换到其他数据源
                    logger.warning(f"Tushare 无权限调用 daily 接口，使用备选数据源")
                    return []
            
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
            
            if adjust == "qfq" and self._points_manager:
                # 检查复权因子权限
                if self._points_manager.has_permission("adj_factor"):
                    adj_factor = self._pro.adj_factor(ts_code=ts_code)
                    df = df.merge(adj_factor, on="ts_code")
                    df["adj_factor"] = df["adj_factor"].fillna(1)
                    for col in ["open", "high", "low", "close"]:
                        df[col] = df[col] * df["adj_factor"]
                else:
                    logger.warning("积分不足，无法获取复权因子，使用非复权数据")
            
            klines = []
            for row in df.sort_values("trade_date").itertuples(index=False):
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row.trade_date)),
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=float(row.vol),
                    amount=float(row.amount) * 1000 if hasattr(row, 'amount') else None
                ))
            return klines
        except Exception as e:
            logger.error(f"获取 K 线数据失败 {code}: {e}")
            return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        try:
            # 检查权限
            if self._points_manager:
                if not self._points_manager.check_and_log_permission("daily", "akshare"):
                    return {}
            
            ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
            df = self._pro.daily(ts_code=ts_code, limit=1)
            
            if df.empty:
                return {}
            
            row = df.iloc[0]
            logger.debug(f"获取实时行情成功 {code}")
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
    
    @api_call_cache(ttl=1800)  # 缓存 30 分钟
    async def get_sector_list(self, sector_type: str = "industry") -> List[SectorInfo]:
        try:
            df = self._pro.index_classify(level="L1", src="SW")
            sectors = []
            for row in df.itertuples(index=False):
                sectors.append(SectorInfo(
                    code=str(row.index_code),
                    name=row.industry_name,
                    sector_type="industry"
                ))
            return sectors
        except Exception as e:
            logger.error(f"获取板块列表失败: {e}")
            return []
    
    @api_call_cache(ttl=1800)  # 缓存 30 分钟
    async def get_sector_components(self, sector_code: str) -> List[str]:
        try:
            # 检查权限
            if self._points_manager:
                if not self._points_manager.check_and_log_permission("index_member", "akshare"):
                    return []
            
            df = self._pro.index_member(index_code=sector_code)
            components = [code.split(".")[0] for code in df["con_code"].tolist()]
            logger.info(f"获取板块成分股成功 {sector_code}: {len(components)}只股票")
            return components
        except Exception as e:
            logger.error(f"获取板块成分股失败 {sector_code}: {e}")
            return []
    
    @api_call_cache(ttl=600)  # 缓存 10 分钟
    async def get_chip_data(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[ChipData]:
        try:
            # 检查权限
            if self._points_manager:
                if not self._points_manager.check_and_log_permission("stk_holdernumber", "akshare"):
                    return []
            
            ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
            df = self._pro.stk_holdernumber(ts_code=ts_code)
            
            chip_data = []
            for row in df.itertuples(index=False):
                date = str(row.ann_date)
                if start_date and date < start_date.replace("-", ""):
                    continue
                if end_date and date > end_date.replace("-", ""):
                    continue
                chip_data.append(ChipData(
                    code=code,
                    date=self.format_date(date),
                    shareholder_count=float(row.holder_num)
                ))
            logger.info(f"获取筹码数据成功 {code}: {len(chip_data)}条")
            return chip_data
        except Exception as e:
            logger.error(f"获取筹码数据失败 {code}: {e}")
            return []

    @api_call_cache(ttl=300)  # 缓存 5 分钟
    async def get_market_index_kline(
        self,
        index_code: str = "000001",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[KLineData]:
        """获取大盘指数 K 线数据"""
        try:
            # 检查权限
            if self._points_manager:
                if not self._points_manager.check_and_log_permission("index_daily", "akshare"):
                    return []
            
            # 映射指数代码到 Tushare 格式
            index_map = {
                "000001": "000001.SH",  # 上证指数
                "000003": "000003.SH",  # 上证 A 股
                "000004": "000004.SH",  # 上证 B 股
                "000016": "000016.SH",  # 上证 50
                "000300": "000300.SH",  # 沪深 300
                "000905": "000905.SH",  # 中证 500
                "399001": "399001.SZ",  # 深证成指
                "399005": "399005.SZ",  # 中小板指
                "399006": "399006.SZ",  # 创业板指
            }
            
            ts_code = index_map.get(index_code, index_code)
            if "." not in ts_code:
                if index_code.startswith(("000", "600")):
                    ts_code = f"{index_code}.SH"
                else:
                    ts_code = f"{index_code}.SZ"
            
            df = self._pro.index_daily(
                ts_code=ts_code,
                start_date=start_date.replace("-", "") if start_date else None,
                end_date=end_date.replace("-", "") if end_date else None
            )
            
            klines = []
            for row in df.sort_values("trade_date").itertuples(index=False):
                klines.append(KLineData(
                    code=index_code,
                    date=self.format_date(str(row.trade_date)),
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=float(row.vol)
                ))
            logger.info(f"获取指数 K 线数据成功 {index_code}: {len(klines)}条")
            return klines
        except Exception as e:
            logger.error(f"获取指数 K 线数据失败 {index_code}: {e}")
            return []

    async def get_stock_intraday_em(self, symbol: str) -> List[Dict[str, Any]]:
        """
        获取个股分时数据（1 分钟）
        Tushare 使用 intraday 接口（需要 5000 积分）
        """
        try:
            # 检查积分权限（分钟线需要 5000 分）
            if self._points_manager:
                if not self._points_manager.check_and_log_permission("intraday", "akshare"):
                    logger.warning(f"Tushare 分时数据需要 5000 积分，当前只有{self._points_manager.get_points()}分，使用备选数据源")
                    return []
            
            ts_code = f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"
            df = self._pro.intraday(ts_code=ts_code)
            
            if df.empty:
                return []
            
            result = []
            for row in df.itertuples(index=False):
                tick_data = {
                    "时间": str(row.trade_time),
                    "成交价": float(row.close),
                    "手数": int(row.vol),
                    "买卖盘性质": "B" if getattr(row, 'buy_sm', 0) > getattr(row, 'sell_sm', 0) else "S"
                }
                result.append(tick_data)
            
            logger.info(f"获取 Tushare 分时数据成功 {symbol}: {len(result)} 条")
            return result
        except Exception as e:
            logger.error(f"获取 Tushare 分时数据失败 {symbol}: {e}")
            return []

    async def get_stock_zh_a_minute(
        self,
        symbol: str,
        period: str = '1',
        adjust: str = ''
    ) -> List[Dict[str, Any]]:
        """
        获取多周期分钟 K 线数据
        Tushare 使用 bar 接口（需要 5000 积分）
        """
        try:
            # 检查积分权限（分钟线需要 5000 分）
            if self._points_manager:
                if not self._points_manager.check_and_log_permission("intraday", "akshare"):
                    logger.warning(f"Tushare 分钟线需要 5000 积分，当前只有{self._points_manager.get_points()}分，使用备选数据源")
                    return []
            
            ts_code = f"{symbol}.SH" if symbol.startswith("6") else f"{symbol}.SZ"
            
            # 周期映射
            freq_map = {
                '1': '1min',
                '5': '5min',
                '15': '15min',
                '30': '30min',
                '60': '60min'
            }
            freq = freq_map.get(period, '1min')
            
            df = self._pro.bar(
                ts_code=ts_code,
                freq=freq,
                adj=adjust if adjust else None
            )
            
            if df.empty:
                return []
            
            result = []
            for row in df.sort_values("trade_time").itertuples(index=False):
                tick_data = {
                    "day": str(row.trade_time),
                    "open": float(row.open),
                    "high": float(row.high),
                    "low": float(row.low),
                    "close": float(row.close),
                    "volume": float(row.vol),
                    "amount": float(row.amount) * 1000 if hasattr(row, 'amount') else None
                }
                result.append(tick_data)
            
            logger.info(f"获取 Tushare 分钟 K 线成功 {symbol} (周期={period}, 复权={adjust}): {len(result)} 条")
            return result
        except Exception as e:
            logger.error(f"获取 Tushare 分钟 K 线失败 {symbol}: {e}")
            return []

    async def get_all_a_shares_realtime(self) -> List[Dict[str, Any]]:
        """获取全市场 A 股实时行情"""
        try:
            # 检查权限
            if self._points_manager:
                if not self._points_manager.check_and_log_permission("sina_md", "akshare"):
                    return []
            
            # 获取实时行情快照
            df = self._pro.sina_md(ts_code="", fields="ts_code,symbol,name,price,change,pct_chg,volume,amount")
            
            if df.empty:
                return []
            
            result = []
            for row in df.itertuples(index=False):
                stock_data = {
                    "代码": row.symbol,
                    "名称": row.name,
                    "最新价": float(row.price) if pd.notna(row.price) else None,
                    "涨跌幅": float(row.pct_chg) if pd.notna(row.pct_chg) else None,
                    "涨跌额": float(row.change) if pd.notna(row.change) else None,
                    "成交量": float(row.volume) if pd.notna(row.volume) else None,
                    "成交额": float(row.amount) if pd.notna(row.amount) else None
                }
                result.append(stock_data)
            
            logger.info(f"获取 Tushare 全市场实时行情成功：{len(result)} 只股票")
            return result
        except Exception as e:
            logger.error(f"获取 Tushare 全市场实时行情失败：{e}")
            return []

    # ========== 新增 API 方法 ==========
    
    @api_call_cache(ttl=600)  # 缓存 10 分钟
    async def get_weekly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """
        获取周线 K 线数据（需要 2000 积分）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型（qfq/hfq/none）
            
        Returns:
            周线 K 线数据列表
        """
        try:
            # 检查适配器是否已初始化
            if not self._is_initialized or not self._pro:
                logger.error("Tushare 适配器未初始化")
                return []
            
            # 检查权限
            if not api_registry.check_permission("get_weekly"):
                logger.warning(f"Tushare 周线需要 2000 积分，当前只有{settings.TUSHARE_POINTS}分，使用备选数据源")
                return []
            
            ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
            adj_map = {"qfq": None, "hfq": "hfq", "": None}
            
            df = self._pro.weekly(
                ts_code=ts_code,
                start_date=start_date.replace("-", "") if start_date else None,
                end_date=end_date.replace("-", "") if end_date else None,
                adj=adj_map.get(adjust)
            )
            
            klines = []
            for row in df.sort_values("trade_date").itertuples(index=False):
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row.trade_date)),
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=float(row.vol)
                ))
            
            logger.info(f"获取周线数据成功 {code}: {len(klines)}条")
            return klines
        except Exception as e:
            logger.error(f"获取周线数据失败 {code}: {e}")
            return []

    @api_call_cache(ttl=600)  # 缓存 10 分钟
    async def get_monthly_kline(
        self,
        code: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        adjust: str = "qfq"
    ) -> List[KLineData]:
        """
        获取月线 K 线数据（需要 2000 积分）
        
        Args:
            code: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            adjust: 复权类型
        """
        try:
            # 检查适配器是否已初始化
            if not self._is_initialized or not self._pro:
                logger.error("Tushare 适配器未初始化")
                return []
            
            if not api_registry.check_permission("get_monthly"):
                logger.warning(f"Tushare 月线需要 2000 积分，使用备选数据源")
                return []
            
            ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
            adj_map = {"qfq": None, "hfq": "hfq", "": None}
            
            df = self._pro.monthly(
                ts_code=ts_code,
                start_date=start_date.replace("-", "") if start_date else None,
                end_date=end_date.replace("-", "") if end_date else None,
                adj=adj_map.get(adjust)
            )
            
            klines = []
            for row in df.sort_values("trade_date").itertuples(index=False):
                klines.append(KLineData(
                    code=code,
                    date=self.format_date(str(row.trade_date)),
                    open=float(row.open),
                    high=float(row.high),
                    low=float(row.low),
                    close=float(row.close),
                    volume=float(row.vol)
                ))
            
            logger.info(f"获取月线数据成功 {code}: {len(klines)}条")
            return klines
        except Exception as e:
            logger.error(f"获取月线数据失败 {code}: {e}")
            return []

    async def get_top_list(self, trade_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取龙虎榜数据（需要 200 积分）
        
        Args:
            trade_date: 交易日期（YYYYMMDD）
        """
        try:
            # 检查适配器是否已初始化
            if not self._is_initialized or not self._pro:
                logger.error("Tushare 适配器未初始化")
                return []
            
            if not api_registry.check_permission("get_top_list"):
                logger.warning(f"Tushare 龙虎榜需要 200 积分，使用备选数据源")
                return []
            
            df = self._pro.top_list(trade_date=trade_date if trade_date else None)
            
            result = []
            for row in df.itertuples(index=False):
                result.append({
                    "code": row.ts_code.split(".")[0],
                    "name": row.name,
                    "close": float(row.close),
                    "change_pct": float(row.pct_chg),
                    "amount": float(row.amount),
                    "net_in": float(row.net_in),
                    "buy_amount": float(row.buy_amount),
                    "sell_amount": float(row.sell_amount)
                })
            
            logger.info(f"获取龙虎榜数据成功：{len(result)}条")
            return result
        except Exception as e:
            logger.error(f"获取龙虎榜数据失败：{e}")
            return []

    async def get_forecast(self, code: str, ann_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取业绩预告数据（需要 800 积分）
        
        Args:
            code: 股票代码
            ann_date: 公告日期
        """
        try:
            # 检查适配器是否已初始化
            if not self._is_initialized or not self._pro:
                logger.error("Tushare 适配器未初始化")
                return []
            
            if not api_registry.check_permission("get_forecast"):
                logger.warning(f"Tushare 业绩预告需要 800 积分，使用备选数据源")
                return []
            
            ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
            df = self._pro.forecast(ts_code=ts_code, ann_date=ann_date if ann_date else None)
            
            result = []
            for row in df.itertuples(index=False):
                result.append({
                    "code": code,
                    "ann_date": str(row.ann_date),
                    "end_date": str(row.end_date),
                    "type": row.type,
                    "net_profit_min": float(row.net_profit_min),
                    "net_profit_max": float(row.net_profit_max),
                    "net_profit_yoy_min": float(row.net_profit_yoy_min),
                    "net_profit_yoy_max": float(row.net_profit_yoy_max)
                })
            
            logger.info(f"获取业绩预告数据成功 {code}: {len(result)}条")
            return result
        except Exception as e:
            logger.error(f"获取业绩预告数据失败 {code}: {e}")
            return []

    async def get_moneyflow(self, code: str, trade_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取资金流向数据（需要 5000 积分）
        
        Args:
            code: 股票代码
            trade_date: 交易日期
        """
        try:
            # 检查适配器是否已初始化
            if not self._is_initialized or not self._pro:
                logger.error("Tushare 适配器未初始化")
                return []
            
            if not api_registry.check_permission("get_moneyflow"):
                logger.warning(f"Tushare 资金流向需要 5000 积分，使用备选数据源")
                return []
            
            ts_code = f"{code}.SH" if code.startswith("6") else f"{code}.SZ"
            df = self._pro.moneyflow(ts_code=ts_code, trade_date=trade_date if trade_date else None)
            
            result = []
            for row in df.itertuples(index=False):
                result.append({
                    "code": code,
                    "trade_date": str(row.trade_date),
                    "buy_sm_amount": float(row.buy_sm_amount) if hasattr(row, 'buy_sm_amount') else None,
                    "sell_sm_amount": float(row.sell_sm_amount) if hasattr(row, 'sell_sm_amount') else None,
                    "buy_md_amount": float(row.buy_md_amount) if hasattr(row, 'buy_md_amount') else None,
                    "sell_md_amount": float(row.sell_md_amount) if hasattr(row, 'sell_md_amount') else None,
                    "buy_lg_amount": float(row.buy_lg_amount) if hasattr(row, 'buy_lg_amount') else None,
                    "sell_lg_amount": float(row.sell_lg_amount) if hasattr(row, 'sell_lg_amount') else None,
                    "buy_elg_amount": float(row.buy_elg_amount) if hasattr(row, 'buy_elg_amount') else None,
                    "sell_elg_amount": float(row.sell_elg_amount) if hasattr(row, 'sell_elg_amount') else None,
                    "net_mf_amount": float(row.net_mf_amount) if hasattr(row, 'net_mf_amount') else None
                })
            
            logger.info(f"获取资金流向数据成功 {code}: {len(result)}条")
            return result
        except Exception as e:
            logger.error(f"获取资金流向数据失败 {code}: {e}")
            return []
    
    async def get_market_moneyflow_dc(
        self,
        trade_date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        获取大盘资金流向数据（东方财富数据源，        接口：moneyflow_mkt_dc
        积分：120积分可试用，6000积分可正式调取
        
        Args:
            trade_date: 交易日期（YYYYMMDD格式）
            start_date: 开始日期（YYYYMMDD格式）
            end_date: 结束日期（YYYYMMDD格式）
            
        Returns:
            大盘资金流向数据列表
        """
        try:
            # 检查适配器是否已初始化
            if not self._is_initialized or not self._pro:
                logger.error("Tushare 适配器未初始化")
                return []
            
            # 检查权限（120积分可试用，6000积分可正式调取）
            if self._points_manager:
                if not self._points_manager.check_and_log_permission("moneyflow_mkt_dc", "akshare"):
                    logger.warning(f"Tushare 大盘资金流向需要 6000 积分，当前只有{self._points_manager.get_points()}分，使用备选数据源")
                    return []
            
            # 调用 Tushare API
            df = await asyncio.to_thread(
                self._pro.moneyflow_mkt_dc,
                trade_date=trade_date,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                return []
            
            result = []
            for row in df.itertuples(index=False):
                result.append({
                    "trade_date": str(row.trade_date),
                    "close_sh": float(row.close_sh) if pd.notna(row.close_sh) else None,
                    "pct_change_sh": float(row.pct_change_sh) if pd.notna(row.pct_change_sh) else None,
                    "close_sz": float(row.close_sz) if pd.notna(row.close_sz) else None,
                    "pct_change_sz": float(row.pct_change_sz) if pd.notna(row.pct_change_sz) else None,
                    "net_amount": float(row.net_amount) if pd.notna(row.net_amount) else None,
                    "net_amount_rate": float(row.net_amount_rate) if pd.notna(row.net_amount_rate) else None,
                    "buy_elg_amount": float(row.buy_elg_amount) if pd.notna(row.buy_elg_amount) else None,
                    "buy_elg_amount_rate": float(row.buy_elg_amount_rate) if pd.notna(row.buy_elg_amount_rate) else None,
                    "buy_lg_amount": float(row.buy_lg_amount) if pd.notna(row.buy_lg_amount) else None,
                    "buy_lg_amount_rate": float(row.buy_lg_amount_rate) if pd.notna(row.buy_lg_amount_rate) else None,
                    "buy_md_amount": float(row.buy_md_amount) if pd.notna(row.buy_md_amount) else None,
                    "buy_md_amount_rate": float(row.buy_md_amount_rate) if pd.notna(row.buy_md_amount_rate) else None,
                    "buy_sm_amount": float(row.buy_sm_amount) if pd.notna(row.buy_sm_amount) else None,
                    "buy_sm_amount_rate": float(row.buy_sm_amount_rate) if pd.notna(row.buy_sm_amount_rate) else None,
                })
            
            logger.info(f"获取大盘资金流向数据成功：{len(result)}条")
            return result
        except Exception as e:
            logger.error(f"获取大盘资金流向数据失败：{e}")
            return []
