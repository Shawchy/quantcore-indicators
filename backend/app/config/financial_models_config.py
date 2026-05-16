"""
金融专用大模型部署配置
支持 Qwen3-8B-Financial 和 FinSenti-Qwen3.5-9B
"""

from typing import Dict, Any
from pydantic import BaseModel, Field


class ModelConfig(BaseModel):
    """模型配置"""
    model_name: str
    model_path: str
    quantization: str = "Q5_K_M"
    n_ctx: int = 32768
    n_gpu_layers: int = -1
    n_threads: int = 8
    verbose: bool = False


# 两个金融专用模型的配置
FINANCIAL_MODELS: Dict[str, ModelConfig] = {
    "numerical": ModelConfig(
        model_name="qwen3-8b-financial-numerical",
        model_path="models/Qwen3-8B-Financial-Numerical-Reasoning-GGUF/qwen3-8b-financial-Q5_K_M.gguf",
        quantization="Q5_K_M",
        n_ctx=32768,
        n_gpu_layers=-1,  # 全部层 GPU 加速
        n_threads=8,
        verbose=False
    ),
    
    "sentiment": ModelConfig(
        model_name="finsenti-qwen3.5-9b",
        model_path="models/FinSenti-Qwen3.5-9B-GGUF/finsenti-qwen3.5-9b-Q5_K_M.gguf",
        quantization="Q5_K_M",
        n_ctx=65536,  # 支持更长文本
        n_gpu_layers=-1,
        n_threads=8,
        verbose=False
    )
}


# Ollama 模型标签配置
OLLAMA_MODEL_TAGS = {
    "numerical": "qwen3:8b-financial",
    "sentiment": "finsenti-qwen3.5:9b"
}


# 部署脚本生成
DEPLOYMENT_SCRIPT = """
# ============================================
# 金融专用大模型部署脚本
# ============================================

# 1. 下载模型（使用 huggingface-cli）
echo "正在下载 Qwen3-8B-Financial-Numerical-Reasoning..."
huggingface-cli download mradermacher/Qwen3-8B-Financial-Numerical-Reasoning-GGUF \\
  --include "*.gguf" \\
  --local-dir models/Qwen3-8B-Financial-Numerical-Reasoning-GGUF

echo "正在下载 FinSenti-Qwen3.5-9B..."
huggingface-cli download mradermacher/FinSenti-Qwen3.5-9B-GGUF \\
  --include "*.gguf" \\
  --local-dir models/FinSenti-Qwen3.5-9B-GGUF

# 2. 导入到 Ollama（创建 Modelfile）
echo "创建 Ollama Modelfile..."

# 数值推理模型
cat > models/Modelfile_numerical << 'EOF'
FROM models/Qwen3-8B-Financial-Numerical-Reasoning-GGUF/qwen3-8b-financial-Q5_K_M.gguf

# 系统提示词 - 金融数值分析专用
SYSTEM \"\"\"你是金融量化分析专家，专注于股票数值计算、技术指标分析和量化策略生成。

核心能力:
1. 精确的数值计算和技术指标分析
2. 量化交易策略设计和回测
3. 财务报表数据提取和比率计算
4. 实时行情数据解读

回答原则:
- 提供具体的计算公式和步骤
- 给出明确的买卖信号和置信度
- 使用专业的金融术语
- 注意风险提示

示例:
用户：计算 600000.SH 的 MACD
你：MACD 计算步骤:
1. EMA(12) = 当前收盘价×2/(12+1) + 前一日 EMA(12)×(1-2/(12+1))
2. EMA(26) = 当前收盘价×2/(26+1) + 前一日 EMA(26)×(1-2/(26+1))
3. DIF = EMA(12) - EMA(26)
4. DEA = DIF 的 9 日 EMA
5. MACD 柱 = 2 × (DIF - DEA)

当前值:DIF=0.15, DEA=0.12, MACD=0.06（金叉信号）\"\"\"
EOF

# 情感分析模型
cat > models/Modelfile_sentiment << 'EOF'
FROM models/FinSenti-Qwen3.5-9B-GGUF/finsenti-qwen3.5-9b-Q5_K_M.gguf

# 系统提示词 - 金融情感分析专用
SYSTEM \"\"\"你是金融市场情感分析专家，擅长解读新闻、研报、社交媒体中的市场情绪。

核心能力:
1. 财经新闻情感倾向分析（正面/负面/中性）
2. 券商研报关键信息提取
3. 市场情绪指标计算
4. 舆情监控和预警

分析维度:
- 情感极性：positive/neutral/negative
- 情感强度：0.0-1.0
- 影响标的：具体股票/行业/大盘
- 时效性：短期/中期/长期影响

示例:
用户：分析这条新闻的情感倾向
新闻：央行宣布降准 0.5 个百分点，释放长期资金约 1 万亿元
你：情感分析结果:
- 极性：positive (正面)
- 强度：0.85 (强正面)
- 受益板块：银行、券商、房地产
- 影响时效：中期 (1-3 个月)
- 解读：降准降低资金成本，提升市场流动性\"\"\"
EOF

# 3. 创建 Ollama 模型
echo "创建 Ollama 模型实例..."
ollama create qwen3:8b-financial -f models/Modelfile_numerical
ollama create finsenti-qwen3.5:9b -f models/Modelfile_sentiment

# 4. 验证安装
echo "验证模型安装..."
ollama list

# 5. 启动 Ollama 服务
echo "启动 Ollama 服务..."
ollama serve

# ============================================
# 使用方法
# ============================================
# 
# 测试数值模型:
# ollama run qwen3:8b-financial "计算 600000.SH 的 RSI 指标，当前价格 10.5 元"
#
# 测试情感模型:
# ollama run finsenti-qwen3.5:9b "分析：证监会发布新规，支持上市公司并购重组"
#
# ============================================
"""


