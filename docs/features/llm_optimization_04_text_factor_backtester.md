# 优化模块 4: 文本因子回测验证框架

## 📊 设计概述

### 问题背景

新增 LLM 文本因子后，必须科学验证其有效性:
- **不能盲目使用**: 需要证明因子有预测能力
- **需要量化收益**: 具体能提升多少年化收益
- **需要控制风险**: 不能引入额外风险
- **需要独立性检验**: 不是传统因子的重复

### 解决方案

设计**完整的因子回测验证框架**，实现:
- ✅ IC 分析 (信息系数)
- ✅ 分层回测 (十分组)
- ✅ 风险调整收益 (夏普/回撤)
- ✅ 因子独立性检验
- ✅ 消融实验 (逐个移除)
- ✅ 稳定性检验 (时间/横截面)

---

## 🏗️ 回测验证流程

```
┌─────────────────────────────────────────────────────────┐
│              因子数据准备                                 │
│                                                         │
│  输入:                                                   │
│  - LLM 文本因子 (日期 × 股票)                           │
│  - 股票收益率 (日期 × 股票)                             │
│  - 传统因子数据 (可选)                                   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Step 1: IC 分析                             │
│                                                         │
│  计算:                                                   │
│  - 每日 IC (因子值与下期收益的相关性)                    │
│  - IC 均值 (应 > 0.03)                                 │
│  - ICIR (IC 均值 / IC 标准差，应 > 0.5)                 │
│  - T 值 (IC 均值 / (IC 标准差 / √N)，应 > 2.0)         │
│  - IC > 0 的比例 (应 > 55%)                             │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Step 2: 分层回测                             │
│                                                         │
│  方法:                                                   │
│  1. 每日按因子值排序，分为 10 组 (Q1-Q10)                │
│  2. 计算每组下期平均收益                                  │
│  3. 绘制各组收益曲线                                     │
│  4. 检验单调性 (Q10 - Q1 > 0)                           │
│                                                         │
│  标准:                                                   │
│  - 多空收益 (Q10-Q1) > 10%/年                           │
│  - 单调性: Q1 < Q2 < ... < Q10                          │
│  - 最高组收益 > 基准                                     │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Step 3: 风险调整收益                         │
│                                                         │
│  构建多空组合:                                           │
│  - 做多 Q10 (因子值最高)                                │
│  - 做空 Q1 (因子值最低)                                 │
│                                                         │
│  计算指标:                                               │
│  - 年化收益 (应 > 10%)                                  │
│  - 年化波动率 (应 < 20%)                                │
│  - 夏普比率 (应 > 1.0)                                  │
│  - 最大回撤 (应 < 20%)                                  │
│  - Calmar 比率 (年化收益 / 最大回撤，应 > 1.0)          │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Step 4: 因子独立性检验                       │
│                                                         │
│  相关性分析:                                             │
│  - 与市值因子相关性 (应 < 0.7)                          │
│  - 与动量因子相关性 (应 < 0.7)                          │
│  - 与价值因子相关性 (应 < 0.7)                          │
│                                                         │
│  回归分析:                                               │
│  - 基准模型 (传统因子) R²                               │
│  - 完整模型 (传统因子 + 文本因子) R²                    │
│  - 增量 R² = 完整 R² - 基准 R² (应 > 5%)               │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              Step 5: 消融实验                             │
│                                                         │
│  方法:                                                   │
│  1. 完整模型: 所有因子                                   │
│  2. 移除文本因子: 观察性能下降                           │
│  3. 移除其他因子: 对比影响                               │
│                                                         │
│  结论:                                                   │
│  - 文本因子贡献度 = (完整 - 移除文本) / 完整             │
│  - 如果贡献度 > 10%，说明因子有效                        │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│              生成验证报告                                 │
│                                                         │
│  输出:                                                   │
│  - FactorValidationReport (结构化数据)                   │
│  - 可视化图表 (IC 趋势、分层收益、资金曲线)              │
│  - 结论与建议 (通过/不通过/需优化)                       │
└─────────────────────────────────────────────────────────┘
```

