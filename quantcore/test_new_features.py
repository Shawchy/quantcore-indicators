"""
新指标和日志系统测试
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'python-api'))

from quantcore import (
    kdj, atr, cci, williams_r, obv,
    get_logger, set_log_level, LogLevel,
    log_context, get_backtest_logger
)


def test_kdj():
    """测试 KDJ 指标"""
    print("\n" + "="*60)
    print("测试 KDJ 指标")
    print("="*60)
    
    # 生成测试数据
    prices = [10.0 + i * 0.1 for i in range(30)]
    
    # 计算 KDJ
    result = kdj(prices, n=9)
    
    if result['k'] and result['d'] and result['j']:
        print(f"✓ KDJ 计算成功")
        print(f"  最新 K 值：{result['k'][-1]:.2f}")
        print(f"  最新 D 值：{result['d'][-1]:.2f}")
        print(f"  最新 J 值：{result['j'][-1]:.2f}")
        
        # 判断金叉死叉
        if len(result['k']) >= 2 and len(result['d']) >= 2:
            if result['k'][-2] < result['d'][-2] and result['k'][-1] > result['d'][-1]:
                print(f"  信号：金叉（买入）")
            elif result['k'][-2] > result['d'][-2] and result['k'][-1] < result['d'][-1]:
                print(f"  信号：死叉（卖出）")
    else:
        print(f"✗ KDJ 计算失败：数据不足")


def test_atr():
    """测试 ATR 指标"""
    print("\n" + "="*60)
    print("测试 ATR 指标")
    print("="*60)
    
    # 生成测试数据
    high = [10.5 + i * 0.1 for i in range(30)]
    low = [9.5 + i * 0.1 for i in range(30)]
    close = [10.0 + i * 0.1 for i in range(30)]
    
    # 计算 ATR
    result = atr(high, low, close, period=14)
    
    if result:
        print(f"✓ ATR 计算成功，共 {len(result)} 个值")
        print(f"  最新 ATR：{result[-1]:.4f}")
        print(f"  ATR 含义：平均每日波幅 {result[-1]:.2f}元")
    else:
        print(f"✗ ATR 计算失败：数据不足")


def test_cci():
    """测试 CCI 指标"""
    print("\n" + "="*60)
    print("测试 CCI 指标")
    print("="*60)
    
    # 生成测试数据
    high = [10.5 + i * 0.1 for i in range(30)]
    low = [9.5 + i * 0.1 for i in range(30)]
    close = [10.0 + i * 0.1 for i in range(30)]
    
    # 计算 CCI
    result = cci(high, low, close, period=14)
    
    if result:
        print(f"✓ CCI 计算成功，共 {len(result)} 个值")
        print(f"  最新 CCI：{result[-1]:.2f}")
        
        # 判断超买超卖
        if result[-1] > 100:
            print(f"  信号：超买（可能回调）")
        elif result[-1] < -100:
            print(f"  信号：超卖（可能反弹）")
        else:
            print(f"  信号：中性")
    else:
        print(f"✗ CCI 计算失败：数据不足")


def test_williams_r():
    """测试 Williams %R 指标"""
    print("\n" + "="*60)
    print("测试 Williams %R 指标")
    print("="*60)
    
    # 生成测试数据
    high = [10.5 + i * 0.1 for i in range(30)]
    low = [9.5 + i * 0.1 for i in range(30)]
    close = [10.0 + i * 0.1 for i in range(30)]
    
    # 计算 Williams %R
    result = williams_r(high, low, close, period=14)
    
    if result:
        print(f"✓ Williams %R 计算成功，共 {len(result)} 个值")
        print(f"  最新值：{result[-1]:.2f}")
        
        # 判断超买超卖
        if result[-1] > -20:
            print(f"  信号：超买（可能回调）")
        elif result[-1] < -80:
            print(f"  信号：超卖（可能反弹）")
        else:
            print(f"  信号：中性")
    else:
        print(f"✗ Williams %R 计算失败：数据不足")


def test_obv():
    """测试 OBV 指标"""
    print("\n" + "="*60)
    print("测试 OBV 指标")
    print("="*60)
    
    # 生成测试数据
    close = [10.0, 10.2, 10.1, 10.5, 10.3, 10.6, 10.8, 10.7, 11.0, 11.2]
    volumes = [1000000, 1200000, 1100000, 1300000, 1000000, 1400000, 1500000, 1200000, 1600000, 1700000]
    
    # 计算 OBV
    result = obv(close, volumes)
    
    if result:
        print(f"✓ OBV 计算成功，共 {len(result)} 个值")
        print(f"  最新 OBV：{result[-1]:.0f}")
        
        # 判断趋势
        if len(result) >= 2:
            if result[-1] > result[-2]:
                print(f"  信号：资金流入")
            elif result[-1] < result[-2]:
                print(f"  信号：资金流出")
            else:
                print(f"  信号：资金平衡")
    else:
        print(f"✗ OBV 计算失败：数据不足")


def test_logger():
    """测试日志系统"""
    print("\n" + "="*60)
    print("测试日志系统")
    print("="*60)
    
    # 获取日志器
    logger = get_backtest_logger()
    
    print("\n测试不同级别的日志:")
    logger.debug("这是一条调试信息")
    logger.info("这是一条一般信息")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    
    # 测试临时改变日志级别
    print("\n测试日志上下文（临时设置为 DEBUG）:")
    with log_context(logger, LogLevel.DEBUG):
        logger.debug("这条调试信息应该显示")
        logger.info("这条一般信息也应该显示")
    
    print("\n上下文结束后（恢复到 INFO）:")
    logger.debug("这条调试信息不应该显示")
    logger.info("这条一般信息应该显示")
    
    print("\n✓ 日志系统测试完成")


def test_all_indicators():
    """测试所有指标"""
    print("\n" + "="*60)
    print("技术指标综合测试")
    print("="*60)
    
    # 生成测试数据
    prices = [10.0 + i * 0.1 for i in range(50)]
    high = [p * 1.02 for p in prices]
    low = [p * 0.98 for p in prices]
    close = prices
    volumes = [1000000 + i * 10000 for i in range(50)]
    
    print("\n计算所有技术指标:")
    
    # MA
    ma5 = sum(prices[-5:]) / 5
    print(f"✓ MA(5): {ma5:.2f}")
    
    # EMA
    ema12 = [prices[0]]
    multiplier = 2 / (12 + 1)
    for price in prices[1:]:
        ema12.append((price - ema12[-1]) * multiplier + ema12[-1])
    print(f"✓ EMA(12): {ema12[-1]:.2f}")
    
    # MACD
    from quantcore import macd
    macd_result = macd(prices)
    if macd_result['macd']:
        print(f"✓ MACD: DIF={macd_result['macd'][-1]:.2f}, DEA={macd_result['signal'][-1]:.2f}")
    
    # RSI
    from quantcore import rsi
    rsi14 = rsi(prices, 14)
    if rsi14:
        print(f"✓ RSI(14): {rsi14[-1]:.2f}")
    
    # BOLL
    from quantcore import bollinger_bands
    boll = bollinger_bands(prices, 20)
    if boll['upper']:
        print(f"✓ BOLL(20): 上轨={boll['upper'][-1]:.2f}, 中轨={boll['middle'][-1]:.2f}, 下轨={boll['lower'][-1]:.2f}")
    
    # KDJ
    kdj_result = kdj(prices, 9)
    if kdj_result['k']:
        print(f"✓ KDJ(9): K={kdj_result['k'][-1]:.2f}, D={kdj_result['d'][-1]:.2f}, J={kdj_result['j'][-1]:.2f}")
    
    # ATR
    atr_result = atr(high, low, close, 14)
    if atr_result:
        print(f"✓ ATR(14): {atr_result[-1]:.4f}")
    
    # CCI
    cci_result = cci(high, low, close, 14)
    if cci_result:
        print(f"✓ CCI(14): {cci_result[-1]:.2f}")
    
    # Williams %R
    wr_result = williams_r(high, low, close, 14)
    if wr_result:
        print(f"✓ Williams %R(14): {wr_result[-1]:.2f}")
    
    # OBV
    obv_result = obv(close, volumes)
    if obv_result:
        print(f"✓ OBV: {obv_result[-1]:.0f}")
    
    print("\n✓ 所有指标计算完成！")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("QuantCore 新指标和日志系统测试")
    print("="*60)
    
    # 测试各个指标
    test_kdj()
    test_atr()
    test_cci()
    test_williams_r()
    test_obv()
    
    # 测试日志系统
    test_logger()
    
    # 综合测试
    test_all_indicators()
    
    print("\n" + "="*60)
    print("✓✓✓ 所有测试完成！")
    print("="*60)