def get_deployment_recommendation(hardware: str = "consumer") -> Dict[str, Any]:
    """
    根据硬件配置推荐部署方案
    
    Args:
        hardware: 硬件类型 ("consumer", "professional", "cloud")
    
    Returns:
        Dict: 部署推荐
    """
    recommendations = {
        "consumer": {
            "description": "消费级显卡 (RTX 3090/4090, 24GB VRAM)",
            "strategy": "单模型部署，按需切换",
            "models": ["numerical"],  # 优先部署数值模型
            "quantization": "Q4_K_M",
            "context_length": 32768,
            "estimated_vram": "6-7GB",
            "notes": "资源有限时优先使用数值模型，情感分析可用传统 NLP 替代"
        },
        
        "professional": {
            "description": "专业级显卡 (RTX 6000 Ada, 48GB VRAM)",
            "strategy": "双模型同时部署",
            "models": ["numerical", "sentiment"],
            "quantization": "Q5_K_M",
            "context_length": 65536,
            "estimated_vram": "14-16GB",
            "notes": "可同时运行两个模型，支持综合分析"
        },
        
        "cloud": {
            "description": "云服务器 (A100 80GB 或多卡)",
            "strategy": "双模型 + 高精度",
            "models": ["numerical", "sentiment"],
            "quantization": "Q6_K 或 BF16",
            "context_length": 131072,
            "estimated_vram": "40-60GB",
            "notes": "使用最高精度，支持超长文本和批量推理"
        }
    }
    
    return recommendations.get(hardware, recommendations["consumer"])


def generate_modelfile(model_type: str) -> str:
    """
    生成 Ollama Modelfile
    
    Args:
        model_type: 模型类型 ("numerical" 或 "sentiment")
    
    Returns:
        str: Modelfile 内容
    """
    if model_type == "numerical":
        return """FROM models/Qwen3-8B-Financial-Numerical-Reasoning-GGUF/qwen3-8b-financial-Q5_K_M.gguf

SYSTEM \"\"\"你是金融量化分析专家，专注于股票数值计算、技术指标分析和量化策略生成。

核心能力:
1. 精确的数值计算和技术指标分析
2. 量化交易策略设计和回测
3. 财务报表数据提取和比率计算
4. 实时行情数据解读

回答原则:
- 提供具体的计算公式和步骤
- 给出明确的买卖信号和置信度
- 使用专业的金融术语
- 注意风险提示\"\"\"

PARAMETER temperature 0.3
PARAMETER top_p 0.9
PARAMETER num_predict 1024
"""
    
    elif model_type == "sentiment":
        return """FROM models/FinSenti-Qwen3.5-9B-GGUF/finsenti-qwen3.5-9b-Q5_K_M.gguf

SYSTEM \"\"\"你是金融市场情感分析专家，擅长解读新闻、研报、社交媒体中的市场情绪。

核心能力:
1. 财经新闻情感倾向分析（正面/负面/中性）
2. 券商研报关键信息提取
3. 市场情绪指标计算
4. 舆情监控和预警

分析维度:
- 情感极性：positive/neutral/negative
- 情感强度：0.0-1.0
- 影响标的：具体股票/行业/大盘
- 时效性：短期/中期/长期影响\"\"\"

PARAMETER temperature 0.4
PARAMETER top_p 0.85
PARAMETER num_predict 1024
"""
    
    else:
        raise ValueError(f"Unknown model_type: {model_type}")


if __name__ == "__main__":
    import json
    
    print("金融专用大模型部署指南")
    print("=" * 60)
    
    # 显示模型配置
    for model_key, config in FINANCIAL_MODELS.items():
        print(f"\n{model_key.upper()} 模型:")
        print(f"  模型名称：{config.model_name}")
        print(f"  模型路径：{config.model_path}")
        print(f"  量化等级：{config.quantization}")
        print(f"  上下文长度：{config.n_ctx}")
        print(f"  GPU 层数：{config.n_gpu_layers}")
    
    # 显示部署推荐
    print("\n\n部署推荐方案:")
    print("=" * 60)
    
    for hardware in ["consumer", "professional", "cloud"]:
        rec = get_deployment_recommendation(hardware)
        print(f"\n{hardware.upper()} 方案:")
        print(f"  硬件：{rec['description']}")
        print(f"  策略：{rec['strategy']}")
        print(f"  部署模型：{', '.join(rec['models'])}")
        print(f"  量化等级：{rec['quantization']}")
        print(f"  显存需求：{rec['estimated_vram']}")
        print(f"  备注：{rec['notes']}")
    
    # 生成部署脚本
    print("\n\n部署脚本已生成，保存为：deploy_financial_models.sh")
    with open("deploy_financial_models.sh", "w", encoding="utf-8") as f:
        f.write(DEPLOYMENT_SCRIPT)
    
    print("\n部署脚本内容预览:")
    print("-" * 60)
    print(DEPLOYMENT_SCRIPT[:500] + "...")
