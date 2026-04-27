"""
QuantCore Bridge - 量化框架桥接模块

优先使用 QuantCore 高性能回测引擎，回退到内置 Python 实现
"""
from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime
from loguru import logger

# 尝试导入 QuantCore
try:
    import sys
    from app.config import get_quantcore_path
    
    quantcore_path = get_quantcore_path()
    if quantcore_path not in sys.path:
        sys.path.insert(0, quantcore_path)
    
    from quantcore import (
        BacktestEngine as QCBacktestEngine,
        BacktestConfig,
        BacktestResult as QCBacktestResult,
        Strategy,
        DataLoader,
        PerformanceAnalyzer,
        GridSearch,
        RiskManager,
    )
    QUANTCORE_AVAILABLE = True
    logger.info("✅ QuantCore 回测引擎已加载")
except ImportError as e:
    QUANTCORE_AVAILABLE = False
    logger.warning(f"⚠️ QuantCore 回测引擎未加载: {e}")


class QuantCoreBacktestBridge:
    """
    QuantCore 回测引擎桥接
    
    优先使用 QuantCore 高性能版本，如果不可用则回退到内置 Python 实现
    """
    
    def __init__(self, initial_capital: float = 1000000, commission_rate: float = 0.0003):
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.quantcore_available = QUANTCORE_AVAILABLE
        
        if self.quantcore_available:
            logger.info(f"QuantCore 引擎初始化: 初始资金={initial_capital:,.0f}")
        else:
            logger.warning("使用内置 Python 回测引擎（性能较低）")
    
    def run_backtest(
        self,
        df: pd.DataFrame,
        strategy_type: str = "ma_cross",
        strategy_params: Optional[Dict[str, Any]] = None,
        code: str = "UNKNOWN"
    ) -> Dict[str, Any]:
        """
        运行回测（自动选择最优引擎）
        
        Args:
            df: K 线数据 (必须包含 date, open, high, low, close, volume)
            strategy_type: 策略类型
            strategy_params: 策略参数
            code: 股票代码
        
        Returns:
            回测结果字典
        """
        if self.quantcore_available:
            return self._run_quantcore_backtest(df, strategy_type, strategy_params, code)
        else:
            return self._run_python_backtest(df, strategy_type, strategy_params, code)
    
    def _run_quantcore_backtest(
        self,
        df: pd.DataFrame,
        strategy_type: str,
        strategy_params: Optional[Dict[str, Any]],
        code: str
    ) -> Dict[str, Any]:
        """使用 QuantCore Rust 引擎运行回测"""
        try:
            # 创建配置
            config = BacktestConfig(
                initial_capital=self.initial_capital,
                commission_rate=self.commission_rate,
                slippage=0.0
            )
            
            # 创建引擎
            engine = QCBacktestEngine(config)
            
            # 转换数据为 QuantCore 格式
            bars = self._df_to_bars(df)
            
            # 创建策略
            strategy = self._create_quantcore_strategy(strategy_type, strategy_params or {})
            
            # 运行回测
            result = engine.run(strategy, bars)
            
            # 转换结果为标准格式
            return {
                'success': True,
                'engine': 'quantcore_rust',
                'initial_capital': result.initial_capital,
                'final_capital': result.final_capital,
                'total_return': result.total_return,
                'annual_return': result.annual_return,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'win_rate': result.win_rate,
                'total_trades': result.total_trades,
                'trades': result.trades,
                'equity_curve': result.equity_curve
            }
            
        except Exception as e:
            logger.error(f"QuantCore 回测失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'engine': 'quantcore_rust'
            }
    
    def _run_python_backtest(
        self,
        df: pd.DataFrame,
        strategy_type: str,
        strategy_params: Optional[Dict[str, Any]],
        code: str
    ) -> Dict[str, Any]:
        """使用内置 Python 引擎运行回测（回退方案）"""
        try:
            from app.core.backtest.engine import BacktestEngine
            
            engine = BacktestEngine(
                initial_capital=self.initial_capital,
                commission_rate=self.commission_rate
            )
            
            result = engine.run(
                df=df,
                strategy_type=strategy_type,
                strategy_params=strategy_params or {}
            )
            
            return {
                'success': True,
                'engine': 'python_builtin',
                'initial_capital': result.initial_capital,
                'final_capital': result.final_capital,
                'total_return': result.total_return,
                'annual_return': result.annual_return,
                'max_drawdown': result.max_drawdown,
                'sharpe_ratio': result.sharpe_ratio,
                'win_rate': result.win_rate,
                'total_trades': result.total_trades,
                'trades': [t.__dict__ for t in result.trades],
                'equity_curve': result.equity_curve
            }
            
        except Exception as e:
            logger.error(f"Python 回测失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'engine': 'python_builtin'
            }
    
    def optimize_parameters(
        self,
        df: pd.DataFrame,
        strategy_type: str,
        param_grid: Dict[str, List[Any]],
        maximize: str = 'sharpe_ratio'
    ) -> Dict[str, Any]:
        """
        参数优化
        
        Args:
            df: K 线数据
            strategy_type: 策略类型
            param_grid: 参数网格 {'short_period': [5, 10, 20], 'long_period': [20, 30, 50]}
            maximize: 优化目标
        
        Returns:
            最优参数和结果
        """
        if self.quantcore_available:
            return self._optimize_quantcore(df, strategy_type, param_grid, maximize)
        else:
            return self._optimize_python(df, strategy_type, param_grid, maximize)
    
    def _optimize_quantcore(
        self,
        df: pd.DataFrame,
        strategy_type: str,
        param_grid: Dict[str, List[Any]],
        maximize: str
    ) -> Dict[str, Any]:
        """使用 QuantCore 优化器"""
        try:
            bars = self._df_to_bars(df)
            strategy_class = self._get_quantcore_strategy_class(strategy_type)
            
            optimizer = GridSearch(
                strategy_class=strategy_class,
                param_grid=param_grid,
                n_jobs=-1  # 使用所有 CPU 核心
            )
            
            result = optimizer.optimize(bars, maximize=maximize)
            
            return {
                'success': True,
                'engine': 'quantcore_optimizer',
                'best_params': result.best_params,
                'best_score': result.best_score,
                'total_runs': result.total_runs,
                'optimization_time': result.optimization_time,
                'results': result.results
            }
        except Exception as e:
            logger.error(f"QuantCore 优化失败: {e}")
            return {'success': False, 'error': str(e), 'engine': 'quantcore_optimizer'}
    
    def _optimize_python(
        self,
        df: pd.DataFrame,
        strategy_type: str,
        param_grid: Dict[str, List[Any]],
        maximize: str
    ) -> Dict[str, Any]:
        """使用 Python 暴力搜索优化"""
        import itertools
        
        best_score = -999999
        best_params = None
        best_result = None
        
        # 生成所有参数组合
        keys = list(param_grid.keys())
        values = list(param_grid.values())
        combinations = list(itertools.product(*values))
        
        logger.info(f"开始参数优化: {len(combinations)} 个组合")
        
        for combo in combinations:
            params = dict(zip(keys, combo))
            
            result = self.run_backtest(df, strategy_type, params)
            
            if result.get('success') and result.get(maximize, -999999) > best_score:
                best_score = result[maximize]
                best_params = params
                best_result = result
        
        return {
            'success': True,
            'engine': 'python_brute_force',
            'best_params': best_params,
            'best_score': best_score,
            'total_runs': len(combinations),
            'best_result': best_result
        }
    
    def _df_to_bars(self, df: pd.DataFrame) -> List:
        """转换 DataFrame 为 QuantCore Bar 列表"""
        if not self.quantcore_available:
            return []
        
        from quantcore import Bar
        
        bars = []
        for _, row in df.iterrows():
            bar = Bar(
                timestamp=row.get('date', ''),
                open=row['open'],
                high=row['high'],
                low=row['low'],
                close=row['close'],
                volume=row.get('volume', 0)
            )
            bars.append(bar)
        
        return bars
    
    def _create_quantcore_strategy(self, strategy_type: str, params: Dict[str, Any]):
        """创建 QuantCore 策略实例"""
        if not self.quantcore_available:
            return None
        
        strategy_class = self._get_quantcore_strategy_class(strategy_type)
        return strategy_class(params)
    
    def _get_quantcore_strategy_class(self, strategy_type: str):
        """获取策略类"""
        if not self.quantcore_available:
            return None
        
        from quantcore.strategy import Strategy
        
        # 创建动态策略类
        class DynamicStrategy(Strategy):
            def __init__(self, params):
                super().__init__()
                self.params = params
            
            def on_bar(self, bar, engine):
                # 简单均线策略示例
                if hasattr(self, 'bars'):
                    self.bars.append(bar)
                else:
                    self.bars = [bar]
                
                if len(self.bars) < 20:
                    return
                
                # MA 交叉策略
                if self.params.get('strategy_type', 'ma_cross') == 'ma_cross':
                    short_period = self.params.get('short_period', 5)
                    long_period = self.params.get('long_period', 20)
                    
                    if len(self.bars) >= long_period:
                        recent = self.bars[-long_period:]
                        ma_short = sum(b.close for b in recent[-short_period:]) / short_period
                        ma_long = sum(b.close for b in recent) / long_period
                        
                        # 安全获取 symbol（优先 bar.symbol，其次 params 中的 symbol）
                        symbol = getattr(bar, 'symbol', self.params.get('symbol', 'UNKNOWN'))
                        
                        if ma_short > ma_long and not engine.portfolio.has_position(symbol):
                            self.buy(symbol, bar.close, 100)
                        elif ma_short < ma_long and engine.portfolio.has_position(symbol):
                            self.sell(symbol, bar.close, 100)
        
        return DynamicStrategy


# 全局单例
_backtest_bridge: Optional[QuantCoreBacktestBridge] = None

def get_backtest_bridge(
    initial_capital: float = 1000000,
    commission_rate: float = 0.0003
) -> QuantCoreBacktestBridge:
    """获取全局回测桥接实例"""
    global _backtest_bridge
    if _backtest_bridge is None:
        _backtest_bridge = QuantCoreBacktestBridge(initial_capital, commission_rate)
    return _backtest_bridge
