"""
Alternative Data Factor (另类数据因子库) ⭐

现代量化 Alpha 的主力来源：
- 互联网行为因子
- 舆情/NLP 情感因子
- 资金行为因子
- ESG 因子
- 事件驱动因子
- 供应链因子
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class AlternativeFactorConfig:
    """另类数据因子配置"""
    enable_sentiment: bool = True
    enable_fund_flow: bool = True
    enable_event: bool = True
    enable_esg: bool = False
    sentiment_sources: List[str] = None  # ["news", "social", "announcement"]
    fund_flow_types: List[str] = None  # ["main", "northbound", "lhb"]


class AlternativeFactorLibrary:
    """
    另类数据因子库 ⭐
    
    这是现代量化 Alpha 的核心来源，包含：
    
    **1. 情感因子 (Sentiment) - NLP：**
    - SENTIMENT_NEWS: 新闻情感得分
    - SENTIMENT_SOCIAL: 社交媒体情感
    - SENTIMENT_ANNOUNCEMENT: 公告情感
    - ATTENTION: 关注度指数
    
    **2. 资金行为因子 (Fund Flow)：**
    - FUND_FLOW_MAIN: 主力资金净流入
    - FUND_FLOW_NORTHBOUND: 北向资金净流入
    - FUND_FLOW_LHB: 龙虎榜净买入
    - INSTITUTION_SURVEY: 机构调研热度
    
    **3. 事件驱动因子 (Event Driver)：**
    - EVENT_LIMIT_UP: 涨停频率
    - EVENT_LHB_APPEAR: 龙虎榜上榜频率
    - EVENT_INSTITUTION_RECOMMEND: 机构推荐强度
    - EVENT_SHAREHOLDER_CHANGE: 股东增减持
    
    **4. ESG 因子：**
    - ESG_ENVIRONMENTAL: 环境评分
    - ESG_SOCIAL: 社会责任评分
    - ESG_GOVERNANCE: 公司治理评分
    
    **5. 供应链因子 (Supply Chain)：**
    - SUPPLY_CHAIN_ACTIVITY: 供应链活跃度
    - SUPPLY_CHAIN_RISK: 供应链风险
    
    数据来源：
    - Backend 数据适配器（龙虎榜、资金流向、股东数据）
    - NLP 模型（新闻、公告、社交媒体）
    - 外部 API（百度指数、ESG 数据等）
    """
    
    def __init__(self, config: Optional[AlternativeFactorConfig] = None):
        self.config = config or AlternativeFactorConfig()
        
        if self.config.sentiment_sources is None:
            self.config.sentiment_sources = ["news"]
        if self.config.fund_flow_types is None:
            self.config.fund_flow_types = ["main", "northbound", "lhb"]
        
        # NLP 分析器缓存
        self._sentiment_analyzer = None
    
    def calculate_all(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有可用的另类数据因子
        
        Args:
            data: 包含另类数据的 DataFrame
            
        Returns:
            DataFrame: 所有另类数据因子
        """
        results = {}
        
        if self.config.enable_sentiment:
            results.update(self.calculate_sentiment(data))
        
        if self.config.enable_fund_flow:
            results.update(self.calculate_fund_flow(data))
        
        if self.config.enable_event:
            results.update(self.calculate_event_driver(data))
        
        if self.config.enable_esg:
            results.update(self.calculate_esg(data))
        
        return pd.DataFrame(results)
    
    def calculate_sentiment(
        self,
        data: pd.DataFrame,
        sources: List[str] = None
    ) -> Dict[str, pd.Series]:
        """
        计算情感因子
        
        使用 NLP 分析文本数据的情感倾向。
        
        Args:
            data: 包含文本或预计算情感的 DataFrame
            sources: 数据源列表
            
        Returns:
            {factor_name: Series}
        """
        sources = sources or self.config.sentiment_sources
        factors = {}
        
        for source in sources:
            col_name = f"sentiment_{source}"
            
            if col_name in data.columns:
                # 使用预计算的情感分数
                scores = data[col_name]
                std = scores.std() if scores.std() > 0 else 1
                normalized = (scores - scores.mean()) / std
                
                name = f"SENTIMENT_{source.upper()}"
                factors[name] = normalized.dropna()
                
                # 综合情感因子
                if len(factors) == 1:
                    factors["SENTIMENT"] = normalized.dropna()
            
            elif 'text' in data.columns and source == "news":
                # 实时计算情感
                try:
                    from quantcore.alpha.alternative.nlp.sentiment_analyzer import SentimentAnalyzer
                    
                    if self._sentiment_analyzer is None:
                        self._sentiment_analyzer = SentimentAnalyzer()
                    
                    scores = self._sentiment_analyzer.batch_analyze(data['text'].tolist())
                    score_series = pd.Series(scores, index=data.index)
                    
                    std = score_series.std() if score_series.std() > 0 else 1
                    normalized = (score_series - score_series.mean()) / std
                    
                    factors["SENTIMENT_NEWS"] = normalized.dropna()
                    factors["SENTIMENT"] = normalized.dropna()
                    
                except ImportError:
                    logger.warning("NLP 模块不可用")
                    factors["SENTIMENT_NEWS"] = self._rule_based_sentiment(data.get('text', pd.Series()))
        
        return factors
    
    def _rule_based_sentiment(self, texts: pd.Series) -> pd.Series:
        """基于规则的情感分析（fallback）"""
        positive_words = [
            '增长', '盈利', '利好', '上涨', '突破', '创新高',
            '增持', '推荐', '买入', '超预期', '大幅提升',
            '扭亏为盈', '业绩亮眼', '前景广阔', '强势'
        ]
        
        negative_words = [
            '下降', '亏损', '利空', '下跌', '跌破', '创新低',
            '减持', '卖出', '低于预期', '大幅下滑',
            '业绩暴雷', '风险', '预警', '回调', '疲软'
        ]
        
        scores = []
        for text in texts:
            text_str = str(text).lower() if text is not None else ""
            pos_count = sum(1 for w in positive_words if w in text_str)
            neg_count = sum(1 for w in negative_words if w in text_str)
            total = pos_count + neg_count
            
            if total > 0:
                score = (pos_count - neg_count) / total
            else:
                score = 0.0
            
            scores.append(score)
        
        result = pd.Series(scores, index=texts.index)
        std = result.std() if result.std() > 0 else 1
        return ((result - result.mean()) / std).dropna()
    
    def calculate_fund_flow(
        self,
        data: pd.DataFrame,
        flow_types: List[str] = None
    ) -> Dict[str, pd.Series]:
        """
        计算资金行为因子
        
        基于 Backend 已有的资金流向数据：
        - main_net_inflow: 主力净流入
        - northbound_net: 北向资金
        - lhb_net_buy: 龙虎榜净买入
        
        Args:
            data: 包含资金流向的 DataFrame
            flow_types: 资金类型列表
            
        Returns:
            {factor_name: Series}
        """
        flow_types = flow_types or self.config.fund_flow_types
        factors = {}
        
        type_col_map = {
            "main": ("main_net_inflow", "FUND_FLOW_MAIN"),
            "northbound": ("northbound_net", "FUND_FLOW_NORTHBOUND"),
            "lhb": ("lhb_net_buy", "FUND_FLOW_LHB"),
            "super_large": ("super_large_order_net", "FUND_FLOW_SUPER_LARGE"),
            "large": ("large_order_net", "FUND_FLOW_LARGE"),
        }
        
        for ftype in flow_types:
            col_name, factor_name = type_col_map.get(ftype, (None, None))
            
            if col_name and col_name in data.columns:
                values = data[col_name]
                std = values.std() if values.std() > 0 else 1
                normalized = (values - values.mean()) / std
                factors[factor_name] = normalized.dropna()
        
        # 综合资金流向因子
        fund_factors = [k for k in factors.keys() if k.startswith("FUND_FLOW_")]
        if len(fund_factors) > 1:
            combined = pd.DataFrame(factors)[fund_factors].mean(axis=1)
            factors["FUND_FLOW"] = combined.dropna()
        elif len(fund_factors) == 1:
            factors["FUND_FLOW"] = factors[fund_factors[0]]
        
        return factors
    
    def calculate_event_driver(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算事件驱动因子
        
        基于 Backend 已有的事件数据：
        - is_limit_up: 是否涨停
        - in_lhb: 是否在龙虎榜
        - recommend_count: 机构推荐次数
        - avg_rating: 平均评级
        - shareholder_change: 股东增减持
        
        Args:
            data: 包含事件数据的 DataFrame
            
        Returns:
            {factor_name: Series}
        """
        factors = {}
        
        # 涨停频率因子
        if 'is_limit_up' in data.columns:
            limit_freq = data['is_limit_up'].rolling(20).sum()
            std = limit_freq.std() if limit_freq.std() > 0 else 1
            factors["EVENT_LIMIT_UP"] = ((limit_freq - limit_freq.mean()) / std).dropna()
        
        # 龙虎榜出现频率
        if 'in_lhb' in data.columns:
            lhb_freq = data['in_lhb'].rolling(60).sum()
            std = lhb_freq.std() if lhb_freq.std() > 0 else 1
            factors["EVENT_LHB_APPEAR"] = ((lhb_freq - lhb_freq.mean()) / std).dropna()
        
        # 机构推荐因子
        if 'recommend_count' in data.columns and 'avg_rating' in data.columns:
            rec_score = data['recommend_count'] * data['avg_rating']
            std = rec_score.std() if rec_score.std() > 0 else 1
            factors["EVENT_INSTITUTION_RECOMMEND"] = ((rec_score - rec_score.mean()) / std).dropna()
        
        # 股东增减持因子
        if 'shareholder_change' in data.columns:
            change = data['shareholder_change']
            std = change.std() if change.std() > 0 else 1
            factors["EVENT_SHAREHOLDER_CHANGE"] = ((change - change.mean()) / std).dropna()
        
        # 回购因子（回购=利好）
        if 'repurchase_amount' in data.columns:
            repurchase = data['repurchase_amount']
            std = repurchase.std() if repurchase.std() > 0 else 1
            factors["EVENT_REPURCHASE"] = ((repurchase - repurchase.mean()) / std).dropna()
        
        return factors
    
    def calculate_esg(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算 ESG 因子
        
        需要外部 ESG 数据源。
        
        Args:
            data: 包含 ESG 数据的 DataFrame
            
        Returns:
            {factor_name: Series}
        """
        factors = {}
        
        esg_fields = [
            ('esg_environmental', 'ESG_ENVIRONMENTAL'),
            ('esg_social', 'ESG_SOCIAL'),
            ('esg_governance', 'ESG_GOVERNANCE'),
            ('esg_total', 'ESG_TOTAL'),
        ]
        
        for field, factor_name in esg_fields:
            if field in data.columns:
                values = data[field]
                std = values.std() if values.std() > 0 else 1
                factors[factor_name] = ((values - values.mean()) / std).dropna()
        
        # 综合 ESG 因子
        esg_factors = [k for k in factors.keys() if k.startswith("ESG_") and k != "ESG_TOTAL"]
        if len(esg_factors) > 1:
            combined = pd.DataFrame(factors)[esg_factors].mean(axis=1)
            factors["ESG_COMPOSITE"] = combined.dropna()
        
        return factors
    
    def calculate_attention(self, data: pd.DataFrame) -> pd.Series:
        """
        计算关注度因子
        
        基于搜索量、讨论量、点击量等指标。
        
        Args:
            data: 包含关注度数据的 DataFrame
            
        Returns:
            Series: 标准化的关注度因子
        """
        attention_cols = ['search_index', 'discussion_volume', 'click_count']
        
        attention_scores = []
        for col in attention_cols:
            if col in data.columns:
                values = data[col]
                std = values.std() if values.std() > 0 else 1
                z_score = (values - values.mean()) / std
                attention_scores.append(z_score.dropna())
        
        if attention_scores:
            combined = pd.concat(attention_scores, axis=1).mean(axis=1)
            std = combined.std() if combined.std() > 0 else 1
            return ((combined - combined.mean()) / std).dropna()
        
        return pd.Series()
    
    def list_available_factors(self) -> List[Dict[str, str]]:
        """列出所有可用的另类数据因子"""
        factors = [
            {"name": "SENTIMENT", "category": "sentiment", "description": "综合情感因子"},
            {"name": "SENTIMENT_NEWS", "category": "sentiment", "description": "新闻情感"},
            {"name": "SENTIMENT_SOCIAL", "category": "sentiment", "description": "社交媒体情感"},
            {"name": "FUND_FLOW", "category": "fund_flow", "description": "综合资金流向"},
            {"name": "FUND_FLOW_MAIN", "category": "fund_flow", "description": "主力资金净流入"},
            {"name": "FUND_FLOW_NORTHBOUND", "category": "fund_flow", "description": "北向资金净流入"},
            {"name": "FUND_FLOW_LHB", "category": "fund_flow", "description": "龙虎榜净买入"},
            {"name": "EVENT_LIMIT_UP", "category": "event", "description": "涨停频率"},
            {"name": "EVENT_LHB_APPEAR", "category": "event", "description": "龙虎榜出现频率"},
            {"name": "EVENT_INSTITUTION_RECOMMEND", "category": "event", "description": "机构推荐强度"},
            {"name": "ATTENTION", "category": "attention", "description": "关注度因子"},
            {"name": "ESG_TOTAL", "category": "esg", "description": "综合ESG评分"},
        ]
        
        return factors
