"""
NLP 模块

提供自然语言处理功能：
- SentimentAnalyzer: 情感分析
- TextEmbedder: 文本向量化
"""

from .sentiment_analyzer import SentimentAnalyzer, SentimentResult

__all__ = [
    "SentimentAnalyzer",
    "SentimentResult",
]
