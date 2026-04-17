"""
风险平价优化器 (Risk Parity)

实现等风险贡献的组合优化。
"""

import numpy as np
import pandas as pd
from typing import Optional
from scipy.optimize import minimize
from loguru import logger

from .base import BaseOptimizer, OptimizationConstraints, OptimizationResult


class RiskParityOptimizer(BaseOptimizer):
    """
    风险平价优化器
    
    目标：使各资产对组合风险的贡献相等。
    
    核心思想：
        RC_i = w_i × (∂σ/∂w_i) = 常数
    
    优势：
    - 不依赖收益预测（更稳健）
    - 自动适应波动率变化
    - 分散化效果更好
    
    使用示例：
        optimizer = RiskParityOptimizer()
        result = optimizer.optimize(returns_data)
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> OptimizationResult:
        """
        执行风险平价优化
        
        Args:
            returns: 资产收益率矩阵
            
        Returns:
            OptimizationResult: 优化结果
        """
        import time
        start_time = time.time()
        
        n_assets = returns.shape[1]
        assets = returns.columns.tolist()
        
        cov = returns.cov().values * 252  # 年化协方差
        
        # 初始权重：逆波动率加权
        vols = np.sqrt(np.diag(cov))
        w0 = (1 / vols) / (1 / vols).sum()
        
        def risk_budget_objective(weights):
            """风险预算目标函数"""
            # 组合波动
            port_var = np.dot(weights, np.dot(cov, weights))
            
            if port_var <= 0:
                return 1e10
            
            port_vol = np.sqrt(port_var)
            
            # 边际风险贡献
            marginal_risk = np.dot(cov, weights) / port_vol
            
            # 风险贡献
            risk_contrib = weights * marginal_risk
            
            # 目标：各资产风险贡献相等
            target_risk = port_vol / n_assets
            
            # 最小化偏差平方和
            return np.sum((risk_contrib - target_risk)**2)
        
        def gradient(weights):
            """梯度"""
            port_var = np.dot(weights, np.dot(cov, weights))
            
            if port_var <= 1e-10:
                return np.ones(n_assets) * 1e10
            
            port_vol = np.sqrt(port_var)
            mrc = np.dot(cov, weights) / port_vol
            rc = weights * mrc
            target = port_vol / n_assets
            
            grad = 2 * (rc - target) * (mrc + weights * (cov / port_vol - 
                  np.outer(mrc, mrc) / port_vol))
            
            return grad
        
        bounds = [(self.constraints.min_position, self.constraints.max_position)] * n_assets
        
        constraints = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]
        
        try:
            result = minimize(
                risk_budget_objective,
                w0,
                method='SLSQP',
                jac=gradient,
                bounds=bounds,
                constraints=constraints,
                options={'maxiter': 1000, 'ftol': 1e-10}
            )
            
            if result.success or result.fun < 1e6:
                weights = pd.Series(result.x, index=assets)
                
                port_return = float(np.dot(result.x, returns.mean().values * 252))
                port_risk = float(np.sqrt(max(0, np.dot(result.x, np.dot(cov, result.x)))))
                sharpe = port_return / port_risk if port_risk > 1e-8 else 0
                
                opt_result = OptimizationResult(
                    weights=weights,
                    expected_return=port_return,
                    risk=port_risk,
                    sharpe_ratio=sharpe,
                    method="Risk Parity",
                    optimization_time=time.time() - start_time,
                    iterations=result.nit,
                    status="optimal" if result.success else "suboptimal",
                    metadata={"objective_value": float(result.fun)}
                )
            else:
                opt_result = OptimizationResult(
                    weights=pd.Series(w0, index=assets),
                    method="Risk Parity",
                    status="infeasible"
                )
                
        except Exception as e:
            logger.error(f"风险平价优化失败: {e}")
            opt_result = OptimizationResult(
                weights=pd.Series(w0, index=assets),
                method="Risk Parity",
                status="error"
            )
        
        self._last_result = opt_result
        return opt_result


class InverseVolatilityWeighting(BaseOptimizer):
    """
    逆波动率加权 (IVP)
    
    简化的风险平价方法，直接按波动率倒数分配权重。
    
    w_i ∝ 1/σ_i
    """
    
    def optimize(self, returns: pd.DataFrame, **kwargs) -> OptimizationResult:
        """执行逆波动率加权"""
        import time
        start_time = time.time()
        
        vols = returns.std().values * np.sqrt(252)  # 年化波动率
        vols = np.maximum(vols, 1e-8)  # 避免除零
        
        inv_vols = 1 / vols
        weights_raw = inv_vols / inv_vols.sum()
        
        # 应用约束
        max_pos = self.constraints.max_position
        min_pos = self.constraints.min_position
        
        # 截断并重新归一化
        weights_clipped = np.clip(weights_raw, min_pos, max_pos)
        weights_final = weights_clipped / weights_clipped.sum()
        
        assets = returns.columns.tolist()
        weights = pd.Series(weights_final, index=assets)
        
        cov = returns.cov().values * 252
        port_return = float(np.dot(weights.values, returns.mean().values * 252))
        port_risk = float(np.sqrt(max(0, np.dot(weights.values, np.dot(cov, weights.values)))))
        sharpe = port_return / port_risk if port_risk > 1e-8 else 0
        
        violations = self._validate_constraints(weights)
        
        return OptimizationResult(
            weights=weights,
            expected_return=port_return,
            risk=port_risk,
            sharpe_ratio=sharpe,
            constraints_satisfied=len(violations) == 0,
            constraint_violations=violations,
            method="Inverse Volatility",
            optimization_time=time.time() - start_time,
            status="optimal"
        )
