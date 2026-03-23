"""东方财富数据适配器

提供东方财富盘口异动、涨停板行情等实时数据
"""
from typing import Optional, List, Dict, Any
import asyncio
import aiohttp
from datetime import datetime
from loguru import logger
import pandas as pd

from .base import BaseDataAdapter, DataSourceType
from ..models.unified_models import (
    StockChanges, StockBoardChange, StockZtPool, MarketChanges,
    StockZtPrevious, StockZtStrong, StockZtSubNew,
    StockComment, StockCommentDetailInstitution, StockCommentDetailScore,
    StockResearchReport, StockNotice, StockBalanceSheet, StockProfitSheet, StockCashFlowSheet,
    StockFinancialIndicator, StockInfoA, StockInfoSH, StockInfoSZ, StockInfoBJ,
    StockIndustryClfHistSW, StockIndustryPERatio, StockHoldNumCNInfo, StockPriceJS,
    StockAConestionLG, StockEBSLG, StockBuffettIndexLG,
    StockZhValuationBaidu, StockValueEM, StockZhVoteBaidu,
    StockAHighLowStatistics, StockABelowNetAssetStatistics,
    StockDzjySctj, StockDzjyMrmx,
    StockMarginRatioPa, StockMarginAccountInfo,
    StockMarginSse, StockMarginDetailSse, StockMarginSzse, StockMarginDetailSzse,
    StockMarginUnderlyingInfoSzse, StockProfitForecastEm,
    StockBoardIndustryNameEm, StockBoardIndustrySpotEm, StockBoardIndustryConsEm
)