---

## 💻 核心代码设计

### 1. IC 分析器

```python
# quantcore/alpha/research/ic_analyzer.py

from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats
from loguru import logger


@dataclass
class ICResult:
    """IC 分析结果"""
    # 核心指标
    ic_mean: float  # IC 均值
    ic_std: float  # IC 标准差
    icir: float  # 信息比率 (IC 均值 / IC 标准差)
    t_value: float  # T 值
    ic_positive_rate: float  # IC > 0 的比例
    
    # 详细数据
    daily_ic: pd.Series  # 每日 IC
    ic_distribution: Dict[str, float]  # IC 分位数
    
    # 统计检验
    p_value: float  # P 值
    is_significant: bool  # 是否显著 (p < 0.05)
    
    def summary(self) -> str:
        """生成摘要"""
        return (
            f"IC 分析报告:\n"
            f"  IC 均值: {self.ic_mean:.4f}\n"
            f"  IC 标准差: {self.ic_std:.4f}\n"
            f"  ICIR: {self.icir:.4f}\n"
            f"  T 值: {self.t_value:.2f}\n"
            f"  IC>0 比例: {self.ic_positive_rate:.1%}\n"
            f"  P 值: {self.p_value:.4f}\n"
            f"  显著性: {'是' if self.is_significant else '否'}"
        )


class ICAnalyzer:
    """IC 分析器"""
    
    def analyze(
        self,
        factor_data: pd.DataFrame,
        return_data: pd.DataFrame,
        forward_days: int = 1
    ) -> ICResult:
        """
        执行 IC 分析
        
        Args:
            factor_data: 因子数据 (日期 × 股票)
            return_data: 收益率数据 (日期 × 股票)
            forward_days: 前向天数 (计算因子与未来收益的相关性)
        
        Returns:
            ICResult: IC 分析结果
        """
        logger.info("开始 IC 分析...")
        
        # 对齐数据
        factor_data, return_data = self._align_data(
            factor_data, return_data, forward_days
        )
        
        # 计算每日 IC
        daily_ic = self._calculate_daily_ic(
            factor_data, return_data
        )
        
        # 计算统计指标
        ic_mean = daily_ic.mean()
        ic_std = daily_ic.std()
        icir = ic_mean / ic_std if ic_std > 0 else 0
        t_value = ic_mean / (ic_std / np.sqrt(len(daily_ic))) if ic_std > 0 else 0
        ic_positive_rate = (daily_ic > 0).sum() / len(daily_ic)
        
        # T 检验
        t_stat, p_value = stats.ttest_1samp(daily_ic.dropna(), 0)
        
        # IC 分布
        ic_distribution = {
            "min": daily_ic.min(),
            "q25": daily_ic.quantile(0.25),
            "median": daily_ic.median(),
            "q75": daily_ic.quantile(0.75),
            "max": daily_ic.max(),
        }
        
        result = ICResult(
            ic_mean=ic_mean,
            ic_std=ic_std,
            icir=icir,
            t_value=t_value,
            ic_positive_rate=ic_positive_rate,
            daily_ic=daily_ic,
            ic_distribution=ic_distribution,
            p_value=p_value,
            is_significant=p_value < 0.05,
        )
        
        logger.info(result.summary())
        
        return result
    
    def _align_data(
        self,
        factor_data: pd.DataFrame,
        return_data: pd.DataFrame,
        forward_days: int
    ) -> tuple:
        """对齐因子和收益率数据"""
        # 将收益率向前偏移 (因子预测未来收益)
        return_shifted = return_data.shift(-forward_days)
        
        # 对齐日期和股票
        common_dates = factor_data.index.intersection(
            return_shifted.index
        )
        common_cols = factor_data.columns.intersection(
            return_shifted.columns
        )
        
        factor_aligned = factor_data.loc[common_dates, common_cols]
        return_aligned = return_shifted.loc[common_dates, common_cols]
        
        # 删除 NaN
        mask = factor_aligned.notna() & return_aligned.notna()
        factor_aligned = factor_aligned.where(mask)
        return_aligned = return_aligned.where(mask)
        
        return factor_aligned, return_aligned
    
    def _calculate_daily_ic(
        self,
        factor_data: pd.DataFrame,
        return_data: pd.DataFrame
    ) -> pd.Series:
        """计算每日 IC (Rank IC)"""
        daily_ic = []
        dates = []
        
        for date in factor_data.index:
            factor_values = factor_data.loc[date].dropna()
            return_values = return_data.loc[date].dropna()
            
            # 取交集
            common_stocks = factor_values.index.intersection(
                return_values.index
            )
            
            if len(common_stocks) < 10:  # 样本太少，跳过
                continue
            
            factor = factor_values[common_stocks]
            returns = return_values[common_stocks]
            
            # 计算 Rank IC (Spearman 相关系数)
            ic = factor.corr(returns, method='spearman')
            
            daily_ic.append(ic)
            dates.append(date)
        
        return pd.Series(daily_ic, index=dates)
```

