"""
Fundamental Data Factor (基本面因子库)

完整的基本面因子集合：
- 价值因子 (Value)
- 质量因子 (Quality)
- 成长因子 (Growth)
- 杠杆因子 (Leverage)
- 盈利稳定性 (Stability)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from loguru import logger


@dataclass
class FundamentalFactorConfig:
    """基本面因子配置"""
    value_metrics: List[str] = None  # ["pe", "pb", "ps", "pcf", "ev_ebitda"]
    quality_metrics: List[str] = None  # ["roe", "roic", "gross_margin", "net_margin"]
    growth_metrics: List[str] = None  # ["revenue_growth", "profit_growth"]
    leverage_metrics: List[str] = None  # ["debt_ratio", "current_ratio"]


class FundamentalFactorLibrary:
    """
    基本面因子库
    
    提供基于财务数据的基本面因子计算方法：
    
    **价值因子 (Value)：**
    - VALUE: 综合价值得分（PE/PB/PS等取倒数后标准化）
    
    **质量因子 (Quality)：**
    - QUALITY: 综合质量得分（ROE/ROIC/毛利率/净利率）
    
    **成长因子 (Growth)：**
    - GROWTH: 综合成长得分（营收增速/净利增速/EPS增速）
    
    **杠杆因子 (Leverage)：**
    - LEVERAGE: 负债率相关因子
    
    **盈利稳定性 (Stability)：**
    - STABILITY: ROE标准差、利润波动等
    
    数据来源：Backend 的财务数据适配器
    - pe_ratio, pb_ratio, ps_ttm, pcf1_ttm, ev_ebitda_24a
    - roe, roic, gross_margin, net_profit_margin
    - revenue_yoy, net_profit_yoy, eps_growth_ttm
    - asset_liability_ratio, current_ratio
    """
    
    def __init__(self, config: Optional[FundamentalFactorConfig] = None):
        self.config = config or FundamentalFactorConfig()
        
        if self.config.value_metrics is None:
            self.config.value_metrics = ["pe", "pb", "ps"]
        if self.config.quality_metrics is None:
            self.config.quality_metrics = ["roe", "gross_margin"]
        if self.config.growth_metrics is None:
            self.config.growth_metrics = ["revenue_growth", "net_profit_growth"]
        
        # 列名映射
        self.col_map = {
            # 估值指标
            'pe': 'pe_ratio',
            'pb': 'pb_ratio',
            'ps': 'ps_ttm',
            'pcf': 'pcf1_ttm',
            'ev_ebitda': 'ev_ebitda_24a',
            
            # 质量指标
            'roe': 'roe',
            'roic': 'roic',
            'gross_margin': 'gross_margin',
            'net_margin': 'net_profit_margin',
            'asset_turnover': 'asset_turnover',
            
            # 成长指标
            'revenue_growth': 'revenue_yoy',
            'net_profit_growth': 'net_profit_yoy',
            'eps_growth': 'eps_growth_ttm',
            'revenue_qoq': 'revenue_qoq',
            
            # 杠杆指标
            'debt_ratio': 'asset_liability_ratio',
            'current_ratio': 'current_ratio',
            'quick_ratio': 'quick_ratio',
            'interest_coverage': 'interest_coverage',
        }
    
    def calculate_all(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算所有基本面因子
        
        Args:
            data: 包含财务指标的 DataFrame
            
        Returns:
            DataFrame: 所有基本面因子
        """
        results = {}
        
        results.update(self.calculate_value(data))
        results.update(self.calculate_quality(data))
        results.update(self.calculate_growth(data))
        results.update(self.calculate_leverage(data))
        results.update(self.calculate_stability(data))
        
        return pd.DataFrame(results)
    
    def calculate_value(
        self,
        data: pd.DataFrame,
        metrics: List[str] = None
    ) -> Dict[str, pd.Series]:
        """
        计算价值因子
        
        原理：估值越低越好，所以对估值指标取倒数后标准化。
        
        Args:
            data: 财务数据
            metrics: 要使用的指标列表
            
        Returns:
            {factor_name: Series}
        """
        metrics = metrics or self.config.value_metrics
        factors = {}
        
        z_scores = []
        for metric in metrics:
            col_name = self.col_map.get(metric)
            if col_name and col_name in data.columns:
                # 取倒数（估值越低越便宜=好）
                inv_metric = 1 / data[col_name].replace(0, np.nan).replace([np.inf, -np.inf], np.nan)
                
                # 标准化
                std = inv_metric.std()
                if std > 0:
                    z_score = (inv_metric - inv_metric.mean()) / std
                else:
                    z_score = inv_metric * 0
                
                z_scores.append(z_score.dropna())
                
                # 单独保存每个指标
                factors[f"VALUE_{metric.upper()}"] = z_score
        
        # 综合价值因子
        if len(z_scores) > 1:
            combined = pd.concat(z_scores, axis=1).mean(axis=1)
            factors["VALUE"] = combined.dropna()
        elif len(z_scores) == 1:
            factors["VALUE"] = z_scores[0]
        
        return factors
    
    def calculate_quality(
        self,
        data: pd.DataFrame,
        metrics: List[str] = None
    ) -> Dict[str, pd.Series]:
        """
        计算质量因子
        
        原理：盈利能力越强，质量越高。
        
        Args:
            data: 财务数据
            metrics: 要使用的指标列表
            
        Returns:
            {factor_name: Series}
        """
        metrics = metrics or self.config.quality_metrics
        factors = {}
        
        z_scores = []
        for metric in metrics:
            col_name = self.col_map.get(metric)
            if col_name and col_name in data.columns:
                values = data[col_name]
                
                # 标准化
                std = values.std()
                if std > 0:
                    z_score = (values - values.mean()) / std
                else:
                    z_score = values * 0
                
                z_scores.append(z_score.dropna())
                factors[f"QUALITY_{metric.upper()}"] = z_score
        
        # 综合质量因子
        if len(z_scores) > 1:
            combined = pd.concat(z_scores, axis=1).mean(axis=1)
            factors["QUALITY"] = combined.dropna()
        elif len(z_scores) == 1:
            factors["QUALITY"] = z_scores[0]
        
        return factors
    
    def calculate_growth(
        self,
        data: pd.DataFrame,
        metrics: List[str] = None
    ) -> Dict[str, pd.Series]:
        """
        计算成长因子
        
        原理：增长速度越快，成长性越好。
        
        Args:
            data: 财务数据
            metrics: 要使用的指标列表
            
        Returns:
            {factor_name: Series}
        """
        metrics = metrics or self.config.growth_metrics
        factors = {}
        
        z_scores = []
        for metric in metrics:
            col_name = self.col_map.get(metric)
            if col_name and col_name in data.columns:
                values = data[col_name]
                
                # 标准化
                std = values.std()
                if std > 0:
                    z_score = (values - values.mean()) / std
                else:
                    z_score = values * 0
                
                z_scores.append(z_score.dropna())
                factors[f"GROWTH_{metric.upper()}"] = z_score
        
        # 综合成长因子
        if len(z_scores) > 1:
            combined = pd.concat(z_scores, axis=1).mean(axis=1)
            factors["GROWTH"] = combined.dropna()
        elif len(z_scores) == 1:
            factors["GROWTH"] = z_scores[0]
        
        return factors
    
    def calculate_leverage(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算杠杆因子
        
        原理：杠杆越低，风险越小，因子值越高。
        
        Args:
            data: 财务数据
            
        Returns:
            {factor_name: Series}
        """
        factors = {}
        
        # 资产负债率（取负，负债率低=好）
        if 'asset_liability_ratio' in data.columns:
            debt = -data['asset_liability_ratio']
            std = debt.std() if debt.std() > 0 else 1
            factors["LEVERAGE_DEBT_RATIO"] = ((debt - debt.mean()) / std).dropna()
        
        # 流动比率（越高越好）
        if 'current_ratio' in data.columns:
            cr = data['current_ratio']
            std = cr.std() if cr.std() > 0 else 1
            factors["LEVERAGE_CURRENT_RATIO"] = ((cr - cr.mean()) / std).dropna()
        
        # 综合杠杆因子
        leverage_factors = [k for k in factors.keys() if k.startswith("LEVERAGE_")]
        if len(leverage_factors) > 1:
            combined = pd.DataFrame(factors)[leverage_factors].mean(axis=1)
            factors["LEVERAGE"] = combined.dropna()
        elif len(leverage_factors) == 1:
            factors["LEVERAGE"] = factors[leverage_factors[0]]
        
        return factors
    
    def calculate_stability(self, data: pd.DataFrame) -> Dict[str, pd.Series]:
        """
        计算盈利稳定性因子
        
        原理：盈利波动越小，稳定性越高。
        
        需要多期数据来计算波动性。
        
        Args:
            data: 财务数据（可能包含多期数据）
            
        Returns:
            {factor_name: Series}
        """
        factors = {}
        
        # ROE 稳定性（如果有多期数据）
        if 'roe_3y_std' in data.columns:
            roe_stability = -data['roe_3y_std']  # 波动小=好
            std = roe_stability.std() if roe_stability.std() > 0 else 1
            factors["STABILITY_ROE"] = ((roe_stability - roe_stability.mean()) / std).dropna()
        
        # 利润稳定性
        if 'profit_volatility' in data.columns:
            profit_stab = -data['profit_volatility']
            std = profit_stab.std() if profit_stab.std() > 0 else 1
            factors["STABILITY_PROFIT"] = ((profit_stab - profit_stab.mean()) / std).dropna()
        
        # 盈余质量（经营现金流/净利润）
        if 'operating_cash_flow' in data.columns and 'net_profit' in data.columns:
            eq = data['operating_cash_flow'] / data['net_profit'].replace(0, np.nan)
            std = eq.std() if eq.std() > 0 else 1
            factors["STABILITY_EARNINGS_QUALITY"] = ((eq - eq.mean()) / std).dropna()
        
        return factors
    
    def list_available_factors(self) -> List[Dict[str, str]]:
        """列出所有可用的基本面因子"""
        factors = [
            {"name": "VALUE", "category": "value", "description": "综合价值因子"},
            {"name": "QUALITY", "category": "quality", "description": "综合质量因子"},
            {"name": "GROWTH", "category": "growth", "description": "综合成长因子"},
            {"name": "LEVERAGE", "category": "leverage", "description": "综合杠杆因子"},
            {"name": "STABILITY_ROE", "category": "stability", "description": "ROE稳定性"},
            {"name": "STABILITY_EARNINGS_QUALITY", "category": "stability", "description": "盈余质量"},
        ]
        
        for m in self.config.value_metrics:
            factors.append({"name": f"VALUE_{m.upper()}", "category": "value", "description": f"价值-{m}"})
        
        for m in self.config.quality_metrics:
            factors.append({"name": f"QUALITY_{m.upper()}", "category": "quality", "description": f"质量-{m}"})
        
        for m in self.config.growth_metrics:
            factors.append({"name": f"GROWTH_{m.upper()}", "category": "growth", "description": f"成长-{m}"})
        
        return factors
