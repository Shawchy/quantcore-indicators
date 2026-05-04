"""
LLM 助手服务 - 基于 Qwen3.5-9B
单一最优模型方案，专注量化交易核心需求
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from dataclasses import dataclass
import asyncio
import time


class LLMResponse(BaseModel):
    """LLM 响应模型"""
    content: str
    model: str
    latency_ms: float
    tokens_used: Optional[int] = None
    confidence: Optional[float] = None


class StockQueryRequest(BaseModel):
    """股票查询请求"""
    symbol: str
    question: str
    market_data: Optional[Dict[str, Any]] = None


class StrategyGenRequest(BaseModel):
    """策略生成请求"""
    strategy_type: str = "technical"  # technical/fundamental/sentiment
    description: str
    risk_level: str = "medium"  # low/medium/high
    symbols: Optional[List[str]] = None


@dataclass
class ModelConfig:
    """模型配置"""
    model_name: str = "qwen3.5:9b"
    base_url: str = "http://localhost:11434"
    temperature: float = 0.3
    max_tokens: int = 1024
    context_length: int = 32768
    top_p: float = 0.9


class QwenAssistant:
    """
    Qwen3.5-9B 量化交易助手
    
    核心能力:
    1. 技术指标计算与解读
    2. 量化策略生成
    3. 交易代码编写
    4. 实时行情分析
    5. 基础情感分析
    
    优势:
    - Alpha Arena 实盘验证
    - 全能无短板
    - 部署简单
    - 显存友好
    """
    
    def __init__(self, config: Optional[ModelConfig] = None):
        """
        初始化助手
        
        Args:
            config: 模型配置
        """
        self.config = config or ModelConfig()
        self._system_prompt = self._build_system_prompt()
        self._stats = {
            "total_requests": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "avg_latency_ms": 0.0
        }
        
        # 延迟导入 Ollama（避免依赖问题）
        self._client = None
    
    def _build_system_prompt(self) -> str:
        """构建系统提示词"""
        return """你是专业量化交易专家，精通：

核心能力:
1. 技术指标计算（MACD, RSI, KDJ, BOLL, MA 等）
2. 量化策略设计与回测
3. 实时行情数据分析
4. 交易代码生成（Python, Backtrader, Qlib）
5. 基础市场情绪分析

回答原则:
- 提供精确计算公式和步骤
- 给出明确买卖信号和置信度
- 使用专业金融术语
- 注意风险提示
- 中文回答，专业简洁
- 数据驱动，避免主观臆测

