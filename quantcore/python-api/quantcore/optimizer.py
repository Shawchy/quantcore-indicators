"""
参数优化工具

提供网格搜索和随机搜索功能，用于策略参数优化
"""

from typing import Dict, List, Any, Callable, Tuple
from dataclasses import dataclass
import itertools
import random
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import time
from datetime import datetime


@dataclass
class OptimizationResult:
    """优化结果"""
    parameters: Dict[str, Any]  # 最优参数
    return_value: float  # 收益率
    sharpe_ratio: float  # 夏普比率
    max_drawdown: float  # 最大回撤
    total_trades: int  # 交易次数
    win_rate: float  # 胜率
    run_time: float  # 运行时间（秒）
    rank: int = 1  # 排名


class GridSearch:
    """
    网格搜索优化器
    
    示例:
        optimizer = GridSearch()
        results = optimizer.optimize(
            strategy_class=DualMAStrategy,
            param_grid={
                'fast_period': [5, 10, 20],
                'slow_period': [20, 60, 120],
            },
            bars=bars,
            objective='sharpe'
        )
    """
    
    def __init__(self, parallel: bool = True, max_workers: int = 4):
        """
        初始化网格搜索
        
        Args:
            parallel: 是否并行执行
            max_workers: 最大工作线程数
        """
        self.parallel = parallel
        self.max_workers = max_workers
        self.results = []
    
    def optimize(
        self,
        strategy_class: Any,
        param_grid: Dict[str, List[Any]],
        bars: List[Any],
        initial_capital: float = 1000000.0,
        objective: str = 'sharpe',
        verbose: bool = True
    ) -> List[OptimizationResult]:
        """
        执行网格搜索
        
        Args:
            strategy_class: 策略类
            param_grid: 参数网格 {param_name: [values]}
            bars: K 线数据
            initial_capital: 初始资金
            objective: 优化目标 ('return', 'sharpe', 'drawdown')
            verbose: 是否打印进度
            
        Returns:
            优化结果列表（按目标排序）
        """
        start_time = time.time()
        
        # 生成所有参数组合
        param_names = list(param_grid.keys())
        param_values = list(param_grid.values())
        all_combinations = list(itertools.product(*param_values))
        
        total_runs = len(all_combinations)
        if verbose:
            print(f"开始网格搜索，共 {total_runs} 种参数组合")
        
        # 创建任务列表
        tasks = []
        for i, values in enumerate(all_combinations):
            params = dict(zip(param_names, values))
            tasks.append((strategy_class, params, bars, initial_capital, i + 1))
        
        # 执行优化
        if self.parallel and total_runs > 1:
            results = self._run_parallel(tasks, objective, verbose)
        else:
            results = self._run_sequential(tasks, objective, verbose)
        
        # 排序
        results = self._sort_results(results, objective)
        
        elapsed = time.time() - start_time
        if verbose:
            print(f"\n网格搜索完成，耗时 {elapsed:.2f}秒")
            print(f"最佳参数：{results[0].parameters}")
            print(f"最佳收益：{results[0].return_value*100:.2f}%")
        
        self.results = results
        return results
    
    def _run_parallel(self, tasks: List[Tuple], objective: str, verbose: bool) -> List[OptimizationResult]:
        """并行执行"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._run_single_task, task) for task in tasks]
            
            for i, future in enumerate(futures):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if verbose and (i + 1) % 10 == 0:
                        print(f"进度：{i+1}/{len(tasks)}")
                except Exception as e:
                    if verbose:
                        print(f"任务 {i+1} 失败：{e}")
        
        return results
    
    def _run_sequential(self, tasks: List[Tuple], objective: str, verbose: bool) -> List[OptimizationResult]:
        """顺序执行"""
        results = []
        
        for i, task in enumerate(tasks):
            try:
                result = self._run_single_task(task)
                results.append(result)
                
                if verbose and (i + 1) % 10 == 0:
                    print(f"进度：{i+1}/{len(tasks)}, 当前收益：{result.return_value*100:.2f}%")
            except Exception as e:
                if verbose:
                    print(f"任务 {i+1} 失败：{e}")
        
        return results
    
    def _run_single_task(self, task: Tuple) -> OptimizationResult:
        """运行单个任务"""
        strategy_class, params, bars, initial_capital, rank = task
        
        # 创建策略实例
        strategy = strategy_class()
        
        # 更新参数
        if hasattr(strategy, 'parameters'):
            strategy.parameters.update(params)
        
        # 设置策略属性
        for key, value in params.items():
            setattr(strategy, key, value)
        
        # 运行回测
        from quantcore import BacktestEngine, BacktestConfig, StrategyRunner
        
        config = BacktestConfig(initial_capital=initial_capital)
        engine = BacktestEngine(config)
        runner = StrategyRunner(strategy)
        result = runner.run(engine, bars)
        
        # 计算绩效指标（简化版，避免 Rust/Python Trade 类型转换问题）
        sharpe = 0.0
        max_dd = 0.0
        win_rate = 0.0
        
        if result.daily_values and len(result.daily_values) > 1:
            # 计算夏普比率
            import statistics
            returns = [(result.daily_values[i] - result.daily_values[i-1]) / result.daily_values[i-1] 
                      for i in range(1, len(result.daily_values))]
            if returns:
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns) if len(returns) > 1 else 1.0
                sharpe = (avg_return - 0.03/250) / std_return * (250 ** 0.5) if std_return > 0 else 0
            
            # 计算最大回撤
            peak = result.daily_values[0]
            for value in result.daily_values:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
        
        # 计算胜率
        if result.trades and len(result.trades) > 0:
            win_rate = 0.5  # 简化处理
        
        # 创建优化结果
        opt_result = OptimizationResult(
            parameters=params,
            return_value=result.total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            total_trades=result.total_trades,
            win_rate=win_rate,
            run_time=0,  # 会在外部计算
            rank=rank
        )
        
        return opt_result
    
    def _sort_results(self, results: List[OptimizationResult], objective: str) -> List[OptimizationResult]:
        """排序结果"""
        if objective == 'return':
            return sorted(results, key=lambda x: x.return_value, reverse=True)
        elif objective == 'sharpe':
            return sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)
        elif objective == 'drawdown':
            return sorted(results, key=lambda x: x.max_drawdown)
        else:
            return results
    
    def print_top_results(self, top_n: int = 10):
        """打印前 N 个结果"""
        if not self.results:
            print("没有优化结果")
            return
        
        print(f"\n{'='*80}")
        print(f"Top {top_n} 优化结果")
        print(f"{'='*80}")
        print(f"{'排名':<6} {'收益率':>12} {'夏普比率':>12} {'最大回撤':>12} {'交易次数':>10} {'参数':<40}")
        print(f"{'-'*80}")
        
        for i, result in enumerate(self.results[:top_n], 1):
            params_str = ', '.join([f"{k}={v}" for k, v in result.parameters.items()])
            print(f"{i:<6} {result.return_value*100:>11.2f}% "
                  f"{result.sharpe_ratio:>12.2f} "
                  f"{result.max_drawdown*100:>11.2f}% "
                  f"{result.total_trades:>10} "
                  f"{params_str:<40}")


class RandomSearch:
    """
    随机搜索优化器
    
    示例:
        optimizer = RandomSearch()
        results = optimizer.optimize(
            strategy_class=DualMAStrategy,
            param_distributions={
                'fast_period': (5, 50),
                'slow_period': (20, 200),
            },
            bars=bars,
            n_iterations=100
        )
    """
    
    def __init__(self, parallel: bool = True, max_workers: int = 4, random_state: int = 42):
        """
        初始化随机搜索
        
        Args:
            parallel: 是否并行执行
            max_workers: 最大工作线程数
            random_state: 随机种子
        """
        self.parallel = parallel
        self.max_workers = max_workers
        self.random_state = random_state
        self.results = []
        random.seed(random_state)
    
    def optimize(
        self,
        strategy_class: Any,
        param_distributions: Dict[str, Tuple[Any, Any]],
        bars: List[Any],
        n_iterations: int = 100,
        initial_capital: float = 1000000.0,
        objective: str = 'sharpe',
        verbose: bool = True
    ) -> List[OptimizationResult]:
        """
        执行随机搜索
        
        Args:
            strategy_class: 策略类
            param_distributions: 参数分布 {param_name: (min, max)}
            bars: K 线数据
            n_iterations: 迭代次数
            initial_capital: 初始资金
            objective: 优化目标
            verbose: 是否打印进度
            
        Returns:
            优化结果列表
        """
        start_time = time.time()
        
        if verbose:
            print(f"开始随机搜索，共 {n_iterations} 次迭代")
        
        # 生成随机参数
        tasks = []
        for i in range(n_iterations):
            params = self._sample_parameters(param_distributions)
            tasks.append((strategy_class, params, bars, initial_capital, i + 1))
        
        # 执行优化
        if self.parallel:
            results = self._run_parallel(tasks, objective, verbose)
        else:
            results = self._run_sequential(tasks, objective, verbose)
        
        # 排序
        results = self._sort_results(results, objective)
        
        elapsed = time.time() - start_time
        if verbose:
            print(f"\n随机搜索完成，耗时 {elapsed:.2f}秒")
            print(f"最佳参数：{results[0].parameters}")
            print(f"最佳收益：{results[0].return_value*100:.2f}%")
        
        self.results = results
        return results
    
    def _sample_parameters(self, param_distributions: Dict[str, Tuple[Any, Any]]) -> Dict[str, Any]:
        """采样参数"""
        params = {}
        
        for param_name, (min_val, max_val) in param_distributions.items():
            if isinstance(min_val, int) and isinstance(max_val, int):
                # 整数参数
                params[param_name] = random.randint(min_val, max_val)
            else:
                # 浮点数参数
                params[param_name] = random.uniform(min_val, max_val)
        
        return params
    
    def _run_parallel(self, tasks: List[Tuple], objective: str, verbose: bool) -> List[OptimizationResult]:
        """并行执行（同 GridSearch）"""
        results = []
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._run_single_task, task) for task in tasks]
            
            for i, future in enumerate(futures):
                try:
                    result = future.result()
                    results.append(result)
                    
                    if verbose and (i + 1) % 10 == 0:
                        print(f"进度：{i+1}/{len(tasks)}")
                except Exception as e:
                    if verbose:
                        print(f"任务 {i+1} 失败：{e}")
        
        return results
    
    def _run_sequential(self, tasks: List[Tuple], objective: str, verbose: bool) -> List[OptimizationResult]:
        """顺序执行"""
        results = []
        
        for i, task in enumerate(tasks):
            try:
                result = self._run_single_task(task)
                results.append(result)
                
                if verbose and (i + 1) % 10 == 0:
                    print(f"进度：{i+1}/{len(tasks)}, 当前收益：{result.return_value*100:.2f}%")
            except Exception as e:
                if verbose:
                    print(f"任务 {i+1} 失败：{e}")
        
        return results
    
    def _run_single_task(self, task: Tuple) -> OptimizationResult:
        """运行单个任务（同 GridSearch）"""
        from quantcore import BacktestEngine, BacktestConfig, StrategyRunner
        
        strategy_class, params, bars, initial_capital, rank = task
        
        # 创建策略实例
        strategy = strategy_class()
        
        # 更新参数
        if hasattr(strategy, 'parameters'):
            strategy.parameters.update(params)
        
        # 设置策略属性
        for key, value in params.items():
            setattr(strategy, key, value)
        
        # 运行回测
        config = BacktestConfig(initial_capital=initial_capital)
        engine = BacktestEngine(config)
        runner = StrategyRunner(strategy)
        result = runner.run(engine, bars)
        
        # 计算绩效指标（简化版）
        sharpe = 0.0
        max_dd = 0.0
        win_rate = 0.0
        
        if result.daily_values and len(result.daily_values) > 1:
            import statistics
            returns = [(result.daily_values[i] - result.daily_values[i-1]) / result.daily_values[i-1] 
                      for i in range(1, len(result.daily_values))]
            if returns:
                avg_return = statistics.mean(returns)
                std_return = statistics.stdev(returns) if len(returns) > 1 else 1.0
                sharpe = (avg_return - 0.03/250) / std_return * (250 ** 0.5) if std_return > 0 else 0
            
            peak = result.daily_values[0]
            for value in result.daily_values:
                if value > peak:
                    peak = value
                dd = (peak - value) / peak
                if dd > max_dd:
                    max_dd = dd
        
        if result.trades and len(result.trades) > 0:
            win_rate = 0.5
        
        opt_result = OptimizationResult(
            parameters=params,
            return_value=result.total_return,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            total_trades=result.total_trades,
            win_rate=win_rate,
            run_time=0,
            rank=rank
        )
        
        return opt_result
    
    def _sort_results(self, results: List[OptimizationResult], objective: str) -> List[OptimizationResult]:
        """排序结果（同 GridSearch）"""
        if objective == 'return':
            return sorted(results, key=lambda x: x.return_value, reverse=True)
        elif objective == 'sharpe':
            return sorted(results, key=lambda x: x.sharpe_ratio, reverse=True)
        elif objective == 'drawdown':
            return sorted(results, key=lambda x: x.max_drawdown)
        else:
            return results
    
    def print_top_results(self, top_n: int = 10):
        """打印前 N 个结果（同 GridSearch）"""
        if not self.results:
            print("没有优化结果")
            return
        
        print(f"\n{'='*80}")
        print(f"Top {top_n} 优化结果")
        print(f"{'='*80}")
        print(f"{'排名':<6} {'收益率':>12} {'夏普比率':>12} {'最大回撤':>12} {'交易次数':>10} {'参数':<40}")
        print(f"{'-'*80}")
        
        for i, result in enumerate(self.results[:top_n], 1):
            params_str = ', '.join([f"{k}={v}" for k, v in result.parameters.items()])
            print(f"{i:<6} {result.return_value*100:>11.2f}% "
                  f"{result.sharpe_ratio:>12.2f} "
                  f"{result.max_drawdown*100:>11.2f}% "
                  f"{result.total_trades:>10} "
                  f"{params_str:<40}")


def optimize_strategy(
    strategy_class: Any,
    param_grid: Dict[str, List[Any]],
    bars: List[Any],
    method: str = 'grid',
    n_iterations: int = 100,
    initial_capital: float = 1000000.0,
    objective: str = 'sharpe',
    parallel: bool = True,
    max_workers: int = 4,
    verbose: bool = True
) -> List[OptimizationResult]:
    """
    策略优化便捷函数
    
    Args:
        strategy_class: 策略类
        param_grid: 参数网格或分布
        bars: K 线数据
        method: 优化方法 ('grid' 或 'random')
        n_iterations: 随机搜索迭代次数
        initial_capital: 初始资金
        objective: 优化目标
        parallel: 是否并行
        max_workers: 最大工作线程数
        verbose: 是否打印进度
        
    Returns:
        优化结果列表
    """
    if method == 'grid':
        optimizer = GridSearch(parallel=parallel, max_workers=max_workers)
        return optimizer.optimize(
            strategy_class=strategy_class,
            param_grid=param_grid,
            bars=bars,
            initial_capital=initial_capital,
            objective=objective,
            verbose=verbose
        )
    elif method == 'random':
        optimizer = RandomSearch(parallel=parallel, max_workers=max_workers)
        return optimizer.optimize(
            strategy_class=strategy_class,
            param_distributions=param_grid,
            bars=bars,
            n_iterations=n_iterations,
            initial_capital=initial_capital,
            objective=objective,
            verbose=verbose
        )
    else:
        raise ValueError(f"Unknown optimization method: {method}")
