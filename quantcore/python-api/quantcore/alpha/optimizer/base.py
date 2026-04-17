"""
组合优化器基类

定义所有优化器的通用接口和约束条件。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
import numpy as np
import pandas as pd
from loguru import logger
from datetime import datetime


@dataclass
class OptimizationConstraints:
    """优化约束条件"""
    long_only: bool = True  # 只允许做多（权重 >= 0）
    max_position: float = 0.10  # 单个资产最大权重 (10%)
    min_position: float = 0.0  # 单个资产最小权重
    target_return: Optional[float] = None  # 目标收益率
    target_risk: Optional[float] = None  # 目标风险（波动率）
    max_turnover: Optional[float] = None  # 最大换手率
    
    # 因子暴露约束
    factor_neutral: bool = False  # 风格因子中性化
    industry_neutral: bool = False  # 行业中性化
    max_factor_exposure: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    # 基准跟踪
    benchmark_weights: Optional[pd.Series] = None  # 基准权重
    max_tracking_error: Optional[float] = None  # 最大跟踪误差
    
    # 其他
    min_assets: int = 10  # 最少持有资产数
    max_assets: Optional[int] = None  # 最多持有资产数


@dataclass
class OptimizationResult:
    """优化结果"""
    weights: pd.Series  # 最优权重 {asset: weight}
    expected_return: float = 0.0  # 预期收益
    risk: float = 0.0  # 风险（波动率）
    sharpe_ratio: float = 0.0  # 夏普比率
    
    # 约束满足情况
    constraints_satisfied: bool = True
    constraint_violations: List[str] = field(default_factory=list)
    
    # 优化信息
    method: str = ""
    optimization_time: float = 0.0
    iterations: int = 0
    status: str = "optimal"  # optimal/infeasible/error
    
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def summary(self) -> str:
        """生成结果摘要"""
        top_weights = self.weights.nlargest(5)
        
        lines = [
            "=" * 60,
            f"组合优化结果 ({self.method})",
            "=" * 60,
            f"状态: {self.status}",
            f"预期年化收益: {self.expected_return:.2%}",
            f"年化波动率:   {self.risk:.2%}",
            f"夏普比率:     {self.sharpe_ratio:.2f}",
            "-" * 60,
            "Top 5 持仓:",
        ]
        
        for asset, w in top_weights.items():
            lines.append(f"  {asset:<12}: {w:>8.2%}")
        
        if self.constraint_violations:
            lines.extend(["-" * 60, "约束违反:"])
            for v in self.constraint_violations[:5]:
                lines.append(f"  ⚠️ {v}")
        
        return "\n".join(lines)


class BaseOptimizer(ABC):
    """
    组合优化器基类
    
    所有优化器必须实现 optimize() 方法。
    
    使用示例：
        optimizer = MeanVarianceOptimizer(constraints=constraints)
        result = optimizer.optimize(returns_data)
        print(result.summary())
    """
    
    def __init__(self, constraints: Optional[OptimizationConstraints] = None):
        self.constraints = constraints or OptimizationConstraints()
        self._last_result: Optional[OptimizationResult] = None
    
    @abstractmethod
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> OptimizationResult:
        """
        执行组合优化
        
        Args:
            returns: 资产收益率数据 (date × asset)
            **kwargs: 额外参数
            
        Returns:
            OptimizationResult: 优化结果
        """
        pass
    
    def _validate_constraints(self, weights: pd.Series) -> List[str]:
        """验证约束是否满足"""
        violations = []
        
        if self.constraints.long_only and (weights < -1e-6).any():
            violations.append("存在负权重（非多头约束）")
        
        if self.constraints.max_position < 1.0:
            max_w = weights.max()
            if max_w > self.constraints.max_position + 1e-4:
                violations.append(f"最大持仓 {max_w:.2%} 超过限制 {self.constraints.max_position:.2%}")
        
        if self.constraints.min_position > 0:
            active = (weights > 1e-4).sum()
            if active < self.constraints.min_assets:
                violations.append(f"活跃持仓 {active} 少于最少要求 {self.constraints.min_assets}")
        
        if self.constraints.benchmark_weights is not None:
            turnover = (weights - self.constraints.benchmark_weights.reindex(weights.index, fill_value=0)).abs().sum() / 2
            if self.constraints.max_turnover and turnover > self.constraints.max_turnover + 1e-4:
                violations.append(f"换手率 {turnover:.2%} 超过限制")
        
        return violations
    
    def _calculate_portfolio_metrics(
        self,
        weights: pd.Series,
        returns: pd.DataFrame
    ) -> Tuple[float, float]:
        """计算组合预期收益和风险"""
        mean_returns = returns.mean() * 252  # 年化
        cov_matrix = returns.cov() * 252
        
        common_idx = mean_returns.index.intersection(weights.index)
        w = weights.loc[common_idx].values
        mu = mean_returns.loc[common_idx].values
        
        port_return = np.dot(w, mu)
        port_var = np.dot(w, np.dot(cov_matrix.loc[common_idx, common_idx].values, w))
        port_risk = np.sqrt(max(0, port_var))
        
        sharpe = port_return / port_risk if port_risk > 1e-8 else 0
        
        return port_return, port_risk, sharpe
