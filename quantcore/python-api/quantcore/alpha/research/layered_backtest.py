"""
分层回测模块

将股票按因子值分层，测试各层收益差异。
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime

import numpy as np
import pandas as pd


@dataclass
class LayeredBacktestResult:
    """分层回测结果"""
    factor_name: str
    n_layers: int = 5
    layer_returns: pd.DataFrame = None  # 各层日收益
    long_short_return: pd.Series = None  # 多空收益
    cumulative_returns: pd.DataFrame = None  # 累计收益
    
    # 统计指标
    long_short_annualized_return: float = 0.0
    long_short_sharpe: float = 0.0
    long_short_max_drawdown: float = 0.0
    win_rate: float = 0.0
    
    n_observations: int = 0
    
    def summary(self) -> str:
        """生成摘要"""
        return f"""
        ┌──────────────────────────────────────┐
        │   分层回测结果: {self.factor_name:<14} │
        ├──────────────────────────────────────┤
        │  分层数:       {self.n_layers:>6d}              │
        │  多空年化收益: {self.long_short_annualized_return:>8.2%}          │
        │  多空夏普比率: {self.long_short_sharpe:>8.2f}           │
        │  多空最大回撤: {self.long_short_max_drawdown:>8.2%}          │
        │  胜率:         {self.win_rate:>7.1%}            │
        └──────────────────────────────────────┘
        """


class LayeredBacktester:
    """
    分层回测器
    
    将股票按因子值分为 N 层，测试各层的收益表现，
    验证因子的选股能力。
    
    使用示例：
        tester = LayeredBacktester()
        result = tester.run(factor_data, returns_data, n_layers=5)
        print(result.summary())
    """
    
    def run(
        self,
        factor_data: pd.DataFrame,
        returns_data: pd.DataFrame,
        n_layers: int = 5,
        long_top: bool = True,
        weight_method: str = "equal"
    ) -> LayeredBacktestResult:
        """
        运行分层回测
        
        Args:
            factor_data: 因子数据 (symbol × date)
            returns_data: 收益率数据 (symbol × date)
            n_layers: 分层数
            long_top: 是否做多顶层（因子值最大的）
            weight_method: 权重方法 (equal/value)
            
        Returns:
            LayeredBacktestResult: 回测结果
        """
        common_dates = sorted(
            set(factor_data.columns).intersection(set(returns_data.columns))
        )
        
        if len(common_dates) < 2:
            return LayeredBacktestResult(factor_name="factor")
        
        layer_returns_list = []
        long_short_returns = []
        
        for i in range(len(common_dates) - 1):
            current_date = common_dates[i]
            future_date = common_dates[i + 1]
            
            if current_date not in factor_data.columns or future_date not in returns_data.columns:
                continue
            
            factors = factor_data[current_date].dropna()
            future_ret = returns_data[future_date].dropna()
            
            common_symbols = factors.index.intersection(future_ret.index)
            
            if len(common_symbols) < n_layers * 10:
                continue
            
            f = factors.loc[common_symbols]
            r = future_ret.loc[common_symbols]
            
            # 按因子值分层
            f_rank = f.rank(pct=True)
            
            layer_ret = []
            for j in range(n_layers):
                lower = j / n_layers
                upper = (j + 1) / n_layers
                
                if j == n_layers - 1:
                    mask = (f_rank >= lower) & (f_rank <= upper)
                else:
                    mask = (f_rank >= lower) & (f_rank < upper)
                
                layer_stocks = f_rank[mask].index
                
                if len(layer_stocks) > 0 and weight_method == "equal":
                    layer_r = r[layer_stocks].mean()
                elif len(layer_stocks) > 0:
                    weights = f.loc[layer_stocks] / f.loc[layer_stocks].sum()
                    layer_r = (r[layer_stocks] * weights).sum()
                else:
                    layer_r = 0.0
                
                layer_ret.append(layer_r)
            
            layer_returns_list.append(layer_ret)
            
            # 多空收益
            if long_top:
                ls_ret = layer_ret[-1] - layer_ret[0]  # 做多顶层，做空底层
            else:
                ls_ret = layer_ret[0] - layer_ret[-1]  # 做多底层，做空顶层
            
            long_short_returns.append(ls_ret)
        
        # 转换为 DataFrame
        dates = common_dates[:len(layer_returns_list)]
        layer_df = pd.DataFrame(
            layer_returns_list, 
            columns=[f'Layer_{i+1}' for i in range(n_layers)],
            index=dates
        )
        
        ls_series = pd.Series(long_short_returns, index=dates)
        
        # 计算累计收益
        cumulative = (1 + layer_df).cumprod()
        
        # 计算统计指标
        annualized_return = ls_series.mean() * 252
        sharpe = ls_series.mean() / ls_series.std() * np.sqrt(252) if ls_series.std() > 0 else 0
        
        # 最大回撤
        cum_ls = (1 + ls_series).cumprod()
        rolling_max = cum_ls.cummax()
        drawdown = (cum_ls - rolling_max) / rolling_max
        max_dd = drawdown.min()
        
        # 胜率
        win_rate = (ls_series > 0).sum() / len(ls_series) if len(ls_series) > 0 else 0
        
        return LayeredBacktestResult(
            factor_name="factor",
            n_layers=n_layers,
            layer_returns=layer_df,
            long_short_return=ls_series,
            cumulative_returns=cumulative,
            long_short_annualized_return=float(annualized_return),
            long_short_sharpe=float(sharpe),
            long_short_max_drawdown=float(max_dd),
            win_rate=float(win_rate),
            n_observations=len(ls_series)
        )
    
    @staticmethod
    def calculate_monotonicity(layer_returns: pd.DataFrame) -> float:
        """
        计算分层收益的单调性
        
        单调性越高，因子选股能力越强。
        
        Args:
            layer_returns: 各层收益 DataFrame
            
        Returns:
            float: 单调性得分 (0-1)
        """
        mean_returns = layer_returns.mean()
        
        # 检查是否单调递增或递减
        diffs = mean_returns.diff().dropna()
        
        if len(diffs) == 0:
            return 0.0
        
        # 计算单调方向一致性
        positive_count = (diffs > 0).sum()
        negative_count = (diffs < 0).sum()
        
        monotonicity = max(positive_count, negative_count) / len(diffs)
        
        return monotonicity
