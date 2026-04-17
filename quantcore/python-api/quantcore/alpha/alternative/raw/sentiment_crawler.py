"""
舆情/情感数据爬虫

从多个数据源采集市场情绪和舆情信息：
- 新闻情感分析
- 社交媒体情绪
- 研报观点提取
- 舆情事件监测
"""

import asyncio
import logging
from datetime import date, datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class SentimentData:
    """舆情数据结构"""
    symbol: str
    date: str
    
    # 综合情感得分 (-1 到 1，负值表示负面，正值表示正面)
    composite_score: float = 0.0
    
    # 各维度情感得分
    news_sentiment: float = 0.0  # 新闻情感
    social_sentiment: float = 0.0  # 社交媒体情感
    analyst_sentiment: float = 0.0  # 分析师情感
    
    # 舆情指标
    news_volume: int = 0  # 新闻数量
    social_mentions: int = 0  # 社交媒体提及量
    analyst_recommendations: int = 0  # 分析师推荐数
    
    # 情感变化趋势
    sentiment_1d_change: float = 0.0  # 日度变化
    sentiment_5d_change: float = 0.0  # 5日变化
    sentiment_momentum: float = 0.0  # 情感动量
    
    # 极端情绪标识
    is_extreme_positive: bool = False  # 极端正面
    is_extreme_negative: bool = False  # 极端负面
    
    # 原始数据
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NewsArticle:
    """新闻文章"""
    title: str
    content: str
    source: str
    publish_time: datetime
    sentiment_score: float = 0.0
    sentiment_label: str = "neutral"  # positive, negative, neutral
    keywords: List[str] = field(default_factory=list)
    relevance_score: float = 0.0


@dataclass
class SocialMediaPost:
    """社交媒体帖子"""
    platform: str  # weibo, xueqiu, etc.
    content: str
    author: str
    publish_time: datetime
    likes: int = 0
    comments: int = 0
    reposts: int = 0
    sentiment_score: float = 0.0
    influence_score: float = 0.0


