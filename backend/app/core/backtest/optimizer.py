from typing import Optional, List, Dict, Any, Callable
import numpy as np
from dataclasses import dataclass
from loguru import logger
import asyncio


@dataclass
class OptimizationResult:
    best_params: Dict[str, Any]
    best_score: float
    all_results: List[Dict[str, Any]]
    n_iterations: int
    optimization_time: float


class ParameterOptimizer:
    def __init__(
        self,
        n_iterations: int = 20,
        random_state: int = 42
    ):
        self.n_iterations = n_iterations
        self.random_state = random_state
    
    def optimize(
        self,
        objective_fn: Callable,
        param_space: Dict[str, List[Any]],
        method: str = "bayesian"
    ) -> OptimizationResult:
        if method == "bayesian":
            return self._bayesian_optimize(objective_fn, param_space)
        elif method == "grid":
            return self._grid_search(objective_fn, param_space)
        elif method == "random":
            return self._random_search(objective_fn, param_space)
        else:
            raise ValueError(f"Unknown optimization method: {method}")
    
    def _bayesian_optimize(
        self,
        objective_fn: Callable,
        param_space: Dict[str, List[Any]]
    ) -> OptimizationResult:
        try:
            from skopt import gp_minimize
            from skopt.space import Real, Integer, Categorical
            
            space = []
            param_names = []
            
            for name, values in param_space.items():
                param_names.append(name)
                if isinstance(values[0], float):
                    space.append(Real(min(values), max(values), name=name))
                elif isinstance(values[0], int):
                    space.append(Integer(min(values), max(values), name=name))
                else:
                    space.append(Categorical(values, name=name))
            
            def wrapped_objective(params):
                param_dict = dict(zip(param_names, params))
                try:
                    score = objective_fn(param_dict)
                    return -score if score is not None else 0
                except Exception as e:
                    logger.warning(f"Objective function failed: {e}")
                    return 0
            
            result = gp_minimize(
                wrapped_objective,
                space,
                n_calls=self.n_iterations,
                random_state=self.random_state,
                verbose=False
            )
            
            best_params = dict(zip(param_names, result.x))
            best_score = -result.fun
            
            all_results = []
            for i, (params, score) in enumerate(zip(result.x_iters, -result.func_vals)):
                all_results.append({
                    "iteration": i + 1,
                    "params": dict(zip(param_names, params)),
                    "score": -score
                })
            
            return OptimizationResult(
                best_params=best_params,
                best_score=best_score,
                all_results=all_results,
                n_iterations=len(all_results),
                optimization_time=result.specs.get("iter_time", 0) * len(all_results) if result.specs else 0
            )
            
        except ImportError:
            logger.warning("scikit-optimize not installed, using random search")
            return self._random_search(objective_fn, param_space)
    
    def _random_search(
        self,
        objective_fn: Callable,
        param_space: Dict[str, List[Any]]
    ) -> OptimizationResult:
        all_results = []
        best_score = -float('inf')
        best_params = {}
        
        np.random.seed(self.random_state)
        
        for i in range(self.n_iterations):
            params = {
                name: np.random.choice(values) if len(values) <= 5 
                else values[np.random.randint(0, len(values))]
                for name, values in param_space.items()
            }
            
            try:
                score = objective_fn(params)
            except Exception as e:
                logger.warning(f"Objective function failed: {e}")
                score = None
            
            if score is not None:
                all_results.append({
                    "iteration": i + 1,
                    "params": params,
                    "score": score
                })
                
                if score > best_score:
                    best_score = score
                    best_params = params
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score if best_score != -float('inf') else 0,
            all_results=all_results,
            n_iterations=len(all_results),
            optimization_time=0
        )
    
    def _grid_search(
        self,
        objective_fn: Callable,
        param_space: Dict[str, List[Any]]
    ) -> OptimizationResult:
        import itertools
        
        param_names = list(param_space.keys())
        param_values = list(param_space.values())
        
        all_combinations = list(itertools.product(*param_values))
        
        all_results = []
        best_score = -float('inf')
        best_params = {}
        
        for i, combination in enumerate(all_combinations):
            params = dict(zip(param_names, combination))
            
            try:
                score = objective_fn(params)
            except Exception as e:
                logger.warning(f"Objective function failed: {e}")
                score = None
            
            if score is not None:
                all_results.append({
                    "iteration": i + 1,
                    "params": params,
                    "score": score
                })
                
                if score > best_score:
                    best_score = score
                    best_params = params
        
        return OptimizationResult(
            best_params=best_params,
            best_score=best_score if best_score != -float('inf') else 0,
            all_results=all_results,
            n_iterations=len(all_results),
            optimization_time=0
        )


class StrategyOptimizer:
    def __init__(self):
        self.optimizer = ParameterOptimizer()
    
    def optimize_strategy(
        self,
        code: str,
        start_date: str,
        end_date: str,
        strategy_type: str,
        param_ranges: Dict[str, List[Any]],
        initial_capital: float = 1000000,
        n_iterations: int = 20,
        method: str = "bayesian"
    ) -> OptimizationResult:
        """
        优化策略参数（按需加载数据）
        
        优化策略：
        1. 只拉取指定股票的 K 线数据
        2. 数据保存到数据库后，下次优化直接使用
        3. 不会批量拉取多只股票数据
        """
        from app.core.backtest import BacktestEngine
        from app.adapters import data_source_manager
        from app.services.data_persistence import data_persistence
        import pandas as pd
        import asyncio
        
        # 按需拉取单只股票数据
        logger.info(f"开始优化 {code} 的策略参数，日期范围：{start_date} - {end_date}")
        
        klines = asyncio.run(
            data_source_manager.get_kline(code, start_date, end_date, "qfq")
        )
        
        # 持久化保存到数据库
        if klines:
            try:
                asyncio.run(data_persistence.save_klines(code, klines, "qfq"))
                logger.info(f"已保存 {len(klines)} 条 K 线数据：{code}")
            except Exception as e:
                logger.warning(f"保存 K 线数据失败：{e}")
        
        if not klines:
            logger.warning(f"无法获取 K 线数据：{code}")
            return OptimizationResult(
                best_params={},
                best_score=0,
                all_results=[],
                n_iterations=0,
                optimization_time=0
            )
        
        df = pd.DataFrame([{
            "date": k.date,
            "open": k.open,
            "high": k.high,
            "low": k.low,
            "close": k.close,
            "volume": k.volume,
            "code": code
        } for k in klines])
        
        engine = BacktestEngine(
            initial_capital=initial_capital,
            commission_rate=0.0003,
            slippage=0.001
        )
        
        def objective_fn(params: Dict[str, Any]) -> float:
            try:
                result = engine.run(
                    df=df,
                    strategy_type=strategy_type,
                    strategy_params=params,
                    position_size=0.95,
                    max_positions=1
                )
                
                if result.total_trades == 0:
                    return 0
                
                score = result.sharpe_ratio
                
                if score < 0:
                    score = 0
                
                return score
            except Exception as e:
                logger.warning(f"Backtest failed: {e}")
                return 0
        
        return self.optimizer.optimize(
            objective_fn=objective_fn,
            param_space=param_ranges,
            method=method
        )


strategy_optimizer = StrategyOptimizer()
parameter_optimizer = ParameterOptimizer()
