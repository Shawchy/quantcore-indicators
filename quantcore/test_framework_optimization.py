# -*- coding: utf-8 -*-
"""
框架优化验证测试

测试优化后的功能：
1. 订单创建重构
2. 绩效计算完善
3. 风控日期处理
4. 异常处理
5. 数据重采样验证
"""

import sys
from datetime import datetime, date, timedelta
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent / "python-api"))

from quantcore.core import Bar, OrderSide, OrderType
from quantcore.engine import BacktestEngine, BacktestConfig
from quantcore.strategy.base import Strategy

# 直接从 risk.py 导入（注意：risk 已重构为包，但 risk.py 仍保留）
import sys
from pathlib import Path
risk_py_path = Path(__file__).parent / "python-api" / "quantcore" / "risk.py"
if risk_py_path.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("risk_module", risk_py_path)
    risk_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(risk_module)
    RiskManager = risk_module.RiskManager
    RiskConfig = risk_module.RiskConfig
else:
    print("警告：risk.py 文件不存在")
    sys.exit(1)

from quantcore.data.resample import Resampler
from quantcore.exceptions import (
    InsufficientDataException,
    DataFormatException,
    DataException
)


class TestStrategy(Strategy):
    """测试策略"""
    
    def __init__(self):
        super().__init__()
        self.bar_count = 0
    
    def on_init(self, engine):
        super().on_init(engine)
    
    def on_bar(self, bar, engine):
        self.bar_count += 1
        
        # 简单策略：第一天买入，第 10 天卖出
        if self.bar_count == 1:
            portfolio = engine.get_portfolio()
            volume = int(portfolio.cash * 0.95 / bar.close / 100) * 100
            if volume >= 100:
                engine.buy(bar.symbol, bar.close, volume)
        elif self.bar_count >= 10:
            portfolio = engine.get_portfolio()
            if bar.symbol in portfolio.positions:
                pos = portfolio.positions[bar.symbol]
                if pos.quantity > 0:
                    engine.sell(bar.symbol, bar.close, pos.quantity)


def generate_test_bars(num_days: int = 20) -> list:
    """生成测试 K 线数据"""
    bars = []
    base_price = 10.0
    base_date = datetime(2024, 1, 1)
    
    for i in range(num_days):
        timestamp = base_date + timedelta(days=i)
        price = base_price + i * 0.1
        
        bar = Bar(
            timestamp=timestamp.strftime('%Y-%m-%d'),
            symbol="SH.600000",
            open=price,
            high=price * 1.02,
            low=price * 0.98,
            close=price * 1.01,
            volume=1000000,
            turnover=10000000
        )
        bars.append(bar)
    
    return bars


def test_order_creation():
    """测试订单创建重构"""
    print("\n" + "="*60)
    print("测试 1: 订单创建重构")
    print("="*60)
    
    config = BacktestConfig(initial_capital=1000000)
    engine = BacktestEngine(config)
    
    # 测试买入订单
    buy_order = engine.buy("SH.600000", 10.0, 1000, "market")
    assert buy_order.order_id == "BUY-1", f"订单 ID 错误：{buy_order.order_id}"
    assert buy_order.side == OrderSide.BUY
    assert buy_order.quantity == 1000
    print("✓ 买入订单创建成功")
    
    # 测试卖出订单
    sell_order = engine.sell("SH.600000", 10.0, 1000, "limit")
    assert sell_order.order_id == "SELL-2", f"订单 ID 错误：{sell_order.order_id}"
    assert sell_order.side == OrderSide.SELL
    assert sell_order.order_type == OrderType.LIMIT
    print("✓ 卖出订单创建成功")
    
    # 测试市价单和限价单
    market_order = engine.buy("SH.600000", 10.0, 1000, "market")
    assert market_order.order_type == OrderType.MARKET
    print("✓ 市价单创建成功")
    
    limit_order = engine.sell("SH.600000", 10.0, 1000, "limit")
    assert limit_order.order_type == OrderType.LIMIT
    print("✓ 限价单创建成功")
    
    print("\n✅ 订单创建重构测试通过")


def test_performance_calculation():
    """测试绩效计算完善"""
    print("\n" + "="*60)
    print("测试 2: 绩效计算完善")
    print("="*60)
    
    # 生成测试数据
    bars = generate_test_bars(20)
    
    # 创建引擎和策略
    config = BacktestConfig(
        initial_capital=1000000,
        commission_rate=0.0003,
        slippage=0.001,
        stamp_tax=0.001
    )
    engine = BacktestEngine(config)
    strategy = TestStrategy()
    
    # 运行回测
    result = engine.run(strategy, bars)
    
    # 验证绩效指标
    print(f"\n初始资金：{result.initial_capital:.2f}")
    print(f"最终资金：{result.final_capital:.2f}")
    print(f"总收益：{result.total_return:.2%}")
    print(f"年化收益：{result.annual_return:.2%}")
    print(f"夏普比率：{result.sharpe_ratio:.2f}")
    print(f"最大回撤：{result.max_drawdown:.2%}")
    print(f"卡尔玛比率：{result.calmar_ratio:.2f}")
    print(f"交易次数：{result.total_trades}")
    print(f"胜率：{result.win_rate:.2%}")
    print(f"盈亏比：{result.profit_loss_ratio:.2f}")
    
    # 验证基本指标存在
    assert result.initial_capital == 1000000
    assert result.final_capital > 0
    assert result.total_trades >= 0
    assert len(result.daily_values) == 20
    
    print("\n✅ 绩效计算完善测试通过")


