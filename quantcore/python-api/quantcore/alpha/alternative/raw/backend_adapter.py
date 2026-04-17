"""
后端数据适配器

统一对接后端API，为Alpha工厂提供数据支持：
- 行情数据
- 基本面数据
- 资金流向数据
- 舆情/情感数据
- ESG 数据
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class BackendConfig:
    """后端配置"""
    base_url: str = "http://localhost:8000"
    api_version: str = "v1"
    timeout: int = 30
    max_retries: int = 3
    
    # API端点配置
    endpoints: Dict[str, str] = None
    
    def __post_init__(self):
        if self.endpoints is None:
            self.endpoints = {
                'stock_list': '/api/{version}/stocks/',
                'stock_quote': '/api/{version}/stocks/{symbol}/quote',
                'stock_kline': '/api/{version}/stocks/{symbol}/kline',
                'fund_flow': '/api/{version}/stocks/{symbol}/fund-flow',
                'sentiment': '/api/{version}/stocks/{symbol}/sentiment',
                'esg': '/api/{version}/stocks/{symbol}/esg',
                'financials': '/api/{version}/stocks/{symbol}/financials',
                'news': '/api/{version}/stocks/{symbol}/news',
            }


class BackendAdapter:
    """
    后端数据适配器
    
    功能：
    - 统一的数据获取接口
    - 自动重试和错误处理
    - 响应缓存
    - 数据格式标准化
    """
    
    def __init__(self, config: Optional[BackendConfig] = None):
        self.config = config or BackendConfig()
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: int = 300  # 5分钟缓存
        
        logger.info(f"后端适配器初始化: {self.config.base_url}")
    
    def _get_endpoint(self, endpoint_name: str, **kwargs) -> str:
        """构建API端点URL"""
        template = self.config.endpoints.get(endpoint_name, '')
        url = template.format(
            version=self.config.api_version,
            **kwargs
        )
        return f"{self.config.base_url}{url}"
    
    async def _make_request(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> Dict[str, Any]:
        """
        发送HTTP请求
        
        Args:
            endpoint: API端点
            params: 请求参数
            method: HTTP方法
            
        Returns:
            Dict: 响应数据
        """
        import aiohttp
        
        url = self._get_endpoint(endpoint)
        
        for attempt in range(self.config.max_retries):
            try:
                timeout = aiohttp.ClientTimeout(total=self.config.timeout)
                
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    if method.upper() == "GET":
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                return data
                            else:
                                logger.warning(
                                    f"请求失败 {url}: status={response.status}"
                                )
                    else:
                        async with session.post(url, json=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                return data
                            
            except asyncio.TimeoutError:
                logger.warning(
                    f"请求超时 {url} (attempt {attempt + 1})"
                )
                if attempt < self.config.max_retries - 1:
                    await asyncio.sleep(1 * (attempt + 1))
                    
            except Exception as e:
                logger.error(f"请求异常 {url}: {e}")
                break
        
        return {}
    
    def _check_cache(self, key: str) -> Optional[Any]:
        """检查缓存"""
        if key in self._cache:
            cached_data, timestamp = self._cache[key]
            if (datetime.now() - timestamp).seconds < self._cache_ttl:
                return cached_data
            else:
                del self._cache[key]
        return None
    
    def _set_cache(self, key: str, data: Any):
        """设置缓存"""
        self._cache[key] = (data, datetime.now())
    
    async def get_stock_list(
        self,
        limit: int = 5000,
        market: Optional[str] = None
    ) -> List[str]:
        """
        获取股票列表
        
        Args:
            limit: 返回数量限制
            market: 市场 (SH/SZ)
            
        Returns:
            List[str]: 股票代码列表
        """
        cache_key = f"stock_list_{market or 'all'}"
        
        cached = self._check_cache(cache_key)
        if cached:
            return cached
        
        try:
            params = {'limit': limit}
            if market:
                params['market'] = market
            
            response = await self._make_request('stock_list', params=params)
            
            if response and 'data' in response:
                stocks = [item.get('code', '') for item in response['data']]
                stocks = [s for s in stocks if s]
                self._set_cache(cache_key, stocks)
                return stocks
                
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
        
        return []
    
    async def get_stock_quote(self, symbol: str) -> Optional[Dict[str, Any]]:
        """
        获取股票实时行情
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 行情数据
        """
        cache_key = f"quote_{symbol}"
        
        cached = self._check_cache(cache_key)
        if cached:
            return cached
        
        try:
            response = await self._make_request(
                'stock_quote', 
                params={'symbol': symbol}
            )
            
            if response and 'data' in response:
                self._set_cache(cache_key, response['data'])
                return response['data']
                
        except Exception as e:
            logger.debug(f"获取{symbol}行情失败: {e}")
        
        return None
    
    async def get_stock_kline(
        self,
        symbol: str,
        start_date: date,
        end_date: date,
        freq: str = 'daily'
    ) -> pd.DataFrame:
        """
        获取K线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            freq: 频率 (daily/weekly/monthly)
            
        Returns:
            DataFrame: K线数据
        """
        cache_key = f"kline_{symbol}_{start_date}_{end_date}_{freq}"
        
        cached = self._check_cache(cache_key)
        if cached:
            return cached
        
        try:
            params = {
                'symbol': symbol,
                'start_date': str(start_date),
                'end_date': str(end_date),
                'freq': freq
            }
            
            response = await self._make_request('stock_kline', params=params)
            
            if response and 'data' in response:
                df = pd.DataFrame(response['data'])
                
                if not df.empty and 'date' in df.columns:
                    df['date'] = pd.to_datetime(df['date'])
                    df.set_index('date', inplace=True)
                    
                    numeric_cols = ['open', 'high', 'low', 'close', 'volume']
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    self._set_cache(cache_key, df)
                    return df
                    
        except Exception as e:
            logger.debug(f"获取{symbol}K线失败: {e}")
        
        return pd.DataFrame()
    
    async def get_fund_flow_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        获取资金流向数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 资金流向数据
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=60)
        
        cache_key = f"fundflow_{symbol}_{start_date}_{end_date}"
        
        cached = self._check_cache(cache_key)
        if cached:
            return cached
        
        try:
            params = {
                'symbol': symbol,
                'start_date': str(start_date),
                'end_date': str(end_date)
            }
            
            response = await self._make_request('fund_flow', params=params)
            
            if response and 'data' in response:
                df = pd.DataFrame(response['data'])
                
                if not df.empty:
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                    
                    numeric_cols = [
                        'main_net_amount', 'super_large_net', 
                        'large_order_net', 'retail_net'
                    ]
                    for col in numeric_cols:
                        if col in df.columns:
                            df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    self._set_cache(cache_key, df)
                    return df
                    
        except Exception as e:
            logger.debug(f"获取{symbol}资金流向失败: {e}")
        
        return pd.DataFrame()
    
    async def get_sentiment_data(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        获取舆情数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 舆情数据
        """
        cache_key = f"sentiment_{symbol}_{start_date}_{end_date}"
        
        cached = self._check_cache(cache_key)
        if cached:
            return cached
        
        try:
            params = {
                'symbol': symbol,
                'start_date': str(start_date),
                'end_date': str(end_date)
            }
            
            response = await self._make_request('sentiment', params=params)
            
            if response and 'data' in response:
                df = pd.DataFrame(response['data'])
                
                if not df.empty:
                    if 'date' in df.columns:
                        df['date'] = pd.to_datetime(df['date'])
                        df.set_index('date', inplace=True)
                    
                    self._set_cache(cache_key, df)
                    return df
                    
        except Exception as e:
            logger.debug(f"获取{symbol}舆情失败: {e}")
        
        return pd.DataFrame()
    
    async def get_news_articles(
        self,
        symbol: str,
        days_back: int = 7
    ) -> List[Dict[str, Any]]:
        """
        获取新闻文章
        
        Args:
            symbol: 股票代码
            days_back: 回溯天数
            
        Returns:
            List[Dict]: 新闻列表
        """
        cache_key = f"news_{symbol}_{days_back}"
        
        cached = self._check_cache(cache_key)
        if cached:
            return cached
        
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            params = {
                'symbol': symbol,
                'start_date': str(start_date),
                'end_date': str(end_date)
            }
            
            response = await self._make_request('news', params=params)
            
            if response and 'data' in response:
                articles = response['data']
                self._set_cache(cache_key, articles)
                return articles
                
        except Exception as e:
            logger.debug(f"获取{symbol}新闻失败: {e}")
        
        return []
    
    async def get_social_media_posts(
        self,
        symbol: str,
        platform: str = "xueqiu",
        hours_back: int = 24
    ) -> List[Dict[str, any]]:
        """
        获取社交媒体帖子
        
        Args:
            symbol: 股票代码
            platform: 平台
            hours_back: 回溯小时数
            
        Returns:
            List[Dict]: 社交媒体帖子列表
        """
        cache_key = f"social_{symbol}_{platform}_{hours_back}"
        
        cached = self._check_cache(cache_key)
        if cached:
            return cached
        
        try:
            params = {
                'symbol': symbol,
                'platform': platform,
                'hours_back': hours_back
            }
            
            response = await self._make_request(
                'sentiment', 
                params={**params, 'type': 'social'}
            )
            
            if response and 'data' in response:
                posts = response['data']
                self._set_cache(cache_key, posts)
                return posts
                
        except Exception as e:
            logger.debug(f"获取{symbol}社交媒体数据失败: {e}")
        
        return []
    
    async def get_esg_data(
        self,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取ESG数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: ESG数据
        """
        cache_key = f"esg_{symbol}"
        
        cached = self._check_cache(cache_key)
        if cached:
            return cached
        
        try:
            response = await self._make_request(
                'esg',
                params={'symbol': symbol}
            )
            
            if response and 'data' in response:
                self._set_cache(cache_key, response['data'])
                return response['data']
                
        except Exception as e:
            logger.debug(f"获取{symbol}ESG数据失败: {e}")
        
        return None
    
    async def get_esg_events(
        self,
        symbol: str,
        days_back: int = 90
    ) -> List[Dict[str, Any]]:
        """
        获取ESG事件
        
        Args:
            symbol: 股票代码
            days_back: 回溯天数
            
        Returns:
            List[Dict]: ESG事件列表
        """
        cache_key = f"esg_events_{symbol}_{days_back}"
        
        cached = self._check_cache(cache_key)
        if cached:
            return cached
        
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=days_back)
            
            params = {
                'symbol': symbol,
                'start_date': str(start_date),
                'end_date': str(end_date),
                'type': 'events'
            }
            
            response = await self._make_request('esg', params=params)
            
            if response and 'data' in response:
                events = response['data']
                self._set_cache(cache_key, events)
                return events
                
        except Exception as e:
            logger.debug(f"获取{symbol}ESG事件失败: {e}")
        
        return []
    
    async def get_financial_data(
        self,
        symbol: str,
        report_type: str = "annual"
    ) -> Optional[Dict[str, Any]]:
        """
        获取财务数据
        
        Args:
            symbol: 股票代码
            report_type: 报告类型 (annual/quarterly)
            
        Returns:
            Dict: 财务数据
        """
        cache_key = f"financials_{symbol}_{report_type}"
        
        cached = self._check_cache(cache_key)
        if cached:
            return cached
        
        try:
            params = {
                'symbol': symbol,
                'report_type': report_type
            }
            
            response = await self._make_request('financials', params=params)
            
            if response and 'data' in response:
                self._set_cache(cache_key, response['data'])
                return response['data']
                
        except Exception as e:
            logger.debug(f"获取{symbol}财务数据失败: {e}")
        
        return None
    
    async def health_check(self) -> bool:
        """
        检查后端服务健康状态
        
        Returns:
            bool: 是否健康
        """
        try:
            import aiohttp
            
            url = f"{self.config.base_url}/health"
            timeout = aiohttp.ClientTimeout(total=5)
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(url) as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.warning(f"后端健康检查失败: {e}")
            return False
    
    def clear_cache(self):
        """清除缓存"""
        self._cache.clear()
        logger.info("后端适配器缓存已清除")
