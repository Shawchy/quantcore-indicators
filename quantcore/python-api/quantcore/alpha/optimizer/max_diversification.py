"""
最大分散度优化器

目标：最大化组合的分散化比率。
"""

import numpy as np
import pandas as pd
from scipy.optimize import minimize
from loguru import logger

from .base import BaseOptimizer, OptimizationConstraints, OptimizationResult


class MaxDiversificationOptimizer(BaseOptimizer):
    """
    最大分散度优化器
    
    目标：最大化 D = (w'σ) / (w'Σw)^{1/2}
    
    其中：
    - σ: 各资产波动率向量
    - Σ: 协方差矩阵
    
    分散化比率越高，组合越分散。
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        **kwargs
    ) -> OptimizationResult:
        """执行最大分散度优化"""
        import time
        start_time = time.time()
        
        n_assets = returns.shape[1]
        assets = returns.columns.tolist()
        
        vols = returns.std().values * np.sqrt(252)
        cov = returns.cov().values * 252
        
        w0 = (1 / vols) / (1 / vols).sum()
        
        def neg_diversification_ratio(w):
            """负的分散化比率（用于最小化）"""
            weighted_vol = np.dot(w, vols)
            port_var = np.dot(w, np.dot(cov, w))
            
            if port_var <= 0:
                return 1e10
            
            port_risk = np.sqrt(port_var)
            dr = weighted_vol / port_risk
            
            return -dr
        
        bounds = [(self.constraints.min_position, self.constraints.max_position)] * n_assets
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
        
        try:
            result = minimize(neg_diversification_ratio, w0, method='SLSQP',
                          bounds=bounds, constraints=constraints,
                          options={'maxiter': 1000})
            
            weights = pd.Series(result.x, index=assets)
            port_return = float(np.dot(result.x, returns.mean().values * 252))
            port_risk = float(np.sqrt(max(0, np.dot(result.x, np.dot(cov, result.x)))))
            sharpe = port_return / port_risk if port_risk > 1e-8 else 0
            
            opt_result = OptimizationResult(
                weights=weights,
                expected_return=port_return,
                risk=port_risk,
                sharpe_ratio=sharpe,
                method="Max Diversification",
                optimization_time=time.time() - start_time,
                status="optimal" if result.success else "suboptimal",
                metadata={"diversification_ratio": -float(result.fun)}
            )
            
        except Exception as e:
            logger.error(f"最大分散度优化失败: {e}")
            opt_result = OptimizationResult(
                weights=pd.Series(w0, index=assets),
                method="Max Diversification",
                status="error"
            )
        
        self._last_result = opt_result
        return opt_result


class MinimumCorrelationOptimizer(BaseOptimizer):
    """
    最小相关优化器
    
    目标：最小化组合内资产的平均相关系数。
    """
    
    def optimize(self, returns: pd.DataFrame, **kwargs) -> OptimizationResult:
        """执行最小相关优化"""
        import time
        start_time = time.time()
        
        corr_matrix = returns.corr().values
        n_assets = returns.shape[1]
        assets = returns.columns.tolist()
        
        w0 = np.ones(n_assets) / n_assets
        
        def avg_correlation(w):
            """加权平均相关系数"""
            # 组合内相关性
            weighted_corr = np.dot(w, np.dot(corr_matrix, w))
            # 减去自相关部分
            diag_contribution = np.sum((w**2) * np.diag(corr_matrix))
            avg_corr = (weighted_corr - diag_contribution) / (1 - np.sum(w**2))
            return avg_corr
        
        def objective(w):
            return avg_correlation(w)
        
        bounds = [(0.01, self.constraints.max_position)] * n_assets
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
        
        try:
            result = minimize(objective, w0, method='SLSQP',
                          bounds=bounds, constraints=constraints,
                          options={'maxiter': 1000})
            
            weights = pd.Series(result.x, index=assets)
            cov = returns.cov().values * 252
            port_return = float(np.dot(result.x, returns.mean().values * 252))
            port_risk = float(np.sqrt(max(0, np.dot(result.x, np.dot(cov, result.x)))))
            sharpe = port_return / port_risk if port_risk > 1e-8 else 0
            
            opt_result = OptimizationResult(
                weights=weights,
                expected_return=port_return,
                risk=port_risk,
                sharpe_ratio=sharpe,
                method="Min Correlation",
                optimization_time=time.time() - start_time,
                metadata={"avg_correlation": -float(result.fun)}
            )
            
        except Exception as e:
            opt_result = OptimizationResult(
                weights=pd.Series(w0, index=assets),
                method="Min Correlation",
                status="error"
            )
        
        self._last_result = opt_result
        return opt_result