---

### 2. 分层回测器

```python
# quantcore/alpha/research/layered_backtester.py

from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class LayeredBacktestResult:
    """分层回测结果"""
    # 各组收益
    group_returns: Dict[int, float]  # {组号: 年化收益}
    group_cumulative_returns: pd.DataFrame  # 各组累计收益
    
    # 多空组合
    long_short_return: float  # 多空年化收益
    long_short_volatility: float  # 多空波动率
    long_short_sharpe: float  # 多空夏普比率
    long_short_max_drawdown: float  # 多空最大回撤
    
    # 单调性检验
    monotonicity_score: float  # 单调性评分 (0-1)
    is_monotonic: bool  # 是否单调
    
    def summary(self) -> str:
        """生成摘要"""
        return (
            f"分层回测结果:\n"
            f"  Q1 (最低组): {self.group_returns.get(1, 0):.2%}\n"
            f"  Q5: {self.group_returns.get(5, 0):.2%}\n"
            f"  Q10 (最高组): {self.group_returns.get(10, 0):.2%}\n"
            f"  多空收益 (Q10-Q1): {self.long_short_return:.2%}\n"
            f"  多空夏普: {self.long_short_sharpe:.2f}\n"
            f"  多空最大回撤: {self.long_short_max_drawdown:.2%}\n"
            f"  单调性: {self.monotonicity_score:.2f} "
            f"{'是' if self.is_monotonic else '否'}"
        )


class LayeredBacktester:
    """分层回测器"""
    
    def __init__(self, n_groups: int = 10):
        """
        Args:
            n_groups: 分组数量 (默认 10)
        """
        self.n_groups = n_groups
    
    def run(
        self,
        factor_data: pd.DataFrame,
        return_data: pd.DataFrame,
        forward_days: int = 1
    ) -> LayeredBacktestResult:
        """
        执行分层回测
        
        Args:
            factor_data: 因子数据 (日期 × 股票)
            return_data: 收益率数据 (日期 × 股票)
            forward_days: 前向天数
        
        Returns:
            LayeredBacktestResult: 回测结果
        """
        logger.info(f"开始分层回测 (n={self.n_groups})...")
        
        # 对齐数据
        factor_data, return_data = self._align_data(
            factor_data, return_data, forward_days
        )
        
        # 每日分组
        group_returns = self._calculate_group_returns(
            factor_data, return_data
        )
        
        # 计算各组年化收益
        annual_returns = {}
        for group_id in range(1, self.n_groups + 1):
            if group_id in group_returns:
                returns = group_returns[group_id]
                annual_returns[group_id] = self._annualize(returns)
            else:
                annual_returns[group_id] = 0.0
        
        # 多空组合
        long_returns = group_returns.get(self.n_groups, pd.Series())
        short_returns = group_returns.get(1, pd.Series())
        long_short_returns = long_returns - short_returns
        
        ls_return = self._annualize(long_short_returns)
        ls_volatility = long_short_returns.std() * np.sqrt(252)
        ls_sharpe = ls_return / ls_volatility if ls_volatility > 0 else 0
        ls_max_drawdown = self._calculate_max_drawdown(
            long_short_returns
        )
        
        # 单调性检验
        monotonicity_score, is_monotonic = self._test_monotonicity(
            annual_returns
        )
        
        result = LayeredBacktestResult(
            group_returns=annual_returns,
            group_cumulative_returns=group_returns,
            long_short_return=ls_return,
            long_short_volatility=ls_volatility,
            long_short_sharpe=ls_sharpe,
            long_short_max_drawdown=ls_max_drawdown,
            monotonicity_score=monotonicity_score,
            is_monotonic=is_monotonic,
        )
        
        logger.info(result.summary())
        
        return result
    
    def _calculate_group_returns(
        self,
        factor_data: pd.DataFrame,
        return_data: pd.DataFrame
    ) -> Dict[int, pd.Series]:
        """计算各组每日收益"""
        group_returns = {i: [] for i in range(1, self.n_groups + 1)}
        dates = []
        
        for date in factor_data.index:
            factor_values = factor_data.loc[date].dropna()
            return_values = return_data.loc[date].dropna()
            
            # 取交集
            common_stocks = factor_values.index.intersection(
                return_values.index
            )
            
            if len(common_stocks) < 10:
                continue
            
            factor = factor_values[common_stocks]
            returns = return_values[common_stocks]
            
            # 按因子值分组
            quantiles = pd.qcut(
                factor,
                q=self.n_groups,
                labels=range(1, self.n_groups + 1),
                duplicates='drop'
            )
            
            # 计算各组平均收益
            for group_id in range(1, self.n_groups + 1):
                mask = quantiles == group_id
                if mask.sum() > 0:
                    group_returns[group_id].append(
                        returns[mask].mean()
                    )
                else:
                    group_returns[group_id].append(0.0)
            
            dates.append(date)
        
        # 转换为 DataFrame
        for group_id in group_returns:
            group_returns[group_id] = pd.Series(
                group_returns[group_id], index=dates
            )
        
        return group_returns
    
    def _annualize(self, returns: pd.Series) -> float:
        """年化收益率"""
        if len(returns) == 0:
            return 0.0
        return (1 + returns.mean()) ** 252 - 1
    
    def _calculate_max_drawdown(
        self,
        returns: pd.Series
    ) -> float:
        """计算最大回撤"""
        cumulative = (1 + returns).cumprod()
        rolling_max = cumulative.expanding().max()
        drawdown = (cumulative - rolling_max) / rolling_max
        return drawdown.min()
    
    def _test_monotonicity(
        self,
        group_returns: Dict[int, float]
    ) -> tuple:
        """
        检验单调性
        
        Returns:
            (score, is_monotonic)
        """
        returns_list = [
            group_returns.get(i, 0)
            for i in range(1, self.n_groups + 1)
        ]
        
        # 计算单调性评分 (相邻组收益差的正比例)
        diffs = [
            returns_list[i+1] - returns_list[i]
            for i in range(len(returns_list)-1)
        ]
        
        positive_diffs = sum(1 for d in diffs if d > 0)
        score = positive_diffs / len(diffs) if diffs else 0
        
        # 判断是否单调 (评分 > 0.8)
        is_monotonic = score >= 0.8
        
        return score, is_monotonic
    
    def _align_data(
        self,
        factor_data: pd.DataFrame,
        return_data: pd.DataFrame,
        forward_days: int
    ) -> tuple:
        """对齐数据"""
        return_shifted = return_data.shift(-forward_days)
        
        common_dates = factor_data.index.intersection(
            return_shifted.index
        )
        common_cols = factor_data.columns.intersection(
            return_shifted.columns
        )
        
        return (
            factor_data.loc[common_dates, common_cols],
            return_shifted.loc[common_dates, common_cols]
        )
```

