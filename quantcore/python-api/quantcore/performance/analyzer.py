# -*- coding: utf-8 -*-
"""
绩效分析模块

提供绩效分析功能：
- PerformanceAnalyzer: 绩效分析器（Rust 实现）
- PerformanceReport: 绩效报告生成
"""

from typing import List, Dict, Any
from ..engine import BacktestResult


class PerformanceReport:
    """绩效报告生成器"""
    
    def __init__(self, result: BacktestResult):
        """
        初始化绩效报告
        
        Args:
            result: 回测结果
        """
        self.result = result
    
    def generate_summary(self) -> str:
        """
        生成绩效摘要
        
        Returns:
            绩效摘要字符串
        """
        summary = []
        summary.append("=" * 60)
        summary.append("绩效分析报告")
        summary.append("=" * 60)
        summary.append(f"初始资金：{self.result.initial_capital:.2f}")
        summary.append(f"最终资金：{self.result.final_capital:.2f}")
        summary.append(f"总收益：{self.result.total_return * 100:.2f}%")
        summary.append(f"交易次数：{self.result.total_trades}")
        summary.append("=" * 60)
        
        return "\n".join(summary)
    
    def print_report(self):
        """打印绩效报告"""
        print(self.generate_summary())
