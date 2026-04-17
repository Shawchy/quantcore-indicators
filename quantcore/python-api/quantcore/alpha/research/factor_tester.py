"""
因子测试器

整合 IC 分析和分层回测，提供完整的因子测试功能。
"""

from typing import Dict, List, Optional, Any
import pandas as pd
from loguru import logger

from .ic_analysis import ICCalculator, ICAnalysis
from .layered_backtest import LayeredBacktester, LayeredBacktestResult


@dataclass
class FactorTestResult:
    """因子测试完整结果"""
    factor_name: str
    ic_result: Optional[ICAnalysis] = None
    backtest_result: Optional[LayeredBacktestResult] = None
    
    # 综合评分
    overall_score: float = 0.0  # 0-100
    
    def summary(self) -> str:
        """生成综合摘要"""
        ic_str = self.ic_result.summary() if self.ic_result else "IC 分析: 未执行"
        bt_str = self.backtest_result.summary() if self.backtest_result else "分层回测: 未执行"
        
        return f"""
{'='*50}
因子测试报告: {self.factor_name}
{'='*50}
{ic_str}
{bt_str}
综合评分: {self.overall_score:.1f}/100
{'='*50}
"""


class FactorTester:
    """
    因子测试器
    
    整合多种因子验证方法：
    
    1. **IC 分析**：评估因子预测能力
       - IC 均值 > 0.03 为好
       - IC IR > 0.5 为稳定
       
    2. **分层回测**：评估因子选股效果
       - 多空收益显著为正
       - 分层收益单调性好
       
    使用示例：
        tester = FactorTester()
        
        result = tester.test(
            factor_name="MOMENTUM_20",
            factor_data=factor_df,
            returns_data=returns_df
        )
        
        print(result.summary())
    """
    
    def __init__(self):
        self.ic_calculator = ICCalculator()
        self.backtester = LayeredBacktester()
    
    def test(
        self,
        factor_name: str,
        factor_data: pd.DataFrame,
        returns_data: pd.DataFrame,
        forward_period: int = 1,
        n_layers: int = 5,
        run_ic: bool = True,
        run_backtest: bool = True
    ) -> FactorTestResult:
        """
        完整的因子测试
        
        Args:
            factor_name: 因子名称
            factor_data: 因子数据 (symbol × date)
            returns_data: 收益率数据 (symbol × date)
            forward_period: 前瞻期
            n_layers: 分层回测分层数
            run_ic: 是否执行 IC 分析
            run_backtest: 是否执行分层回测
            
        Returns:
            FactorTestResult: 测试结果
        """
        result = FactorTestResult(factor_name=factor_name)
        
        logger.info(f"开始测试因子: {factor_name}")
        
        # IC 分析
        if run_ic:
            try:
                ic_result = self.ic_calculator.calculate_series(
                    factor_data, returns_data, forward_period=forward_period
                )
                ic_result.factor_name = factor_name
                result.ic_result = ic_result
                
                logger.info(f"IC 分析完成: mean={ic_result.ic_mean:.4f}, IR={ic_result.ic_ir:.4f}")
                
            except Exception as e:
                logger.error(f"IC 分析失败: {e}")
        
        # 分层回测
        if run_backtest:
            try:
                bt_result = self.backtester.run(
                    factor_data, returns_data, n_layers=n_layers
                )
                bt_result.factor_name = factor_name
                result.backtest_result = bt_result
                
                logger.info(f"分层回测完成: 年化收益={bt_result.long_short_annualized_return:.2%}")
                
            except Exception as e:
                logger.error(f"分层回测失败: {e}")
        
        # 计算综合评分
        result.overall_score = self._calculate_overall_score(result)
        
        return result
    
    def _calculate_overall_score(self, result: FactorTestResult) -> float:
        """
        计算因子综合评分 (0-100)
        
        评分标准：
        - IC 均值绝对值 (40分): |IC| * 1000
        - IC IR (20分): IR * 40
        - 显著性 (10分): p < 0.05
        - 多空年化收益 (20分): 收益率 * 200
        - 夏普比率 (10分): Sharpe * 10
        
        Returns:
            float: 综合得分
        """
        score = 0.0
        
        # IC 相关评分
        if result.ic_result:
            ic = result.ic_result
            
            # IC 均值 (0-40分)
            score += min(abs(ic.ic_mean) * 1000, 40)
            
            # IC IR (0-20分)
            score += min(abs(ic.ic_ir) * 40, 20)
            
            # 显著性 (0-10分)
            if ic.is_significant():
                score += 10
        
        # 回测相关评分
        if result.backtest_result:
            bt = result.backtest_result
            
            # 多空年化收益 (0-20分)
            score += max(min(bt.long_short_annualized_return * 200, 20), -5)
            
            # 夏普比率 (0-10分)
            score += max(min(bt.long_short_sharpe * 10, 10), 0)
        
        return max(0, min(100, score))
    
    def test_multiple_factors(
        self,
        factors_dict: Dict[str, pd.DataFrame],
        returns_data: pd.DataFrame,
        **kwargs
    ) -> Dict[str, FactorTestResult]:
        """
        批量测试多个因子
        
        Args:
            factors_dict: {factor_name: factor_data}
            returns_data: 收益率数据
            
        Returns:
            {factor_name: FactorTestResult}
        """
        results = {}
        
        for name, factor_data in factors_dict.items():
            try:
                result = self.test(name, factor_data, returns_data, **kwargs)
                results[name] = result
                
                logger.info(f"{name}: 综合评分={result.overall_score:.1f}")
                
            except Exception as e:
                logger.error(f"测试因子 {name} 失败: {e}")
        
        # 按评分排序
        sorted_results = dict(sorted(results.items(), key=lambda x: x[1].overall_score, reverse=True))
        
        return sorted_results
    
    def generate_report(self, results: Dict[str, FactorTestResult]) -> str:
        """
        生成因子测试报告
        
        Args:
            results: {factor_name: FactorTestResult}
            
        Returns:
            str: 报告文本
        """
        lines = []
        lines.append("=" * 70)
        lines.append("                    Data Factor Alpha 工厂 - 因子测试报告")
        lines.append("=" * 70)
        lines.append("")
        
        # 排名表格
        lines.append("┌─────────────────────────┬──────────┬──────────┬──────────┬────────┐")
        lines.append("│ 因子名称                 │ 综合评分  │ IC均值   │ IC IR   │ 胜率   │")
        lines.append("├─────────────────────────┼──────────┼──────────┼──────────┼────────┤")
        
        for name, result in results.items():
            ic_mean = f"{result.ic_result.ic_mean:.4f}" if result.ic_result else "N/A"
            ic_ir = f"{result.ic_result.ic_ir:.4f}" if result.ic_result else "N/A"
            win_rate = f"{result.backtest_result.win_rate:.1%}" if result.backtest_result else "N/A"
            
            lines.append(f"│ {name:<23} │ {result.overall_score:>8.1f} │ {ic_mean:>8s} │ {ic_ir:>8s} │ {win_rate:>6s} │")
        
        lines.append("└─────────────────────────┴──────────┴──────────┴──────────┴────────┘")
        lines.append("")
        
        # 详细结果（Top 5）
        top_5 = sorted(results.items(), key=lambda x: x[1].overall_score, reverse=True)[:5]
        
        for name, result in top_5:
            lines.append(result.summary())
        
        return "\n".join(lines)