---

### 3. 因子独立性检验

```python
# quantcore/alpha/research/factor_independence_tester.py

from typing import Dict, List, Optional
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy import stats
from loguru import logger


@dataclass
class IndependenceResult:
    """因子独立性检验结果"""
    # 相关性分析
    correlations: Dict[str, float]  # {因子名: 相关系数}
    max_correlation: float  # 最大相关性
    avg_correlation: float  # 平均相关性
    
    # 回归分析
    baseline_r2: float  # 基准模型 R²
    full_r2: float  # 完整模型 R²
    incremental_r2: float  # 增量 R²
    
    # 结论
    is_independent: bool  # 是否独立
    conclusion: str  # 结论描述
    
    def summary(self) -> str:
        """生成摘要"""
        return (
            f"因子独立性检验:\n"
            f"  最大相关性: {self.max_correlation:.3f}\n"
            f"  平均相关性: {self.avg_correlation:.3f}\n"
            f"  基准 R²: {self.baseline_r2:.4f}\n"
            f"  完整 R²: {self.full_r2:.4f}\n"
            f"  增量 R²: {self.incremental_r2:.4f}\n"
            f"  独立性: {'是' if self.is_independent else '否'}\n"
            f"  结论: {self.conclusion}"
        )


class FactorIndependenceTester:
    """因子独立性检验器"""
    
    def __init__(
        self,
        correlation_threshold: float = 0.7,
        incremental_r2_threshold: float = 0.05
    ):
        """
        Args:
            correlation_threshold: 相关性阈值
            incremental_r2_threshold: 增量 R²阈值
        """
        self.correlation_threshold = correlation_threshold
        self.incremental_r2_threshold = incremental_r2_threshold
    
    def test(
        self,
        target_factor: pd.Series,
        other_factors: Dict[str, pd.Series],
        returns: pd.Series
    ) -> IndependenceResult:
        """
        执行因子独立性检验
        
        Args:
            target_factor: 目标因子 (待检验因子)
            other_factors: 其他因子 {因子名: 因子值}
            returns: 收益率
        
        Returns:
            IndependenceResult: 检验结果
        """
        logger.info("开始因子独立性检验...")
        
        # Step 1: 相关性分析
        correlations = self._calculate_correlations(
            target_factor, other_factors
        )
        max_corr = max(abs(v) for v in correlations.values())
        avg_corr = np.mean([abs(v) for v in correlations.values()])
        
        # Step 2: 回归分析
        baseline_r2 = self._regression_r2(
            returns, other_factors
        )
        
        all_factors = {"target": target_factor, **other_factors}
        full_r2 = self._regression_r2(returns, all_factors)
        
        incremental_r2 = full_r2 - baseline_r2
        
        # Step 3: 结论
        is_independent = (
            max_corr < self.correlation_threshold and
            incremental_r2 >= self.incremental_r2_threshold
        )
        
        if is_independent:
            conclusion = (
                f"因子独立，增量 R²={incremental_r2:.2%}，"
                f"与传统因子相关性较低"
            )
        else:
            if max_corr >= self.correlation_threshold:
                conclusion = (
                    f"因子与传统因子相关性过高 "
                    f"(max={max_corr:.3f})，可能重复"
                )
            else:
                conclusion = (
                    f"增量 R²过低 ({incremental_r2:.2%})，"
                    f"因子解释力不足"
                )
        
        result = IndependenceResult(
            correlations=correlations,
            max_correlation=max_corr,
            avg_correlation=avg_corr,
            baseline_r2=baseline_r2,
            full_r2=full_r2,
            incremental_r2=incremental_r2,
            is_independent=is_independent,
            conclusion=conclusion,
        )
        
        logger.info(result.summary())
        
        return result
    
    def _calculate_correlations(
        self,
        target: pd.Series,
        others: Dict[str, pd.Series]
    ) -> Dict[str, float]:
        """计算目标因子与其他因子的相关性"""
        correlations = {}
        
        for name, factor in others.items():
            # 对齐数据
            aligned = pd.concat([target, factor], axis=1).dropna()
            if len(aligned) > 0:
                corr = aligned.iloc[:, 0].corr(aligned.iloc[:, 1])
                correlations[name] = corr
            else:
                correlations[name] = 0.0
        
        return correlations
    
    def _regression_r2(
        self,
        returns: pd.Series,
        factors: Dict[str, pd.Series]
    ) -> float:
        """计算回归 R²"""
        # 构建因子矩阵
        factor_df = pd.DataFrame(factors)
        
        # 对齐数据
        aligned = pd.concat([returns, factor_df], axis=1).dropna()
        if len(aligned) < len(factors) + 1:
            return 0.0
        
        y = aligned.iloc[:, 0]
        X = aligned.iloc[:, 1:]
        
        # 添加常数项
        X = pd.concat([X, pd.Series(1, index=X.index, name='const')], axis=1)
        
        # OLS 回归
        try:
            import statsmodels.api as sm
            model = sm.OLS(y, X).fit()
            return model.rsquared
        except Exception as e:
            logger.error(f"回归失败: {e}")
            return 0.0
```

