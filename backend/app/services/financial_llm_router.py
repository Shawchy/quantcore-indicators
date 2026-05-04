"""
金融领域双模型路由服务
根据任务类型自动选择合适的金融专用大模型
"""

from typing import Dict, Any, Optional, List
from enum import Enum
import asyncio
import logging
import time

logger = logging.getLogger(__name__)


class TaskType(Enum):
    """任务类型枚举"""
    NUMERICAL_ANALYSIS = "numerical_analysis"  # 数值分析
    SENTIMENT_ANALYSIS = "sentiment_analysis"  # 情感分析
    STRATEGY_GENERATION = "strategy_generation"  # 策略生成
    REPORT_SUMMARIZATION = "report_summarization"  # 研报摘要
    CODE_GENERATION = "code_generation"  # 代码生成
    GENERAL_QUERY = "general_query"  # 通用查询


class ModelType(Enum):
    """模型类型枚举"""
    NUMERICAL_MODEL = "qwen3-8b-financial-numerical"
    SENTIMENT_MODEL = "finsenti-qwen3.5-9b"


class FinancialLLMRouter:
    """
    金融 LLM 路由服务
    根据任务类型自动选择最优模型
    """
    
    def __init__(self):
        self.numerical_model_name = "qwen3:8b-financial"
        self.sentiment_model_name = "finsenti-qwen3.5:9b"
        self._task_model_mapping = self._setup_task_mapping()
    
    def _setup_task_mapping(self) -> Dict[TaskType, ModelType]:
        """设置任务 - 模型映射关系"""
        return {
            TaskType.NUMERICAL_ANALYSIS: ModelType.NUMERICAL_MODEL,
            TaskType.STRATEGY_GENERATION: ModelType.NUMERICAL_MODEL,
            TaskType.CODE_GENERATION: ModelType.NUMERICAL_MODEL,
            TaskType.SENTIMENT_ANALYSIS: ModelType.SENTIMENT_MODEL,
            TaskType.REPORT_SUMMARIZATION: ModelType.SENTIMENT_MODEL,
            TaskType.GENERAL_QUERY: ModelType.NUMERICAL_MODEL,
        }
    
    def _classify_task(self, query: str, context: Optional[Dict] = None) -> TaskType:
        """
        根据查询内容分类任务类型
        
        Args:
            query: 用户查询
            context: 额外上下文信息
        
        Returns:
            TaskType: 任务类型
        """
        query_lower = query.lower()
        
        # 数值分析关键词
        numerical_keywords = [
            "计算", "数值", "指标", "回测", "量化",
            "calculate", "numerical", "indicator", "backtest"
        ]
        
        # 情感分析关键词
        sentiment_keywords = [
            "情感", "情绪", "舆情", "新闻", "研报",
            "sentiment", "emotion", "news", "report"
        ]
        
        # 策略生成关键词
        strategy_keywords = [
            "策略", "交易", "买入", "卖出", "持仓",
            "strategy", "trading", "buy", "sell"
        ]
        
        # 代码生成关键词
        code_keywords = [
            "代码", "实现", "函数", "python", "backtrader",
            "code", "implement", "function"
        ]
        
        # 检测关键词
        if any(kw in query_lower for kw in sentiment_keywords):
            return TaskType.SENTIMENT_ANALYSIS
        
        if any(kw in query_lower for kw in code_keywords):
            return TaskType.CODE_GENERATION
        
        if any(kw in query_lower for kw in strategy_keywords):
            return TaskType.STRATEGY_GENERATION
        
        if any(kw in query_lower for kw in numerical_keywords):
            return TaskType.NUMERICAL_ANALYSIS
        
        return TaskType.GENERAL_QUERY
    
    def select_model(self, task_type: TaskType) -> str:
        """
        根据任务类型选择模型
        
        Args:
            task_type: 任务类型
        
        Returns:
            str: 模型名称
        """
        model_type = self._task_model_mapping.get(
            task_type, 
            ModelType.NUMERICAL_MODEL
        )
        
        if model_type == ModelType.NUMERICAL_MODEL:
            return self.numerical_model_name
        else:
            return self.sentiment_model_name
    
    async def route_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        stock_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        路由查询到合适的模型并执行
        
        Args:
            query: 用户查询
            context: 上下文信息
            stock_data: 股票数据
        
        Returns:
            Dict: 模型响应
        """
        # 分类任务
        task_type = self._classify_task(query, context)
        
        # 选择模型
        model_name = self.select_model(task_type)
        
        # 执行查询（实际实现需要调用对应的模型服务）
        result = await self._execute_query(
            model_name=model_name,
            task_type=task_type,
            query=query,
            context=context,
            stock_data=stock_data
        )
        
        return {
            "task_type": task_type.value,
            "model_used": model_name,
            "response": result,
            "confidence": self._calculate_confidence(task_type, context)
        }
    
    async def _execute_query(
        self,
        model_name: str,
        task_type: TaskType,
        query: str,
        context: Optional[Dict] = None,
        stock_data: Optional[Dict] = None
    ) -> Any:
        """
        执行查询（集成到 qwen_assistant.py）
        
        实际调用时通过 QwenAssistant 服务执行模型推理
        """
        max_retries = 2
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                from app.services.qwen_assistant import get_assistant
                assistant = get_assistant()
                
                # 根据任务类型调用不同的助手方法
                if task_type == TaskType.SENTIMENT_ANALYSIS:
                    result = await assistant.analyze_sentiment(
                        text=query,
                        symbol=context.get("symbol") if context else None
                    )
                    return result.content
                elif task_type == TaskType.STRATEGY_GENERATION:
                    result = await assistant.generate_strategy(
                        description=query,
                        strategy_type="technical",
                        symbols=context.get("symbols") if context else None
                    )
                    return result.content
                elif task_type == TaskType.CODE_GENERATION:
                    result = await assistant.explain_code(code=query)
                    return result.content
                else:
                    result = await assistant.query_stock(
                        symbol=context.get("symbol", "unknown") if context else "unknown",
                        question=query,
                        market_data=stock_data
                    )
                    return result.content
            except Exception as e:
                last_error = e
                logger.error(f"LLM 调用失败 (尝试 {attempt + 1}/{max_retries + 1}): 模型={model_name}, 任务={task_type.value}, 错误={e}")
                
                # 如果不是最后一次尝试，等待后重试
                if attempt < max_retries:
                    wait_time = 2 ** (attempt + 1)
                    logger.info(f"等待 {wait_time} 秒后重试...")
                    await asyncio.sleep(wait_time)
                    continue
        
        # 所有重试均失败
        error_detail = {
            "error_code": "model_service_unavailable",
            "message": "模型服务暂时不可用，请稍后重试",
            "model_name": model_name,
            "task_type": task_type.value,
            "error": str(last_error),
            "timestamp": time.time(),
            "retries_exhausted": True
        }
        logger.error(f"LLM 调用最终失败: {error_detail}")
        return error_detail
    
    def _calculate_confidence(
        self, 
        task_type: TaskType, 
        context: Optional[Dict] = None
    ) -> float:
        """
        计算任务分类置信度
        
        Args:
            task_type: 任务类型
            context: 上下文
        
        Returns:
            float: 置信度 (0-1)
        """
        base_confidence = {
            TaskType.NUMERICAL_ANALYSIS: 0.85,
            TaskType.SENTIMENT_ANALYSIS: 0.90,
            TaskType.STRATEGY_GENERATION: 0.80,
            TaskType.REPORT_SUMMARIZATION: 0.88,
            TaskType.CODE_GENERATION: 0.82,
            TaskType.GENERAL_QUERY: 0.75
        }
        
        return base_confidence.get(task_type, 0.75)
    
    def get_model_recommendation(self, use_case: str) -> Dict[str, Any]:
        """
        根据使用场景推荐模型
        
        Args:
            use_case: 使用场景描述
        
        Returns:
            Dict: 推荐信息
        """
        recommendations = {
            "quantitative_trading": {
                "primary_model": self.numerical_model_name,
                "reason": "数值计算和策略回测能力强",
                "quantization": "Q5_K_M",
                "vram_requirement": "~6GB"
            },
            "sentiment_monitoring": {
                "primary_model": self.sentiment_model_name,
                "reason": "金融情感分析专用优化",
                "quantization": "Q4_K_M",
                "vram_requirement": "~6GB"
            },
            "research_analysis": {
                "primary_model": self.sentiment_model_name,
                "reason": "支持长文本和图表理解",
                "quantization": "Q5_K_M",
                "vram_requirement": "~7GB"
            },
            "realtime_analysis": {
                "primary_model": self.numerical_model_name,
                "reason": "推理速度快，延迟低",
                "quantization": "Q4_K_M",
                "vram_requirement": "~5GB"
            }
        }
        
        return recommendations.get(
            use_case,
            recommendations["quantitative_trading"]
        )


class DualModelService:
    """
    双模型并行服务
    同时使用两个模型进行综合分析
    """
    
    def __init__(self):
        self.router = FinancialLLMRouter()
    
    async def comprehensive_analysis(
        self,
        stock_symbol: str,
        query: str,
        market_data: Dict[str, Any],
        news_data: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        综合分析：同时使用数值模型和情感模型
        
        Args:
            stock_symbol: 股票代码
            query: 用户查询
            market_data: 市场数据
            news_data: 新闻数据
        
        Returns:
            Dict: 综合分析结果
        """
        # 并行执行两个模型的分析
        numerical_task = self.router.route_query(
            query=f"分析{stock_symbol}的技术指标和量化信号：{query}",
            context={"symbol": stock_symbol, "data": market_data},
            stock_data=market_data
        )
        
        sentiment_task = self.router.route_query(
            query=f"分析{stock_symbol}的市场情绪和舆情：{' '.join(news_data or [])}",
            context={"symbol": stock_symbol, "news": news_data}
        )
        
        # 等待两个模型完成
        numerical_result, sentiment_result = await asyncio.gather(
            numerical_task,
            sentiment_task,
            return_exceptions=True
        )
        
        # 整合结果
        return {
            "symbol": stock_symbol,
            "numerical_analysis": numerical_result if not isinstance(numerical_result, Exception) else None,
            "sentiment_analysis": sentiment_result if not isinstance(sentiment_result, Exception) else None,
            "combined_signal": self._combine_signals(
                numerical_result,
                sentiment_result
            )
        }
    
    def _combine_signals(
        self,
        numerical: Dict,
        sentiment: Dict
    ) -> Dict[str, Any]:
        """
        综合两个模型的信号
        
        融合逻辑:
        1. 数值信号权重 60%（技术指标更客观）
        2. 情感信号权重 40%（市场情绪辅助）
        3. 综合判断生成最终信号
        """
        signal_scores = {"bullish": 0, "neutral": 0, "bearish": 0}
        factors = []
        
        # 解析数值模型信号
        if numerical and not isinstance(numerical, Exception):
            num_confidence = numerical.get("confidence", 0.5)
            num_response = numerical.get("response", "")
            
            # 从响应中提取信号倾向
            if any(kw in num_response.lower() for kw in ["买入", "看涨", "bullish", "金叉", "超卖"]):
                signal_scores["bullish"] += 0.6 * num_confidence
                factors.append(f"数值模型看涨（置信度 {num_confidence:.2f}）")
            elif any(kw in num_response.lower() for kw in ["卖出", "看跌", "bearish", "死叉", "超买"]):
                signal_scores["bearish"] += 0.6 * num_confidence
                factors.append(f"数值模型看跌（置信度 {num_confidence:.2f}）")
            else:
                signal_scores["neutral"] += 0.6 * num_confidence
                factors.append(f"数值模型中性（置信度 {num_confidence:.2f}）")
        
        # 解析情感模型信号
        if sentiment and not isinstance(sentiment, Exception):
            sent_confidence = sentiment.get("confidence", 0.5)
            sent_response = sentiment.get("response", "")
            
            if any(kw in sent_response.lower() for kw in ["积极", "利好", "positive", "乐观"]):
                signal_scores["bullish"] += 0.4 * sent_confidence
                factors.append(f"情感模型积极（置信度 {sent_confidence:.2f}）")
            elif any(kw in sent_response.lower() for kw in ["消极", "利空", "negative", "悲观"]):
                signal_scores["bearish"] += 0.4 * sent_confidence
                factors.append(f"情感模型消极（置信度 {sent_confidence:.2f}）")
            else:
                signal_scores["neutral"] += 0.4 * sent_confidence
                factors.append(f"情感模型中性（置信度 {sent_confidence:.2f}）")
        
        # 确定最终信号
        max_signal = max(signal_scores, key=signal_scores.get)
        max_score = signal_scores[max_signal]
        
        # 计算综合置信度
        total_confidence = sum(signal_scores.values())
        combined_confidence = max_score / total_confidence if total_confidence > 0 else 0.5
        
        return {
            "signal": max_signal,
            "confidence": round(combined_confidence, 2),
            "scores": signal_scores,
            "factors": factors,
            "recommendation": self._generate_recommendation(max_signal, combined_confidence, factors)
        }
    
    def _generate_recommendation(
        self,
        signal: str,
        confidence: float,
        factors: list
    ) -> str:
        """生成操作建议"""
        if signal == "bullish" and confidence >= 0.6:
            return f"建议：可轻仓试多，综合置信度 {confidence:.0%}。{'；'.join(factors)}"
        elif signal == "bearish" and confidence >= 0.6:
            return f"建议：建议减仓或观望，综合置信度 {confidence:.0%}。{'；'.join(factors)}"
        else:
            return f"建议：信号不明确，建议观望。{'；'.join(factors)}"