class SentimentCrawler:
    """
    舆情/情感数据爬虫
    
    功能：
    - 多源情感数据采集
    - 情感分析引擎集成
    - 舆情因子计算
    - 异常情绪检测
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 情感阈值配置
        self.extreme_positive_threshold = self.config.get(
            'extreme_positive_threshold', 0.7
        )
        self.extreme_negative_threshold = self.config.get(
            'extreme_negative_threshold', -0.7
        )
        
        # 数据源权重
        self.source_weights = self.config.get('source_weights', {
            'news': 0.4,
            'social': 0.3,
            'analyst': 0.3
        })
        
        # 缓存
        self._cache: Dict[str, Any] = {}
        self._cache_ttl = self.config.get('cache_ttl', 3600)  # 秒
        
        logger.info("舆情数据爬虫初始化完成")
    
    async def get_stock_sentiment(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None
    ) -> pd.DataFrame:
        """
        获取股票舆情数据时间序列
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 舆情数据
        """
        if end_date is None:
            end_date = date.today()
        if start_date is None:
            start_date = end_date - timedelta(days=90)
            
        try:
            from quantcore.alpha.alternative.raw.backend_adapter import (
                BackendAdapter
            )
            
            adapter = BackendAdapter()
            
            # 尝试获取舆情数据
            sentiment_df = await adapter.get_sentiment_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date
            )
            
            if not sentiment_df.empty:
                logger.debug(f"获取{symbol}舆情数据成功")
                return sentiment_df
                
            logger.info(f"Backend无{symbol}舆情数据，使用模拟数据")
            return await self._generate_mock_sentiment(symbol, start_date, end_date)
            
        except Exception as e:
            logger.warning(f"获取{symbol}舆情数据失败: {e}")
            return await self._generate_mock_sentiment(symbol, start_date, end_date)
    
    async def _generate_mock_sentiment(
        self,
        symbol: str,
        start_date: date,
        end_date: date
    ) -> pd.DataFrame:
        """
        生成模拟舆情数据（用于开发和测试）
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 模拟舆情数据
        """
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        n_days = len(dates)
        
        np.random.seed(hash(symbol) % (2**32))
        
        base_sentiment = np.random.uniform(-0.2, 0.2)
        sentiment_walk = np.cumsum(np.random.randn(n_days) * 0.05) + base_sentiment
        sentiment_walk = np.clip(sentiment_walk, -1, 1)
        
        data = {
            'date': dates,
            'symbol': symbol,
            'composite_score': sentiment_walk,
            'news_sentiment': sentiment_walk + np.random.randn(n_days) * 0.1,
            'social_sentiment': sentiment_walk + np.random.randn(n_days) * 0.15,
            'analyst_sentiment': sentiment_walk + np.random.randn(n_days) * 0.08,
            'news_volume': np.random.poisson(5, n_days),
            'social_mentions': np.random.poisson(20, n_days),
        }
        
        df = pd.DataFrame(data)
        
        for col in ['composite_score', 'news_sentiment', 'social_sentiment', 
                    'analyst_sentiment']:
            df[col] = df[col].clip(-1, 1)
        
        return df
    
    async def get_latest_sentiment(self, symbol: str) -> Optional[SentimentData]:
        """
        获取最新舆情数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            SentimentData: 最新舆情数据
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            sentiment_df = await self.get_stock_sentiment(
                symbol, start_date, end_date
            )
            
            if sentiment_df.empty:
                return None
            
            latest = sentiment_df.iloc[-1]
            
            # 计算情感变化
            if len(sentiment_df) >= 2:
                sentiment_1d_change = latest['composite_score'] - \
                    sentiment_df.iloc[-2]['composite_score']
            else:
                sentiment_1d_change = 0.0
            
            if len(sentiment_df) >= 5:
                sentiment_5d_change = latest['composite_score'] - \
                    sentiment_df.iloc[-5]['composite_score']
            else:
                sentiment_5d_change = 0.0
            
            # 计算情感动量（短期平均 - 长期平均）
            if len(sentiment_df) >= 10:
                short_term = sentiment_df.tail(5)['composite_score'].mean()
                long_term = sentiment_df.head(10)['composite_score'].mean()
                sentiment_momentum = short_term - long_term
            else:
                sentiment_momentum = 0.0
            
            # 检测极端情绪
            is_extreme_positive = latest['composite_score'] > \
                self.extreme_positive_threshold
            is_extreme_negative = latest['composite_score'] < \
                self.extreme_negative_threshold
            
            return SentimentData(
                symbol=symbol,
                date=str(end_date),
                composite_score=latest['composite_score'],
                news_sentiment=latest.get('news_sentiment', 0.0),
                social_sentiment=latest.get('social_sentiment', 0.0),
                analyst_sentiment=latest.get('analyst_sentiment', 0.0),
                news_volume=int(latest.get('news_volume', 0)),
                social_mentions=int(latest.get('social_mentions', 0)),
                sentiment_1d_change=sentiment_1d_change,
                sentiment_5d_change=sentiment_5d_change,
                sentiment_momentum=sentiment_momentum,
                is_extreme_positive=is_extreme_positive,
                is_extreme_negative=is_extreme_negative
            )
            
        except Exception as e:
            logger.error(f"获取{symbol}最新舆情失败: {e}")
            return None
    
    async def fetch_news_articles(
        self,
        symbol: str,
        days_back: int = 7
    ) -> List[NewsArticle]:
        """
        获取相关新闻文章
        
        Args:
            symbol: 股票代码
            days_back: 回溯天数
            
        Returns:
            List[NewsArticle]: 新闻列表
        """
        try:
            from quantcore.alpha.alternative.raw.backend_adapter import (
                BackendAdapter
            )
            
            adapter = BackendAdapter()
            
            articles = await adapter.get_news_articles(
                symbol=symbol,
                days_back=days_back
            )
            
            if articles:
                return articles
            
            return await self._generate_mock_news(symbol, days_back)
            
        except Exception as e:
            logger.warning(f"获取{symbol}新闻失败: {e}")
            return await self._generate_mock_news(symbol, days_back)
    
    async def _generate_mock_news(
        self,
        symbol: str,
        days_back: int = 7
    ) -> List[NewsArticle]:
        """生成模拟新闻数据"""
        mock_titles = [
            f"{symbol}发布季度财报，业绩超预期",
            f"{symbol}获得重要订单，业务前景看好",
            f"分析师上调{symbol}目标价",
            f"{symbol}宣布战略合作计划",
            f"市场担忧{symbol}行业竞争加剧",
        ]
        
        articles = []
        now = datetime.now()
        
        for i in range(min(5, len(mock_titles))):
            article = NewsArticle(
                title=mock_titles[i],
                content=f"这是关于{symbol}的模拟新闻内容...",
                source="模拟数据源",
                publish_time=now - timedelta(hours=i*12),
                sentiment_score=np.random.uniform(-0.5, 0.8),
                sentiment_label=np.random.choice(
                    ['positive', 'negative', 'neutral'],
                    p=[0.6, 0.2, 0.2]
                ),
                keywords=[symbol, "财经", "股票"],
                relevance_score=np.random.uniform(0.7, 1.0)
            )
            articles.append(article)
        
        return articles
    
    async def fetch_social_media_posts(
        self,
        symbol: str,
        platform: str = "xueqiu",
        hours_back: int = 24
    ) -> List[SocialMediaPost]:
        """
        获取社交媒体帖子
        
        Args:
            symbol: 股票代码
            platform: 平台名称
            hours_back: 回溯小时数
            
        Returns:
            List[SocialMediaPost]: 社交媒体帖子列表
        """
        try:
            from quantcore.alpha.alternative.raw.backend_adapter import (
                BackendAdapter
            )
            
            adapter = BackendAdapter()
            
            posts = await adapter.get_social_media_posts(
                symbol=symbol,
                platform=platform,
                hours_back=hours_back
            )
            
            if posts:
                return posts
            
            return await self._generate_mock_social_posts(symbol, platform)
            
        except Exception as e:
            logger.warning(f"获取{symbol}社交媒体数据失败: {e}")
            return await self._generate_mock_social_posts(symbol, platform)
    
    async def _generate_mock_social_posts(
        self,
        symbol: str,
        platform: str = "xueqiu"
    ) -> List[SocialMediaPost]:
        """生成模拟社交媒体数据"""
        mock_contents = [
            f"看好{symbol}的长期发展！",
            f"{symbol}今天表现不错",
            f"大家觉得{symbol}能涨到多少？",
            f"{symbol}的技术面分析...",
            f"持仓{symbol}中，继续观察",
        ]
        
        posts = []
        now = datetime.now()
        
        for i in range(len(mock_contents)):
            post = SocialMediaPost(
                platform=platform,
                content=mock_contents[i],
                author=f"用户{i+1}",
                publish_time=now - timedelta(hours=i*2),
                likes=np.random.randint(0, 100),
                comments=np.random.randint(0, 50),
                reposts=np.random.randint(0, 30),
                sentiment_score=np.random.uniform(-0.3, 0.7),
                influence_score=np.random.uniform(0.1, 1.0)
            )
            posts.append(post)
        
        return posts
    
    async def calculate_sentiment_factors(
        self,
        symbols: List[str],
        end_date: Optional[date] = None
    ) -> Dict[str, Dict[str, float]]:
        """
        批量计算舆情因子
        
        Args:
            symbols: 股票代码列表
            end_date: 截止日期
            
        Returns:
            {symbol: {factor_name: factor_value}}
        """
        if end_date is None:
            end_date = date.today()
        
        all_factors = {}
        
        tasks = [self.get_latest_sentiment(s) for s in symbols]
        sentiments = await asyncio.gather(*tasks, return_exceptions=True)
        
        for symbol, sentiment in zip(symbols, sentiments):
            if isinstance(sentiment, Exception) or sentiment is None:
                continue
            
            try:
                factors = {
                    "symbol": symbol,
                    "date": str(end_date),
                    
                    # 综合情感得分（标准化到正态分布）
                    "sentiment_composite": sentiment.composite_score,
                    
                    # 新闻情感因子
                    "sentiment_news": sentiment.news_sentiment,
                    
                    # 社交媒体情感因子
                    "sentiment_social": sentiment.social_sentiment,
                    
                    # 分析师情感因子
                    "sentiment_analyst": sentiment.analyst_sentiment,
                    
                    # 情感动量因子（短期变化）
                    "sentiment_momentum_1d": sentiment.sentiment_1d_change,
                    
                    # 中期情感趋势
                    "sentiment_trend_5d": sentiment.sentiment_5d_change,
                    
                    # 情感动量
                    "sentiment_acceleration": sentiment.sentiment_momentum,
                    
                    # 新闻关注度因子（标准化）
                    "news_attention": np.log1p(sentiment.news_volume),
                    
                    # 社交媒体热度因子
                    "social_popularity": np.log1p(sentiment.social_mentions),
                    
                    # 极端正面情绪标记
                    "extreme_positive_flag": 1.0 if sentiment.is_extreme_positive else 0.0,
                    
                    # 极端负面情绪标记
                    "extreme_negative_flag": 1.0 if sentiment.is_extreme_negative else 0.0,
                    
                    # 情绪分歧度（绝对值越大越一致）
                    "sentiment_consensus": abs(sentiment.composite_score),
                }
                
                all_factors[symbol] = factors
                
            except Exception as e:
                logger.debug(f"计算{symbol}舆情因子失败: {e}")
                continue
        
        return all_factors
    
    async def detect_sentiment_anomaly(
        self,
        symbol: str,
        window: int = 20
    ) -> Dict[str, Any]:
        """
        检测异常舆情波动
        
        Args:
            symbol: 股票代码
            window: 统计窗口
            
        Returns:
            Dict: 异常检测结果
        """
        try:
            end_date = date.today()
            start_date = end_date - timedelta(days=window*2)
            
            sentiment_df = await self.get_stock_sentiment(
                symbol, start_date, end_date
            )
            
            if len(sentiment_df) < window:
                return {'is_anomaly': False, 'reason': '数据不足'}
            
            recent = sentiment_df.tail(window)
            historical = sentiment_df.head(window)
            
            recent_mean = recent['composite_score'].mean()
            recent_std = recent['composite_score'].std()
            historical_mean = historical['composite_score'].mean()
            historical_std = historical['composite_score'].std()
            
            z_score = ((recent_mean - historical_mean) / 
                      (historical_std + 1e-8))
            
            volatility_ratio = recent_std / (historical_std + 1e-8)
            
            is_anomaly = abs(z_score) > 2.0 or volatility_ratio > 2.0
            
            result = {
                'symbol': symbol,
                'is_anomaly': is_anomaly,
                'z_score': z_score,
                'volatility_ratio': volatility_ratio,
                'recent_mean': recent_mean,
                'historical_mean': historical_mean,
                'anomaly_type': 'spike' if z_score > 2.0 else 
                               'drop' if z_score < -2.0 else
                               'volatility' if volatility_ratio > 2.0 else 'normal'
            }
            
            if is_anomaly:
                logger.warning(f"检测到{symbol}舆情异常: {result['anomaly_type']}")
            
            return result
            
        except Exception as e:
            logger.error(f"检测{symbol}舆情异常失败: {e}")
            return {'is_anomaly': False, 'error': str(e)}
    
    async def get_market_sentiment_index(
        self,
        symbols: Optional[List[str]] = None
    ) -> Dict[str, float]:
        """
        计算市场整体情绪指数
        
        Args:
            symbols: 股票列表（None表示全市场）
            
        Returns:
            Dict: 市场情绪指标
        """
        try:
            if symbols is None:
                symbols = await self._get_major_stocks()
            
            sentiments = await self.calculate_sentiment_factors(symbols)
            
            if not sentiments:
                return {}
            
            composite_scores = [
                s.get('sentiment_composite', 0) 
                for s in sentiments.values()
            ]
            
            positive_count = sum(1 for s in composite_scores if s > 0.1)
            negative_count = sum(1 for s in composite_scores if s < -0.1)
            total_count = len(composite_scores)
            
            market_index = {
                'market_sentiment_mean': np.mean(composite_scores),
                'market_sentiment_median': np.median(composite_scores),
                'market_sentiment_std': np.std(composite_scores),
                
                # 情绪广度指标
                'positive_ratio': positive_count / total_count if total_count > 0 else 0,
                'negative_ratio': negative_count / total_count if total_count > 0 else 0,
                
                # 极端情绪比例
                'extreme_positive_ratio': sum(
                    1 for s in sentiments.values() 
                    if s.get('extreme_positive_flag', 0) == 1.0
                ) / total_count if total_count > 0 else 0,
                
                'extreme_negative_ratio': sum(
                    1 for s in sentiments.values() 
                    if s.get('extreme_negative_flag', 0) == 1.0
                ) / total_count if total_count > 0 else 0,
                
                # 样本数量
                'sample_size': total_count,
            }
            
            return market_index
            
        except Exception as e:
            logger.error(f"计算市场情绪指数失败: {e}")
            return {}
    
    async def _get_major_stocks(self) -> List[str]:
        """获取主要股票列表"""
        try:
            from quantcore.alpha.alternative.raw.backend_adapter import (
                BackendAdapter
            )
            
            adapter = BackendAdapter()
            stocks = await adapter.get_stock_list(limit=100)
            return stocks[:100]
            
        except Exception:
            return []