---

### 4. 消融实验器

```python
# quantcore/alpha/research/ablation_study.py

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import numpy as np
import pandas as pd
from loguru import logger


@dataclass
class AblationResult:
    """消融实验结果"""
    # 各配置的性能
    full_performance: Dict[str, float]  # 完整模型
    ablation_performances: Dict[str, Dict[str, float]]  # 消融各模型
    
    # 因子贡献度
    factor_contributions: Dict[str, float]  # {因子名: 贡献度}
    
    # 排名
    factor_ranking: List[Tuple[str, float]]  # [(因子名，贡献度), ...]
    
    def summary(self) -> str:
        """生成摘要"""
        lines = [
            f"消融实验结果:",
            f"  完整模型: 年化收益={self.full_performance.get('annual_return', 0):.2%}",
            f"",
            f"  因子贡献度排名:",
        ]
        
        for factor, contribution in self.factor_ranking:
            lines.append(f"    {factor}: {contribution:.2%}")
        
        return "\n".join(lines)


class AblationStudy:
    """消融实验器"""
    
    def __init__(self, metric: str = "annual_return"):
        """
        Args:
            metric: 评估指标 (年化收益/夏普比率等)
        """
        self.metric = metric
    
    def run(
        self,
        factors: Dict[str, pd.Series],
        returns: pd.Series,
        strategy_func: callable
    ) -> AblationResult:
        """
        执行消融实验
        
        Args:
            factors: 所有因子 {因子名: 因子值}
            returns: 收益率
            strategy_func: 策略函数 (输入因子，返回绩效指标)
        
        Returns:
            AblationResult: 消融结果
        """
        logger.info("开始消融实验...")
        
        # Step 1: 完整模型
        full_performance = strategy_func(factors, returns)
        
        # Step 2: 逐个移除因子
        ablation_performances = {}
        factor_contributions = {}
        
        for factor_name in factors:
            # 移除当前因子
            reduced_factors = {
                k: v for k, v in factors.items()
                if k != factor_name
            }
            
            # 评估
            reduced_performance = strategy_func(
                reduced_factors, returns
            )
            
            ablation_performances[factor_name] = reduced_performance
            
            # 计算贡献度
            contribution = (
                full_performance.get(self.metric, 0) -
                reduced_performance.get(self.metric, 0)
            )
            factor_contributions[factor_name] = contribution
        
        # Step 3: 排名
        factor_ranking = sorted(
            factor_contributions.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        result = AblationResult(
            full_performance=full_performance,
            ablation_performances=ablation_performances,
            factor_contributions=factor_contributions,
            factor_ranking=factor_ranking,
        )
        
        logger.info(result.summary())
        
        return result
```

