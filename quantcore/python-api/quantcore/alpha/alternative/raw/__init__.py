"""
另类数据原始采集模块

提供非传统金融数据的原始数据采集能力：
- 后端数据适配器
- 资金流向爬虫
- 舆情/情感爬虫
- ESG 数据爬虫
"""

from .backend_adapter import BackendAdapter, BackendConfig
from .fund_flow_crawler import FundFlowCrawler, FundFlowData
from .sentiment_crawler import SentimentCrawler, SentimentData
from .esg_crawler import ESGCrawler, ESGScore

__all__ = [
    "BackendAdapter",
    "BackendConfig",
    "FundFlowCrawler",
    "FundFlowData",
    "SentimentCrawler", 
    "SentimentData",
    "ESGCrawler",
    "ESGScore",
]