def test_risk_manager_date_handling():
    """测试风控日期处理"""
    print("\n" + "="*60)
    print("测试 3: 风控日期处理（回测模式）")
    print("="*60)
    
    config = RiskConfig(
        max_position_ratio=0.95,
        stop_loss_ratio=0.08,
        max_daily_loss=50000
    )
    
    # 回测模式
    risk_manager = RiskManager(config, initial_capital=1000000, is_backtest=True)
    
    # 模拟第一天
    test_date1 = date(2024, 1, 1)
    risk_manager.update_portfolio(1000000, 500000, current_date=test_date1)
    risk_manager.add_trade("SH.600000", "buy", 1000, 10.0)
    
    assert risk_manager.today_date == test_date1
    assert len(risk_manager.today_trades) == 1
    print(f"✓ 第一天交易记录：{len(risk_manager.today_trades)} 笔")
    
    # 模拟第二天（应该重置交易计数）
    test_date2 = date(2024, 1, 2)
    risk_manager.update_portfolio(1010000, 510000, current_date=test_date2)
    
    assert risk_manager.today_date == test_date2
    assert len(risk_manager.today_trades) == 0  # 已重置
    print(f"✓ 第二天交易记录重置：{len(risk_manager.today_trades)} 笔")
    
    # 同一天再次更新（不应该重置）
    risk_manager.update_portfolio(1020000, 520000, current_date=test_date2)
    assert len(risk_manager.today_trades) == 0  # 保持为 0
    print(f"✓ 同一天交易记录保持：{len(risk_manager.today_trades)} 笔")
    
    print("\n✅ 风控日期处理测试通过")


def test_resample_validation():
    """测试数据重采样验证"""
    print("\n" + "="*60)
    print("测试 4: 数据重采样验证")
    print("="*60)
    
    # 生成测试数据
    bars = generate_test_bars(20)
    
    # 测试空数据异常
    try:
        resampler = Resampler([])
        print("❌ 应该抛出 InsufficientDataException")
    except InsufficientDataException as e:
        print(f"✓ 正确抛出数据异常：{e}")
    
    # 测试正常重采样
    resampler = Resampler(bars)
    daily_bars = resampler.resample_to_daily()
    assert len(daily_bars) == 20
    print(f"✓ 日线重采样成功：{len(daily_bars)} 根 K 线")
    
    # 测试无效频率
    try:
        resampler.resample("invalid")
        print("❌ 应该抛出 DataException")
    except DataException as e:
        print(f"✓ 正确抛出频率异常：{e}")
    
    # 测试无效分钟频率
    try:
        resampler.resample("-5min")
        print("❌ 应该抛出 DataException")
    except DataException as e:
        print(f"✓ 正确抛出分钟频率异常：{e}")
    
    print("\n✅ 数据重采样验证测试通过")


def test_exception_hierarchy():
    """测试异常层次结构"""
    print("\n" + "="*60)
    print("测试 5: 异常层次结构")
    print("="*60)
    
    # 测试基础异常
    try:
        from quantcore.exceptions import QuantCoreException
        raise QuantCoreException("测试异常", "TEST")
    except QuantCoreException as e:
        print(f"✓ 基础异常：{e}")
    
    # 测试数据异常
    try:
        from quantcore.exceptions import DataException
        raise DataException("数据错误", "DATA_ERR")
    except DataException as e:
        print(f"✓ 数据异常：{e}")
    
    # 测试风控异常
    try:
        from quantcore.exceptions import RiskException
        raise RiskException("风控触发", "RISK_TRIGGER")
    except RiskException as e:
        print(f"✓ 风控异常：{e}")
    
    print("\n✅ 异常层次结构测试通过")


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*70)
    print("QuantCore 框架优化验证测试")
    print("="*70)
    
    tests = [
        ("订单创建重构", test_order_creation),
        ("绩效计算完善", test_performance_calculation),
        ("风控日期处理", test_risk_manager_date_handling),
        ("数据重采样验证", test_resample_validation),
        ("异常层次结构", test_exception_hierarchy),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except Exception as e:
            print(f"\n❌ {test_name} 测试失败：{e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*70)
    print(f"测试完成：{passed} 通过，{failed} 失败")
    print("="*70)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
