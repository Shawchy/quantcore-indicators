"""
因子约束优化器

在组合优化中加入 Barra 风格因子的暴露约束。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
from scipy.optimize import minimize
from loguru import logger

from .base import BaseOptimizer, OptimizationConstraints, OptimizationResult


class FactorConstrainedOptimizer(BaseOptimizer):
    """
    因子约束优化器
    
    在均值-方差优化的基础上，增加：
    - 风格因子暴露约束（如 Beta、Size 中性化）
    - 行业中性约束
    - 最大/最小因子暴露限制
    
    使用示例：
        optimizer = FactorConstrainedOptimizer(
            constraints=OptimizationConstraints(
                factor_neutral=True,
                max_factor_exposure={"BETA": (-0.1, 0.1), "SIZE": (-0.2, 0.2)}
            )
        )
        result = optimizer.optimize(returns_data, factor_exposures=exposure_df)
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        factor_exposures: Optional[pd.DataFrame] = None,
        industry_map: Optional[Dict[str, str]] = None,
        risk_aversion: float = 1.0,
        **kwargs
    ) -> OptimizationResult:
        """
        执行带因子约束的优化
        
        Args:
            returns: 资产收益率数据
            factor_exposures: 因子暴露矩阵 (asset × factor)
            industry_map: {asset: industry} 映射
            risk_aversion: 风险厌恶系数
            
        Returns:
            OptimizationResult: 优化结果
        """
        import time
        start_time = time.time()
        
        n_assets = returns.shape[1]
        assets = returns.columns.tolist()
        
        mu = returns.mean().values * 252
        cov = returns.cov().values * 252
        
        w0 = np.ones(n_assets) / n_assets
        
        # 构建约束条件列表
        constraints_list = [
            {'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}
        ]
        
        # 因子暴露约束
        if factor_exposures is not None:
            common_factors = [f for f in factor_exposures.columns 
                            if f in self.constraints.max_factor_exposure]
            
            for factor_name in common_factors:
                min_exp, max_exp = self.constraints.max_factor_exposure[factor_name]
                
                if factor_name in factor_exposures.columns:
                    f_values = factor_exposures[factor_name].reindex(assets).fillna(0).values
                    
                    constraints_list.append({
                        'type': 'ineq',
                        'fun': lambda w, fv=f_values, mn=min_exp: np.dot(w, fv) - mn
                    })
                    
                    constraints_list.append({
                        'type': 'ineq',
                        'fun': lambda w, fv=f_values, mx=max_exp: mx - np.dot(w, fv)
                    })
            
            # 完全中性化（如果设置）
            if self.constraints.factor_neutral:
                for factor_name in factor_exposures.columns[:5]:  # 主要风格因子
                    f_values = factor_exposures[factor_name].reindex(assets).fillna(0).values
                    
                    constraints_list.append({
                        'type': 'eq',
                        'fun': lambda w, fv=f_values: np.dot(w, fv),
                        "name": f"neutral_{factor_name}"
                    })
        
        # 行业中性约束
        if self.constraints.industry_neutral and industry_map is not None:
            industries = set(industry_map.values())
            
            for industry in industries:
                mask = np.array([1.0 if industry_map.get(a) == industry else 0.0 
                               for a in assets])
                
                if mask.sum() > 0:
                    # 目标：行业权重等于市场权重（假设等权）
                    target_weight = mask.sum() / n_assets
                    
                    constraints_list.append({
                        'type': 'ineq',
                        'fun': lambda w, m=mask, tw=target_weight: (np.dot(w, m) - tw) - 0.05
                    })
                    constraints_list.append({
                        'type': 'ineq',
                        'fun': lambda w, m=mask, tw=target_weight: tw - (np.dot(w, m) + 0.05)
                    })
        
        bounds = [(0, self.constraints.max_position)] * n_assets
        
        def objective(w):
            port_return = np.dot(w, mu)
            port_var = np.dot(w, np.dot(cov, w))
            return -(port_return - risk_aversion / 2 * port_var)
        
        try:
            result = minimize(objective, w0, method='SLSQP',
                          bounds=bounds, constraints=constraints_list,
                          options={'maxiter': 1000})
            
            weights = pd.Series(result.x, index=assets)
            
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
                method="Factor Constrained",
                optimization_time=time.time() - start_time,
                iterations=result.nit,
                status="optimal" if result.success else "suboptimal"
            )
            
        except Exception as e:
            logger.error(f"因子约束优化失败: {e}")
            opt_result = OptimizationResult(
                weights=pd.Series(w0, index=assets),
                method="Factor Constrained",
                status="error"
            )
        
        self._last_result = opt_result
        return opt_result
    
    def calculate_factor_exposures(
        self,
        weights: pd.Series,
        factor_exposures: pd.DataFrame
    ) -> Dict[str, float]:
        """计算组合的因子暴露"""
        exposures = {}
        
        for factor in factor_exposures.columns:
            common_idx = weights.index.intersection(factor_exposures.index)
            if len(common_idx) > 0:
                exposure = (weights.loc[common_idx] * 
                           factor_exposures.loc[common_idx, factor]).sum()
                exposures[factor] = float(exposure)
        
        return exposures
