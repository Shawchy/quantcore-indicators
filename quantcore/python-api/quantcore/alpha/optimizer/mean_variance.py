"""
均值-方差优化器 (Markowitz)

经典的 Markowitz 均值-方差模型。
目标：最大化效用函数 U = μ - λ × σ²
"""

import numpy as np
import pandas as pd
from typing import Optional, Tuple, List
from scipy.optimize import minimize
from loguru import logger

from .base import BaseOptimizer, OptimizationConstraints, OptimizationResult


class MeanVarianceOptimizer(BaseOptimizer):
    """
    均值-方差优化器 (Markowitz)
    
    目标函数：
        max  w'μ - (λ/2) w'Σw
        
    约束条件：
        - w'1 = 1 (权重和为1)
        - w_i ≥ 0 (多头约束)
        - w_i ≤ max_position (单资产上限)
        
    使用示例：
        optimizer = MeanVarianceOptimizer(
            constraints=OptimizationConstraints(
                long_only=True,
                max_position=0.10
            )
        )
        result = optimizer.optimize(returns_data, risk_aversion=2.0)
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        risk_aversion: float = 1.0,
        **kwargs
    ) -> OptimizationResult:
        """
        执行均值-方差优化
        
        Args:
            returns: 资产收益率矩阵 (T × N)
            risk_aversion: 风险厌恶系数 (λ)，越大越保守
            
        Returns:
            OptimizationResult: 优化结果
        """
        import time
        start_time = time.time()
        
        n_assets = returns.shape[1]
        assets = returns.columns.tolist()
        
        # 预期收益和协方差
        mu = returns.mean().values * 252  # 年化收益
        cov = returns.cov().values * 252  # 年化协方差
        
        # 初始权重（等权）
        w0 = np.ones(n_assets) / n_assets
        
        # 约束条件
        constraints_list = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}  # 权重和为1
        ]
        
        if self.constraints.target_return is not None:
            constraints_list.append({
                'type': 'eq',
                'fun': lambda w: float(np.dot(w, mu)) - self.constraints.target_return
            })
        
        bounds = []
        for i in range(n_assets):
            lower = self.constraints.min_position
            upper = self.constraints.max_position
            if self.constraints.long_only:
                lower = max(lower, 0.0)
            bounds.append((lower, upper))
        
        # 目标函数：最大化风险调整后收益
        def objective(w):
            port_return = np.dot(w, mu)
            port_var = np.dot(w, np.dot(cov, w))
            return -(port_return - risk_aversion / 2 * port_var)  # 最小化负效用
        
        # 梯度（可选，加速收敛）
        def gradient(w):
            return -(mu - risk_aversion * np.dot(cov, w))
        
        try:
            result = minimize(
                objective,
                w0,
                method='SLSQP',
                jac=gradient,
                bounds=bounds,
                constraints=constraints_list,
                options={'maxiter': 1000, 'ftol': 1e-8}
            )
            
            if result.success or result.fun < 1e10:
                weights = pd.Series(result.x, index=assets)
                
                # 计算组合指标
                port_return = float(np.dot(result.x, mu))
                port_risk = float(np.sqrt(max(0, np.dot(result.x, np.dot(cov, result.x)))))
                sharpe = port_return / port_risk if port_risk > 1e-8 else 0
                
                violations = self._validate_constraints(weights)
                
                opt_result = OptimizationResult(
                    weights=weights,
                    expected_return=port_return,
                    risk=port_risk,
                    sharpe_ratio=sharpe,
                    constraints_satisfied=len(violations) == 0,
                    constraint_violations=violations,
                    method="Mean-Variance",
                    optimization_time=time.time() - start_time,
                    iterations=result.nit,
                    status="optimal" if result.success else "suboptimal"
                )
            else:
                opt_result = OptimizationResult(
                    weights=pd.Series(w0, index=assets),
                    method="Mean-Variance",
                    status="infeasible",
                    constraint_violations=["优化未收敛"]
                )
                
        except Exception as e:
            logger.error(f"均值-方差优化失败: {e}")
            opt_result = OptimizationResult(
                weights=pd.Series(w0, index=assets),
                method="Mean-Variance",
                status="error",
                constraint_violations=[str(e)]
            )
        
        self._last_result = opt_result
        return opt_result
    
    def efficient_frontier(
        self,
        returns: pd.DataFrame,
        n_points: int = 20
    ) -> pd.DataFrame:
        """
        计算有效前沿
        
        Args:
            returns: 收益率数据
            n_points: 前沿点数
            
        Returns:
            DataFrame: 有效前沿点 (return, risk, sharpe)
        """
        frontier = []
        
        min_ret = returns.mean().min() * 252
        max_ret = returns.mean().max() * 252
        target_returns = np.linspace(min_ret, max_ret, n_points)
        
        for target in target_returns:
            old_target = self.constraints.target_return
            self.constraints.target_return = target
            
            result = self.optimize(returns, risk_aversion=1.0)
            
            self.constraints.target_return = old_target
            
            if result.status != "error":
                frontier.append({
                    "return": result.expected_return,
                    "risk": result.risk,
                    "sharpe": result.sharpe_ratio
                })
        
        return pd.DataFrame(frontier)


class MinVarianceOptimizer(BaseOptimizer):
    """
    最小方差优化器
    
    目标：最小化组合波动率，不考虑预期收益。
    
    适用于：
    - 风险厌恶型投资者
    - 作为其他优化的基准比较
    """
    
    def optimize(self, returns: pd.DataFrame, **kwargs) -> OptimizationResult:
        """执行最小方差优化"""
        import time
        start_time = time.time()
        
        n_assets = returns.shape[1]
        assets = returns.columns.tolist()
        cov = returns.cov().values * 252
        
        w0 = np.ones(n_assets) / n_assets
        
        def objective(w):
            return np.dot(w, np.dot(cov, w))
        
        def gradient(w):
            return 2 * np.dot(cov, w)
        
        bounds = [(0, self.constraints.max_position)] * n_assets
        
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
        
        try:
            result = minimize(objective, w0, method='SLSQP', jac=gradient,
                          bounds=bounds, constraints=constraints,
                          options={'maxiter': 1000})
            
            weights = pd.Series(result.x, index=assets)
            port_risk = float(np.sqrt(max(0, objective(result.x))))
            port_return = float(np.dot(result.x, returns.mean().values * 252))
            sharpe = port_return / port_risk if port_risk > 1e-8 else 0
            
            opt_result = OptimizationResult(
                weights=weights,
                expected_return=port_return,
                risk=port_risk,
                sharpe_ratio=sharpe,
                method="Min-Variance",
                optimization_time=time.time() - start_time,
                status="optimal" if result.success else "suboptimal"
            )
            
        except Exception as e:
            opt_result = OptimizationResult(
                weights=pd.Series(w0, index=assets),
                method="Min-Variance",
                status="error"
            )
        
        self._last_result = opt_result
        return opt_result
