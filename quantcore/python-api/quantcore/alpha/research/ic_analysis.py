"""
IC 分析模块

计算因子的信息系数（Information Coefficient），
评估因子预测未来收益的能力。
"""

from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

import numpy as np
import pandas as pd
from scipy import stats


@dataclass
class ICAnalysis:
    """IC 分析结果"""
    factor_name: str
    ic_series: pd.Series = None  # 每日 IC 值
    ic_mean: float = 0.0  # IC 均值
    ic_std: float = 0.0  # IC 标准差
    ic_ir: float = 0.0  # IC 信息比率 (mean/std)
    ic_positive_ratio: float = 0.0  # IC 为正的比例
    rank_ic_mean: float = 0.0  # Rank IC 均值
    rank_ic_ir: float = 0.0  # Rank IC 信息比率
    t_stat: float = 0.0  # t 统计量 (检验IC是否显著不为0)
    p_value: float = 1.0  # p 值
    
    # 统计摘要
    n_observations: int = 0  # 观测数
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    def is_significant(self, alpha: float = 0.05) -> bool:
        """判断 IC 是否统计显著"""
        return self.p_value < alpha and abs(self.ic_mean) > 0.02
    
    def summary(self) -> str:
        """生成分析摘要"""
        sig = "✅ 显著" if self.is_significant() else "❌ 不显著"
        
        return f"""
        ┌─────────────────────────────────────┐
        │         IC 分析结果: {self.factor_name:<12} │
        ├─────────────────────────────────────┤
        │  IC 均值:     {self.ic_mean:>8.4f}            │
        │  IC 标准差:   {self.ic_std:>8.4f}            │
        │  IC IR:       {self.ic_ir:>8.4f}            │
        │  正向比例:     {self.ic_positive_ratio:>7.1%}             │
        │  Rank IC IR:  {self.rank_ic_ir:>8.4f}            │
        │  t-statistic: {self.t_stat:>8.4f}            │
        │  p-value:     {self.p_value:>8.4f}            │
        │  显著性:      {sig:<12}           │
        │  观测数:       {self.n_observations:>6d}              │
        └─────────────────────────────────────┘
        """


class ICCalculator:
    """
    IC 计算器
    
    计算因子与下期收益的相关系数。
    
    支持两种 IC：
    - Pearson IC: 线性相关系数
    - Rank IC (Spearman): 秩相关系数，更稳健
    """
    
    @staticmethod
    def calculate(
        factor_values: pd.Series,
        forward_returns: pd.Series,
        method: str = "pearson"
    ) -> float:
        """
        计算 IC
        
        Args:
            factor_values: 因子值序列
            forward_returns: 下期收益率序列
            method: 相关方法 (pearson/spearman)
            
        Returns:
            IC 值
        """
        # 对齐数据
        common_idx = factor_values.dropna().index.intersection(
            forward_returns.dropna().index
        )
        
        if len(common_idx) < 10:
            return np.nan
        
        f = factor_values.loc[common_idx]
        r = forward_returns.loc[common_idx]
        
        try:
            if method == "spearman":
                ic, _ = stats.spearmanr(f, r)
            else:
                ic, _ = stats.pearsonr(f, r)
            
            return ic
            
        except Exception:
            return np.nan
    
    @staticmethod
    def calculate_series(
        factor_data: pd.DataFrame,
        returns_data: pd.DataFrame,
        forward_period: int = 1,
        method: str = "pearson"
    ) -> ICAnalysis:
        """
        计算时间序列 IC
        
        Args:
            factor_data: 因子数据 (symbol × date)
            returns_data: 收益率数据 (symbol × date)
            forward_period: 前瞻期数
            method: 相关方法
            
        Returns:
            ICAnalysis: 完整的 IC 分析结果
        """
        ic_list = []
        rank_ic_list = []
        
        common_dates = sorted(
            set(factor_data.columns).intersection(set(returns_data.columns))
        )
        
        for i in range(len(common_dates) - forward_period):
            current_date = common_dates[i]
            future_date = common_dates[i + forward_period]
            
            if current_date not in factor_data.columns or future_date not in returns_data.columns:
                continue
            
            factors = factor_data[current_date].dropna()
            future_ret = returns_data[future_date].dropna()
            
            common_symbols = factors.index.intersection(future_ret.index)
            
            if len(common_symbols) < 10:
                continue
            
            f = factors.loc[common_symbols]
            r = future_ret.loc[common_symbols]
            
            # Pearson IC
            try:
                pearson_ic, _ = stats.pearsonr(f, r)
                ic_list.append(pearson_ic)
            except Exception:
                pass
            
            # Spearman IC (Rank IC)
            try:
                spearman_ic, _ = stats.spearmanr(f, r)
                rank_ic_list.append(spearman_ic)
            except Exception:
                pass
        
        ic_series = pd.Series(ic_list, index=common_dates[:len(ic_list)])
        rank_ic_series = pd.Series(rank_ic_list, index=common_dates[:len(rank_ic_list)])
        
        # 计算统计量
        ic_mean = ic_series.mean() if len(ic_series) > 0 else 0
        ic_std = ic_series.std() if len(ic_series) > 0 else 0
        ic_ir = ic_mean / ic_std if ic_std > 0 else 0
        
        rank_ic_mean = rank_ic_series.mean() if len(rank_ic_series) > 0 else 0
        rank_ic_std = rank_ic_series.std() if len(rank_ic_series) > 0 else 0
        rank_ic_ir = rank_ic_mean / rank_ic_std if rank_ic_std > 0 else 0
        
        # t 检验
        n = len(ic_series)
        t_stat = ic_mean * np.sqrt(n) / ic_std if ic_std > 0 else 0
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n-1)) if n > 1 else 1.0
        
        positive_ratio = (ic_series > 0).sum() / len(ic_series) if len(ic_series) > 0 else 0
        
        result = ICAnalysis(
            factor_name="factor",
            ic_series=ic_series,
            ic_mean=float(ic_mean),
            ic_std=float(ic_std),
            ic_ir=float(ic_ir),
            ic_positive_ratio=float(positive_ratio),
            rank_ic_mean=float(rank_ic_mean),
            rank_ic_ir=float(rank_ic_ir),
            t_stat=float(t_stat),
            p_value=float(p_value),
            n_observations=n,
            start_date=ic_series.index.min() if len(ic_series) > 0 else None,
            end_date=ic_series.index.max() if len(ic_series) > 0 else None
        )
        
        return result
    
    @staticmethod
    def calculate_decay(
        factor_data: pd.DataFrame,
        returns_data: pd.DataFrame,
        max_period: int = 20
    ) -> pd.DataFrame:
        """
        计算因子衰减曲线
        
        分析因子预测能力随时间的变化。
        
        Args:
            factor_data: 因子数据
            returns_data: 收益率数据
            max_period: 最大前瞻期
            
        Returns:
            DataFrame: 各期的 IC 统计
        """
        results = []
        
        for period in range(1, max_period + 1):
            ic_result = ICCalculator.calculate_series(
                factor_data, returns_data, 
                forward_period=period
            )
            
            results.append({
                "period": period,
                "ic_mean": ic_result.ic_mean,
                "ic_ir": ic_result.ic_ir,
                "positive_ratio": ic_result.ic_positive_ratio,
                "is_significant": ic_result.is_significant()
            })
        
        return pd.DataFrame(results)
