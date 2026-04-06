# -*- coding: utf-8 -*-
"""
策略框架模块

提供策略开发接口：
- Strategy: 策略基类
- StrategyRunner: 策略运行器
"""

from .base import Strategy, StrategyRunner

__all__ = [
    'Strategy',
    'StrategyRunner',
]