# 使用示例
async def demo():
    """演示双模型路由服务"""
    router = FinancialLLMRouter()
    
    # 测试不同任务类型
    test_cases = [
        "计算 600000.SH 的 MACD 和 RSI 指标",
        "分析浦发银行的市场情绪",
        "生成一个均值回归策略",
        "编写 backtrader 交易代码",
        "总结这份券商研报"
    ]
    
    print("金融 LLM 路由服务演示\n")
    print("=" * 60)
    
    for query in test_cases:
        result = await router.route_query(query)
        print(f"\n查询：{query}")
        print(f"任务类型：{result['task_type']}")
        print(f"使用模型：{result['model_used']}")
        print(f"置信度：{result['confidence']:.2f}")
        print("-" * 60)
    
    # 获取推荐配置
    print("\n\n模型推荐配置:")
    print("=" * 60)
    
    for use_case in ["quantitative_trading", "sentiment_monitoring", 
                     "research_analysis", "realtime_analysis"]:
        rec = router.get_model_recommendation(use_case)
        print(f"\n场景：{use_case}")
        print(f"推荐模型：{rec['primary_model']}")
        print(f"原因：{rec['reason']}")
        print(f"量化等级：{rec['quantization']}")
        print(f"显存需求：{rec['vram_requirement']}")


if __name__ == "__main__":
    asyncio.run(demo())