示例:
用户：计算 600000.SH 的 MACD
你：【MACD 计算结果】
参数：EMA(12)=10.52, EMA(26)=10.38
DIF = 0.14
DEA = 0.11
MACD 柱 = 0.06
信号：金叉（看涨），置信度 75%
建议：可轻仓试多，止损 10.20 元"""
    
    def _get_client(self):
        """获取 Ollama 客户端"""
        if self._client is None:
            try:
                from ollama import Client
                self._client = Client(
                    host=self.config.base_url,
                    timeout=120.0
                )
            except ImportError:
                raise ImportError("请安装 ollama: pip install ollama")
        return self._client
    
    async def query_stock(
        self,
        symbol: str,
        question: str,
        market_data: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        股票查询
        
        Args:
            symbol: 股票代码
            question: 问题
            market_data: 市场数据
        
        Returns:
            LLMResponse: 响应
        """
        start_time = time.time()
        
        # 构建上下文
        context = self._build_stock_context(symbol, market_data)
        prompt = f"{context}\n\n用户问题：{question}"
        
        try:
            # 调用模型
            response = await self._generate(prompt)
            
            # 更新统计
            latency = (time.time() - start_time) * 1000
            self._update_stats(success=True, latency=latency)
            
            return LLMResponse(
                content=response,
                model=self.config.model_name,
                latency_ms=latency
            )
            
        except Exception as e:
            self._update_stats(success=False)
            raise RuntimeError(f"股票查询失败：{str(e)}")
    
    async def generate_strategy(
        self,
        description: str,
        strategy_type: str = "technical",
        risk_level: str = "medium",
        symbols: Optional[List[str]] = None
    ) -> LLMResponse:
        """
        生成量化策略
        
        Args:
            description: 策略描述
            strategy_type: 策略类型
            risk_level: 风险等级
            symbols: 标的列表
        
        Returns:
            LLMResponse: 生成的策略
        """
        start_time = time.time()
        
        # 构建策略生成提示
        prompt = f"""请生成一个量化交易策略：

策略类型：{strategy_type}
风险等级：{risk_level}
策略描述：{description}
关注标的：{', '.join(symbols) if symbols else '全市场'}

请提供:
1. 策略逻辑和原理
2. 入场条件（明确信号）
3. 出场条件（止盈/止损）
4. 仓位管理建议
5. 风险提示

如果需要代码实现，请使用 Python + Backtrader 格式。"""
        
        try:
            response = await self._generate(prompt, system_prompt=self._system_prompt)
            
            latency = (time.time() - start_time) * 1000
            self._update_stats(success=True, latency=latency)
            
            return LLMResponse(
                content=response,
                model=self.config.model_name,
                latency_ms=latency
            )
            
        except Exception as e:
            self._update_stats(success=False)
            raise RuntimeError(f"策略生成失败：{str(e)}")
    
    async def explain_code(
        self,
        code: str,
        focus: Optional[str] = None
    ) -> LLMResponse:
        """
        解释交易代码
        
        Args:
            code: 代码
            focus: 关注点（如"风险控制"、"信号生成"等）
        
        Returns:
            LLMResponse: 解释
        """
        start_time = time.time()
        
        prompt = f"""请解释以下交易代码：

```python
{code}
```
"""
        if focus:
            prompt += f"\n请重点解释：{focus}"
        
        try:
            response = await self._generate(prompt)
            
            latency = (time.time() - start_time) * 1000
            self._update_stats(success=True, latency=latency)
            
            return LLMResponse(
                content=response,
                model=self.config.model_name,
                latency_ms=latency
            )
            
        except Exception as e:
            self._update_stats(success=False)
            raise RuntimeError(f"代码解释失败：{str(e)}")
    
    async def analyze_sentiment(
        self,
        text: str,
        symbol: Optional[str] = None
    ) -> LLMResponse:
        """
        情感分析
        
        Args:
            text: 文本内容
            symbol: 相关标的
        
        Returns:
            LLMResponse: 情感分析结果
        """
        start_time = time.time()
        
        prompt = f"""请分析以下文本的情感倾向：

文本：{text}
"""
        if symbol:
            prompt += f"\n相关标的：{symbol}"
        
        prompt += """
请从以下维度分析:
1. 情感极性（positive/neutral/negative）
2. 情感强度（0.0-1.0）
3. 影响标的
4. 时效性（短期/中期/长期）
5. 操作建议"""
        
        try:
            response = await self._generate(prompt)
            
            latency = (time.time() - start_time) * 1000
            self._update_stats(success=True, latency=latency)
            
            return LLMResponse(
                content=response,
                model=self.config.model_name,
                latency_ms=latency
            )
            
        except Exception as e:
            self._update_stats(success=False)
            raise RuntimeError(f"情感分析失败：{str(e)}")
    
    async def _generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        调用模型生成响应
        
        Args:
            prompt: 用户提示
            system_prompt: 系统提示
        
        Returns:
            str: 生成内容
        """
        client = self._get_client()
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        def _call():
            return client.chat(
                model=self.config.model_name,
                messages=[
                    {"role": "system", "content": system_prompt or self._system_prompt},
                    {"role": "user", "content": prompt}
                ],
                options={
                    "temperature": self.config.temperature,
                    "num_predict": self.config.max_tokens,
                    "top_p": self.config.top_p,
                }
            )
        
        response = await asyncio.wait_for(
            loop.run_in_executor(None, _call),
            timeout=120
        )
        
        # 提取响应内容
        if hasattr(response, 'message'):
            return response.message.content
        elif isinstance(response, dict) and 'message' in response:
            return response['message']['content']
        else:
            return str(response)
    
    def _build_stock_context(
        self,
        symbol: str,
        market_data: Optional[Dict[str, Any]] = None
    ) -> str:
        """构建股票上下文"""
        context = f"股票代码：{symbol}"
        
        if market_data:
            context += "\n\n市场数据:"
            for key, value in market_data.items():
                if isinstance(value, float):
                    context += f"\n- {key}: {value:.2f}"
                else:
                    context += f"\n- {key}: {value}"
        
        return context
    
    def _update_stats(self, success: bool, latency: float = 0.0):
        """更新统计信息"""
        self._stats["total_requests"] += 1
        
        if success:
            self._stats["successful_requests"] += 1
            # 移动平均延迟
            n = self._stats["successful_requests"]
            self._stats["avg_latency_ms"] = (
                (self._stats["avg_latency_ms"] * (n - 1) + latency) / n
            )
        else:
            self._stats["failed_requests"] += 1
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self._stats.copy()
    
    def health_check(self) -> bool:
        """健康检查"""
        try:
            client = self._get_client()
            # 简单测试
            response = client.chat(
                model=self.config.model_name,
                messages=[{"role": "user", "content": "你好"}],
                options={"num_predict": 10}
            )
            return True
        except Exception:
            return False


# 全局助手实例
_assistant: Optional[QwenAssistant] = None


def get_assistant() -> QwenAssistant:
    """获取助手实例（单例模式）"""
    global _assistant
    if _assistant is None:
        _assistant = QwenAssistant()
    return _assistant


# 演示
async def demo():
    """演示功能"""
    print("=" * 60)
    print("Qwen3.5-9B 量化交易助手演示")
    print("=" * 60)
    
    assistant = get_assistant()
    
    # 测试 1: 股票查询
    print("\n【测试 1】技术指标计算")
    print("-" * 60)
    try:
        result = await assistant.query_stock(
            symbol="600000.SH",
            question="计算 MACD 和 RSI 指标，并给出操作建议",
            market_data={
                "current_price": 10.52,
                "prev_close": 10.45,
                "change_percent": 0.67
            }
        )
        print(f"响应时间：{result.latency_ms:.0f}ms")
        print(f"内容:\n{result.content}")
    except Exception as e:
        print(f"错误：{e}")
    
    # 测试 2: 策略生成
    print("\n【测试 2】量化策略生成")
    print("-" * 60)
    try:
        result = await assistant.generate_strategy(
            description="RSI 超卖反弹策略，当 RSI 低于 30 时买入，高于 70 时卖出",
            strategy_type="technical",
            risk_level="medium",
            symbols=["600000.SH", "000001.SZ"]
        )
        print(f"响应时间：{result.latency_ms:.0f}ms")
        print(f"内容:\n{result.content[:500]}...")
    except Exception as e:
        print(f"错误：{e}")
    
    # 测试 3: 情感分析
    print("\n【测试 3】市场情感分析")
    print("-" * 60)
    try:
        result = await assistant.analyze_sentiment(
            text="央行宣布降准 0.5 个百分点，释放长期资金约 1 万亿元",
            symbol="银行板块"
        )
        print(f"响应时间：{result.latency_ms:.0f}ms")
        print(f"内容:\n{result.content}")
    except Exception as e:
        print(f"错误：{e}")
    
    # 显示统计
    print("\n【统计信息】")
    print("-" * 60)
    stats = assistant.get_stats()
    print(f"总请求：{stats['total_requests']}")
    print(f"成功：{stats['successful_requests']}")
    print(f"失败：{stats['failed_requests']}")
    print(f"平均延迟：{stats['avg_latency_ms']:.0f}ms")


if __name__ == "__main__":
    asyncio.run(demo())
