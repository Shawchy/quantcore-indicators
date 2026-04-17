"""
Black-Litterman 优化器

将投资者观点与市场均衡收益结合的贝叶斯方法。
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from scipy.optimize import minimize
from loguru import logger

from .base import BaseOptimizer, OptimizationConstraints, OptimizationResult


class BlackLittermanOptimizer(BaseOptimizer):
    """
    Black-Litterman 优化器
    
    将主观观点与市场均衡结合，生成更稳健的预期收益。
    
    核心公式：
        E[R] = [(τΣ)^{-1} + P'Ω^{-1}P]^{-1} × [(τΣ)^{-1}Π + P'Ω^{-1}Q]
    
    其中：
        - Π: 均衡收益（隐含收益）
        - Σ: 协方差矩阵
        - P: 观点选取矩阵
        - Q: 观点收益向量
        - Ω: 观点不确定性矩阵
        - τ: 缩放参数
    
    使用示例：
        bl = BlackLittermanOptimizer()
        
        # 设置观点
        views = [
            {"assets": ["AAPL", "MSFT"], "view": [0.02, 0.01], "confidence": 0.7}
        ]
        
        result = bl.optimize(returns_data, views=views)
    """
    
    def optimize(
        self,
        returns: pd.DataFrame,
        views: List[Dict[str, Any]] = None,
        tau: float = 0.05,
        risk_aversion: float = 1.0,
        **kwargs
    ) -> OptimizationResult:
        """
        执行 Black-Litterman 优化
        
        Args:
            returns: 资产收益率数据
            views: 投资者观点列表
            tau: 缩放参数（均衡收益的不确定性）
            risk_aversion: 风险厌恶系数
            
        Returns:
            OptimizationResult: 优化结果
        """
        import time
        start_time = time.time()
        
        n_assets = returns.shape[1]
        assets = returns.columns.tolist()
        
        # 计算市场参数
        mu_hist = returns.mean().values * 252
        cov = returns.cov().values * 252
        
        # 计算均衡收益（隐含收益）
        # Π = δ × Σ × w_mkt (简化：假设等权)
        delta = 2.5  # 风险厌恶系数
        w_mkt = np.ones(n_assets) / n_assets
        pi = np.dot(cov, w_mkt) * delta
        
        if views is None:
            # 无观点，退化为均值-方差
            bl_returns = mu_hist.copy()
            logger.info("无观点输入，使用历史收益")
        else:
            # 处理观点，计算 BL 收益
            bl_returns = self._blend_views(
                pi, cov, views, tau, assets
            )
        
        # 使用 BL 收益进行均值-方差优化
        w0 = np.ones(n_assets) / n_assets
        
        def objective(w):
            port_return = np.dot(w, bl_returns)
            port_var = np.dot(w, np.dot(cov, w))
            return -(port_return - risk_aversion / 2 * port_var)
        
        bounds = [(0, self.constraints.max_position)] * n_assets
        constraints = [{'type': 'eq', 'fun': lambda w: np.sum(w) - 1.0}]
        
        try:
            result = minimize(objective, w0, method='SLSQP',
                          bounds=bounds, constraints=constraints,
                          options={'maxiter': 1000})
            
            weights = pd.Series(result.x, index=assets)
            
            port_return = float(np.dot(result.x, bl_returns))
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
                method="Black-Litterman",
                optimization_time=time.time() - start_time,
                iterations=result.nit,
                status="optimal" if result.success else "suboptimal",
                metadata={
                    "equilibrium_returns": dict(zip(assets, pi)),
                    "bl_returns": dict(zip(assets, bl_returns)),
                    "n_views": len(views) if views else 0
                }
            )
            
        except Exception as e:
            logger.error(f"BL 优化失败: {e}")
            opt_result = OptimizationResult(
                weights=pd.Series(w0, index=assets),
                method="Black-Litterman",
                status="error"
            )
        
        self._last_result = opt_result
        return opt_result
    
    def _blend_views(
        self,
        pi: np.ndarray,
        cov: np.ndarray,
        views: List[Dict[str, Any]],
        tau: float,
        assets: List[str]
    ) -> np.ndarray:
        """
        将观点与均衡收益融合
        
        Args:
            pi: 均衡收益向量
            cov: 协方差矩阵
            views: 观点列表
            tau: 缩放参数
            assets: 资产列表
            
        Returns:
            ndarray: BL 调整后的预期收益
        """
        n_assets = len(assets)
        asset_map = {name: i for i, name in enumerate(assets)}
        
        # 构建观点矩阵
        P_list = []
        Q_list = []
        omega_list = []
        
        for view in views:
            view_assets = view.get("assets", [])
            view_values = view.get("view", [])
            confidence = view.get("confidence", 0.5)
            
            # 构建行向量 P
            p = np.zeros(n_assets)
            for asset, value in zip(view_assets, view_values):
                if asset in asset_map:
                    p[asset_map[asset]] = value
            
            # 归一化（相对观点）
            if p.sum() != 0 and len(view_assets) > 1:
                p[p != 0] = p[p != 0] / abs(p[p != 0]).sum()
                q = abs(view_values[0])  # 绝对收益观点
            
            elif len(view_assets) == 1:
                q = view_values[0]
            else:
                continue
            
            P_list.append(p)
            Q_list.append(q)
            
            # 观点不确定性 Ω = diag(p × Σ × p') / confidence^2
            p_cov = np.outer(p, np.dot(cov, p))
            omega = p_cov.sum() / (confidence **2 + 1e-8)
            omega_list.append(max(omega, 1e-6))  # 下限
        
        if not P_list:
            return pi
        
        P_matrix = np.array(P_list)
        Q_vector = np.array(Q_list)
        Omega_inv = np.diag(1.0 / np.array(omega_list))
        
        # BL 公式
        tau_cov_inv = np.linalg.inv(tau * cov + 1e-8 * np.eye(n_assets))
        
        M1 = tau_cov_inv + P_matrix.T @ Omega_inv @ P_matrix
        M2 = tau_cov_inv @ pi + P_matrix.T @ Omega_inv @ Q_vector
        
        try:
            bl_returns = np.linalg.solve(M1, M2)
        except np.linalg.LinAlgError:
            bl_returns = pi  # fallback
        
        return bl_returns
    
    def add_view(
        self,
        assets: List[str],
        view_type: str = "relative",
        **kwargs
    ) -> Dict[str, Any]:
        """
        辅助函数：创建标准观点格式
        
        Args:
            assets: 涉及资产
            view_type: "absolute" 或 "relative"
            **kwargs: 视点参数
            
        Returns:
            Dict: 观点字典
        """
        if view_type == "absolute":
            return {
                "assets": assets,
                "view": kwargs.get("expected_returns", []),
                "confidence": kwargs.get("confidence", 0.5)
            }
        else:
            return {
                "assets": assets,
                "view": kwargs.get("outperformance", []),
                "confidence": kwargs.get("confidence", 0.5)
            }


class EqualWeightContributionOptimizer(BaseOptimizer):
    """
    等风险贡献优化器的简化版本
    
    直接最小化风险贡献差异，不依赖梯度计算。
    """
    
    def optimize(self, returns: pd.DataFrame, **kwargs) -> OptimizationResult:
        """执行等风险贡献优化"""
        rp_optimizer = RiskParityOptimizer(constraints=self.constraints)
        result = rp_optimizer.optimize(returns)
        result.method = "Equal Risk Contribution"
        self._last_result = result
        return result
