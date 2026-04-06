# -*- coding: utf-8 -*-
"""
绩效分析模块
"""

from .analyzer import PerformanceReport
from quantcore import quantcore_engine as qe

# 从 Rust 引擎导入 PerformanceAnalyzer
PerformanceAnalyzer = qe.PerformanceAnalyzer

__all__ = [
    'PerformanceReport',
    'PerformanceAnalyzer',
]