class EastMoneyAdapter(BaseDataAdapter):
    """东方财富数据适配器
    
    数据源：
    - 盘口异动数据：http://quote.eastmoney.com/changes/
    - 涨停板行情：https://quote.eastmoney.com/ztb/detail
    """
    
    # 异动类型映射
    CHANGE_TYPES = {
        'rocket': '火箭发射',
        'rebound': '快速反弹',
        'big_buy': '大笔买入',
        'limit_up': '封涨停板',
        'open_limit_down': '打开跌停板',
        'have_big_buy': '有大买盘',
        'call_auction_up': '竞价上涨',
        'high_open_5day': '高开 5 日线',
        'up_gap': '向上缺口',
        'new_60day_high': '60 日新高',
        'big_60day_up': '60 日大幅上涨',
        'accel_down': '加速下跌',
        'high_dive': '高台跳水',
        'big_sell': '大笔卖出',
        'limit_down': '封跌停板',
        'open_limit_up': '打开涨停板',
        'have_big_sell': '有大卖盘',
        'call_auction_down': '竞价下跌',
        'low_open_5day': '低开 5 日线',
        'down_gap': '向下缺口',
        'new_60day_low': '60 日新低',
        'big_60day_down': '60 日大幅下跌',
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self._session: Optional[aiohttp.ClientSession] = None
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: Dict[str, float] = {}
        self._cache_ttl = 60  # 60 秒缓存
    
    @property
    def source_type(self) -> DataSourceType:
        return DataSourceType.EASTMONEY
    
    async def initialize(self) -> bool:
        """初始化东方财富适配器"""
        try:
            self._session = aiohttp.ClientSession()
            self._is_initialized = True
            logger.info("东方财富适配器初始化成功")
            return True
        except Exception as e:
            logger.error(f"东方财富适配器初始化失败：{e}")
            return False
    
    async def close(self) -> None:
        """关闭连接"""
        if self._session:
            await self._session.close()
        self._is_initialized = False
        logger.info("东方财富适配器已关闭")
    
    def _get_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存 key"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}={v}")
        return "_".join(key_parts)
    
    def _get_from_cache(self, key: str) -> Optional[Any]:
        """从缓存获取数据"""
        import time
        if key not in self._cache:
            return None
        
        timestamp = self._cache_timestamp.get(key, 0)
        if time.time() - timestamp > self._cache_ttl:
            del self._cache[key]
            del self._cache_timestamp[key]
            return None
        
        return self._cache[key]
    
    def _set_to_cache(self, key: str, value: Any):
        """设置缓存"""
        import time
        self._cache[key] = value
        self._cache_timestamp[key] = time.time()
    
    async def _fetch_json(self, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """异步获取 JSON 数据"""
        if not self._session:
            logger.error("HTTP session 未初始化")
            return None
        
        try:
            async with self._session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    logger.error(f"请求失败：{resp.status}")
                    return None
        except asyncio.TimeoutError:
            logger.error(f"请求超时：{url}")
            return None
        except Exception as e:
            logger.error(f"请求异常：{e}")
            return None
    
    async def get_stock_changes(self, symbol: str = "大笔买入") -> List[StockChanges]:
        """获取盘口异动数据
        
        Args:
            symbol: 异动类型，如"大笔买入"、"火箭发射"等
        
        Returns:
            盘口异动数据列表
        """
        # 缓存检查
        cache_key = self._get_cache_key('changes', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        # 东方财富盘口异动 API（模拟）
        # 实际实现需要调用东方财富的 API 接口
        # 这里使用 AKShare 作为示例
        try:
            import akshare as ak
            
            # 使用 AKShare 获取数据（同步调用转异步）
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_changes_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            changes = []
            for _, row in df.iterrows():
                changes.append(StockChanges(
                    time=str(row.get('时间', '')),
                    code=str(row.get('代码', '')),
                    name=str(row.get('名称', '')),
                    board=str(row.get('板块', '')),
                    related_info=str(row.get('相关信息', '')),
                    change_type=symbol
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, changes)
            
            logger.info(f"获取盘口异动数据成功：{symbol}, 共{len(changes)}条")
            return changes
            
        except Exception as e:
            logger.error(f"获取盘口异动数据失败：{e}")
            return []
    
    async def get_board_changes(self) -> List[StockBoardChange]:
        """获取板块异动详情
        
        Returns:
            板块异动数据列表
        """
        # 缓存检查
        cache_key = self._get_cache_key('board_changes')
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_board_change_em()
            )
            
            if df is None or df.empty:
                return []
            
            changes = []
            for _, row in df.iterrows():
                changes.append(StockBoardChange(
                    board_name=str(row.get('板块名称', '')),
                    change_pct=float(row.get('涨跌幅', 0)),
                    net_inflow=float(row.get('主力净流入', 0)),
                    change_count=int(row.get('板块异动总次数', 0)),
                    top_stock_code=str(row.get('板块异动最频繁个股及所属类型 - 股票代码', '')),
                    top_stock_name=str(row.get('板块异动最频繁个股及所属类型 - 股票名称', '')),
                    top_stock_type=str(row.get('板块异动最频繁个股及所属类型 - 买卖方向', '')),
                    change_types=row.get('板块具体异动类型列表及出现次数', [])
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, changes)
            
            logger.info(f"获取板块异动数据成功，共{len(changes)}条")
            return changes
            
        except Exception as e:
            logger.error(f"获取板块异动数据失败：{e}")
            return []
    
    async def get_zt_pool(self, date: Optional[str] = None) -> List[StockZtPool]:
        """获取涨停股池数据
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为今日
        
        Returns:
            涨停股池数据列表
        """
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        # 缓存检查
        cache_key = self._get_cache_key('zt_pool', date=date)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_zt_pool_em(date=date)
            )
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append(StockZtPool(
                    serial_no=int(row.get('序号', 0)),
                    code=str(row.get('代码', '')),
                    name=str(row.get('名称', '')),
                    change_pct=float(row.get('涨跌幅', 0)),
                    latest_price=float(row.get('最新价', 0)),
                    turnover=float(row.get('成交额', 0)),
                    float_mv=float(row.get('流通市值', 0)),
                    total_mv=float(row.get('总市值', 0)),
                    turnover_rate=float(row.get('换手率', 0)),
                    seal_fund=float(row.get('封板资金', 0)),
                    first_seal_time=str(row.get('首次封板时间', '')),
                    last_seal_time=str(row.get('最后封板时间', '')),
                    open_count=int(row.get('炸板次数', 0)),
                    zt_stats=str(row.get('涨停统计', '')),
                    continuous_count=int(row.get('连板数', 1)),
                    industry=str(row.get('所属行业', ''))
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, zt_stocks)
            
            logger.info(f"获取涨停股池数据成功：{date}, 共{len(zt_stocks)}条")
            return zt_stocks
            
        except Exception as e:
            logger.error(f"获取涨停股池数据失败：{e}")
            return []
    
    async def get_zt_pool_previous(self, date: Optional[str] = None) -> List[StockZtPrevious]:
        """获取昨日涨停股池数据
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为昨日
        
        Returns:
            昨日涨停股池数据列表
        """
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        # 缓存检查
        cache_key = self._get_cache_key('zt_previous', date=date)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_zt_pool_previous_em(date=date)
            )
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append(StockZtPrevious(
                    serial_no=int(row.get('序号', 0)),
                    code=str(row.get('代码', '')),
                    name=str(row.get('名称', '')),
                    change_pct=float(row.get('涨跌幅', 0)),
                    latest_price=float(row.get('最新价', 0)),
                    limit_up_price=float(row.get('涨停价', 0)),
                    turnover=float(row.get('成交额', 0)),
                    float_mv=float(row.get('流通市值', 0)),
                    total_mv=float(row.get('总市值', 0)),
                    turnover_rate=float(row.get('换手率', 0)),
                    speed_pct=float(row.get('涨速', 0)),
                    amplitude=float(row.get('振幅', 0)),
                    yesterday_seal_time=str(row.get('昨日封板时间', '')),
                    yesterday_continuous=int(row.get('昨日连板数', 1)),
                    zt_stats=str(row.get('涨停统计', '')),
                    industry=str(row.get('所属行业', ''))
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, zt_stocks)
            
            logger.info(f"获取昨日涨停股池数据成功：{date}, 共{len(zt_stocks)}条")
            return zt_stocks
            
        except Exception as e:
            logger.error(f"获取昨日涨停股池数据失败：{e}")
            return []
    
    async def get_zt_pool_strong(self, date: Optional[str] = None) -> List[StockZtStrong]:
        """获取强势股池数据
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为今日
        
        Returns:
            强势股池数据列表
        """
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        # 缓存检查
        cache_key = self._get_cache_key('zt_strong', date=date)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_zt_pool_strong_em(date=date)
            )
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append(StockZtStrong(
                    serial_no=int(row.get('序号', 0)),
                    code=str(row.get('代码', '')),
                    name=str(row.get('名称', '')),
                    change_pct=float(row.get('涨跌幅', 0)),
                    latest_price=float(row.get('最新价', 0)),
                    limit_up_price=float(row.get('涨停价', 0)),
                    turnover=float(row.get('成交额', 0)),
                    float_mv=float(row.get('流通市值', 0)),
                    total_mv=float(row.get('总市值', 0)),
                    turnover_rate=float(row.get('换手率', 0)),
                    speed_pct=float(row.get('涨速', 0)),
                    is_new_high=str(row.get('是否新高', '')),
                    volume_ratio=float(row.get('量比', 0)),
                    zt_stats=str(row.get('涨停统计', '')),
                    reason=str(row.get('入选理由', '')),
                    industry=str(row.get('所属行业', ''))
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, zt_stocks)
            
            logger.info(f"获取强势股池数据成功：{date}, 共{len(zt_stocks)}条")
            return zt_stocks
            
        except Exception as e:
            logger.error(f"获取强势股池数据失败：{e}")
            return []
    
    async def get_zt_pool_sub_new(self, date: Optional[str] = None) -> List[StockZtSubNew]:
        """获取次新股池数据
        
        Args:
            date: 日期，格式 YYYYMMDD，默认为今日
        
        Returns:
            次新股池数据列表
        """
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        # 缓存检查
        cache_key = self._get_cache_key('zt_sub_new', date=date)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_zt_pool_sub_new_em(date=date)
            )
            
            if df is None or df.empty:
                return []
            
            zt_stocks = []
            for _, row in df.iterrows():
                zt_stocks.append(StockZtSubNew(
                    serial_no=int(row.get('序号', 0)),
                    code=str(row.get('代码', '')),
                    name=str(row.get('名称', '')),
                    change_pct=float(row.get('涨跌幅', 0)),
                    latest_price=float(row.get('最新价', 0)),
                    limit_up_price=float(row.get('涨停价', 0)),
                    turnover=float(row.get('成交额', 0)),
                    float_mv=float(row.get('流通市值', 0)),
                    total_mv=float(row.get('总市值', 0)),
                    turnover_rate=float(row.get('转手率', 0)),
                    open_days=int(row.get('开板几日', 0)),
                    open_date=str(row.get('开板日期', '')),
                    list_date=str(row.get('上市日期', '')),
                    is_new_high=str(row.get('是否新高', '')),
                    zt_stats=str(row.get('涨停统计', '')),
                    industry=str(row.get('所属行业', ''))
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, zt_stocks)
            
            logger.info(f"获取次新股池数据成功：{date}, 共{len(zt_stocks)}条")
            return zt_stocks
            
        except Exception as e:
            logger.error(f"获取次新股池数据失败：{e}")
            return []
    
    async def get_market_changes_summary(self) -> MarketChanges:
        """获取市场异动汇总
        
        Returns:
            市场异动汇总数据
        """
        try:
            # 获取各类型异动数据
            all_changes = await asyncio.gather(
                self.get_stock_changes('火箭发射'),
                self.get_stock_changes('快速反弹'),
                self.get_stock_changes('大笔买入'),
                self.get_stock_changes('大笔卖出'),
                self.get_stock_changes('封涨停板'),
                self.get_stock_changes('封跌停板'),
                self.get_stock_changes('高台跳水'),
                return_exceptions=True
            )
            
            # 统计各类型数量
            rocket_launch = len(all_changes[0]) if isinstance(all_changes[0], list) else 0
            fast_rebound = len(all_changes[1]) if isinstance(all_changes[1], list) else 0
            big_buy = len(all_changes[2]) if isinstance(all_changes[2], list) else 0
            big_sell = len(all_changes[3]) if isinstance(all_changes[3], list) else 0
            limit_up = len(all_changes[4]) if isinstance(all_changes[4], list) else 0
            limit_down = len(all_changes[5]) if isinstance(all_changes[5], list) else 0
            high_dive = len(all_changes[6]) if isinstance(all_changes[6], list) else 0
            
            total = rocket_launch + fast_rebound + big_buy + big_sell + limit_up + limit_down + high_dive
            
            return MarketChanges(
                timestamp=datetime.now().isoformat(),
                total_changes=total,
                rocket_launch=rocket_launch,
                fast_rebound=fast_rebound,
                big_buy=big_buy,
                big_sell=big_sell,
                limit_up=limit_up,
                limit_down=limit_down,
                high_dive=high_dive
            )
            
        except Exception as e:
            logger.error(f"获取市场异动汇总失败：{e}")
            return MarketChanges(
                timestamp=datetime.now().isoformat(),
                total_changes=0,
                rocket_launch=0,
                fast_rebound=0,
                big_buy=0,
                big_sell=0,
                limit_up=0,
                limit_down=0,
                high_dive=0
            )
    
    # ========== 基础方法实现（不需要的返回空） ==========
    
    async def get_stock_info(self, code: str) -> Optional[Any]:
        return None
    
    async def get_kline(self, code: str, start_date: Optional[str] = None, end_date: Optional[str] = None, adjust: str = "qfq") -> List[Any]:
        return []
    
    async def get_realtime_quote(self, code: str) -> Dict[str, Any]:
        return {}
    
    async def get_stock_comment(self) -> List[StockComment]:
        """获取千股千评数据
        
        Returns:
            千股千评数据列表
        """
        # 缓存检查
        cache_key = self._get_cache_key('stock_comment')
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_comment_em()
            )
            
            if df is None or df.empty:
                return []
            
            comments = []
            for _, row in df.iterrows():
                comments.append(StockComment(
                    serial_no=int(row.get('序号', 0)),
                    code=str(row.get('代码', '')),
                    name=str(row.get('名称', '')),
                    latest_price=float(row.get('最新价', 0)),
                    change_pct=float(row.get('涨跌幅', 0)),
                    turnover_rate=float(row.get('换手率', 0)),
                    pe_ratio=float(row.get('市盈率', 0)),
                    main_force_cost=float(row.get('主力成本', 0)),
                    institution_participation=float(row.get('机构参与度', 0)),
                    comprehensive_score=float(row.get('综合得分', 0)),
                    rise=int(row.get('上升', 0)),
                    current_rank=int(row.get('目前排名', 0)),
                    attention_index=float(row.get('关注指数', 0)),
                    trading_day=str(row.get('交易日', ''))
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, comments)
            
            logger.info(f"获取千股千评数据成功，共{len(comments)}条")
            return comments
            
        except Exception as e:
            logger.error(f"获取千股千评数据失败：{e}")
            return []
    
    async def get_stock_comment_detail_institution(self, symbol: str) -> List[StockCommentDetailInstitution]:
        """获取千股千评详情 - 主力控盘 - 机构参与度
        
        Args:
            symbol: 股票代码，如"600000"
        
        Returns:
            机构参与度历史数据列表
        """
        # 缓存检查
        cache_key = self._get_cache_key('stock_comment_detail_institution', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_comment_detail_zlkp_jgcyd_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            details = []
            for _, row in df.iterrows():
                details.append(StockCommentDetailInstitution(
                    trading_day=str(row.get('交易日', '')),
                    institution_participation=float(row.get('机构参与度', 0))
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, details)
            
            logger.info(f"获取个股机构参与度数据成功：{symbol}, 共{len(details)}条")
            return details
            
        except Exception as e:
            logger.error(f"获取个股机构参与度数据失败：{e}")
            return []
    
    async def get_stock_comment_detail_score(self, symbol: str) -> List[StockCommentDetailScore]:
        """获取千股千评详情 - 综合评价 - 历史评分
        
        Args:
            symbol: 股票代码，如"600000"
        
        Returns:
            历史评分数据列表
        """
        # 缓存检查
        cache_key = self._get_cache_key('stock_comment_detail_score', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_comment_detail_zhpj_lspf_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            details = []
            for _, row in df.iterrows():
                details.append(StockCommentDetailScore(
                    trading_day=str(row.get('交易日', '')),
                    score=float(row.get('评分', 0))
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, details)
            
            logger.info(f"获取个股历史评分数据成功：{symbol}, 共{len(details)}条")
            return details
            
        except Exception as e:
            logger.error(f"获取个股历史评分数据失败：{e}")
            return []
    
    async def get_stock_research_report(self, symbol: str) -> List[StockResearchReport]:
        """获取个股研报数据
        
        Args:
            symbol: 股票代码，如"000001"
        
        Returns:
            个股研报数据列表
        """
        # 缓存检查
        cache_key = self._get_cache_key('stock_research_report', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_research_report_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            reports = []
            for _, row in df.iterrows():
                reports.append(StockResearchReport(
                    serial_no=int(row.get('序号', 0)),
                    stock_code=str(row.get('股票代码', '')),
                    stock_name=str(row.get('股票简称', '')),
                    report_name=str(row.get('报告名称', '')),
                    rating=str(row.get('东财评级', '')),
                    institution=str(row.get('机构', '')),
                    recent_report_count=int(row.get('近一月个股研报数', 0)),
                    forecast_2024_eps=float(row.get('2024-盈利预测 - 收益', 0)) if pd.notna(row.get('2024-盈利预测 - 收益')) else None,
                    forecast_2024_pe=float(row.get('2024-盈利预测 - 市盈率', 0)) if pd.notna(row.get('2024-盈利预测 - 市盈率')) else None,
                    forecast_2025_eps=float(row.get('2025-盈利预测 - 收益', 0)) if pd.notna(row.get('2025-盈利预测 - 收益')) else None,
                    forecast_2025_pe=float(row.get('2025-盈利预测 - 市盈率', 0)) if pd.notna(row.get('2025-盈利预测 - 市盈率')) else None,
                    forecast_2026_eps=float(row.get('2026-盈利预测 - 收益', 0)) if pd.notna(row.get('2026-盈利预测 - 收益')) else None,
                    forecast_2026_pe=float(row.get('2026-盈利预测 - 市盈率', 0)) if pd.notna(row.get('2026-盈利预测 - 市盈率')) else None,
                    industry=str(row.get('行业', '')),
                    report_date=str(row.get('日期', '')),
                    report_pdf_url=str(row.get('报告 PDF 链接', ''))
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, reports)
            
            logger.info(f"获取个股研报数据成功：{symbol}, 共{len(reports)}条")
            return reports
            
        except Exception as e:
            logger.error(f"获取个股研报数据失败：{e}")
            return []
    
    async def get_stock_notice_report(self, symbol: str = "全部", date: Optional[str] = None) -> List[StockNotice]:
        """获取沪深京 A 股公告
        
        Args:
            symbol: 公告类型，可选值：
                - 全部
                - 重大事项
                - 财务报告
                - 融资公告
                - 风险提示
                - 资产重组
                - 信息变更
                - 持股变动
            date: 日期，格式 YYYYMMDD，默认为今日
        
        Returns:
            公告数据列表
        """
        if not date:
            date = datetime.now().strftime('%Y%m%d')
        
        # 缓存检查
        cache_key = self._get_cache_key('stock_notice_report', symbol=symbol, date=date)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            import pandas as pd
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_notice_report(symbol=symbol, date=date)
            )
            
            if df is None or df.empty:
                return []
            
            notices = []
            for _, row in df.iterrows():
                notices.append(StockNotice(
                    code=str(row.get('代码', '')),
                    name=str(row.get('名称', '')),
                    notice_title=str(row.get('公告标题', '')),
                    notice_type=str(row.get('公告类型', '')),
                    notice_date=str(row.get('公告日期', '')),
                    url=str(row.get('网址', ''))
                ))
            
            # 保存到缓存
            self._set_to_cache(cache_key, notices)
            
            logger.info(f"获取公告数据成功：{symbol} {date}, 共{len(notices)}条")
            return notices
            
        except Exception as e:
            logger.error(f"获取公告数据失败：{e}")
            return []
    
    async def get_balance_sheet_by_report(self, symbol: str) -> List[StockBalanceSheet]:
        """获取资产负债表 - 按报告期
        
        Args:
            symbol: 股票代码，如"SH600519"
        
        Returns:
            资产负债表数据列表（按报告期）
        """
        # 缓存检查
        cache_key = self._get_cache_key('balance_sheet_report', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_balance_sheet_by_report_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            sheets = []
            for _, row in df.iterrows():
                # 提取主要字段
                main_fields = {
                    'secucode': str(row.get('SECUCODE', '')),
                    'security_code': str(row.get('SECURITY_CODE', '')),
                    'security_name_abbr': str(row.get('SECURITY_NAME_ABBR', None)) if pd.notna(row.get('SECURITY_NAME_ABBR')) else None,
                    'end_date': str(row.get('END_DATE', None)) if pd.notna(row.get('END_DATE')) else None,
                    'report_date': str(row.get('REPORT_DATE', None)) if pd.notna(row.get('REPORT_DATE')) else None,
                    'total_assets': float(row.get('TOTAL_ASSETS', 0)) if pd.notna(row.get('TOTAL_ASSETS')) else None,
                    'total_liabilities': float(row.get('TOTAL_LIABILITIES', 0)) if pd.notna(row.get('TOTAL_LIABILITIES')) else None,
                    'total_equity': float(row.get('TOTAL_EQUITY', 0)) if pd.notna(row.get('TOTAL_EQUITY')) else None,
                    'cash_equivalents': float(row.get('CASH_EQUIVALENTS', 0)) if pd.notna(row.get('CASH_EQUIVALENTS')) else None,
                    'accounts_receivable': float(row.get('ACCOUNTS_RECEIVABLE', 0)) if pd.notna(row.get('ACCOUNTS_RECEIVABLE')) else None,
                    'inventory': float(row.get('INVENTORY', 0)) if pd.notna(row.get('INVENTORY')) else None,
                    'fixed_assets': float(row.get('FIXED_ASSETS', 0)) if pd.notna(row.get('FIXED_ASSETS')) else None,
                    'short_term_borrowings': float(row.get('SHORT_TERM_BORROWINGS', 0)) if pd.notna(row.get('SHORT_TERM_BORROWINGS')) else None,
                    'accounts_payable': float(row.get('ACCOUNTS_PAYABLE', 0)) if pd.notna(row.get('ACCOUNTS_PAYABLE')) else None,
                    'long_term_borrowings': float(row.get('LONG_TERM_BORROWINGS', 0)) if pd.notna(row.get('LONG_TERM_BORROWINGS')) else None,
                    'retained_earnings': float(row.get('RETAINED_EARNINGS', 0)) if pd.notna(row.get('RETAINED_EARNINGS')) else None,
                    'paid_in_capital': float(row.get('PAID_IN_CAPITAL', 0)) if pd.notna(row.get('PAID_IN_CAPITAL')) else None,
                }
                
                # 收集其他所有字段到 extra_fields
                extra_fields = {}
                skip_columns = ['SECUCODE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 'END_DATE', 
                               'REPORT_DATE', 'TOTAL_ASSETS', 'TOTAL_LIABILITIES', 'TOTAL_EQUITY',
                               'CASH_EQUIVALENTS', 'ACCOUNTS_RECEIVABLE', 'INVENTORY', 'FIXED_ASSETS',
                               'SHORT_TERM_BORROWINGS', 'ACCOUNTS_PAYABLE', 'LONG_TERM_BORROWINGS',
                               'RETAINED_EARNINGS', 'PAID_IN_CAPITAL']
                
                for col in df.columns:
                    if col not in skip_columns:
                        val = row.get(col, None)
                        if pd.notna(val):
                            extra_fields[col] = float(val) if isinstance(val, (int, float)) else str(val)
                
                main_fields['extra_fields'] = extra_fields
                sheets.append(StockBalanceSheet(**main_fields))
            
            # 保存到缓存
            self._set_to_cache(cache_key, sheets)
            
            logger.info(f"获取资产负债表（报告期）数据成功：{symbol}, 共{len(sheets)}条")
            return sheets
            
        except Exception as e:
            logger.error(f"获取资产负债表（报告期）数据失败：{e}")
            return []
    
    async def get_balance_sheet_by_yearly(self, symbol: str) -> List[StockBalanceSheet]:
        """获取资产负债表 - 按年度
        
        Args:
            symbol: 股票代码，如"SH600519"
        
        Returns:
            资产负债表数据列表（按年度）
        """
        # 缓存检查
        cache_key = self._get_cache_key('balance_sheet_yearly', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_balance_sheet_by_yearly_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            sheets = []
            for _, row in df.iterrows():
                # 提取主要字段
                main_fields = {
                    'secucode': str(row.get('SECUCODE', '')),
                    'security_code': str(row.get('SECURITY_CODE', '')),
                    'security_name_abbr': str(row.get('SECURITY_NAME_ABBR', None)) if pd.notna(row.get('SECURITY_NAME_ABBR')) else None,
                    'end_date': str(row.get('END_DATE', None)) if pd.notna(row.get('END_DATE')) else None,
                    'report_date': str(row.get('REPORT_DATE', None)) if pd.notna(row.get('REPORT_DATE')) else None,
                    'total_assets': float(row.get('TOTAL_ASSETS', 0)) if pd.notna(row.get('TOTAL_ASSETS')) else None,
                    'total_liabilities': float(row.get('TOTAL_LIABILITIES', 0)) if pd.notna(row.get('TOTAL_LIABILITIES')) else None,
                    'total_equity': float(row.get('TOTAL_EQUITY', 0)) if pd.notna(row.get('TOTAL_EQUITY')) else None,
                    'cash_equivalents': float(row.get('CASH_EQUIVALENTS', 0)) if pd.notna(row.get('CASH_EQUIVALENTS')) else None,
                    'accounts_receivable': float(row.get('ACCOUNTS_RECEIVABLE', 0)) if pd.notna(row.get('ACCOUNTS_RECEIVABLE')) else None,
                    'inventory': float(row.get('INVENTORY', 0)) if pd.notna(row.get('INVENTORY')) else None,
                    'fixed_assets': float(row.get('FIXED_ASSETS', 0)) if pd.notna(row.get('FIXED_ASSETS')) else None,
                    'short_term_borrowings': float(row.get('SHORT_TERM_BORROWINGS', 0)) if pd.notna(row.get('SHORT_TERM_BORROWINGS')) else None,
                    'accounts_payable': float(row.get('ACCOUNTS_PAYABLE', 0)) if pd.notna(row.get('ACCOUNTS_PAYABLE')) else None,
                    'long_term_borrowings': float(row.get('LONG_TERM_BORROWINGS', 0)) if pd.notna(row.get('LONG_TERM_BORROWINGS')) else None,
                    'retained_earnings': float(row.get('RETAINED_EARNINGS', 0)) if pd.notna(row.get('RETAINED_EARNINGS')) else None,
                    'paid_in_capital': float(row.get('PAID_IN_CAPITAL', 0)) if pd.notna(row.get('PAID_IN_CAPITAL')) else None,
                }
                
                # 收集其他所有字段到 extra_fields
                extra_fields = {}
                skip_columns = ['SECUCODE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 'END_DATE', 
                               'REPORT_DATE', 'TOTAL_ASSETS', 'TOTAL_LIABILITIES', 'TOTAL_EQUITY',
                               'CASH_EQUIVALENTS', 'ACCOUNTS_RECEIVABLE', 'INVENTORY', 'FIXED_ASSETS',
                               'SHORT_TERM_BORROWINGS', 'ACCOUNTS_PAYABLE', 'LONG_TERM_BORROWINGS',
                               'RETAINED_EARNINGS', 'PAID_IN_CAPITAL']
                
                for col in df.columns:
                    if col not in skip_columns:
                        val = row.get(col, None)
                        if pd.notna(val):
                            extra_fields[col] = float(val) if isinstance(val, (int, float)) else str(val)
                
                main_fields['extra_fields'] = extra_fields
                sheets.append(StockBalanceSheet(**main_fields))
            
            # 保存到缓存
            self._set_to_cache(cache_key, sheets)
            
            logger.info(f"获取资产负债表（年度）数据成功：{symbol}, 共{len(sheets)}条")
            return sheets
            
        except Exception as e:
            logger.error(f"获取资产负债表（年度）数据失败：{e}")
            return []
    
    async def get_profit_sheet_by_report(self, symbol: str) -> List[StockProfitSheet]:
        """获取利润表 - 按报告期
        
        Args:
            symbol: 股票代码，如"SH600519"
        
        Returns:
            利润表数据列表（按报告期）
        """
        # 缓存检查
        cache_key = self._get_cache_key('profit_sheet_report', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_profit_sheet_by_report_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            sheets = []
            for _, row in df.iterrows():
                # 提取主要字段
                main_fields = {
                    'secucode': str(row.get('SECUCODE', '')),
                    'security_code': str(row.get('SECURITY_CODE', '')),
                    'security_name_abbr': str(row.get('SECURITY_NAME_ABBR', None)) if pd.notna(row.get('SECURITY_NAME_ABBR')) else None,
                    'end_date': str(row.get('END_DATE', None)) if pd.notna(row.get('END_DATE')) else None,
                    'report_date': str(row.get('REPORT_DATE', None)) if pd.notna(row.get('REPORT_DATE')) else None,
                    'total_revenue': float(row.get('TOTAL_REVENUE', 0)) if pd.notna(row.get('TOTAL_REVENUE')) else None,
                    'operating_revenue': float(row.get('OPERATING_REVENUE', 0)) if pd.notna(row.get('OPERATING_REVENUE')) else None,
                    'operating_cost': float(row.get('OPERATING_COST', 0)) if pd.notna(row.get('OPERATING_COST')) else None,
                    'operating_profit': float(row.get('OPERATING_PROFIT', 0)) if pd.notna(row.get('OPERATING_PROFIT')) else None,
                    'total_profit': float(row.get('TOTAL_PROFIT', 0)) if pd.notna(row.get('TOTAL_PROFIT')) else None,
                    'net_profit': float(row.get('NET_PROFIT', 0)) if pd.notna(row.get('NET_PROFIT')) else None,
                    'parent_netprofit': float(row.get('PARENT_NETPROFIT', 0)) if pd.notna(row.get('PARENT_NETPROFIT')) else None,
                    'deduct_parent_netprofit': float(row.get('DEDUCT_PARENT_NETPROFIT', 0)) if pd.notna(row.get('DEDUCT_PARENT_NETPROFIT')) else None,
                    'operating_tax': float(row.get('OPERATING_TAX', 0)) if pd.notna(row.get('OPERATING_TAX')) else None,
                    'sales_expense': float(row.get('SALES_EXPENSE', 0)) if pd.notna(row.get('SALES_EXPENSE')) else None,
                    'admin_expense': float(row.get('ADMIN_EXPENSE', 0)) if pd.notna(row.get('ADMIN_EXPENSE')) else None,
                    'rd_expense': float(row.get('RD_EXPENSE', 0)) if pd.notna(row.get('RD_EXPENSE')) else None,
                    'finance_expense': float(row.get('FINANCE_EXPENSE', 0)) if pd.notna(row.get('FINANCE_EXPENSE')) else None,
                    'other_income': float(row.get('OTHER_INCOME', 0)) if pd.notna(row.get('OTHER_INCOME')) else None,
                    'investment_income': float(row.get('INVESTMENT_INCOME', 0)) if pd.notna(row.get('INVESTMENT_INCOME')) else None,
                    'non_operating_income': float(row.get('NON_OPERATING_INCOME', 0)) if pd.notna(row.get('NON_OPERATING_INCOME')) else None,
                    'non_operating_expense': float(row.get('NON_OPERATING_EXPENSE', 0)) if pd.notna(row.get('NON_OPERATING_EXPENSE')) else None,
                    'income_tax': float(row.get('INCOME_TAX', 0)) if pd.notna(row.get('INCOME_TAX')) else None,
                }
                
                # 收集其他所有字段到 extra_fields
                extra_fields = {}
                skip_columns = ['SECUCODE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 'END_DATE', 
                               'REPORT_DATE', 'TOTAL_REVENUE', 'OPERATING_REVENUE', 'OPERATING_COST',
                               'OPERATING_PROFIT', 'TOTAL_PROFIT', 'NET_PROFIT', 'PARENT_NETPROFIT',
                               'DEDUCT_PARENT_NETPROFIT', 'OPERATING_TAX', 'SALES_EXPENSE',
                               'ADMIN_EXPENSE', 'RD_EXPENSE', 'FINANCE_EXPENSE', 'OTHER_INCOME',
                               'INVESTMENT_INCOME', 'NON_OPERATING_INCOME', 'NON_OPERATING_EXPENSE',
                               'INCOME_TAX']
                
                for col in df.columns:
                    if col not in skip_columns:
                        val = row.get(col, None)
                        if pd.notna(val):
                            extra_fields[col] = float(val) if isinstance(val, (int, float)) else str(val)
                
                main_fields['extra_fields'] = extra_fields
                sheets.append(StockProfitSheet(**main_fields))
            
            # 保存到缓存
            self._set_to_cache(cache_key, sheets)
            
            logger.info(f"获取利润表（报告期）数据成功：{symbol}, 共{len(sheets)}条")
            return sheets
            
        except Exception as e:
            logger.error(f"获取利润表（报告期）数据失败：{e}")
            return []
    
    async def get_profit_sheet_by_yearly(self, symbol: str) -> List[StockProfitSheet]:
        """获取利润表 - 按年度
        
        Args:
            symbol: 股票代码，如"SH600519"
        
        Returns:
            利润表数据列表（按年度）
        """
        # 缓存检查
        cache_key = self._get_cache_key('profit_sheet_yearly', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_profit_sheet_by_yearly_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            sheets = []
            for _, row in df.iterrows():
                # 提取主要字段（与 get_profit_sheet_by_report 相同）
                main_fields = {
                    'secucode': str(row.get('SECUCODE', '')),
                    'security_code': str(row.get('SECURITY_CODE', '')),
                    'security_name_abbr': str(row.get('SECURITY_NAME_ABBR', None)) if pd.notna(row.get('SECURITY_NAME_ABBR')) else None,
                    'end_date': str(row.get('END_DATE', None)) if pd.notna(row.get('END_DATE')) else None,
                    'report_date': str(row.get('REPORT_DATE', None)) if pd.notna(row.get('REPORT_DATE')) else None,
                    'total_revenue': float(row.get('TOTAL_REVENUE', 0)) if pd.notna(row.get('TOTAL_REVENUE')) else None,
                    'operating_revenue': float(row.get('OPERATING_REVENUE', 0)) if pd.notna(row.get('OPERATING_REVENUE')) else None,
                    'operating_cost': float(row.get('OPERATING_COST', 0)) if pd.notna(row.get('OPERATING_COST')) else None,
                    'operating_profit': float(row.get('OPERATING_PROFIT', 0)) if pd.notna(row.get('OPERATING_PROFIT')) else None,
                    'total_profit': float(row.get('TOTAL_PROFIT', 0)) if pd.notna(row.get('TOTAL_PROFIT')) else None,
                    'net_profit': float(row.get('NET_PROFIT', 0)) if pd.notna(row.get('NET_PROFIT')) else None,
                    'parent_netprofit': float(row.get('PARENT_NETPROFIT', 0)) if pd.notna(row.get('PARENT_NETPROFIT')) else None,
                    'deduct_parent_netprofit': float(row.get('DEDUCT_PARENT_NETPROFIT', 0)) if pd.notna(row.get('DEDUCT_PARENT_NETPROFIT')) else None,
                    'operating_tax': float(row.get('OPERATING_TAX', 0)) if pd.notna(row.get('OPERATING_TAX')) else None,
                    'sales_expense': float(row.get('SALES_EXPENSE', 0)) if pd.notna(row.get('SALES_EXPENSE')) else None,
                    'admin_expense': float(row.get('ADMIN_EXPENSE', 0)) if pd.notna(row.get('ADMIN_EXPENSE')) else None,
                    'rd_expense': float(row.get('RD_EXPENSE', 0)) if pd.notna(row.get('RD_EXPENSE')) else None,
                    'finance_expense': float(row.get('FINANCE_EXPENSE', 0)) if pd.notna(row.get('FINANCE_EXPENSE')) else None,
                    'other_income': float(row.get('OTHER_INCOME', 0)) if pd.notna(row.get('OTHER_INCOME')) else None,
                    'investment_income': float(row.get('INVESTMENT_INCOME', 0)) if pd.notna(row.get('INVESTMENT_INCOME')) else None,
                    'non_operating_income': float(row.get('NON_OPERATING_INCOME', 0)) if pd.notna(row.get('NON_OPERATING_INCOME')) else None,
                    'non_operating_expense': float(row.get('NON_OPERATING_EXPENSE', 0)) if pd.notna(row.get('NON_OPERATING_EXPENSE')) else None,
                    'income_tax': float(row.get('INCOME_TAX', 0)) if pd.notna(row.get('INCOME_TAX')) else None,
                }
                
                # 收集其他所有字段到 extra_fields
                extra_fields = {}
                skip_columns = ['SECUCODE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 'END_DATE', 
                               'REPORT_DATE', 'TOTAL_REVENUE', 'OPERATING_REVENUE', 'OPERATING_COST',
                               'OPERATING_PROFIT', 'TOTAL_PROFIT', 'NET_PROFIT', 'PARENT_NETPROFIT',
                               'DEDUCT_PARENT_NETPROFIT', 'OPERATING_TAX', 'SALES_EXPENSE',
                               'ADMIN_EXPENSE', 'RD_EXPENSE', 'FINANCE_EXPENSE', 'OTHER_INCOME',
                               'INVESTMENT_INCOME', 'NON_OPERATING_INCOME', 'NON_OPERATING_EXPENSE',
                               'INCOME_TAX']
                
                for col in df.columns:
                    if col not in skip_columns:
                        val = row.get(col, None)
                        if pd.notna(val):
                            extra_fields[col] = float(val) if isinstance(val, (int, float)) else str(val)
                
                main_fields['extra_fields'] = extra_fields
                sheets.append(StockProfitSheet(**main_fields))
            
            # 保存到缓存
            self._set_to_cache(cache_key, sheets)
            
            logger.info(f"获取利润表（年度）数据成功：{symbol}, 共{len(sheets)}条")
            return sheets
            
        except Exception as e:
            logger.error(f"获取利润表（年度）数据失败：{e}")
            return []
    
    async def get_profit_sheet_by_quarterly(self, symbol: str) -> List[StockProfitSheet]:
        """获取利润表 - 按单季度
        
        Args:
            symbol: 股票代码，如"SH600519"
        
        Returns:
            利润表数据列表（按单季度）
        """
        # 缓存检查
        cache_key = self._get_cache_key('profit_sheet_quarterly', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            logger.debug(f"缓存命中：{cache_key}")
            return cached
        
        try:
            import akshare as ak
            
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_profit_sheet_by_quarterly_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            sheets = []
            for _, row in df.iterrows():
                # 提取主要字段（与 get_profit_sheet_by_report 相同）
                main_fields = {
                    'secucode': str(row.get('SECUCODE', '')),
                    'security_code': str(row.get('SECURITY_CODE', '')),
                    'security_name_abbr': str(row.get('SECURITY_NAME_ABBR', None)) if pd.notna(row.get('SECURITY_NAME_ABBR')) else None,
                    'end_date': str(row.get('END_DATE', None)) if pd.notna(row.get('END_DATE')) else None,
                    'report_date': str(row.get('REPORT_DATE', None)) if pd.notna(row.get('REPORT_DATE')) else None,
                    'total_revenue': float(row.get('TOTAL_REVENUE', 0)) if pd.notna(row.get('TOTAL_REVENUE')) else None,
                    'operating_revenue': float(row.get('OPERATING_REVENUE', 0)) if pd.notna(row.get('OPERATING_REVENUE')) else None,
                    'operating_cost': float(row.get('OPERATING_COST', 0)) if pd.notna(row.get('OPERATING_COST')) else None,
                    'operating_profit': float(row.get('OPERATING_PROFIT', 0)) if pd.notna(row.get('OPERATING_PROFIT')) else None,
                    'total_profit': float(row.get('TOTAL_PROFIT', 0)) if pd.notna(row.get('TOTAL_PROFIT')) else None,
                    'net_profit': float(row.get('NET_PROFIT', 0)) if pd.notna(row.get('NET_PROFIT')) else None,
                    'parent_netprofit': float(row.get('PARENT_NETPROFIT', 0)) if pd.notna(row.get('PARENT_NETPROFIT')) else None,
                    'deduct_parent_netprofit': float(row.get('DEDUCT_PARENT_NETPROFIT', 0)) if pd.notna(row.get('DEDUCT_PARENT_NETPROFIT')) else None,
                    'operating_tax': float(row.get('OPERATING_TAX', 0)) if pd.notna(row.get('OPERATING_TAX')) else None,
                    'sales_expense': float(row.get('SALES_EXPENSE', 0)) if pd.notna(row.get('SALES_EXPENSE')) else None,
                    'admin_expense': float(row.get('ADMIN_EXPENSE', 0)) if pd.notna(row.get('ADMIN_EXPENSE')) else None,
                    'rd_expense': float(row.get('RD_EXPENSE', 0)) if pd.notna(row.get('RD_EXPENSE')) else None,
                    'finance_expense': float(row.get('FINANCE_EXPENSE', 0)) if pd.notna(row.get('FINANCE_EXPENSE')) else None,
                    'other_income': float(row.get('OTHER_INCOME', 0)) if pd.notna(row.get('OTHER_INCOME')) else None,
                    'investment_income': float(row.get('INVESTMENT_INCOME', 0)) if pd.notna(row.get('INVESTMENT_INCOME')) else None,
                    'non_operating_income': float(row.get('NON_OPERATING_INCOME', 0)) if pd.notna(row.get('NON_OPERATING_INCOME')) else None,
                    'non_operating_expense': float(row.get('NON_OPERATING_EXPENSE', 0)) if pd.notna(row.get('NON_OPERATING_EXPENSE')) else None,
                    'income_tax': float(row.get('INCOME_TAX', 0)) if pd.notna(row.get('INCOME_TAX')) else None,
                }
                
                # 收集其他所有字段到 extra_fields
                extra_fields = {}
                skip_columns = ['SECUCODE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 'END_DATE', 
                               'REPORT_DATE', 'TOTAL_REVENUE', 'OPERATING_REVENUE', 'OPERATING_COST',
                               'OPERATING_PROFIT', 'TOTAL_PROFIT', 'NET_PROFIT', 'PARENT_NETPROFIT',
                               'DEDUCT_PARENT_NETPROFIT', 'OPERATING_TAX', 'SALES_EXPENSE',
                               'ADMIN_EXPENSE', 'RD_EXPENSE', 'FINANCE_EXPENSE', 'OTHER_INCOME',
                               'INVESTMENT_INCOME', 'NON_OPERATING_INCOME', 'NON_OPERATING_EXPENSE',
                               'INCOME_TAX']
                
                for col in df.columns:
                    if col not in skip_columns:
                        val = row.get(col, None)
                        if pd.notna(val):
                            extra_fields[col] = float(val) if isinstance(val, (int, float)) else str(val)
                
                main_fields['extra_fields'] = extra_fields
                sheets.append(StockProfitSheet(**main_fields))
            
            # 保存到缓存
            self._set_to_cache(cache_key, sheets)
            
            logger.info(f"获取利润表（单季度）数据成功：{symbol}, 共{len(sheets)}条")
            return sheets
            
        except Exception as e:
            logger.error(f"获取利润表（单季度）数据失败：{e}")
            return []
    
    async def get_cash_flow_sheet_by_report(self, symbol: str) -> List[StockCashFlowSheet]:
        """获取现金流量表 - 按报告期"""
        cache_key = self._get_cache_key('cash_flow_sheet_report', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_cash_flow_sheet_by_report_em(symbol=symbol))
            
            if df is None or df.empty:
                return []
            
            sheets = []
            for _, row in df.iterrows():
                main_fields = {
                    'secucode': str(row.get('SECUCODE', '')),
                    'security_code': str(row.get('SECURITY_CODE', '')),
                    'security_name_abbr': str(row.get('SECURITY_NAME_ABBR', None)) if pd.notna(row.get('SECURITY_NAME_ABBR')) else None,
                    'end_date': str(row.get('END_DATE', None)) if pd.notna(row.get('END_DATE')) else None,
                    'report_date': str(row.get('REPORT_DATE', None)) if pd.notna(row.get('REPORT_DATE')) else None,
                    'operating_cash_in': float(row.get('OPERATING_CASH_IN', 0)) if pd.notna(row.get('OPERATING_CASH_IN')) else None,
                    'operating_cash_out': float(row.get('OPERATING_CASH_OUT', 0)) if pd.notna(row.get('OPERATING_CASH_OUT')) else None,
                    'operating_net_cash': float(row.get('OPERATING_NET_CASH', 0)) if pd.notna(row.get('OPERATING_NET_CASH')) else None,
                    'investing_cash_in': float(row.get('INVESTING_CASH_IN', 0)) if pd.notna(row.get('INVESTING_CASH_IN')) else None,
                    'investing_cash_out': float(row.get('INVESTING_CASH_OUT', 0)) if pd.notna(row.get('INVESTING_CASH_OUT')) else None,
                    'investing_net_cash': float(row.get('INVESTING_NET_CASH', 0)) if pd.notna(row.get('INVESTING_NET_CASH')) else None,
                    'financing_cash_in': float(row.get('FINANCING_CASH_IN', 0)) if pd.notna(row.get('FINANCING_CASH_IN')) else None,
                    'financing_cash_out': float(row.get('FINANCING_CASH_OUT', 0)) if pd.notna(row.get('FINANCING_CASH_OUT')) else None,
                    'financing_net_cash': float(row.get('FINANCING_NET_CASH', 0)) if pd.notna(row.get('FINANCING_NET_CASH')) else None,
                    'cash_add': float(row.get('CASH_ADD', 0)) if pd.notna(row.get('CASH_ADD')) else None,
                    'cash_end': float(row.get('CASH_END', 0)) if pd.notna(row.get('CASH_END')) else None,
                    'depreciation': float(row.get('DEPRECIATION', 0)) if pd.notna(row.get('DEPRECIATION')) else None,
                    'minority_interest': float(row.get('MINORITY_INTEREST', 0)) if pd.notna(row.get('MINORITY_INTEREST')) else None,
                }
                extra_fields = {}
                skip_columns = ['SECUCODE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 'END_DATE', 'REPORT_DATE',
                               'OPERATING_CASH_IN', 'OPERATING_CASH_OUT', 'OPERATING_NET_CASH',
                               'INVESTING_CASH_IN', 'INVESTING_CASH_OUT', 'INVESTING_NET_CASH',
                               'FINANCING_CASH_IN', 'FINANCING_CASH_OUT', 'FINANCING_NET_CASH',
                               'CASH_ADD', 'CASH_END', 'DEPRECIATION', 'MINORITY_INTEREST']
                for col in df.columns:
                    if col not in skip_columns and pd.notna(row.get(col)):
                        val = row.get(col, None)
                        extra_fields[col] = float(val) if isinstance(val, (int, float)) else str(val)
                main_fields['extra_fields'] = extra_fields
                sheets.append(StockCashFlowSheet(**main_fields))
            
            self._set_to_cache(cache_key, sheets)
            logger.info(f"获取现金流量表（报告期）数据成功：{symbol}, 共{len(sheets)}条")
            return sheets
        except Exception as e:
            logger.error(f"获取现金流量表（报告期）数据失败：{e}")
            return []
    
    async def get_cash_flow_sheet_by_yearly(self, symbol: str) -> List[StockCashFlowSheet]:
        """获取现金流量表 - 按年度"""
        cache_key = self._get_cache_key('cash_flow_sheet_yearly', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_cash_flow_sheet_by_yearly_em(symbol=symbol))
            
            if df is None or df.empty:
                return []
            
            sheets = []
            for _, row in df.iterrows():
                main_fields = {
                    'secucode': str(row.get('SECUCODE', '')),
                    'security_code': str(row.get('SECURITY_CODE', '')),
                    'security_name_abbr': str(row.get('SECURITY_NAME_ABBR', None)) if pd.notna(row.get('SECURITY_NAME_ABBR')) else None,
                    'end_date': str(row.get('END_DATE', None)) if pd.notna(row.get('END_DATE')) else None,
                    'report_date': str(row.get('REPORT_DATE', None)) if pd.notna(row.get('REPORT_DATE')) else None,
                    'operating_cash_in': float(row.get('OPERATING_CASH_IN', 0)) if pd.notna(row.get('OPERATING_CASH_IN')) else None,
                    'operating_cash_out': float(row.get('OPERATING_CASH_OUT', 0)) if pd.notna(row.get('OPERATING_CASH_OUT')) else None,
                    'operating_net_cash': float(row.get('OPERATING_NET_CASH', 0)) if pd.notna(row.get('OPERATING_NET_CASH')) else None,
                    'investing_cash_in': float(row.get('INVESTING_CASH_IN', 0)) if pd.notna(row.get('INVESTING_CASH_IN')) else None,
                    'investing_cash_out': float(row.get('INVESTING_CASH_OUT', 0)) if pd.notna(row.get('INVESTING_CASH_OUT')) else None,
                    'investing_net_cash': float(row.get('INVESTING_NET_CASH', 0)) if pd.notna(row.get('INVESTING_NET_CASH')) else None,
                    'financing_cash_in': float(row.get('FINANCING_CASH_IN', 0)) if pd.notna(row.get('FINANCING_CASH_IN')) else None,
                    'financing_cash_out': float(row.get('FINANCING_CASH_OUT', 0)) if pd.notna(row.get('FINANCING_CASH_OUT')) else None,
                    'financing_net_cash': float(row.get('FINANCING_NET_CASH', 0)) if pd.notna(row.get('FINANCING_NET_CASH')) else None,
                    'cash_add': float(row.get('CASH_ADD', 0)) if pd.notna(row.get('CASH_ADD')) else None,
                    'cash_end': float(row.get('CASH_END', 0)) if pd.notna(row.get('CASH_END')) else None,
                    'depreciation': float(row.get('DEPRECIATION', 0)) if pd.notna(row.get('DEPRECIATION')) else None,
                    'minority_interest': float(row.get('MINORITY_INTEREST', 0)) if pd.notna(row.get('MINORITY_INTEREST')) else None,
                }
                extra_fields = {}
                skip_columns = ['SECUCODE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 'END_DATE', 'REPORT_DATE',
                               'OPERATING_CASH_IN', 'OPERATING_CASH_OUT', 'OPERATING_NET_CASH',
                               'INVESTING_CASH_IN', 'INVESTING_CASH_OUT', 'INVESTING_NET_CASH',
                               'FINANCING_CASH_IN', 'FINANCING_CASH_OUT', 'FINANCING_NET_CASH',
                               'CASH_ADD', 'CASH_END', 'DEPRECIATION', 'MINORITY_INTEREST']
                for col in df.columns:
                    if col not in skip_columns and pd.notna(row.get(col)):
                        val = row.get(col, None)
                        extra_fields[col] = float(val) if isinstance(val, (int, float)) else str(val)
                main_fields['extra_fields'] = extra_fields
                sheets.append(StockCashFlowSheet(**main_fields))
            
            self._set_to_cache(cache_key, sheets)
            logger.info(f"获取现金流量表（年度）数据成功：{symbol}, 共{len(sheets)}条")
            return sheets
        except Exception as e:
            logger.error(f"获取现金流量表（年度）数据失败：{e}")
            return []
    
    async def get_cash_flow_sheet_by_quarterly(self, symbol: str) -> List[StockCashFlowSheet]:
        """获取现金流量表 - 按单季度"""
        cache_key = self._get_cache_key('cash_flow_sheet_quarterly', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_cash_flow_sheet_by_quarterly_em(symbol=symbol))
            
            if df is None or df.empty:
                return []
            
            sheets = []
            for _, row in df.iterrows():
                main_fields = {
                    'secucode': str(row.get('SECUCODE', '')),
                    'security_code': str(row.get('SECURITY_CODE', '')),
                    'security_name_abbr': str(row.get('SECURITY_NAME_ABBR', None)) if pd.notna(row.get('SECURITY_NAME_ABBR')) else None,
                    'end_date': str(row.get('END_DATE', None)) if pd.notna(row.get('END_DATE')) else None,
                    'report_date': str(row.get('REPORT_DATE', None)) if pd.notna(row.get('REPORT_DATE')) else None,
                    'operating_cash_in': float(row.get('OPERATING_CASH_IN', 0)) if pd.notna(row.get('OPERATING_CASH_IN')) else None,
                    'operating_cash_out': float(row.get('OPERATING_CASH_OUT', 0)) if pd.notna(row.get('OPERATING_CASH_OUT')) else None,
                    'operating_net_cash': float(row.get('OPERATING_NET_CASH', 0)) if pd.notna(row.get('OPERATING_NET_CASH')) else None,
                    'investing_cash_in': float(row.get('INVESTING_CASH_IN', 0)) if pd.notna(row.get('INVESTING_CASH_IN')) else None,
                    'investing_cash_out': float(row.get('INVESTING_CASH_OUT', 0)) if pd.notna(row.get('INVESTING_CASH_OUT')) else None,
                    'investing_net_cash': float(row.get('INVESTING_NET_CASH', 0)) if pd.notna(row.get('INVESTING_NET_CASH')) else None,
                    'financing_cash_in': float(row.get('FINANCING_CASH_IN', 0)) if pd.notna(row.get('FINANCING_CASH_IN')) else None,
                    'financing_cash_out': float(row.get('FINANCING_CASH_OUT', 0)) if pd.notna(row.get('FINANCING_CASH_OUT')) else None,
                    'financing_net_cash': float(row.get('FINANCING_NET_CASH', 0)) if pd.notna(row.get('FINANCING_NET_CASH')) else None,
                    'cash_add': float(row.get('CASH_ADD', 0)) if pd.notna(row.get('CASH_ADD')) else None,
                    'cash_end': float(row.get('CASH_END', 0)) if pd.notna(row.get('CASH_END')) else None,
                    'depreciation': float(row.get('DEPRECIATION', 0)) if pd.notna(row.get('DEPRECIATION')) else None,
                    'minority_interest': float(row.get('MINORITY_INTEREST', 0)) if pd.notna(row.get('MINORITY_INTEREST')) else None,
                }
                extra_fields = {}
                skip_columns = ['SECUCODE', 'SECURITY_CODE', 'SECURITY_NAME_ABBR', 'END_DATE', 'REPORT_DATE',
                               'OPERATING_CASH_IN', 'OPERATING_CASH_OUT', 'OPERATING_NET_CASH',
                               'INVESTING_CASH_IN', 'INVESTING_CASH_OUT', 'INVESTING_NET_CASH',
                               'FINANCING_CASH_IN', 'FINANCING_CASH_OUT', 'FINANCING_NET_CASH',
                               'CASH_ADD', 'CASH_END', 'DEPRECIATION', 'MINORITY_INTEREST']
                for col in df.columns:
                    if col not in skip_columns and pd.notna(row.get(col)):
                        val = row.get(col, None)
                        extra_fields[col] = float(val) if isinstance(val, (int, float)) else str(val)
                main_fields['extra_fields'] = extra_fields
                sheets.append(StockCashFlowSheet(**main_fields))
            
            self._set_to_cache(cache_key, sheets)
            logger.info(f"获取现金流量表（单季度）数据成功：{symbol}, 共{len(sheets)}条")
            return sheets
        except Exception as e:
            logger.error(f"获取现金流量表（单季度）数据失败：{e}")
            return []

    async def get_financial_analysis_indicator(self, symbol: str, start_year: str) -> List[StockFinancialIndicator]:
        """获取新浪财经财务指标
        
        Args:
            symbol: 股票代码（6 位数字）
            start_year: 开始年份（如"2020"）
        
        Returns:
            财务指标数据列表
        """
        cache_key = self._get_cache_key('financial_analysis_indicator', symbol=symbol, start_year=start_year)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_financial_analysis_indicator(symbol=symbol, start_year=start_year)
            )
            
            if df is None or df.empty:
                return []
            
            indicators = []
            for _, row in df.iterrows():
                main_fields = {
                    'date': str(row.get('日期', None)) if pd.notna(row.get('日期')) else None,
                    'diluted_eps': float(row.get('摊薄每股收益 (元)', 0)) if pd.notna(row.get('摊薄每股收益 (元)')) else None,
                    'weighted_eps': float(row.get('加权每股收益 (元)', 0)) if pd.notna(row.get('加权每股收益 (元)')) else None,
                    'adjusted_eps': float(row.get('每股收益_调整后 (元)', 0)) if pd.notna(row.get('每股收益_调整后 (元)')) else None,
                    'non_recurring_eps': float(row.get('扣除非经常性损益后的每股收益 (元)', 0)) if pd.notna(row.get('扣除非经常性损益后的每股收益 (元)')) else None,
                    'adjusted_net_asset_per_share_before': float(row.get('每股净资产_调整前 (元)', 0)) if pd.notna(row.get('每股净资产_调整前 (元)')) else None,
                    'adjusted_net_asset_per_share_after': float(row.get('每股净资产_调整后 (元)', 0)) if pd.notna(row.get('每股净资产_调整后 (元)')) else None,
                    'operating_cash_flow_per_share': float(row.get('每股经营性现金流 (元)', 0)) if pd.notna(row.get('每股经营性现金流 (元)')) else None,
                    'capital_reserve_per_share': float(row.get('每股资本公积金 (元)', 0)) if pd.notna(row.get('每股资本公积金 (元)')) else None,
                    'undistributed_profit_per_share': float(row.get('每股未分配利润 (元)', 0)) if pd.notna(row.get('每股未分配利润 (元)')) else None,
                    'adjusted_net_assets_per_share': float(row.get('调整后的每股净资产 (元)', 0)) if pd.notna(row.get('调整后的每股净资产 (元)')) else None,
                    
                    # 盈利能力指标
                    'return_on_total_assets': float(row.get('总资产利润率 (%)', 0)) if pd.notna(row.get('总资产利润率 (%)')) else None,
                    'return_on_main_business': float(row.get('主营业务利润率 (%)', 0)) if pd.notna(row.get('主营业务利润率 (%)')) else None,
                    'return_on_net_assets': float(row.get('总资产净利润率 (%)', 0)) if pd.notna(row.get('总资产净利润率 (%)')) else None,
                    'return_on_cost_expense': float(row.get('成本费用利润率 (%)', 0)) if pd.notna(row.get('成本费用利润率 (%)')) else None,
                    'operating_profit_margin': float(row.get('营业利润率 (%)', 0)) if pd.notna(row.get('营业利润率 (%)')) else None,
                    'main_business_cost_ratio': float(row.get('主营业务成本率 (%)', 0)) if pd.notna(row.get('主营业务成本率 (%)')) else None,
                    'net_profit_margin': float(row.get('销售净利率 (%)', 0)) if pd.notna(row.get('销售净利率 (%)')) else None,
                    'share_capital_return_rate': float(row.get('股本报酬率 (%)', 0)) if pd.notna(row.get('股本报酬率 (%)')) else None,
                    'return_on_net_assets_weighted': float(row.get('加权净资产报酬率 (%)', 0)) if pd.notna(row.get('加权净资产报酬率 (%)')) else None,
                    'return_on_assets': float(row.get('资产报酬率 (%)', 0)) if pd.notna(row.get('资产报酬率 (%)')) else None,
                    'gross_profit_margin': float(row.get('销售毛利率 (%)', 0)) if pd.notna(row.get('销售毛利率 (%)')) else None,
                    'three_expense_ratio': float(row.get('三项费用比重', 0)) if pd.notna(row.get('三项费用比重')) else None,
                    'non_main_business_ratio': float(row.get('非主营比重', 0)) if pd.notna(row.get('非主营比重')) else None,
                    'main_profit_ratio': float(row.get('主营利润比重', 0)) if pd.notna(row.get('主营利润比重')) else None,
                    'dividend_payout_ratio': float(row.get('股息发放率 (%)', 0)) if pd.notna(row.get('股息发放率 (%)')) else None,
                    'investment_return_rate': float(row.get('投资收益率 (%)', 0)) if pd.notna(row.get('投资收益率 (%)')) else None,
                    'main_business_profit': float(row.get('主营业务利润 (元)', 0)) if pd.notna(row.get('主营业务利润 (元)')) else None,
                    'roe': float(row.get('净资产收益率 (%)', 0)) if pd.notna(row.get('净资产收益率 (%)')) else None,
                    'weighted_roe': float(row.get('加权净资产收益率 (%)', 0)) if pd.notna(row.get('加权净资产收益率 (%)')) else None,
                    'non_recurring_net_profit': float(row.get('扣除非经常性损益后的净利润 (元)', 0)) if pd.notna(row.get('扣除非经常性损益后的净利润 (元)')) else None,
                    
                    # 成长能力指标
                    'revenue_growth_rate': float(row.get('主营业务收入增长率 (%)', 0)) if pd.notna(row.get('主营业务收入增长率 (%)')) else None,
                    'net_profit_growth_rate': float(row.get('净利润增长率 (%)', 0)) if pd.notna(row.get('净利润增长率 (%)')) else None,
                    'net_assets_growth_rate': float(row.get('净资产增长率 (%)', 0)) if pd.notna(row.get('净资产增长率 (%)')) else None,
                    'total_assets_growth_rate': float(row.get('总资产增长率 (%)', 0)) if pd.notna(row.get('总资产增长率 (%)')) else None,
                    
                    # 营运能力指标
                    'accounts_receivable_turnover': float(row.get('应收账款周转率 (次)', 0)) if pd.notna(row.get('应收账款周转率 (次)')) else None,
                    'accounts_receivable_turnover_days': float(row.get('应收账款周转天数 (天)', 0)) if pd.notna(row.get('应收账款周转天数 (天)')) else None,
                    'inventory_turnover_days': float(row.get('存货周转天数 (天)', 0)) if pd.notna(row.get('存货周转天数 (天)')) else None,
                    'inventory_turnover': float(row.get('存货周转率 (次)', 0)) if pd.notna(row.get('存货周转率 (次)')) else None,
                    'fixed_assets_turnover': float(row.get('固定资产周转率 (次)', 0)) if pd.notna(row.get('固定资产周转率 (次)')) else None,
                    'total_assets_turnover': float(row.get('总资产周转率 (次)', 0)) if pd.notna(row.get('总资产周转率 (次)')) else None,
                    'total_assets_turnover_days': float(row.get('总资产周转天数 (天)', 0)) if pd.notna(row.get('总资产周转天数 (天)')) else None,
                    'current_assets_turnover': float(row.get('流动资产周转率 (次)', 0)) if pd.notna(row.get('流动资产周转率 (次)')) else None,
                    'current_assets_turnover_days': float(row.get('流动资产周转天数 (天)', 0)) if pd.notna(row.get('流动资产周转天数 (天)')) else None,
                    'equity_turnover': float(row.get('股东权益周转率 (次)', 0)) if pd.notna(row.get('股东权益周转率 (次)')) else None,
                    
                    # 偿债能力指标
                    'current_ratio': float(row.get('流动比率', 0)) if pd.notna(row.get('流动比率')) else None,
                    'quick_ratio': float(row.get('速动比率', 0)) if pd.notna(row.get('速动比率')) else None,
                    'cash_ratio': float(row.get('现金比率 (%)', 0)) if pd.notna(row.get('现金比率 (%)')) else None,
                    'interest_payment_multiple': float(row.get('利息支付倍数', 0)) if pd.notna(row.get('利息支付倍数')) else None,
                    'long_term_debt_to_working_capital': float(row.get('长期债务与营运资金比率 (%)', 0)) if pd.notna(row.get('长期债务与营运资金比率 (%)')) else None,
                    'equity_ratio': float(row.get('股东权益比率 (%)', 0)) if pd.notna(row.get('股东权益比率 (%)')) else None,
                    'long_term_debt_ratio': float(row.get('长期负债比率 (%)', 0)) if pd.notna(row.get('长期负债比率 (%)')) else None,
                    'equity_to_fixed_assets': float(row.get('股东权益与固定资产比率 (%)', 0)) if pd.notna(row.get('股东权益与固定资产比率 (%)')) else None,
                    'debt_to_equity': float(row.get('负债与所有者权益比率 (%)', 0)) if pd.notna(row.get('负债与所有者权益比率 (%)')) else None,
                    'long_term_assets_to_long_term_capital': float(row.get('长期资产与长期资金比率 (%)', 0)) if pd.notna(row.get('长期资产与长期资金比率 (%)')) else None,
                    'capitalization_ratio': float(row.get('资本化比率 (%)', 0)) if pd.notna(row.get('资本化比率 (%)')) else None,
                    'fixed_assets_net_value_ratio': float(row.get('固定资产净值率 (%)', 0)) if pd.notna(row.get('固定资产净值率 (%)')) else None,
                    'capital_fixed_ratio': float(row.get('资本固定化比率 (%)', 0)) if pd.notna(row.get('资本固定化比率 (%)')) else None,
                    'equity_ratio_percent': float(row.get('产权比率 (%)', 0)) if pd.notna(row.get('产权比率 (%)')) else None,
                    'liquidation_value_ratio': float(row.get('清算价值比率 (%)', 0)) if pd.notna(row.get('清算价值比率 (%)')) else None,
                    'fixed_assets_ratio': float(row.get('固定资产比重 (%)', 0)) if pd.notna(row.get('固定资产比重 (%)')) else None,
                    'asset_liability_ratio': float(row.get('资产负债率 (%)', 0)) if pd.notna(row.get('资产负债率 (%)')) else None,
                    
                    # 现金流量指标
                    'operating_cash_to_sales': float(row.get('经营现金净流量对销售收入比率 (%)', 0)) if pd.notna(row.get('经营现金净流量对销售收入比率 (%)')) else None,
                    'operating_cash_to_assets': float(row.get('资产的经营现金流量回报率 (%)', 0)) if pd.notna(row.get('资产的经营现金流量回报率 (%)')) else None,
                    'operating_cash_to_net_profit': float(row.get('经营现金净流量与净利润的比率 (%)', 0)) if pd.notna(row.get('经营现金净流量与净利润的比率 (%)')) else None,
                    'operating_cash_to_debt': float(row.get('经营现金净流量对负债比率 (%)', 0)) if pd.notna(row.get('经营现金净流量对负债比率 (%)')) else None,
                    'cash_flow_ratio': float(row.get('现金流量比率 (%)', 0)) if pd.notna(row.get('现金流量比率 (%)')) else None,
                    
                    # 投资明细
                    'short_term_stock_investment': float(row.get('短期股票投资 (元)', 0)) if pd.notna(row.get('短期股票投资 (元)')) else None,
                    'short_term_bond_investment': float(row.get('短期债券投资 (元)', 0)) if pd.notna(row.get('短期债券投资 (元)')) else None,
                    'short_term_other_investment': float(row.get('短期其它经营性投资 (元)', 0)) if pd.notna(row.get('短期其它经营性投资 (元)')) else None,
                    'long_term_stock_investment': float(row.get('长期股票投资 (元)', 0)) if pd.notna(row.get('长期股票投资 (元)')) else None,
                    'long_term_bond_investment': float(row.get('长期债券投资 (元)', 0)) if pd.notna(row.get('长期债券投资 (元)')) else None,
                    'long_term_other_investment': float(row.get('长期其它经营性投资 (元)', 0)) if pd.notna(row.get('长期其它经营性投资 (元)')) else None,
                    
                    # 应收款项明细
                    'accounts_receivable_within_1_year': float(row.get('1 年以内应收帐款 (元)', 0)) if pd.notna(row.get('1 年以内应收帐款 (元)')) else None,
                    'accounts_receivable_1_to_2_years': float(row.get('1-2 年以内应收帐款 (元)', 0)) if pd.notna(row.get('1-2 年以内应收帐款 (元)')) else None,
                    'accounts_receivable_2_to_3_years': float(row.get('2-3 年以内应收帐款 (元)', 0)) if pd.notna(row.get('2-3 年以内应收帐款 (元)')) else None,
                    'accounts_receivable_within_3_years': float(row.get('3 年以内应收帐款 (元)', 0)) if pd.notna(row.get('3 年以内应收帐款 (元)')) else None,
                    'advances_within_1_year': float(row.get('1 年以内预付货款 (元)', 0)) if pd.notna(row.get('1 年以内预付货款 (元)')) else None,
                    'advances_1_to_2_years': float(row.get('1-2 年以内预付货款 (元)', 0)) if pd.notna(row.get('1-2 年以内预付货款 (元)')) else None,
                    'advances_2_to_3_years': float(row.get('2-3 年以内预付货款 (元)', 0)) if pd.notna(row.get('2-3 年以内预付货款 (元)')) else None,
                    'advances_within_3_years': float(row.get('3 年以内预付货款 (元)', 0)) if pd.notna(row.get('3 年以内预付货款 (元)')) else None,
                    'other_receivables_within_1_year': float(row.get('1 年以内其它应收款 (元)', 0)) if pd.notna(row.get('1 年以内其它应收款 (元)')) else None,
                    'other_receivables_1_to_2_years': float(row.get('1-2 年以内其它应收款 (元)', 0)) if pd.notna(row.get('1-2 年以内其它应收款 (元)')) else None,
                    'other_receivables_2_to_3_years': float(row.get('2-3 年以内其它应收款 (元)', 0)) if pd.notna(row.get('2-3 年以内其它应收款 (元)')) else None,
                    'other_receivables_within_3_years': float(row.get('3 年以内其它应收款 (元)', 0)) if pd.notna(row.get('3 年以内其它应收款 (元)')) else None,
                }
                
                # 其他字段存储在 extra_fields 中
                extra_fields = {}
                skip_columns = [
                    '日期', '摊薄每股收益 (元)', '加权每股收益 (元)', '每股收益_调整后 (元)', '扣除非经常性损益后的每股收益 (元)',
                    '每股净资产_调整前 (元)', '每股净资产_调整后 (元)', '每股经营性现金流 (元)', '每股资本公积金 (元)', '每股未分配利润 (元)',
                    '调整后的每股净资产 (元)', '总资产利润率 (%)', '主营业务利润率 (%)', '总资产净利润率 (%)', '成本费用利润率 (%)',
                    '营业利润率 (%)', '主营业务成本率 (%)', '销售净利率 (%)', '股本报酬率 (%)', '加权净资产报酬率 (%)',
                    '资产报酬率 (%)', '销售毛利率 (%)', '三项费用比重', '非主营比重', '主营利润比重', '股息发放率 (%)',
                    '投资收益率 (%)', '主营业务利润 (元)', '净资产收益率 (%)', '加权净资产收益率 (%)', '扣除非经常性损益后的净利润 (元)',
                    '主营业务收入增长率 (%)', '净利润增长率 (%)', '净资产增长率 (%)', '总资产增长率 (%)', '应收账款周转率 (次)',
                    '应收账款周转天数 (天)', '存货周转天数 (天)', '存货周转率 (次)', '固定资产周转率 (次)', '总资产周转率 (次)',
                    '总资产周转天数 (天)', '流动资产周转率 (次)', '流动资产周转天数 (天)', '股东权益周转率 (次)', '流动比率',
                    '速动比率', '现金比率 (%)', '利息支付倍数', '长期债务与营运资金比率 (%)', '股东权益比率 (%)',
                    '长期负债比率 (%)', '股东权益与固定资产比率 (%)', '负债与所有者权益比率 (%)', '长期资产与长期资金比率 (%)',
                    '资本化比率 (%)', '固定资产净值率 (%)', '资本固定化比率 (%)', '产权比率 (%)', '清算价值比率 (%)',
                    '固定资产比重 (%)', '资产负债率 (%)', '经营现金净流量对销售收入比率 (%)', '资产的经营现金流量回报率 (%)',
                    '经营现金净流量与净利润的比率 (%)', '经营现金净流量对负债比率 (%)', '现金流量比率 (%)', '短期股票投资 (元)',
                    '短期债券投资 (元)', '短期其它经营性投资 (元)', '长期股票投资 (元)', '长期债券投资 (元)', '长期其它经营性投资 (元)',
                    '1 年以内应收帐款 (元)', '1-2 年以内应收帐款 (元)', '2-3 年以内应收帐款 (元)', '3 年以内应收帐款 (元)',
                    '1 年以内预付货款 (元)', '1-2 年以内预付货款 (元)', '2-3 年以内预付货款 (元)', '3 年以内预付货款 (元)',
                    '1 年以内其它应收款 (元)', '1-2 年以内其它应收款 (元)', '2-3 年以内其它应收款 (元)', '3 年以内其它应收款 (元)'
                ]
                for col in df.columns:
                    if col not in skip_columns and pd.notna(row.get(col)):
                        val = row.get(col, None)
                        extra_fields[col] = float(val) if isinstance(val, (int, float)) else str(val)
                main_fields['extra_fields'] = extra_fields
                indicators.append(StockFinancialIndicator(**main_fields))
            
            self._set_to_cache(cache_key, indicators)
            logger.info(f"获取新浪财经财务指标数据成功：{symbol}({start_year}), 共{len(indicators)}条")
            return indicators
        except Exception as e:
            logger.error(f"获取新浪财经财务指标数据失败：{e}")
            return []

    async def get_stock_info_a_code_name(self) -> List[StockInfoA]:
        """获取沪深京 A 股股票列表"""
        cache_key = self._get_cache_key('stock_info_a_code_name')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_info_a_code_name())
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stock = StockInfoA(
                    code=str(row.get('code', '')),
                    name=str(row.get('name', ''))
                )
                stocks.append(stock)
            
            self._set_to_cache(cache_key, stocks)
            logger.info(f"获取沪深京 A 股股票列表成功，共{len(stocks)}条")
            return stocks
        except Exception as e:
            logger.error(f"获取沪深京 A 股股票列表失败：{e}")
            return []

    async def get_stock_info_sh_name_code(self, symbol: str = "主板 A 股") -> List[StockInfoSH]:
        """获取上海证券交易所股票列表
        
        Args:
            symbol: 板块类型，可选值："主板 A 股"、"主板 B 股"、"科创板"
        
        Returns:
            上海证券交易所股票列表
        """
        cache_key = self._get_cache_key('stock_info_sh_name_code', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_info_sh_name_code(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                main_fields = {
                    'security_code': str(row.get('证券代码', '')),
                    'security_abbr': str(row.get('证券简称', '')),
                    'company_name': str(row.get('公司全称', '')),
                    'list_date': str(row.get('上市日期', '')),
                }
                
                # 其他字段存储在 extra_fields 中
                extra_fields = {}
                skip_columns = ['证券代码', '证券简称', '公司全称', '上市日期']
                for col in df.columns:
                    if col not in skip_columns and pd.notna(row.get(col)):
                        val = row.get(col, None)
                        extra_fields[col] = str(val)
                main_fields['extra_fields'] = extra_fields
                
                stock = StockInfoSH(**main_fields)
                stocks.append(stock)
            
            self._set_to_cache(cache_key, stocks)
            logger.info(f"获取上海证券交易所股票列表成功 ({symbol}), 共{len(stocks)}条")
            return stocks
        except Exception as e:
            logger.error(f"获取上海证券交易所股票列表失败：{e}")
            return []

    async def get_stock_info_sz_name_code(self, symbol: str = "A 股列表") -> List[StockInfoSZ]:
        """获取深圳证券交易所股票列表
        
        Args:
            symbol: 板块类型，可选值："A 股列表"、"B 股列表"、"CDR 列表"、"AB 股列表"
        
        Returns:
            深圳证券交易所股票列表
        """
        cache_key = self._get_cache_key('stock_info_sz_name_code', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_info_sz_name_code(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                main_fields = {
                    'board': str(row.get('板块', '')),
                    'stock_code': str(row.get('A 股代码', '')),
                    'stock_abbr': str(row.get('A 股简称', '')),
                    'list_date': str(row.get('A 股上市日期', '')),
                    'total_shares': int(row.get('A 股总股本', 0)) if pd.notna(row.get('A 股总股本')) else None,
                    'circulating_shares': int(row.get('A 股流通股本', 0)) if pd.notna(row.get('A 股流通股本')) else None,
                    'industry': str(row.get('所属行业', '')),
                }
                
                # 其他字段存储在 extra_fields 中
                extra_fields = {}
                skip_columns = ['板块', 'A 股代码', 'A 股简称', 'A 股上市日期', 'A 股总股本', 'A 股流通股本', '所属行业']
                for col in df.columns:
                    if col not in skip_columns and pd.notna(row.get(col)):
                        val = row.get(col, None)
                        extra_fields[col] = str(val)
                main_fields['extra_fields'] = extra_fields
                
                stock = StockInfoSZ(**main_fields)
                stocks.append(stock)
            
            self._set_to_cache(cache_key, stocks)
            logger.info(f"获取深圳证券交易所股票列表成功 ({symbol}), 共{len(stocks)}条")
            return stocks
        except Exception as e:
            logger.error(f"获取深圳证券交易所股票列表失败：{e}")
            return []

    async def get_stock_info_bj_name_code(self) -> List[StockInfoBJ]:
        """获取北京证券交易所股票列表"""
        cache_key = self._get_cache_key('stock_info_bj_name_code')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_info_bj_name_code())
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                stock = StockInfoBJ(
                    security_code=str(row.get('证券代码', '')),
                    security_abbr=str(row.get('证券简称', '')),
                    total_shares=int(row.get('总股本', 0)) if pd.notna(row.get('总股本')) else None,
                    circulating_shares=int(row.get('流通股本', 0)) if pd.notna(row.get('流通股本')) else None,
                    list_date=str(row.get('上市日期', '')),
                    industry=str(row.get('所属行业', '')),
                    region=str(row.get('地区', '')),
                    report_date=str(row.get('报告日期', ''))
                )
                stocks.append(stock)
            
            self._set_to_cache(cache_key, stocks)
            logger.info(f"获取北京证券交易所股票列表成功，共{len(stocks)}条")
            return stocks
        except Exception as e:
            logger.error(f"获取北京证券交易所股票列表失败：{e}")
            return []

    async def get_stock_industry_clf_hist_sw(self) -> List[StockIndustryClfHistSW]:
        """获取申万行业分类变动历史"""
        cache_key = self._get_cache_key('stock_industry_clf_hist_sw')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_industry_clf_hist_sw())
            
            if df is None or df.empty:
                return []
            
            industries = []
            for _, row in df.iterrows():
                industry = StockIndustryClfHistSW(
                    symbol=str(row.get('symbol', '')),
                    start_date=str(row.get('start_date', '')),
                    industry_code=str(row.get('industry_code', '')),
                    update_time=str(row.get('update_time', ''))
                )
                industries.append(industry)
            
            self._set_to_cache(cache_key, industries)
            logger.info(f"获取申万行业分类变动历史成功，共{len(industries)}条")
            return industries
        except Exception as e:
            logger.error(f"获取申万行业分类变动历史失败：{e}")
            return []

    async def get_stock_industry_pe_ratio_cninfo(self, symbol: str = "国证行业分类", date: str = None) -> List[StockIndustryPERatio]:
        """获取行业市盈率
        
        Args:
            symbol: 行业分类类型，可选值："证监会行业分类"、"国证行业分类"
            date: 交易日，格式 YYYYMMDD，默认为最近日期
        
        Returns:
            行业市盈率数据列表
        """
        if date is None:
            from datetime import datetime
            date = datetime.now().strftime("%Y%m%d")
        
        cache_key = self._get_cache_key('stock_industry_pe_ratio_cninfo', symbol=symbol, date=date)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_industry_pe_ratio_cninfo(symbol=symbol, date=date)
            )
            
            if df is None or df.empty:
                return []
            
            pe_ratios = []
            for _, row in df.iterrows():
                main_fields = {
                    'change_date': str(row.get('变动日期', '')),
                    'industry_class': str(row.get('行业分类', '')),
                    'industry_level': int(row.get('行业层级', 0)) if pd.notna(row.get('行业层级')) else None,
                    'industry_code': str(row.get('行业编码', '')),
                    'industry_name': str(row.get('行业名称', '')),
                    'company_count': float(row.get('公司数量', 0)) if pd.notna(row.get('公司数量')) else None,
                    'calc_company_count': float(row.get('纳入计算公司数量', 0)) if pd.notna(row.get('纳入计算公司数量')) else None,
                    'total_market_cap': float(row.get('总市值 - 静态', 0)) if pd.notna(row.get('总市值 - 静态')) else None,
                    'net_profit': float(row.get('净利润 - 静态', 0)) if pd.notna(row.get('净利润 - 静态')) else None,
                    'pe_static_weighted': float(row.get('静态市盈率 - 加权平均', 0)) if pd.notna(row.get('静态市盈率 - 加权平均')) else None,
                    'pe_static_median': float(row.get('静态市盈率 - 中位数', 0)) if pd.notna(row.get('静态市盈率 - 中位数')) else None,
                    'pe_static_arithmetic': float(row.get('静态市盈率 - 算术平均', 0)) if pd.notna(row.get('静态市盈率 - 算术平均')) else None,
                }
                
                # 其他字段存储在 extra_fields 中
                extra_fields = {}
                skip_columns = ['变动日期', '行业分类', '行业层级', '行业编码', '行业名称', '公司数量', 
                               '纳入计算公司数量', '总市值 - 静态', '净利润 - 静态', '静态市盈率 - 加权平均',
                               '静态市盈率 - 中位数', '静态市盈率 - 算术平均']
                for col in df.columns:
                    if col not in skip_columns and pd.notna(row.get(col)):
                        val = row.get(col, None)
                        extra_fields[col] = str(val)
                main_fields['extra_fields'] = extra_fields
                
                pe_ratio = StockIndustryPERatio(**main_fields)
                pe_ratios.append(pe_ratio)
            
            self._set_to_cache(cache_key, pe_ratios)
            logger.info(f"获取行业市盈率数据成功 ({symbol}, {date}), 共{len(pe_ratios)}条")
            return pe_ratios
        except Exception as e:
            logger.error(f"获取行业市盈率数据失败：{e}")
            return []

    async def get_stock_hold_num_cninfo(self, date: str) -> List[StockHoldNumCNInfo]:
        """获取股东人数及持股集中度
        
        Args:
            date: 报告期，格式 YYYYMMDD，可选值：XXXX0331、XXXX0630、XXXX0930、XXXX1231
                  从 20170331 开始
        
        Returns:
            股东人数及持股集中度数据列表
        """
        cache_key = self._get_cache_key('stock_hold_num_cninfo', date=date)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_hold_num_cninfo(date=date)
            )
            
            if df is None or df.empty:
                return []
            
            hold_nums = []
            for _, row in df.iterrows():
                main_fields = {
                    'security_code': str(row.get('证券代码', '')),
                    'security_abbr': str(row.get('证券简称', '')),
                    'change_date': str(row.get('变动日期', '')),
                    'current_holder_count': int(row.get('本期股东人数', 0)) if pd.notna(row.get('本期股东人数')) else None,
                    'previous_holder_count': float(row.get('上期股东人数', 0)) if pd.notna(row.get('上期股东人数')) else None,
                    'holder_count_growth': float(row.get('股东人数增幅', 0)) if pd.notna(row.get('股东人数增幅')) else None,
                    'current_avg_shares': int(row.get('本期人均持股数量', 0)) if pd.notna(row.get('本期人均持股数量')) else None,
                    'previous_avg_shares': float(row.get('上期人均持股数量', 0)) if pd.notna(row.get('上期人均持股数量')) else None,
                    'avg_shares_growth': float(row.get('人均持股数量增幅', 0)) if pd.notna(row.get('人均持股数量增幅')) else None,
                }
                
                # 其他字段存储在 extra_fields 中
                extra_fields = {}
                skip_columns = ['证券代码', '证券简称', '变动日期', '本期股东人数', '上期股东人数', 
                               '股东人数增幅', '本期人均持股数量', '上期人均持股数量', '人均持股数量增幅']
                for col in df.columns:
                    if col not in skip_columns and pd.notna(row.get(col)):
                        val = row.get(col, None)
                        extra_fields[col] = str(val)
                main_fields['extra_fields'] = extra_fields
                
                hold_num = StockHoldNumCNInfo(**main_fields)
                hold_nums.append(hold_num)
            
            self._set_to_cache(cache_key, hold_nums)
            logger.info(f"获取股东人数及持股集中度数据成功 ({date}), 共{len(hold_nums)}条")
            return hold_nums
        except Exception as e:
            logger.error(f"获取股东人数及持股集中度数据失败：{e}")
            return []

    async def get_stock_price_js(self, symbol: str = "us") -> List[StockPriceJS]:
        """获取美港目标价
        
        Args:
            symbol: 市场类型，可选值："us"（美股）、"hk"（港股）
        
        Returns:
            美港目标价数据列表
        """
        cache_key = self._get_cache_key('stock_price_js', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_price_js(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            price_targets = []
            for _, row in df.iterrows():
                main_fields = {
                    'date': str(row.get('日期', '')),
                    'stock_name': str(row.get('个股名称', '')),
                    'rating': str(row.get('评级', '')) if pd.notna(row.get('评级')) else None,
                    'previous_target': float(row.get('先前目标价', 0)) if pd.notna(row.get('先前目标价')) else None,
                    'latest_target': float(row.get('最新目标价', 0)) if pd.notna(row.get('最新目标价')) else None,
                    'institution': str(row.get('机构名称', '')),
                }
                
                # 其他字段存储在 extra_fields 中
                extra_fields = {}
                skip_columns = ['日期', '个股名称', '评级', '先前目标价', '最新目标价', '机构名称']
                for col in df.columns:
                    if col not in skip_columns and pd.notna(row.get(col)):
                        val = row.get(col, None)
                        extra_fields[col] = str(val)
                main_fields['extra_fields'] = extra_fields
                
                price_target = StockPriceJS(**main_fields)
                price_targets.append(price_target)
            
            self._set_to_cache(cache_key, price_targets)
            logger.info(f"获取美港目标价数据成功 ({symbol}), 共{len(price_targets)}条")
            return price_targets
        except Exception as e:
            logger.error(f"获取美港目标价数据失败：{e}")
            return []

    async def get_stock_a_congestion_lg(self) -> List[StockAConestionLG]:
        """获取乐咕乐股 - 大盘拥挤度"""
        cache_key = self._get_cache_key('stock_a_congestion_lg')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_a_congestion_lg())
            
            if df is None or df.empty:
                return []
            
            congestion_data = []
            for _, row in df.iterrows():
                congestion = StockAConestionLG(
                    date=str(row.get('date', '')),
                    close=float(row.get('close', 0)) if pd.notna(row.get('close')) else None,
                    congestion=float(row.get('congestion', 0)) if pd.notna(row.get('congestion')) else None
                )
                congestion_data.append(congestion)
            
            self._set_to_cache(cache_key, congestion_data)
            logger.info(f"获取乐咕乐股大盘拥挤度成功，共{len(congestion_data)}条")
            return congestion_data
        except Exception as e:
            logger.error(f"获取乐咕乐股大盘拥挤度失败：{e}")
            return []

    async def get_stock_ebs_lg(self) -> List[StockEBSLG]:
        """获取乐咕乐股 - 股债利差"""
        cache_key = self._get_cache_key('stock_ebs_lg')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_ebs_lg())
            
            if df is None or df.empty:
                return []
            
            ebs_data = []
            for _, row in df.iterrows():
                ebs = StockEBSLG(
                    date=str(row.get('日期', '')),
                    hs300_index=float(row.get('沪深 300 指数', 0)) if pd.notna(row.get('沪深 300 指数')) else None,
                    ebs=float(row.get('股债利差', 0)) if pd.notna(row.get('股债利差')) else None,
                    ebs_ma=float(row.get('股债利差均线', 0)) if pd.notna(row.get('股债利差均线')) else None
                )
                ebs_data.append(ebs)
            
            self._set_to_cache(cache_key, ebs_data)
            logger.info(f"获取乐咕乐股股债利差成功，共{len(ebs_data)}条")
            return ebs_data
        except Exception as e:
            logger.error(f"获取乐咕乐股股债利差失败：{e}")
            return []

    async def get_stock_buffett_index_lg(self) -> List[StockBuffettIndexLG]:
        """获取乐咕乐股 - 巴菲特指标"""
        cache_key = self._get_cache_key('stock_buffett_index_lg')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_buffett_index_lg())
            
            if df is None or df.empty:
                return []
            
            buffett_data = []
            for _, row in df.iterrows():
                buffett = StockBuffettIndexLG(
                    date=str(row.get('日期', '')),
                    close=float(row.get('收盘价', 0)) if pd.notna(row.get('收盘价')) else None,
                    total_market_cap=float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None,
                    gdp=float(row.get('GDP', 0)) if pd.notna(row.get('GDP')) else None,
                    decile_10y=float(row.get('近十年分位数', 0)) if pd.notna(row.get('近十年分位数')) else None,
                    decile_all=float(row.get('总历史分位数', 0)) if pd.notna(row.get('总历史分位数')) else None
                )
                buffett_data.append(buffett)
            
            self._set_to_cache(cache_key, buffett_data)
            logger.info(f"获取乐咕乐股巴菲特指标成功，共{len(buffett_data)}条")
            return buffett_data
        except Exception as e:
            logger.error(f"获取乐咕乐股巴菲特指标失败：{e}")
            return []

    async def get_stock_zh_valuation_baidu(
        self, 
        symbol: str, 
        indicator: str = "总市值", 
        period: str = "近一年"
    ) -> List[StockZhValuationBaidu]:
        """获取百度股市通-A 股估值数据"""
        cache_key = self._get_cache_key(f'stock_zh_valuation_baidu_{symbol}_{indicator}_{period}')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_zh_valuation_baidu(symbol=symbol, indicator=indicator, period=period)
            )
            
            if df is None or df.empty:
                return []
            
            valuation_data = []
            for _, row in df.iterrows():
                valuation = StockZhValuationBaidu(
                    date=str(row.get('date', '')),
                    value=float(row.get('value', 0)) if pd.notna(row.get('value')) else None
                )
                valuation_data.append(valuation)
            
            self._set_to_cache(cache_key, valuation_data)
            logger.info(f"获取百度股市通{symbol}估值数据成功，共{len(valuation_data)}条")
            return valuation_data
        except Exception as e:
            logger.error(f"获取百度股市通估值数据失败：{e}")
            return []

    async def get_stock_value_em(self, symbol: str) -> List[StockValueEM]:
        """获取东方财富网 - 个股估值数据"""
        cache_key = self._get_cache_key(f'stock_value_em_{symbol}')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_value_em(symbol=symbol))
            
            if df is None or df.empty:
                return []
            
            value_data = []
            for _, row in df.iterrows():
                value = StockValueEM(
                    report_date=str(row.get('数据日期', '')),
                    close_price=float(row.get('当日收盘价', 0)) if pd.notna(row.get('当日收盘价')) else None,
                    change_pct=float(row.get('当日涨跌幅', 0)) if pd.notna(row.get('当日涨跌幅')) else None,
                    total_mv=float(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None,
                    float_mv=float(row.get('流通市值', 0)) if pd.notna(row.get('流通市值')) else None,
                    total_shares=float(row.get('总股本', 0)) if pd.notna(row.get('总股本')) else None,
                    float_shares=float(row.get('流通股本', 0)) if pd.notna(row.get('流通股本')) else None,
                    pe_ttm=float(row.get('PE(TTM)', 0)) if pd.notna(row.get('PE(TTM)')) else None,
                    pe_static=float(row.get('PE(静)', 0)) if pd.notna(row.get('PE(静)')) else None,
                    pb=float(row.get('市净率', 0)) if pd.notna(row.get('市净率')) else None,
                    peg=float(row.get('PEG 值', 0)) if pd.notna(row.get('PEG 值')) else None,
                    pc=float(row.get('市现率', 0)) if pd.notna(row.get('市现率')) else None,
                    ps=float(row.get('市销率', 0)) if pd.notna(row.get('市销率')) else None
                )
                value_data.append(value)
            
            self._set_to_cache(cache_key, value_data)
            logger.info(f"获取东方财富个股估值{symbol}成功，共{len(value_data)}条")
            return value_data
        except Exception as e:
            logger.error(f"获取东方财富个股估值失败：{e}")
            return []

    async def get_stock_zh_vote_baidu(
        self, 
        symbol: str, 
        indicator: str = "股票"
    ) -> List[StockZhVoteBaidu]:
        """获取百度股市通 - 涨跌投票数据"""
        cache_key = self._get_cache_key(f'stock_zh_vote_baidu_{symbol}_{indicator}')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_zh_vote_baidu(symbol=symbol, indicator=indicator)
            )
            
            if df is None or df.empty:
                return []
            
            vote_data = []
            for _, row in df.iterrows():
                vote = StockZhVoteBaidu(
                    period=str(row.get('周期', '')),
                    vote_up=int(row.get('看涨', 0)) if pd.notna(row.get('看涨')) else None,
                    vote_down=int(row.get('看跌', 0)) if pd.notna(row.get('看跌')) else None,
                    vote_up_ratio=float(row.get('看涨比例', 0)) if pd.notna(row.get('看涨比例')) else None,
                    vote_down_ratio=float(row.get('看跌比例', 0)) if pd.notna(row.get('看跌比例')) else None
                )
                vote_data.append(vote)
            
            self._set_to_cache(cache_key, vote_data)
            logger.info(f"获取百度股市通涨跌投票{symbol}成功，共{len(vote_data)}条")
            return vote_data
        except Exception as e:
            logger.error(f"获取百度股市通涨跌投票失败：{e}")
            return []

    async def get_stock_a_high_low_statistics(
        self, 
        symbol: str = "all"
    ) -> List[StockAHighLowStatistics]:
        """获取乐咕乐股 - 创新高/新低统计数据"""
        cache_key = self._get_cache_key(f'stock_a_high_low_statistics_{symbol}')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_a_high_low_statistics(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            hl_data = []
            for _, row in df.iterrows():
                hl = StockAHighLowStatistics(
                    date=str(row.get('date', '')),
                    close=float(row.get('close', 0)) if pd.notna(row.get('close')) else None,
                    high20=int(row.get('high20', 0)) if pd.notna(row.get('high20')) else None,
                    low20=int(row.get('low20', 0)) if pd.notna(row.get('low20')) else None,
                    high60=int(row.get('high60', 0)) if pd.notna(row.get('high60')) else None,
                    low60=int(row.get('low60', 0)) if pd.notna(row.get('low60')) else None,
                    high120=int(row.get('high120', 0)) if pd.notna(row.get('high120')) else None,
                    low120=int(row.get('low120', 0)) if pd.notna(row.get('low120')) else None
                )
                hl_data.append(hl)
            
            self._set_to_cache(cache_key, hl_data)
            logger.info(f"获取乐咕乐股创新高/新低统计{symbol}成功，共{len(hl_data)}条")
            return hl_data
        except Exception as e:
            logger.error(f"获取乐咕乐股创新高/新低统计失败：{e}")
            return []

    async def get_stock_a_below_net_asset_statistics(
        self, 
        symbol: str = "全部 A 股"
    ) -> List[StockABelowNetAssetStatistics]:
        """获取乐咕乐股 - 破净股统计数据"""
        cache_key = self._get_cache_key(f'stock_a_below_net_asset_statistics_{symbol}')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_a_below_net_asset_statistics(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            bn_data = []
            for _, row in df.iterrows():
                bn = StockABelowNetAssetStatistics(
                    date=str(row.get('date', '')),
                    below_net_asset=int(row.get('below_net_asset', 0)) if pd.notna(row.get('below_net_asset')) else None,
                    total_company=int(row.get('total_company', 0)) if pd.notna(row.get('total_company')) else None,
                    below_net_asset_ratio=float(row.get('below_net_asset_ratio', 0)) if pd.notna(row.get('below_net_asset_ratio')) else None
                )
                bn_data.append(bn)
            
            self._set_to_cache(cache_key, bn_data)
            logger.info(f"获取乐咕乐股破净股统计{symbol}成功，共{len(bn_data)}条")
            return bn_data
        except Exception as e:
            logger.error(f"获取乐咕乐股破净股统计失败：{e}")
            return []

    async def get_stock_dzjy_sctj(self) -> List[StockDzjySctj]:
        """获取东方财富网 - 大宗交易市场统计"""
        cache_key = self._get_cache_key('stock_dzjy_sctj')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_dzjy_sctj())
            
            if df is None or df.empty:
                return []
            
            sctj_data = []
            for _, row in df.iterrows():
                sctj = StockDzjySctj(
                    index=int(row.get('序号', 0)) if pd.notna(row.get('序号')) else None,
                    date=str(row.get('交易日期', '')),
                    sh_index=float(row.get('上证指数', 0)) if pd.notna(row.get('上证指数')) else None,
                    sh_change_pct=float(row.get('上证指数涨跌幅', 0)) if pd.notna(row.get('上证指数涨跌幅')) else None,
                    total_amount=float(row.get('大宗交易成交总额', 0)) if pd.notna(row.get('大宗交易成交总额')) else None,
                    premium_amount=float(row.get('溢价成交总额', 0)) if pd.notna(row.get('溢价成交总额')) else None,
                    premium_ratio=float(row.get('溢价成交总额占比', 0)) if pd.notna(row.get('溢价成交总额占比')) else None,
                    discount_amount=float(row.get('折价成交总额', 0)) if pd.notna(row.get('折价成交总额')) else None,
                    discount_ratio=float(row.get('折价成交总额占比', 0)) if pd.notna(row.get('折价成交总额占比')) else None
                )
                sctj_data.append(sctj)
            
            self._set_to_cache(cache_key, sctj_data)
            logger.info(f"获取大宗交易市场统计成功，共{len(sctj_data)}条")
            return sctj_data
        except Exception as e:
            logger.error(f"获取大宗交易市场统计失败：{e}")
            return []

    async def get_stock_dzjy_mrmx(
        self,
        symbol: str = "A 股",
        start_date: str = "",
        end_date: str = ""
    ) -> List[StockDzjyMrmx]:
        """获取东方财富网 - 大宗交易每日明细"""
        cache_key = self._get_cache_key(f'stock_dzjy_mrmx_{symbol}_{start_date}_{end_date}')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_dzjy_mrmx(symbol=symbol, start_date=start_date, end_date=end_date)
            )
            
            if df is None or df.empty:
                return []
            
            mrmx_data = []
            for _, row in df.iterrows():
                mrmx = StockDzjyMrmx(
                    index=int(row.get('序号', 0)) if pd.notna(row.get('序号')) else None,
                    date=str(row.get('交易日期', '')),
                    stock_code=str(row.get('证券代码', '')),
                    stock_name=str(row.get('证券简称', '')),
                    change_pct=float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    close_price=float(row.get('收盘价', 0)) if pd.notna(row.get('收盘价')) else None,
                    deal_price=float(row.get('成交价', 0)) if pd.notna(row.get('成交价')) else None,
                    premium_ratio=float(row.get('折溢率', 0)) if pd.notna(row.get('折溢率')) else None,
                    volume=int(row.get('成交量', 0)) if pd.notna(row.get('成交量')) else None,
                    amount=float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    amount_ratio=float(row.get('成交额/流通市值', 0)) if pd.notna(row.get('成交额/流通市值')) else None,
                    buyer_dept=str(row.get('买方营业部', '')),
                    seller_dept=str(row.get('卖方营业部', ''))
                )
                mrmx_data.append(mrmx)
            
            self._set_to_cache(cache_key, mrmx_data)
            logger.info(f"获取大宗交易每日明细{symbol}成功，共{len(mrmx_data)}条")
            return mrmx_data
        except Exception as e:
            logger.error(f"获取大宗交易每日明细失败：{e}")
            return []

    async def get_stock_margin_ratio_pa(
        self,
        symbol: str = "深市",
        date: str = ""
    ) -> List[StockMarginRatioPa]:
        """获取平安证券 - 融资融券标的证券及保证金比例"""
        cache_key = self._get_cache_key(f'stock_margin_ratio_pa_{symbol}_{date}')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, 
                lambda: ak.stock_margin_ratio_pa(symbol=symbol, date=date)
            )
            
            if df is None or df.empty:
                return []
            
            ratio_data = []
            for _, row in df.iterrows():
                ratio = StockMarginRatioPa(
                    stock_code=str(row.get('证券代码', '')),
                    stock_name=str(row.get('证券简称', '')),
                    margin_ratio=float(row.get('融资比例', 0)) if pd.notna(row.get('融资比例')) else None,
                    short_ratio=float(row.get('融券比例', 0)) if pd.notna(row.get('融券比例')) else None
                )
                ratio_data.append(ratio)
            
            self._set_to_cache(cache_key, ratio_data)
            logger.info(f"获取融资融券保证金比例{symbol}成功，共{len(ratio_data)}条")
            return ratio_data
        except Exception as e:
            logger.error(f"获取融资融券保证金比例失败：{e}")
            return []

    async def get_stock_margin_account_info(self) -> List[StockMarginAccountInfo]:
        """获取东方财富网 - 融资融券账户统计"""
        cache_key = self._get_cache_key('stock_margin_account_info')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(None, lambda: ak.stock_margin_account_info())
            
            if df is None or df.empty:
                return []
            
            info_data = []
            for _, row in df.iterrows():
                info = StockMarginAccountInfo(
                    date=str(row.get('日期', '')),
                    margin_balance=float(row.get('融资余额', 0)) if pd.notna(row.get('融资余额')) else None,
                    short_balance=float(row.get('融券余额', 0)) if pd.notna(row.get('融券余额')) else None,
                    margin_buy=float(row.get('融资买入额', 0)) if pd.notna(row.get('融资买入额')) else None,
                    short_sell=float(row.get('融券卖出额', 0)) if pd.notna(row.get('融券卖出额')) else None,
                    broker_count=int(row.get('证券公司数量', 0)) if pd.notna(row.get('证券公司数量')) else None,
                    branch_count=int(row.get('营业部数量', 0)) if pd.notna(row.get('营业部数量')) else None,
                    individual_count=float(row.get('个人投资者数量', 0)) if pd.notna(row.get('个人投资者数量')) else None,
                    institution_count=int(row.get('机构投资者数量', 0)) if pd.notna(row.get('机构投资者数量')) else None,
                    active_count=float(row.get('参与交易的投资者数量', 0)) if pd.notna(row.get('参与交易的投资者数量')) else None,
                    debt_count=float(row.get('有融资融券负债的投资者数量', 0)) if pd.notna(row.get('有融资融券负债的投资者数量')) else None,
                    collateral_value=float(row.get('担保物总价值', 0)) if pd.notna(row.get('担保物总价值')) else None,
                    collateral_ratio=float(row.get('平均维持担保比例', 0)) if pd.notna(row.get('平均维持担保比例')) else None
                )
                info_data.append(info)
            
            self._set_to_cache(cache_key, info_data)
            logger.info(f"获取融资融券账户统计成功，共{len(info_data)}条")
            return info_data
        except Exception as e:
            logger.error(f"获取融资融券账户统计失败：{e}")
            return []

    async def get_stock_margin_sse(self, start_date: str, end_date: str) -> List[StockMarginSse]:
        """获取上海证券交易所 - 融资融券汇总数据
        
        Args:
            start_date: 开始日期，格式 YYYYMMDD
            end_date: 结束日期，格式 YYYYMMDD
        
        Returns:
            融资融券汇总数据列表
        """
        cache_key = self._get_cache_key('stock_margin_sse', start_date=start_date, end_date=end_date)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_margin_sse(start_date=start_date, end_date=end_date)
            )
            
            if df is None or df.empty:
                return []
            
            margin_data = []
            for _, row in df.iterrows():
                margin = StockMarginSse(
                    credit_trade_date=str(row.get('信用交易日期', '')),
                    margin_balance=int(row.get('融资余额', 0)) if pd.notna(row.get('融资余额')) else None,
                    margin_buy=int(row.get('融资买入额', 0)) if pd.notna(row.get('融资买入额')) else None,
                    short_remaining=int(row.get('融券余量', 0)) if pd.notna(row.get('融券余量')) else None,
                    short_remaining_amount=int(row.get('融券余量金额', 0)) if pd.notna(row.get('融券余量金额')) else None,
                    short_sell=int(row.get('融券卖出量', 0)) if pd.notna(row.get('融券卖出量')) else None,
                    total_margin_short_balance=int(row.get('融资融券余额', 0)) if pd.notna(row.get('融资融券余额')) else None
                )
                margin_data.append(margin)
            
            self._set_to_cache(cache_key, margin_data)
            logger.info(f"获取上交所融资融券汇总成功 ({start_date}-{end_date}), 共{len(margin_data)}条")
            return margin_data
        except Exception as e:
            logger.error(f"获取上交所融资融券汇总失败：{e}")
            return []

    async def get_stock_margin_detail_sse(self, date: str) -> List[StockMarginDetailSse]:
        """获取上海证券交易所 - 融资融券明细数据
        
        Args:
            date: 交易日期，格式 YYYYMMDD
        
        Returns:
            融资融券明细数据列表
        """
        cache_key = self._get_cache_key('stock_margin_detail_sse', date=date)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_margin_detail_sse(date=date)
            )
            
            if df is None or df.empty:
                return []
            
            detail_data = []
            for _, row in df.iterrows():
                detail = StockMarginDetailSse(
                    credit_trade_date=str(row.get('信用交易日期', '')),
                    stock_code=str(row.get('标的证券代码', '')),
                    stock_name=str(row.get('标的证券简称', '')),
                    margin_balance=int(row.get('融资余额', 0)) if pd.notna(row.get('融资余额')) else None,
                    margin_buy=int(row.get('融资买入额', 0)) if pd.notna(row.get('融资买入额')) else None,
                    margin_repay=int(row.get('融资偿还额', 0)) if pd.notna(row.get('融资偿还额')) else None,
                    short_remaining=int(row.get('融券余量', 0)) if pd.notna(row.get('融券余量')) else None,
                    short_sell=int(row.get('融券卖出量', 0)) if pd.notna(row.get('融券卖出量')) else None,
                    short_repay=int(row.get('融券偿还量', 0)) if pd.notna(row.get('融券偿还量')) else None
                )
                detail_data.append(detail)
            
            self._set_to_cache(cache_key, detail_data)
            logger.info(f"获取上交所融资融券明细成功 ({date}), 共{len(detail_data)}条")
            return detail_data
        except Exception as e:
            logger.error(f"获取上交所融资融券明细失败：{e}")
            return []

    async def get_stock_margin_szse(self, date: str) -> List[StockMarginSzse]:
        """获取深圳证券交易所 - 融资融券汇总数据
        
        Args:
            date: 交易日期，格式 YYYYMMDD
        
        Returns:
            融资融券汇总数据列表
        """
        cache_key = self._get_cache_key('stock_margin_szse', date=date)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_margin_szse(date=date)
            )
            
            if df is None or df.empty:
                return []
            
            margin_data = []
            for _, row in df.iterrows():
                margin = StockMarginSzse(
                    margin_buy=float(row.get('融资买入额', 0)) if pd.notna(row.get('融资买入额')) else None,
                    margin_balance=float(row.get('融资余额', 0)) if pd.notna(row.get('融资余额')) else None,
                    short_sell=float(row.get('融券卖出量', 0)) if pd.notna(row.get('融券卖出量')) else None,
                    short_remaining=float(row.get('融券余量', 0)) if pd.notna(row.get('融券余量')) else None,
                    short_balance=float(row.get('融券余额', 0)) if pd.notna(row.get('融券余额')) else None,
                    total_margin_short_balance=float(row.get('融资融券余额', 0)) if pd.notna(row.get('融资融券余额')) else None
                )
                margin_data.append(margin)
            
            self._set_to_cache(cache_key, margin_data)
            logger.info(f"获取深交所融资融券汇总成功 ({date}), 共{len(margin_data)}条")
            return margin_data
        except Exception as e:
            logger.error(f"获取深交所融资融券汇总失败：{e}")
            return []

    async def get_stock_margin_detail_szse(self, date: str) -> List[StockMarginDetailSzse]:
        """获取深圳证券交易所 - 融资融券明细数据
        
        Args:
            date: 交易日期，格式 YYYYMMDD
        
        Returns:
            融资融券明细数据列表
        """
        cache_key = self._get_cache_key('stock_margin_detail_szse', date=date)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_margin_detail_szse(date=date)
            )
            
            if df is None or df.empty:
                return []
            
            detail_data = []
            for _, row in df.iterrows():
                detail = StockMarginDetailSzse(
                    stock_code=str(row.get('证券代码', '')),
                    stock_name=str(row.get('证券简称', '')),
                    margin_buy=int(row.get('融资买入额', 0)) if pd.notna(row.get('融资买入额')) else None,
                    margin_balance=int(row.get('融资余额', 0)) if pd.notna(row.get('融资余额')) else None,
                    short_sell=int(row.get('融券卖出量', 0)) if pd.notna(row.get('融券卖出量')) else None,
                    short_remaining=int(row.get('融券余量', 0)) if pd.notna(row.get('融券余量')) else None,
                    short_balance=int(row.get('融券余额', 0)) if pd.notna(row.get('融券余额')) else None,
                    total_margin_short_balance=int(row.get('融资融券余额', 0)) if pd.notna(row.get('融资融券余额')) else None
                )
                detail_data.append(detail)
            
            self._set_to_cache(cache_key, detail_data)
            logger.info(f"获取深交所融资融券明细成功 ({date}), 共{len(detail_data)}条")
            return detail_data
        except Exception as e:
            logger.error(f"获取深交所融资融券明细失败：{e}")
            return []

    async def get_stock_margin_underlying_info_szse(self, date: str) -> List[StockMarginUnderlyingInfoSzse]:
        """获取深圳证券交易所 - 标的证券信息
        
        Args:
            date: 交易日期，格式 YYYYMMDD
        
        Returns:
            标的证券信息数据列表
        """
        cache_key = self._get_cache_key('stock_margin_underlying_info_szse', date=date)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_margin_underlying_info_szse(date=date)
            )
            
            if df is None or df.empty:
                return []
            
            info_data = []
            for _, row in df.iterrows():
                info = StockMarginUnderlyingInfoSzse(
                    stock_code=str(row.get('证券代码', '')),
                    stock_name=str(row.get('证券简称', '')),
                    margin_target=str(row.get('融资标的', '')),
                    short_target=str(row.get('融券标的', '')),
                    margin_available_today=str(row.get('当日可融资', '')),
                    short_available_today=str(row.get('当日可融券', '')),
                    short_sell_price_restriction=str(row.get('融券卖出价格限制', '')),
                    price_limit=str(row.get('涨跌幅限制', ''))
                )
                info_data.append(info)
            
            self._set_to_cache(cache_key, info_data)
            logger.info(f"获取深交所标的证券信息成功 ({date}), 共{len(info_data)}条")
            return info_data
        except Exception as e:
            logger.error(f"获取深交所标的证券信息失败：{e}")
            return []

    async def get_stock_profit_forecast_em(self, symbol: str = "") -> List[StockProfitForecastEm]:
        """获取东方财富网 - 盈利预测
        
        Args:
            symbol: 行业板块名称，默认为空（获取全部数据）
        
        Returns:
            盈利预测数据列表
        """
        cache_key = self._get_cache_key('stock_profit_forecast_em', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_profit_forecast_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            forecast_data = []
            for _, row in df.iterrows():
                forecast = StockProfitForecastEm(
                    serial_number=int(row.get('序号', 0)) if pd.notna(row.get('序号')) else None,
                    stock_code=str(row.get('代码', '')),
                    stock_name=str(row.get('名称', '')),
                    report_count=int(row.get('研报数', 0)) if pd.notna(row.get('研报数')) else None,
                    buy_rating=float(row.get('机构投资评级 (近六个月)-买入', 0)) if pd.notna(row.get('机构投资评级 (近六个月)-买入')) else None,
                    add_rating=float(row.get('机构投资评级 (近六个月)-增持', 0)) if pd.notna(row.get('机构投资评级 (近六个月)-增持')) else None,
                    neutral_rating=float(row.get('机构投资评级 (近六个月)-中性', 0)) if pd.notna(row.get('机构投资评级 (近六个月)-中性')) else None,
                    reduce_rating=int(row.get('机构投资评级 (近六个月)-减持', 0)) if pd.notna(row.get('机构投资评级 (近六个月)-减持')) else None,
                    sell_rating=int(row.get('机构投资评级 (近六个月)-卖出', 0)) if pd.notna(row.get('机构投资评级 (近六个月)-卖出')) else None,
                    eps_2022=float(row.get('2022 预测每股收益', 0)) if pd.notna(row.get('2022 预测每股收益')) else None,
                    eps_2023=float(row.get('2023 预测每股收益', 0)) if pd.notna(row.get('2023 预测每股收益')) else None,
                    eps_2024=float(row.get('2024 预测每股收益', 0)) if pd.notna(row.get('2024 预测每股收益')) else None,
                    eps_2025=float(row.get('2025 预测每股收益', 0)) if pd.notna(row.get('2025 预测每股收益')) else None
                )
                forecast_data.append(forecast)
            
            self._set_to_cache(cache_key, forecast_data)
            logger.info(f"获取东方财富盈利预测成功 ({symbol or '全部'}), 共{len(forecast_data)}条")
            return forecast_data
        except Exception as e:
            logger.error(f"获取东方财富盈利预测失败：{e}")
            return []

    async def get_stock_board_industry_name_em(self) -> List[StockBoardIndustryNameEm]:
        """获取东方财富 - 行业板块
        
        Returns:
            行业板块数据列表
        """
        cache_key = self._get_cache_key('stock_board_industry_name_em')
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_board_industry_name_em()
            )
            
            if df is None or df.empty:
                return []
            
            board_data = []
            for _, row in df.iterrows():
                board = StockBoardIndustryNameEm(
                    rank=int(row.get('排名', 0)) if pd.notna(row.get('排名')) else None,
                    board_name=str(row.get('板块名称', '')),
                    board_code=str(row.get('板块代码', '')),
                    latest_price=float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    change_amount=float(row.get('涨跌额', 0)) if pd.notna(row.get('涨跌额')) else None,
                    change_percent=float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    total_market_value=int(row.get('总市值', 0)) if pd.notna(row.get('总市值')) else None,
                    turnover_rate=float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else None,
                    rise_count=int(row.get('上涨家数', 0)) if pd.notna(row.get('上涨家数')) else None,
                    fall_count=int(row.get('下跌家数', 0)) if pd.notna(row.get('下跌家数')) else None,
                    leading_stock=str(row.get('领涨股票', '')),
                    leading_stock_change_percent=float(row.get('领涨股票 - 涨跌幅', 0)) if pd.notna(row.get('领涨股票 - 涨跌幅')) else None
                )
                board_data.append(board)
            
            self._set_to_cache(cache_key, board_data)
            logger.info(f"获取东方财富行业板块成功，共{len(board_data)}条")
            return board_data
        except Exception as e:
            logger.error(f"获取东方财富行业板块失败：{e}")
            return []

    async def get_stock_board_industry_spot_em(self, symbol: str) -> List[StockBoardIndustrySpotEm]:
        """获取东方财富 - 行业板块实时行情
        
        Args:
            symbol: 板块名称，如"小金属"
        
        Returns:
            行业板块实时行情数据列表
        """
        cache_key = self._get_cache_key('stock_board_industry_spot_em', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_board_industry_spot_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            spot_data = []
            for _, row in df.iterrows():
                spot = StockBoardIndustrySpotEm(
                    item=str(row.get('item', '')),
                    value=float(row.get('value', 0)) if pd.notna(row.get('value')) else None
                )
                spot_data.append(spot)
            
            self._set_to_cache(cache_key, spot_data)
            logger.info(f"获取东方财富行业板块实时行情成功 ({symbol}), 共{len(spot_data)}条")
            return spot_data
        except Exception as e:
            logger.error(f"获取东方财富行业板块实时行情失败：{e}")
            return []

    async def get_stock_board_industry_cons_em(self, symbol: str) -> List[StockBoardIndustryConsEm]:
        """获取东方财富 - 行业板块成份股
        
        Args:
            symbol: 板块名称或板块代码，如"小金属"或"BK1027"
        
        Returns:
            行业板块成份股数据列表
        """
        cache_key = self._get_cache_key('stock_board_industry_cons_em', symbol=symbol)
        cached = self._get_from_cache(cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: ak.stock_board_industry_cons_em(symbol=symbol)
            )
            
            if df is None or df.empty:
                return []
            
            cons_data = []
            for _, row in df.iterrows():
                cons = StockBoardIndustryConsEm(
                    serial_number=int(row.get('序号', 0)) if pd.notna(row.get('序号')) else None,
                    stock_code=str(row.get('代码', '')),
                    stock_name=str(row.get('名称', '')),
                    latest_price=float(row.get('最新价', 0)) if pd.notna(row.get('最新价')) else None,
                    change_percent=float(row.get('涨跌幅', 0)) if pd.notna(row.get('涨跌幅')) else None,
                    change_amount=float(row.get('涨跌额', 0)) if pd.notna(row.get('涨跌额')) else None,
                    volume=float(row.get('成交量', 0)) if pd.notna(row.get('成交量')) else None,
                    amount=float(row.get('成交额', 0)) if pd.notna(row.get('成交额')) else None,
                    amplitude=float(row.get('振幅', 0)) if pd.notna(row.get('振幅')) else None,
                    high=float(row.get('最高', 0)) if pd.notna(row.get('最高')) else None,
                    low=float(row.get('最低', 0)) if pd.notna(row.get('最低')) else None,
                    open=float(row.get('今开', 0)) if pd.notna(row.get('今开')) else None,
                    prev_close=float(row.get('昨收', 0)) if pd.notna(row.get('昨收')) else None,
                    turnover_rate=float(row.get('换手率', 0)) if pd.notna(row.get('换手率')) else None,
                    pe_ratio_dynamic=float(row.get('市盈率 - 动态', 0)) if pd.notna(row.get('市盈率 - 动态')) else None,
                    pb_ratio=float(row.get('市净率', 0)) if pd.notna(row.get('市净率')) else None
                )
                cons_data.append(cons)
            
            self._set_to_cache(cache_key, cons_data)
            logger.info(f"获取东方财富行业板块成份股成功 ({symbol}), 共{len(cons_data)}条")
            return cons_data
        except Exception as e:
            logger.error(f"获取东方财富行业板块成份股失败：{e}")
            return []