---

### 5. 主验证器 (组合所有测试)

```python
# quantcore/alpha/research/text_factor_validator.py

from typing import Dict, Optional
from dataclasses import dataclass
from datetime import date
import pandas as pd
from loguru import logger

from .ic_analyzer import ICAnalyzer, ICResult
from .layered_backtester import LayeredBacktester, LayeredBacktestResult
from .factor_independence_tester import (
    FactorIndependenceTester,
    IndependenceResult
)
from .ablation_study import AblationStudy, AblationResult


@dataclass
class FactorValidationReport:
    """因子验证报告"""
    factor_name: str
    validation_date: date
    
    # 各测试结果
    ic_result: ICResult
    layered_result: LayeredBacktestResult
    independence_result: IndependenceResult
    ablation_result: Optional[AblationResult] = None
    
    # 综合结论
    overall_score: float  # 综合评分 (0-100)
    passed: bool  # 是否通过验证
    conclusion: str  # 结论
    suggestions: list  # 建议
    
    def summary(self) -> str:
        """生成完整报告"""
        lines = [
            "=" * 60,
            f"因子验证报告: {self.factor_name}",
            f"验证日期: {self.validation_date}",
            "=" * 60,
            "",
            "1. IC 分析",
            "-" * 40,
            self.ic_result.summary(),
            "",
            "2. 分层回测",
            "-" * 40,
            self.layered_result.summary(),
            "",
            "3. 因子独立性",
            "-" * 40,
            self.independence_result.summary(),
            "",
            "4. 综合结论",
            "-" * 40,
            f"  综合评分: {self.overall_score:.1f}/100",
            f"  验证结果: {'✅ 通过' if self.passed else '❌ 未通过'}",
            f"  结论: {self.conclusion}",
            "",
            "5. 优化建议",
            "-" * 40,
        ]
        
        for i, suggestion in enumerate(self.suggestions, 1):
            lines.append(f"  {i}. {suggestion}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)


class TextFactorValidator:
    """文本因子验证器"""
    
    def __init__(self):
        self.ic_analyzer = ICAnalyzer()
        self.layered_backtester = LayeredBacktester()
        self.independence_tester = FactorIndependenceTester()
        self.ablation_study = AblationStudy()
    
    def validate(
        self,
        factor_name: str,
        factor_data: pd.DataFrame,
        return_data: pd.DataFrame,
        other_factors: Optional[Dict[str, pd.DataFrame]] = None,
        forward_days: int = 1
    ) -> FactorValidationReport:
        """
        执行完整验证
        
        Args:
            factor_name: 因子名称
            factor_data: 因子数据 (日期 × 股票)
            return_data: 收益率数据 (日期 × 股票)
            other_factors: 其他因子 (可选)
            forward_days: 前向天数
        
        Returns:
            FactorValidationReport: 验证报告
        """
        logger.info(f"开始验证因子: {factor_name}")
        
        # Step 1: IC 分析
        ic_result = self.ic_analyzer.analyze(
            factor_data, return_data, forward_days
        )
        
        # Step 2: 分层回测
        layered_result = self.layered_backtester.run(
            factor_data, return_data, forward_days
        )
        
        # Step 3: 因子独立性
        if other_factors:
            # 取目标因子
            target_factor = factor_data.iloc[:, 0]
            
            # 取其他因子的第一列
            other_factors_flat = {
                name: df.iloc[:, 0]
                for name, df in other_factors.items()
            }
            
            # 收益率 (第一列)
            returns = return_data.iloc[:, 0]
            
            independence_result = self.independence_tester.test(
                target_factor, other_factors_flat, returns
            )
        else:
            independence_result = IndependenceResult(
                correlations={},
                max_correlation=0.0,
                avg_correlation=0.0,
                baseline_r2=0.0,
                full_r2=0.0,
                incremental_r2=0.0,
                is_independent=True,
                conclusion="未提供其他因子，跳过独立性检验",
            )
        
        # Step 4: 综合评分
        overall_score, passed, conclusion, suggestions = (
            self._calculate_overall_score(
                ic_result, layered_result, independence_result
            )
        )
        
        # 生成报告
        report = FactorValidationReport(
            factor_name=factor_name,
            validation_date=pd.Timestamp.now().date(),
            ic_result=ic_result,
            layered_result=layered_result,
            independence_result=independence_result,
            overall_score=overall_score,
            passed=passed,
            conclusion=conclusion,
            suggestions=suggestions,
        )
        
        logger.info(report.summary())
        
        return report
    
    def _calculate_overall_score(
        self,
        ic_result: ICResult,
        layered_result: LayeredBacktestResult,
        independence_result: IndependenceResult
    ) -> tuple:
        """
        计算综合评分
        
        Returns:
            (score, passed, conclusion, suggestions)
        """
        score = 0.0
        suggestions = []
        
        # IC 分析评分 (40 分)
        ic_score = 0
        
        if abs(ic_result.ic_mean) > 0.03:
            ic_score += 10
        else:
            suggestions.append("IC 均值偏低，需要优化因子计算")
        
        if ic_result.icir > 0.5:
            ic_score += 10
        else:
            suggestions.append("ICIR 偏低，因子稳定性不足")
        
        if ic_result.t_value > 2.0:
            ic_score += 10
        else:
            suggestions.append("T 值偏低，因子不显著")
        
        if ic_result.ic_positive_rate > 0.55:
            ic_score += 10
        else:
            suggestions.append("IC 正比例偏低")
        
        score += ic_score
        
        # 分层回测评分 (40 分)
        ls_score = 0
        
        if abs(layered_result.long_short_return) > 0.10:
            ls_score += 10
        else:
            suggestions.append("多空收益偏低")
        
        if layered_result.long_short_sharpe > 1.0:
            ls_score += 10
        else:
            suggestions.append("夏普比率偏低")
        
        if abs(layered_result.long_short_max_drawdown) < 0.20:
            ls_score += 10
        else:
            suggestions.append("最大回撤偏大")
        
        if layered_result.is_monotonic:
            ls_score += 10
        else:
            suggestions.append("单调性不足，因子排序能力弱")
        
        score += ls_score
        
        # 独立性评分 (20 分)
        ind_score = 0
        
        if independence_result.max_correlation < 0.7:
            ind_score += 10
        else:
            suggestions.append("与传统因子相关性过高")
        
        if independence_result.incremental_r2 > 0.05:
            ind_score += 10
        else:
            suggestions.append("增量 R²过低")
        
        score += ind_score
        
        # 判断是否通过 (≥ 70 分)
        passed = score >= 70
        
        # 结论
        if passed:
            if score >= 90:
                conclusion = "因子优秀，可直接使用"
            elif score >= 80:
                conclusion = "因子良好，建议继续使用"
            else:
                conclusion = "因子合格，但有优化空间"
        else:
            conclusion = "因子未通过验证，需要重新设计"
        
        return score, passed, conclusion, suggestions
```

---

## 📊 验证标准

### 通过标准

| 测试项目 | 优秀 (≥ 90 分) | 良好 (80-89 分) | 合格 (70-79 分) | 未通过 (< 70 分) |
|---------|--------------|--------------|--------------|---------------|
| IC 均值 | > 0.05 | 0.03-0.05 | 0.02-0.03 | < 0.02 |
| ICIR | > 1.0 | 0.5-1.0 | 0.3-0.5 | < 0.3 |
| 多空年化收益 | > 15% | 10-15% | 5-10% | < 5% |
| 多空夏普比率 | > 2.0 | 1.0-2.0 | 0.5-1.0 | < 0.5 |
| 最大回撤 | < 15% | 15-20% | 20-25% | > 25% |
| 增量 R² | > 10% | 5-10% | 3-5% | < 3% |

---

**文档版本**: v1.0  
**创建时间**: 2026-04-24  
**模块位置**: quantcore/alpha/research/
