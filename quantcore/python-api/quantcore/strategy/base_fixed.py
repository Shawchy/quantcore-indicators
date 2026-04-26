# -*- coding: utf-8 -*-
"""
策略框架模块（修复版）

修复内容：
1. 消除 StrategyRunner.run() 中的重复执行问题
2. 增加事件驱动架构支持
3. 添加策略生命周期管理
"""

from typing import TYPE_CHECKING, List, Dict, Any, Optional
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, field

if TYPE_CHECKING:
    from ..engine import BacktestEngine
    from ..core import Bar


class StrategyState(Enum):
    """策略状态枚举"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    PAUSED = "paused"
    FINISHED = "finished"
    ERROR = "error"


@dataclass
class StrategyMetrics:
    """策略运行指标"""
    total_bars_processed: int = 0
    total_orders_created: int = 0
    execution_time_ms: float = 0.0
    memory_usage_mb: float = 0.0
    errors_count: int = 0


class Strategy:
    """策略基类（增强版）"""

    # 策略参数（子类可覆盖）
    parameters = {}

    def __init__(self):
        """初始化策略"""
        self.engine = None
        self.context = {}
        self._state = StrategyState.INITIALIZED
        self._metrics = StrategyMetrics()
        self._start_time: Optional[datetime] = None

    @property
    def state(self) -> StrategyState:
        """获取当前策略状态"""
        return self._state

    def on_init(self, engine: 'BacktestEngine'):
        """
        策略初始化

        Args:
            engine: 回测引擎
        """
        self.engine = engine
        self._state = StrategyState.INITIALIZED
        self._start_time = datetime.now()

    def on_bar(self, bar: 'Bar', engine: 'BacktestEngine'):
        """
        K 线事件

        Args:
            bar: K 线数据
            engine: 回测引擎
        """
        raise NotImplementedError("子类必须实现 on_bar 方法")

    def on_order(self, order):
        """
        订单事件

        Args:
            order: 订单对象
        """
        pass

    def on_trade(self, trade):
        """
        成交事件

        Args:
            trade: 成交对象
        """
        pass

    def on_finish(self, engine: 'BacktestEngine'):
        """
        回测结束

        Args:
            engine: 回测引擎
        """
        pass

    def on_error(self, error: Exception, context: Dict[str, Any] = None):
        """
        错误处理（新增）

        Args:
            error: 异常对象
            context: 错误上下文
        """
        self._state = StrategyState.ERROR
        self._metrics.errors_count += 1
        print(f"[Strategy Error] {error}")

    def buy(self, symbol: str, price: float, volume: int, order_type: str = "market"):
        """
        买入

        Args:
            symbol: 证券代码
            price: 价格
            volume: 数量
            order_type: 订单类型 ("market" 或 "limit")
        """
        if not self.engine:
            raise RuntimeError("Strategy not initialized. Call on_init() first.")

        order = self.engine.buy(symbol, price, volume, order_type)
        self._metrics.total_orders_created += 1
        return order

    def sell(self, symbol: str, price: float, volume: int, order_type: str = "market"):
        """
        卖出

        Args:
            symbol: 证券代码
            price: 价格
            volume: 数量
            order_type: 订单类型 ("market" 或 "limit")
        """
        if not self.engine:
            raise RuntimeError("Strategy not initialized. Call on_init() first.")

        order = self.engine.sell(symbol, price, volume, order_type)
        self._metrics.total_orders_created += 1
        return order

    def get_position(self, symbol: str):
        """获取持仓"""
        if not self.engine:
            raise RuntimeError("Strategy not initialized.")
        return self.engine.get_portfolio().get_position(symbol)

    def has_position(self, symbol: str) -> bool:
        """是否有持仓"""
        if not self.engine:
            return False
        return self.engine.get_portfolio().has_position(symbol)

    def get_cash(self) -> float:
        """获取可用资金"""
        if not self.engine:
            return 0.0
        return self.engine.get_portfolio().cash

    def get_metrics(self) -> StrategyMetrics:
        """获取策略运行指标"""
        return self._metrics


class StrategyRunner:
    """
    策略运行器（修复版）

    主要改进：
    1. 消除重复执行问题
    2. 增加状态管理
    3. 支持暂停/恢复
    4. 完善错误处理
    """

    def __init__(self, strategy: Strategy):
        """
        初始化策略运行器

        Args:
            strategy: 策略对象
        """
        if not isinstance(strategy, Strategy):
            raise TypeError(f"Expected Strategy instance, got {type(strategy)}")

        self.strategy = strategy
        self._current_bar_index: int = 0
        self._is_paused: bool = False

    def run(
        self,
        engine: 'BacktestEngine',
        bars: List['Bar'],
        start_index: int = 0,
        end_index: Optional[int] = None
    ) -> Any:
        """
        运行策略回测（已修复重复执行问题）

        Args:
            engine: 回测引擎（必须已经初始化并配置好）
            bars: K 线数据列表
            start_index: 起始索引（用于断点续跑）
            end_index: 结束索引（None表示到最后）

        Returns:
            回测结果（由 BacktestEngine 返回）

        使用示例：
        ```python
        runner = StrategyRunner(MyStrategy())
        config = BacktestConfig(initial_capital=1000000)
        engine = BacktestEngine(config)

        # 加载数据
        bars = load_data('SH.600000', ...)

        # 运行回测（只执行一次！）
        result = runner.run(engine, bars)
        ```
        """
        # 验证输入
        if not bars:
            raise ValueError("Bars list cannot be empty")

        if start_index < 0 or start_index >= len(bars):
            raise ValueError(f"Invalid start_index: {start_index}")

        if end_index is not None and (end_index < start_index or end_index > len(bars)):
            raise ValueError(f"Invalid end_index: {end_index}")

        # 设置实际结束索引
        actual_end_index = end_index if end_index is not None else len(bars)

        try:
            # ========== 第一步：初始化策略 ==========
            self.strategy.on_init(engine)
            self.strategy._state = StrategyState.RUNNING

            # ========== 第二步：遍历K线数据（只执行一次！）==========
            for i in range(start_index, actual_end_index):
                # 检查是否暂停
                if self._is_paused:
                    self._current_bar_index = i
                    break

                bar = bars[i]

                # 更新指标
                self.strategy._metrics.total_bars_processed += 1
                self._current_bar_index = i + 1

                # 触发策略的 on_bar 事件
                try:
                    self.strategy.on_bar(bar, engine)
                except Exception as e:
                    # 策略执行出错，调用错误处理
                    self.strategy.on_error(e, {
                        'bar_index': i,
                        'bar_timestamp': getattr(bar, 'timestamp', None),
                        'symbol': getattr(bar, 'symbol', None)
                    })
                    # 可以选择继续或中断
                    # 这里选择继续执行，记录错误

            # ========== 第三步：回测结束 ==========
            if not self._is_paused:
                self.strategy.on_finish(engine)
                self.strategy._state = StrategyState.FINISHED

                # 计算执行时间
                if self.strategy._start_time:
                    elapsed = (datetime.now() - self.strategy._start_time).total_seconds() * 1000
                    self.strategy._metrics.execution_time_ms = elapsed

            # ========== 第四步：返回结果（不再重新运行！）==========
            # 关键改进：直接返回引擎中已计算的结果，而不是再次调用 engine.run()
            result = engine.get_current_result()

            return result

        except Exception as e:
            self.strategy.on_error(e, {'phase': 'execution'})
            raise

    def pause(self):
        """暂停策略执行"""
        self._is_paused = True
        self.strategy._state = StrategyState.PAUSED

    def resume(
        self,
        engine: 'BacktestEngine',
        bars: List['Bar']
    ) -> Any:
        """
        恍复策略执行（从断点继续）

        Args:
            engine: 回测引擎
            bars: K 线数据列表（必须是同一组数据）

        Returns:
            回测结果
        """
        if not self._is_paused:
            print("Warning: Strategy is not paused")
            return None

        self._is_paused = False
        return self.run(engine, bars, start_index=self._current_bar_index)

    def get_progress(self) -> Dict[str, Any]:
        """
        获取执行进度

        Returns:
            包含进度信息的字典
        """
        return {
            'state': self.strategy.state.value,
            'current_bar_index': self._current_bar_index,
            'total_bars_processed': self.strategy._metrics.total_bars_processed,
            'total_orders_created': self.strategy._metrics.total_orders_created,
            'errors_count': self.strategy._metrics.errors_count,
            'is_paused': self._is_paused
        }


__all__ = ['Strategy', 'StrategyRunner', 'StrategyState', 'StrategyMetrics']
