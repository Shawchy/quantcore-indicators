"""
风险归因模块

提供组合风险的分解和归因分析功能。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from .barra_model import PortfolioRiskResult


@dataclass
class RiskDecomposition:
    """风险分解结果"""
    total_risk: float
    factor_risk: float
    specific_risk: float
    
    factor_pct: float  # 因子风险占比%
    specific_pct: float  # 特质风险占比%
    
    # 各因子贡献（绝对值）
    factor_contributions: Dict[str, float]
    
    # 边际风险贡献 (MCR)
    marginal_contributions: Dict[str, float]
    
    # 风险集中度指标
    concentration_hhi: float = 0.0
    concentration_ratio: float = 0.0  # Top N 因子风险占比
    
    # 时间序列属性
    date: Optional[Any] = None
    
    def summary(self) -> str:
        """生成摘要报告"""
        top_factors = sorted(
            self.factor_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )[:5]
        
        lines = [
            "┌" + "─" * 50 + "┐",
            f"│ {'风险归因分析':^48} │",
            ├" + "─" * 50 + "┤",
            f"│ 总风险:       {self.total_risk:>12.2%}{'':>26}│",
            f"│ 因子风险:     {self.factor_risk:>12.2%} ({self.factor_pct:.1f}%){'':>16}│",
            f"│ 特质风险:     {self.specific_risk:>12.2%} ({self.specific_pct:.1f}%){'':>16}│",
            ├" + "─" * 50 + "┤",
            f"│ 主要因子风险贡献:":^52}│",
        ]
        
        for name, contrib in top_factors:
            bar_len = int(abs(contrib) / self.total_risk * 30)
            bar = "█" * max(0, bar_len) if contrib > 0 else "░" * max(0, bar_len)
            sign = "+" if contrib > 0 else ""
            lines.append(f"│   {name:<10}: {sign}{contrib:>8.2%} {bar:<15}│")
        
        lines.extend([
            "└" + "─" * 50 + "┘",
            f"\n风险集中度 HHI: {self.concentration_hhi:.4f}"
        ])
        
        return "\n".join(lines)


class RiskAttribution:
    """
    风险归因分析器
    
    将组合总风险分解为：
    - 各风格因子的风险贡献
    - 各行业的风险贡献
    - 个股特质风险贡献
    
    并计算边际风险贡献，用于风险管理。
    """
    
    @staticmethod
    def decompose(
        portfolio_risk: PortfolioRiskResult,
        top_n: int = 10
    ) -> RiskDecomposition:
        """
        分解风险来源
        
        Args:
            portfolio_risk: 组合风险结果
            top_n: 显示前 N 个主要因子
            
        Returns:
            RiskDecomposition: 详细分解结果
        """
        total = portfolio_risk.total_risk
        
        if total == 0 or total is None:
            return RiskDecomposition(
                total_risk=0,
                factor_risk=0,
                specific_risk=0,
                factor_pct=0,
                specific_pct=100,
                factor_contributions={},
                marginal_contributions={}
            )
        
        factor_pct = portfolio_risk.factor_risk / total * 100
        specific_pct = portfolio_risk.specific_risk / total * 100
        
        # 因子贡献排序
        sorted_contrib = sorted(
            portfolio_risk.factor_contributions.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        # 计算集中度
        contributions = [abs(c) for c in portfolio_risk.factor_contributions.values()]
        total_abs = sum(contributions)
        
        if total_abs > 0:
            hhi = sum((c / total_abs)**2 for c in contributions)
            
            # Top N 集中度
            top_n_sum = sum(sorted(contributions, reverse=True)[:top_n])
            concentration_ratio = top_n_sum / total_abs if total_abs > 0 else 0
        else:
            hhi = 0
            concentration_ratio = 0
        
        return RiskDecomposition(
            total_risk=total,
            factor_risk=portfolio_risk.factor_risk,
            specific_risk=portfolio_risk.specific_risk,
            factor_pct=factor_pct,
            specific_pct=specific_pct,
            factor_contributions=dict(portfolio_risk.factor_contributions),
            marginal_contributions=dict(portfolio_risk.marginal_contributions),
            concentration_hhi=hhi,
            concentration_ratio=concentration_ratio
        )
    
    @staticmethod
    def calculate_marginal_risk(
        weights: np.ndarray,
        exposures: np.ndarray,
        cov_matrix: np.ndarray
    ) -> np.ndarray:
        """
        计算边际风险贡献 (MCR)
        
        MCR_i = ∂σ_p / ∂w_i
        
        表示权重微小变化对组合风险的影响。
        
        Args:
            weights: 权重向量
            exposures: 因子暴露矩阵 (N × K)
            cov_matrix: 协方差矩阵 (K × K)
            
        Returns:
            ndarray: 各资产的边际风险贡献
        """
        portfolio_exposure = (weights * exposures.T).sum(axis=1)  # K × 1
        var = float(portfolio_exposure @ cov_matrix @ portfolio_exposure)
        
        if var <= 0:
            return np.zeros(len(weights))
        
        sigma = np.sqrt(var)
        
        # MCR = (B @ F @ B' @ w) / σ
        mcr = (exposures @ cov_matrix @ portfolio_exposure) / sigma
        
        return mcr
    
    @staticmethod
    def calculate_component_risk(
        weights: np.ndarray,
        exposures: np.ndarray,
        cov_matrix: np.DataFrame,
        specific_variances: np.ndarray
    ) -> Tuple[Dict[str, float], float]:
        """
        计算各成分的风险贡献 (CR)
        
        CR_k = w_k × MCR_k × σ_p / σ_p = w_k × MCR_k
        
        Args:
            weights: 权重向量
            exposures: 因子暴露矩阵
            cov_matrix: 协方差 DataFrame
            specific_variances: 特质方差向量
            
        Returns:
            Tuple: (因子贡献字典, 特质风险)
        """
        factor_names = list(cov_matrix.columns)
        n_assets = len(weights)
        
        # 组合因子暴露
        port_exp = (weights * exposures.T).sum(axis=1)
        
        # 因子风险
        factor_var = float(port_exp @ cov_matrix.values @ port_exp)
        
        # 各因子贡献
        factor_cr = {}
        for i, name in enumerate(factor_names):
            cr = port_exp[i] * (cov_matrix.values @ port_exp)[i] / (np.sqrt(factor_var) if factor_var > 0 else 1)
            factor_cr[name] = cr
        
        # 特质风险
        specific_var = (weights**2 * specific_variances).sum()
        specific_risk = np.sqrt(max(0, specific_var))
        
        return factor_cr, specific_risk
    
    @staticmethod
    def risk_budget_check(
        target_weights: pd.Series,
        current_weights: pd.Series,
        risk_tolerance: float = 0.02
    ) -> Dict[str, Any]:
        """
        检查是否超出风险预算
        
        Args:
            target_weights: 目标权重
            current_weights: 当前权重
            risk_tolerance: 风险容忍度
            
        Returns:
            Dict: 风险检查结果
        """
        deviation = (current_weights - target_weights).abs().sum() / 2
        
        status = "OK" if deviation < risk_tolerance else "WARNING"
        
        return {
            "status": status,
            "deviation": float(deviation),
            "tolerance": risk_tolerance,
            "excess": max(0, deviation - risk_tolerance),
            "max_deviation_stock": {
                stock: float((current_weights - target_weights).abs().idxmax()),
                value: float((current_weights - target_weights).abs().max())
            }
        }
