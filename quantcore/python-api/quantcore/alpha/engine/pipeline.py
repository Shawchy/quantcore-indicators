"""
因子流水线模块

定义因子的完整处理流程：原始数据 → 因子计算 → 标准化 → 存储
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import time

import pandas as pd
import numpy as np
from loguru import logger

from .engine import FactorEngine


class PipelineStage(Enum):
    """流水线阶段"""
    RAW = "raw"
    CALCULATED = "calculated"
    NORMALIZED = "normalized"
    WINSORIZED = "winsorized"
    NEUTRALIZED = "neutralized"
    FINAL = "final"


@dataclass
class PipelineConfig:
    """流水线配置"""
    winsorize_limits: tuple = (0.01, 0.99)
    normalization_method: str = "zscore"
    neutralize_industry: bool = True
    neutralize_size: bool = True
    neutralize_market_cap: bool = True
    min_valid_ratio: float = 0.5
    handle_missing: str = "drop"  # drop/fill/forward_fill


@dataclass
class PipelineResult:
    """流水线结果"""
    factor_name: str
    stage_results: Dict[PipelineStage, pd.Series] = field(default_factory=dict)
    final_values: Optional[pd.Series] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    processing_time: float = 0.0


class FactorPipeline:
    """
    因子处理流水线
    
    定义从原始数据到最终因子的完整处理流程：
    
    1. 原始数据验证
    2. 因子计算
    3. 去极值 (Winsorization)
    4. 标准化 (Normalization)
    5. 中性化 (Neutralization) - 可选
    
    使用示例：
        pipeline = FactorPipeline(config=PipelineConfig())
        result = pipeline.run("MOMENTUM_20", data, engine)
        print(result.final_values)
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        
        # 处理步骤
        self._steps: List[Callable] = [
            self._validate,
            self._calculate,
            self._winsorize,
            self._normalize,
            self._neutralize
        ]
        
        # 中性化数据（行业分类、市值等）
        self._neutralizers = {}
    
    def run(
        self,
        factor_name: str,
        data: pd.DataFrame,
        engine: FactorEngine,
        **kwargs
    ) -> PipelineResult:
        """
        运行因子处理流水线
        
        Args:
            factor_name: 因子名称
            data: 输入数据
            engine: 因子引擎实例
            **kwargs: 额外参数
            
        Returns:
            PipelineResult: 流水线结果
        """
        start_time = time.time()
        result = PipelineResult(factor_name=factor_name)
        
        try:
            # 阶段1: 验证
            validated_data = self._validate(data, result)
            
            # 阶段2: 计算
            raw_values = self._calculate(validated_data, factor_name, engine, result)
            
            if raw_values is None or len(raw_values) == 0:
                result.metadata["status"] = "empty"
                return result
            
            # 阶段3: 去极值
            winsorized = self._winsorize(raw_values, result)
            
            # 阶段4: 标准化
            normalized = self._normalize(winsorized, result)
            
            # 阶段5: 中性化（可选）
            final_values = self._neutralize(normalized, data, result)
            
            result.final_values = final_values
            result.metadata["status"] = "success"
            
        except Exception as e:
            logger.error(f"流水线执行失败 {factor_name}: {e}")
            result.metadata["status"] = "error"
            result.metadata["error"] = str(e)
        
        result.processing_time = time.time() - start_time
        return result
    
    def _validate(self, data: pd.DataFrame, result: PipelineResult) -> pd.DataFrame:
        """验证输入数据"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            raise ValueError(f"缺少必要列: {missing_cols}")
        
        # 处理缺失值
        if self.config.handle_missing == "drop":
            data = data.dropna(subset=required_cols)
        elif self.config.handle_missing == "fill":
            data = data.fillna(method='ffill').fillna(0)
        elif self.config.handle_missing == "forward_fill":
            data = data.ffill().bfill(0)
        
        result.stage_results[PipelineStage.RAW] = data['close']
        return data
    
    def _calculate(
        self,
        data: pd.DataFrame,
        factor_name: str,
        engine: FactorEngine,
        result: PipelineResult
    ) -> pd.Series:
        """计算因子原始值"""
        calc_result = engine.calculate(factor_name, data)
        raw_values = calc_result.values
        
        result.stage_results[PipelineStage.CALCULATED] = raw_values
        
        # 更新元数据
        result.metadata.update(calc_result.metadata)
        
        return raw_values
    
    def _winsorize(self, values: pd.Series, result: PipelineResult) -> pd.Series:
        """去极值处理"""
        lower = values.quantile(self.config.winsorize_limits[0])
        upper = values.quantile(self.config.winsorize_limits[1])
        winsorized = values.clip(lower, upper)
        
        result.stage_results[PipelineStage.WINSORIZED] = winsorized
        return winsorized
    
    def _normalize(self, values: pd.Series, result: PipelineResult) -> pd.Series:
        """标准化处理"""
        method = self.config.normalization_method
        
        if method == "zscore":
            std = values.std()
            if std > 0:
                normalized = (values - values.mean()) / std
            else:
                normalized = pd.Series(0.0, index=values.index)
        
        elif method == "rank":
            normalized = values.rank(pct=True) * 2 - 1
        
        elif method == "minmax":
            min_val = values.min()
            max_val = values.max()
            if max_val > min_val:
                normalized = (values - min_val) / (max_val - min_val)
            else:
                normalized = pd.Series(0.5, index=values.index)
        
        else:
            raise ValueError(f"未知标准化方法: {method}")
        
        result.stage_results[PipelineStage.NORMALIZED] = normalized
        return normalized
    
    def _neutralize(
        self,
        values: pd.Series,
        original_data: pd.DataFrame,
        result: PipelineResult
    ) -> pd.Series:
        """中性化处理"""
        neutralized = values.copy()
        
        if not any([
            self.config.neutralize_industry,
            self.config.neutralize_size,
            self.config.neutralize_market_cap
        ]):
            result.stage_results[PipelineStage.NEUTRALIZED] = neutralized
            result.stage_results[PipelineStage.FINAL] = neutralized
            return neutralized
        
        # 行业中性化
        if self.config.neutralize_industry and 'industry' in original_data.columns:
            industry_groups = original_data['industry']
            neutralized = self._regress_out(neutralized, industry_groups)
        
        # 市值中性化
        if self.config.neutralize_size and 'total_market_cap' in original_data.columns:
            log_cap = np.log(original_data['total_market_cap'].replace(0, np.nan))
            neutralized = self._regress_out(neutralized, log_cap)
        
        result.stage_results[PipelineStage.NEUTRALIZED] = neutralized
        result.stage_results[PipelineStage.FINAL] = neutralized
        return neutralized
    
    def _regress_out(self, values: pd.Series, regressor: pd.Series) -> pd.Series:
        """
        回归去除某个变量的影响
        
        Args:
            values: 目标变量
            regressor: 要回归掉的变量
            
        Returns:
            回归残差
        """
        common_idx = values.dropna().index.intersection(regressor.dropna().index)
        
        if len(common_idx) < 30:
            return values
        
        y = values.loc[common_idx].values
        x = regressor.loc[common_idx].values.reshape(-1, 1)
        
        # 添加常数项
        X = np.column_stack([np.ones(len(x)), x])
        
        # 最小二乘回归
        try:
            beta = np.linalg.lstsq(X, y, rcond=None)[0]
            residuals = y - X @ beta
            
            result = values.copy()
            result.loc[common_idx] = residuals
            return result
            
        except Exception as e:
            logger.debug(f"回归失败: {e}")
            return values
    
    def run_batch(
        self,
        factor_names: List[str],
        data: pd.DataFrame,
        engine: FactorEngine,
        **kwargs
    ) -> Dict[str, PipelineResult]:
        """
        批量运行多个因子的流水线
        
        Args:
            factor_names: 因子名称列表
            data: 输入数据
            engine: 因子引擎
            
        Returns:
            {factor_name: PipelineResult}
        """
        results = {}
        
        for name in factor_names:
            try:
                result = self.run(name, data, engine, **kwargs)
                results[name] = result
            except Exception as e:
                logger.debug(f"因子 {name} 流水线失败: {e}")
                continue
        
        return results
