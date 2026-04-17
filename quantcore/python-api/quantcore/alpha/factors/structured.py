"""
Alternative Structure Factor (结构化另类因子库) ⭐

使用非传统方法构建的因子：
- 文本 Embedding 因子
- 知识图谱关联因子
- 时序预测残差因子
- 高频 Microstructure 因子
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class StructuredFactorConfig:
    """结构化因子配置"""
    enable_text_embedding: bool = False  # 需要 BERT/GPT 模型
    enable_knowledge_graph: bool = False  # 需要 Neo4j
    enable_time_series_residual: bool = True
    enable_microstructure: bool = False  # 需要高频数据


class StructuredFactorLibrary:
    """
    结构化另类因子库 ⭐
    
    使用 AI/ML/图等非传统方法构建的因子：
    
    **1. 文本 Embedding 因子：**
    - TEXT_EMBEDDING_NEWS: 新闻文本向量降维
    - TEXT_EMBEDDING_REPORT: 研报摘要向量
    
    **2. 知识图谱因子：**
    - GRAPH_INDUSTRY_CENTRALITY: 行业中心度
    - GRAPH_SUPPLY_CHAIN_RISK: 供应链风险
    
    **3. 时序残差因子：**
    - TS_RESIDUAL_MA: 均线回归残差
    - TS_RESIDUAL_TREND: 趋势残差
    - TS_RESIDUAL_SEASONAL: 季节性残差
    
    **4. 高频 Microstructure 因子：**
    - MICRO_ORDER_IMBALANCE: 订单不平衡
    - MICRO_BID_ASK_SPREAD: 买卖价差
    """
    
    def __init__(self, config: Optional[StructuredFactorConfig] = None):
        self.config = config or StructuredFactorConfig()
    
    def calculate_all(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算所有可用的结构化因子"""
        results = {}
        
        if self.config.enable_time_series_residual:
            results.update(self.calculate_time_series_residual(data))
        
        return pd.DataFrame(results)
    
    def calculate_time_series_residual(
        self,
        data: pd.DataFrame,
        method: str = "ma"
    ) -> Dict[str, pd.Series]:
        """
        计算时序残差因子
        
        原理：价格偏离趋势的程度，残差大=异常=可能有Alpha机会。
        
        Args:
            data: 价格数据
            method: 残差计算方法 (ma/trend/seasonal)
            
        Returns:
            {factor_name: Series}
        """
        factors = {}
        close = data['close']
        
        if method in ["ma", "all"]:
            # MA 回归残差
            ma20 = close.rolling(20).mean()
            residual_ma = (close - ma20) / ma20.replace(0, np.nan)
            
            std = residual_ma.std() if residual_ma.std() > 0 else 1
            factors["TS_RESIDUAL_MA"] = ((residual_ma - residual_ma.mean()) / std).dropna()
            
            # MA60 回归残差
            ma60 = close.rolling(60).mean()
            residual_ma60 = (close - ma60) / ma60.replace(0, np.nan)
            
            std = residual_ma60.std() if residual_ma60.std() > 0 else 1
            factors["TS_RESIDUAL_MA60"] = ((residual_ma60 - residual_ma60.mean()) / std).dropna()
        
        if method in ["trend", "all"]:
            # 线性趋势残差（20日）
            def calc_trend_residual(series, window=20):
                residuals = []
                for i in range(window, len(series)):
                    y = series.iloc[i-window:i+1].values
                    x = np.arange(window)
                    beta = np.polyfit(x, y, 1)
                    trend = beta[0] * x + beta[1]
                    residual = y[-1] - trend[-1]
                    residuals.append(residual)
                return pd.Series(residuals, index=series.index[window:])
            
            trend_resid = calc_trend_residual(close, 20)
            std = trend_resid.std() if len(trend_resid) > 0 and trend_resid.std() > 0 else 1
            
            if len(trend_resid) > 0:
                factors["TS_RESIDUAL_TREND"] = ((trend_resid - trend_resid.mean()) / std).dropna()
        
        if method in ["seasonal", "all"]:
            # 日内季节性残差（如果有多日数据）
            returns = close.pct_change()
            
            # 计算同时段历史均值
            hour_returns = returns.groupby(returns.index.hour).transform('mean')
            seasonal_residual = returns - hour_returns
            
            std = seasonal_residual.std() if seasonal_residual.std() > 0 else 1
            factors["TS_RESIDUAL_SEASONAL"] = ((seasonal_residual - seasonal_residual.mean()) / std).dropna()
        
        return factors
    
    def calculate_text_embedding(self, texts: List[str]) -> Optional[pd.Series]:
        """
        计算文本 Embedding 因子（需要模型支持）
        
        使用 BERT/GPT 将文本转换为向量，然后降维得到因子值。
        
        Args:
            texts: 文本列表
            
        Returns:
            Series: Embedding 因子值
        """
        try:
            from sentence_transformers import SentenceTransformer
            
            model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
            embeddings = model.encode(texts)
            
            # 取第一主成分作为因子
            from sklearn.decomposition import PCA
            pca = PCA(n_components=1)
            factor_values = pca.fit_transform(embeddings).flatten()
            
            result = pd.Series(factor_values)
            std = result.std() if result.std() > 0 else 1
            return ((result - result.mean()) / std)
            
        except ImportError:
            logger.warning("sentence-transformers 未安装，无法计算文本Embedding")
            return None
    
    def list_available_factors(self) -> List[Dict[str, str]]:
        """列出所有可用的结构化因子"""
        factors = [
            {"name": "TS_RESIDUAL_MA", "category": "time_series", "description": "均线回归残差"},
            {"name": "TS_RESIDUAL_MA60", "category": "time_series", "description": "60日均线残差"},
            {"name": "TS_RESIDUAL_TREND", "category": "time_series", "description": "线性趋势残差"},
            {"name": "TEXT_EMBEDDING_NEWS", "category": "text_embedding", "description": "新闻文本Embedding"},
            {"name": "GRAPH_INDUSTRY_CENTRALITY", "category": "knowledge_graph", "description": "行业中心度"},
        ]
        
        return factors
