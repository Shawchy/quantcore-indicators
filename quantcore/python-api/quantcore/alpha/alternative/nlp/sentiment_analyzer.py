"""
NLP 情感分析器

使用 BERT 或规则方法进行中文金融文本情感分析。
"""

from typing import List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class SentimentResult:
    """情感分析结果"""
    text: str
    label: str  # positive/negative/neutral
    score: float  # 置信度 [0, 1]
    positive_prob: float  # 正面概率
    negative_prob: float  # 负面概率
    neutral_prob: float  # 中性概率


class SentimentAnalyzer:
    """
    金融文本情感分析器
    
    支持：
    - BERT 模型情感分类（高精度）
    - 规则方法（快速 fallback）
    
    使用示例：
        analyzer = SentimentAnalyzer()
        
        # 分析单条文本
        result = analyzer.analyze("公司业绩大幅增长，超出市场预期")
        print(result.label, result.score)
        
        # 批量分析
        scores = analyzer.batch_analyze(["利好消息", "利空消息"])
        print(scores)  # [正分, 负分]
    """
    
    # 中文金融情感词库
    POSITIVE_WORDS = [
        # 增长类
        '增长', '盈利', '利好', '上涨', '突破', '创新高',
        '增持', '推荐', '买入', '超预期', '大幅提升',
        '扭亏为盈', '业绩亮眼', '前景广阔', '强势', '领跑',
        '攀升', '飙升', '暴涨', '反弹', '回升',
        
        # 质量类
        '优质', '稳健', '龙头', '核心', '领先', '优势',
        '竞争力', '护城河', '品牌价值', '市场份额', '垄断',
        
        # 事件类
        '回购', '分红', '送转', '并购', '合作', '签约',
        '中标', '获批', '认证', '获奖', '评级上调',
    ]
    
    NEGATIVE_WORDS = [
        # 下降类
        '下降', '亏损', '利空', '下跌', '跌破', '创新低',
        '减持', '卖出', '低于预期', '大幅下滑',
        '业绩暴雷', '风险', '预警', '回调', '疲软',
        '暴跌', '跳水', '崩盘', '阴跌', '低迷',
        
        # 风险类
        '债务', '违约', '诉讼', '处罚', '调查', '退市',
        'ST', '*ST', '暂停上市', '破产', '重组',
        
        # 事件类
        '解禁', '减持', '质押', '冻结', '立案', '问询',
        '监管', '约谈', '通报', '整改', '下架',
    ]
    
    # 强度修饰词
    INTENSIFIERS = {
        '非常': 1.5, '极其': 2.0, '特别': 1.5,
        '大幅': 1.5, '显著': 1.3, '明显': 1.2,
        '略': 0.7, '稍微': 0.6, '小幅': 0.7,
        '可能': 0.8, '或许': 0.8,
    }
    
    def __init__(self, model_name: str = None):
        """
        初始化情感分析器
        
        Args:
            model_name: BERT 模型名称（None=规则方法）
        """
        self.model_name = model_name
        self._model = None
        self._tokenizer = None
        self._use_rule_based = True
        
        if model_name:
            try:
                from transformers import AutoTokenizer, AutoModelForSequenceClassification
                import torch
                
                logger.info(f"加载 BERT 情感模型: {model_name}")
                self._tokenizer = AutoTokenizer.from_pretrained(model_name)
                self._model = AutoModelForSequenceClassification.from_pretrained(
                    model_name, num_labels=3
                )
                self._model.eval()
                self._use_rule_based = False
                logger.info("BERT 模型加载完成")
                
            except ImportError:
                logger.warning("transformers 未安装，使用规则方法")
            except Exception as e:
                logger.error(f"模型加载失败: {e}，使用规则方法")
    
    def analyze(self, text: str) -> SentimentResult:
        """
        分析单条文本情感
        
        Args:
            text: 输入文本
            
        Returns:
            SentimentResult: 情感分析结果
        """
        if not text or len(text.strip()) == 0:
            return SentimentResult(
                text=text or "", label="neutral", score=0.5,
                positive_prob=0.33, negative_prob=0.33, neutral_prob=0.34
            )
        
        if not self._use_rule_based and self._model is not None:
            return self._bert_analyze(text)
        else:
            return self._rule_based_analyze(text)
    
    def _bert_analyze(self, text: str) -> SentimentResult:
        """BERT 模型分析"""
        import torch
        
        inputs = self._tokenizer(
            text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        with torch.no_grad():
            outputs = self._model(**inputs)
            probs = torch.softmax(outputs.logits, dim=-1)[0]
        
        labels = ["negative", "neutral", "positive"]
        pred_label = labels[probs.argmax().item()]
        
        return SentimentResult(
            text=text,
            label=pred_label,
            score=float(probs.max()),
            positive_prob=float(probs[2]),
            negative_prob=float(probs[0]),
            neutral_prob=float(probs[1])
        )
    
    def _rule_based_analyze(self, text: str) -> SentimentResult:
        """基于规则的情感分析"""
        text_lower = text.lower()
        
        pos_count = 0
        neg_count = 0
        
        # 统计正面词汇
        for word in self.POSITIVE_WORDS:
            if word in text_lower:
                intensity = self._get_intensity(text_lower, word)
                pos_count += intensity
        
        # 统计负面词汇
        for word in self.NEGATIVE_WORDS:
            if word in text_lower:
                intensity = self._get_intensity(text_lower, word)
                neg_count += intensity
        
        total = pos_count + neg_count
        
        if total == 0:
            return SentimentResult(
                text=text, label="neutral", score=0.5,
                positive_prob=0.33, negative_prob=0.33, neutral_prob=0.34
            )
        
        pos_prob = pos_count / total
        neg_prob = neg_count / total
        neu_prob = max(0, 1 - pos_prob - neg_prob) / 2
        
        if pos_prob > neg_prob:
            label = "positive"
            score = pos_prob
        elif neg_prob > pos_prob:
            label = "negative"
            score = neg_prob
        else:
            label = "neutral"
            score = 0.5
        
        return SentimentResult(
            text=text,
            label=label,
            score=score,
            positive_prob=pos_prob,
            negative_prob=neg_prob,
            neutral_prob=neu_prob
        )
    
    def _get_intensity(self, text: str, target_word: str) -> float:
        """获取词语的强度修饰"""
        idx = text.find(target_word)
        if idx == -1:
            return 1.0
        
        # 检查前面的修饰词
        prefix = text[max(0, idx-10):idx]
        
        for word, multiplier in self.INTENSIFIERS.items():
            if word in prefix:
                return multiplier
        
        return 1.0
    
    def batch_analyze(self, texts: List[str]) -> List[float]:
        """
        批量分析文本，返回情感得分
        
        Args:
            texts: 文本列表
            
        Returns:
            List[float]: 情感得分 (-1 到 1，正值=正面)
        """
        scores = []
        
        for text in texts:
            result = self.analyze(text)
            score = result.positive_prob - result.negative_prob
            scores.append(score)
        
        return scores
    
    def analyze_dataframe(
        self,
        df: pd.DataFrame,
        text_column: str = "text",
        output_column: str = "sentiment_score"
    ) -> pd.DataFrame:
        """
        对 DataFrame 进行批量情感分析
        
        Args:
            df: 输入 DataFrame
            text_column: 文本列名
            output_column: 输出列名
            
        Returns:
            DataFrame: 添加了情感分数的新 DataFrame
        """
        texts = df[text_column].fillna("").tolist()
        scores = self.batch_analyze(texts)
        
        df = df.copy()
        df[output_column] = scores
        
        return df
    
    def get_sentiment_distribution(self, texts: List[str]) -> Dict[str, int]:
        """
        获取情感分布统计
        
        Args:
            texts: 文本列表
            
        Returns:
            Dict: {label: count}
        """
        distribution = {"positive": 0, "negative": 0, "neutral": 0}
        
        for text in texts:
            result = self.analyze(text)
            distribution[result.label] += 1
        
        return distribution
