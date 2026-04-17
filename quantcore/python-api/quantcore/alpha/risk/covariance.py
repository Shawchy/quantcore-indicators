"""
协方差矩阵估计模块

提供多种协方差估计方法：
- EWMA (指数加权)
- Simple (简单滚动)
- Newey-West (异方差稳健)
"""

import numpy as np
import pandas as pd
from typing import Optional


class CovarianceEstimator:
    """
    协方差矩阵估计器
    
    支持多种估计方法，用于 Barra 风险模型。
    """
    
    @staticmethod
    def ewma_covariance(
        returns: pd.DataFrame,
        lambda_decay: float = 0.94,
        min_observations: int = 60
    ) -> pd.DataFrame:
        """
        EWMA (指数加权移动平均) 协方差
        
        近期数据权重更高，适合捕捉时变波动。
        
        Args:
            returns: 因子收益率矩阵 (T × N)
            lambda_decay: 衰减因子（默认 0.94）
            min_observations: 最小观测数
            
        Returns:
            DataFrame: 协方差矩阵 (N × N)
        """
        n = len(returns)
        
        if n < min_observations:
            # 数据不足，返回简单协方差
            return returns.cov()
        
        weights = np.array([lambda_decay ** (n - 1 - i) for i in range(n)])
        weights = weights / weights.sum()
        
        mean = returns.mean()
        centered = returns - mean
        
        p = returns.shape[1]
        cov_matrix = np.zeros((p, p))
        
        for i in range(n):
            r = centered.iloc[i].values.reshape(-1, 1)
            cov_matrix += weights[i] * (r @ r.T)
        
        return pd.DataFrame(
            cov_matrix,
            index=returns.columns,
            columns=returns.columns
        )
    
    @staticmethod
    def simple_covariance(
        returns: pd.DataFrame,
        window: int = 252,
        annualize: bool = True
    ) -> pd.DataFrame:
        """
        简单滚动窗口协方差
        
        Args:
            returns: 收益率矩阵
            window: 回看窗口
            annualize: 是否年化
            
        Returns:
            DataFrame: 协方差矩阵
        """
        cov = returns.tail(window).cov()
        
        if annualize:
            cov = cov * 252
        
        return cov
    
    @staticmethod
    def shrinkage_covariance(
        returns: pd.DataFrame,
        shrinkage_target: str = "constant",
        shrinkage_intensity: Optional[float] = None
    ) -> pd.DataFrame:
        """
        收缩估计 (Ledoit-Wolf)
        
        在样本协方差和目标之间进行收缩，
        降低估计误差。
        
        Args:
            returns: 收益率矩阵
            shrinkage_target: 目标类型 ("constant", "identity", "single_factor")
            shrinkage_intensity: 收缩强度 (None=自动计算)
            
        Returns:
            DataFrame: 收缩后的协方差矩阵
        """
        sample_cov = returns.cov()
        n, p = returns.shape
        
        if shrinkage_target == "identity":
            target = np.eye(p) * np.trace(sample_cov.values) / p
        
        elif shrinkage_target == "constant":
            mean_var = np.diag(sample_cov).mean()
            target = np.eye(p) * mean_var
        
        elif shrinkage_target == "single_factor":
            # 单因子模型：市场因子解释所有协方差
            avg_return = returns.mean(axis=1)
            beta = returns.cov().dot(avg_return) / avg_return.var() if avg_return.var() > 0 else np.zeros(p)
            target = np.outer(beta, beta) * avg_return.var()
            
            # 对角线用样本值
            np.fill_diagonal(target, np.diag(sample_cov.values))
        
        else:
            raise ValueError(f"未知收缩目标: {shrinkage_target}")
        
        # 计算最优收缩强度（简化版）
        if shrinkage_intensity is None:
            # Ledoit-Wolf 简化公式
            sum_sq = ((sample_cov - target)**2).sum().sum()
            if sum_sq > 0:
                shrinkage_intensity = max(0, min(1, (n * p) / (n**2 * sum_sq)))
            else:
                shrinkage_intensity = 1.0
        
        shrunk_cov = shrinkage_intensity * target + (1 - shrinkage_intensity) * sample_cov.values
        
        return pd.DataFrame(
            shrunk_cov,
            index=sample_cov.index,
            columns=sample_cov.columns
        )
    
    @staticmethod
    def correlation_from_covariance(cov_matrix: pd.DataFrame) -> pd.DataFrame:
        """从协方差矩阵计算相关系数矩阵"""
        std = np.sqrt(np.diag(cov_matrix.values))
        
        if any(std == 0):
            std[std == 0] = 1.0
        
        corr = cov_matrix / np.outer(std, std)
        return corr.clip(-1, 1)


class SpecificRiskEstimator:
    """
    特质风险估计器
    
    估计无法被风格/行业因子解释的个股特有风险。
    """
    
    @staticmethod
    def estimate(
        residual_returns: pd.DataFrame,
        method: str = "historical",
        window: int = 60
    ) -> pd.Series:
        """
        估计特质风险
        
        Args:
            residual_returns: 残差收益率 (date × symbol)
            method: 估计方法 ("historical"/"structural")
            window: 回看窗口
            
        Returns:
            Series: 各股票特质风险（年化波动率）
        """
        if method == "historical":
            vol = residual_returns.tail(window).std() * np.sqrt(252)
            return vol.clip(lower=0.05, upper=3.0)
        
        elif method == "structural":
            # 基于结构化模型的特质风险估计
            # 需要额外信息（市值、流动性等）
            vol = residual_returns.tail(window).std() * np.sqrt(252)
            return vol.clip(lower=0.05, upper=3.0)
        
        else:
            raise ValueError(f"未知方法: {method}")
    
    @staticmethod
    def estimate_with_adjustments(
        residual_returns: pd.DataFrame,
        market_cap: pd.Series,
        turnover: Optional[pd.Series] = None,
        window: int = 60
    ) -> pd.Series:
        """
        带调整的特质风险估计
        
        小市值、低流动性的股票通常有更高的特质风险。
        """
        base_risk = residual_returns.tail(window).std() * np.sqrt(252)
        
        # 市值调整：小市值股票风险更高
        log_cap = np.log(market_cap.clip(lower=1e6))
        cap_z = (log_cap - log_cap.mean()) / log_cap.std()
        cap_adj = 1.0 + 0.3 * cap_z  # 小市值增加风险
        
        adjusted_risk = base_risk * cap_adj
        
        # 流动性调整：低流动性增加风险
        if turnover is not None:
            turnover_z = (turnover - turnover.mean()) / turnover.std()
            liq_adj = 1.0 - 0.2 * turnover_z  # 低流动性增加风险
            adjusted_risk = adjusted_risk / liq_adj.replace(0, 1)
        
        return adjusted_risk.clip(lower=0.05, upper=5.0)
